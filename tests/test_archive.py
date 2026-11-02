"""Pruebas básicas del archivo de un año y metadatos editoriales."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import update_news as news
from scripts.notas_locales import _photo_category


def fake(title, date, published_at=None):
    return {
        "title": title, "source": "Medio de prueba",
        "url": "https://news.google.com/rss/articles/example" + date.replace("-", ""),
        "date": date, "published_at": published_at,
        "category": "CDMX",
    }


class BoroughAndArchiveTests(unittest.TestCase):
    def test_first_boroughs_and_exact_mentions(self):
        self.assertEqual(news.BOROUGHS[:2], ("La Magdalena Contreras", "Álvaro Obregón"))
        self.assertEqual(news.identify_location("Noticias en Magdalena Contreras")[0], "La Magdalena Contreras")
        self.assertEqual(news.identify_location("Cierre vial en Álvaro Obregón CDMX")[0], "Álvaro Obregón")
        self.assertEqual(news.identify_location("Incidente en Iztapalapa")[0], "Iztapalapa")
        self.assertEqual(news.identify_location("En Coyoacán y Tlalpan")[0], "")
        self.assertEqual(news.identify_location("Los planes del Metro CDMX")[0], "")

    def test_person_detentions_from_government_feed_are_security(self):
        title = "Detienen a tres hombres por obras irregulares en Tláhuac"
        self.assertEqual(news.category_by_headline(title, "Gobierno"), "Seguridad")
        article = fake(title, "2026-11-01")
        article["category"] = "Gobierno"
        fixed = news.standardize(article)
        self.assertEqual(fixed["category"], "Seguridad")
        self.assertEqual(fixed["borough"], "Tláhuac")
        # Detener obras o servicios no equivale a detener personas.
        self.assertEqual(news.category_by_headline(
            "Detienen obras irregulares en Tláhuac", "Gobierno"), "Gobierno")
        self.assertEqual(news.category_by_headline(
            "Detienen el servicio de agua por reparaciones", "Gobierno"), "Gobierno")
        self.assertEqual(news.category_by_headline(
            "Capturan a dos sospechosos en CDMX", "CDMX"), "Seguridad")

    def test_hoy_no_circula_is_mobility_and_rejects_catrina_photos(self):
        title = "Día de Muertos, no de multas: Así aplica el Hoy No Circula este lunes 2 de noviembre"
        self.assertEqual(news.category_by_headline(title, "CDMX"), "Movilidad")
        self.assertEqual(news.category_by_headline(title, "Cultura"), "Movilidad")
        article = fake(title, "2026-11-01")
        self.assertEqual(news.standardize(article)["category"], "Movilidad")
        self.assertEqual(_photo_category(article), "Movilidad")
        self.assertLess(news._photo_score(article, {
            "category": "CDMX", "topic": "Desfile de Catrinas in Mexico City 2026 (53)",
        }), 0)
        self.assertLess(news._photo_score(article, {
            "category": "Cultura", "topic": "Día de Muertos y desfile de Catrinas",
        }), 0)
        self.assertGreaterEqual(news._photo_score(article, {
            "category": "Movilidad", "topic": "Tráfico vehicular en Paseo de la Reforma",
        }), 0)

    def test_road_closures_are_mobility_and_reject_patrol_photos(self):
        article = fake("GP de México 2026: Calles Cerradas y Alternativas Viales en CDMX", "2026-11-01")
        article["category"] = "Seguridad"  # Clasificación de origen RSS.
        article["photo"] = {
            "id": "patrullas", "kind": "representativa",
            "category": "Seguridad", "topic": "Nuevas patrullas para Cuajimalpa",
            "url": "/assets/fotos/patrullas.jpg",
        }
        fixed = news.standardize(article)
        self.assertEqual(fixed["category"], "Movilidad")
        self.assertLess(news._photo_score(fixed, fixed["photo"]), 0)
        self.assertLess(news._photo_score(fixed, {
            "id": "ecobici", "kind": "representativa",
            "category": "Movilidad", "topic": "Ecobici Estación 15",
        }), 0)
        self.assertGreaterEqual(news._photo_score(fixed, {
            "id": "avenida", "kind": "representativa",
            "category": "Movilidad", "topic": "Tráfico vehicular en avenida Reforma",
        }), 0)
        self.assertEqual(news.category_by_headline(
            "Cierre vial en Xochimilco", "Seguridad"), "Movilidad")
        self.assertEqual(news.category_by_headline(
            "Detienen a dos tras cierre vial por balacera", "Seguridad"), "Seguridad")

    def test_specific_news_photos_reject_unrelated_subjects(self):
        # Tres fotografías efectivamente detectadas en la portada del 1 de noviembre.
        fountain = {"title": "ONU premia rescate de la Fuente Iztaccíhuatl en Cuauhtémoc",
                    "category": "CDMX", "borough": "Cuauhtémoc"}
        self.assertLess(news._photo_score(fountain, {
            "category": "Alcaldías", "topic": "Rescate de Unidades Habitacionales Alcaldía Cuauhtémoc 02",
            "keywords": ["Cuauhtémoc alcaldía Ciudad de México"],
        }), 0)
        self.assertGreaterEqual(news._photo_score(fountain, {
            "category": "CDMX", "topic": "Fuente monumental en plaza de Ciudad de México",
        }), 0)

        motorcycles = {"title": "Al corralón más de 500 motos en Rodada del Terror en CDMX",
                       "category": "Seguridad"}
        self.assertLess(news._photo_score(motorcycles, {
            "category": "Seguridad", "topic": "Protección civil CDMX",
        }), 0)
        self.assertGreaterEqual(news._photo_score(motorcycles, {
            "category": "Seguridad", "topic": "Rodada de motociclistas en CDMX",
        }), 0)

        racing = {"title": "Bandera roja en CDMX por accidente de Bottas",
                  "category": "Movilidad"}
        self.assertLess(news._photo_score(racing, {
            "category": "Movilidad", "topic": "Mexico City Metrobus Hamburgo Station",
        }), 0)
        self.assertGreaterEqual(news._photo_score(racing, {
            "category": "Movilidad", "topic": "Autódromo Hermanos Rodríguez, circuito de carreras",
        }), 0)
        # Etiquetas genéricas como "Calles Ciudad de México" no vuelven
        # pertinente una foto de carnavales para un operativo del GP.
        gp_security = {"title": "GP de México: detienen a 30 y detectan acreditaciones falsas",
                       "category": "Seguridad"}
        self.assertLess(news._photo_score(gp_security, {
            "category": "CDMX", "topic": "Declaratoria de carnavales como patrimonio cultural",
            "keywords": ["Calles Ciudad de México"],
        }), 0)
        self.assertGreaterEqual(news._photo_score(gp_security, {
            "category": "CDMX", "topic": "Autódromo Hermanos Rodríguez",
        }), 0)
        # También cubre titulares de la Rodada del Terror que dicen
        # "vehículos" en lugar de "motos".
        rodada = {"title": "Remiten 515 vehículos durante la Mega Rodada del Terror 2026",
                  "category": "Seguridad"}
        self.assertLess(news._photo_score(rodada, {
            "category": "Seguridad", "topic": "Graduación de la Policía de CDMX",
        }), 0)
        # No afectar la noticia distinta sobre cierres viales del GP.
        closures = {"title": "GP de México: Calles Cerradas y Alternativas Viales en CDMX",
                    "category": "Movilidad"}
        self.assertGreaterEqual(news._photo_score(closures, {
            "category": "Movilidad", "topic": "Tráfico vehicular en avenida Reforma",
        }), 0)
        self.assertLess(news._photo_score(closures, {
            "category": "Movilidad", "topic": "Trolebús Línea 2 sobre Avenida Yucatán",
        }), 0)
        self.assertLess(news._photo_score(gp_security, {
            "category": "CDMX", "topic": "Calles Seminario y Moneda Centro Histórico",
        }), 0)

    def test_new_headlines_require_relevant_photo_context(self):
        # Ejemplos publicados el 1 de noviembre, no fotografías del hecho.
        children = {"title": "¡Los niños también van a las urnas! CDMX abre consulta para menores",
                    "category": "CDMX"}
        self.assertLess(news._photo_score(children, {
            "category": "CDMX", "topic": "Ciudad de México en cuarentena 1",
        }), 0)
        self.assertGreaterEqual(news._photo_score(children, {
            "category": "CDMX", "topic": "Consulta infantil con urnas y boletas",
        }), 0)

        winter = {"title": "CDMX pone en marcha programa de atención por temporada invernal",
                  "category": "CDMX"}
        self.assertLess(news._photo_score(winter, {
            "category": "Movilidad", "topic": "Metrobús en Paseo de la Reforma",
        }), 0)
        self.assertGreaterEqual(news._photo_score(winter, {
            "category": "CDMX", "topic": "Albergue de invierno y entrega de cobijas",
        }), 0)

        racing = {"title": "Alonso abandonó en Ciudad de México", "category": "CDMX"}
        self.assertLess(news._photo_score(racing, {
            "category": "CDMX", "topic": "Trajineras en Xochimilco",
        }), 0)
        self.assertGreaterEqual(news._photo_score(racing, {
            "category": "CDMX", "topic": "Autódromo Hermanos Rodríguez circuito",
        }), 0)

    def test_november_photo_context_rejects_unrelated_stock_images(self):
        # Imágenes observadas en news.json público: ninguna es foto del hecho.
        cases = [
            ("Aeropuerto Internacional de la Ciudad de México: estatus de vuelos demorados",
             "Monumento a Colón Paseo de la Reforma", "Terminal aérea del aeropuerto de la CDMX"),
            ("La Ciudad de México inicia noviembre con mañanas frías y rachas de viento",
             "Cosecha de Lluvia 04", "Nubes y viento sobre Ciudad de México"),
            ("Microbús Atropella y Mata a un Hombre en Azcapotzalco",
             "Parroquia de Santa Catarina, Azcapotzalco", "Microbús en avenida de Ciudad de México"),
            ("Día de Muertos en CDMX, más de 11 mil policías cuidan dichas festividades",
             "Museo de Arte Moderno", "Patrullas de policía en operativo de vigilancia"),
            ("Detienen a tres hombres por construcción irregular en Tláhuac",
             "Plaza central de San Pedro Tláhuac", "Policías de la Fiscalía de CDMX"),
            ("Activista denuncia envenenamientos de perros en Xochimilco",
             "Animales Bosque de Tlalpan 04", "Perros en un parque de la ciudad"),
            ("Azcapotzalco lidera empleo de mujeres CDMX",
             "Ciclovía en proceso en Azcapotzalco", "Mujeres trabajadoras en oficinas"),
            ("Morena se reunió con más de 6 mil militantes en la CDMX",
             "Ciudad de México Alameda Central", "Reunión política de militantes de Morena"),
            ("Asamblea comunitaria determina relevo de autoridades auxiliares en Álvaro Obregón",
             "Avenida Álvaro Obregón, Colonia Roma", "Asamblea comunitaria de vecinos"),
        ]
        for title, unrelated, relevant in cases:
            article = {"title": title, "category": "CDMX"}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": "CDMX", "topic": unrelated,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": "CDMX", "topic": relevant,
                }), 0)
        police = {"title": "Día de Muertos, policías cuidan festividades",
                  "category": "Seguridad"}
        self.assertEqual(_photo_category(police), "Seguridad")

    def test_new_photo_guardrails_reject_mismatched_landmarks(self):
        # Fotografías representativas sí, pero no iglesias para muertes,
        # parques para mascotas, ni edificios de gobierno para bloqueos.
        cases = [
            ("Fallece Juan Atkins, pionero de la música techno, en la CDMX",
             "Iglesia de San Juan Bautista en Coyoacán", "DJ en escenario de música techno"),
            ("Perritos piden calaverita en la Central de Abastos",
             "Parque Lira Ciudad de México", "Perros y mascotas en una plaza"),
            ("Matan a Balazos a un Hombre en Azcapotzalco",
             "Parroquia de Santa Catarina", "Edificio de la Fiscalía de CDMX"),
            ("Coyoacán sin agua las próximas 40 horas",
             "Plaza central de Coyoacán", "Tuberías de abastecimiento de agua"),
            ("Fallece motociclista en la México-Cuernavaca",
             "Ángel de la Independencia en la noche", "Motocicletas en carretera"),
            ("Colectivo de Búsqueda Bloquea Avenida Juárez",
             "Sala de Tesorería en Palacio Nacional", "Protesta en avenida Juárez"),
            ("Panteón donde descansan ídolos de México",
             "Plaza central de San Pedro Tláhuac", "Panteón y tumbas históricas"),
            ("Gran Desfile de Día de Muertos reúne a miles",
             "Exposición en el Museo Nacional de Antropología", "Desfile de Catrinas"),
            ("Recuerdo de Bono del concierto de U2 en CDMX",
             "Ciudad Universitaria dedication plaque", "Concierto de música rock"),
            ("Trámite de licencia de conducir permanente",
             "Palacio Nacional Ciudad de México", "Trámite de licencia de conducir"),
            ("Cuál es la calidad del aire en CDMX",
             "Alameda Central desde el aire", "Contaminación del aire en CDMX"),
        ]
        for title, unrelated, relevant in cases:
            article = {"title": title, "category": "CDMX"}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": "CDMX", "topic": unrelated,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": "CDMX", "topic": relevant,
                }), 0)

    def test_protest_and_crime_photos_need_more_than_shared_category(self):
        blockade = {"title": "Colectivo de Búsqueda Bloquea Avenida Juárez",
                    "category": "Movilidad"}
        self.assertLess(news._photo_score(blockade, {
            "category": "Movilidad",
            "topic": "Trolebús de la Línea 2 sobre Avenida Yucatán",
        }), 0)
        self.assertGreaterEqual(news._photo_score(blockade, {
            "category": "CDMX", "topic": "Protesta de colectivo en la ciudad",
        }), 0)
        crime = {"title": "Matan a Balazos a un Hombre en Azcapotzalco",
                 "category": "Seguridad"}
        self.assertLess(news._photo_score(crime, {
            "category": "Seguridad",
            "topic": "Graduación de la Policía de la Ciudad de México",
        }), 0)
        self.assertLess(news._photo_score(crime, {
            "category": "Seguridad",
            "topic": "Entrega Claudia Sheinbaum 113 nuevas patrullas en Gustavo A Madero",
        }), 0)
        self.assertGreaterEqual(news._photo_score(crime, {
            "category": "CDMX", "topic": "Edificio de la Fiscalía de CDMX",
        }), 0)

    def test_editorial_headline_categories_for_crime_parade_and_road(self):
        self.assertEqual(news.category_by_headline(
            "Matan a Balazos a un Hombre en Azcapotzalco", "CDMX"), "Seguridad")
        self.assertEqual(news.category_by_headline(
            "Condenan a un hombre a prisión en CDMX", "CDMX"), "Seguridad")
        self.assertEqual(news.category_by_headline(
            "Gran Desfile de Día de Muertos reúne a miles", "Seguridad"), "Cultura")
        self.assertEqual(news.category_by_headline(
            "Colectivo de Búsqueda Bloquea Avenida Juárez", "Gobierno"), "Movilidad")
        self.assertEqual(news.category_by_headline(
            "Fallece motociclista en la México-Cuernavaca", "CDMX"), "Movilidad")
        self.assertEqual(news.category_by_headline(
            "Desfile de policías por operativo de seguridad", "Seguridad"), "Seguridad")

    def test_unambiguous_outside_region_is_not_promoted_or_mislocated(self):
        title = "Muere conductor tras chocar contra autobús en Carretera a Laredo en Escobedo"
        self.assertTrue(news.outside_cdmx_scope(title))
        veracruz = ("Las fincas de café de Veracruz donde ves la pizca, "
                    "el tostado y la cata: cuánto cuesta el recorrido "
                    "en este Pueblo Mágico a 4 horas y media de CDMX")
        self.assertTrue(news.outside_cdmx_scope(veracruz))
        self.assertEqual(news.identify_location(veracruz)[1], "Veracruz (fuera de CDMX)")
        veracruz_article = news.standardize(fake(veracruz, datetime.now(timezone.utc).date().isoformat()))
        self.assertLess(news._photo_score(veracruz_article, {
            "category": "CDMX", "topic": "Iglesia de San Matías en Iztacalco",
        }), 0)
        self.assertEqual(news.homepage_articles([veracruz_article], [], datetime.now(timezone.utc)), [])
        self.assertFalse(news.outside_cdmx_scope("Feria de café de Veracruz se celebra en CDMX"))
        spain = "México confirma once connacionales heridos en el accidente de tren en España"
        self.assertTrue(news.outside_cdmx_scope(spain))
        self.assertEqual(news.identify_location(spain)[1], "España (fuera de CDMX)")
        self.assertFalse(news.outside_cdmx_scope("Exposición sobre trenes de España en CDMX"))
        self.assertFalse(news.outside_cdmx_scope("Familias acuden a panteones de CdMx y Monterrey"))
        self.assertFalse(news.outside_cdmx_scope("Cierre vial en la alcaldía Xochimilco"))
        self.assertFalse(news.outside_cdmx_scope("CDMX y Escobedo: carreteras a Laredo en discusión"))
        date = datetime.now(timezone.utc).date().isoformat()
        outside = news.standardize(fake(title, date))
        local = news.standardize(fake("Cierre vial en Xochimilco CDMX", date))
        self.assertEqual(outside["location"], "Escobedo, Nuevo León (fuera de CDMX)")
        self.assertEqual(news.homepage_articles([outside, local], [], datetime.now(timezone.utc)),
                         [local])
        # El registro puede conservarse en la hemeroteca; solo se evita
        # su incorporación a la portada de noticias de CDMX.

    def test_source_time_is_real_or_missing(self):
        now="2026-10-11T23:40:00Z"
        article=news.standardize(fake("Una noticia sobre Xochimilco en CDMX", "2026-10-11", now))
        self.assertEqual(article["published_at"], now)
        self.assertEqual(article["borough"], "Xochimilco")
        self.assertEqual(article["date"], "2026-10-11")
        legacy=news.standardize(fake("Una noticia sobre Xochimilco en CDMX", "2026-10-11"))
        self.assertIsNone(legacy["published_at"])
        self.assertEqual(legacy["location"], "Xochimilco (mencionada en el titular)")

    def test_older_than_365_days_expires_even_within_month(self):
        now=datetime.now(timezone.utc)
        cutoff=now-timedelta(days=365)
        expired=(now-timedelta(days=366)).date().isoformat()
        kept=(now-timedelta(days=364)).date().isoformat()
        old=news.standardize(fake("Titular antiguo del Metro CDMX", expired))
        current=news.standardize(fake("Titular reciente en Xochimilco", kept))
        self.assertFalse(news.still_valid(old, cutoff))
        self.assertTrue(news.still_valid(current, cutoff))

    def test_months_merge_and_old_files_deleted(self):
        now=datetime.now(timezone.utc)
        date=(now-timedelta(days=1)).date().isoformat()
        earlier=(now-timedelta(days=400)).date().isoformat()
        story=news.standardize(fake("Reunión comunitaria en Magdalena Contreras", date))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/"archivo"
            archive.mkdir()
            # Un archivo de un mes vencido no debe mantenerse.
            news.write_json(archive/(earlier[:7]+".json"), {
                "month":earlier[:7],
                "articles":[news.standardize(fake("Información vencida en CDMX", earlier))]
            })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root/"alcaldias", DEST=root/"news.json"):
                months=news.consolidate_archive([story], now-timedelta(days=365), "Prueba")
                self.assertEqual(len(months), 1)
                self.assertEqual(months[0]["month"], date[:7])
                self.assertFalse((archive/(earlier[:7]+".json")).exists())
                saved=json.loads((archive/(date[:7]+".json")).read_text(encoding="utf-8"))
                self.assertEqual(len(saved["articles"]), 1)
                self.assertEqual(saved["articles"][0]["borough"], "La Magdalena Contreras")
                directory=json.loads((root/"alcaldias"/"noticias.json").read_text(encoding="utf-8"))
                self.assertEqual(len(directory["boroughs"]), 16)


    def test_archive_repairs_unrelated_photo_and_preserves_verified_photo(self):
        now = datetime.now(timezone.utc)
        date = (now - timedelta(days=1)).date().isoformat()
        old = news.standardize(fake("Muévete en Bici recorre seis alcaldías", date))
        old["category"] = "Seguridad"  # Etiqueta RSS anterior, corregida al releer.
        old["photo"] = {
            "id": "patrullas", "kind": "representativa",
            "category": "Seguridad", "topic": "Entrega de patrullas",
            "url": "/assets/fotos/patrullas.jpg",
        }
        verified = news.standardize(fake("Ciclistas recorren avenida de CDMX", date))
        verified["photo"] = {
            "id": "hecho_confirmado", "kind": "hecho", "verified": True,
            "category": "Movilidad", "topic": "Ciclistas en la avenida",
            "url": "/assets/fotos/hecho_confirmado.jpg",
        }

        def assign_replacement(items):
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["category"], "Movilidad")
            items[0]["photo"] = {
                "id": "bicicletas", "kind": "representativa",
                "category": "Movilidad", "topic": "Estación de bicicletas",
                "url": "/assets/fotos/bicicletas.jpg",
            }
            return {"assigned": 1}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archivo"
            archive.mkdir()
            news.write_json(archive / (date[:7] + ".json"), {
                "month": date[:7], "articles": [old, verified],
            })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root / "alcaldias",
                                DEST=root / "news.json"):
                with patch.object(news, "assign_photos", side_effect=assign_replacement) as replacement:
                    news.consolidate_archive([], now - timedelta(days=365), "Prueba")
                    replacement.assert_called_once()
            saved = json.loads((archive / (date[:7] + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(len(saved["articles"]), 2)
            by_title = {item["title"]: item for item in saved["articles"]}
            self.assertEqual(by_title[old["title"]]["photo"]["id"], "bicicletas")
            self.assertEqual(by_title[verified["title"]]["photo"]["id"], "hecho_confirmado")


    def test_archive_prioritizes_recent_mismatched_photos(self):
        now = datetime.now(timezone.utc)
        records = {}
        for age in range(26, 0, -1):
            day = (now - timedelta(days=age)).date().isoformat()
            item = news.standardize(fake(f"Muévete en Bici recorre seis alcaldías {age}", day))
            item["category"] = "Seguridad"
            item["photo"] = {
                "id": f"patrullas_{age}", "kind": "representativa",
                "category": "Seguridad", "topic": "Entrega de patrullas",
                "url": "/assets/fotos/patrullas.jpg",
            }
            records.setdefault(day[:7], []).append(item)

        selected = []

        def repair(items):
            selected.extend(item["date"] for item in items)
            for item in items:
                item["photo"] = {
                    "id": "bici", "kind": "representativa",
                    "category": "Movilidad", "topic": "Bicicletas",
                    "url": "/assets/fotos/bicicletas.jpg",
                }
            return {"assigned": len(items)}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archivo"
            archive.mkdir()
            for month, articles in records.items():
                news.write_json(archive / (month + ".json"), {
                    "month": month, "articles": articles,
                })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root / "alcaldias",
                                DEST=root / "news.json"):
                with patch.object(news, "assign_photos", side_effect=repair):
                    news.consolidate_archive([], now - timedelta(days=365), "Prueba")

        self.assertEqual(len(selected), 24)
        self.assertEqual(selected[0], (now - timedelta(days=1)).date().isoformat())
        self.assertEqual(selected[-1], (now - timedelta(days=24)).date().isoformat())


    def test_recent_archive_restores_homepage_when_only_curated_news_arrives(self):
        now = datetime(2026, 11, 1, 22, 10, tzinfo=timezone.utc)
        curated = news.standardize(fake(
            "Accidente de motocicleta confirmado en CDMX", "2026-11-01",
            (now - timedelta(minutes=5)).isoformat()))
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archivo"
            archive.mkdir()
            recent = []
            for i in range(14):
                stamp = now - timedelta(minutes=15 + i)
                item = fake(f"Reporte de movilidad en CDMX número {i}", "2026-11-01",
                            stamp.isoformat())
                item["url"] = f"https://news.google.com/rss/articles/recent{i}"
                recent.append(news.standardize(item))
            expired = news.standardize(fake(
                "Noticia antigua de movilidad en CDMX", "2026-10-20",
                "2026-10-20T10:00:00+00:00"))
            news.write_json(archive / "2026-11.json", {"articles": recent})
            news.write_json(archive / "2026-10.json", {"articles": [expired]})
            with patch.object(news, "ARCHIVE_DIR", archive):
                result = news.fill_recent_from_archive([curated], now)
        self.assertEqual(len(result), 15)
        self.assertEqual(len({news.article_key(x) for x in result}), 15)
        self.assertIn(curated["title"], [x["title"] for x in result])
        self.assertNotIn(expired["title"], [x["title"] for x in result])



if __name__ == "__main__":
    unittest.main()
