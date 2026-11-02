"""Regresiones: fotografías locales en artículos HTML indexables."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_article_seo import render, render_photo


class ArticlePhotoTests(unittest.TestCase):
    def test_historic_airport_article_does_not_show_unrelated_monument(self):
        page = (Path(__file__).resolve().parents[1] /
                "articulos/16c3ecff879d86a90e17/index.html").read_text(encoding="utf-8")
        self.assertIn("Aeropuerto Internacional de la Ciudad de México", page)
        self.assertNotIn("Monumento_a_Col", page)
        self.assertIn("Sin fotografía del aeropuerto", page)

    def test_external_archive_article_is_not_labeled_as_cdmx(self):
        item = {
            "title": "Asamblea comunitaria determina relevo de autoridades auxiliares en Álvaro Obregón",
            "source": "Meganoticias.mx", "date": "2026-11-01",
            "local_url": "/noticias/?id=69e99bd8aec5a3438db7&mes=2026-11",
            "location": "Álvaro Obregón, Juchitán, Oaxaca (fuera de CDMX)",
            "category": "CDMX",
        }
        page = render(item, "69e99bd8aec5a3438db7")
        self.assertIn("Álvaro Obregón, Juchitán, Oaxaca (fuera de CDMX) · 2026-11-01", page)
        self.assertNotIn("<p>CDMX · 2026-11-01", page)
        item["location"] = "Coyoacán (mencionada en el titular)"
        self.assertIn("<p>CDMX · 2026-11-01", render(item, "69e99bd8aec5a3438db7"))

    def test_local_photo_keeps_credits(self):
        html = render_photo({"category": "Seguridad", "photo": {
            "url": "/assets/fotos/seguridad.jpg", "kind": "representativa",
            "author": "Autor de prueba", "license": "CC BY 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/"}})
        self.assertIn('src="/assets/fotos/seguridad.jpg"', html)
        self.assertIn("Imagen representativa", html)
        self.assertIn("Autor de prueba", html)
        self.assertIn("CC BY 4.0", html)

    def test_borough_photo(self):
        self.assertIn('src="/assets/alcaldias/azcapotzalco.jpg"',
                      render_photo({"photo": {"url": "/assets/alcaldias/azcapotzalco.jpg"}}))

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
