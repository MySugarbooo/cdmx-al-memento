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

    def test_sensitive_story_hides_generic_representative_photo(self):
        item = {
            "title": "Caso Vadhir Derbez: Fiscalía CDMX tendría ADN relacionado con denuncia por violación",
            "category": "CDMX",
            "local_url": "/noticias/?id=15c774326c62e64d619e&mes=2026-11",
            "photo": {
                "url": "/assets/fotos/archivo_seguridad_003.jpg",
                "kind": "representativa",
                "author": "Gobierno de la Ciudad de México",
                "license": "CC BY 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Adquisici%C3%B3n_patrullas_para_la_Polic%C3%ADa_02.jpg",
            },
        }
        self.assertEqual(render_photo(item), "")
        page = render(item, "15c774326c62e64d619e")
        self.assertIn("Sin fotografía verificada del hecho", page)
        self.assertNotIn('src="/assets/fotos/archivo_seguridad_003.jpg"', page)
    def test_animal_cruelty_story_hides_generic_animal_photo(self):
        item = {
            "title": "Detienen a acusado de maltrato animal en Tlalpan",
            "category": "Seguridad",
            "local_url": "/noticias/?id=50c470b90270a39d9138&mes=2026-11",
            "photo": {
                "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/42/Animales_Bosque_de_Tlalpan_07.JPG/960px-Animales_Bosque_de_Tlalpan_07.JPG",
                "kind": "representativa",
                "author": "Inakiherrasti",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Animales_Bosque_de_Tlalpan_07.JPG",
            },
        }
        self.assertEqual(render_photo(item), "")
        page = render(item, "50c470b90270a39d9138")
        self.assertIn("Sin fotografía verificada del hecho", page)
        self.assertNotIn("Animales_Bosque_de_Tlalpan_07", page)


    def test_sensitive_story_allows_only_verified_event_photo(self):
        item = {
            "title": "Denuncia por violación: Fiscalía CDMX investiga",
            "photo": {
                "url": "/assets/fotos/archivo_seguridad_003.jpg",
                "kind": "hecho",
                "verified": True,
                "evidence_url": "https://example.org/evidence",
                "author": "Autor verificado",
                "license": "CC BY 4.0",
            },
        }
        self.assertIn('src="/assets/fotos/archivo_seguridad_003.jpg"', render_photo(item))

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
