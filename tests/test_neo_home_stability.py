"""Evita el regreso intermitente a la portada antigua en iPhone y con redes lentas."""
import json
import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from update_news import refresh_homepage_fallback, merge_recent_previous_feed

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
        self.assertIn("const candidates=state.stories.map((item,index)=>({item,index})).filter(({item})=>photoInfo(item)&&!isWeatherForecastOnly(item)&&!isStaleTimeSensitiveHeadline(item));", script)

    def test_ads_archive_and_caching_unchanged(self):
        home = read("index.html")
        self.assertIn("ca-pub-6521969406386261",home)
        self.assertIn('id="embedded-news-fallback"',home)
        self.assertIn('src="/app.js?v=',home)
        self.assertIn('href="/archivo/"',home)
        self.assertIn('src="/assets/neo-home.js?v=',home)
        self.assertIn('src="/assets/neo-home.js?v=20261113-accredited-hero-copy1"', home)
        self.assertRegex(home, r'href="/assets/neo-home\.css\?v=[a-zA-Z0-9_-]+"')
        headers=read("_headers")
        self.assertIn("Cache-Control: no-cache, must-revalidate",headers)
        self.assertIn("/index.html",headers)


    def test_hero_rotation_randomizes_recent_eligible_stories(self):
        script = read("assets/neo-home.js")
        apply = script[script.index("function applyStories(items,source)"):script.index("function start()")]
        self.assertIn("const heroCandidates=items.map", apply)
        self.assertIn("photoInfo(item)&&!isWeatherForecastOnly(item)", apply)
        self.assertIn("const alternatives=heroCandidates.filter(({item})=>item.url!==last);", apply)
        self.assertIn("const choices=alternatives.length?alternatives:heroCandidates;", apply)
        self.assertIn("choices[Math.floor(Math.random()*choices.length)].index", apply)
        self.assertIn("cdmx-neo-last-feature", apply)

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

    def test_expired_today_and_live_headlines_do_not_become_the_lead(self):
        script = read("assets/neo-home.js")
        self.assertIn("function isStaleTimeSensitiveHeadline(article,now=new Date())", script)
        self.assertIn(r"\b(?:hoy|en vivo)\b", script)
        self.assertIn("return day!==homepageDateFormatter.format(now);", script)
        hero = script[script.index("function renderHero()"):script.index("function renderNews()")]
        self.assertIn("!isStaleTimeSensitiveHeadline(item)", hero)
        apply = script[script.index("function applyStories(items,source)"):script.index("function start()")]
        self.assertIn("!isStaleTimeSensitiveHeadline(item)", apply)


    def test_embedded_fallback_is_refreshed_with_recent_news_and_excludes_expired_live_headlines(self):
        now = datetime(2026, 11, 13, 9, 50, tzinfo=timezone.utc)
        photo = {
            "kind": "representativa",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fd/example.jpg/960px-example.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:example.jpg",
            "author": "Autor de prueba",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            "topic": "Concierto representativo en CDMX",
        }
        current = {
            "title": "Concierto de prueba en CDMX",
            "url": "https://news.google.com/rss/articles/current",
            "local_url": "/noticias/?id=current&mes=2026-11",
            "source": "Medio de prueba",
            "date": "2026-11-13",
            "published_at": "2026-11-13T08:00:00Z",
            "category": "Cultura",
            "brief": {"lead": "Resumen actual"},
            "photo": photo,
        }
        expired_live = {
            "title": "Marchas en CDMX hoy 12 de noviembre EN VIVO",
            "url": "https://news.google.com/rss/articles/expired-live",
            "local_url": "/noticias/?id=expired&mes=2026-11",
            "source": "Medio de prueba",
            "date": "2026-11-12",
            "published_at": "2026-11-13T03:00:00Z",
            "category": "Movilidad",
            "brief": {"lead": "Resumen vencido"},
            "photo": photo,
        }
        old = {
            "title": "Noticia antigua",
            "url": "https://news.google.com/rss/articles/old",
            "local_url": "/noticias/?id=old&mes=2026-10",
            "source": "Medio de prueba",
            "date": "2026-10-26",
            "published_at": "2026-10-26T11:10:08Z",
            "category": "CDMX",
            "brief": {"lead": "Resumen antiguo"},
            "photo": photo,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text(
                '<html><script id="embedded-news-fallback" type="application/json">[{"title":"viejo"}]</script></html>',
                encoding="utf-8",
            )
            count = refresh_homepage_fallback(path, [current, expired_live, old], now)
            html = path.read_text(encoding="utf-8")
        match = re.search(
            r'<script id="embedded-news-fallback" type="application/json">(.*?)</script>',
            html,
            re.S,
        )
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        self.assertEqual(count, 1)
        self.assertEqual([item["title"] for item in payload], ["Concierto de prueba en CDMX"])
        self.assertIn("photo", payload[0])
        self.assertNotIn("Noticia antigua", html)
        self.assertNotIn("Marchas en CDMX hoy 12 de noviembre", html)

    def test_partial_rss_keeps_recent_previous_feed_and_drops_stale_entries(self):
        now = datetime(2026, 11, 13, 10, 30, tzinfo=timezone.utc)
        current = {
            "title": "Nueva noticia de CDMX",
            "url": "https://news.google.com/rss/articles/current",
            "source": "Medio de prueba",
            "date": "2026-11-13",
            "published_at": "2026-11-13T10:00:00Z",
            "category": "CDMX",
        }
        recent_previous = {
            "title": "Noticia previa reciente de CDMX",
            "url": "https://news.google.com/rss/articles/previous",
            "source": "Medio de prueba",
            "date": "2026-11-13",
            "published_at": "2026-11-13T08:00:00Z",
            "category": "CDMX",
        }
        stale_previous = {
            "title": "Noticia antigua de CDMX",
            "url": "https://news.google.com/rss/articles/stale",
            "source": "Medio de prueba",
            "date": "2026-11-09",
            "published_at": "2026-11-09T08:00:00Z",
            "category": "CDMX",
        }

        merged = merge_recent_previous_feed(
            [current], [recent_previous, stale_previous], now
        )
        titles = {item["title"] for item in merged}
        self.assertIn("Nueva noticia de CDMX", titles)
        self.assertIn("Noticia previa reciente de CDMX", titles)
        self.assertNotIn("Noticia antigua de CDMX", titles)


    def test_news_workflow_stages_the_generated_homepage_fallback_and_tests_prs(self):
        workflow = read(".github/workflows/news.yml")
        self.assertIn("pull_request:", workflow)
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertGreaterEqual(workflow.count("if: github.event_name != 'pull_request'"), 5)
        stage_lines = [line for line in workflow.splitlines() if "git add -A --" in line]
        self.assertEqual(len(stage_lines), 2)
        self.assertTrue(all("index.html" in line for line in stage_lines))


    def test_homepage_copy_explains_representative_photos_without_claiming_documentary_evidence(self):
        home = read("index.html")
        script = read("assets/neo-home.js")
        self.assertIn("imágenes representativas se identifican como tales", home)
        self.assertIn("Preparando una noticia destacada con fotografía acreditada", home)
        self.assertIn("Noticias recientes sin imagen acreditada disponible", script)
        self.assertIn("fotografías representativas acreditadas", script)
        self.assertIn("Sin imagen contextual acreditada disponible", script)

if __name__ == '__main__':
    unittest.main()
