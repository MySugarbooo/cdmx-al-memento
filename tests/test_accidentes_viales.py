"""Regresiones de cobertura vial y redacción responsable de accidentes."""
import unittest

from update_news import LOCAL_EVENT_QUERIES, category_by_headline, standardize
from scripts.notas_locales import summarize


class AccidentCoverageTests(unittest.TestCase):
    def article(self, title, category="Seguridad"):
        return {
            "title": title,
            "url": "https://news.google.com/rss/articles/noticia-accidente-prueba",
            "source": "Medio de prueba",
            "date": "2026-11-01",
            "category": category,
        }

    def test_accident_searches_are_included(self):
        text = " ".join(LOCAL_EVENT_QUERIES).lower()
        for term in ("motociclista", "derrape", "choque", "volcadura", "atropellamiento"):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_road_crashes_are_mobility_even_from_security_feed(self):
        for title in (
            "Dos motociclistas lesionados tras choque en Iztapalapa",
            "Accidente de moto provoca cierre vial en la CDMX",
            "Volcadura de automóvil en avenida Insurgentes",
            "Atropellamiento en vialidad de Ciudad de México",
            "Motociclista derrapa en la alcaldía Tlalpan",
        ):
            with self.subTest(title=title):
                self.assertEqual(category_by_headline(title, "Seguridad"), "Movilidad")

    def test_crime_context_stays_in_security(self):
        title = "Persecución policial termina en choque y detención en CDMX"
        self.assertEqual(category_by_headline(title, "Seguridad"), "Seguridad")

    def test_unrelated_topics_keep_existing_categories(self):
        self.assertEqual(
            category_by_headline("Exhibición de motocicletas en museo de CDMX", "Cultura"),
            "Cultura",
        )

    def test_accidents_are_published_and_summarized_without_false_deaths(self):
        article = standardize(self.article(
            "Choque de motocicleta y tráiler genera afectaciones viales en CDMX"
        ))
        self.assertIsNotNone(article)
        self.assertEqual(article["category"], "Movilidad")
        lead = article["brief"]["lead"]
        self.assertIn("motocicleta", lead)
        self.assertIn("no permite determinar", lead)
        self.assertNotIn("consecuencias mortales", lead)

    def test_confirmed_death_is_reported_without_inventing_numbers(self):
        text = summarize(self.article(
            "Motociclista fallece tras choque en Iztapalapa"
        ))["lead"]
        self.assertIn("fallecimiento", text)
        self.assertIn("sin que esta ficha agregue cifras", text)


if __name__ == "__main__":
    unittest.main()
