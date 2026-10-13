"""Comprueba que las 16 alcaldías tengan historia, foto real y enlace directo."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets" / "alcaldias"
NAMES = [
    "La Magdalena Contreras", "Álvaro Obregón", "Azcapotzalco", "Benito Juárez",
    "Coyoacán", "Cuajimalpa de Morelos", "Cuauhtémoc", "Gustavo A. Madero",
    "Iztacalco", "Iztapalapa", "Miguel Hidalgo", "Milpa Alta", "Tláhuac",
    "Tlalpan", "Venustiano Carranza", "Xochimilco",
]


class ProfileTests(unittest.TestCase):
    def test_16_distinct_histories_with_sources(self):
        stories = json.loads((BASE / "historias.json").read_text(encoding="utf-8"))["boroughs"]
        self.assertEqual([p["name"] for p in stories], NAMES)
        self.assertEqual(len({p["slug"] for p in stories}), 16)
        for item in stories:
            self.assertGreaterEqual(len(item["history"]), 2)
            self.assertGreaterEqual(len(item["landmarks"]), 2)
            self.assertTrue(item["sources"])
            self.assertTrue(all(link["url"].startswith("https://") for link in item["sources"]))

    def test_16_verified_distinct_location_photos(self):
        photos = json.loads((BASE / "fotos.json").read_text(encoding="utf-8"))["photos"]
        self.assertEqual([p["name"] for p in photos], NAMES)
        self.assertEqual(len({p["source"] for p in photos}), 16)
        for p in photos:
            image = BASE / (p["slug"] + ".jpg")
            self.assertTrue(image.is_file(), str(image))
            self.assertGreater(image.stat().st_size, 4000)
            self.assertIn("commons.wikimedia.org/wiki/File:", p["source"])
            self.assertTrue(p["author"])
            self.assertTrue(p["license"])

    def test_news_navigation_without_old_grid(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        html = (ROOT / "alcaldias" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "assets" / "hemeroteca.js").read_text(encoding="utf-8")
        self.assertEqual(home.count("#noticias-alcaldia"), 16)
        self.assertIn('<section class="borough-news-column" id="noticias-alcaldia"', html)
        self.assertNotIn('<section class="borough-page-top" id="noticias-alcaldia"', html)
        css = (ROOT / 'styles.css').read_text(encoding='utf-8')
        self.assertIn('.borough-news-column{min-width:0;scroll-margin-top:130px}', css)
        self.assertIn('id="borough-results"', html)
        self.assertIn('id="borough-photo"', html)
        self.assertIn('id="borough-history-text"', html)
        self.assertIn('id="borough-selector"', html)
        self.assertNotIn('id="borough-directory"', html)
        self.assertIn("url.hash='#noticias-alcaldia'", js)


    def test_mobile_topic_tabs_scroll_to_news_not_borough_menu(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        js = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('href="#noticias" data-filter=""', home)
        self.assertIn('href="#noticias" data-filter="Metro"', home)
        self.assertIn('href="#noticias" data-filter="Seguridad"', home)
        self.assertIn('.news-main{width:100%;order:0}', css)
        self.assertIn('.borough-rail{width:100%;position:static;order:1;', css)
        self.assertIn('window.scrollTo({top:0', js)
        self.assertNotIn('scrollToHeadlines();', js)
        self.assertIn('function changeTopic(requested)', js)
        self.assertIn('displayTopic(next)', js)
        self.assertIn('topicStage.hidden=!next', js)
        self.assertIn('homeView.hidden=Boolean(next)', js)
        self.assertIn("id=\"topic-stage\"", home)
        self.assertIn("id=\"home-view\"", home)
        self.assertIn("id=\"topic-stage-grid\"", home)
        self.assertIn(".topic-stage[hidden],.home-view[hidden]", css)
        self.assertIn('/styles.css?v=20261013-slide-full', home)
        self.assertIn('/app.js?v=20261013-noticias-propias', home)


    def test_illustrated_map_featured_above_news_and_real_transport_layers(self):
        home=(ROOT / "index.html").read_text(encoding="utf-8")
        page=(ROOT / "mapa" / "index.html").read_text(encoding="utf-8")
        script=(ROOT / "mapa" / "mapa.js").read_text(encoding="utf-8")
        proxy=(ROOT / "functions" / "api" / "transporte.js").read_text(encoding="utf-8")
        css=(ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn('class="news-side-column"', home)
        self.assertIn('class="city-map-teaser city-map-teaser--hero"', home)
        self.assertEqual(home.count('class="city-map-teaser city-map-teaser--hero"'), 1)
        self.assertTrue(home.index('id="main-title"') < home.index('class="home-map-section"') < home.index('class="hero-ctas"'))
        self.assertTrue(home.index('class="home-map-section"') < home.index('class="news-side-column"'))
        self.assertNotIn('class="city-map-teaser"', home)
        self.assertIn('loading="lazy" tabindex="-1" aria-hidden="true"', home)
        self.assertIn('.home-map-section .city-map-teaser--hero', css)
        self.assertIn('href="/mapa/"', home)
        self.assertIn('src="/mapa/preview.html?v=3"', home)
        preview=(ROOT / "mapa" / "preview.html").read_text(encoding="utf-8")
        self.assertIn('https://tile.openstreetmap.org/{z}/{x}/{y}.png', preview)
        self.assertIn('https://tile.openstreetmap.org/{z}/{x}/{y}.png', script)
        self.assertNotIn('basemaps.cartocdn.com', script)
        self.assertIn('id="mapa-ampliar"', page)
        self.assertIn('mapa-ampliado', script)
        self.assertIn('mapa/mapa.css?v=4', page)
        self.assertIn('mapa/mapa.js?v=4', page)
        self.assertIn('.news-side-column{order:1;width:100%}', css)
        self.assertIn('.news-layout>.news-side-column{display:contents}', css)
        self.assertIn('.news-layout>.news-side-column>.borough-rail{order:2;width:100%}', css)
        self.assertIn('id="mapa-interactivo"', page)
        for mode in ['metro', 'metrobus', 'ligero', 'cablebus', 'trolebus', 'rtp', 'camiones']:
            self.assertIn('value="'+mode+'"', page)
            self.assertIn(mode+':', script)
            self.assertIn(mode+':', proxy)
        self.assertIn("Atlas de Movilidad Integrada", page)
        self.assertIn('geojson', proxy)
        self.assertIn('"mapa/"', (ROOT / 'update_news.py').read_text(encoding='utf-8'))
        self.assertIn('/styles.css?v=20261013-cercadeti', page)
        self.assertIn('minZoom:9,maxZoom:19', script)
        self.assertIn('value="naturaleza" checked', page)
        self.assertIn("id:'los-dinamos'", script)
        self.assertIn("id:'desierto-leones'", script)
        self.assertIn("id:'bosque-tlalpan'", script)
        self.assertIn("id:'cumbres-ajusco'", script)
        self.assertIn('layerNature=L.layerGroup().addTo(map)', script)
        self.assertIn("group=mode==='naturaleza'?layerNature:mode==='museos'?layerMuseums:mode==='salud'?layerHealth:layerMonuments", script)
        self.assertIn('id="menu-superior"', home)
        self.assertIn('data-nav-shift="-1"', home)
        self.assertIn('scroll-snap-type:x proximity', css)
        self.assertIn('function centerNavItem(item)', (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn('class="news-slide-viewport"', home)
        self.assertIn('id="news-slide-panel"', home)
        self.assertIn('id="current-topic"', home)
        self.assertIn('function changeTopic(requested)', (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn('changeTopic(el.dataset.filter', (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn('transform:\'translateX(', (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn('const ghost=outgoing.cloneNode(true)', (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn("const duration=720", (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn("behavior:'smooth'", (ROOT / "app.js").read_text(encoding='utf-8'))
        self.assertIn('.news-slide-viewport{min-width:0;', css)
        # Las pestañas aparecen en el mismo orden lógico arriba y en el filtro secundario.
        self.assertLess(home.index('button class="filter" data-filter="Seguridad"'),home.index('button class="filter" data-filter="Movilidad"'))


if __name__ == "__main__":
    unittest.main()
