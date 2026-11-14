"""Regression tests for the public SEO/deployment checker."""
import unittest
from pathlib import Path

from scripts.check_public_seo import (
    DEPLOY_ATTEMPTS,
    archive_records,
    homepage_script_source,
    article_id,
    parse_sitemap,
    validate_article_html,
    validate_feed,
)


class PublicSeoTests(unittest.TestCase):
    def valid_article(self):
        return {
            "title": "Aviso de movilidad en Cablebús Línea 1",
            "url": "https://news.google.com/rss/articles/test",
            "source": "N+",
            "date": "2026-11-12",
            "category": "Movilidad",
            "location": "Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús)",
            "local_url": "/noticias/?id=0123456789abcdefabcd&mes=2026-11",
            "photo": {
                "url": "https://upload.wikimedia.org/example.jpg",
                "author": "Sistema de Transporte Público Cablebús",
                "license": "CC BY 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
                "source": "https://commons.wikimedia.org/wiki/File:Example.jpg",
            },
        }

    def test_feed_requires_unique_links_and_complete_photo_credits(self):
        feed = {"updated": "2026-11-12 23:01 UTC", "articles": [self.valid_article()]}
        self.assertEqual(len(validate_feed(feed)), 1)
        duplicate = self.valid_article()
        feed["articles"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicados"):
            validate_feed(feed)

    def test_feed_rejects_incomplete_photo_attribution(self):
        article = self.valid_article()
        article["photo"].pop("licenseUrl")
        with self.assertRaisesRegex(ValueError, "licenseUrl"):
            validate_feed({"updated": "now", "articles": [article]})

    def test_archive_records_supports_list_and_wrapped_objects(self):
        self.assertEqual(len(archive_records([{"id": "a"}])), 1)
        self.assertEqual(len(archive_records({"articles": [{"id": "a"}, {"id": "b"}]})), 2)
        with self.assertRaises(ValueError):
            archive_records({"unexpected": []})

    def test_article_id_requires_a_valid_local_news_link(self):
        self.assertEqual(
            article_id(self.valid_article()),
            "0123456789abcdefabcd",
        )
        self.assertIsNone(article_id({"local_url": "/noticias/?id=bad"}))

    def test_article_html_requires_exact_location_and_photo_credits(self):
        article = self.valid_article()
        html = (
            "<p>Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús) · "
            "2026-11-12 · Fuente: N+</p><h1>Aviso de movilidad en Cablebús Línea 1</h1>"
            "<figcaption>Sistema de Transporte Público Cablebús · CC BY 4.0</figcaption>"
        )
        self.assertTrue(validate_article_html(article, html.encode("utf-8")))
        with self.assertRaisesRegex(ValueError, "location"):
            validate_article_html(article, html.replace("Gustavo A. Madero, ", "").encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "license"):
            validate_article_html(article, html.replace("CC BY 4.0", "").encode("utf-8"))

    def test_sensitive_article_without_photo_requires_notice(self):
        article = {
            "title": "Detienen a presunto maltratador de animales",
            "source": "Medio",
            "date": "2026-11-12",
            "location": "Tlalpan",
            "sensitive_media": True,
        }
        self.assertTrue(
            validate_article_html(
                article,
                (
                    "<h1>Detienen a presunto maltratador de animales</h1>"
                    "<p>Tlalpan · 2026-11-12 · Fuente: Medio</p>"
                    "<p>Sin fotografía verificada del hecho</p>"
                ).encode("utf-8"),
            )
        )
        with self.assertRaisesRegex(ValueError, "aviso"):
            validate_article_html(
                article,
                (
                    "<h1>Detienen a presunto maltratador de animales</h1>"
                    "<p>Tlalpan · 2026-11-12 · Fuente: Medio</p>"
                ).encode("utf-8"),
            )

    def test_deployment_wait_and_homepage_script_match_main(self):
        self.assertEqual(DEPLOY_ATTEMPTS, 36)
        source, content = homepage_script_source()
        self.assertRegex(source, r"^/assets/neo-home\.js\?v=[a-zA-Z0-9_-]+$")
        self.assertIn(b"function isWeatherForecastOnly(article)", content)

    def test_moved_article_routes_use_archive_route_index(self):
        script = (Path(__file__).resolve().parent.parent / "assets" / "noticias-locales.js").read_text(encoding="utf-8")
        self.assertIn("readJSON('/archivo/rutas.json')", script)
        self.assertIn("routeIndex?.routes?.[id]", script)
        self.assertIn("'/archivo/'+archiveMonth+'.json'", script)

    def test_moved_story_prefers_its_verified_direct_source_url(self):
        script = (Path(__file__).resolve().parent.parent / "assets" / "noticias-locales.js").read_text(encoding="utf-8")
        self.assertIn("article.source_url||article.url", script)
        self.assertIn("www.hoytamaulipas.net", script)

    def test_sitemap_requires_unique_same_domain_urls(self):
        xml = (
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "<url><loc>https://cdmx-al-memento.pages.dev/articulos/abc/</loc></url>"
            "</urlset>"
        )
        self.assertEqual(
            parse_sitemap(xml.encode("utf-8"), "test sitemap"),
            {"https://cdmx-al-memento.pages.dev/articulos/abc/"},
        )
        external = xml.replace("cdmx-al-memento.pages.dev", "example.org")
        with self.assertRaisesRegex(ValueError, "fuera del dominio"):
            parse_sitemap(external.encode("utf-8"), "test sitemap")


if __name__ == "__main__":
    unittest.main()
