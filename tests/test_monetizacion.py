"""Comprobaciones de contenido original, igualdad territorial y SEO."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def txt(p):return (ROOT/p).read_text(encoding="utf-8")

class MonetizacionTests(unittest.TestCase):
    def test_guides_have_unique_pages_and_credits(self):
        data=json.loads(txt("assets/alcaldias/historias.json"))["boroughs"]
        photos=json.loads(txt("assets/alcaldias/fotos.json"))["photos"]
        self.assertEqual(len(data),16)
        self.assertEqual(len(photos),16)
        self.assertEqual(len(list((ROOT/"descubre").glob("*.html"))),17)
        for item in data:
            with self.subTest(borough=item["name"]):
                page=txt("descubre/"+item["slug"]+".html")
                self.assertIn(item["name"],page)
                self.assertIn("application/ld+json",page)
                self.assertIn("/assets/alcaldias/"+item["slug"]+".jpg",page)
                self.assertIn("Ver licencia y fotografía original",page)
                self.assertIn("Cómo planear tu visita",page)
                self.assertIn("Fuentes y contexto",page)
                self.assertIn(item["landmarks"][0],page)
                self.assertIn('rel="canonical"',page)
        hub=txt("descubre/index.html")
        for item in data:
            self.assertIn('href="/descubre/'+item["slug"]+'.html"',hub)

    def test_home_shows_each_borough_equally_and_new_sections(self):
        home=txt("index.html")
        self.assertEqual(home.count('class="alcaldia-card"'),16)
        self.assertNotIn('class="alcaldia-card principal"',home)
        for path in ("/descubre/","/agenda/","/negocios/","/herramientas/"):
            self.assertIn('href="'+path+'"',home)
        self.assertIn("CDMX PARA TODOS",home)
        self.assertLess(home.index("Álvaro Obregón"),home.index("La Magdalena Contreras"))

    def test_event_agenda_has_verified_dates_and_no_expired_cards(self):
        page=txt("agenda/index.html")
        manifest=json.loads(txt("agenda/eventos.json"))
        self.assertIn('id="agenda-borough"',page)
        self.assertIn('id="agenda-free"',page)
        self.assertIn('cartelera.cdmx.gob.mx',page)
        self.assertTrue(manifest["events"])
        for event in manifest["events"]:
            self.assertRegex(event["starts"],r"^\d{4}-\d{2}-\d{2}$")
            self.assertRegex(event["ends"],r"^\d{4}-\d{2}-\d{2}$")
            self.assertLessEqual(event["starts"],event["ends"])
            self.assertTrue(event["official"].startswith("https://"))
            self.assertIn(event["borough"],txt("assets/agenda.js"))
        js=txt("assets/agenda.js")
        self.assertIn("x.ends>=now",js)
        self.assertIn("No tenemos eventos con fecha",js)

    def test_market_directory_and_sponsorship_are_honest(self):
        html=txt("negocios/index.html")
        js=txt("assets/negocios.js")
        sponsor=txt("publicidad/index.html")
        self.assertIn('id="local-market-area"',html)
        self.assertIn("OpenStreetMap",html)
        self.assertIn("sedeco.cdmx.gob.mx",html)
        self.assertIn("mercados",html.lower())
        self.assertIn("16 alcaldías",html)
        self.assertIn("Mercado de San Juan",js)
        self.assertIn("boroughs=['Álvaro Obregón'",js)
        self.assertIn("Publicidad",sponsor)
        self.assertIn("Patrocinado",sponsor)
        self.assertIn("no significa que la cuenta esté aprobada",sponsor)

    def test_calculators_have_real_forms_and_official_sources(self):
        doc=txt("herramientas/index.html")
        js=txt("assets/herramientas.js")
        for name in ["aguinaldo","vacaciones","finiquito","ahorro","distancias"]:
            self.assertIn('id="tool-'+name+'"',doc)
            self.assertIn('id="tool-'+name+'-out"',doc)
        self.assertIn("profedet",doc.lower())
        self.assertIn("function vacations(years)",js)
        self.assertIn("daysInYear",js)
        self.assertIn("salary*15*days/total",js)
        self.assertIn("salary*days*(percentage/100)",js)
        self.assertIn("antes de impuestos",doc)

    def test_sitemap_and_robot_and_scripts(self):
        sitemap=txt("sitemap.xml")
        robots=txt("robots.txt")
        self.assertIn("Sitemap: https://cdmx-al-memento.pages.dev/sitemap.xml",robots)
        for path in ("/descubre/","/agenda/","/negocios/","/herramientas/","/publicidad/"):
            self.assertIn("https://cdmx-al-memento.pages.dev"+path,sitemap)
        for item in json.loads(txt("assets/alcaldias/historias.json"))["boroughs"]:
            self.assertIn("/descubre/"+item["slug"]+".html",sitemap)
        self.assertIn('src="/assets/clima-ticker.js?v=4"',txt("descubre/alvaro-obregon.html"))
        self.assertIn("descubre/",txt("update_news.py"))
        flow=txt(".github/workflows/news.yml")
        self.assertIn("python scripts/generar_guias.py",flow)
        self.assertIn("node --check assets/agenda.js",flow)
        self.assertIn("node --check assets/herramientas.js",flow)

if __name__=="__main__":unittest.main()
