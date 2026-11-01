"""Previene asignar fotos de patrullas a noticias de ciclismo o tecnología."""
import unittest

from scripts.notas_locales import _photo_category, _photo_score, assign_photos
from update_news import category_by_headline


class PhotoRelevanceTests(unittest.TestCase):
    def test_rss_category_uses_obvious_headline_subject(self):
        self.assertEqual(category_by_headline(
            "Muévete en Bici este 1 de noviembre", "Seguridad"), "Movilidad")
        self.assertEqual(category_by_headline(
            "Un robot en el centro de la Ciudad de México", "Seguridad"), "CDMX")
        self.assertEqual(category_by_headline(
            "Policía utiliza robot para investigar un robo", "Seguridad"), "Seguridad")

    def test_mismatched_patrol_image_is_rejected(self):
        patrol = {"topic": "Adquisición de patrullas para la Policía",
                  "category": "Seguridad", "keywords": ["seguridad"]}
        bike = {"title": "Muévete en Bici 1 de noviembre",
                "category": "Seguridad", "borough": ""}
        robot = {"title": "Un robot en el centro de la Ciudad de México",
                 "category": "Seguridad", "borough": ""}
        self.assertEqual(_photo_category(bike), "Movilidad")
        self.assertEqual(_photo_category(robot), "CDMX")
        self.assertLess(_photo_score(bike, patrol), 0)
        self.assertLess(_photo_score(robot, patrol), 0)

    def test_bike_photo_must_show_bicycle_context(self):
        bike = {"title": "Muévete en Bici 1 de noviembre",
                "category": "Seguridad", "borough": ""}
        generic_bus = {"topic": "Metrobús en Paseo de la Reforma",
                       "category": "Movilidad", "keywords": ["movilidad"]}
        real_bicycle = {"topic": "Bicicletas en una avenida de CDMX",
                        "category": "Alcaldías", "keywords": ["bicicleta"]}
        self.assertLess(_photo_score(bike, generic_bus), 0)
        self.assertGreaterEqual(_photo_score(bike, real_bicycle), 0)

    def test_published_choices_are_not_police_photos(self):
        articles = [
            {"title": "Muévete en Bici 1 de noviembre", "category": "Seguridad",
             "borough": "", "url": "https://news.google.com/rss/articles/bike"},
            {"title": "Un robot en el centro de la Ciudad de México",
             "category": "Seguridad", "borough": "",
             "url": "https://news.google.com/rss/articles/robot"},
        ]
        assign_photos(articles)
        for article in articles:
            with self.subTest(title=article["title"]):
                self.assertIn("photo", article)
                photo = article["photo"]
                self.assertNotEqual(photo.get("category"), "Seguridad")
                self.assertNotIn("patrulla", str(photo.get("topic")).lower())
                self.assertEqual(photo.get("kind"), "representativa")


if __name__ == "__main__":
    unittest.main()
