"""Etapa 8: regresiones estáticas de Aire CDMX y 16 pronósticos."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


class AirPageTests(unittest.TestCase):
    def test_html_has_source_disclosure_and_interface(self):
        html = read("aire/index.html")
        for part in (
            'id="air-index-value"', 'id="air-index-risk"',
            'id="air-index-reported"', 'id="air-index-checked"',
            'id="air-index-pollutant"', 'id="air-index-status"',
            'id="air-index-recommendation"', 'id="air-weather-grid"',
            'id="air-borough"', 'id="air-weather-update"',
            'id="air-contingency-list"', 'id="air-contingency-status"',
            '/assets/aire.css?v=1', '/assets/aire.js?v=1',
            'https://www.aire.cdmx.gob.mx/ultima-hora-reporte.php',
            'https://www.gob.mx/comisionambiental/es/archivo/prensa',
            'https://api.met.no/',
        ):
            self.assertIn(part, html)
        self.assertIn('no presentamos un índice de contaminación por alcaldía', html.lower())
        self.assertIn('content="index,follow"', html)

    def test_api_validates_freshness_and_refuses_estimates(self):
        script = read("functions/api/aire.js")
        self.assertIn('const MAX_AGE=150*60*1000', script)
        self.assertIn("status:'unavailable'", script)
        self.assertIn("parseAirReport", script)
        self.assertIn('sourceStamp', script)
        self.assertIn('reported_at:publishedAt', script)
        self.assertIn("cache.put", script)
        self.assertIn("no-store", script)
        self.assertNotIn("innerHTML", read("assets/aire.js"))

    def test_16_alcaldias_and_weather_not_misrepresented(self):
        client = read("assets/aire.js")
        api = read("functions/api/clima.js")
        for borough in (
            "Álvaro Obregón", "Azcapotzalco", "Benito Juárez",
            "Coyoacán", "Cuajimalpa de Morelos", "Cuauhtémoc",
            "Gustavo A. Madero", "Iztacalco", "Iztapalapa",
            "La Magdalena Contreras", "Miguel Hidalgo", "Milpa Alta",
            "Tláhuac", "Tlalpan", "Venustiano Carranza", "Xochimilco",
        ):
            self.assertIn(borough, client)
            self.assertIn(borough, api)
        self.assertIn("precipitation_mm:precip", api)
        self.assertIn("precipitation_window_hours:precipHours", api)
        self.assertIn("estimated:true", api)
        self.assertIn("source:'MET Norway'", api)
        self.assertIn("function validForecast(data,name)", client)
        self.assertIn("function knownAir(data)", client)
        self.assertIn("No se muestran temperaturas estimadas sin fecha y fuente", client)
        self.assertIn("Una noticia", read("trafico/index.html"))

    def test_bulletins_are_archived_not_active_claims(self):
        script = read("functions/api/contingencias.js")
        html = read("aire/index.html")
        client = read("assets/aire.js")
        self.assertIn("archived:true", script)
        self.assertIn("no confirma que la contingencia esté activa ahora", script)
        self.assertIn("Un aviso antiguo no informa si existe una contingencia", html)
        self.assertIn("Estado vigente: no verificado", client)
        self.assertIn("https://www.gob.mx/comisionambiental/es/archivo/prensa", html)

    def test_navigation_and_sitemap(self):
        for path in ("index.html", "avisos/index.html", "cerca/index.html"):
            self.assertIn('href="/aire/"', read(path))
        self.assertIn('"aire/"', read("update_news.py"))
        self.assertIn('https://cdmx-al-memento.pages.dev/aire/</loc>', read("sitemap.xml"))
        self.assertIn("/aire/\n  Cache-Control: no-cache, must-revalidate", read("_headers"))

    def test_moderation_rules_and_workflow_stay_intact(self):
        rules = read("firebase/firestore.rules")
        self.assertIn("allow read, delete: if moderator()", rules)
        self.assertIn("match /community/main/voteTotals/{commentId}", rules)
        self.assertIn("match /community/main/moderationActions/{actionId}", rules)
        workflow = read(".github/workflows/news.yml")
        self.assertIn("'tests/test_air_page.py'", workflow)
        self.assertIn("node tests/test_aire_api.mjs", workflow)
        self.assertIn("node --check --input-type=module < functions/api/aire.js", workflow)


if __name__ == "__main__":
    unittest.main()
