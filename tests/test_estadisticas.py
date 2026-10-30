"""Regresiones para el panel público de métricas verificables."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Stats(unittest.TestCase):
 def test_panel_has_accessible_sources(self):
  html=(ROOT/'estadisticas/index.html').read_text(encoding='utf-8')
  for value in ['stats-visitors','stats-likes','stats-news','stats-updated','stats-status','stats-refresh','/assets/estadisticas.js?v=3','/assets/premium-2026.css?v=1']:
   self.assertIn(value,html)
 def test_no_counter_pollution(self):
  js=(ROOT/'assets/estadisticas.js').read_text(encoding='utf-8')
  for source in ['/api/engagement','/api/likes','/news.json']:
   self.assertIn(source,js)
  self.assertIn("method:'GET'",js)
  self.assertNotIn("action:'visit'",js)
  self.assertNotIn("method:'POST'",js)
  self.assertNotIn("method:'PUT'",js)
  self.assertIn('Promise.allSettled',js)
 def test_category_chart(self):
  html=(ROOT/'estadisticas/index.html').read_text(encoding='utf-8')
  js=(ROOT/'assets/estadisticas.js').read_text(encoding='utf-8')
  self.assertIn('stats-breakdown',html)
  self.assertIn('renderBreakdown(news)',js)
  self.assertIn('textContent=name',js)
  self.assertIn('stats-breakdown-track',(ROOT/'assets/estadisticas.css').read_text(encoding='utf-8'))
 def test_links_and_regeneration(self):
  self.assertIn('/estadisticas/',(ROOT/'index.html').read_text(encoding='utf-8'))
  self.assertIn('/estadisticas/',(ROOT/'servicios/index.html').read_text(encoding='utf-8'))
  self.assertIn('estadisticas/',(ROOT/'update_news.py').read_text(encoding='utf-8'))
  self.assertIn('/estadisticas/',(ROOT/'sitemap.xml').read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
