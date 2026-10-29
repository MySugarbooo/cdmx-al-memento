"""Pruebas de humo para la sección Noticias en desarrollo."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DevelopmentNewsTests(unittest.TestCase):
    def test_page_and_assets_exist(self):
        page = (ROOT / "noticias-en-desarrollo/index.html").read_text(encoding="utf-8")
        self.assertIn('id="dev-timeline"', page)
        self.assertIn('id="dev-status"', page)
        self.assertIn('id="dev-category"', page)
        self.assertIn('id="dev-search"', page)
        self.assertIn('/assets/noticias-en-desarrollo.js', page)
        self.assertIn('/assets/noticias-en-desarrollo.css', page)

    def test_story_links_are_local_and_source_links_are_restricted(self):
        script = (ROOT / "assets/noticias-en-desarrollo.js").read_text(encoding="utf-8")
        self.assertIn("/news.json?t=", script)
        self.assertIn("news.google.com", script)
        self.assertIn("textContent", script)
        self.assertNotIn("innerHTML", script)
        self.assertIn("noopener noreferrer", script)

    def test_news_catalog_has_expected_structure(self):
        catalog = json.loads((ROOT / "news.json").read_text(encoding="utf-8"))
        self.assertIsInstance(catalog.get("articles"), list)
        for article in catalog["articles"][:5]:
            self.assertIsInstance(article.get("title"), str)
            self.assertIsInstance(article.get("source"), str)
            self.assertIsInstance(article.get("local_url"), str)


if __name__ == "__main__":
    unittest.main()
