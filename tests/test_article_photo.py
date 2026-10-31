"""Regresiones: fotografías locales en artículos HTML indexables."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_article_seo import render_photo


class ArticlePhotoTests(unittest.TestCase):
    def test_local_photo_keeps_credits(self):
        html = render_photo({"category": "Seguridad", "photo": {
            "url": "/assets/fotos/seguridad.jpg", "kind": "representativa",
            "author": "Autor de prueba", "license": "CC BY 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/"}})
        self.assertIn('src="/assets/fotos/seguridad.jpg"', html)
        self.assertIn("Imagen representativa", html)
        self.assertIn("Autor de prueba", html)
        self.assertIn("CC BY 4.0", html)

    def test_https_remote_photo(self):
        self.assertIn('src="https://example.org/image.jpg"',
                      render_photo({"photo": {"url": "https://example.org/image.jpg"}}))

    def test_unsafe_local_urls_rejected(self):
        for url in ("//example.org/x.jpg", "/assets/fotos/../secret.txt",
                    "/assets/fotos/x.jpg?redirect=1", "javascript:alert(1)",
                    "/other/x.jpg"):
            with self.subTest(url=url):
                self.assertEqual(render_photo({"photo": {"url": url}}), "")


if __name__ == "__main__":
    unittest.main()
