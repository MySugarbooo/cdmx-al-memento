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
        self.assertGreaterEqual(home.count('class="neo-news-card"'), 4)
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

    def test_ads_archive_and_caching_unchanged(self):
        home = read("index.html")
        self.assertIn("ca-pub-6521969406386261",home)
        self.assertIn('id="embedded-news-fallback"',home)
        self.assertIn('src="/app.js?v=',home)
        self.assertIn('href="/archivo/"',home)
        self.assertIn('src="/assets/neo-home.js?v=20261027-estable1"',home)
        self.assertIn('href="/assets/neo-home.css?v=20261027-estable1"',home)
        headers=read("_headers")
        self.assertIn("Cache-Control: no-cache, must-revalidate",headers)
        self.assertIn("/index.html",headers)

if __name__ == '__main__':
    unittest.main()
