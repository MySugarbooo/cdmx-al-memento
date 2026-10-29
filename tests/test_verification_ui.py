"""Pruebas de las fichas de verificación de las noticias."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VerificationUiTests(unittest.TestCase):
    def test_news_page_loads_verification_style_and_script(self):
        markup = (ROOT / "noticias/index.html").read_text(encoding="utf-8")
        self.assertIn("/assets/verificacion.css", markup)
        self.assertIn("/assets/noticias-locales.js", markup)

    def test_facts_are_not_labeled_verified_without_evidence(self):
        script = (ROOT / "assets/noticias-locales.js").read_text(encoding="utf-8")
        self.assertIn("Ficha de verificación", script)
        self.assertIn("Verificación independiente pendiente", script)
        self.assertIn("no equivale a confirmar los hechos", script)
        self.assertIn("archive.updated", script)
        self.assertIn("current.updated", script)
        self.assertIn("safeExternal(article.url)", script)


if __name__ == "__main__":
    unittest.main()
