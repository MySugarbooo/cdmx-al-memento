"""Validar renovación de fotos, licencias y precisión de atribuciones."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import actualizar_fotos as photos


def sample_page(title="File:Metro Ciudad de México 2026.jpg", uploaded="2026-10-11T18:00:00Z",
                taken="2026-10-11 11:00:00", license_name="CC BY-SA 4.0"):
    return {
        "title": title,
        "imageinfo": [{
            "timestamp": uploaded,
            "width": 1500,
            "height": 1000,
            "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/example.jpg/1100px-example.jpg",
            "descriptionurl": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
            "extmetadata": {
                "Artist": {"value": '<a href="/wiki/User:Example">Autora de prueba</a>'},
                "LicenseShortName": {"value": license_name},
                "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
                "DateTimeOriginal": {"value": taken},
            },
        }],
    }


class RecentPhotoTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 12, 14, tzinfo=timezone.utc)

    def test_license_and_attribution(self):
        meta = sample_page()["imageinfo"][0]["extmetadata"]
        self.assertEqual(photos.licensed(meta)[0], "CC BY-SA 4.0")
        self.assertEqual(photos.clean_html(meta["Artist"]["value"]), "Autora de prueba")
        meta["LicenseShortName"]["value"] = "CC BY-NC 4.0"
        self.assertIsNone(photos.licensed(meta))

    def test_location_required_and_wrong_cities_rejected(self):
        self.assertTrue(photos.matches_place("Metro Ciudad de México 2026.jpg", "Metro"))
        self.assertFalse(photos.matches_place("Metro Louisville Kentucky.jpg", "Metro"))
        self.assertFalse(photos.matches_place("Palace of Fine Arts San Francisco.jpg", "Gobierno"))
        self.assertFalse(photos.matches_place("Random station.jpg", "Metro"))

    def test_timestamp_is_upload_not_capture(self):
        recent = photos.candidate(sample_page(), "Metro", self.now)
        self.assertEqual(recent["uploaded_at"], "2026-10-11")
        self.assertEqual(recent["captured_at"], "2026-10-11")
        self.assertIn("upload.wikimedia.org", recent["url"])
        old_photo = sample_page(taken="2013-01-10 12:00:00")
        self.assertIsNone(photos.candidate(old_photo, "Metro", self.now))
        old_upload = sample_page(uploaded="2020-01-01T12:00:00Z")
        self.assertIsNone(photos.candidate(old_upload, "Metro", self.now))

    def test_update_is_daily_and_avoids_breakage_on_failure(self):
        with TemporaryDirectory() as folder:
            dest = Path(folder) / "recientes.json"
            with patch.object(photos, "DEST", dest):
                with patch.object(photos, "QUERIES", {"Metro": ("Metro CDMX",)}):
                    with patch.object(photos, "request_photos", return_value=[sample_page()]) as get:
                        output = photos.update(self.now)
                        self.assertEqual(len(output["photos"]), 1)
                        self.assertEqual(get.call_count, 1)
                        same = photos.update(self.now + timedelta(minutes=15))
                        self.assertEqual(same["photos"], output["photos"])
                        self.assertEqual(get.call_count, 1)
                    with patch.object(photos, "request_photos", side_effect=OSError("offline")):
                        retry = photos.update(self.now + timedelta(days=2), force=True)
                        self.assertEqual(retry["photos"], output["photos"])

    def test_site_uses_image_manifest_and_fallbacks(self):
        base = Path(__file__).resolve().parent.parent
        js = (base / "assets/fotos.js").read_text(encoding="utf-8")
        app = (base / "app.js").read_text(encoding="utf-8")
        workflow = (base / ".github/workflows/news.yml").read_text(encoding="utf-8")
        self.assertIn("addRecentCatalog(catalog)", js)
        self.assertIn("candidatesForArticle", js)
        self.assertIn("refreshStaticPhotos()", app)
        self.assertIn("fetch('/assets/fotos/recientes.json?t='", app)
        self.assertIn("python scripts/actualizar_fotos.py", workflow)
        self.assertIn("assets/fotos/recientes.json", workflow)
        self.assertIn("fotografías de contexto", (base / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
