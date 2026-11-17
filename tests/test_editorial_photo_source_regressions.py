"""Regresiones editoriales de fuentes y fotos para noticias de noviembre de 2026."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import scripts.notas_locales as photos
import update_news as news
from update_news import category_by_headline


class CurrentEditorialPhotoSourceRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = {photo["id"]: photo for photo in photos._pool()}

    def _assert_photo_replaced(self, article, wrong_id, preferred_id):
        wrong = deepcopy(self.pool[wrong_id])
        preferred = deepcopy(self.pool[preferred_id])
        article["photo"] = wrong
        self.assertLess(photos._photo_score(article, wrong), 0)
        self.assertEqual(photos._photo_score(article, preferred), 5000)
        with patch.object(photos, "_pool", return_value=[wrong, preferred]), patch.object(
            photos, "_load", return_value=[]
        ):
            photos.assign_photos([article])
        self.assertEqual(article["photo"]["id"], preferred_id)
        self.assertEqual(article["photo"]["kind"], "representativa")
        for field in ("source", "author", "license", "licenseUrl"):
            self.assertTrue(article["photo"].get(field), field)

    def test_maya_november_20_parade_has_mobility_category_source_and_monument_photo(self):
        title = "Desfile del 20 de noviembre: ruta, horario y cierres en la CDMX"
        self.assertEqual(
            category_by_headline(title, "Seguridad", "Maya Comunicación"),
            "Movilidad",
        )
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/maya-desfile-20-noviembre-2026",
            "source": "Maya Comunicación",
            "date": "2026-11-16",
            "published_at": "2026-11-17T02:58:59Z",
            "category": "Seguridad",
        })
        self.assertIsNotNone(article)
        self.assertTrue(photos.is_maya_revolucion_desfile_2026(article))
        self.assertEqual(article["category"], "Movilidad")
        self.assertEqual(article["source_url"], news.MAYA_REVOLUCION_DESFILE_SOURCE_URL)
        self.assertEqual(article["borough"], "Cuauhtémoc")
        self.assertIn("10:00", article["brief"]["lead"])
        self.assertIn("Zócalo", article["brief"]["lead"])
        self.assertIn("Monumento a la Revolución", article["brief"]["lead"])
        self.assertIn("5 de Mayo", article["brief"]["lead"])
        self.assertIn("cierres", article["brief"]["context"].lower())
        self._assert_photo_replaced(
            article,
            "reciente_a5a3bc52fa77c066",
            "contexto_monumento_revolucion_desfile_2026",
        )
        self.assertEqual(article["photo"]["author"], "CésarRood")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertIn("no del desfile de 2026", article["photo"]["topic"])

    def test_benito_juarez_detention_uses_patrol_not_earthquake_reconstruction_photo(self):
        title = (
            "Detienen a sujeto en la alcaldía Benito Juárez tras agredir y privar "
            "de la libertad a una joven en su departamento"
        )
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/diario-mexico-benito-juarez-detencion-2026",
            "source": "Diario de México",
            "date": "2026-11-16",
            "published_at": "2026-11-16T22:47:48Z",
            "category": "Seguridad",
        })
        self.assertIsNotNone(article)
        self.assertTrue(photos.is_diario_mexico_benito_juarez_detention_story(article))
        self.assertEqual(article["category"], "Seguridad")
        self.assertEqual(
            article["source_url"],
            news.DIARIO_MEXICO_BENITO_JUAREZ_DETENTION_SOURCE_URL,
        )
        self.assertEqual(article["borough"], "Benito Juárez")
        self.assertIn("SSC", article["brief"]["lead"])
        self.assertIn("Blindar BJ", article["brief"]["lead"])
        self.assertIn("FGJCDMX", article["brief"]["lead"])
        self.assertIn("presunción de inocencia", article["brief"]["pending"])
        self.assertIn("no precisa calle", article["location"])
        self._assert_photo_replaced(
            article,
            "contexto_reconstruccion_edificios_benito_juarez_2019",
            "seguridad",
        )
        self.assertEqual(article["photo"]["author"], "RainerRowe")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertIn("Patrulla", article["photo"]["topic"])

    def test_rafael_castro_story_uses_original_as_source_and_licensed_basketball_context(self):
        title = "Rafael Castro asciende de Capitanes CDMX a los Atlanta Hawks de la NBA"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/as-mexico-rafael-castro-capitanes-atlanta-2026",
            "source": "AS México",
            "date": "2026-11-16",
            "published_at": "2026-11-17T05:53:20Z",
            "category": "CDMX",
        })
        self.assertIsNotNone(article)
        self.assertTrue(photos.is_rafael_castro_capitanes_nba_story(article))
        self.assertEqual(article["source_url"], news.AS_MEXICO_RAFAEL_CASTRO_SOURCE_URL)
        self.assertIn("contrato de dos vías", article["brief"]["lead"])
        self.assertIn("Atlanta Hawks", article["brief"]["lead"])
        self.assertIn("College Park Skyhawks", article["brief"]["lead"])
        self.assertIn("décimo", article["brief"]["context"])
        self.assertIn("no había anunciado", article["brief"]["pending"])
        self._assert_photo_replaced(article, "commons_66033711", "commons_58302191")
        self.assertEqual(article["photo"]["author"], "Daniel Case")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 3.0")
        self.assertIn("no muestra a Rafael Castro ni a Capitanes", article["photo"]["topic"])
        self.assertLessEqual(len(article["photo"]["topic"]), 150)


if __name__ == "__main__":
    unittest.main()
