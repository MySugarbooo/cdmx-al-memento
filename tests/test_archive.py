"""Pruebas básicas del archivo de un año y metadatos editoriales."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import update_news as news


def fake(title, date, published_at=None):
    return {
        "title": title, "source": "Medio de prueba",
        "url": "https://news.google.com/rss/articles/example" + date.replace("-", ""),
        "date": date, "published_at": published_at,
        "category": "CDMX",
    }


class BoroughAndArchiveTests(unittest.TestCase):
    def test_first_boroughs_and_exact_mentions(self):
        self.assertEqual(news.BOROUGHS[:2], ("La Magdalena Contreras", "Álvaro Obregón"))
        self.assertEqual(news.identify_location("Noticias en Magdalena Contreras")[0], "La Magdalena Contreras")
        self.assertEqual(news.identify_location("Cierre vial en Álvaro Obregón CDMX")[0], "Álvaro Obregón")
        self.assertEqual(news.identify_location("Incidente en Iztapalapa")[0], "Iztapalapa")
        self.assertEqual(news.identify_location("En Coyoacán y Tlalpan")[0], "")
        self.assertEqual(news.identify_location("Los planes del Metro CDMX")[0], "")

    def test_source_time_is_real_or_missing(self):
        now="2026-10-11T23:40:00Z"
        article=news.standardize(fake("Una noticia sobre Xochimilco en CDMX", "2026-10-11", now))
        self.assertEqual(article["published_at"], now)
        self.assertEqual(article["borough"], "Xochimilco")
        self.assertEqual(article["date"], "2026-10-11")
        legacy=news.standardize(fake("Una noticia sobre Xochimilco en CDMX", "2026-10-11"))
        self.assertIsNone(legacy["published_at"])
        self.assertEqual(legacy["location"], "Xochimilco (mencionada en el titular)")

    def test_older_than_365_days_expires_even_within_month(self):
        now=datetime.now(timezone.utc)
        cutoff=now-timedelta(days=365)
        expired=(now-timedelta(days=366)).date().isoformat()
        kept=(now-timedelta(days=364)).date().isoformat()
        old=news.standardize(fake("Titular antiguo del Metro CDMX", expired))
        current=news.standardize(fake("Titular reciente en Xochimilco", kept))
        self.assertFalse(news.still_valid(old, cutoff))
        self.assertTrue(news.still_valid(current, cutoff))

    def test_months_merge_and_old_files_deleted(self):
        now=datetime.now(timezone.utc)
        date=(now-timedelta(days=1)).date().isoformat()
        earlier=(now-timedelta(days=400)).date().isoformat()
        story=news.standardize(fake("Reunión comunitaria en Magdalena Contreras", date))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/"archivo"
            archive.mkdir()
            # Un archivo de un mes vencido no debe mantenerse.
            news.write_json(archive/(earlier[:7]+".json"), {
                "month":earlier[:7],
                "articles":[news.standardize(fake("Información vencida en CDMX", earlier))]
            })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root/"alcaldias", DEST=root/"news.json"):
                months=news.consolidate_archive([story], now-timedelta(days=365), "Prueba")
                self.assertEqual(len(months), 1)
                self.assertEqual(months[0]["month"], date[:7])
                self.assertFalse((archive/(earlier[:7]+".json")).exists())
                saved=json.loads((archive/(date[:7]+".json")).read_text(encoding="utf-8"))
                self.assertEqual(len(saved["articles"]), 1)
                self.assertEqual(saved["articles"][0]["borough"], "La Magdalena Contreras")
                directory=json.loads((root/"alcaldias"/"noticias.json").read_text(encoding="utf-8"))
                self.assertEqual(len(directory["boroughs"]), 16)


if __name__ == "__main__":
    unittest.main()
