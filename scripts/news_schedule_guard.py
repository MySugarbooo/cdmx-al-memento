"""Evita repetir la actualización de noticias cuando llegan cron de respaldo.

El feed se marca con UTC al inicio de cada generación. Los disparos schedule
se espacian cada 15 minutos; solo se ejecuta el pipeline si el feed tiene
50 minutos o más, falta o contiene una marca de tiempo inválida.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_AGE_MINUTES = 50
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M UTC"


def should_run(
    event_name: str,
    feed: object,
    now: datetime | None = None,
    max_age_minutes: int = MAX_AGE_MINUTES,
) -> bool:
    """Return whether this event should execute the news pipeline."""
    if event_name != "schedule":
        return True
    if not isinstance(feed, dict):
        return True

    updated_raw = feed.get("updated")
    if not isinstance(updated_raw, str):
        return True
    try:
        updated = datetime.strptime(updated_raw, TIMESTAMP_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return True

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age_seconds = (
        current.astimezone(timezone.utc) - updated
    ).total_seconds()
    # Una fecha futura puede indicar reloj desfasado: no bloquear la actualización.
    return age_seconds < 0 or age_seconds >= max_age_minutes * 60


def main() -> int:
    feed_path = ROOT / "news.json"
    try:
        feed = json.loads(feed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        feed = {}

    run_pipeline = should_run(os.getenv("GITHUB_EVENT_NAME", ""), feed)
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(
                f"should_run={'true' if run_pipeline else 'false'}\\n"
            )

    if run_pipeline:
        print("Actualización requerida: el feed está ausente, inválido o tiene 50 minutos o más.")
    else:
        print("Se omite este cron: news.json se actualizó hace menos de 50 minutos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
