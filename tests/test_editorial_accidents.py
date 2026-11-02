"""Pruebas de publicación editorial para accidentes cotejados con sus fuentes."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import update_news as news
from scripts import notas_locales as photos


class VerifiedAccidentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = json.loads(news.CURATED_INCIDENTS.read_text(encoding="utf-8"))["articles"]

    def test_six_reports_have_sources_and_original_summaries(self):
        self.assertEqual(len(self.records), 6)
        for record in self.records:
            with self.subTest(title=record["title"]):
                self.assertIs(record["editorial_verified"], True)
                self.assertIs(record["sensitive_media"], True)
                self.assertEqual(record["category"], "Movilidad")
                self.assertTrue(record["source"])
                self.assertTrue(record["brief"]["lead"])
                self.assertTrue(record["brief"]["context"])
                self.assertTrue(record["brief"]["pending"])
                self.assertTrue(record["brief"]["method"])
                item = news.standardize(record)
                self.assertIsNotNone(item)
                self.assertEqual(item["brief"]["lead"], record["brief"]["lead"])
                self.assertEqual(item["editorial_verified"], True)
                self.assertRegex(item["local_url"], r"^/noticias/\?id=[a-f0-9]{20}&mes=2026-(10|11)$")
                self.assertEqual(news.standardize(item)["brief"], item["brief"])

    def test_other_external_links_cannot_enter_unreviewed_feed(self):
        good = self.records[0]
        self.assertTrue(news.valid_link(good["url"], True))
        self.assertFalse(news.valid_link(good["url"], False))
        self.assertFalse(news.valid_link("https://untrusted.example/story", True))
        self.assertFalse(news.valid_link("http://comova.mx/story", True))
        self.assertFalse(news.valid_link("https://comova.mx@untrusted.example/story", True))
        self.assertIsNone(news.standardize({**good, "editorial_verified": False}))

    def test_sensitive_report_discards_legacy_unverified_photo(self):
        raw = dict(self.records[0])
        raw["photo"] = {
            "id": "foto_ajena", "kind": "representativa",
            "topic": "Patrullas en Ciudad de México",
            "url": "/assets/fotos/foto_ajena.jpg",
        }
        cleaned = news.standardize(raw)
        self.assertNotIn("photo", cleaned)
        self.assertIs(cleaned["sensitive_media"], True)

    def test_sensitive_report_never_receives_unrelated_context_photo(self):
        article = news.standardize(self.records[0])
        police_photo = {
            "id": "patrulla", "category": "Movilidad", "kind": "representativa",
            "topic": "Un vehículo en la Ciudad de México", "url": "/assets/fotos/patrulla.jpg",
        }
        with patch.object(photos, "_pool", return_value=[police_photo]), patch.object(
            photos, "verified_event_photo", return_value=None
        ):
            photos.assign_photos([article])
        self.assertNotIn("photo", article)

    def test_recent_verified_incident_is_visible_but_old_incident_is_not_pinned(self):
        now = datetime.now(timezone.utc)
        items = [{
            "title": f"Noticia general en CDMX {i}",
            "date": now.date().isoformat(),
            "url": f"https://news.google.com/rss/articles/item{i}",
            "published_at": (now - timedelta(minutes=i)).isoformat(),
        } for i in range(60)]
        recent = {
            "title": "Accidente vial cotejado",
            "editorial_verified": True,
            "date": now.date().isoformat(),
            "url": "https://comova.mx/aviso/accidente-verificado/",
            "published_at": (now - timedelta(hours=30)).isoformat(),
        }
        stale = {
            **recent, "url": "https://comova.mx/aviso/accidente-vencido/",
            "published_at": (now - timedelta(days=4)).isoformat(),
        }
        visible = news.homepage_articles(items, [recent, stale], now)
        self.assertEqual(len(visible), 60)
        self.assertIn(recent["url"], [entry["url"] for entry in visible])
        self.assertNotIn(stale["url"], [entry["url"] for entry in visible])

    def test_unphotographed_curated_incident_stays_in_archive_not_portada(self):
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        stamp = now.isoformat(timespec="seconds")
        sample = {
            **self.records[0], "date": today, "published_at": stamp,
        }
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            registry = folder / "editorial.json"
            registry.write_text(json.dumps({"articles": [sample]}), encoding="utf-8")
            with patch.multiple(news, DEST=folder / "news.json",
                                ARCHIVE_DIR=folder / "archivo",
                                BOROUGH_DIR=folder / "alcaldias",
                                CURATED_INCIDENTS=registry):
                with patch.object(news, "gather", return_value=[]):
                    news.update()
                current = json.loads((folder / "news.json").read_text(encoding="utf-8"))
                archive = json.loads((folder / "archivo" / (today[:7] + ".json")).read_text(encoding="utf-8"))
                # Una noticia sin imagen comprobada se conserva como antecedente,
                # pero no se publica en la portada con una foto genérica.
                self.assertEqual(len(current["articles"]), 0)
                self.assertEqual(len(archive["articles"]), 1)
                self.assertTrue(archive["articles"][0]["editorial_verified"])
                self.assertEqual(archive["articles"][0]["brief"]["lead"], sample["brief"]["lead"])


if __name__ == "__main__":
    unittest.main()
