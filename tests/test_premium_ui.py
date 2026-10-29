"""Etapa 10: cobertura de la capa premium no destructiva."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','comunidad/index.html','movilidad/index.html',
'servicios/index.html','alcaldias/index.html','reportes-ciudadanos/index.html',
'aire/index.html','trafico/index.html','avisos/index.html','cerca/index.html',
'guias/index.html','seguridad/index.html','reportes/index.html',
'contacto.html','privacidad.html','sobre-nosotros.html',
'politica-editorial.html','creditos-fotograficos.html',
'archivo/index.html','mapa/index.html','cdmx/index.html',
'fotografias/index.html','noticias/index.html','descubre/index.html',
'agenda/index.html','negocios/index.html','herramientas/index.html',
'publicidad/index.html']
class PremiumUI(unittest.TestCase):
 def test_stylesheet_on_critical_pages(self):
  for page in PAGES:
   with self.subTest(page=page):
    html=(ROOT/page).read_text(encoding='utf-8')
    self.assertIn('/assets/premium-2026.css?v=1',html)
    self.assertEqual(html.count('/assets/premium-2026.css?v=1'),1)
    self.assertIn('</head>',html)
 def test_generated_reports_preserve_design(self):
  generator=(ROOT/'update_news.py').read_text(encoding='utf-8')
  self.assertIn('premium-2026.css?v=1',generator)
 def test_reduced_motion_keyboard_and_mobile(self):
  css=(ROOT/'assets/premium-2026.css').read_text(encoding='utf-8')
  for item in ['prefers-reduced-motion:reduce',':focus-visible','@media(max-width:720px)','overflow-wrap:anywhere','min-height:44px']:
   self.assertIn(item,css)
  self.assertNotIn('display:none!important',css)
  self.assertNotIn('position:fixed',css)
 def test_preserve_essential_functions(self):
  home=(ROOT/'index.html').read_text(encoding='utf-8')
  forum=(ROOT/'comunidad/index.html').read_text(encoding='utf-8')
  citizen=(ROOT/'reportes-ciudadanos/index.html').read_text(encoding='utf-8')
  for x in ['/assets/neo-home.js','/app.js','/assets/portal.js','adsbygoogle.js']:
   self.assertIn(x,home)
  self.assertIn('/assets/comments.js',forum)
  self.assertIn('/assets/reportes-ciudadanos.js',citizen)
  self.assertIn('/assets/comments-config.js',citizen)
if __name__=='__main__':unittest.main()
