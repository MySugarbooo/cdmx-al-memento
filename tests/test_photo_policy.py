"""Regresión: fotografía real del hecho solo si coincide y admite reutilización."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import update_news
from scripts import notas_locales as photos


ARTICLE = {
    "title": "Incidente verificado en CDMX",
    "url": "https://news.google.com/rss/articles/evento-test",
    "date": "2026-10-30",
    "category": "CDMX",
    "borough": "",
}


def approval(**overrides):
    data = {
        "article_url": ARTICLE["url"],
        "article_title": ARTICLE["title"],
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/evento.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Evento.jpg",
        "evidence_url": "https://ejemplo.org/cobertura/acontecimiento",
        "author": "Fotógrafa acreditada",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        "topic": "Acontecimiento documentado",
        "event_match_confirmed": True,
        "rights_confirmed": True,
        "reviewed_by": "Edición responsable",
        "reviewed_at": "2026-10-30T10:00:00Z",
    }
    data.update(overrides)
    return data


def context_photo(id_="archivo_prueba"):
    return {
        "id": id_, "kind": "representativa",
        "url": "/assets/fotos/" + id_ + ".jpg",
        "category": "CDMX", "borough": "",
        "topic": "Vista general de la ciudad",
        "source": "https://commons.wikimedia.org/wiki/File:Ciudad.jpg",
        "author": "Autor de contexto",
        "license": "CC BY 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
    }


class NewsPhotoPolicyTests(unittest.TestCase):
    def test_only_reviewed_licensed_exact_event_can_be_labelled_as_such(self):
        result = photos.verified_event_photo(ARTICLE, [approval()])
        self.assertEqual(result["kind"], "hecho")
        self.assertTrue(result["verified"])
        self.assertEqual(result["author"], "Fotógrafa acreditada")

    def test_similar_title_copyright_or_unproven_event_never_count_as_real(self):
        for changes in (
            {"article_title": "Otra noticia del mismo tema"},
            {"article_url": "https://news.google.com/rss/articles/otra"},
            {"event_match_confirmed": False},
            {"rights_confirmed": False},
            {"evidence_url": ""},
            {"reviewed_by": ""},
            {"reviewed_at": "no revisado"},
            {"license": "CC BY-NC 4.0"},
            {"licenseUrl": "https://creativecommons.org/licenses/by-nc/4.0/"},
            {"source": "https://unperiodico.example/foto.jpg"},
            {"url": "https://medio.example/foto.jpg"},
        ):
            with self.subTest(changes=changes):
                self.assertIsNone(photos.verified_event_photo(ARTICLE, [approval(**changes)]))

    def test_context_photo_matches_exact_metro_line_not_another_line(self):
        article = dict(ARTICLE, title="Usuarios del Metro caminan por la Línea 12", category="Metro")
        line_two = dict(context_photo("linea_2"), topic="Metro Línea 2 CDMX", category="Metro")
        generic = dict(context_photo("metro_generico"), topic="Metro de la Ciudad de México", category="Metro")
        line_twelve = dict(context_photo("linea_12"), topic="Metro Línea 12 CDMX", category="Metro")
        old_accident = dict(context_photo("accidente_2021"),
                            topic="Incidente Línea 12 Ciudad México 2021", category="Metro")
        self.assertLess(photos._photo_score(article, line_two), 0)
        self.assertLess(photos._photo_score(article, old_accident), 0)
        self.assertGreater(photos._photo_score(article, line_twelve),
                           photos._photo_score(article, generic))
        with patch.object(photos, "_pool", return_value=[line_two, generic, line_twelve, old_accident]):
            with patch.object(photos, "VERIFIED_EVENTS", Path("/tmp/never-loaded-photo-registry.json")):
                photos.assign_photos([article])
        self.assertEqual(article["photo"]["id"], "linea_12")
        self.assertEqual(article["photo"]["kind"], "representativa")


    def test_plural_metro_line_list_rejects_unlisted_lines(self):
        cases = (
            (
                "Metro CDMX: Alta afluencia y retrasos en Líneas 3, 7, 12 y A este miércoles",
                "Afluencia Ferrería-Arena Ciudad de México Línea 6 (2024)",
                "Metro Línea 12 CDMX",
            ),
            (
                "Metro CDMX hoy: retrasos y trenes llenos afectan las Líneas 7, 12 y B",
                "Estación Pino Suárez de la Línea 1 del Metro de la Ciudad de México 01",
                "Metro Línea 12 CDMX",
            ),
        )
        generic = dict(
            context_photo("metro_generico"),
            topic="Metro de la Ciudad de México",
            category="Metro",
        )
        for title, unrelated_topic, matching_topic in cases:
            with self.subTest(title=title):
                article = dict(ARTICLE, title=title, category="Metro")
                unrelated = dict(
                    context_photo("linea_no_mencionada"),
                    topic=unrelated_topic,
                    category="Metro",
                )
                matching = dict(
                    context_photo("linea_mencionada"),
                    topic=matching_topic,
                    category="Metro",
                )
                self.assertLess(photos._photo_score(article, unrelated), 0)
                self.assertGreater(
                    photos._photo_score(article, matching),
                    photos._photo_score(article, generic),
                )

        article = dict(ARTICLE, title=cases[0][0], category="Metro")
        line_six = dict(
            context_photo("linea_6"),
            topic=cases[0][1],
            category="Metro",
        )
        line_twelve = dict(
            context_photo("linea_12"),
            topic=cases[0][2],
            category="Metro",
        )
        with patch.object(photos, "_pool", return_value=[line_six, generic, line_twelve]):
            with patch.object(photos, "VERIFIED_EVENTS", Path("/tmp/never-loaded-photo-registry.json")):
                photos.assign_photos([article])
        self.assertEqual(article["photo"]["id"], "linea_12")
        self.assertEqual(article["photo"]["kind"], "representativa")

    def test_gas_explosion_uses_bomberos_photo_not_unrelated_drainage(self):
        article = dict(
            ARTICLE,
            title="Explosión de gas en local de Azcapotzalco: Baches, socavones y otras afectaciones en CDMX hoy",
            category="CDMX",
        )
        drainage = dict(
            context_photo("desazolve"),
            topic="Programa de desazolves 2019 04",
            category="CDMX",
            keywords=["Drenaje Ciudad de México"],
        )
        firefighters = dict(
            context_photo("bomberos"),
            topic="Equipo de trabajo de los Bomberos CDMX IMG 2922",
            category="Seguridad",
            keywords=["Bomberos Ciudad de México"],
        )

        self.assertEqual(photos._photo_category(article), "Seguridad")
        self.assertLess(photos._photo_score(article, drainage), 0)
        self.assertGreaterEqual(photos._photo_score(article, firefighters), 0)

        with patch.object(photos, "_pool", return_value=[drainage, firefighters]):
            with patch.object(
                photos,
                "VERIFIED_EVENTS",
                Path("/tmp/never-loaded-gas-photo-registry.json"),
            ):
                stats = photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "bomberos")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(stats["assigned"], 1)

    def test_adaptive_sports_story_uses_wheelchair_basketball_context(self):
        article = dict(
            ARTICLE,
            title="Plantean a Clara Brugada festival de deporte adaptado para personas con discapacidad motriz en CDMX",
            category="Gobierno",
        )
        unrelated = dict(
            context_photo("bellas_artes"),
            topic="Palacio de Bellas Artes, Ciudad de México",
            category="Cultura",
            keywords=["Cultura"],
        )
        wheelchair = next(
            photo for photo in photos._pool()
            if photo["id"] == "contexto_baloncesto_silla_ruedas"
        )

        self.assertLess(photos._photo_score(article, unrelated), 0)
        self.assertGreaterEqual(photos._photo_score(article, wheelchair), 0)
        self.assertEqual(wheelchair["author"], "2010 World Wheelchair Basketball Championship")
        self.assertEqual(wheelchair["license"], "CC BY 2.0")
        self.assertTrue(wheelchair["source"].startswith("https://commons.wikimedia.org/wiki/File:"))

        with patch.object(
            photos,
            "VERIFIED_EVENTS",
            Path("/tmp/never-loaded-adaptive-sports-photo-registry.json"),
        ):
            stats = photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "contexto_baloncesto_silla_ruedas")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(stats["assigned"], 1)

    def test_subject_outranks_generic_category_or_unrelated_picture(self):
        examples = (
            ("Desfile de Catrinas en el Zócalo de CDMX", "Cultura",
             ("desfile", "Desfile de Catrinas Ciudad de México", "CDMX"),
             ("museo", "Palacio de Bellas Artes Ciudad de México", "Cultura")),
            ("Rescatan perritos en parque de la capital", "Seguridad",
             ("animales", "Animales Bosque de Tlalpan", "Medio Ambiente"),
             ("patrulla", "Patrulla CDMX", "Seguridad")),
            ("Problemas en Iztapalapa", "CDMX",
             ("iztapalapa", "Panorama de Iztapalapa", "Alcaldías"),
             ("reforma", "Paseo de la Reforma", "CDMX")),
        )
        for title, category, preferred, other in examples:
            with self.subTest(title=title):
                article=dict(ARTICLE,title=title,category=category)
                if "Iztapalapa" in title:
                    article["borough"]="Iztapalapa"
                important=dict(context_photo(preferred[0]),topic=preferred[1],category=preferred[2])
                generic=dict(context_photo(other[0]),topic=other[1],category=other[2])
                self.assertGreater(photos._photo_score(article,important),
                                   photos._photo_score(article,generic))

    def test_exact_preferred_then_licensed_representative(self):
        with TemporaryDirectory() as tmp:
            registry = Path(tmp) / "hechos.json"
            registry.write_text(json.dumps({"photos": [approval()]}), encoding="utf-8")
            with patch.object(photos, "VERIFIED_EVENTS", registry), patch.object(
                photos, "_pool", return_value=[context_photo()]
            ):
                article = dict(ARTICLE)
                stats = photos.assign_photos([article])
                self.assertEqual(stats["del_hecho_verificadas"], 1)
                self.assertEqual(article["photo"]["kind"], "hecho")
                registry.write_text(json.dumps({"photos": []}), encoding="utf-8")
                article["photo"] = approval(kind="hecho", verified=True, id="hecho_antiguo")
                stats = photos.assign_photos([article])
                self.assertEqual(stats["del_hecho_verificadas"], 0)
                self.assertEqual(article["photo"]["kind"], "representativa")
                self.assertFalse(article["photo"].get("verified", False))

    def test_cable_theft_is_security_and_requires_security_context_photo(self):
        title = "Detienen a hombre por robo de cable de alumbrado público en Iztapalapa"
        article = dict(ARTICLE, title=title, category="CDMX", borough="Iztapalapa")
        metro = dict(
            context_photo("metro_iztapalapa"),
            topic="Metro Iztapalapa 02",
            category="Alcaldías",
            keywords=["Iztapalapa Ciudad de México"],
        )
        patrol = dict(
            context_photo("archivo_seguridad_002"),
            topic="Patrulla vecinal",
            category="Seguridad",
            keywords=["patrulla", "seguridad"],
        )

        self.assertEqual(update_news.category_by_headline(title, "CDMX"), "Seguridad")
        self.assertEqual(
            update_news.category_by_headline(
                "Robo de cable de alumbrado público en Iztapalapa", "CDMX"
            ),
            "Seguridad",
        )
        archived = update_news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/cable-theft-test",
            "source": "Sociedad Noticias",
            "date": "2026-11-11",
            "category": "CDMX",
            "photo": metro,
        })
        self.assertEqual(archived["category"], "Seguridad")
        self.assertLess(photos._photo_score(archived, archived["photo"]), 0)
        self.assertLess(photos._photo_score(article, metro), 0)
        self.assertGreaterEqual(photos._photo_score(article, patrol), 0)

        with patch.object(photos, "_pool", return_value=[metro, patrol]):
            with patch.object(
                photos,
                "VERIFIED_EVENTS",
                Path("/tmp/never-loaded-cable-theft-photo-registry.json"),
            ):
                photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "archivo_seguridad_002")
        self.assertEqual(article["photo"]["kind"], "representativa")


    def test_iztapalapa_lgbtttiq_support_cut_uses_government_and_pride_context(self):
        title = "Iztapalapa recorta 83% el apoyo a población LGBTTTIQ+"
        article = dict(
            ARTICLE,
            title=title,
            source="24-horas",
            category=update_news.category_by_headline(title, "CDMX"),
            borough="Iztapalapa",
            location="Iztapalapa (mencionada en el titular)",
        )
        self.assertEqual(article["category"], "Gobierno")

        brief = photos.summarize(article)
        self.assertIn("400 beneficiarios en 2026, frente a 1,400 en 2025", brief["lead"])
        self.assertIn("siete millones de pesos en 2025 y de 1.2 millones en 2026", brief["lead"])
        self.assertIn("83% del titular se refiere al recorte presupuestal", brief["lead"])
        self.assertIn("cuerpo de la nota de 24-horas", brief["method"])

        metro = dict(
            context_photo("metro_iztapalapa"),
            topic="Metro Iztapalapa 02",
            category="Alcaldías",
            keywords=["Iztapalapa Ciudad de México"],
        )
        pride = next(
            (photo for photo in photos._pool()
             if photo["id"] == "reciente_19fe4dac412af46a"),
            None,
        )
        self.assertIsNotNone(pride)
        self.assertEqual(pride["author"], "TSolange")
        self.assertEqual(pride["license"], "CC BY-SA 4.0")
        self.assertLess(photos._photo_score(article, metro), 0)
        self.assertGreaterEqual(photos._photo_score(article, pride), 0)

        with patch.object(photos, "_pool", return_value=[metro, pride]), patch.object(
            photos,
            "VERIFIED_EVENTS",
            Path("/tmp/never-loaded-lgbtttiq-photo-registry.json"),
        ):
            stats = photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "reciente_19fe4dac412af46a")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(article["photo"]["author"], "TSolange")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertEqual(stats["assigned"], 1)


if __name__ == "__main__":
    unittest.main()
