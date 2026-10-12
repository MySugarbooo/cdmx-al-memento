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
        self.assertIn("document.querySelector('.news-main .bar')", js)
        self.assertIn('window.scrollTo({top:', js)
        self.assertIn('/styles.css?v=20261012-tabs2', home)
        self.assertIn('/app.js?v=20261012-tabs2', home)


    def test_illustrated_map_appears_as_side_card_and_real_transport_layers(self):
        home=(ROOT / "index.html").read_text(encoding="utf-8")
        page=(ROOT / "mapa" / "index.html").read_text(encoding="utf-8")
        script=(ROOT / "mapa" / "mapa.js").read_text(encoding="utf-8")
        proxy=(ROOT / "functions" / "api" / "transporte.js").read_text(encoding="utf-8")
        css=(ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn('class="news-side-column"', home)
        self.assertIn('class="city-map-teaser"', home)
        self.assertIn('href="/mapa/"', home)
        self.assertIn('src="/mapa/mini.svg"', home)
        self.assertIn('.news-side-column{order:1;width:100%}', css)
        self.assertIn('id="mapa-interactivo"', page)
        for mode in ['metro', 'metrobus', 'ligero', 'cablebus', 'trolebus', 'rtp', 'camiones']:
            self.assertIn('value="'+mode+'"', page)
            self.assertIn(mode+':', script)
            self.assertIn(mode+':', proxy)
        self.assertIn("Atlas de Movilidad Integrada", page)
        self.assertIn('geojson', proxy)
        self.assertIn('minZoom:9,maxZoom:19', script)


if __name__ == "__main__":
    unittest.main()
