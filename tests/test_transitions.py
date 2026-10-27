"""Verifica que la navegación visible sea animada y segura en iOS.

Las páginas mantienen enlaces HTML normales: si falla el JS, siguen funcionando.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class TransitionTests(unittest.TestCase):
    def test_category_swipes_move_both_panels(self):
        js=read("app.js")
        css=read("styles.css")
        self.assertIn("const ghost=outgoing.cloneNode(true)",js)
        self.assertIn("document.body.append(ghost)",js)
        self.assertIn("displayTopic(next)",js)
        self.assertIn("const duration=720",js)
        self.assertIn("const leave=ghost.animate([",js)
        self.assertIn("const arrive=incoming.animate([",js)
        self.assertIn("if(token!==topicSwitchToken)return",js)
        self.assertIn("behavior:'smooth'",js)
        self.assertNotIn("behavior:'instant'",js)
        self.assertIn("navReducedMotion()",js)
        self.assertIn(".topic-transition-ghost",css)
        self.assertIn("@view-transition{navigation:auto}",css)
        self.assertIn("memento-page-leave",css)
        self.assertIn("memento-page-arrive",css)
        self.assertIn("const outgoing=before?topicStage:homeView",js)
        self.assertIn("const incoming=next?topicStage:homeView",js)

    def test_interpage_navigation_is_seamless_and_keeps_real_links(self):
        """Do not animate the old page to blank or delay normal navigation."""
        js=read("assets/page-transitions.js")
        css=read("assets/neo-site.css")
        self.assertIn("@view-transition{navigation:auto}",css)
        self.assertIn("::view-transition-old(root)",css)
        self.assertIn("::view-transition-new(root)",css)
        self.assertIn("@media(prefers-reduced-motion:reduce)",css)
        self.assertIn("document.body.classList.add('neo-site-inner')",js)
        self.assertIn("header.replaceChildren(top,nav)",js)
        self.assertIn("target.scrollIntoView({behavior:'smooth'",js)
        self.assertNotIn("window.location.assign",js)
        self.assertNotIn("duration:190",js)
        self.assertIn("/seguridad/",js)
        self.assertIn("/servicios/",js)

    def test_every_primary_page_loads_transitions(self):
        paths=[p for p in ROOT.rglob("*.html")
               if ".git" not in p.parts and p.relative_to(ROOT).as_posix() not in ("mapa/preview.html", "escribe-pro/index.html")]
        self.assertGreaterEqual(len(paths),45)
        for path in paths:
            with self.subTest(page=str(path.relative_to(ROOT))):
                self.assertRegex(path.read_text(encoding="utf-8"),r'page-transitions\.js\?v=[^"\s]+')

    def test_generators_preserve_navigation(self):
        self.assertIn("page-transitions.js",read("update_news.py"))
        self.assertIn("page-transitions.js",read("scripts/generar_guias.py"))
        self.assertIn("page-transitions.js",read("scripts/animales_feed.py"))
        self.assertIn("styles.css?v=20261027-unificado",read("scripts/animales_feed.py"))
        self.assertRegex(read("index.html"), r'<script[^>]+src="/app\.js\?v=[^"]+"')

    def test_section_landing_pages_use_verified_feed_and_theme(self):
        css=read("styles.css")
        self.assertTrue(css.startswith('@import url("/assets/neo-site.css'))
        for page in ("seguridad/index.html","servicios/index.html"):
            html=read(page)
            self.assertIn('id="neo-section-stories"',html)
            self.assertIn('/assets/neo-sections.js',html)
            self.assertIn('/assets/page-transitions.js',html)
            self.assertIn('pagead2.googlesyndication.com',html)
        js=read("assets/neo-sections.js")
        self.assertIn("'/news.json?site=sections-'",js)
        self.assertIn("document.createElement",js)
        self.assertIn("a.category===category",js)

if __name__=="__main__":
    unittest.main()
