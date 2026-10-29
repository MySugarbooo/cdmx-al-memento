"""Actualiza el estado público de Metro y Metrobús a partir del tablero oficial.

El origen es incidentesmovilidad.cdmx.gob.mx, integrado en las páginas de
Metro y Metrobús. El cliente externo observatorio==0.1.0 (MIT, felipao-mx)
resuelve la paginación necesaria para incluir las líneas A/B y múltiples
incidencias. No se interpreta "Servicio Regular" como trenes circulando.

Si falla o está incompleta la consulta, NO se reemplaza el último JSON válido.
El navegador deja de mostrar un estado cuando su consulta envejece >90 min.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "transporte" / "estado.json"
METRO_LINES = frozenset([*(str(n) for n in range(1, 10)), "12", "A", "B"])
METROBUS_LINES = frozenset(str(n) for n in range(1, 8))
OFFICIAL = {
    "stc": "https://www.metro.cdmx.gob.mx/la-red/estado-del-servicio",
    "mb": "https://metrobus.cdmx.gob.mx/ServicioMB",
}
STATUS_SOURCE = "https://incidentesmovilidad.cdmx.gob.mx/public/bandejaEstadoServicio.xhtml"


class IncompleteTransitData(ValueError):
    """The official feed did not include all expected lines."""


def clean(value: object, max_length: int = 280) -> str:
    return " ".join(str(value or "").split())[:max_length]


def normalize(system: str, data: list[dict]) -> list[dict]:
    """Accept only complete, recognized rows; preserve simultaneous incidents."""
    expected = METRO_LINES if system == "stc" else METROBUS_LINES if system == "mb" else None
    if expected is None:
        raise ValueError("Sistema de transporte desconocido")
    if not isinstance(data, list) or not (len(expected) <= len(data) <= 50):
        raise IncompleteTransitData(f"{system}: cantidad de filas inesperada")
    output = []
    for row in data:
        if not isinstance(row, dict):
            raise IncompleteTransitData(f"{system}: fila inválida")
        line = clean(row.get("linea"), 10).upper()
        state = clean(row.get("estado"), 110)
        if line not in expected or not state:
            raise IncompleteTransitData(f"{system}: línea o estado inválido: {line}")
        output.append({
            "linea": line,
            "estado": state,
            "estaciones_afectadas": clean(row.get("estaciones_afectadas"), 180),
            "informacion_adicional": clean(row.get("informacion_adicional"), 350),
            "regular": state.casefold().startswith("servicio regular"),
        })
    present = {item["linea"] for item in output}
    if present != expected:
        raise IncompleteTransitData(f"{system}: faltan líneas {sorted(expected - present)}")
    return output


async def fetch_snapshot() -> dict:
    # La importación diferida permite ejecutar pruebas sin acceder a internet.
    from observatorio import StatusClient

    async with StatusClient(timeout=18.0) as client:
        metro, metrobus = await asyncio.gather(client.fetch("stc"), client.fetch("mb"))
    lines = {
        "stc": normalize("stc", metro),
        "mb": normalize("mb", metrobus),
    }
    return {
        "schema": 1,
        "source": "Tablero público oficial de incidentes de movilidad CDMX",
        "source_url": STATUS_SOURCE,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "ok",
        "operators": {k: {"url": v, "rows": lines[k]} for k, v in OFFICIAL.items()},
        "note": "Hora de consulta del archivo, no de publicación de cada incidente ni de modificación de la fuente.",
    }


def write_snapshot(data: dict, destination: Path = OUT) -> None:
    if data.get("status") != "ok":
        raise IncompleteTransitData("No se permiten estados de ejemplo como reales")
    if not data.get("operators", {}).get("stc", {}).get("rows"):
        raise IncompleteTransitData("Faltan datos del Metro")
    if not data.get("operators", {}).get("mb", {}).get("rows"):
        raise IncompleteTransitData("Faltan datos del Metrobús")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, destination)


def main() -> None:
    data = asyncio.run(fetch_snapshot())
    write_snapshot(data)
    print(
        "Consulta oficial correcta:",
        data["checked_at"],
        "Metro", len(data["operators"]["stc"]["rows"]),
        "Metrobús", len(data["operators"]["mb"]["rows"]),
    )


if __name__ == "__main__":
    main()
