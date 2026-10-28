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
        self.assertEqual(home.count("#noticias-alcaldia"), 16 * (2 if 'id="neo-home"' in home else 1))
        self.assertIn('<section class="borough-news-column" id="noticias-alcaldia"', html)
        self.assertNotIn('<section class="borough-page-top" id="noticias-alcaldia"', html)
        css = (ROOT / 'styles.css').read_text(encoding='utf-8')
        self.assertIn('.borough-news-column{min-width:0;scroll-margin-top:130px}', css)
        self.assertIn('id="borough-results"', html)
        self.assertIn('id="borough-photo"', html)
        self.assertIn('id="borough-history-text"', html)
        self.assertIn('id="borough-selector"', html)
        self.assertNotIn('id="borough-directory"', html)
        self.assertIn("const url=boroughUrl(name)+'#noticias-alcaldia'", js)
        self.assertIn("history.pushState({alcaldia:name}",js)
        for slug in ("iztapalapa","tlalpan","xochimilco","cuauhtemoc"):
            self.assertTrue((ROOT / 'alcaldias' / slug / 'index.html').is_file(), slug)


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
        self.assertRegex(home, r'<link[^>]+href="/styles\.css\?v=[^"]+"')
        self.assertRegex(home, r'<script[^>]+src="/app\.js\?v=[^"]+"')


    def test_official_borough_map_keeps_neighborhood_navigation_without_extra_layers(self):
        home=(ROOT / "index.html").read_text(encoding="utf-8")
        page=(ROOT / "mapa" / "index.html").read_text(encoding="utf-8")
        script=(ROOT / "mapa" / "mapa.js").read_text(encoding="utf-8")
        preview=(ROOT / "mapa" / "preview-alcaldias-rutas-20261028.html").read_text(encoding="utf-8")
        css=(ROOT / "styles.css").read_text(encoding="utf-8")
        geo=json.loads((ROOT / "mapa" / "alcaldias.geojson").read_text(encoding="utf-8"))
        self.assertEqual(len(geo["features"]),16)
        self.assertIn('class="city-map-teaser city-map-teaser--hero"',home)
        self.assertIn('class="home-map-section"',home)
        self.assertIn('id="mapa-interactivo"',page)
        self.assertIn('id="mapa-ampliar"',page)
        self.assertIn('src="/mapa/preview-alcaldias-rutas-20261028.html"',home)
        self.assertIn('https://tile.openstreetmap.org/{z}/{x}/{y}.png',preview)
        self.assertIn('https://tile.openstreetmap.org/{z}/{x}/{y}.png',script)
        self.assertNotIn('basemaps.cartocdn.com',script)
        self.assertIn('dataUrl=',script)
        self.assertIn('/mapa/alcaldias.geojson?v=',script)
        self.assertIn("layer.on('mouseover'",script)
        self.assertIn("layer.on('click'",script)
        self.assertIn('window.location.assign(urlFor(name))',script)
        self.assertIn("color:'#fff'",script)
        self.assertIn("fillColor:'#f077ad'",preview)
        self.assertIn("window.parent.location.assign(link)",preview)
        self.assertIn('value="naturaleza" checked',page)
        self.assertIn('value="museos"',page)
        self.assertNotIn('value="salud"',page)
        self.assertNotIn('value="metro"',page)
        for place in ("los-dinamos","desierto-leones","bosque-tlalpan","museo-antropologia"):
            self.assertIn("id:'"+place+"'",script)
        self.assertIn('id="menu-superior"',home)
        self.assertIn('class="news-slide-viewport"',home)
        self.assertIn('id="news-slide-panel"',home)
        self.assertIn('function changeTopic(requested)',(ROOT / "app.js").read_text(encoding="utf-8"))
        self.assertIn('.home-map-section .city-map-teaser--hero',css)


if __name__ == "__main__":
    unittest.main()
