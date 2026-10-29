"""Pruebas sin red para el tablero verificado de Metro y Metrobús."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.estado_transporte import (
    IncompleteTransitData, METRO_LINES, METROBUS_LINES,
    normalize, write_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def example(system: str, extra: bool = False) -> list[dict]:
    lines = sorted(METRO_LINES if system == "stc" else METROBUS_LINES)
    result = [
        {
            "linea": line,
            "estado": "Servicio Regular",
            "estaciones_afectadas": "Ninguna",
            "informacion_adicional": "",
        }
        for line in lines
    ]
    if extra:
        result.append({
            "linea": lines[0],
            "estado": "Retraso en el servicio",
            "estaciones_afectadas": "Tramo de prueba",
            "informacion_adicional": "Texto de prueba",
        })
    return result


class TransportStatusTests(unittest.TestCase):
    def test_metro_includes_lines_a_b_and_12(self):
        self.assertEqual(len(METRO_LINES), 12)
        self.assertTrue({"A", "B", "12"}.issubset(METRO_LINES))
        parsed = normalize("stc", example("stc"))
        self.assertEqual(len(parsed), 12)
        self.assertEqual({x["linea"] for x in parsed}, METRO_LINES)

    def test_metrobus_includes_seven_lines(self):
        self.assertEqual(len(METROBUS_LINES), 7)
        self.assertEqual(len(normalize("mb", example("mb"))), 7)

    def test_multiple_incidents_same_line_are_preserved(self):
        rows = normalize("stc", example("stc", extra=True))
        self.assertEqual(len(rows), 13)
        self.assertEqual(len([x for x in rows if x["linea"] == "1"]), 2)
        self.assertTrue(any(not x["regular"] for x in rows))

    def test_incomplete_metro_does_not_pass_as_regular(self):
        rows = [x for x in example("stc") if x["linea"] != "B"]
        with self.assertRaises(IncompleteTransitData):
            normalize("stc", rows)
        with self.assertRaises(IncompleteTransitData):
            normalize("mb", example("mb")[:-1])

    def test_unknown_line_and_unknown_system_are_rejected(self):
        rows = example("mb")
        rows[0]["linea"] = "999"
        with self.assertRaises(IncompleteTransitData):
            normalize("mb", rows)
        with self.assertRaises(ValueError):
            normalize("other", rows)

    def test_malformed_or_blank_status_rejected(self):
        rows = example("stc")
        rows[1]["estado"] = ""
        with self.assertRaises(IncompleteTransitData):
            normalize("stc", rows)

    def test_snapshot_write_is_atomic_and_refuses_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "estado.json"
            old = "anterior"
            destination.write_text(old, encoding="utf-8")
            with self.assertRaises(IncompleteTransitData):
                write_snapshot({"status": "unavailable"}, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), old)
            payload = {
                "status": "ok",
                "operators": {
                    "stc": {"rows": normalize("stc", example("stc"))},
                    "mb": {"rows": normalize("mb", example("mb"))},
                },
            }
            write_snapshot(payload, destination)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"], "ok")

    def test_public_page_has_source_links_and_fail_closed_policy(self):
        page = (ROOT / "movilidad/index.html").read_text(encoding="utf-8")
        script = (ROOT / "assets/estado-transporte.js").read_text(encoding="utf-8")
        for expected in (
            'id="transport-live"', 'id="transport-grid"',
            'id="transport-updated"', 'id="transport-refresh"',
            'id="transport-stat-metro"', 'id="transport-stat-mb"',
            'data-transport-filter="mb"', '/assets/estado-transporte.js',
            '/assets/estado-transporte.css',
            'https://www.metro.cdmx.gob.mx/la-red/estado-del-servicio',
            'https://metrobus.cdmx.gob.mx/ServicioMB',
        ):
            self.assertIn(expected, page)
        for expected in (
            "const maximumAge=90*60*1000",
            "function isFresh(data)",
            "function isComplete(data)",
            "checked_at",
            "'/transporte/estado.json?v='",
            "textContent",
            "Sin verificación reciente",
        ):
            self.assertIn(expected, script)
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("localStorage", script)

    def test_initial_dataset_never_claims_real_incidents(self):
        data = json.loads((ROOT / "transporte/estado.json").read_text(encoding="utf-8"))
        self.assertIn(data["status"], {"ok", "unavailable"})
        if data["status"] == "unavailable":
            self.assertIsNone(data["checked_at"])
            self.assertEqual(data["operators"]["stc"]["rows"], [])
            self.assertEqual(data["operators"]["mb"]["rows"], [])


if __name__ == "__main__":
    unittest.main()
