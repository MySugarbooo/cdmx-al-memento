"""Calidad editorial: tesis con evidencia, fuentes claras y portada de noticias primero."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.analisis_editorial import build_editorial, choose_topic, THEMES

ROOT = Path(__file__).resolve().parent.parent

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

NOW=datetime(2026,10,13,11,0,tzinfo=timezone.utc)


def article(title, source, age=2, url="https://news.google.com/rss/articles/example"):
    return {
        "title":title, "source":source, "url":url,
        "published_at":(NOW-timedelta(hours=age)).isoformat().replace("+00:00","Z"),
        "category":"Metro",
    }


class EditorialTests(unittest.TestCase):
    def test_two_independent_sources_support_cautious_metro_thesis(self):
        rows=[
            article("Trabajadores del Metro advierten posible suspensión en Línea A","N+"),
            article("Piden rehabilitación de la Línea A del Metro CDMX","El Sol de México"),
        ]
        theme, sources=choose_topic(rows,NOW)
        self.assertEqual(theme["id"],"metro-a")
        self.assertEqual(len(sources),2)
        output=build_editorial(rows,NOW)
        for part in ("Tesis editorial","Qué aportan los titulares","Qué falta por comprobar",
                     "Nuestra opinión editorial","Conclusión razonada",
                     "Fuentes periodísticas relacionadas", "Metro CDMX"):
            self.assertIn(part,output)
        self.assertIn("N+",output)
        self.assertIn("El Sol de México",output)
        self.assertIn("no permiten afirmar un cierre efectivo",output)
        self.assertIn("no hemos",output)

    def test_one_source_is_never_construed_as_corroborration(self):
        rows=[
            article("Sindicato del Metro advierte cierre en Línea A","Un medio"),
            article("Línea A del Metro pendiente de rehabilitación","Un medio"),
        ]
        theme,_=choose_topic(rows,NOW)
        self.assertIsNone(theme)
        output=build_editorial(rows,NOW)
        self.assertIn("No detectamos al menos dos medios",output)
        self.assertIn("Tesis editorial",output)
        self.assertIn("opinión",output.lower())

    def test_outdated_and_bad_links_cannot_be_cited(self):
        rows=[
            article("Línea A del Metro en obras","Medio 1",age=55),
            article("Línea A del Metro, piden ajustes","Medio 2",url="https://unsafe.example"),
        ]
        theme,sources=choose_topic(rows,NOW)
        self.assertIsNone(theme)
        self.assertEqual(sources,[])
        self.assertIn("No hay suficientes fuentes",build_editorial(rows,NOW))

    def test_html_from_sources_is_escaped(self):
        rows=[
            article("Línea A del Metro con <script>alert(1)</script>","N+"),
            article("Línea A del Metro enfrenta dudas","Otro"),
        ]
        output=build_editorial(rows,NOW)
        self.assertNotIn("<script>",output)
        self.assertIn("&lt;script&gt;",output)

    def test_home_news_precede_side_features_and_report_is_linked(self):
        html=read("index.html")
        css=read("assets/explora.css")
        app=read("app.js")
        self.assertIn('class="explore-feature home-extras"',html)
        self.assertLess(html.index('id="portal-today-list"'),html.index('id="home-discover"'))
        self.assertLess(html.index('id="featured-grid"'),html.index('id="home-discover"'))
        self.assertLess(html.index('id="grid"'),html.index('id="home-discover"'))
        self.assertIn("id=\"editorial-latest-link\"",html)
        self.assertIn("editorialLatest.href=latest.url",app)
        self.assertIn(".home-extras-track",css)
        self.assertIn("overflow-x:auto",css)
        self.assertIn(".editorial-thesis",css)

    def test_daily_report_builder_and_transparency(self):
        generator=read("update_news.py")
        policy=read("politica-editorial.html")
        self.assertIn("build_editorial(rows, datetime.now(timezone.utc))",generator)
        self.assertIn("Análisis editorial",policy)
        self.assertIn("opinión",policy)
        self.assertIn("Fuentes",policy)
        self.assertIn("re.fullmatch",generator)


if __name__=="__main__":
    unittest.main()
