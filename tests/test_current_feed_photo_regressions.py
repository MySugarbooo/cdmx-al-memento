"""Regresiones editoriales de fotografías del feed vigente de CDMX AL MEMENTO."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.notas_locales as photos
import update_news as news

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "news.json"


class CurrentFeedPhotoRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.articles = json.loads(FEED.read_text(encoding="utf-8"))["articles"]

    def find_article(self, fragment):
        normalized = fragment.casefold()
        return deepcopy(next(
            item for item in self.articles
            if normalized in str(item.get("title") or "").casefold()
        ))

    def assert_reassigned(self, fragment, expected_photo_id):
        article = self.find_article(fragment)
        self.assertTrue(
            news.photo_needs_refresh(article),
            f"La fotografía actual ya no parece incongruente: {article.get('title')}",
        )
        photos.assign_photos([article])
        self.assertEqual(article.get("photo", {}).get("id"), expected_photo_id)
        self.assertEqual(article["photo"].get("kind"), "representativa")
        for field in ("url", "source", "author", "license", "licenseUrl"):
            self.assertTrue(article["photo"].get(field), f"Falta {field} en {article['title']}")

    def test_panda_story_uses_chapultepec_panda_archive_photo(self):
        self.assert_reassigned("nuevo oso panda", "contexto_panda_chapultepec_2015")

    def test_roller_derby_story_uses_roller_derby_archive_photo(self):
        self.assert_reassigned("subcampeonato nacional de roller derby", "contexto_roller_derby_toulouse_2012")

    def test_juan_gabriel_postal_exhibition_uses_the_actual_venue(self):
        self.assert_reassigned("juan gabriel en el palacio postal", "contexto_palacio_postal_2010")

    def test_electric_personal_vehicle_registration_stories_use_micromobility_photo(self):
        for fragment in (
            "vehículos eléctricos personales",
            "vehículos motorizados eléctricos",
            "prorrogan registro de vehículos eléctricos en cdmx",
            "monopatines y bicicletas eléctricas",
        ):
            with self.subTest(fragment=fragment):
                self.assert_reassigned(fragment, "contexto_grin_escooter_cdmx_2019")

    def test_gallinas_program_stories_use_a_gallinero_archive_photo(self):
        for fragment in (
            "regalar gallinas ponedoras",
            "entrega de gallinas ponedoras",
            "gallinas en casa",
        ):
            with self.subTest(fragment=fragment):
                self.assert_reassigned(fragment, "contexto_gallinero_chinampa_xochimilco")

    def test_corona_capital_story_uses_the_same_venue_as_context(self):
        self.assert_reassigned("corona capital 2026", "contexto_concierto_foro_sol_2023")

    def test_cdmx_blockade_alternatives_use_a_cdmx_traffic_photo(self):
        self.assert_reassigned("atorado en los bloqueos", "contexto_trafico_eje_central")

    def test_animal_poisoning_story_remains_without_a_context_photo(self):
        article = self.find_article("envenenamiento de perros en xochimilco")
        self.assertTrue(photos.is_sensitive_media(article))
        photos.assign_photos([article])
        self.assertNotIn("photo", article)


if __name__ == "__main__":
    unittest.main()
