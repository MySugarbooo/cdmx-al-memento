"""Evita el regreso intermitente a la portada antigua en iPhone y con redes lentas."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

class StableHomepageTests(unittest.TestCase):
    def test_new_homepage_is_in_html_without_js_or_live_feed(self):
        home = read("index.html")
        self.assertIn('<html lang="es" class="neo-active">', home)
        self.assertIn('<section id="neo-home"', home)
        self.assertIn('id="neo-home-critical"', home)
        self.assertLess(home.index('id="neo-home"'), home.index('id="nota-principal"'))
        self.assertIn('html.neo-active #contenido> :not(#neo-home){display:none!important}', home)
        self.assertIn('id="neo-hero-title"', home)
        self.assertIn('id="neo-borough-list"', home)
        self.assertIn('id="neo-official-map"', home)
        self.assertIn('id="neo-news-grid"', home)
        self.assertIn('id="neo-links"', home)
        # El HTML inicial conserva el diseño, sin publicar tarjetas antiguas
        # con fotos genéricas cuando no existe evidencia documental del hecho.
        self.assertNotIn('class="neo-news-card"', home)
        self.assertIn('Cargando noticias con fotografías acreditadas', home)
        self.assertIn('Noticias de Ciudad de México', home)
        self.assertIn('id="neo-hero-img" class="neo-hero-image" src="/assets/fotos/reforma.jpg"', home)
        for path in ("/cdmx/", "/seguridad/", "/servicios/", "/alcaldias/", "/comunidad/"):
            self.assertIn('href="' + path + '"', home)
        self.assertEqual(home.count('id="neo-home"'), 1)
        self.assertEqual(home.count('id="neo-news-grid"'), 1)

    def test_network_failure_never_reveals_previous_layout(self):
        script = read("assets/neo-home.js")
        self.assertIn("const shell=document.getElementById('neo-home')",script)
        self.assertIn("if(!shell.hasChildNodes())shell.innerHTML",script)
        self.assertIn("function eligibleStories(feed)",script)
        self.assertIn("function applyStories(items,source)",script)
        self.assertIn("applyStories(eligibleStories(JSON.parse(fallback.textContent)),'backup')",script)
        self.assertIn("if(!shell.isConnected)root.prepend(shell)",script)
        self.assertIn("document.documentElement.classList.add('neo-active')",script)
        self.assertIn("fetch('/news.json?t='+Date.now(),{cache:'no-store'})",script)
        self.assertLess(script.index("if(!shell.isConnected)root.prepend(shell)"),script.index("fetch('/news.json?t='+Date.now()"))
        self.assertIn("state.fromBackup=source!=='online'",script)
        self.assertNotIn("se mantiene el diseño anterior",script)
        self.assertNotIn("if(!articles.length)throw Error('feed vacío')",script)

    def test_homepage_only_shows_today_or_yesterday_in_mexico_city(self):
        script = read("assets/neo-home.js")
        self.assertIn("timeZone:'America/Mexico_City'", script)
        self.assertIn("function homepageDay(value)", script)
        self.assertIn("function isHomepageRecent(article,now=new Date())", script)
        self.assertIn("!isHomepageRecent(a)", script)
        self.assertIn("No hay noticias de hoy o ayer para destacar", script)
        self.assertIn("Respaldo reciente (hoy o ayer)", script)
        self.assertNotIn("Titulares de respaldo (pueden no estar actualizados)", script)

    def test_sensitive_headlines_do_not_reuse_context_photos(self):
        script = read("assets/neo-home.js")
        self.assertIn("const sensitiveMediaTitle=title=>/", script)
        self.assertIn("violaci[oó]n|abuso sexual|agresi[oó]n sexual|acoso sexual|violencia sexual", script)
        self.assertIn("sensitiveMediaTitle(a?.title)", script)
        self.assertIn("if((a?.sensitive_media||sensitiveMediaTitle(a?.title))&&!documented)return null;", script)
        self.assertIn("const sensitive=a?.sensitive_media===true||sensitiveMediaTitle(a?.title);", script)
        self.assertIn("if((!p&&!sensitive)||(p&&usedPhotos.has(p.url)))return false;", script)
        self.assertIn("Sin fotografía verificada del hecho", script)
        self.assertIn("const candidates=state.stories.map((item,index)=>({item,index})).filter(({item})=>photoInfo(item)&&!isWeatherForecastOnly(item));", script)

    def test_ads_archive_and_caching_unchanged(self):
        home = read("index.html")
        self.assertIn("ca-pub-6521969406386261",home)
        self.assertIn('id="embedded-news-fallback"',home)
        self.assertIn('src="/app.js?v=',home)
        self.assertIn('href="/archivo/"',home)
        self.assertIn('src="/assets/neo-home.js?v=',home)
        self.assertIn('src="/assets/neo-home.js?v=20261112-no-weather-hero2"', home)
        self.assertRegex(home, r'href="/assets/neo-home\.css\?v=[a-zA-Z0-9_-]+"')
        headers=read("_headers")
        self.assertIn("Cache-Control: no-cache, must-revalidate",headers)
        self.assertIn("/index.html",headers)


    def test_weather_forecasts_do_not_take_the_lead_story(self):
        script = read("assets/neo-home.js")
        self.assertIn("function isWeatherForecastOnly(article)", script)
        hero = script[script.index("function renderHero()"):script.index("function renderNews()")]
        self.assertIn("!isWeatherForecastOnly(item)", hero)
        self.assertIn("return forecastOnly&&!concreteImpact;", script)
        self.assertIn(r"habr[aá]\s+(?:lluvias|tormenta|chubascos|granizo)", script)
        self.assertIn(r"activan\s+alerta\s+por\s+(?:lluvias|diluvio|tormenta)", script)
        self.assertIn(r"se esperan?\s+(?:lluvias|tormentas|chubascos|granizo|temperaturas?|frente frío)", script)
        self.assertIn(r"lluvias?\s+(?:fuertes|intensas|moderadas|ligeras|torrenciales)\s+en\s+(?:la\s+)?(?:cdmx|ciudad\s+de\s+m[eé]xico)", script)
        # Los avisos de clima permanecen en las últimas noticias; solo se excluyen del destacado.
        news = script[script.index("function renderNews()"):script.index("function mirrorVisits()")]
        self.assertIn("const all=state.stories;", news)
        self.assertNotIn("isWeatherForecastOnly", news)
        self.assertIn("suspenden|suspende", script)

if __name__ == '__main__':
    unittest.main()
