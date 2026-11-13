"""Previene asignar fotos de patrullas a noticias de ciclismo o tecnología."""
import unittest
from unittest.mock import patch

from scripts.notas_locales import _pool, _photo_category, _photo_score, assign_photos
import update_news as news
import scripts.notas_locales as photos
from update_news import category_by_headline

def representative_photo(photo_id, category, topic, keywords):
    return {
        "id": photo_id,
        "kind": "representativa",
        "category": category,
        "topic": topic,
        "keywords": keywords,
        "url": "/assets/fotos/regression-test.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Regression_test.jpg",
        "author": "Autor de prueba",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
    }


class PhotoRelevanceTests(unittest.TestCase):
    def test_rss_category_uses_obvious_headline_subject(self):
        self.assertEqual(category_by_headline(
            "Muévete en Bici este 1 de noviembre", "Seguridad"), "Movilidad")
        self.assertEqual(category_by_headline(
            "Un robot en el centro de la Ciudad de México", "Seguridad"), "CDMX")
        self.assertEqual(category_by_headline(
            "Policía utiliza robot para investigar un robo", "Seguridad"), "Seguridad")

    def test_robar_infinitive_classifies_store_robbery_and_rejects_city_landmark(self):
        title = ("2996: En la alcaldía Venustiano Carranza, efectivos de la SSC "
                 "detuvieron a dos posibles responsables de robar dinero en efectivo "
                 "de una tienda de conveniencia")
        source = "Secretaría de Seguridad Ciudadana de la CDMX"
        self.assertEqual(category_by_headline(title, "CDMX", source), "Seguridad")
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/robbery-ssc-regression",
            "source": source,
            "date": "2026-11-12",
            "category": "CDMX",
            "photo": {
                "id": "commons_36264294",
                "category": "CDMX",
                "topic": "Monumento a Colón Paseo de la Reforma Ciudad de México 2",
                "keywords": ["Paseo de la Reforma Ciudad de México"],
                "author": "ProtoplasmaKid",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Monumento_a_Col%C3%B3n_Paseo_de_la_Reforma_Ciudad_de_M%C3%A9xico_2.jpg",
                "url": "/assets/fotos/monumento-colon.jpg",
            },
        })
        self.assertEqual(article["category"], "Seguridad")
        landmark = {
            "category": "CDMX",
            "topic": "Monumento a Colón Paseo de la Reforma Ciudad de México 2",
            "keywords": ["Paseo de la Reforma Ciudad de México"],
        }
        patrol = {
            "category": "Seguridad",
            "topic": "Patrulla de Ciudad de México",
            "keywords": ["policía CDMX"],
        }
        self.assertLess(_photo_score(article, landmark), 0)
        self.assertGreaterEqual(_photo_score(article, patrol), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["category"], "Seguridad")
        self.assertGreaterEqual(_photo_score(article, article["photo"]), 0)

    def test_execution_headline_uses_security_and_rejects_ciclovia_photo(self):
        title = "VIDEO | Ejecutan a un hombre en la colonia Libertad, alcaldía Azcapotzalco"
        self.assertEqual(category_by_headline(title, "CDMX"), "Seguridad")
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/execution-regression",
            "source": "Diario de México",
            "date": "2026-11-11",
            "category": "CDMX",
        })
        self.assertEqual(article["category"], "Seguridad")
        ciclovia = {
            "category": "Alcaldías",
            "topic": "Ciclovía en proceso en la Alcaldía Azcapotzalco",
            "keywords": ["Azcapotzalco Ciudad de México"],
        }
        patrol = {
            "category": "Seguridad",
            "topic": "Jeep policia cdmx",
            "keywords": ["policia"],
        }
        self.assertLess(_photo_score(article, ciclovia), 0)
        self.assertGreaterEqual(_photo_score(article, patrol), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["category"], "Seguridad")
        self.assertTrue(any(word in article["photo"]["topic"].casefold()
                            for word in ("policia", "patrulla")))

    def test_nfl_event_is_not_metro_and_uses_licensed_football_photo(self):
        title = ("NFL en México: estas son todas las actividades que podrás disfrutar "
                 "en las calles de la CDMX previo al juego de San Francisco 49ers "
                 "vs Minnesota Vikings")
        self.assertEqual(category_by_headline(title, "Metro"), "CDMX")
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/nfl-regression",
            "source": "Infobae",
            "date": "2026-11-11",
            "category": "Metro",
        })
        self.assertEqual(article["category"], "CDMX")
        self.assertNotIn("servicio del Metro", article["brief"]["lead"])
        metro = {
            "category": "Metro",
            "topic": "Estación Ermita de la Línea 12 del Metro de la Ciudad de México",
            "keywords": ["Metro Ciudad de México"],
        }
        self.assertLess(_photo_score(article, metro), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_futbol_americano_nfl")
        self.assertEqual(article["photo"]["author"], "Torsten Bolten, AFpix.de")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 3.0")

    def test_ecatepec_archive_alternates_are_normalized_without_losing_source_metadata(self):
        title = (
            "Vuelca pipa de gas en la México-Pachuca; hay al menos 2 lesionados "
            "y caos vial con dirección a la CDMX"
        )
        url = "https://news.google.com/rss/articles/ecatepec-archive-version-regression"
        stale_photo = {
            "id": "commons_firefighters_cdmx",
            "kind": "representativa",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/example.jpg",
            "topic": "Equipo de trabajo de los Bomberos CDMX",
            "author": "Gobierno CDMX",
            "license": "CC0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/deed.en",
            "source": "https://commons.wikimedia.org/wiki/File:Bomberos_CDMX.jpg",
        }
        stale_brief = {
            "lead": "La pipa volcó en la capital.",
            "context": "Contexto anterior.",
            "pending": "Pendiente anterior.",
            "method": "Método anterior.",
        }
        article = news.standardize({
            "title": title,
            "url": url,
            "source": "El Sol de México",
            "date": "2026-11-12",
            "category": "Movilidad",
            "alternate_versions": [{
                "title": title,
                "url": url,
                "source": "El Sol de México",
                "date": "2026-11-11",
                "published_at": "2026-11-11T19:23:33Z",
                "category": "Movilidad",
                "borough": "",
                "location": "Ciudad de México (sin alcaldía identificada)",
                "local_url": "/noticias/?id=ecatepec-archive&mes=2026-11",
                "brief": stale_brief,
                "photo": stale_photo,
            }],
        })

        self.assertEqual(article["location"], "Ecatepec, Estado de México (fuera de CDMX)")
        self.assertEqual(news.sanitize_outside_cdmx_versions(article), 1)
        version = article["alternate_versions"][0]
        self.assertEqual(version["location"], article["location"])
        self.assertEqual(version["source"], "El Sol de México")
        self.assertEqual(version["url"], url)
        self.assertEqual(version["date"], "2026-11-11")
        self.assertIn("Ecatepec, Estado de México", version["brief"]["lead"])
        self.assertIn("al menos dos personas lesionadas", version["brief"]["lead"])
        self.assertNotIn("en la capital", version["brief"]["lead"])
        self.assertNotIn("photo", version)

    def test_gas_tanker_rollovers_are_mobility_and_reject_cdmx_photos_outside_cdmx(self):
        titles = [
            "Vuelca pipa de gas en la México-Pachuca; hay al menos 2 lesionados y caos vial con dirección a la CDMX",
            "Vuelca pipa de gas LP en la México-Pachuca y colapsa el tráfico con dirección a CDMX",
            "Pipa de gas se vuelca en la autopista México-Pachuca; cierran carriles hacia Cdmx por emergencia",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertEqual(category_by_headline(title, "CDMX"), "Movilidad")

        article = news.standardize({
            "title": titles[0],
            "url": "https://news.google.com/rss/articles/gas-tanker-rollover-regression",
            "source": "El Sol de México",
            "date": "2026-11-11",
            "category": "CDMX",
        })
        self.assertEqual(article["category"], "Movilidad")
        self.assertEqual(article["location"], "Ecatepec, Estado de México (fuera de CDMX)")
        self.assertIn("una pipa de gas", article["brief"]["lead"])
        self.assertIn("al menos dos personas lesionadas", article["brief"]["lead"])
        self.assertEqual(_photo_category(article), "Seguridad")
        police_graduation = {
            "category": "Seguridad",
            "topic": "Graduación de la Policía de la Ciudad de México",
            "keywords": ["Policía Ciudad de México"],
        }
        metrobus = {
            "category": "Movilidad",
            "topic": "Mexico City Metrobus Line 1 Durango station",
            "keywords": ["Metrobús Ciudad de México"],
        }
        firefighters = {
            "category": "Seguridad",
            "topic": "Equipo de trabajo de los Bomberos CDMX IMG 2922",
            "keywords": ["Bomberos Ciudad de México"],
        }
        self.assertLess(_photo_score(article, police_graduation), 0)
        self.assertLess(_photo_score(article, metrobus), 0)
        self.assertLess(_photo_score(article, firefighters), 0)
        assign_photos([article])
        self.assertNotIn("photo", article)

    def test_paseo_tollocan_rollover_is_located_in_edomex_and_has_no_cdmx_photo(self):
        title = (
            "Caos vial en Paseo Tollocan rumbo a CDMX por volcadura de pipa con gas LP"
        )
        cdmx_firefighters = {
            "id": "commons_75139345",
            "kind": "representativa",
            "category": "Seguridad",
            "topic": "Equipo de trabajo de los Bomberos CDMX IMG 3039",
            "keywords": ["Bomberos Ciudad de México"],
            "author": "Gobierno CDMX",
            "license": "CC0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/deed.en",
            "source": "https://commons.wikimedia.org/wiki/File:Equipo_de_trabajo_de_los_Bomberos_CDMX_IMG_3039_(29724113197).jpg",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6f/Equipo_de_trabajo_de_los_Bomberos_CDMX_IMG_3039_(29724113197).jpg/960px-Equipo_de_trabajo_de_los_Bomberos_CDMX_IMG_3039_(29724113197).jpg",
        }
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/paseo-tollocan-rollover-regression",
            "source": "Diario Evolución",
            "date": "2026-11-12",
            "category": "Movilidad",
            "photo": cdmx_firefighters,
        })

        self.assertEqual(article["category"], "Movilidad")
        self.assertEqual(article["borough"], "")
        self.assertEqual(
            article["location"],
            "Santa María Totoltepec, Toluca, Estado de México (fuera de CDMX)",
        )
        self.assertTrue(news.headline_has_cdmx_signal(title))
        self.assertTrue(news.local_for_homepage(article))
        self.assertIn("Santa María Totoltepec", article["brief"]["lead"])
        self.assertIn("Toluca, Estado de México", article["brief"]["lead"])
        self.assertIn("carriles laterales", article["brief"]["lead"])
        self.assertNotIn("en la capital", article["brief"]["lead"].casefold())
        self.assertIn("SéUno Noticias", article["brief"]["method"])

        # Una fotografía identificada como Bomberos CDMX no debe ilustrar
        # un incidente situado en Toluca, aunque el trayecto afectado vaya a CDMX.
        with patch.object(photos, "_pool", return_value=[cdmx_firefighters]):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_chinampas_single_day_and_license_photos_need_matching_topics(self):
        chinampas = {
            "title": "Arca Tierra y Lucio Usobiaga reciben reconocimiento por proteger las chinampas de Xochimilco",
            "category": "CDMX", "borough": "",
        }
        xochimilco_plaza = {
            "category": "CDMX",
            "topic": "Explanada Delegación Xochimilco, Ciudad de México",
            "keywords": ["CDMX"],
        }
        xochimilco_canals = {
            "category": "CDMX",
            "topic": "Canales de Xochimilco, Ciudad de México",
            "keywords": ["Xochimilco Ciudad de México"],
        }
        self.assertLess(_photo_score(chinampas, xochimilco_plaza), 0)
        self.assertGreaterEqual(_photo_score(chinampas, xochimilco_canals), 0)

        single_day = {
            "title": "Día del Soltero hoy: Actividades en CDMX, escapadas y origen del 11/11",
            "category": "Cultura", "borough": "",
        }
        unrelated_unam = {
            "category": "Cultura",
            "topic": "Recepción de Marichuy Patricio en Ciudad Universitaria UNAM 06",
            "keywords": ["Ciudad Universitaria UNAM Ciudad de México"],
        }
        market = {
            "category": "Alcaldías",
            "topic": "MX MM COYOACÁN - Mercado",
            "keywords": ["Coyoacán Ciudad de México"],
        }
        self.assertLess(_photo_score(single_day, unrelated_unam), 0)
        self.assertGreaterEqual(_photo_score(single_day, market), 0)

        permanent_license = {
            "title": "Licencia permanente CDMX 2026: módulos para tramitarla sin cita",
            "category": "Gobierno", "borough": "",
        }
        treasury_room = {
            "category": "Gobierno",
            "topic": "Sala de Tesorería en Palacio Nacional - IV",
            "keywords": ["Palacio Nacional Ciudad de México"],
        }
        self.assertLess(_photo_score(permanent_license, treasury_room), 0)

        chinampas_article = {
            "title": chinampas["title"], "category": "CDMX", "borough": "Xochimilco",
            "url": "https://news.google.com/rss/articles/chinampas-photo-regression",
        }
        assign_photos([chinampas_article])
        self.assertIn("photo", chinampas_article)
        chinampas_context = (chinampas_article["photo"]["topic"] + " " +
                             " ".join(chinampas_article["photo"].get("keywords", []))).casefold()
        self.assertRegex(chinampas_context, r"canales? de xochimilco|chinampas|agricultura|hortalizas?")

        single_article = {
            "title": single_day["title"], "category": "Cultura", "borough": "Coyoacán",
            "url": "https://news.google.com/rss/articles/single-day-photo-regression",
        }
        assign_photos([single_article])
        self.assertIn("photo", single_article)
        single_context = (single_article["photo"]["topic"] + " " +
                          " ".join(single_article["photo"].get("keywords", []))).casefold()
        self.assertRegex(single_context, r"mercado|compras?|tiendas?|ofertas?|comercio")

        license_article = {
            "title": permanent_license["title"], "category": "Gobierno", "borough": "",
            "url": "https://news.google.com/rss/articles/license-photo-regression",
        }
        assign_photos([license_article])
        if "photo" in license_article:
            license_context = (license_article["photo"]["topic"] + " " +
                               " ".join(license_article["photo"].get("keywords", []))).casefold()
            self.assertRegex(license_context, r"licencia|conducir|semovi|modulo de licencias?|tramite vehicular")

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

    def test_cablebus_line_one_alert_uses_correct_route_category_summary_and_photo(self):
        title = "Activan Alerta Amarilla por Lluvia Fuerte en CDMX; Línea 1 del Cablebús Suspende Servicio"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/cablebus-line1-photo-regression",
            "source": "N+",
            "date": "2026-11-12",
            "category": "CDMX",
        })

        self.assertEqual(article["category"], "Movilidad")
        self.assertEqual(article["borough"], "Gustavo A. Madero")
        self.assertEqual(
            article["location"],
            "Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús)",
        )
        self.assertIn("suspendió el servicio", article["brief"]["lead"])
        self.assertIn("Gustavo A. Madero", article["brief"]["context"])
        self.assertIn("no indican la hora exacta", article["brief"]["pending"])

        santa_marta_line_2 = {
            "id": "commons_108310960",
            "category": "Movilidad",
            "topic": "Estación Cablebús Santa Marta 2",
            "keywords": ["Cablebús Ciudad de México"],
        }
        line_3_cabin = {
            "id": "cablebus_line_3",
            "category": "Movilidad",
            "topic": "Cabina del Cablebús Línea 3",
            "keywords": ["Cablebús Ciudad de México"],
        }
        line_1_station = {
            "id": "cablebus_line_1",
            "category": "Movilidad",
            "topic": "Estación Cablebús Indios Verdes Línea 1",
            "keywords": ["Cablebús Ciudad de México"],
        }

        self.assertLess(_photo_score(article, santa_marta_line_2), 0)
        self.assertLess(_photo_score(article, line_3_cabin), 0)
        self.assertGreaterEqual(_photo_score(article, line_1_station), 0)
        with patch.object(photos, "_pool", return_value=[santa_marta_line_2]):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_recent_news_rejects_unrelated_context_photos(self):
        cases = [
            ("Socavón calles GAM: Afectaciones en la CDMX este martes",
             "Edificios, Paseo de la Reforma (CDMX) 0131", "CDMX", "CDMX"),
            ("¿Por qué repartidores vandalizaron la caseta de un inmueble en CDMX? Esto sabemos",
             "El Paraguas (126505121)", "CDMX", "CDMX"),
            ("Temperaturas en Ciudad de México: prepárate antes de salir de casa",
             "Casa Centro Histórico de la Ciudad de México 01", "CDMX", "CDMX"),
            ("Líneas 4, 5 y 6 del Cablebús mejorarán calidad de vida en seis alcaldías, afirma Gobierno de la CDMX",
             "Estación Los Pinos - Línea 3 del Cablebús 07", "Gobierno", "Movilidad"),
            ("Karol G en el Estadio GNP Seguros de la CDMX: el setlist que prepara la colombiana",
             "Torre Latinoamericana y Edificio La Nacional", "CDMX", "CDMX"),
            ("Verificentros CDMX suspenden servicio: día en el que reabren para no retrasar tu verificación",
             "Ciudad de México - Alameda Central 0370", "CDMX", "CDMX"),
            ("Cancelan foro de POZMVM en Coyoacán por pleito entre PAN y Morena",
             "Boleto cine Esperanza Coyoacán Ciudad de México 6 de mayo de 1928 02", "CDMX", "CDMX"),
            ("Fraudes en compras por internet se disparan en CDMX: Policía Cibernética atiende más de 31 mil reportes",
             "Graduación de la Policía de la Ciudad de México", "Seguridad", "Seguridad"),
            ("Tlalpan da nueva vida al papel con Recicla para Leer",
             "Animales Bosque de Tlalpan 01", "CDMX", "Alcaldías"),
            ("CDMX estrena sistema inteligente para detectar hasta 30 mil fugas de agua",
             "Palacio de Bellas Artes", "CDMX", "CDMX"),
            ("CDMX lleva 10 semanas sin casos activos de sarampión: Secretaría de Salud",
             "Palacio Nacional Ciudad de México DF", "CDMX", "CDMX"),
            ("Lanzan piedras contra autos en Periférico CDMX: denuncian ataques a la altura de Anatole France",
             "Cacerolazo contra la violencia - Ciudad de México - 2", "CDMX", "CDMX"),
            ("Repartidores bloquean zona en CDMX tras amenazas con arma de fuego (VIDEO)",
             "Equipo de trabajo de los Bomberos CDMX IMG 3025", "Seguridad", "Seguridad"),
            ("Repartidores de App Irrumpen en Unidad Habitacional de CDMX tras Amenaza con Arma de Fuego",
             "Graduación de la Policía de la Ciudad de México", "Seguridad", "Seguridad"),
            ("Repartidores anuncian bloqueos en CDMX: ¿qué calles cerrarán este viernes?",
             "Trolebús de la Línea 5 en Paseo de la Reforma y Matamoros", "CDMX", "CDMX"),
            ("VIDEO | Jauría de perros ataca a mujer que caminaba en la Magdalena Contreras; es el segundo caso reportado",
             "Animales Bosque de Tlalpan 02", "CDMX", "Alcaldías"),
        ]
        for title, topic, category, photo_category in cases:
            article = {"title": title, "category": category, "borough": ""}
            photo = {"topic": topic, "category": photo_category, "keywords": []}
            with self.subTest(title=title, topic=topic):
                self.assertLess(_photo_score(article, photo), 0)

    def test_delivery_worker_stories_reject_landmarks_and_keep_protest_context(self):
        cases = [
            (
                "Repartidores protestan por vecino armado y vandalizan caseta en CDMX",
                "Seguridad", "Monumento a Colón Paseo de la Reforma Ciudad de México 6", "CDMX",
            ),
            (
                "Conductores y repartidores alistan movilización en CDMX este miércoles",
                "Movilidad", "Macrosimulacro 2019 Ciudad de México 08", "Seguridad",
            ),
            (
                "Bloqueo de Repartidores en la Glorieta de Camarones, Azcapotzalco, CDMX: Alternativas Viales",
                "Movilidad", "Torre Latinoamericana desde Calle Madero, Ciudad de México", "CDMX",
            ),
            (
                "Alcaldía Benito Juárez llama a resolver controversias por la vía legal ante manifestación de repartidores",
                "Movilidad", "Parque Hundido, alcaldía Benito Juárez", "Alcaldías",
            ),
            (
                "Difunden imágenes con el rostro del sujeto que amenazó a un repartidor",
                "Seguridad", "Macrosimulacro 2019 Ciudad de México 01", "Seguridad",
            ),
            (
                "Repartidores de aplicación toman HOY la CDMX: qué calles cerrarán este 11 de noviembre",
                "Movilidad", "Monumento a Colón Paseo de la Reforma Ciudad de México 6", "CDMX",
            ),
        ]
        for title, category, topic, photo_category in cases:
            article = {"title": title, "category": category, "borough": ""}
            photo = {"topic": topic, "category": photo_category, "keywords": []}
            with self.subTest(title=title, topic=topic):
                self.assertLess(_photo_score(article, photo), 0)

        article = {
            "title": "Repartidores anuncian dos bloqueos estratégicos en CDMX; estas son sus demandas",
            "category": "Movilidad", "borough": "",
        }
        unrelated_protest = {
            "id": "unrelated-cacerolazo",
            "topic": "Cacerolazo contra la violencia - Ciudad de México - 3",
            "category": "CDMX", "keywords": ["Ángel de la Independencia Ciudad de México"],
        }
        self.assertLess(_photo_score(article, unrelated_protest), 0)
        self.assertTrue(news.photo_needs_refresh({**article, "photo": unrelated_protest}))
        with patch.object(photos, "_pool", return_value=[unrelated_protest]):
            assign_photos([article])
        self.assertNotIn("photo", article)

        relevant_delivery = {
            "topic": "Repartidores de aplicación en movilización",
            "category": "Movilidad", "keywords": ["conductores de aplicación"],
        }
        self.assertGreaterEqual(_photo_score(article, relevant_delivery), 0)

    def test_tianguis_and_care_budget_require_topic_matched_photos(self):
        cases = [
            (
                {
                    "title": "Cuántos tianguis hay en CDMX: alcaldías y días",
                    "category": "CDMX", "borough": "",
                },
                {
                    "id": "unrelated-8m",
                    "topic": "Zócalo de la Ciudad de México durante el 8M, 2019",
                    "category": "CDMX", "keywords": ["Zócalo Ciudad de México"],
                },
            ),
            (
                {
                    "title": "Presupuesto de cuidados 2027: ¿cuánto llegará a la CDMX y cómo se puede comprobar?",
                    "category": "Gobierno", "borough": "",
                },
                {
                    "id": "unrelated-palacio",
                    "topic": "Fachada del Palacio Nacional, Ciudad de México 01",
                    "category": "Gobierno", "keywords": ["Palacio Nacional Ciudad de México"],
                },
            ),
        ]
        for article, photo in cases:
            with self.subTest(title=article["title"], topic=photo["topic"]):
                self.assertLess(_photo_score(article, photo), 0)
                self.assertTrue(news.photo_needs_refresh({**article, "photo": photo}))
                with patch.object(photos, "_pool", return_value=[photo]):
                    assign_photos([article])
                self.assertNotIn("photo", article)

        relevant_tianguis = {
            "topic": "Tianguis de la Ciudad de México con puestos de frutas y verduras",
            "category": "CDMX", "keywords": ["comercio ambulante"],
        }
        tianguis_article = cases[0][0]
        self.assertGreaterEqual(_photo_score(tianguis_article, relevant_tianguis), 0)

        relevant_care = {
            "topic": "Centro de atención y cuidado infantil en Ciudad de México",
            "category": "Gobierno", "keywords": ["servicios de cuidado"],
        }
        care_article = cases[1][0]
        self.assertGreaterEqual(_photo_score(care_article, relevant_care), 0)

    def test_building_block_is_not_mistaken_for_a_road_blockade(self):
        article = {
            "title": "Construyen un nuevo bloque de departamentos en CDMX",
            "category": "CDMX", "borough": "",
        }
        photo = {
            "topic": "Edificio de departamentos en Ciudad de México",
            "category": "CDMX", "keywords": [],
        }
        self.assertGreaterEqual(_photo_score(article, photo), 0)

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


    def test_electric_transport_plan_rejects_palacio_nacional_photo(self):
        title = "Prevén transporte 100% eléctrico en 20 años en CDMX"
        category = category_by_headline(title, "Gobierno")
        self.assertEqual(category, "Movilidad")
        article = {"title": title, "category": category, "borough": ""}
        self.assertEqual(_photo_category(article), "Movilidad")
        palace = {
            "category": "Gobierno",
            "topic": "Palacio Nacional Ciudad de México City",
            "keywords": ["Gobierno"],
        }
        trolleybus = {
            "category": "Movilidad",
            "topic": "Trolebús de la Ciudad de México",
            "keywords": ["Trolebús Ciudad de México"],
        }
        self.assertLess(_photo_score(article, palace), 0)
        self.assertGreaterEqual(_photo_score(article, trolleybus), 0)

    def test_tabe_surveillance_story_rejects_unrelated_reforma_monument(self):
        title = "Tabe reporta más vigilancia y alumbrado en Miguel Hidalgo; destaca apoyos a mujeres"
        category = category_by_headline(title, "CDMX")
        self.assertEqual(category, "Seguridad")
        article = {"title": title, "category": category, "borough": "Miguel Hidalgo"}
        self.assertEqual(_photo_category(article), "Seguridad")
        monument = {
            "category": "CDMX",
            "topic": "Monumento a Colón Paseo de la Reforma Ciudad de México 4",
            "keywords": ["CDMX"],
        }
        cuajimalpa_patrol = {
            "category": "Seguridad",
            "topic": "Nuevas patrullas para Cuajimalpa 01",
            "keywords": ["Cuajimalpa Ciudad de México"],
        }
        patrol = {
            "category": "Seguridad",
            "topic": "Patrulla de Ciudad de México",
            "keywords": ["Seguridad"],
        }
        self.assertLess(_photo_score(article, monument), 0)
        self.assertLess(_photo_score(article, cuajimalpa_patrol), 0)
        self.assertGreaterEqual(_photo_score(article, patrol), 0)

    def test_robbery_story_rejects_police_graduation_photo(self):
        title = "Roban Casa de Empeño en el Centro de Azcapotzalco, CDMX"
        category = category_by_headline(title, "CDMX")
        self.assertEqual(category, "Seguridad")
        article = {"title": title, "category": category, "borough": "Azcapotzalco"}
        graduation = {
            "category": "Seguridad",
            "topic": "Graduación de la Policía de la Ciudad de México",
            "keywords": ["Policía Ciudad de México"],
        }
        traffic_police = {
            "category": "Seguridad",
            "topic": "Policía de tránsito Ciudad de México con automovilistas",
            "keywords": ["Policía de tránsito"],
        }
        patrol = {
            "category": "Seguridad",
            "topic": "Patrulla de Ciudad de México",
            "keywords": ["Policía Ciudad de México"],
        }
        self.assertLess(_photo_score(article, graduation), 0)
        self.assertLess(_photo_score(article, traffic_police), 0)
        self.assertGreaterEqual(_photo_score(article, patrol), 0)


    def test_cine_de_barrio_rejects_unrelated_museum_photo(self):
        title = "Festival Cine de Barrio llega a la CDMX con películas, karaoke y rodada con entrada gratuita"
        category = category_by_headline(title, "CDMX")
        self.assertEqual(category, "Cultura")
        article = {"title": title, "category": category, "borough": ""}
        self.assertEqual(_photo_category(article), "Cultura")
        museum = {
            "category": "CDMX",
            "topic": "Entrada al Museo Nacional de Antropología de México",
            "keywords": ["Museo Nacional de Antropología Ciudad de México"],
        }
        cinema = {
            "category": "Alcaldías",
            "topic": "Bosquecinema, Bosque de Tlalpan, Ciudad de México",
            "keywords": ["Tlalpan Ciudad de México"],
        }
        self.assertLess(_photo_score(article, museum), 0)
        self.assertGreaterEqual(_photo_score(article, cinema), 0)


    def test_animal_poisoning_is_sensitive_even_when_local_context_matches(self):
        article = {
            "title": "Más de 30 perritos envenenados en Xochimilco; qué se sabe del caso",
            "category": "CDMX",
            "borough": "Xochimilco",
        }
        tlalpan_animals = {
            "category": "Alcaldías",
            "topic": "Animales Bosque de Tlalpan 08",
            "keywords": ["Tlalpan Ciudad de México"],
        }
        condesa_dogs = {
            "category": "Medio Ambiente",
            "topic": "Perros descansando en el Parque España, Ciudad de México",
            "keywords": ["perros", "Condesa"],
        }
        xochimilco_dogs = {
            "category": "Medio Ambiente",
            "topic": "Perros en Xochimilco, Ciudad de México",
            "keywords": ["perros", "Xochimilco"],
        }
        self.assertLess(_photo_score(article, tlalpan_animals), 0)
        self.assertLess(_photo_score(article, condesa_dogs), 0)
        self.assertGreaterEqual(_photo_score(article, xochimilco_dogs), 0)
        self.assertTrue(photos.is_sensitive_media(article))
        with patch.object(photos, "_pool", return_value=[xochimilco_dogs]):
            assign_photos([article])
        self.assertTrue(article["sensitive_media"])
        self.assertNotIn("photo", article)

        city_wide_rescue = {
            "title": "Rescatan perritos en parque de la capital",
            "category": "Seguridad",
            "borough": "CDMX",
        }
        self.assertGreaterEqual(_photo_score(city_wide_rescue, tlalpan_animals), 0)


    def test_lajornada_housing_summary_clarifies_scope_and_source_figures(self):
        article = news.standardize({
            "title": "CDMX: 95% de la población no puede comprar vivienda",
            "url": "https://news.google.com/rss/articles/housing-summary-regression",
            "source": "La Jornada",
            "date": "2026-11-12",
            "category": "Gobierno",
        })
        brief = article["brief"]
        self.assertIn("oferta de vivienda de alto costo en la zona central", brief["lead"])
        self.assertIn("$59,829", brief["lead"])
        self.assertIn("$32,495", brief["lead"])
        self.assertIn("no a toda vivienda disponible en CDMX", brief["pending"])
        self.assertIn("reportaje completo de La Jornada", brief["method"])
        self.assertNotIn("sin acceso al cuerpo", brief["lead"])

    def test_education_and_housing_articles_reject_generic_landmark_photos(self):
        pool = _pool()
        landmark = next(p for p in pool if "torre latinoamericana" in p["topic"].casefold())
        school = next(p for p in pool if "escuela primaria" in p["topic"].casefold()
                      or "mejora de escuelas" in p["topic"].casefold())
        housing = next(p for p in pool if "unidades habitacionales" in p["topic"].casefold())

        education_article = news.standardize({
            "title": "PT va en CDMX por el fortalecimiento de la educación integral de niños y niñas desde la cuna",
            "url": "https://news.google.com/rss/articles/education-photo-regression",
            "source": "Partido del Trabajo",
            "date": "2026-11-12",
            "category": "CDMX",
            "photo": landmark,
        })
        housing_article = news.standardize({
            "title": "Renta de vivienda en CDMX y Valle de México se encarece más del doble que la compra",
            "url": "https://news.google.com/rss/articles/housing-photo-regression",
            "source": "La Jornada",
            "date": "2026-11-12",
            "category": "CDMX",
            "photo": landmark,
        })

        self.assertLess(_photo_score(education_article, landmark), 0)
        self.assertGreaterEqual(_photo_score(education_article, school), 0)
        self.assertLess(_photo_score(housing_article, landmark), 0)
        self.assertGreaterEqual(_photo_score(housing_article, housing), 0)

        # La asequibilidad y la compra de vivienda también exigen contexto residencial.
        palace = next(p for p in pool if "palacio nacional" in p["topic"].casefold())
        historic_house = next(p for p in pool if "casa centro historico" in news.fold(p["topic"]))
        purchase_article = news.standardize({
            "title": "CDMX: 95% de la población no puede comprar vivienda",
            "url": "https://news.google.com/rss/articles/housing-affordability-photo-regression",
            "source": "La Jornada",
            "date": "2026-11-12",
            "category": "Gobierno",
            "photo": palace,
        })
        self.assertLess(_photo_score(purchase_article, palace), 0)
        self.assertGreaterEqual(_photo_score(purchase_article, historic_house), 0)
        assign_photos([purchase_article])
        purchase_topic = news.fold(purchase_article["photo"]["topic"])
        self.assertRegex(purchase_topic, r"(?:unidades habitacionales|casa centro historico|casa en la avenida|casa gonzalez de cosio)")
        self.assertEqual(purchase_article["photo"]["kind"], "representativa")

        emergency = {
            "category": "Seguridad",
            "topic": "Equipo de trabajo de los Bomberos CDMX IMG 2922",
            "keywords": ["Bomberos Ciudad de México"],
        }
        self.assertLess(_photo_score(housing_article, emergency), 0)

        assign_photos([education_article, housing_article])
        self.assertRegex(education_article["photo"]["topic"].casefold(), r"escuela")
        housing_topic = news.fold(housing_article["photo"]["topic"])
        self.assertRegex(housing_topic, r"(?:unidades habitacionales|casa centro historico|casa en la avenida|casa gonzalez de cosio)")
        for article in (education_article, housing_article):
            photo = article["photo"]
            self.assertTrue(photo["author"])
            self.assertTrue(photo["license"])
            self.assertTrue(photo["licenseUrl"])
            self.assertTrue(photo["source"].startswith("https://commons.wikimedia.org/wiki/File:"))


    def test_guerrero_highway_after_protests_rejects_ecobici_and_uses_regional_road_photo(self):
        article = news.standardize({
            "title": "Pacta Gobierno carretera en Guerrero tras protestas en CDMX",
            "url": "https://news.google.com/rss/articles/guerrero-highway-photo-regression",
            "source": "Reforma",
            "date": "2026-11-12",
            "category": "Gobierno",
        })
        ecobici = {
            "id": "commons_20495838",
            "kind": "representativa",
            "category": "Movilidad",
            "topic": "EcoBici Ciudad de México",
            "keywords": ["ECOBICI Ciudad de México"],
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/76/EcoBici_Ciudad_de_M%C3%A9xico.jpg/960px-EcoBici_Ciudad_de_M%C3%A9xico.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
            "source": "https://commons.wikimedia.org/wiki/File:EcoBici_Ciudad_de_M%C3%A9xico.jpg",
            "author": "Denis Bocquet",
            "license": "CC BY 2.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/2.0",
        }
        highway = {
            "id": "contexto_carretera_guerrero",
            "kind": "representativa",
            "category": "Movilidad",
            "topic": "Carretera Federal 95 en el Cañón del Zopilote, Guerrero (imagen representativa; no corresponde a la obra anunciada)",
            "keywords": ["carretera", "autopista", "Guerrero", "infraestructura vial"],
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/ff/Zopilote_Canyon%2C_Guerrero_and_Mx_Highway_95.jpg/960px-Zopilote_Canyon%2C_Guerrero_and_Mx_Highway_95.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
            "source": "https://commons.wikimedia.org/wiki/File:Zopilote_Canyon,_Guerrero_and_Mx_Highway_95.jpg",
            "author": "Sealight",
            "license": "CC BY-SA 3.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/3.0/",
        }

        self.assertLess(_photo_score(article, ecobici), 0)
        self.assertGreaterEqual(_photo_score(article, highway), 0)
        with patch("scripts.notas_locales._pool", return_value=[ecobici, highway]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_carretera_guerrero")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertIn("no corresponde a la obra anunciada", article["photo"]["topic"])

        unrelated = news.standardize({
            "title": "Contraloría CDMX avanza en transparencia y rendición de cuentas",
            "url": "https://news.google.com/rss/articles/unrelated-government-photo-regression",
            "source": "Talla Politica",
            "date": "2026-11-12",
            "category": "Gobierno",
        })
        self.assertLess(_photo_score(unrelated, highway), 0)


    def test_motorcycle_march_is_mobility_and_uses_motorcycle_context(self):
        title = "Motociclistas marcharán hoy en CDMX; habrá otras 6 concentraciones"
        self.assertEqual(category_by_headline(title, "Metro"), "Movilidad")
        article = {"title": title, "category": "Movilidad", "borough": ""}
        cacerolazo = {
            "id": "generic_cacerolazo",
            "kind": "representativa",
            "category": "CDMX",
            "topic": "Cacerolazo contra la violencia - Ciudad de México",
            "keywords": ["cacerolazo", "protesta"],
        }
        motorcycle = {
            "id": "contexto_motocicleta_zocalo_brigada_2017",
            "kind": "representativa",
            "category": "Movilidad",
            "topic": "Motocicleta de apoyo de una brigada voluntaria en el Zócalo de la Ciudad de México (2017; imagen representativa)",
            "keywords": ["motocicleta", "motociclistas", "moto", "movilidad"],
            "author": "ProtoplasmaKid",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source": "https://commons.wikimedia.org/wiki/File:Ayuda_tras_el_Terremoto_de_Puebla_de_2017_-_Ciudad_de_M%C3%A9xico_-_3.jpg",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d5/Ayuda_tras_el_Terremoto_de_Puebla_de_2017_-_Ciudad_de_M%C3%A9xico_-_3.jpg/960px-Ayuda_tras_el_Terremoto_de_Puebla_de_2017_-_Ciudad_de_M%C3%A9xico_-_3.jpg",
        }
        self.assertLess(_photo_score(article, cacerolazo), 0)
        self.assertGreaterEqual(_photo_score(article, motorcycle), 0)
        with patch.object(photos, "_pool", return_value=[cacerolazo, motorcycle]), patch.object(
            photos, "_load", return_value=[]
        ):
            stats = assign_photos([article])
        self.assertEqual(article["photo"]["id"], motorcycle["id"])
        self.assertEqual(article["photo"]["author"], "ProtoplasmaKid")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertEqual(stats["assigned"], 1)

    def test_plaza_meave_story_rejects_patrol_handover_photo_and_uses_consoles(self):
        title = "CDMX: aseguran más de medio millón de pesos en consolas y videojuegos piratas al interior de la Plaza Meave"
        self.assertEqual(category_by_headline(title, "CDMX"), "Seguridad")
        article = {"title": title, "category": "Seguridad", "borough": ""}
        patrol_handover = {
            "id": "archivo_seguridad_011",
            "kind": "representativa",
            "category": "Seguridad",
            "topic": "Claudia Sheinbaum entrega patrullas Iztapalapa 02",
            "keywords": ["Seguridad"],
        }
        consoles = {
            "id": "contexto_consolas_videojuegos_2026",
            "kind": "representativa",
            "category": "Seguridad",
            "topic": "Tres consolas actuales y videojuegos en estantería (imagen representativa; no corresponde a la mercancía asegurada)",
            "keywords": ["consolas", "videojuegos", "Nintendo Switch", "Xbox", "PlayStation"],
            "author": "InclusiveGameLab",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
            "source": "https://commons.wikimedia.org/wiki/File:InclusiveGameLab_Current_Console_Generation_CC-BY-SA.jpg",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/11/InclusiveGameLab_Current_Console_Generation_CC-BY-SA.jpg/960px-InclusiveGameLab_Current_Console_Generation_CC-BY-SA.jpg",
        }
        self.assertLess(_photo_score(article, patrol_handover), 0)
        self.assertGreaterEqual(_photo_score(article, consoles), 0)
        with patch.object(photos, "_pool", return_value=[patrol_handover, consoles]), patch.object(
            photos, "_load", return_value=[]
        ):
            stats = assign_photos([article])
        self.assertEqual(article["photo"]["id"], consoles["id"])
        self.assertEqual(article["photo"]["author"], "InclusiveGameLab")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertEqual(stats["assigned"], 1)


    def test_tame_impala_announcement_rejects_carnival_photo_without_music_context(self):
        article = {
            "title": "¡Tame Impala regresa a México en 2027! Dos noches en CDMX",
            "category": "CDMX", "borough": "",
        }
        carnival = {
            "id": "carnaval_cdmx",
            "category": "CDMX",
            "topic": "Declaratoria de Carnavales como Patrimonio Cultural Inmaterial de la Ciudad de México 13",
            "keywords": ["carnavales", "cultura"],
        }
        music_stage = {
            "id": "escenario_musical",
            "category": "Cultura",
            "topic": "Concierto de rock en escenario de CDMX",
            "keywords": ["música en vivo", "banda", "rock"],
        }
        self.assertLess(_photo_score(article, carnival), 0)
        self.assertGreaterEqual(_photo_score(article, music_stage), 0)
        with patch.object(photos, "_pool", return_value=[carnival]):
            assign_photos([article])
        self.assertNotIn("photo", article)


    def test_intercity_train_articles_reject_city_landmarks_and_light_rail_photos(self):
        titles = (
            "Llega a México el primer tren de la ruta CDMX-Pachuca; tendrá capacidad para 893 pasajeros",
            "Llega a México el primer tren de pasajeros que conectará la CDMX con Pachuca",
            "Obras de construcción del Tren Ciudad de México-Guadalajara inician en diciembre: SICT",
            "Llega la primera unidad del tren que dará servicio en la ruta Ciudad de México-Pachuca",
        )
        landmark = {
            "id": "angel_cdmx",
            "category": "CDMX",
            "topic": "Ángel de la Ciudad de México",
            "keywords": ["Ciudad de México", "monumento"],
        }
        light_rail = {
            "id": "tren_ligero_cdmx",
            "category": "Movilidad",
            "topic": "Tren Ligero de la Ciudad de México",
            "keywords": ["tren ligero", "movilidad"],
        }
        for index, title in enumerate(titles):
            with self.subTest(title=title):
                article = news.standardize({
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/intercity-train-photo-{index}",
                    "source": "N+",
                    "date": "2026-11-12",
                    "category": "CDMX",
                    "photo": landmark,
                })
                self.assertEqual(article["category"], "Movilidad")
                self.assertLess(_photo_score(article, landmark), 0)
                self.assertLess(_photo_score(article, light_rail), 0)
                with patch.object(photos, "_pool", return_value=[landmark, light_rail]), patch.object(
                    photos, "_load", return_value=[]
                ):
                    assign_photos([article])
                self.assertNotIn("photo", article)

    def test_kidnapping_and_business_crime_reject_landmarks_traffic_and_graduations(self):
        titles = (
            "Caen tres secuestradores en la alcaldía Venustiano Carranza",
            "Policías de la CDMX rescataron a un hombre secuestrado en La Merced al detener a tres sujetos",
            "Caen 35.6% los delitos contra empresas y comercios en CDMX, presume Pablo Vázquez",
        )
        photos_to_reject = (
            {
                "id": "zocalo",
                "category": "CDMX",
                "topic": "Zócalo de la Ciudad de México",
                "keywords": ["Centro Histórico"],
            },
            {
                "id": "policia_transito",
                "category": "Seguridad",
                "topic": "Policía de tránsito Ciudad de México marcando alto a auto",
                "keywords": ["policía de tránsito", "automovilistas"],
            },
            {
                "id": "graduacion_policia",
                "category": "Seguridad",
                "topic": "Graduación de la Policía de la Ciudad de México",
                "keywords": ["policía", "graduación"],
            },
        )
        for index, title in enumerate(titles):
            with self.subTest(title=title):
                article = news.standardize({
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/kidnapping-crime-photo-{index}",
                    "source": "N+",
                    "date": "2026-11-12",
                    "category": "CDMX",
                })
                self.assertEqual(article["category"], "Seguridad")
                for photo in photos_to_reject:
                    self.assertLess(_photo_score(article, photo), 0)
                with patch.object(photos, "_pool", return_value=list(photos_to_reject)), patch.object(
                    photos, "_load", return_value=[]
                ):
                    assign_photos([article])
                self.assertNotIn("photo", article)

    def test_metropolitan_search_and_ezln_collective_reject_unrelated_photos(self):
        graduation = {
            "id": "police_graduation",
            "category": "Seguridad",
            "topic": "Graduación de la Policía de la Ciudad de México",
            "keywords": ["policía", "graduación"],
        }
        monument = {
            "id": "monumento_revolucion",
            "category": "CDMX",
            "topic": "Monumento a la Revolución CDMX 2",
            "keywords": ["Monumento a la Revolución"],
        }
        cases = (
            (
                "Fiscalías de Morelos, CDMX y Edomex se unen en la primera Búsqueda Metropolitana Triple Frontera",
                "Gobierno",
                graduation,
            ),
            (
                "EZLN pide perdón a colectivo buscador, tras rechazar reunión en la Glorieta de las y los desaparecidos en CDMX",
                "CDMX",
                monument,
            ),
        )
        for index, (title, category, wrong_photo) in enumerate(cases):
            with self.subTest(title=title):
                article = news.standardize({
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/metropolitan-search-photo-{index}",
                    "source": "Medio de prueba",
                    "date": "2026-11-12",
                    "category": category,
                })
                self.assertLess(_photo_score(article, wrong_photo), 0)
                with patch.object(photos, "_pool", return_value=[wrong_photo]), patch.object(
                    photos, "_load", return_value=[]
                ):
                    assign_photos([article])
                self.assertNotIn("photo", article)


    def test_toboggan_sumo_and_atm_advice_reject_unrelated_photos(self):
        cases = (
            (
                "Toboganes gigantes llegan a la CDMX: dónde y cuándo abre la obra de arte interactiva que podrás disfrutar de manera gratuita",
                {
                    "id": "carnival_declaration",
                    "category": "CDMX",
                    "topic": "Declaratoria de carnavales como patrimonio cultural inmaterial de la Ciudad de México",
                    "keywords": ["carnaval", "patrimonio cultural"],
                },
            ),
            (
                "El sumo regresa a CDMX tras 45 años: cuándo será el torneo y dónde comprar boletos",
                {
                    "id": "monumento_colon",
                    "category": "CDMX",
                    "topic": "Panorámica Monumento a Colón - Paseo de la Reforma - Ciudad de México",
                    "keywords": ["monumento", "Reforma"],
                },
            ),
            (
                "Seis recomendaciones clave emitidas por la Policía Bancaria de la Ciudad de México para proteger tu dinero y evitar fraudes o alteraciones en cajeros automáticos durante las compras del Buen Fin 2026",
                {
                    "id": "police_graduation",
                    "category": "Seguridad",
                    "topic": "Graduación de la Policía de la Ciudad de México",
                    "keywords": ["policía", "graduación"],
                },
            ),
        )
        for index, (title, wrong_photo) in enumerate(cases):
            with self.subTest(title=title):
                article = news.standardize({
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/culture-atm-photo-{index}",
                    "source": "Medio de prueba",
                    "date": "2026-11-12",
                    "category": "CDMX",
                    "photo": wrong_photo,
                })
                self.assertLess(_photo_score(article, wrong_photo), 0)
                with patch.object(photos, "_pool", return_value=[wrong_photo]), patch.object(
                    photos, "_load", return_value=[]
                ):
                    assign_photos([article])
                self.assertNotIn("photo", article)

    def test_mottu_march_rejects_cacerolazo_and_uses_motorcycle_context(self):
        title = "Motociclistas de Mottu México marcharán de Iztacalco al Zócalo; se suman seis concentraciones en la CDMX"
        cacerolazo = {
            "id": "cacerolazo_violencia_3",
            "category": "CDMX",
            "topic": "Cacerolazo contra la violencia - Ciudad de México - 3",
            "keywords": ["cacerolazo", "protesta"],
        }
        motorcycle = {
            "id": "contexto_motocicleta_zocalo_brigada_2017",
            "kind": "representativa",
            "category": "Movilidad",
            "topic": "Motocicleta de apoyo de una brigada voluntaria en el Zócalo de la Ciudad de México (2017; imagen representativa, no corresponde a la marcha de 2026)",
            "keywords": ["motocicleta", "motociclistas", "moto", "movilidad", "marcha de motociclistas", "Zócalo", "Ciudad de México"],
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d5/Ayuda_tras_el_Terremoto_de_Puebla_de_2017_-_Ciudad_de_M%C3%A9xico_-_3.jpg/960px-Ayuda_tras_el_Terremoto_de_Puebla_de_2017_-_Ciudad_de_M%C3%A9xico_-_3.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
            "source": "https://commons.wikimedia.org/wiki/File:Ayuda_tras_el_Terremoto_de_Puebla_de_2017_-_Ciudad_de_M%C3%A9xico_-_3.jpg",
            "author": "ProtoplasmaKid",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        }
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/mottu-photo-regression",
            "source": "Medio de prueba",
            "date": "2026-11-12",
            "category": "Movilidad",
            "photo": cacerolazo,
        })
        self.assertLess(_photo_score(article, cacerolazo), 0)
        self.assertGreater(_photo_score(article, motorcycle), 0)
        with patch.object(photos, "_pool", return_value=[cacerolazo, motorcycle]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_motocicleta_zocalo_brigada_2017")
        self.assertIn("no corresponde a la marcha de 2026", article["photo"]["topic"])

    def test_kidnapping_story_rejects_traffic_light_police_photo_and_uses_patrol_context(self):
        title = "Policías de la CDMX rescataron a un hombre secuestrado en La Merced al detener a tres sujetos con armas y droga"
        traffic = {
            "id": "policia_semaforo",
            "category": "Seguridad",
            "topic": "Policía controlando el semáforo, Ciudad de México",
            "keywords": ["policía", "semáforo", "tránsito"],
        }
        patrol = {
            "id": "seguridad",
            "category": "Seguridad",
            "topic": "Patrulla de Ciudad de México",
            "keywords": ["Seguridad"],
            "url": "/assets/fotos/seguridad.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:Patrulla_cdmx.jpg",
            "author": "RainerRowe",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
        }
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/kidnapping-traffic-photo-regression",
            "source": "Medio de prueba",
            "date": "2026-11-12",
            "category": "Seguridad",
            "photo": traffic,
        })
        self.assertLess(_photo_score(article, traffic), 0)
        self.assertGreater(_photo_score(article, patrol), 0)
        with patch.object(photos, "_pool", return_value=[traffic, patrol]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "seguridad")

    def test_infobae_ballet_is_culture_in_iztacalco_and_rejects_metro_and_landmark_photos(self):
        title = "Función gratis del ballet «La Zapatilla de Cristal» llega a CDMX: fecha y sede"
        metro = {
            "id": "metro_pantitlan",
            "category": "Metro",
            "topic": "Estación Pantitlán de la Línea 1 del Metro de Ciudad de México",
            "keywords": ["Metro CDMX", "Pantitlán"],
            "url": "/assets/fotos/metro-pantitlan.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:Metro_CDMX_IMG_0231_(25900065922).jpg",
            "author": "Gobierno CDMX",
            "license": "CC0 1.0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        }
        bellas = {
            "id": "bellas_artes",
            "category": "Cultura",
            "topic": "Palacio de Bellas Artes, Ciudad de México",
            "keywords": ["Cultura", "Palacio de Bellas Artes"],
            "url": "/assets/fotos/bellas-artes.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:Palacio_de_Bellas_Artes_-_CDMX.jpg",
            "author": "JUAN CARLOS GONZALEZ",
            "license": "CC0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        }
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/ballet-zapatilla-regression",
            "source": "Infobae",
            "date": "2026-11-12",
            "category": "Metro",
            "photo": metro,
        })
        self.assertEqual(article["category"], "Cultura")
        self.assertEqual(article["borough"], "Iztacalco")
        self.assertIn("Utopía Mixiuhca", article["location"])
        self.assertEqual(
            article["source_url"],
            "https://www.infobae.com/mexico/2026/11/12/funcion-gratis-del-ballet-la-zapatilla-de-cristal-llega-a-cdmx-fecha-y-sede/",
        )
        self.assertIn("28 de noviembre", article["brief"]["lead"])
        self.assertIn("13:00", article["brief"]["lead"])
        self.assertEqual(_photo_category(article), "Cultura")
        self.assertLess(_photo_score(article, metro), 0)
        self.assertLess(_photo_score(article, bellas), 0)
        with patch.object(photos, "_pool", return_value=[metro, bellas]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_pulque_barbacoa_fair_uses_licensed_representative_food_photo(self):
        title = "Feria del Pulque y la Barbacoa en La Magdalena Contreras. Fechas y qué encontrarás"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/pulque-barbacoa-fair-regression",
            "source": "El Universal",
            "date": "2026-11-12",
            "category": "CDMX",
        })
        self.assertEqual(article["category"], "Cultura")
        self.assertEqual(article["borough"], "La Magdalena Contreras")
        self.assertIn("José Moreno Salido", article["location"])
        self.assertIn("13 al 15 de noviembre", article["brief"]["lead"])
        self.assertIn("8:00 a 19:00", article["brief"]["lead"])
        self.assertIn("POSTA México", article["brief"]["method"])
        photo = next(
            item for item in photos._pool()
            if item["id"] == "contexto_barbacoa_xochimilco_2026"
        )
        self.assertEqual(photo["author"], "ProtoplasmaKid")
        self.assertEqual(photo["license"], "CC BY-SA 4.0")
        self.assertIn("no corresponde a la Feria", photo["topic"])
        self.assertGreaterEqual(_photo_score(article, photo), 0)
        with patch.object(photos, "_pool", return_value=[photo]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_barbacoa_xochimilco_2026")

    def test_cirque_du_soleil_is_culture_and_rejects_generic_city_photo(self):
        title = "Cirque Du Soleil ya ofrece funciones en CDMX con su espectáculo ECHO"
        generic_city = {
            "id": "generic_city",
            "category": "CDMX",
            "topic": "D.F. - panoramio (7), Ciudad de México",
            "keywords": ["Ciudad de México"],
            "url": "/assets/fotos/generic-city.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:DF_panoramio.jpg",
            "author": "Fotógrafo acreditado",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        }
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/cirque-echo-regression",
            "source": "88.9 Noticias",
            "date": "2026-11-12",
            "category": "CDMX",
            "photo": generic_city,
        })
        self.assertEqual(article["category"], "Cultura")
        self.assertEqual(_photo_category(article), "Cultura")
        self.assertLess(_photo_score(article, generic_city), 0)
        with patch.object(photos, "_pool", return_value=[generic_city]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_rain_alert_uses_rain_operation_not_rainwater_harvesting_photo(self):
        title = (
            "Activan alerta por diluvio en CDMX: Estas son las alcaldías que se verán "
            "afectadas por las fuertes lluvias | LISTA"
        )
        harvest = {
            "id": "cosecha_lluvia",
            "category": "Medio Ambiente",
            "topic": "Cosecha de Lluvia 02",
            "keywords": ["Lluvia Ciudad de México"],
            "url": "/assets/fotos/cosecha-lluvia.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:Cosecha_de_Lluvia_02.jpg",
            "author": "Gobierno de la Ciudad de México",
            "license": "CC BY 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
        }
        operation = {
            "id": "operativo_lluvias",
            "category": "Medio Ambiente",
            "topic": "Operativo Lluvias CDMX, atención a afectaciones por precipitación",
            "keywords": ["Lluvia Ciudad de México", "operativo de lluvias"],
            "url": "/assets/fotos/operativo-lluvias.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:Operativo_Lluvias_-i---i-_(36298031503).jpg",
            "author": "Gobierno CDMX",
            "license": "CC0 1.0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        }
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/rain-alert-photo-regression",
            "source": "El Heraldo de México",
            "date": "2026-11-12",
            "category": "CDMX",
            "photo": harvest,
        })
        self.assertEqual(article["category"], "Medio Ambiente")
        self.assertLess(_photo_score(article, harvest), 0)
        self.assertGreaterEqual(_photo_score(article, operation), 0)
        with patch.object(photos, "_pool", return_value=[harvest, operation]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "operativo_lluvias")


    def test_adoption_caravan_is_not_metro_and_government_topics_are_classified(self):
        adoption = "Caravana de adopción en Reforma: perritos rescatados buscan hogar en CDMX"
        tabe = "Mauricio Tabe presenta su Quinto Informe de Gobierno en Miguel Hidalgo"
        congress = "Recibe Congreso capitalino proyecto del Plan General de Desarrollo CDMX 2027-2047"
        self.assertEqual(category_by_headline(adoption, "Metro"), "CDMX")
        self.assertEqual(category_by_headline(tabe, "CDMX"), "Gobierno")
        self.assertEqual(category_by_headline(congress, "CDMX"), "Gobierno")

    def test_congress_news_rejects_national_palace_and_congress_avenue_photos(self):
        article = {
            "title": "Recibe Congreso capitalino proyecto del Plan General de Desarrollo CDMX 2027-2047",
            "category": "Gobierno",
            "url": "https://news.google.com/rss/articles/congress-photo-regression",
        }
        avenue = representative_photo(
            "congreso_union_avenue", "Movilidad",
            "Fotografía aérea de Avenida H. Congreso de la Unión, Candelaria de los Patos y Centro Histórico; tránsito vehicular",
            ["Avenida Congreso de la Unión", "Candelaria de los Patos", "tránsito vehicular"],
        )
        treasury = representative_photo(
            "national_palace_treasury", "Gobierno",
            "Sala de Tesorería en Palacio Nacional - VII", ["Palacio Nacional Ciudad de México"],
        )
        self.assertLess(_photo_score(article, avenue), 0)
        self.assertLess(_photo_score(article, treasury), 0)
        with patch.object(photos, "_pool", return_value=[avenue, treasury]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_local_mayor_report_uses_miguel_hidalgo_context_not_national_palace(self):
        article = {
            "title": "Mauricio Tabe presenta su Quinto Informe de Gobierno en Miguel Hidalgo",
            "category": "Gobierno",
            "borough": "Miguel Hidalgo",
            "url": "https://news.google.com/rss/articles/tabe-report-photo-regression",
        }
        palace = representative_photo(
            "palacio_nacional", "Gobierno", "Palacio Nacional Ciudad de México DF", ["Gobierno"]
        )
        chapultepec = representative_photo(
            "bosque_chapultepec", "CDMX", "Bosque de Chapultepec, Ciudad de México", ["Chapultepec"]
        )
        self.assertLess(_photo_score(article, palace), 0)
        self.assertGreaterEqual(_photo_score(article, chapultepec), 0)
        with patch.object(photos, "_pool", return_value=[palace, chapultepec]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "bosque_chapultepec")

    def test_avenida_alvaro_obregon_in_roma_is_not_the_alcaldia(self):
        article = {
            "title": "Actividades vecinales en la alcaldía Álvaro Obregón",
            "category": "CDMX",
            "borough": "Álvaro Obregón",
            "url": "https://news.google.com/rss/articles/alvaro-obregon-photo-regression",
        }
        roma = representative_photo(
            "avenida_alvaro_obregon_roma", "Alcaldías",
            "Casa en la Avenida Álvaro Obregón, Colonia Roma Norte, Cuauhtémoc, Ciudad de México",
            ["Avenida Álvaro Obregón", "Colonia Roma Norte", "Cuauhtémoc"],
        )
        san_angel = representative_photo(
            "san_angel_alvaro_obregon", "Alcaldías",
            "Fuente de cantera gris, San Ángel, Del. Álvaro Obregón, Ciudad de México",
            ["Álvaro Obregón Ciudad de México"],
        )
        self.assertLess(_photo_score(article, roma), 0)
        self.assertGreaterEqual(_photo_score(article, san_angel), 0)
        with patch.object(photos, "_pool", return_value=[roma, san_angel]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "san_angel_alvaro_obregon")

    def test_environmental_justice_uses_ecological_park_not_national_palace(self):
        article = {
            "title": "Gobierno de la Ciudad de México fortalece la justicia ambiental con acciones para proteger la biodiversidad y mejorar la calidad de vida en la capital",
            "category": "Gobierno",
            "url": "https://news.google.com/rss/articles/environmental-justice-photo-regression",
        }
        palace = representative_photo(
            "palacio_nacional", "Gobierno", "Palacio Nacional Ciudad de México DF", ["Gobierno"]
        )
        park = representative_photo(
            "parque_ecologico", "Medio Ambiente",
            "Parque Ecológico de la Ciudad de México 10", ["Parques Ciudad de México"]
        )
        self.assertLess(_photo_score(article, palace), 0)
        self.assertGreaterEqual(_photo_score(article, park), 0)
        with patch.object(photos, "_pool", return_value=[palace, park]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "parque_ecologico")

    def test_casa_ecologica_requires_solar_or_rainwater_context(self):
        article = {
            "title": "CDMX lanza programa Casa Ecológica para instalar captadores de agua y energía solar en hogares",
            "category": "Gobierno",
            "url": "https://news.google.com/rss/articles/casa-ecologica-photo-regression",
        }
        palace = representative_photo(
            "palacio_tesoreria", "Gobierno",
            "Sala de Tesorería en Palacio Nacional - IV", ["Palacio Nacional Ciudad de México"]
        )
        rainwater = representative_photo(
            "cosecha_lluvia", "Medio Ambiente", "Cosecha de Lluvia 06", ["Lluvia Ciudad de México"]
        )
        self.assertLess(_photo_score(article, palace), 0)
        self.assertGreaterEqual(_photo_score(article, rainwater), 0)
        with patch.object(photos, "_pool", return_value=[palace, rainwater]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "cosecha_lluvia")

    def test_plan_general_development_rejects_palacio_nacional_street_photo(self):
        article = {
            "title": "Exige PRI retirar el Plan General de Desarrollo de la CDMX",
            "category": "Gobierno",
            "url": "https://news.google.com/rss/articles/plan-general-photo-regression",
        }
        palace_street = representative_photo(
            "madero_palace", "Gobierno",
            "Calle Francisco I. Madero de la Ciudad de México, con el Palacio Nacional al fondo",
            ["Gobierno"],
        )
        self.assertLess(_photo_score(article, palace_street), 0)
        with patch.object(photos, "_pool", return_value=[palace_street]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_pueblos_magicos_guide_rejects_centro_historico_cdmx_photo(self):
        article = {
            "title": "Puente del 16 de noviembre: 8 Pueblos Mágicos a menos de 3 horas de CDMX para una escapada de tres días",
            "category": "CDMX",
            "url": "https://news.google.com/rss/articles/pueblos-magicos-photo-regression",
        }
        centro = representative_photo(
            "centro_cdmx", "CDMX", "Ciudad de México - Colonia Centro 6984",
            ["Centro Histórico Ciudad de México"],
        )
        self.assertLess(_photo_score(article, centro), 0)
        with patch.object(photos, "_pool", return_value=[centro]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_cch_sur_story_rejects_generic_coyoacan_bench_photo(self):
        article = {
            "title": "Muere profesor dentro de las instalaciones del CCH Sur de la UNAM en alcaldía Coyoacán",
            "category": "CDMX",
            "borough": "Coyoacán",
            "url": "https://news.google.com/rss/articles/cch-sur-photo-regression",
        }
        bench = representative_photo(
            "coyoacan_bench", "CDMX", "4. Coyoacán banca Ciudad de México", ["CDMX"]
        )
        self.assertLess(_photo_score(article, bench), 0)
        with patch.object(photos, "_pool", return_value=[bench]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_valle_de_mexico_territory_story_rejects_national_palace_photo(self):
        article = {
            "title": "VIDEO | Edomex, CDMX y Valle de México: ¿cuáles son sus diferencias y qué territorios comprenden?",
            "category": "Gobierno",
            "url": "https://news.google.com/rss/articles/valle-metropolitano-photo-regression",
        }
        palace = representative_photo(
            "palacio_nacional", "Gobierno",
            "Fachada del Palacio Nacional, Ciudad de México 01", ["Palacio Nacional Ciudad de México"]
        )
        self.assertLess(_photo_score(article, palace), 0)
        with patch.object(photos, "_pool", return_value=[palace]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_march_agenda_rejects_earthquake_volunteer_motorcycle_photo(self):
        article = {
            "title": "Marchas en CDMX hoy 12 de noviembre: rutas, horarios y calles afectadas EN VIVO",
            "category": "Movilidad",
            "url": "https://news.google.com/rss/articles/march-agenda-photo-regression",
        }
        motorcycle = representative_photo(
            "brigade_motorcycle", "CDMX",
            "Motocicleta de apoyo de una brigada voluntaria en el Zócalo de la Ciudad de México tras el sismo de 2017",
            ["motocicleta", "moto", "Zócalo", "brigada voluntaria", "sismo 2017", "Ciudad de México"],
        )
        self.assertLess(_photo_score(article, motorcycle), 0)
        with patch.object(photos, "_pool", return_value=[motorcycle]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_photo_catalog_metadata_matches_the_actual_location_and_subject(self):
        index = {p["id"]: p for p in photos._load(photos.NEWS_PHOTOS, "photos")}
        editorial = {p["id"]: p for p in photos._load(
            photos.ROOT / "assets/fotos/catalogo-editorial-1100.json", "photos"
        )}
        context = {p["id"]: p for p in photos._load(photos.TOPIC_PHOTOS, "photos")}
        for photo_id in ("commons_51892797", "commons_51894949", "commons_24433238", "commons_175612248"):
            for catalog in (index, editorial):
                item = catalog[photo_id]
                self.assertIn("Cuauhtémoc", " ".join(item["keywords"]))
                self.assertIn("Colonia Roma", " ".join(item["keywords"]))
        avenue = index["commons_169149220"]
        self.assertEqual(avenue["category"], "Movilidad")
        self.assertIn("Avenida H. Congreso de la Unión", avenue["topic"])
        self.assertNotIn("Congreso de la Ciudad de México edificio", avenue["keywords"])
        motorcycle = context["contexto_motocicleta_zocalo_brigada_2017"]
        self.assertNotIn("marcha de motociclistas", motorcycle["keywords"])
        self.assertNotIn("motociclistas", motorcycle["keywords"])



    def test_congress_building_is_acceptable_for_plan_general_story(self):
        article = {
            "title": "Recibe Congreso capitalino proyecto del Plan General de Desarrollo CDMX 2027-2047",
            "category": "Gobierno",
            "url": "https://news.google.com/rss/articles/congress-building-photo-regression",
        }
        congress = representative_photo(
            "palacio_legislativo", "Gobierno",
            "Palacio Legislativo de Donceles, Congreso de la Ciudad de México",
            ["Congreso de la Ciudad de México", "Donceles"],
        )
        self.assertGreaterEqual(_photo_score(article, congress), 0)



    def test_rainwater_harvesting_uses_cosecha_photo_not_borough_flower(self):
        article = news.standardize({
            "title": "CDMX instalará miles de sistemas para captar agua de lluvia en Álvaro Obregón",
            "url": "https://news.google.com/rss/articles/rainwater-photo-regression",
            "source": "Enfoque Noticias",
            "date": "2026-11-12",
            "category": "CDMX",
        })
        self.assertEqual(article["category"], "Medio Ambiente")
        harvest = representative_photo(
            "cosecha_lluvia_05",
            "Medio Ambiente",
            "Cosecha de Lluvia 05",
            ["captación de agua de lluvia", "sistemas de captación pluvial"],
        )
        flower = representative_photo(
            "alvaro_obregon_flower",
            "Alcaldías",
            "Flor del camellón de Álvaro Obregón, Ciudad de México",
            ["Álvaro Obregón", "flores", "camellón"],
        )
        self.assertLess(_photo_score(article, flower), 0)
        self.assertGreaterEqual(_photo_score(article, harvest), 0)
        with patch.object(photos, "_pool", return_value=[flower, harvest]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "cosecha_lluvia_05")


    def test_profeco_service_story_rejects_unrelated_cacerolazo_photo(self):
        article = news.standardize({
            "title": "Ubicación de módulos de Profeco en CDMX para quejas en El Buen Fin",
            "url": "https://news.google.com/rss/articles/profeco-photo-regression",
            "source": "El Sol de México",
            "date": "2026-11-12",
            "category": "CDMX",
        })
        cacerolazo = representative_photo(
            "cacerolazo_contra_violencia",
            "CDMX",
            "Cacerolazo contra la violencia - Ciudad de México - 2",
            ["Ángel de la Independencia Ciudad de México"],
        )
        consumer_service = representative_photo(
            "profeco_modules",
            "CDMX",
            "Módulos de atención de Profeco para quejas de consumidores",
            ["Profeco", "atención al consumidor", "El Buen Fin"],
        )
        self.assertLess(_photo_score(article, cacerolazo), 0)
        self.assertGreaterEqual(_photo_score(article, consumer_service), 0)
        with patch.object(photos, "_pool", return_value=[cacerolazo]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_trolleybus_photo_in_cuauhtemoc_is_rejected_for_vc_pickup_crash(self):
        article = news.standardize({
            "title": "Accidente en Canal del Norte: Camioneta Choca y Termina Destrozada en Venustiano Carranza",
            "url": "https://news.google.com/rss/articles/canal-del-norte-photo-regression",
            "source": "N+",
            "date": "2026-11-12",
            "category": "Movilidad",
        })
        index = {p["id"]: p for p in photos._load(photos.NEWS_PHOTOS, "photos")}
        trolleybus = index["commons_175612248"]
        self.assertEqual(article["borough"], "Venustiano Carranza")
        self.assertIn("Cuauhtémoc", " ".join(trolleybus["keywords"]))
        self.assertLess(_photo_score(article, trolleybus), 0)
        with patch.object(photos, "_pool", return_value=[trolleybus]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertNotIn("photo", article)

if __name__ == "__main__":
    unittest.main()
