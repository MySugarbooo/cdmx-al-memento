"""Regresión: fotografía real del hecho solo si coincide y admite reutilización."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import update_news
from scripts import animales_feed
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

    def test_mexico_pachuca_pipa_reports_are_located_in_ecatepec(self):
        titles = (
            "Vuelca pipa de gas en la México-Pachuca; hay al menos 2 lesionados y caos vial con dirección a la CDMX",
            "Vuelca pipa de gas en la México-Pachuca y afecta tránsito a CDMX",
            "Vuelca pipa de gas LP en la México-Pachuca y colapsa el tráfico con dirección a CDMX",
            "Pipa de gas se vuelca en la autopista México-Pachuca; cierran carriles hacia Cdmx por emergencia",
        )
        for title in titles:
            with self.subTest(title=title):
                article = dict(ARTICLE, title=title, source="El Sol de México",
                               date="2026-11-11", category="Movilidad")
                borough, location = update_news.identify_location(title, article["date"])
                brief = photos.summarize(article)
                self.assertEqual(borough, "")
                self.assertEqual(location, "Ecatepec, Estado de México (fuera de CDMX)")
                self.assertIn("Ecatepec, Estado de México", brief["lead"])
                self.assertIn("una pipa de gas", brief["lead"])
                self.assertIn("fuera de la capital", brief["lead"])
                self.assertIn("La Jornada", brief["method"])

    def test_archive_cleanup_removes_sensitive_context_photos_and_keeps_verified_event_photo(self):
        title = "Caso Vadhir Derbez: Fiscalía CDMX tendría ADN relacionado con denuncia por violación"
        contextual = dict(ARTICLE, title=title, photo=context_photo("patrullas"))
        animal_title = "Detienen a acusado de maltrato animal en Tlalpan"
        animal_contextual = dict(ARTICLE, title=animal_title, photo=context_photo("conejo_bosque"))
        verified_photo = {
            "id": "hecho_aprobado",
            "kind": "hecho",
            "verified": True,
            "evidence_url": "https://ejemplo.org/evidencia",
        }
        documented = dict(ARTICLE, title=title, photo=verified_photo)
        removed = update_news.clear_sensitive_context_photos(
            [contextual, animal_contextual, documented]
        )
        self.assertEqual(removed, 2)
        self.assertTrue(contextual["sensitive_media"])
        self.assertNotIn("photo", contextual)
        self.assertTrue(animal_contextual["sensitive_media"])
        self.assertNotIn("photo", animal_contextual)
        self.assertIs(documented["photo"], verified_photo)

    def test_sensitive_media_headlines_never_receive_context_photos(self):
        titles = (
            "Caso Vadhir Derbez: Fiscalía CDMX tendría ADN relacionado con denuncia por violación",
            "Denuncian abuso sexual en una institución",
            "Investigan agresión sexual en la capital",
            "Denuncia por acoso sexual en un centro de trabajo",
            "Alerta por violencia sexual contra menores",
            "Detienen a hombre señalado de matar perros en la alcaldía Tlalpan",
            "Detienen a acusado de maltrato animal en Tlalpan",
            "Investigan crueldad animal tras envenenamiento de mascotas",
            "Envenenan a los perros de Xochimilco",
            "Más de 30 perritos envenenados en Xochimilco",
        )
        with TemporaryDirectory() as tmp:
            registry = Path(tmp) / "hechos.json"
            with patch.object(photos, "_pool", return_value=[context_photo("patrullas")]), patch.object(
                photos, "VERIFIED_EVENTS", registry
            ):
                for title in titles:
                    with self.subTest(title=title):
                        article = dict(ARTICLE, title=title, photo=context_photo("foto_anterior"))
                        photos.assign_photos([article])
                        self.assertTrue(article.get("sensitive_media"))
                        self.assertNotIn("photo", article)
        self.assertFalse(photos.is_sensitive_media(dict(
            ARTICLE, title="Rescatan perros en un refugio de Tlalpan"
        )))

    def test_homepage_feed_keeps_no_photo_stories_and_verified_event_images(self):
        sensitive = dict(
            ARTICLE,
            title="Detienen a acusado de maltrato animal en Tlalpan",
            url="https://news.google.com/rss/articles/animal-sensitive",
            local_url="/noticias/?id=animal-sensitive&mes=2026-11",
            sensitive_media=True,
            photo=context_photo("conejo_bosque"),
        )
        music = dict(
            ARTICLE,
            title="¡Tame Impala regresa a México en 2027! Dos noches en CDMX",
            url="https://news.google.com/rss/articles/tame-impala",
            local_url="/noticias/?id=tame-impala&mes=2026-11",
            photo=dict(
                context_photo("carnaval_cdmx"),
                topic="Declaratoria de Carnavales como Patrimonio Cultural Inmaterial de la Ciudad de México 13",
                keywords=["carnavales", "cultura"],
            ),
        )
        curated = dict(
            ARTICLE,
            title="Servicios de emergencia atienden percance de motociclista en Calzada Acoxpa",
            url="https://news.google.com/rss/articles/curated-incident",
            local_url="/noticias/?id=curated-incident&mes=2026-11",
            sensitive_media=True,
        )
        verified = dict(
            ARTICLE,
            title="Acontecimiento con fotografía documental verificada",
            url="https://news.google.com/rss/articles/verified-event",
            local_url="/noticias/?id=verified-event&mes=2026-11",
            photo=dict(
                context_photo("verified_event"),
                kind="hecho",
                verified=True,
                evidence_url="https://ejemplo.org/evidencia",
            ),
        )
        with patch.object(update_news, "dedupe_homepage_events", side_effect=lambda items: items):
            feed = update_news.build_homepage_feed([sensitive, music, curated, verified])

        self.assertEqual(len(feed), 2)
        self.assertIn(sensitive, feed)
        self.assertNotIn("photo", sensitive)
        self.assertNotIn(music, feed)
        self.assertNotIn("photo", music)
        self.assertNotIn(curated, feed)
        self.assertIn(verified, feed)
        self.assertEqual(verified["photo"]["kind"], "hecho")
        self.assertTrue(verified["photo"]["verified"])

    def test_animals_page_keeps_sensitive_headline_without_photo(self):
        title = "Detienen a acusado de maltrato animal en Tlalpan"
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "news.json"
            destination = Path(tmp) / "actualidad.html"
            source.write_text(json.dumps({"articles": [{
                "title": title,
                "url": "https://news.google.com/rss/articles/animal-sensitive",
                "date": "2026-11-12",
                "source": "El Universal",
                "location": "Tlalpan",
            }]}), encoding="utf-8")
            with patch.object(animales_feed, "SOURCE", source), patch.object(
                animales_feed, "DEST", destination
            ):
                animales_feed.build()
            page = destination.read_text(encoding="utf-8")
        self.assertIn(title, page)
        self.assertIn("Leer noticia original", page)

    def test_sensitive_media_allows_only_an_exact_approved_event_photo(self):
        title = "Caso Vadhir Derbez: Fiscalía CDMX tendría ADN relacionado con denuncia por violación"
        article = dict(ARTICLE, title=title)
        with TemporaryDirectory() as tmp:
            registry = Path(tmp) / "hechos.json"
            registry.write_text(json.dumps({"photos": [
                approval(article_url=article["url"], article_title=title)
            ]}), encoding="utf-8")
            with patch.object(photos, "_pool", return_value=[context_photo("patrullas")]), patch.object(
                photos, "VERIFIED_EVENTS", registry
            ):
                photos.assign_photos([article])
        self.assertEqual(article["photo"]["kind"], "hecho")
        self.assertTrue(article["photo"]["verified"])

        animal_title = "Detienen a acusado de maltrato animal en Tlalpan"
        animal_article = dict(
            ARTICLE, title=animal_title,
            url="https://news.google.com/rss/articles/animal-event-verified",
        )
        with TemporaryDirectory() as animal_tmp:
            animal_registry = Path(animal_tmp) / "hechos.json"
            animal_registry.write_text(json.dumps({"photos": [
                approval(article_url=animal_article["url"], article_title=animal_title)
            ]}), encoding="utf-8")
            with patch.object(photos, "_pool", return_value=[context_photo("conejo_bosque")]), patch.object(
                photos, "VERIFIED_EVENTS", animal_registry
            ):
                photos.assign_photos([animal_article])
        self.assertEqual(animal_article["photo"]["kind"], "hecho")
        self.assertTrue(animal_article["photo"]["verified"])

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
        self.assertEqual(update_news.category_by_headline(article["title"], "CDMX"), "Seguridad")
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

    def test_ssc_buen_fin_operativo_rejects_cybersecurity_photo_and_uses_patrol_context(self):
        title = ("2999: La SSC implementará un operativo de seguridad, vigilancia y vialidad "
                 "por el “Buen Fin 2026”, con la participación más de 16 mil policías en la ciudad de México")
        article = dict(
            ARTICLE,
            title=title,
            category="Metro",
            source="Secretaría de Seguridad Ciudadana de la CDMX",
        )
        laptop = dict(
            context_photo("laptop"),
            category="Seguridad",
            topic="Laptop asegurada con cadena y candado; fotografía representativa de seguridad informática",
            keywords=["ciberseguridad", "seguridad digital", "laptop"],
        )
        patrol = next(
            photo for photo in photos._pool()
            if photo["id"] == "archivo_seguridad_001"
        )

        self.assertEqual(photos._photo_category(article), "Seguridad")
        self.assertLess(photos._photo_score(article, laptop), 0)
        self.assertGreaterEqual(photos._photo_score(article, patrol), 0)

        with patch.object(photos, "_pool", return_value=[laptop, patrol]):
            with patch.object(
                photos,
                "VERIFIED_EVENTS",
                Path("/tmp/never-loaded-ssc-buen-fin-photo-registry.json"),
            ):
                stats = photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "archivo_seguridad_001")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(article["photo"]["author"], "Gobierno de la Ciudad de México")
        self.assertEqual(article["photo"]["license"], "CC BY 4.0")
        self.assertTrue(article["photo"]["source"].startswith("https://commons.wikimedia.org/wiki/File:"))
        self.assertEqual(stats["assigned"], 1)

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
        unrelated = dict(ARTICLE, title="Retrasos en el Metro de Iztapalapa", category="Metro", borough="Iztapalapa")
        self.assertLess(photos._photo_score(unrelated, pride), 0)

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


    def test_current_feed_incongruent_photos_are_rejected(self):
        def photo(id_, topic, category="CDMX", keywords=()):
            return dict(context_photo(id_), topic=topic, category=category, keywords=list(keywords))

        plaza_title = "¿Qué pasó en Plaza Meave hoy? Autoridades de CDMX realizan operativo"
        autoparts_title = "Decomisan 3 toneladas de autopartes en Alcaldía Cuauhtémoc"
        tabe_title = "Tabe en Miguel Hidalgo: cinco años de cambio"
        coyoacan_title = "Hemos cambiado y mejorado el rostro de Coyoacán: Giovani Gutierrez"
        cases = (
            (
                "De Polanco a Coyoacán: tres clubes de pádel en CDMX", "CDMX",
                photo("church_padel", "Iglesia de San Juan Bautista en Coyoacán, Ciudad de México", keywords=("Coyoacán",)),
            ),
            (
                "Refugio Franciscano busca frenar diligencia judicial en predio de Cuajimalpa", "Gobierno",
                photo("treasury_room", "Sala de Tesorería del Palacio Nacional, Ciudad de México", "Gobierno"),
            ),
            (
                "Armenta pide a Antorcha Campesina no manifestarse en CDMX", "CDMX",
                photo("carnival", "Declaratoria de Carnavales como Patrimonio Cultural de la Ciudad de México"),
            ),
            (
                "Trabajan Morelos, CDMX y Estado de México con colectivos en jornada de búsqueda", "CDMX",
                photo("garden", "Jardín Escénico del Bosque de Chapultepec, Ciudad de México"),
            ),
            (
                plaza_title, update_news.category_by_headline(plaza_title, "CDMX"),
                photo("zocalo", "Plaza de la Constitución, Zócalo de la Ciudad de México"),
            ),
            (
                autoparts_title, update_news.category_by_headline(autoparts_title, "CDMX"),
                photo("cuauhtemoc_bust", "Busto de Cuauhtémoc en la Ciudad de México"),
            ),
            (
                "CDMX Decomisa 3 Toneladas de Autopartes en Operativos Contra el Robo de Autos; Hay 3 Detenidos",
                "Seguridad",
                photo("cyber_laptop", "Laptop asegurada con cadena y candado; fotografía representativa de seguridad informática", "Seguridad"),
            ),
            (
                "Buen Fin 2026 en CDMX: así será el operativo de seguridad y cómo pedir escolta bancaria gratuita",
                "Seguridad",
                photo("cyber_laptop", "Laptop asegurada con cadena y candado; fotografía representativa de seguridad informática", "Seguridad", ("ciberseguridad", "seguridad digital")),
            ),
            (
                tabe_title, update_news.category_by_headline(tabe_title, "Seguridad"),
                photo("firefighters", "Equipo de trabajo de los Bomberos CDMX", "Seguridad"),
            ),
            (
                coyoacan_title, update_news.category_by_headline(coyoacan_title, "CDMX"),
                photo("historic_ticket", "Boleto de cine Esperanza Coyoacán, Ciudad de México"),
            ),
        )
        for title, category, image in cases:
            with self.subTest(title=title):
                article = dict(ARTICLE, title=title, category=category, borough="")
                self.assertLess(photos._photo_score(article, image), 0)

    def test_relevant_representative_photos_remain_eligible(self):
        def photo(id_, topic, category="CDMX", keywords=()):
            return dict(context_photo(id_), topic=topic, category=category, keywords=list(keywords))

        cases = (
            (
                "De Polanco a Coyoacán: tres clubes de pádel en CDMX", "CDMX",
                photo("padel_court", "Club de pádel, cancha deportiva y raquetas en CDMX", keywords=("pádel", "deporte")),
            ),
            (
                "Refugio Franciscano busca frenar diligencia judicial en predio de Cuajimalpa", "Gobierno",
                photo("dogs_context", "Perros descansando en el Parque España, Ciudad de México", "Medio Ambiente", ("perros", "mascotas")),
            ),
            (
                "Armenta pide a Antorcha Campesina no manifestarse en CDMX", "CDMX",
                photo("peace_march", "Ciudad Universitaria, marcha por la paz", "Cultura", ("marcha", "protesta")),
            ),
            (
                "Trabajan Morelos, CDMX y Estado de México con colectivos en jornada de búsqueda", "CDMX",
                photo("search_collective", "Colectivos de búsqueda de personas desaparecidas en campo", keywords=("personas desaparecidas",)),
            ),
            (
                "¿Qué pasó en Plaza Meave hoy? Autoridades de CDMX realizan operativo", "Seguridad",
                photo("police_jeep", "Jeep de la policía de la Ciudad de México", "Seguridad", ("policía", "patrulla")),
            ),
            (
                "Decomisan 3 toneladas de autopartes en Alcaldía Cuauhtémoc", "Seguridad",
                photo("police_patrol", "Patrulla de la Policía de la Ciudad de México", "Seguridad", ("policía", "patrulla")),
            ),
            (
                "Alerta por fraude cibernético en compras por internet en CDMX", "Seguridad",
                photo("cyber_laptop", "Laptop asegurada con cadena y candado; fotografía representativa de seguridad informática", "Seguridad", ("ciberseguridad", "seguridad digital")),
            ),
            (
                "Tabe en Miguel Hidalgo: cinco años de cambio", "Gobierno",
                photo("government_building", "Palacio Nacional, sede del Gobierno de México", "Gobierno", ("gobierno",)),
            ),
            (
                "Hemos cambiado y mejorado el rostro de Coyoacán: Giovani Gutierrez", "Gobierno",
                photo("coyoacan_church", "Iglesia de San Juan Bautista en Coyoacán, Ciudad de México", keywords=("Coyoacán",)),
            ),
            (
                "¡Así celebrará La Orquesta Mondragón su 50 aniversario en CDMX!", "CDMX",
                photo("cathedral_choir", "Coro de la Catedral Metropolitana de la Ciudad de México", keywords=("coro", "música")),
            ),
            (
                "Día del Soltero hoy: actividades en CDMX, escapadas y origen del 11/11", "Cultura",
                photo("coyoacan_market", "Mercado de Coyoacán, Ciudad de México", "Alcaldías", ("mercado", "Coyoacán")),
            ),
        )
        for title, category, image in cases:
            with self.subTest(title=title):
                borough = "Coyoacán" if title.startswith("Día del Soltero") else ""
                article = dict(ARTICLE, title=title, category=category, borough=borough)
                self.assertGreaterEqual(photos._photo_score(article, image), 0)

    def test_assign_photos_uses_relevant_context_and_skips_unrelated_images(self):
        def photo(id_, topic, category="CDMX", keywords=()):
            return dict(context_photo(id_), topic=topic, category=category, keywords=list(keywords))

        with patch.object(photos, "VERIFIED_EVENTS", Path("/tmp/never-loaded-photo-registry.json")):
            shelter = dict(
                ARTICLE,
                title="Refugio Franciscano busca frenar diligencia judicial en predio de Cuajimalpa",
                category="Gobierno",
            )
            treasury = photo("treasury_room", "Sala de Tesorería del Palacio Nacional", "Gobierno")
            dogs = photo("dogs_context", "Perros descansando en el Parque España", "Medio Ambiente", ("perros", "mascotas"))
            with patch.object(photos, "_pool", return_value=[treasury, dogs]):
                photos.assign_photos([shelter])
            self.assertEqual(shelter["photo"]["id"], "dogs_context")

            padel = dict(ARTICLE, title="De Polanco a Coyoacán: tres clubes de pádel en CDMX", category="CDMX")
            church = photo("church_padel", "Iglesia de San Juan Bautista en Coyoacán")
            with patch.object(photos, "_pool", return_value=[church]):
                stats = photos.assign_photos([padel])
            self.assertNotIn("photo", padel)
            self.assertEqual(stats["assigned"], 0)

            autoparts = dict(
                ARTICLE,
                title="CDMX Decomisa 3 Toneladas de Autopartes en Operativos Contra el Robo de Autos; Hay 3 Detenidos",
                category="Seguridad",
            )
            laptop = photo("cyber_laptop", "Laptop asegurada con cadena y candado; seguridad informática", "Seguridad")
            police = photo("police_patrol", "Patrulla de la Policía de la Ciudad de México", "Seguridad", ("policía", "patrulla"))
            with patch.object(photos, "_pool", return_value=[laptop, police]):
                photos.assign_photos([autoparts])
            self.assertEqual(autoparts["photo"]["id"], "police_patrol")

    def test_contraloria_article_uses_government_photo_not_cathedral_choir(self):
        title = "Contraloría de la Cdmx detecta observaciones por 839 mdp en fiscalización"
        category = update_news.category_by_headline(title, "CDMX")
        self.assertEqual(category, "Gobierno")
        article = dict(ARTICLE, title=title, category=category)
        choir = dict(
            context_photo("cathedral_choir"),
            topic="Coro de la Catedral metropolitana de la Ciudad de México 11",
            category="CDMX",
            keywords=["Catedral Metropolitana Ciudad de México"],
        )
        government = dict(
            context_photo("government_building"),
            topic="Fachada del Palacio Nacional, sede del Gobierno de México",
            category="Gobierno",
            keywords=["Gobierno", "Palacio Nacional"],
        )
        self.assertLess(photos._photo_score(article, choir), 0)
        self.assertGreaterEqual(photos._photo_score(article, government), 0)
        with patch.object(photos, "_pool", return_value=[choir, government]), patch.object(
            photos, "VERIFIED_EVENTS", Path("/tmp/never-loaded-contraloria-photo-registry.json")
        ):
            stats = photos.assign_photos([article])
        self.assertEqual(article["photo"]["id"], "government_building")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(stats["assigned"], 1)


    def test_plural_armed_attacks_against_delivery_riders_reject_unrelated_city_photo(self):
        title = "Agrupación de repartidores de aplicación documenta al menos 20 ataques armados en CDMX"
        category = update_news.category_by_headline(title, "CDMX", "La Jornada")
        self.assertEqual(category, "Seguridad")
        article = dict(ARTICLE, title=title, category=category)
        water_register = dict(
            context_photo("chapultepec_water_register"),
            topic="Registro de agua. Primera Sección del Bosque de Chapultepec - 4",
            category="CDMX",
            keywords=["Medio Ambiente"],
        )
        delivery_riders = dict(
            context_photo("delivery_riders"),
            topic="Repartidores de aplicación en motocicleta en Ciudad de México",
            category="CDMX",
            keywords=["repartidores", "motociclistas"],
        )
        patrol = dict(
            context_photo("security_patrol"),
            topic="Patrulla de la Policía de la Ciudad de México",
            category="Seguridad",
            keywords=["policía", "patrulla"],
        )

        self.assertEqual(photos._photo_category(article), "Seguridad")
        self.assertLess(photos._photo_score(article, water_register), 0)
        self.assertGreaterEqual(photos._photo_score(article, delivery_riders), 0)
        self.assertGreaterEqual(photos._photo_score(article, patrol), 0)

        with patch.object(photos, "_pool", return_value=[water_register, delivery_riders]), patch.object(
            photos,
            "VERIFIED_EVENTS",
            Path("/tmp/never-loaded-delivery-attack-photo-registry.json"),
        ):
            stats = photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "delivery_riders")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(stats["assigned"], 1)


    def test_fgr_ine_intervention_rejects_police_graduation_and_selects_patrol_context(self):
        title = "FGR interviene en oficinas de Administración del INE en Ciudad de México"
        article = dict(ARTICLE, title=title, category="Seguridad")
        graduation = dict(
            context_photo("commons_75245995"),
            topic="Graduación de la Policía de la Ciudad de México",
            category="Seguridad",
            keywords=["Policía Ciudad de México"],
        )
        patrol_acquisition = dict(
            context_photo("commons_157006042"),
            topic="Nuevas patrullas para Cuajimalpa 06",
            category="Seguridad",
            keywords=["Secretaría de Seguridad Ciudadana CDMX patrulla"],
        )
        patrol = dict(
            context_photo("commons_102129730"),
            topic="Patrulla cdmx",
            category="Seguridad",
            keywords=["Seguridad", "Patrulla CDMX"],
        )

        self.assertLess(photos._photo_score(article, graduation), 0)
        self.assertLess(photos._photo_score(article, patrol_acquisition), 0)
        self.assertGreaterEqual(photos._photo_score(article, patrol), 0)

        with patch.object(photos, "_pool", return_value=[graduation, patrol_acquisition, patrol]), patch.object(
            photos,
            "VERIFIED_EVENTS",
            Path("/tmp/never-loaded-fgr-ine-photo-registry.json"),
        ):
            stats = photos.assign_photos([article])

        self.assertEqual(article["photo"]["id"], "commons_102129730")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(stats["assigned"], 1)

if __name__ == "__main__":
    unittest.main()
