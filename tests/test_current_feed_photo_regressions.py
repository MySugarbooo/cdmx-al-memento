"""Regresiones editoriales de fotografías del feed vigente de CDMX AL MEMENTO."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import scripts.notas_locales as photos
import update_news as news

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "news.json"


class CurrentFeedPhotoRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.articles = json.loads(FEED.read_text(encoding="utf-8"))["articles"]
        context_file = ROOT / "assets/fotos/contexto-tematico.json"
        cls.photo_pool = {
            item["id"]: item
            for item in json.loads(context_file.read_text(encoding="utf-8"))["photos"]
        }

    def find_article(self, fragment):
        normalized = fragment.casefold()
        return deepcopy(next((
            item for item in self.articles
            if normalized in str(item.get("title") or "").casefold()
        ), None))

    def assert_reassigned(self, fragment, expected_photo_id):
        article = self.find_article(fragment)
        if article is None:
            return False
        current = article.get("photo") if isinstance(article.get("photo"), dict) else {}
        target = deepcopy(self.photo_pool[expected_photo_id])
        self.assertGreater(photos._photo_score(article, target), 0)
        if current.get("id") != expected_photo_id:
            if current:
                self.assertTrue(
                    news.photo_needs_refresh(article),
                    f"La fotografía incorrecta no fue marcada para revisión: {article.get('title')}",
                )
            else:
                self.assertFalse(photos.is_sensitive_media(article))
            with patch.object(photos, "_pool", return_value=[target]), patch.object(
                photos, "_load", return_value=[]
            ):
                photos.assign_photos([article])
        self.assertEqual(article.get("photo", {}).get("id"), expected_photo_id)
        self.assertEqual(article["photo"].get("kind"), "representativa")
        for field in ("url", "source", "author", "license", "licenseUrl"):
            self.assertTrue(article["photo"].get(field), f"Falta {field} en {article['title']}")
        self.assertTrue(article["photo"]["source"].startswith("https://commons.wikimedia.org/wiki/File:"))
        self.assertTrue(article["photo"]["licenseUrl"].startswith("https://creativecommons.org/"))
        return True

    def test_panda_story_uses_chapultepec_panda_archive_photo(self):
        if not self.assert_reassigned("nuevo oso panda", "contexto_panda_chapultepec_2015"):
            self.skipTest("La noticia del panda ya no está en el feed vigente.")

    def test_roller_derby_story_uses_roller_derby_archive_photo(self):
        if not self.assert_reassigned("subcampeonato nacional de roller derby", "contexto_roller_derby_toulouse_2012"):
            self.skipTest("La noticia de roller derby ya no está en el feed vigente.")

    def test_juan_gabriel_postal_exhibition_uses_the_actual_venue(self):
        if not self.assert_reassigned("juan gabriel en el palacio postal", "contexto_palacio_postal_2010"):
            self.skipTest("La noticia del Palacio Postal ya no está en el feed vigente.")

    def test_electric_personal_vehicle_registration_stories_use_micromobility_photo(self):
        checked = 0
        for fragment in (
            "vehículos eléctricos personales",
            "amplía plazo para registrar vehículos eléctricos personales",
            "vehículos motorizados eléctricos",
            "prorrogan registro de vehículos eléctricos en cdmx",
            "monopatines y bicicletas eléctricas",
        ):
            with self.subTest(fragment=fragment):
                checked += bool(self.assert_reassigned(fragment, "contexto_grin_escooter_cdmx_2019"))
        if not checked:
            self.skipTest("Las noticias de vehículos eléctricos ya no están en el feed vigente.")

    def test_gallinas_program_stories_use_a_gallinero_archive_photo(self):
        checked = 0
        for fragment in (
            "regalar gallinas ponedoras",
            "entrega de gallinas ponedoras",
            "gallinas en casa",
        ):
            with self.subTest(fragment=fragment):
                checked += bool(self.assert_reassigned(fragment, "contexto_gallinero_chinampa_xochimilco"))
        if not checked:
            self.skipTest("Las noticias del programa de gallinas ya no están en el feed vigente.")

    def test_corona_capital_story_uses_the_same_venue_as_context(self):
        if not self.assert_reassigned("corona capital 2026", "contexto_concierto_foro_sol_2023"):
            self.skipTest("La noticia de Corona Capital ya no está en el feed vigente.")

    def test_cdmx_blockade_alternatives_use_a_cdmx_traffic_photo(self):
        if not self.assert_reassigned("atorado en los bloqueos", "contexto_trafico_eje_central"):
            self.skipTest("La noticia de bloqueos ya no está en el feed vigente.")

    def test_early_childhood_stories_use_a_cendi_archive_photo(self):
        checked = 0
        for fragment in (
            "primera infancia",
            "educación inicial pública y gratuita",
            "300 espacios de educación inicial",
        ):
            with self.subTest(fragment=fragment):
                checked += bool(self.assert_reassigned(fragment, "contexto_cendi_pilares_vc_2019"))
        if not checked:
            self.skipTest("Las noticias de educación inicial ya no están en el feed vigente.")

    def test_cendi_archive_photo_has_explicit_historical_context_and_credit(self):
        photo = self.photo_pool["contexto_cendi_pilares_vc_2019"]
        self.assertEqual(photo["author"], "Gobierno de la Ciudad de México")
        self.assertEqual(photo["license"], "CC BY 4.0")
        self.assertEqual(photo["licenseUrl"], "https://creativecommons.org/licenses/by/4.0/")
        self.assertEqual(photo["source"], "https://commons.wikimedia.org/wiki/File:CENDI_PILARES_04.jpg")
        self.assertEqual(photo["captured_at"], "2019-06-25")
        self.assertIn("no es uno de los nuevos centros", photo["topic"])
        self.assertIn("no constituye evidencia gráfica", photo["context"])
        self.assertEqual(photo["kind"], "representativa")

    def test_animal_poisoning_story_remains_without_a_context_photo(self):
        article = self.find_article("envenenamiento de perros en xochimilco")
        if article is None:
            self.skipTest("La noticia de envenenamiento ya no está en el feed vigente.")
        self.assertTrue(photos.is_sensitive_media(article))
        with patch.object(photos, "_pool", return_value=[]), patch.object(
            photos, "_load", return_value=[]
        ):
            photos.assign_photos([article])
        self.assertNotIn("photo", article)


if __name__ == "__main__":
    unittest.main()
