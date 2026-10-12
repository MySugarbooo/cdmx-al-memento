"""Comprueba que las 16 alcaldías tengan historia, foto real y enlace directo."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets" / "alcaldias"
NAMES = [
    "La Magdalena Contreras", "Álvaro Obregón", "Azcapotzalco", "Benito Juárez",
    "Coyoacán", "Cuajimalpa de Morelos", "Cuauhtémoc", "Gustavo A. Madero",
    "Iztacalco", "Iztapalapa", "Miguel Hidalgo", "Milpa Alta", "Tláhuac",
    "Tlalpan", "Venustiano Carranza", "Xochimilco",
]


class ProfileTests(unittest.TestCase):
    def test_16_distinct_histories_with_sources(self):
        stories = json.loads((BASE / "historias.json").read_text(encoding="utf-8"))["boroughs"]
        self.assertEqual([p["name"] for p in stories], NAMES)
        self.assertEqual(len({p["slug"] for p in stories}), 16)
        for item in stories:
            self.assertGreaterEqual(len(item["history"]), 2)
            self.assertGreaterEqual(len(item["landmarks"]), 2)
            self.assertTrue(item["sources"])
            self.assertTrue(all(link["url"].startswith("https://") for link in item["sources"]))

    def test_16_verified_distinct_location_photos(self):
        photos = json.loads((BASE / "fotos.json").read_text(encoding="utf-8"))["photos"]
        self.assertEqual([p["name"] for p in photos], NAMES)
        self.assertEqual(len({p["source"] for p in photos}), 16)
        for p in photos:
            image = BASE / (p["slug"] + ".jpg")
            self.assertTrue(image.is_file(), str(image))
            self.assertGreater(image.stat().st_size, 4000)
            self.assertIn("commons.wikimedia.org/wiki/File:", p["source"])
            self.assertTrue(p["author"])
            self.assertTrue(p["license"])

    def test_news_navigation_without_old_grid(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        html = (ROOT / "alcaldias" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "assets" / "hemeroteca.js").read_text(encoding="utf-8")
        self.assertEqual(home.count("#noticias-alcaldia"), 16)
        self.assertIn('id="noticias-alcaldia"', html)
        self.assertIn('id="borough-results"', html)
        self.assertIn('id="borough-photo"', html)
        self.assertIn('id="borough-history-text"', html)
        self.assertIn('id="borough-selector"', html)
        self.assertNotIn('id="borough-directory"', html)
        self.assertIn("url.hash='#noticias-alcaldia'", js)


if __name__ == "__main__":
    unittest.main()
