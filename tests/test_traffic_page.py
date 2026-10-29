"""Etapa 7: pruebas estáticas de tráfico, fuentes, accesibilidad y seguridad.

Estas pruebas no afirman que un cierre se encuentre activo ni consultan la red.
El parser de noticias se prueba por separado en test_trafico_api.mjs.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class TrafficPageTests(unittest.TestCase):
    def test_page_contains_filters_and_sources(self):
        doc = read("trafico/index.html")
        for expected in [
            'id="traffic-list"', 'id="traffic-status"', 'id="traffic-type"',
            'id="traffic-borough"', 'id="traffic-search"', 'id="traffic-reload"',
            'id="traffic-more"', 'id="traffic-total"', 'id="traffic-last-checked"',
            'id="traffic-borough-count"', '/assets/trafico.css', '/assets/trafico.js',
            'https://x.com/OVIALCDMX', 'https://x.com/C5_CDMX',
            'https://www.ssc.cdmx.gob.mx/ciudadania/agenda-de-movilizaciones-sociales',
        ]:
            self.assertIn(expected, doc)
        self.assertIn('content="index,follow"', doc)

    def test_articles_are_not_described_as_live_traffic(self):
        page = read("trafico/index.html")
        script = read("assets/trafico.js")
        api = read("functions/api/trafico.js")
        self.assertIn("no acreditan por sí mismos que una calle siga cerrada", page)
        self.assertIn("no implica un cierre confirmado", page.lower().replace("implican", "implica"))
        self.assertIn("ventana de publicación: últimas 48 h.", script)
        self.assertIn("Una noticia no demuestra que siga existiendo un cierre", script)
        self.assertIn("Titulares periodísticos, NO cierres confirmados", api)
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("eval(", script)
        self.assertNotIn("localStorage", script)
        self.assertIn("const maxAge=48*60*60*1000", script)

    def test_index_links_and_fallback(self):
        client = read("assets/trafico.js")
        self.assertIn("'/api/trafico?t='", client)
        self.assertIn("'/news.json?t='", client)
        self.assertIn("function normalizeApi(data)", client)
        self.assertIn("function fromArchive(data)", client)
        self.assertIn("function allowedURL(value)", client)
        self.assertIn("new AbortController()", client)
        self.assertIn("new Intl.DateTimeFormat('es-MX'", client)
        self.assertIn("No encontramos titulares viales recientes verificables", client)

    def test_navigation_and_sitemap(self):
        for path in ["index.html", "movilidad/index.html", "avisos/index.html"]:
            self.assertIn('href="/trafico/"', read(path))
        self.assertIn("/trafico/", read("guias/cierres-viales.html"))
        self.assertIn('"trafico/"', read("update_news.py"))
        self.assertIn("https://cdmx-al-memento.pages.dev/trafico/</loc>", read("sitemap.xml"))
        self.assertIn("/trafico/\n  Cache-Control: no-cache, must-revalidate", read("_headers"))

    def test_automated_api_has_no_secrets_or_unrestricted_proxy(self):
        api = read("functions/api/trafico.js")
        self.assertIn("const SOURCES=[", api)
        self.assertIn("https://news.google.com/rss/search", api)
        self.assertIn("const CACHE_SECONDS=15*60", api)
        self.assertIn("const MAX_FETCH_MS=7500", api)
        self.assertIn("const MAX_AGE_MS=48*60*60*1000", api)
        self.assertIn("function linkSafe(url)", api)
        self.assertNotIn("request.url).searchParams.get('url')", api)
        self.assertNotIn("FIREBASE_ADMIN", api)
        self.assertNotIn("apiKey", api)


if __name__ == "__main__":
    unittest.main()
