"""Garantiza noticias leíbles aquí, fotografías únicas y atribución responsable."""
import unittest
from pathlib import Path
from scripts.notas_locales import assign_photos, local_link, summarize
from update_news import category_by_headline

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

    def test_fatal_microbus_headline_is_not_described_as_unknown_outcome(self):
        article = {
            "title": "Microbús Atropella y Mata a un Hombre en Situación de Calle en Azcapotzalco",
            "url": "https://news.google.com/rss/articles/example-fatal-microbus",
            "source": "N+", "date": "2026-11-01",
            "category": "Movilidad", "borough": "Azcapotzalco",
        }
        lead = summarize(article)["lead"]
        self.assertIn("un microbús", lead)
        self.assertIn("El propio titular señala un fallecimiento", lead)
        self.assertNotIn("no permite determinar", lead)
        article["title"] = "Choque entre dos vehículos en Azcapotzalco"
        self.assertIn("no permite determinar", summarize(article)["lead"])

    def test_metrobús_only_headline_is_not_summarized_as_metro(self):
        article = {
            "title": "Estado de las estaciones del Metrobús en esta última hora del 11 de noviembre",
            "url": "https://news.google.com/rss/articles/example-metrobus-only",
            "source": "Infobae", "date": "2026-11-11",
            "category": "Movilidad", "borough": "",
        }
        lead = summarize(article)["lead"]
        self.assertIn("servicio del Metrobús de Ciudad de México", lead)
        self.assertNotIn("Metro de Ciudad de México", lead)

    def test_combined_transit_headline_names_each_service(self):
        article = {
            "title": "¿Hay atrasos en Metro CDMX, Metrobús y Tren Suburbano? Estado del servicio hoy",
            "url": "https://news.google.com/rss/articles/example-multiple-transit",
            "source": "Eje Central", "date": "2026-11-11",
            "category": "Movilidad", "borough": "",
        }
        lead = summarize(article)["lead"]
        self.assertIn("Metro, Metrobús y Tren Suburbano", lead)
        self.assertNotIn("solo", lead.casefold())

    def test_capital_government_plan_headline_is_classified_as_government(self):
        title = ("EN UN HECHO HISTÓRICO, APRUEBA GOBIERNO DE LA CIUDAD DE MÉXICO "
                 "EL PROYECTO DEL PLAN GENERAL DE DESARROLLO 2025-2045 "
                 "Y LO ENVÍA AL CONGRESO LOCAL.")
        self.assertEqual(category_by_headline(title, "CDMX"), "Gobierno")
        # Una regla general de Gobierno no debe ocultar una detención específica.
        security_title = "Detienen a un hombre tras operativo del Gobierno de la Ciudad de México"
        self.assertEqual(category_by_headline(security_title, "CDMX"), "Seguridad")

    def test_ssc_buen_fin_operativo_is_security_and_uses_official_facts(self):
        title = ("2999: La SSC implementará un operativo de seguridad, vigilancia y vialidad "
                 "por el “Buen Fin 2026”, con la participación más de 16 mil policías en la ciudad de México")
        source = "Secretaría de Seguridad Ciudadana de la CDMX"
        self.assertEqual(category_by_headline(title, "Metro", source), "Seguridad")
        article = {
            "title": title,
            "url": "https://news.google.com/rss/articles/example-ssc-buen-fin",
            "source": source,
            "date": "2026-11-11",
            "category": "Seguridad",
            "borough": "",
        }
        brief = summarize(article)
        self.assertIn("16,300 policías", brief["lead"])
        self.assertIn("16 alcaldías", brief["lead"])
        self.assertIn("13 al 17 de noviembre de 2026", brief["lead"])
        self.assertIn("comunicado oficial de la SSC", brief["method"])
        self.assertNotIn("clasifica como Metro", brief["lead"])
        self.assertIn("ajuste del operativo", brief["pending"])
        self.assertNotIn("El índice RSS", brief["pending"])
        self.assertIn("seguridad", brief["context"].casefold())

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
        self.assertIn("Consultar la fuente original",js)
        self.assertIn('title.textContent=article.title',js)
        self.assertIn("id='+id+'&mes='+month",js)
        self.assertIn("section.append(source)",js)

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

    def test_recent_operativo_and_government_headlines_are_classified_correctly(self):
        cases = (
            ("Tabe en Miguel Hidalgo: cinco años de cambio", "Seguridad", "Gobierno"),
            ("Hemos cambiado y mejorado el rostro de Coyoacán: Giovani Gutierrez", "CDMX", "Gobierno"),
            ("Contraloría de la Cdmx detecta observaciones por 839 mdp en fiscalización", "CDMX", "Gobierno"),
            ("¿Qué pasó en Plaza Meave hoy? Autoridades de CDMX realizan operativo", "CDMX", "Seguridad"),
            ("Decomisan 3 toneladas de autopartes en Alcaldía Cuauhtémoc", "CDMX", "Seguridad"),
        )
        for title, feed_category, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(category_by_headline(title, feed_category), expected)


if __name__=="__main__":
    unittest.main()
