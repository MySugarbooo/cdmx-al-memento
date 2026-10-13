"""Pruebas del clima horizontal: páginas, CSS, API y privacidad."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


class WeatherRibbonTests(unittest.TestCase):
    def test_all_main_pages_show_weather_above_navigation(self):
        paths = [
            "index.html", "cerca/index.html", "movilidad/index.html",
            "avisos/index.html", "favoritos/index.html", "alcaldias/index.html",
            "mapa/index.html", "archivo/index.html", "reportes/index.html",
            "guias/index.html", "guias/alertas-por-lluvia.html",
            "guias/estado-del-metro.html", "guias/cierres-viales.html",
            "guias/tramites-cdmx.html", "contacto.html", "privacidad.html",
            "politica-editorial.html", "sobre-nosotros.html",
            "creditos-fotograficos.html",
        ]
        for path in paths:
            with self.subTest(page=path):
                html = text(path)
                self.assertIn('id="weather-ribbon"', html)
                self.assertIn('id="weather-ribbon-track"', html)
                self.assertIn('id="weather-borough"', html)
                self.assertIn('id="weather-screen-reader"', html)
                self.assertLess(html.index('id="weather-ribbon"'), html.index('<header>'))
                self.assertIn('/assets/clima-ticker.css?v=3', html)
                self.assertIn('/assets/clima-ticker.js?v=3', html)
        self.assertIn('/assets/portal.js?v=4', text('index.html'))
        self.assertIn('/assets/portal.js?v=4', text('cerca/index.html'))

    def test_api_has_16_alcaldias_and_never_invents_data(self):
        api = text('functions/api/clima.js')
        client = text('assets/clima-ticker.js')
        expected = [
            'La Magdalena Contreras', 'Álvaro Obregón', 'Azcapotzalco',
            'Benito Juárez', 'Coyoacán', 'Cuajimalpa de Morelos',
            'Cuauhtémoc', 'Gustavo A. Madero', 'Iztacalco', 'Iztapalapa',
            'Miguel Hidalgo', 'Milpa Alta', 'Tláhuac', 'Tlalpan',
            'Venustiano Carranza', 'Xochimilco',
        ]
        for name in expected:
            self.assertIn("'" + name + "':", api)
            self.assertIn("'" + name + "'", client)
        # La API no acepta lat/lon arbitrarias proporcionadas por el visitante.
        self.assertIn("Object.hasOwn(BOROUGHS,name)", api)
        self.assertIn("lat.toFixed(4)", api)
        self.assertIn("lon.toFixed(4)", api)
        self.assertIn('https://api.met.no/weatherapi/locationforecast/2.0/compact', api)
        self.assertIn("'User-Agent':", api)
        self.assertIn('source:\'MET Norway\'', api)
        self.assertIn('estimated:true', api)
        self.assertIn("return json({alcaldia:name,error:", api)
        self.assertIn('no es medición en calle', api)

    def test_animation_accessibility_and_local_preferences(self):
        css = text('assets/clima-ticker.css')
        js = text('assets/clima-ticker.js')
        portal = text('assets/portal.js')
        self.assertIn('@keyframes weather-slide', css)
        self.assertIn('animation-play-state:paused', css)
        self.assertIn('@media(prefers-reduced-motion:reduce)', css)
        self.assertIn('body>header{top:var(--weather-strip-height)}', css)
        self.assertIn('aria-hidden', js)
        self.assertIn('a.tabIndex=-1', js)
        self.assertIn('cdmx.memento.alcaldia.v1', js)
        self.assertIn("window.addEventListener('storage'", js)
        self.assertIn('cdmx:borough-changed', js)
        self.assertIn('cdmx:borough-changed', portal)
        self.assertIn('Pronósticos: MET Norway', js)
        self.assertIn('https://api.met.no/', js)
        self.assertIn('No se muestran datos sin verificar.', js)
        self.assertIn("const CENTER='Cuauhtémoc'", js)
        self.assertIn('return [CENTER,...rest]', js)
        self.assertIn('Math.random()', js)
        self.assertIn('const CACHE_KEY=', js)
        self.assertIn('MAX_STALE=120*60*1000', js)
        self.assertIn('loadCache()', js)
        self.assertIn('for(const name of order)renderOne(name)', js)
        self.assertIn('const speed=window.innerWidth<600?78:88', js)
        self.assertIn('track.style.setProperty(\'--weather-duration\'', js)
        self.assertIn('await Promise.all([worker(),worker(),worker()])', js)
        self.assertIn("refreshAll()", js)
        self.assertIn('var(--weather-duration,36s)', css)
        self.assertIn('weather-chip--selected', css)
        # La fecha aparece a la derecha y se calcula en la zona CDMX.
        self.assertIn("document.createElement('time')", js)
        self.assertIn("dateBadge.className='weather-ribbon__date'", js)
        self.assertIn("if(bar)bar.append(dateBadge)", js)
        self.assertIn("timeZone:zone", js)
        self.assertIn("'America/Mexico_City'", js)
        self.assertIn("weekday:'long'", js)
        self.assertIn("month:'long',year:'numeric'", js)
        self.assertIn("dateBadge.dateTime=", js)
        self.assertIn("setInterval(refreshDate,60000)", js)
        self.assertIn(".weather-ribbon__date{", css)
        self.assertIn(".weather-date__short{display:none}", css)
        self.assertIn('animation-play-state:paused', css)

    def test_workflow_and_reports_preserve_strip(self):
        workflow = text('.github/workflows/news.yml')
        self.assertIn("tests/test_weather.py", workflow)
        self.assertIn("node --check assets/clima-ticker.js", workflow)
        self.assertIn("node --check --input-type=module < functions/api/clima.js", workflow)
        reports = text('update_news.py')
        self.assertIn("/assets/clima-ticker.css?v=3", reports)
        self.assertIn("/assets/clima-ticker.js?v=3", reports)
        self.assertIn("weather = (", reports)
        privacy = text('privacidad.html')
        self.assertIn('MET Norway', privacy)
        self.assertIn('no requiere GPS', privacy)


if __name__ == '__main__':
    unittest.main()
