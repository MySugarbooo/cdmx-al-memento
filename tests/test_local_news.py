"""Garantiza noticias leíbles aquí, fotografías únicas y atribución responsable."""
import unittest
from pathlib import Path
from scripts.notas_locales import assign_photos, local_link, summarize

ROOT=Path(__file__).resolve().parents[1]

class LocalNewsTests(unittest.TestCase):
    def make(self,i,category):
        return {"title":f"El Metro de CDMX reporta avance de la línea {i} de transporte",
                "url":"https://news.google.com/rss/articles/sample"+str(i),
                "source":"Periódico de prueba","date":"2026-10-13",
                "category":category,"borough":""}

    def test_distinct_real_photos_for_sixty_news(self):
        groups=["CDMX","Metro","Seguridad","Movilidad","Cultura","Gobierno"]
        items=[self.make(i,groups[i%len(groups)]) for i in range(60)]
        stats=assign_photos(items)
        self.assertGreaterEqual(stats["available"],60)
        self.assertEqual(stats["assigned"],60)
        self.assertEqual(stats["unique"],60)
        for item in items:
            photo=item["photo"]
            self.assertTrue(photo["author"])
            self.assertTrue(photo["license"])
            self.assertIn("https://commons.wikimedia.org/wiki/File:",photo["source"])
            self.assertTrue(photo["url"].startswith(("/assets/","https://thumb.wikimedia.org","https://upload.wikimedia.org")))

    def test_local_link_based_on_original_url(self):
        article=self.make(1,"Metro")
        link=local_link(article)
        self.assertRegex(link,r"^/noticias/\?id=[a-f0-9]{20}&mes=2026-10$")
        self.assertEqual(link,local_link(article))
        self.assertNotEqual(link,local_link(self.make(2,"Metro")))

    def test_sources_are_named_and_facts_not_invented(self):
        article=self.make(1,"Metro")
        brief=summarize(article)
        self.assertIn("Periódico de prueba",brief["lead"])
        self.assertIn("Metro",brief["lead"])
        self.assertIn("deben comprobarse",brief["pending"])
        self.assertIn("titular",brief["method"])
        self.assertNotIn("entrevistamos",brief["lead"])

    def test_reader_is_internal_and_signed(self):
        html=(ROOT/"noticias/index.html").read_text(encoding="utf-8")
        js=(ROOT/"assets/noticias-locales.js").read_text(encoding="utf-8")
        self.assertIn("Por Amau Kisumi",html)
        self.assertIn('id="local-story-photo"',html)
        self.assertIn("article.brief?.lead",js)
        self.assertIn("function selectedPhoto(x)",js)
        self.assertIn("const rights=selectedPhoto(article)||{}",js)
        self.assertIn("safeExternal(rights.source)",js)
        self.assertIn("origin.href=rights.source",js)
        self.assertIn("Consultar la fuente original (opcional)",js)
        self.assertIn('title.textContent=article.title',js)
        self.assertIn("id='+id+'&mes='+month",js)
        self.assertIn("source.append(ref)",js)

    def test_home_and_portals_open_local_pages(self):
        home=(ROOT/"app.js").read_text(encoding="utf-8")
        portal=(ROOT/"assets/portal.js").read_text(encoding="utf-8")
        archive=(ROOT/"assets/hemeroteca.js").read_text(encoding="utf-8")
        updater=(ROOT/"update_news.py").read_text(encoding="utf-8")
        self.assertIn("a.local_url||'/noticias/'",home)
        self.assertIn("Leer resumen de Amau Kisumi",home)
        self.assertIn("a.local_url||'/noticias/'",portal)
        self.assertIn("article.local_url||'/noticias/'",archive)
        self.assertIn("assign_photos(items[:60])",updater)
        self.assertIn('"local_url"',updater)
        self.assertIn("summarize(result)",updater)

if __name__=="__main__":
    unittest.main()
