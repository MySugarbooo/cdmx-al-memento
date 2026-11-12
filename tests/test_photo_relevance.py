"""Previene asignar fotos de patrullas a noticias de ciclismo o tecnología."""
import unittest
from unittest.mock import patch

from scripts.notas_locales import _pool, _photo_category, _photo_score, assign_photos
import update_news as news
import scripts.notas_locales as photos
from update_news import category_by_headline


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
            "title": "Repartidores protestan por vecino armado y vandalizan caseta en CDMX",
            "category": "Seguridad", "borough": "",
        }
        protest_photo = {
            "topic": "Cacerolazo contra la violencia - Ciudad de México - 1",
            "category": "CDMX", "keywords": ["protesta", "manifestantes"],
        }
        self.assertGreaterEqual(_photo_score(article, protest_photo), 0)
        assign_photos([article])
        self.assertRegex(
            article["photo"]["topic"].casefold(),
            r"cacerolazo|marcha por la paz|manifestaci[oó]n",
        )
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertTrue(article["photo"].get("author"))
        self.assertTrue(article["photo"].get("license"))
        self.assertTrue(article["photo"].get("licenseUrl"))
        self.assertTrue(article["photo"].get("source"))

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


    def test_local_animal_story_rejects_photos_from_other_boroughs(self):
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


if __name__ == "__main__":
    unittest.main()
