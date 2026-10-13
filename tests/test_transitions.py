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
        self.assertIn("const duration=480",js)
        self.assertIn("const leave=ghost.animate([",js)
        self.assertIn("const arrive=incoming.animate([",js)
        self.assertIn("if(token!==topicSwitchToken)return",js)
        self.assertIn("behavior:'smooth'",js)
        self.assertNotIn("behavior:'instant'",js)
        self.assertIn("navReducedMotion()",js)
        self.assertIn(".topic-transition-ghost",css)

    def test_interpage_slides_preserve_real_navigation(self):
        js=read("assets/page-transitions.js")
        for snippet in (
            "window.location.assign(target.href)",
            "event.preventDefault()",
            "sessionStorage.setItem(KEY",
            "sessionStorage.removeItem(KEY)",
            "event.metaKey",
            "event.ctrlKey",
            "event.shiftKey",
            "event.altKey",
            "a.hasAttribute('download')",
            "target.origin!==location.origin",
            "target.pathname===location.pathname",
            "reduced()",
            "window.addEventListener('pageshow',resetExit)",
            "duration:190",
            "duration:380",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,js)

    def test_every_primary_page_loads_transitions(self):
        paths=[p for p in ROOT.rglob("*.html")
               if ".git" not in p.parts and p.relative_to(ROOT).as_posix()!="mapa/preview.html"]
        self.assertGreaterEqual(len(paths),45)
        for path in paths:
            with self.subTest(page=str(path.relative_to(ROOT))):
                self.assertIn('page-transitions.js?v=1',path.read_text(encoding="utf-8"))

    def test_generators_preserve_animation(self):
        self.assertIn('page-transitions.js?v=1',read("update_news.py"))
        self.assertIn('page-transitions.js?v=1',read("scripts/generar_guias.py"))
        self.assertIn('/app.js?v=20261013-deslizamiento',read("index.html"))

if __name__=="__main__":
    unittest.main()
