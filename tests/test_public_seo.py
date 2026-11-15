"""Regression tests for the public SEO/deployment checker."""
import unittest
from pathlib import Path

from scripts.check_public_seo import (
    DEPLOY_ATTEMPTS,
    ARCHIVE_ARTICLE_SAMPLE_SIZE,
    article_targets,
    archive_records,
    homepage_script_source,
    public_photo_count,
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

    def test_article_targets_cover_all_feed_and_recent_archive_items(self):
        feed = []
        for index in range(5):
            article = self.valid_article()
            article["local_url"] = f"/noticias/?id={index:020x}&mes=2026-11"
            feed.append(article)
        archive = []
        for index in range(100):
            article = self.valid_article()
            article["local_url"] = f"/noticias/?id={index + 100:020x}&mes=2026-11"
            archive.append(article)
        targets = article_targets(feed, archive)
        target_ids = {article_id(item) for item in targets}
        self.assertEqual(len(targets), 105)
        self.assertIn(article_id(feed[4]), target_ids)
        self.assertIn(article_id(archive[83]), target_ids)
        self.assertEqual(ARCHIVE_ARTICLE_SAMPLE_SIZE, 100)

    def test_article_html_rejects_photo_when_main_has_none(self):
        article = self.valid_article()
        article["photo"] = None
        page = (
            "<h1>Aviso de movilidad en Cablebús Línea 1</h1>"
            "<p>Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús) · "
            "2026-11-12 · Fuente: N+</p>"
            '<figure class="article-photo"><img src="/assets/fotos/incorrecta.jpg"></figure>'
        )
        with self.assertRaisesRegex(ValueError, "fotografía"):
            validate_article_html(article, page.encode("utf-8"))

    def test_article_html_rejects_a_different_assigned_photo_url(self):
        article = self.valid_article()
        page = (
            "<h1>Aviso de movilidad en Cablebús Línea 1</h1>"
            "<p>Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús) · "
            "2026-11-12 · Fuente: N+</p>"
            '<figure class="article-photo"><img src="https://upload.wikimedia.org/other.jpg">'
            "<figcaption>Sistema de Transporte Público Cablebús · CC BY 4.0</figcaption></figure>"
        )
        with self.assertRaisesRegex(ValueError, "URL asignada"):
            validate_article_html(article, page.encode("utf-8"))

    def test_article_html_allows_no_photo_when_main_has_none(self):
        article = self.valid_article()
        article["photo"] = None
        page = (
            "<h1>Aviso de movilidad en Cablebús Línea 1</h1>"
            "<p>Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús) · "
            "2026-11-12 · Fuente: N+</p>"
        )
        self.assertTrue(validate_article_html(article, page.encode("utf-8")))

    def test_article_html_requires_exact_location_and_photo_credits(self):
        article = self.valid_article()
        html = (
            "<p>Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús) · "
            "2026-11-12 · Fuente: N+</p><h1>Aviso de movilidad en Cablebús Línea 1</h1>"
            '<figure class="article-photo"><img src="https://upload.wikimedia.org/example.jpg">'
            "<figcaption>Sistema de Transporte Público Cablebús · CC BY 4.0</figcaption></figure>"
        )
        self.assertTrue(validate_article_html(article, html.encode("utf-8")))
        with self.assertRaisesRegex(ValueError, "location"):
            validate_article_html(article, html.replace("Gustavo A. Madero, ", "").encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "license"):
            validate_article_html(article, html.replace("CC BY 4.0", "").encode("utf-8"))

    def test_sensitive_article_without_photo_requires_notice(self):
        article = self.valid_article()
        article["title"] = "Detienen a presunto maltratador de animales"
        article["location"] = "Tlalpan"
        article["date"] = "2026-11-12"
        article["source"] = "Medio"
        article["sensitive_media"] = True
        article["photo"] = {
            "kind": "representativa",
            "url": "/assets/fotos/archivo_seguridad_003.jpg",
            "author": "Autor de archivo",
            "license": "CC BY 4.0",
        }
        page = (
            "<h1>Detienen a presunto maltratador de animales</h1>"
            "<p>Tlalpan · 2026-11-12 · Fuente: Medio</p>"
            "<p>Sin fotografía verificada del hecho</p>"
        )
        self.assertTrue(validate_article_html(article, page.encode("utf-8")))
        with self.assertRaisesRegex(ValueError, "aviso"):
            validate_article_html(
                article,
                (
                    "<h1>Detienen a presunto maltratador de animales</h1>"
                    "<p>Tlalpan · 2026-11-12 · Fuente: Medio</p>"
                ).encode("utf-8"),
            )
        with self.assertRaisesRegex(ValueError, "no autorizada"):
            validate_article_html(
                article,
                (
                    "<h1>Detienen a presunto maltratador de animales</h1>"
                    "<p>Tlalpan · 2026-11-12 · Fuente: Medio</p>"
                    "<p>Sin fotografía verificada del hecho</p>"
                    '<figure class="article-photo"><img src="/assets/fotos/incorrecta.jpg"></figure>'
                ).encode("utf-8"),
            )

    def test_public_photo_count_matches_the_merged_credit_catalog(self):
        root = Path(__file__).resolve().parents[1]
        count = public_photo_count()
        page = (root / "creditos-fotograficos.html").read_text(encoding="utf-8")
        self.assertIn(f"Fototeca editorial: {count:,} imágenes", page)
        self.assertIn(f"La biblioteca reúne {count:,} imágenes", page)

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
        self.assertIn("function articleRouteId(x)", script)
        self.assertIn("archiveMonth===month&&archive?archive:await readJSON", script)
        self.assertIn("movedItems.find(x=>articleRouteId(x)===id)", script)

    def test_moved_article_comment_aliases_share_the_original_collection(self):
        root = Path(__file__).resolve().parent.parent
        script = (root / "assets" / "comments.js").read_text(encoding="utf-8")
        self.assertIn("fetch('/archivo/rutas.json',{cache:'no-store'})", script)
        self.assertIn("routeIndex?.comment_months?.[id]", script)
        self.assertIn("commentsMonth+'_'+id", script)
        for relative in ("noticias/index.html", "comunidad/index.html"):
            page = (root / relative).read_text(encoding="utf-8")
            self.assertIn("/assets/comments.js?v=17-route-month-alias", page)

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
