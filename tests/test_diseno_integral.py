"""Pruebas de regresión del diseño editorial y navegación de CDMX AL MEMENTO."""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NOTICE = "Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos."


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class DesignAuditRegressionTests(unittest.TestCase):
    def test_html_main_balanced_in_key_sections(self):
        for page in (
            "index.html", "noticias/index.html", "seguridad/index.html",
            "servicios/index.html", "fotografias/index.html",
            "comunidad/index.html", "alcaldias/index.html",
        ):
            with self.subTest(page=page):
                content = read(page)
                self.assertEqual(len(re.findall(r"<main\\b", content)), 1)
                self.assertEqual(len(re.findall(r"</main\\s*>", content)), 1)

    def test_visible_non_js_header_fallbacks(self):
        for page in ("seguridad/index.html", "servicios/index.html", "fotografias/index.html"):
            with self.subTest(page=page):
                self.assertNotIn("<header></header>", read(page))
                self.assertIn('aria-label="Secciones principales"', read(page))

    def test_no_second_banner_over_existing_headline(self):
        code = read("assets/page-transitions.js")
        self.assertIn("if(!main.querySelector('h1", code)
        self.assertIn("main.prepend(banner)", code)

    def test_phone_dock_and_tablet_sidebar(self):
        home = read("index.html")
        css = read("assets/neo-home.css")
        self.assertIn('class="neo-dock"', home)
        self.assertIn("max-width:1040px", home)
        self.assertIn(".neo-right-column", home)
        self.assertIn(".neo-dock{display:flex", css)
        self.assertIn("Restricción por color", home)
        self.assertIn("Toca restricción", home)

    def test_legible_credits_and_accessible_gallery(self):
        home = read("index.html")
        gallery = read("fotografias/index.html")
        self.assertIn(".neo-credit{font-size:12px", home)
        self.assertIn("max-width:620px", gallery)
        self.assertIn("neo-photo-skeleton", gallery)
        self.assertIn("neo-photo-search", read("assets/neo-gallery.js"))

    def test_photo_sources_and_fast_news_index(self):
        full = json.loads(read("assets/fotos/catalogo-editorial-1100.json"))
        quick = json.loads(read("assets/fotos/indice-noticias-1100.json"))
        self.assertGreater(len(full["photos"]), 900)
        self.assertEqual(full["count"], quick["count"])
        self.assertEqual(
            {p["id"] for p in full["photos"]},
            {p["id"] for p in quick["photos"]},
        )
        self.assertLess(len(json.dumps(quick)), len(json.dumps(full)))
        self.assertIn("indice-noticias-1100.json", read("assets/fotos.js"))

    def test_illustrative_legend_and_author_credit(self):
        for path in ("assets/neo-gallery.js", "assets/neo-home.js",
                     "assets/noticias-locales.js", "assets/neo-sections.js"):
            with self.subTest(path=path):
                self.assertIn(NOTICE, read(path))
        self.assertIn("photo.author", read("assets/neo-sections.js"))
        self.assertIn("photo.license", read("assets/neo-sections.js"))

    def test_shared_theme_and_optional_navigation_overflow_hint(self):
        core = read("assets/neo-site.css")
        self.assertIn("Capa editorial unificada", core)
        self.assertIn("#080e18", core)
        self.assertIn("neo-global-nav::after", core)
        self.assertIn("neo-inner-dock", core)


if __name__ == "__main__":
    unittest.main()
