"""Regresiones para el portal de alcaldías, noticias y movilidad."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PortalTests(unittest.TestCase):
    def test_home_has_daily_digest_borough_and_shortcuts(self):
        home = get("index.html")
        self.assertIn('id="portal-today-list"', home)
        self.assertIn('id="portal-date"', home)
        self.assertIn('id="portal-today-note"', home)
        self.assertIn('id="home-borough-select" data-borough-select', home)
        self.assertIn('id="portal-borough-list"', home)
        self.assertIn('id="portal-enable-notifications"', home)
        for url in ("/cerca/", "/movilidad/", "/avisos/", "/favoritos/"):
            self.assertIn('href="' + url + '"', home)
        self.assertIn('/assets/portal.css?v=1', home)
        self.assertIn('/assets/portal.js?v=5', home)
        # El mapa sigue justo después del titular principal; no se pierde.
        self.assertLess(home.index('id="main-title"'), home.index('class="home-map-section"'))
        self.assertLess(home.index('class="home-map-section"'), home.index('id="portal-today-list"'))
        # El carrusel de noticias por categorías se conserva.
        self.assertIn('id="topic-stage"', home)
        self.assertIn('id="topic-stage-grid"', home)

    def test_original_pages_have_metadata_and_content(self):
        cases = {
            "cerca/": ("CDMX cerca de ti", 'data-borough-select'),
            "movilidad/": ("Metro, Metrobús y transporte", 'id="portal-metro-lines"'),
            "avisos/": ("Alertas y avisos de la CDMX", 'id="portal-alert-list"'),
            "favoritos/": ("Mis noticias guardadas", 'id="portal-favorites-list"'),
        }
        for path, (title, component) in cases.items():
            with self.subTest(page=path):
                html = get(path + "index.html")
                self.assertIn(title, html)
                self.assertIn(component, html)
                self.assertIn('https://cdmx-al-memento.pages.dev/' + path, html)
                self.assertIn('<meta name="description"', html)
                self.assertIn('/assets/portal.css?v=1', html)
                self.assertIn('/assets/portal.js?v=5', html)
                self.assertIn('href="/politica-editorial.html"', html)
                self.assertIn('href="/privacidad.html"', html)
        self.assertIn('content="noindex,follow"', get("favoritos/index.html"))

    def test_local_preferences_and_favorites_are_private(self):
        js = get("assets/portal.js")
        self.assertIn('cdmx.memento.alcaldia.v1', js)
        self.assertIn('cdmx.memento.favoritos.v1', js)
        self.assertIn('localStorage.getItem', js)
        self.assertIn('localStorage.setItem', js)
        self.assertIn('readFavorites()', js)
        self.assertIn('toggleFavorite(item)', js)
        self.assertIn('new MutationObserver', js)
        self.assertIn("card.querySelector('a.read", js)
        self.assertIn("a.local_url||'/noticias/'", js)
        self.assertNotIn('fetch(\'/api/save', js)
        priv = get('privacidad.html')
        self.assertIn('cdmx.memento.alcaldia.v1', priv)
        self.assertIn('cdmx.memento.favoritos.v1', priv)

    def test_notifications_require_consent_and_open_page(self):
        js = get("assets/portal.js")
        self.assertIn('Notification.requestPermission()', js)
        self.assertIn('document.visibilityState', js)
        self.assertIn('!noticeEnabled', js)
        self.assertIn('setInterval(pollNotifications,15*60*1000)', js)
        for page in ('index.html', 'cerca/index.html', 'avisos/index.html'):
            self.assertIn('id="portal-enable-notifications"', get(page))
            self.assertIn('id="portal-notification-status"', get(page))
        self.assertIn('mientras la página esté abierta', get('index.html'))

    def test_transit_is_reference_and_alerts_link_to_official_sources(self):
        js = get('assets/portal.js')
        self.assertIn("id:'1'", js)
        self.assertIn("id:'12'", js)
        self.assertIn("id:'A'", js)
        self.assertIn("id:'B'", js)
        self.assertEqual(len(re.findall(r"\{id:'(?:[1-9]|12|A|B)',color:", js)), 12)
        transit = get('movilidad/index.html')
        alerts = get('avisos/index.html')
        self.assertIn('no confirma el estado de servicio en tiempo real', transit)
        self.assertIn('metro.cdmx.gob.mx/la-red', transit)
        self.assertIn('metrobus.cdmx.gob.mx/ServicioMB', transit)
        self.assertIn('proteccioncivil.cdmx.gob.mx', alerts)
        self.assertIn('aire.cdmx.gob.mx', alerts)
        self.assertIn('911', alerts)
        self.assertIn('no es un sistema de alarma', alerts)

    def test_map_has_categories_and_points_without_emergency_claims(self):
        page = get('mapa/index.html')
        js = get('mapa/mapa.js')
        for mode in ('museos', 'salud', 'naturaleza', 'monumentos'):
            self.assertIn('value="' + mode + '"', page)
        for place in ('museo-antropologia', 'templo-mayor', 'hospital-general', 'bosque-chapultepec'):
            self.assertIn("id:'" + place + "'", js)
        self.assertIn('layerMuseums=L.layerGroup().addTo(map)', js)
        self.assertIn('layerHealth=L.layerGroup()', js)
        self.assertIn('no informan capacidad, urgencias', page)

    def test_sitemap_and_automatic_checks(self):
        python = get('update_news.py')
        for path in ('"cerca/"', '"movilidad/"', '"avisos/"'):
            self.assertIn(path, python)
        workflow = get('.github/workflows/news.yml')
        self.assertIn('tests/test_portal.py', workflow)
        self.assertIn('node --check assets/portal.js', workflow)
        self.assertIn('node --check mapa/mapa.js', workflow)


if __name__ == '__main__':
    unittest.main()
