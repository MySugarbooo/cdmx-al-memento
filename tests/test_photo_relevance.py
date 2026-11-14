"""Previene asignar fotos de patrullas a noticias de ciclismo o tecnología."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.notas_locales import _pool, _photo_category, _photo_score, assign_photos
import update_news as news
import scripts.notas_locales as photos
from update_news import category_by_headline

REPO_ROOT = Path(__file__).resolve().parents[1]

def representative_photo(photo_id, category, topic, keywords):
    return {
        "id": photo_id,
        "kind": "representativa",
        "category": category,
        "topic": topic,
        "keywords": keywords,
        "url": f"/assets/fotos/{photo_id}.jpg",
        "source": f"https://commons.wikimedia.org/wiki/File:{photo_id}.jpg",
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

    def test_womens_defensive_driving_workshop_has_verified_mobility_location_and_summary(self):
        title = "Ofrecen taller gratuito de manejo defensivo y preventivo para mujeres en CDMX"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/women-defensive-driving-workshop",
            "source": "El Sol de México",
            "date": "2026-11-14",
            "published_at": "2026-11-14T17:33:57Z",
            "category": "CDMX",
        })
        self.assertEqual(article["category"], "Movilidad")
        self.assertEqual(article["borough"], "Gustavo A. Madero")
        self.assertIn("Gustavo A. Madero", article["location"])
        self.assertIn("27 de noviembre de 2026", article["brief"]["lead"])
        self.assertIn("hasta un día antes", article["brief"]["lead"])
        self.assertIn("no se consultó el cuerpo íntegro", article["brief"]["method"])
        self.assertEqual(
            article["source_url"],
            "https://oem.com.mx/elsoldemexico/metropoli/ofrecen-taller-gratuito-de-manejo-defensivo-y-preventivo-para-mujeres-en-cdmx-33130686",
        )
        self.assertEqual(article["description"], article["brief"]["lead"])

    def test_shared_concert_photo_caption_is_generic_in_all_catalogs(self):
        expected = "Concierto de Kings of Leon en el Palacio de los Deportes, CDMX (octubre de 2009); foto de archivo representativa, no documenta eventos de la noticia."
        relative_paths = (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        )
        for relative in relative_paths:
            with self.subTest(path=relative):
                data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
                photo = next(
                    (item for item in data.get("photos", [])
                     if item.get("id") == "contexto_concierto_palacio_deportes_2009"),
                    None,
                )
                self.assertIsNotNone(photo, relative)
                self.assertEqual(photo.get("topic"), expected)
                self.assertNotIn("María León", photo.get("topic", ""))

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


    def test_theatre_recommendations_reject_plant_photo_and_use_theatre_context(self):
        title = "Obras de teatro que tienes que ver en noviembre en CDMX"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/theatre-photo-regression",
            "source": "Chilango",
            "date": "2026-11-14",
            "category": "CDMX",
        })
        self.assertEqual(article["category"], "Cultura")
        self.assertEqual(_photo_category(article), "Cultura")

        plant = next(
            photo for photo in _pool()
            if photo.get("id") == "commons_57104818"
        )
        theatre = next(
            photo for photo in _pool()
            if "teatro angela peralta" in news.fold(photo.get("topic", ""))
        )
        self.assertLess(_photo_score(article, plant), 0)
        self.assertGreaterEqual(_photo_score(article, theatre), 0)

        with patch.object(photos, "_pool", return_value=[plant, theatre]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_teatro_angela_peralta")
        self.assertEqual(article["photo"]["kind"], "representativa")

    def test_theatre_recommendation_summary_is_specific_and_cautious(self):
        article = news.standardize({
            "title": "Obras de teatro que tienes que ver en noviembre en CDMX",
            "url": "https://news.google.com/rss/articles/theatre-summary-regression",
            "source": "Chilango",
            "date": "2026-11-14",
            "category": "CDMX",
        })
        lead = article["brief"]["lead"].casefold()
        self.assertIn("recomendaciones de obras de teatro", lead)
        self.assertIn("cartelera original", lead)
        self.assertNotIn("sin acceso al cuerpo", lead)
        self.assertEqual(article["description"], article["brief"]["lead"])


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

    def test_delivery_rider_blockade_uses_credited_postal_motorcycle_context(self):
        title = "Repartidores de aplicaciones bloquean calles de CDMX contra nuevas placas y licencias"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/delivery-rider-context-regression",
            "source": "Diario de Yucatán",
            "date": "2026-11-11",
            "category": "Movilidad",
        })
        courier = next(
            (photo for photo in _pool()
             if photo.get("id") == "contexto_repartidores_motocicleta_cdmx"),
            None,
        )
        self.assertIsNotNone(courier)
        self.assertEqual(courier["kind"], "representativa")
        self.assertEqual(courier["author"], "Palacio Postal")
        self.assertEqual(courier["license"], "CC BY-SA 4.0")
        self.assertIn("no del bloqueo actual", courier["topic"])

        unrelated_protest = {
            "id": "generic_cacerolazo",
            "kind": "representativa",
            "category": "CDMX",
            "topic": "Cacerolazo contra la violencia en Ciudad de México",
            "keywords": ["cacerolazo", "protesta", "manifestación"],
        }
        self.assertLess(_photo_score(article, unrelated_protest), 0)
        self.assertGreaterEqual(_photo_score(article, courier), 0)
        with patch.object(photos, "_pool", return_value=[unrelated_protest, courier]), patch.object(
            photos, "_load", return_value=[]
        ):
            stats = assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_repartidores_motocicleta_cdmx")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(article["photo"]["author"], "Palacio Postal")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertEqual(stats["assigned"], 1)

    def test_generic_march_does_not_use_delivery_photo_disclaimer_as_protest_context(self):
        title = "Viernes 13 de quincena, marchas y bloqueos en CdMx: consulta las alcaldías afectadas"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/generic-march-photo-regression",
            "source": "Sin Embargo",
            "date": "2026-11-13",
            "category": "Movilidad",
        })
        pool = _pool()
        courier = next(
            photo for photo in pool
            if photo.get("id") == "contexto_repartidores_motocicleta_cdmx"
        )
        motorcycle = next(
            photo for photo in pool
            if photo.get("id") == "contexto_motocicleta_zocalo_brigada_2017"
        )
        march_photo = next(
            photo for photo in pool
            if photo.get("id") == "commons_54378318"
        )
        disclaimer_only = representative_photo(
            "negative_disclaimer_only",
            "Cultura",
            "Retrato urbano de archivo; imagen representativa, no corresponde a una marcha",
            ["retrato", "archivo"],
        )

        self.assertLess(_photo_score(article, courier), 0)
        self.assertLess(_photo_score(article, motorcycle), 0)
        self.assertLess(_photo_score(article, disclaimer_only), 0)
        self.assertGreaterEqual(_photo_score(article, march_photo), 0)

        with patch.object(
            photos, "_pool", return_value=[courier, motorcycle, disclaimer_only, march_photo]
        ), patch.object(photos, "_load", return_value=[]):
            stats = assign_photos([article])

        self.assertEqual(article["photo"]["id"], "commons_54378318")
        self.assertEqual(article["photo"]["author"], "Malomalverde")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 3.0")
        self.assertEqual(stats["assigned"], 1)

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


    def test_maria_leon_concert_rejects_unrelated_dance_photo_and_uses_concert_context(self):
        title = ("María León presentó su nueva “Era de Villana” en el Teatro Metropólitan "
                 "de la CDMX: entre invitados, nostalgia y canciones inéditas")
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/maria-leon-photo-regression",
            "source": "Infobae",
            "date": "2026-11-13",
            "published_at": "2026-11-13T07:53:32Z",
            "category": "CDMX",
        })
        self.assertEqual(category_by_headline(title, "CDMX", "Infobae"), "Cultura")
        self.assertEqual(article["category"], "Cultura")
        dance = representative_photo(
            "unrelated_dance_photo", "Cultura",
            "Danza del Fuego performance outside Museo Nacional de Antropología, Chapultepec, CDMX",
            ["Danza del Fuego", "Museo Nacional de Antropología", "danza"],
        )
        dance["source"] = "https://commons.wikimedia.org/wiki/File:Danza_del_Fuego.jpg"
        choir = representative_photo(
            "unrelated_cathedral_choir", "Cultura",
            "Coro de la Catedral metropolitana de la Ciudad de México 01",
            ["coro", "Catedral metropolitana", "música", "Ciudad de México"],
        )
        choir["source"] = "https://commons.wikimedia.org/wiki/File:Coro_Catedral_Metropolitana.jpg"
        concert = representative_photo(
            "contexto_concierto_palacio_deportes_2009", "Cultura",
            "Concierto de Kings of Leon en el Palacio de los Deportes, CDMX (octubre de 2009); foto de archivo representativa, no documenta eventos de la noticia.",
            ["concierto", "música en vivo", "Palacio de los Deportes", "Ciudad de México"],
        )
        concert["url"] = "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fd/PalaciodelosDeportes_Concierto.jpg/960px-PalaciodelosDeportes_Concierto.jpg"
        concert["source"] = "https://commons.wikimedia.org/wiki/File:PalaciodelosDeportes_Concierto.jpg"
        self.assertLess(_photo_score(article, dance), 0)
        self.assertLess(_photo_score(article, choir), 0)
        self.assertGreaterEqual(_photo_score(article, concert), 0)
        self.assertTrue(news.photo_needs_refresh({**article, "photo": dance}))
        article["photo"] = dance
        with patch.object(photos, "_pool", return_value=[dance, concert]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_concierto_palacio_deportes_2009")



    def test_assign_photos_reuses_relevant_reserved_concert_photo_when_other_pool_items_do_not_match(self):
        title = ("María León presentó su nueva “Era de Villana” en el Teatro Metropólitan "
                 "de la CDMX: entre invitados, nostalgia y canciones inéditas")
        first = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/maria-leon-first-photo",
            "source": "Infobae",
            "date": "2026-11-13",
            "published_at": "2026-11-13T07:53:32Z",
            "category": "CDMX",
        })
        second = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/maria-leon-second-photo",
            "source": "Infobae",
            "date": "2026-11-13",
            "published_at": "2026-11-13T07:53:32Z",
            "category": "CDMX",
        })
        concert = representative_photo(
            "contexto_concierto_palacio_deportes_2009", "Cultura",
            "Concierto de Kings of Leon en el Palacio de los Deportes, CDMX (octubre de 2009); foto de archivo representativa, no documenta eventos de la noticia.",
            ["concierto", "música en vivo", "Palacio de los Deportes", "Ciudad de México"],
        )
        concert["url"] = "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fd/PalaciodelosDeportes_Concierto.jpg/960px-PalaciodelosDeportes_Concierto.jpg"
        concert["source"] = "https://commons.wikimedia.org/wiki/File:PalaciodelosDeportes_Concierto.jpg"
        choir = representative_photo(
            "unrelated_cathedral_choir", "Cultura",
            "Coro de la Catedral metropolitana de la Ciudad de México 01",
            ["coro", "Catedral metropolitana", "música", "Ciudad de México"],
        )
        choir["source"] = "https://commons.wikimedia.org/wiki/File:Coro_Catedral_Metropolitana.jpg"
        with patch.object(photos, "_pool", return_value=[concert, choir]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([first, second])
        self.assertEqual(first["photo"]["id"], concert["id"])
        self.assertEqual(second["photo"]["id"], concert["id"])

    def test_assign_photos_preserves_credited_relevant_photo_when_pool_has_no_match(self):
        title = ("María León presentó su nueva “Era de Villana” en el Teatro Metropólitan "
                 "de la CDMX: entre invitados, nostalgia y canciones inéditas")
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/maria-leon-preserve-photo-regression",
            "source": "Infobae",
            "date": "2026-11-13",
            "published_at": "2026-11-13T07:53:32Z",
            "category": "CDMX",
        })
        existing = representative_photo(
            "contexto_concierto_palacio_deportes_2009", "Cultura",
            "Concierto de Kings of Leon en el Palacio de los Deportes, CDMX (octubre de 2009); foto de archivo representativa, no documenta eventos de la noticia.",
            ["concierto", "música en vivo", "Palacio de los Deportes", "Ciudad de México"],
        )
        existing["url"] = "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fd/PalaciodelosDeportes_Concierto.jpg/960px-PalaciodelosDeportes_Concierto.jpg"
        existing["source"] = "https://commons.wikimedia.org/wiki/File:PalaciodelosDeportes_Concierto.jpg"
        unrelated = representative_photo(
            "unrelated_dance_photo", "Cultura",
            "Danza del Fuego performance outside Museo Nacional de Antropología, Chapultepec, CDMX",
            ["Danza del Fuego", "Museo Nacional de Antropología", "danza"],
        )
        unrelated["source"] = "https://commons.wikimedia.org/wiki/File:Danza_del_Fuego.jpg"
        article["photo"] = existing
        self.assertGreaterEqual(_photo_score(article, existing), 0)
        self.assertLess(_photo_score(article, unrelated), 0)
        with patch.object(photos, "_pool", return_value=[unrelated]), patch.object(
            photos, "_load", return_value=[]
        ):
            stats = assign_photos([article])
        self.assertEqual(article["photo"]["id"], existing["id"])
        self.assertEqual(stats["assigned"], 1)


    def test_assign_photos_preserves_credited_local_photo_when_pool_has_no_match(self):
        title = ("María León presentó su nueva “Era de Villana” en el Teatro Metropólitan "
                 "de la CDMX: entre invitados, nostalgia y canciones inéditas")
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/maria-leon-local-photo-regression",
            "source": "Infobae",
            "date": "2026-11-13",
            "published_at": "2026-11-13T07:53:32Z",
            "category": "CDMX",
        })
        existing = representative_photo(
            "local_concert_context", "Cultura",
            "Concierto en el Teatro Metropólitan de Ciudad de México; imagen representativa, no corresponde a María León.",
            ["concierto", "música en vivo", "Teatro Metropólitan", "Ciudad de México"],
        )
        existing["source"] = "https://commons.wikimedia.org/wiki/File:Local_concert_context.jpg"
        unrelated = representative_photo(
            "unrelated_dance_photo", "Cultura",
            "Danza del Fuego performance outside Museo Nacional de Antropología, Chapultepec, CDMX",
            ["Danza del Fuego", "Museo Nacional de Antropología", "danza"],
        )
        unrelated["source"] = "https://commons.wikimedia.org/wiki/File:Danza_del_Fuego.jpg"
        article["photo"] = existing
        self.assertGreaterEqual(_photo_score(article, existing), 0)
        self.assertLess(_photo_score(article, unrelated), 0)
        with patch.object(photos, "_pool", return_value=[unrelated]), patch.object(
            photos, "_load", return_value=[]
        ):
            stats = assign_photos([article])
        self.assertEqual(article["photo"]["id"], existing["id"])
        self.assertEqual(stats["assigned"], 1)


    def test_current_feed_coverage_and_archive_maria_leon_photo(self):
        data = news.load_json(news.DEST, {"articles": []})
        articles = deepcopy(data.get("articles", []))
        self.assertGreaterEqual(len(articles), 25)
        stats = assign_photos(articles)
        self.assertGreaterEqual(stats["assigned"], 25)

        archive = news.load_json(news.ARCHIVE_DIR / "2026-11.json", {"articles": []})
        archived_articles = archive.get("articles", [])
        maria = next(
            (
                item for item in archived_articles
                if item.get("source") == "Infobae"
                and "maria leon" in photos._photo_fold(item.get("title", ""))
            ),
            None,
        )
        self.assertIsNotNone(maria)
        self.assertEqual(
            maria.get("photo", {}).get("id"),
            "contexto_concierto_palacio_deportes_2009",
        )
        self.assertGreaterEqual(_photo_score(maria, maria["photo"]), 0)
        maria_photo_topic = photos._photo_fold(maria["photo"].get("topic", ""))
        self.assertIn("palacio de los deportes", maria_photo_topic)
        self.assertNotIn("coro de la catedral", maria_photo_topic)
        self.assertNotIn("danza del fuego", maria_photo_topic)
        self.assertGreater(stats["unique"], 0)


    def test_cacomixtle_story_replaces_drainage_photo_with_species_context(self):
        article = news.standardize({
            "title": "De los bosques al asfalto: los avistamientos de cacomixtles en la Ciudad de México",
            "url": "https://news.google.com/rss/articles/cacomixtle-photo-regression",
            "source": "Sopitas.com",
            "date": "2026-11-13",
            "category": "CDMX",
        })
        article["category"] = "CDMX"
        drainage = representative_photo(
            "contexto_drenaje_humedal",
            "Servicios",
            "Salida del drenaje hacia el canal del Humedal",
            ["Drenaje Ciudad de México"],
        )
        cacomixtle = next(
            photo for photo in _pool()
            if photo["id"] == "contexto_cacomixtle_babisuri"
        )
        self.assertLess(_photo_score(article, drainage), 0)
        self.assertGreaterEqual(_photo_score(article, cacomixtle), 0)
        with patch.object(photos, "_pool", return_value=[drainage, cacomixtle]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_cacomixtle_babisuri")
        self.assertEqual(article["photo"]["author"], "Jaen Mena")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")

        for relative in (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        ):
            data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
            registered = next(
                item for item in data["photos"]
                if item["id"] == "contexto_cacomixtle_babisuri"
            )
            self.assertEqual(registered["author"], "Jaen Mena")
            self.assertEqual(registered["license"], "CC BY-SA 4.0")
            self.assertTrue(registered["source"].startswith("https://commons.wikimedia.org/wiki/File:"))
            self.assertTrue(registered["licenseUrl"].startswith("https://creativecommons.org/"))

    def test_circuito_interior_crash_rejects_autodromo_and_uses_traffic_context(self):
        article = news.standardize({
            "title": "Accidente en Circuito Interior Hoy: Caos Vial en Esta Zona por Choque de Tráiler en CDMX",
            "url": "https://news.google.com/rss/articles/circuito-interior-photo-regression",
            "source": "N+",
            "date": "2026-11-13",
            "category": "Movilidad",
        })
        article["category"] = "Movilidad"
        pool = _pool()
        autodromo = next(
            photo for photo in pool
            if photo["id"] == "contexto_autodromo_hermanos_rodriguez"
        )
        traffic = next(
            photo for photo in pool
            if photo["id"] == "contexto_trafico_eje_central"
        )
        article["photo"] = autodromo
        self.assertLess(_photo_score(article, autodromo), 0)
        self.assertGreaterEqual(_photo_score(article, traffic), 0)
        with patch.object(photos, "_pool", return_value=[autodromo, traffic]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_trafico_eje_central")
        self.assertEqual(article["photo"]["author"], "Sergio Estrada Flores")
        self.assertEqual(article["photo"]["license"], "CC BY 4.0")


    def test_november_13_incongruent_feed_photos_are_rejected(self):
        cases = [
            ("Accidente en Canal del Norte: Camioneta Choca y Termina Destrozada",
             "Movilidad", "Avenida Francisco I. Madero, Centro Histórico, Ciudad de México - Torre Latinoamericana"),
            ("Accidente en Circuito Interior Hoy: Caos Vial por Choque de Tráiler en CDMX",
             "Movilidad", "Interior de metrobús"),
            ("Caravana con 500 migrantes acampa en Huixtla, Chiapas: esperan a más para avanzar a CDMX",
             "CDMX", "Metrobús en Monumento a la Revolución - TurismoCDMX"),
            ("Mckenna Grace de Los juegos del hambre recuerda a su familia mexicana y canta Pimpón en CDMX",
             "CDMX", "Declaratoria de carnavales como patrimonio cultural inmaterial de la Ciudad de México"),
            ("Joseph Zada y Mckenna Grace desatan la emoción en CDMX durante la alfombra roja de Los Juegos del Hambre",
             "CDMX", "Zócalo de la Ciudad de México durante el 8M, 2019"),
            ("Proponen en Congreso CDMX sancionar a empresas que no entreguen medicamentos a tiempo",
             "CDMX", "Palacio Nacional, sede del Gobierno de México"),
            ("Análisis del PGD CDMX: advierten riesgo de expropiación con banco de suelo",
             "Gobierno", "Sala de Tesorería en Palacio Nacional"),
            ("¿Cuánto cuesta rentar en CDMX? Precios por alcaldía y cuánto necesitas ganar",
             "CDMX", "Teatro Ángela Peralta, Polanco"),
            ("¿Cuánto gana un tamalero en CDMX? Así son los ingresos de un vendedor",
             "CDMX", "Monumento a la Revolución, Ciudad de México"),
            ("¿Cuánto gana un repartidor en CDMX? Estos son sus ingresos diarios",
             "CDMX", "Gran Hotel Ciudad de México formerly El Centro Mercantil"),
            ("Chelerías en CDMX: cuánto cuesta abrir un negocio y qué permisos necesita",
             "CDMX", "Ángel de la Independencia, Ciudad de México"),
            ("CEO de DiDi Latinoamérica se pone al volante en CDMX",
             "CDMX", "Torre Latinoamericana, Centro Histórico de Ciudad de México"),
            ("¡Jet está de vuelta! Su riff más famoso sonará en CDMX en 2027",
             "CDMX", "Plaza de la Constitución (Zócalo) tras un día lluvioso"),
            ("Hasta 35 km/h de rachas en alcaldías de la CDMX este miércoles 11 de noviembre",
             "CDMX", "Zócalo de la Ciudad de México, México"),
            ("Madres de familia denuncian falta de infraestructura en primarias de Coyoacán: exigen domos y mantenimiento",
             "Metro", "Estación Coyoacán de la Línea 3 del Metro de la Ciudad de México 01"),
            ("Mckenna Grace de Los juegos del hambre recuerda a su familia mexicana y canta Pimpón en CDMX",
             "CDMX", "Cineteca Nacional Bodega de Arte - Línea 3 del Cablebús - 1"),
            ("Joseph Zada y Mckenna Grace desatan la emoción en CDMX durante la alfombra de Los Juegos del Hambre",
             "CDMX", "Zócalo de la Ciudad de México durante el 8M, 2019"),
            ("Proponen en el Congreso CDMX sancionar a empresas que no entreguen medicamentos a tiempo",
             "CDMX", "Fotografía aérea de Avenida H. Congreso de la Unión, Candelaria de los Patos y Centro Histórico; tránsito vehicular"),
            ("Congreso de Cdmx condena violencia en foro metropolitano",
             "CDMX", "Palacio Nacional Ciudad de México City DF"),
            ("Accidente en Circuito Interior Hoy: Caos Vial por Choque de Tráiler en CDMX",
             "Movilidad", "003041-004 CAMIONES DE LIMPIA FEBRERO 17 1930 (32497046872)"),
        ]
        for index, (title, category, topic) in enumerate(cases):
            photo_category = "Gobierno" if "Palacio Nacional" in topic or "Tesorería" in topic else category
            photo = representative_photo(
                f"bad_portada_photo_{index}", photo_category, topic, ["Ciudad de México"]
            )
            article = {"title": title, "category": category, "borough": ""}
            with self.subTest(title=title):
                self.assertLess(_photo_score(article, photo), 0)
                self.assertTrue(news.photo_needs_refresh({**article, "photo": photo}))

    def test_november_13_relevant_representative_photos_remain_eligible(self):
        housing = representative_photo(
            "house_context", "CDMX", "Casa Centro Histórico de la Ciudad de México",
            ["vivienda", "casa"],
        )
        courier = next(
            photo for photo in photos._pool()
            if photo["id"] == "contexto_repartidores_motocicleta_cdmx"
        )
        traffic = representative_photo(
            "traffic_context", "Movilidad", "Tránsito vehicular en Eje Central, Ciudad de México",
            ["tráfico vehicular"],
        )
        concert = representative_photo(
            "concert_context", "Cultura", "Banda de rock en concierto con guitarras en escenario",
            ["rock", "concierto"],
        )
        weather = representative_photo(
            "weather_context", "Medio Ambiente", "Viento y nubes sobre Ciudad de México",
            ["viento", "rachas"],
        )
        self.assertGreaterEqual(_photo_score({"title": "¿Cuánto cuesta rentar en CDMX?", "category": "CDMX"}, housing), 0)
        self.assertGreaterEqual(_photo_score({"title": "¿Cuánto gana un repartidor en CDMX?", "category": "CDMX"}, courier), 0)
        self.assertGreaterEqual(_photo_score({"title": "Accidente en Canal del Norte: Camioneta choca", "category": "Movilidad"}, traffic), 0)
        self.assertGreaterEqual(_photo_score({"title": "¡Jet está de vuelta! Su riff más famoso sonará en CDMX en 2027", "category": "CDMX"}, concert), 0)
        self.assertGreaterEqual(_photo_score({"title": "Hasta 35 km/h de rachas en alcaldías de la CDMX", "category": "CDMX"}, weather), 0)


class PerifericoPhotoRegressionTests(unittest.TestCase):
    def test_rocazos_story_rejects_zocalo_and_uses_periferico_photo(self):
        article = news.standardize({
            "title": "Llueven «rocazos» en CDMX",
            "url": "https://news.google.com/rss/articles/rocazos-photo-regression",
            "source": "José Cárdenas",
            "date": "2026-11-13",
            "category": "CDMX",
        })
        zocalo = representative_photo(
            "commons_46666275", "CDMX",
            "Zócalo desde la Torre Latinoamericana, Ciudad de México",
            ["Torre Latinoamericana Ciudad de México"],
        )
        periferico = representative_photo(
            "contexto_periferico_sur_2015", "Movilidad",
            "Lateral del Periférico Sur desde la Glorieta de Vaqueritos, Tlalpan, Ciudad de México (22 de septiembre de 2015); fotografía de archivo representativa de una vialidad, no documenta el taller ni a sus participantes.",
            ["Periférico Sur", "tránsito vehicular", "automovilistas", "vialidad", "Ciudad de México", "Tlalpan"],
        )
        periferico.update({
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cf/Periferico_sur.JPG/960px-Periferico_sur.JPG?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=thumbnail&_=20150924185737",
            "source": "https://commons.wikimedia.org/wiki/File:Periferico_sur.JPG",
            "author": "Victorcinco523",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        })
        self.assertLess(photos._photo_score(article, zocalo), 0)
        self.assertGreaterEqual(photos._photo_score(article, periferico), 0)
        with patch.object(photos, "_pool", return_value=[zocalo, periferico]), patch.object(
            photos, "_load", return_value=[]
        ):
            stats = photos.assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_periferico_sur_2015")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertEqual(article["photo"]["author"], "Victorcinco523")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertEqual(stats["assigned"], 1)

    def test_periferico_photo_is_present_in_all_editorial_catalogs(self):
        expected_source = "https://commons.wikimedia.org/wiki/File:Periferico_sur.JPG"
        for relative in (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        ):
            with self.subTest(path=relative):
                data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
                photo = next(
                    item for item in data["photos"]
                    if item.get("id") == "contexto_periferico_sur_2015"
                )
                self.assertEqual(photo["source"], expected_source)
                self.assertEqual(photo["author"], "Victorcinco523")
                self.assertEqual(photo["license"], "CC BY-SA 4.0")
                self.assertEqual(photo["context"],
                    "Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.")
                self.assertEqual(photo["topic"], "Lateral del Periférico Sur desde la Glorieta de Vaqueritos, Tlalpan, Ciudad de México (22 de septiembre de 2015); fotografía de archivo representativa de una vialidad, no documenta el taller ni a sus participantes.")
                self.assertEqual(photo.get("captured_at"), "2015-09-22")

    def test_existing_representative_photo_refreshes_metadata_from_catalog(self):
        old = representative_photo(
            "contexto_periferico_sur_2015", "Movilidad",
            "Texto editorial anterior sobre un ataque.",
            ["Periférico Sur", "vialidad"],
        )
        old["legacy_note"] = "conservar dato adicional"
        current = representative_photo(
            "contexto_periferico_sur_2015", "Movilidad",
            "Lateral del Periférico Sur desde la Glorieta de Vaqueritos, Tlalpan, Ciudad de México (22 de septiembre de 2015); fotografía de archivo representativa de una vialidad, no documenta el taller ni a sus participantes.",
            ["Periférico Sur", "vialidad", "Tlalpan"],
        )
        article = {
            "title": "Taller de manejo defensivo para mujeres en CDMX",
            "category": "Movilidad",
            "photo": old,
        }
        with patch.object(photos, "_pool", return_value=[current]):
            photos.assign_photos([article])
        self.assertEqual(article["photo"]["topic"], current["topic"])
        self.assertEqual(article["photo"]["legacy_note"], "conservar dato adicional")

    def test_farmacias_del_ahorro_acquisition_rejects_unrelated_carnival_photo(self):
        title = "Farmacias del Ahorro compra Benavides y fortalece su presencia en CDMX y Edomex"
        article = news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/farmacias-benavides-photo-regression",
            "source": "El Sol de México",
            "date": "2026-11-13",
            "published_at": "2026-11-13T18:38:11Z",
            "category": "CDMX",
        })
        carnival = representative_photo(
            "unrelated_carnival_photo",
            "CDMX",
            "DECLARATORIA DE CARNAVALES COMO PATRIMONIO CULTURAL INMATERIAL DE LA CIUDAD DE MÉXICO 13",
            ["Calles Ciudad de México"],
        )
        pharmacy = representative_photo(
            "contexto_farmacia_santa_maria_ribera_2022",
            "CDMX",
            "Farmacia de barrio en Santa María de la Ribera, Cuauhtémoc, CDMX (29 dic 2022); imagen representativa, no es de Farmacias del Ahorro ni Benavides.",
            ["farmacia", "farmacia de barrio", "Santa María de la Ribera", "Cuauhtémoc", "Ciudad de México"],
        )
        pharmacy.update({
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/85/Farmacia_en_Santa_Mar%C3%ADa_de_la_Ribera.jpg/960px-Farmacia_en_Santa_Mar%C3%ADa_de_la_Ribera.jpg",
            "source": "https://commons.wikimedia.org/wiki/File:Farmacia_en_Santa_Mar%C3%ADa_de_la_Ribera.jpg",
            "author": "ProtoplasmaKid",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        })
        self.assertLess(_photo_score(article, carnival), 0)
        self.assertGreaterEqual(_photo_score(article, pharmacy), 0)
        article["photo"] = carnival
        with patch.object(photos, "_pool", return_value=[carnival, pharmacy]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], pharmacy["id"])
        self.assertEqual(article["photo"]["author"], "ProtoplasmaKid")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")
        self.assertIn("no es de Farmacias del Ahorro ni Benavides", article["photo"]["topic"])

    def test_pharmacy_context_photo_has_complete_attribution_in_all_catalogs(self):
        expected_topic = "Farmacia de barrio en Santa María de la Ribera, Cuauhtémoc, CDMX (29 dic 2022); imagen representativa, no es de Farmacias del Ahorro ni Benavides."
        relative_paths = (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        )
        for relative in relative_paths:
            with self.subTest(path=relative):
                data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
                photo = next((item for item in data.get("photos", [])
                              if item.get("id") == "contexto_farmacia_santa_maria_ribera_2022"), None)
                self.assertIsNotNone(photo, relative)
                self.assertEqual(photo.get("topic"), expected_topic)
                self.assertEqual(photo.get("author"), "ProtoplasmaKid")
                self.assertEqual(photo.get("license"), "CC BY-SA 4.0")
                self.assertEqual(photo.get("source"), "https://commons.wikimedia.org/wiki/File:Farmacia_en_Santa_Mar%C3%ADa_de_la_Ribera.jpg")


class CrimePhotoCategoryRegressionTests(unittest.TestCase):
    def test_crime_headlines_in_cdmx_category_reject_borough_only_photos(self):
        cases = (
            (
                "Cae sujeto que asaltaba mujeres en taxi y moto en Magdalena Contreras",
                "MX NS LA MAGDALENA CONTRERAS 03",
            ),
            (
                "Cae sujeto señalado por asaltos violentos contra mujeres en Magdalena Contreras",
                "MX NS LA MAGDALENA CONTRERAS 09",
            ),
            (
                "Detienen a Taxista Acusado de Intentar Asaltar a una Mujer en la Magdalena Contreras, CDMX",
                "MX NS LA MAGDALENA CONTRERAS 05",
            ),
        )
        for title, photo_topic in cases:
            with self.subTest(title=title):
                article = {
                    "title": title,
                    "category": "CDMX",
                    "borough": "La Magdalena Contreras",
                }
                borough_photo = representative_photo(
                    "borough_only_crime_context",
                    "Alcaldías",
                    photo_topic,
                    ["Magdalena Contreras Ciudad de México"],
                )
                self.assertLess(_photo_score(article, borough_photo), 0)



class EditorialPhotoMismatchRegressionTests(unittest.TestCase):
    def assert_photo_replaced(self, title, category, current, candidate, borough=""):
        article = {
            "title": title,
            "category": category,
            "borough": borough,
            "url": "https://news.google.com/rss/articles/editorial-photo-regression",
            "photo": current,
        }
        self.assertTrue(news.photo_needs_refresh(article))
        self.assertLess(_photo_score(article, current), 0)
        self.assertGreaterEqual(_photo_score(article, candidate), 0)
        with patch.object(photos, "_pool", return_value=[current, candidate]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], candidate["id"])
        self.assertEqual(article["photo"]["author"], "Autor de prueba")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 4.0")

    def test_public_lighting_story_replaces_police_patrol_with_luminarias(self):
        current = representative_photo("patrulla-luminarias", "Seguridad",
            "Nuevas patrullas para Cuajimalpa 05", ["patrullas", "policía", "seguridad"])
        candidate = representative_photo("luminarias-alvaro-obregon", "Seguridad",
            "Luminarias de Avenida Álvaro Obregón, colonia Roma, CDMX (2013); imagen representativa, no documenta las obras de SOBSE.",
            ["luminarias", "alumbrado público", "iluminación urbana", "farolas"])
        self.assert_photo_replaced(
            "Con más de 80 mil nuevas luminarias, la SOBSE fortalece la seguridad en caminos de la Ciudad de México",
            "Seguridad", current, candidate)

    def test_semovi_license_suspension_replaces_palacio_nacional_with_semovi_offices(self):
        current = representative_photo("palacio-semovi", "Gobierno",
            "Palacio Nacional de México - Exteriores - 3", ["Palacio Nacional", "Gobierno"])
        candidate = representative_photo("oficinas-semovi-roma", "Gobierno",
            "Fachada de oficinas de SEMOVI en colonia Roma, CDMX (2022); imagen representativa, no documenta la suspensión de trámites.",
            ["SEMOVI", "Secretaría de Movilidad", "licencias", "trámites", "control vehicular", "oficinas"])
        self.assert_photo_replaced(
            "Semovi suspenderá trámites de licencias y control vehicular en CDMX",
            "Gobierno", current, candidate)

    def test_safety_ranking_replaces_theatre_with_police_patrol(self):
        current = representative_photo("teatro-miguel-hidalgo", "CDMX",
            "Teatro Ángela Peralta, Polanco, alcaldía Miguel Hidalgo",
            ["Teatro Ángela Peralta", "Polanco", "Miguel Hidalgo"])
        candidate = representative_photo("patrulla-cdmx-ranking", "Seguridad",
            "Patrulla de Ciudad de México; imagen representativa, no documenta el ranking de seguridad de Miguel Hidalgo.",
            ["patrullas", "policía", "seguridad ciudadana", "Ciudad de México"])
        self.assert_photo_replaced(
            "Tabe: Miguel Hidalgo es la segunda alcaldía más segura de CDMX",
            "Seguridad", current, candidate, "Miguel Hidalgo")

    def test_building_safety_story_replaces_patrol_with_building_reconstruction(self):
        current = representative_photo("patrulla-construcciones", "Seguridad",
            "Nuevas patrullas para Cuajimalpa 02", ["patrullas", "seguridad"])
        candidate = representative_photo("reconstruccion-edificios-bj", "Seguridad",
            "Reconstrucción de edificios en Benito Juárez tras el sismo de 2017; imagen de archivo representativa.",
            ["edificios", "reconstrucción", "seguridad estructural", "inmuebles"])
        self.assert_photo_replaced(
            "CDMX prepara reformas para reforzar la seguridad de las construcciones; edificios anteriores a 1985, prioridad",
            "Seguridad", current, candidate)

    def test_saltillo_security_model_rejects_cdmx_patrol_photo(self):
        article = news.standardize({
            "title": "Destacan en CDMX modelo de seguridad aplicado en Saltillo",
            "url": "https://news.google.com/rss/articles/saltillo-security-photo-regression",
            "source": "El Horizonte",
            "date": "2026-11-14",
            "category": "Seguridad",
            "location": "Ciudad de México (sin alcaldía identificada)",
        })
        cdmx_patrol = representative_photo(
            "commons_157006042",
            "Seguridad",
            "Nuevas patrullas para Cuajimalpa 06",
            ["Secretaría de Seguridad Ciudadana CDMX patrulla"],
        )
        saltillo_patrol = representative_photo(
            "saltillo-police-context",
            "Seguridad",
            "Policía Municipal de Saltillo, Coahuila",
            ["seguridad", "patrullas", "Saltillo"],
        )

        self.assertLess(_photo_score(article, cdmx_patrol), 0)
        self.assertGreaterEqual(_photo_score(article, saltillo_patrol), 0)
        article["photo"] = cdmx_patrol
        with patch.object(photos, "_pool", return_value=[cdmx_patrol]):
            assign_photos([article])
        self.assertNotIn("photo", article)

    def test_neto_store_count_replaces_city_panorama_with_grocery_store(self):
        current = representative_photo("panorama-neto", "CDMX",
            "Panorámicas CDMX IMG 4417 Alameda Central", ["Alameda Central", "panorámica", "CDMX"])
        candidate = representative_photo("tienda-coyoacan-neto", "CDMX",
            "Tienda de abarrotes en el mercado de Coyoacán, CDMX (2018); imagen representativa, no es una sucursal de Tiendas Neto.",
            ["tienda de abarrotes", "comercio minorista", "tiendas", "Coyoacán"])
        self.assert_photo_replaced(
            "Neto rebasa las 2 mil tiendas; CDMX y Edomex concentran tres de cada diez",
            "CDMX", current, candidate)

    def test_hostile_architecture_story_replaces_monument_with_hostile_planter(self):
        current = representative_photo("monumento-arquitectura-hostil", "CDMX",
            "Estando firmes (Monumento a la Revolución, CDMX, México)",
            ["Monumento a la Revolución", "CDMX"])
        candidate = representative_photo("jardinera-hostil-benito-juarez", "CDMX",
            "Jardinera de arquitectura hostil en Eje 6 y Patriotismo, Benito Juárez, CDMX (2023); imagen representativa.",
            ["arquitectura hostil", "jardineras con púas", "comercio ambulante", "Benito Juárez"])
        self.assert_photo_replaced(
            "Bancas que impiden recostarse y jardineras con púas: arquitectura hostil en CDMX",
            "CDMX", current, candidate)

    def test_new_context_photos_have_complete_credits_in_all_catalogs(self):
        expected = {
            "contexto_luminarias_alvaro_obregon_2013",
            "contexto_semovi_oficinas_roma_2022",
            "contexto_tienda_abarrotes_coyoacan_2018",
            "contexto_jardinera_arquitectura_hostil_benito_juarez_2023",
            "contexto_aicm_aviones_pista_2026",
            "contexto_consolas_videojuegos_2026",
        }
        for relative in (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        ):
            with self.subTest(path=relative):
                data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
                photos_by_id = {item.get("id"): item for item in data.get("photos", [])}
                for photo_id in expected:
                    self.assertIn(photo_id, photos_by_id)
                    item = photos_by_id[photo_id]
                    self.assertTrue(item.get("author"))
                    self.assertEqual(item.get("license"), "CC BY-SA 4.0")
                    self.assertTrue(item.get("source", "").startswith("https://commons.wikimedia.org/wiki/File:"))
                    self.assertTrue(item.get("licenseUrl", "").startswith("https://creativecommons.org/"))
                if "count" in data:
                    self.assertEqual(data["count"], len(data["photos"]))


class CurrentFeedEditorialPhotoRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = {photo["id"]: photo for photo in _pool()}

    def assert_photo_replaced(self, title, category, current_id, candidate_id):
        current = deepcopy(self.pool[current_id])
        candidate = deepcopy(self.pool[candidate_id])
        article = {
            "title": title,
            "category": category,
            "source": "El Sol de México",
            "url": "https://news.google.com/rss/articles/editorial-photo-current-feed-regression",
            "date": "2026-11-13",
            "photo": current,
        }
        self.assertTrue(news.photo_needs_refresh(article))
        self.assertLess(_photo_score(article, current), 0)
        self.assertGreaterEqual(_photo_score(article, candidate), 0)
        with patch.object(photos, "_pool", return_value=[current, candidate]), patch.object(
            photos, "_load", return_value=[]
        ):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], candidate_id)
        self.assertTrue(article["photo"]["author"])
        self.assertTrue(article["photo"]["license"])

    def test_airport_flight_story_replaces_metro_terminal_station_with_aicm_aircraft(self):
        self.assert_photo_replaced(
            "Aeropuerto de CDMX informa sobre afectaciones de vuelos desde y hacia EEUU",
            "Movilidad", "reciente_c4e1387f207f104c", "contexto_aicm_aviones_pista_2026")

    def test_airspace_closure_story_rejects_unrelated_city_sculpture_and_uses_aircraft_photo(self):
        title = "El cierre aéreo de EE.UU. afectó a más de 6,000 pasajeros en la Ciudad de México"
        self.assertEqual(category_by_headline(title, "CDMX"), "Movilidad")
        self.assert_photo_replaced(
            title, "Movilidad", "commons_80021377", "contexto_aicm_aviones_pista_2026")

    def test_pokemon_go_story_replaces_market_with_specific_gameplay_photo(self):
        self.assert_photo_replaced(
            "Pokémon Go genera 420,000 dólares en CDMX y muestra que México es un mercado clave para el juego",
            "Cultura", "commons_75214598", "contexto_pokemon_go_bench_2016")

    def test_garbage_story_replaces_treasury_hall_with_concert_photo(self):
        self.assert_photo_replaced(
            "Garbage llega al Zócalo de CDMX: Shirley Manson agradece al público mexicano",
            "Cultura", "commons_98002541", "contexto_concierto_palacio_deportes_2009")

    def test_market_funding_story_replaces_covid_sanitation_photo_with_market_context(self):
        self.assert_photo_replaced(
            "Mercados de CDMX recibirán un millón de pesos para mejorar sus instalaciones",
            "Gobierno", "commons_89299418", "commons_152145024")

    def test_bramadero_resource_delivery_rejects_cicloton_and_uses_market_investment_photo(self):
        title = "Entrega Brugada recursos al Mercado Bramadero de Iztacalco"
        self.assertEqual(category_by_headline(title, "CDMX"), "Gobierno")
        self.assert_photo_replaced(
            title, "Gobierno", "commons_41703830", "commons_152145024")

    def test_console_photo_caption_is_explicitly_representative_not_pokemon_go(self):
        expected = "Consolas y videojuegos actuales (fotografía de 2026); imagen representativa del sector de videojuegos, no corresponde a Pokémon Go ni a la mercancía asegurada en Plaza Meave."
        for relative in (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        ):
            with self.subTest(path=relative):
                data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
                photo = next(item for item in data["photos"] if item.get("id") == "contexto_consolas_videojuegos_2026")
                self.assertEqual(photo["topic"], expected)



class CurrentEditorialPhotoRegressionTests(unittest.TestCase):
    def make_article(self, title, category="CDMX", source="Medio de prueba"):
        return news.standardize({
            "title": title,
            "url": "https://news.google.com/rss/articles/editorial-context-regression",
            "source": source,
            "date": "2026-11-13",
            "category": category,
        })

    def photo(self, photo_id):
        return next((item for item in _pool() if item.get("id") == photo_id), None)

    def test_wild_rift_is_culture_and_uses_mobile_gaming_context(self):
        title = "K/DA Wild Rift en CDMX: Riot Games confirma una pop-up especial en Centro Santa Fe"
        article = self.make_article(title, source="TierraGamer")
        self.assertEqual(article["category"], "Cultura")
        self.assertEqual(_photo_category(article), "Cultura")
        unrelated = self.photo("commons_83241758")
        relevant = self.photo("contexto_juego_movil_smartphone_2016")
        self.assertIsNotNone(unrelated)
        self.assertIsNotNone(relevant)
        self.assertLess(_photo_score(article, unrelated), 0)
        self.assertGreaterEqual(_photo_score(article, relevant), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_juego_movil_smartphone_2016")

    def test_employment_fair_is_services_and_uses_archival_job_fair_photo(self):
        title = ("Feria del Empleo en Iztapalapa ofrece mil vacantes con empresas "
                 "como Bimbo, Sears y Chedraui; fecha y horario")
        article = self.make_article(title, source="El Sol de México")
        self.assertEqual(article["category"], "Servicios")
        unrelated = self.photo("commons_20284563")
        relevant = self.photo("contexto_feria_empleo_cdmx_2018")
        self.assertIsNotNone(unrelated)
        self.assertIsNotNone(relevant)
        self.assertLess(_photo_score(article, unrelated), 0)
        self.assertGreaterEqual(_photo_score(article, relevant), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_feria_empleo_cdmx_2018")

    def test_women_entrepreneurs_fair_rejects_old_posada_photo(self):
        title = "Impulsa alcaldía Iztacalco el comercio local con la Feria de Mujeres Emprendedoras"
        article = self.make_article(title)
        self.assertEqual(article["category"], "Servicios")
        unrelated = self.photo("commons_75043274")
        relevant = self.photo("contexto_emprendimiento_femenino_2025")
        self.assertIsNotNone(unrelated)
        self.assertIsNotNone(relevant)
        self.assertLess(_photo_score(article, unrelated), 0)
        self.assertGreaterEqual(_photo_score(article, relevant), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_emprendimiento_femenino_2025")

    def test_weather_forecast_rejects_unrelated_angel_bicycle_photo(self):
        title = "Previsión meteorológica del estado del tiempo en Ciudad de México para este sábado 14 de noviembre"
        article = self.make_article(title, category="CDMX", source="Infobae")
        unrelated = {
            "id": "commons_109767271",
            "kind": "representativa",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/73/%C3%81ngel_de_la_independencia_en_bici.jpg/960px-%C3%81ngel_de_la_independencia_en_bici.jpg",
            "category": "CDMX",
            "borough": "",
            "topic": "Ángel de la independencia en bici",
            "keywords": ["Ángel de la Independencia Ciudad de México"],
            "author": "Didaskalia edu",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source": "https://commons.wikimedia.org/wiki/File:%C3%81ngel_de_la_independencia_en_bici.jpg",
        }
        article["photo"] = deepcopy(unrelated)
        self.assertLess(_photo_score(article, unrelated), 0)
        assign_photos([article])
        assigned = article.get("photo")
        self.assertTrue(
            assigned is None or _photo_score(article, assigned) >= 0,
            "Una previsión meteorológica no debe conservar una foto de bicicleta o monumento sin contexto del clima.",
        )

    def test_market_c5_stories_reject_non_surveillance_market_photos(self):
        cases = (
            ("Mercado Bramadero en Iztacalco será el primero conectado al C5; "
             "Brugada asegura que todos los mercados tendrán cámaras", "commons_89299418"),
            ("Mercados de CDMX tendrán vigilancia conectada al C5, anuncia Brugada",
             "commons_152145024"),
        )
        for title, wrong_id in cases:
            with self.subTest(title=title):
                article = self.make_article(title)
                self.assertEqual(article["category"], "Seguridad")
                wrong = self.photo(wrong_id)
                self.assertIsNotNone(wrong)
                self.assertLess(_photo_score(article, wrong), 0)
                with patch.object(photos, "_pool", return_value=[wrong]):
                    assign_photos([article])
                self.assertNotIn("photo", article)

                surveillance = representative_photo(
                    "market-security-cameras",
                    "Seguridad",
                    "Cámaras de videovigilancia conectadas al C5 en un mercado público",
                    ["mercados públicos", "C5", "cámaras de seguridad"],
                )
                self.assertGreaterEqual(_photo_score(article, surveillance), 0)

    def test_animal_rights_march_rejects_unrelated_peace_march_photo(self):
        article = self.make_article(
            "Marcha por los derechos de los animales y otras manifestaciones este sábado de Buen Fin en CDMX"
        )
        peace_march = self.photo("commons_54378318")
        self.assertIsNotNone(peace_march)
        self.assertLess(_photo_score(article, peace_march), 0)
        with patch.object(photos, "_pool", return_value=[peace_march]):
            assign_photos([article])
        self.assertNotIn("photo", article)

        animal_march = representative_photo(
            "animal-rights-march",
            article["category"],
            "Marcha por los derechos de los animales en Ciudad de México",
            ["manifestación por los animales", "protección animal"],
        )
        self.assertGreaterEqual(_photo_score(article, animal_march), 0)

    def test_vehicle_crashes_reject_metro_and_quake_support_motorcycle_photos(self):
        cases = (
            (
                "Vuelca Automóvil y Deja una Persona Herida en la Colonia Vicente Guerrero, Iztapalapa",
                "commons_20284563",
            ),
            (
                "Mueren dos motociclistas tras accidente vial en Venustiano Carranza",
                "contexto_motocicleta_zocalo_brigada_2017",
            ),
        )
        for title, wrong_id in cases:
            with self.subTest(title=title):
                article = self.make_article(title, category="Movilidad")
                wrong = self.photo(wrong_id)
                self.assertIsNotNone(wrong)
                self.assertLess(_photo_score(article, wrong), 0)
                with patch.object(photos, "_pool", return_value=[wrong]):
                    assign_photos([article])
                self.assertNotIn("photo", article)

                road_context = representative_photo(
                    "traffic-context",
                    article["category"],
                    "Tráfico vehicular y vialidad en la alcaldía mencionada en Ciudad de México",
                    ["tránsito vehicular", "automóviles", "accidente vial", "vialidad"],
                )
                self.assertGreaterEqual(_photo_score(article, road_context), 0)

    def test_autoparts_seizure_rejects_new_patrols_photo(self):
        article = self.make_article(
            "Aseguran tres toneladas de autopartes presuntamente robadas en CDMX",
            category="Seguridad",
        )
        patrols = self.photo("commons_157006043")
        self.assertIsNotNone(patrols)
        self.assertLess(_photo_score(article, patrols), 0)
        with patch.object(photos, "_pool", return_value=[patrols]):
            assign_photos([article])
        self.assertNotIn("photo", article)

        recovered_parts = representative_photo(
            "recovered-auto-parts",
            "Seguridad",
            "Autopartes y refacciones recuperadas en un almacén",
            ["autopartes", "refacciones", "decomiso"],
        )
        self.assertGreaterEqual(_photo_score(article, recovered_parts), 0)

    def test_extortion_is_security_even_when_rss_says_cdmx(self):
        title = "Vinculan a proceso a Ismael N por extorsionar a comerciante en Iztapalapa"
        self.assertEqual(category_by_headline(title, "CDMX"), "Seguridad")
        article = self.make_article(title)
        self.assertEqual(article["category"], "Seguridad")

    def test_new_context_photos_have_licensed_credits_in_all_public_catalogs(self):
        expected = {
            "contexto_juego_movil_smartphone_2016",
            "contexto_feria_empleo_cdmx_2018",
            "contexto_emprendimiento_femenino_2025",
        }
        for relative in (
            "assets/fotos/contexto-tematico.json",
            "assets/fotos/indice-noticias-1100.json",
            "assets/fotos/catalogo-editorial-1100.json",
        ):
            data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
            photos_by_id = {item.get("id"): item for item in data.get("photos", [])}
            for photo_id in expected:
                with self.subTest(path=relative, photo=photo_id):
                    photo = photos_by_id.get(photo_id)
                    self.assertIsNotNone(photo)
                    self.assertEqual(photo.get("kind"), "representativa")
                    self.assertTrue(photo.get("author"))
                    self.assertTrue(photo.get("license"))
                    self.assertTrue(photo.get("source", "").startswith(
                        "https://commons.wikimedia.org/wiki/File:"
                    ))
                    self.assertTrue(photo.get("licenseUrl", "").startswith(
                        "https://creativecommons.org/"
                    ))
                    self.assertTrue(photo.get("context", "").startswith(
                        "Imagen de carácter ilustrativo y referencial;"
                    ))

    def test_advertising_license_story_rejects_semovi_photo_and_uses_building_ads(self):
        title = "Hay 17 empresas de publicidad sin licencia en CDMX: Metrópolis"
        article = self.make_article(title, category="Gobierno", source="El Universal")
        semovi = self.photo("contexto_semovi_oficinas_roma_2022")
        advertising = self.photo("contexto_publicidad_edificios_condesa_2013")
        self.assertIsNotNone(semovi)
        self.assertIsNotNone(advertising)
        self.assertLess(_photo_score(article, semovi), 0)
        self.assertGreaterEqual(_photo_score(article, advertising), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_publicidad_edificios_condesa_2013")
        self.assertEqual(article["photo"]["author"], "Keizers")
        self.assertEqual(article["photo"]["license"], "CC BY-SA 3.0")

    def test_pokemon_go_story_rejects_console_photo_and_uses_gameplay_photo(self):
        title = "Pokémon Go genera 420,000 dólares en CDMX y muestra que México es un mercado clave para el juego"
        article = self.make_article(title, category="Cultura", source="Expansión")
        consoles = self.photo("contexto_consolas_videojuegos_2026")
        gameplay = self.photo("contexto_pokemon_go_bench_2016")
        self.assertIsNotNone(consoles)
        self.assertIsNotNone(gameplay)
        self.assertLess(_photo_score(article, consoles), 0)
        self.assertGreaterEqual(_photo_score(article, gameplay), 0)
        assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_pokemon_go_bench_2016")
        self.assertEqual(article["photo"]["author"], "Monika P")
        self.assertEqual(article["photo"]["license"], "CC0 1.0")

    def test_contextual_photo_credits_are_merged_into_public_credit_catalog(self):
        data = json.loads((REPO_ROOT / "assets/fotos/contexto-tematico.json").read_text(encoding="utf-8"))
        photos = {item["id"]: item for item in data["photos"]}
        for photo_id in ("contexto_publicidad_edificios_condesa_2013", "contexto_pokemon_go_bench_2016"):
            photo = photos.get(photo_id)
            self.assertIsNotNone(photo)
            self.assertTrue(photo["author"])
            self.assertTrue(photo["license"])
            self.assertTrue(photo["licenseUrl"].startswith("https://creativecommons.org/"))
            self.assertTrue(photo["source"].startswith("https://commons.wikimedia.org/wiki/File:"))
        loader = (REPO_ROOT / "assets/creditos.js").read_text(encoding="utf-8")
        self.assertIn("/assets/fotos/contexto-tematico.json", loader)
        self.assertIn("new Map", loader)

    def test_current_feed_rejects_unrelated_hydraulic_nightlife_and_security_photos(self):
        cases = (
            (
                "Proyectan 643 obras hidráulicas y aumenta 77% la inversión en la Cdmx",
                "CDMX",
                "Obras remodelación Zócalo Ciudad de México 2017",
            ),
            (
                "Antro Home Alone: fiesta en mansión de Polanco CDMX",
                "Cultura",
                "Teatro Ángela Peralta, Polanco, alcaldía Miguel Hidalgo, Ciudad de México",
            ),
            (
                "CDMX encabeza la tasa de denuncias por fraude en México: 2.6 veces el promedio nacional",
                "Seguridad",
                "Graduación de la Policía de la Ciudad de México",
            ),
            (
                "Extorsiones en Puebla se originan en cárceles del Edomex, CDMX y Jalisco",
                "Seguridad",
                "Graduación de la Policía de la Ciudad de México",
            ),
            (
                "Aseguran tres toneladas de autopartes presuntamente robadas en CDMX",
                "Seguridad",
                "Graduación de la Policía de la Ciudad de México",
            ),
            (
                "Procesan a presunto extorsionador en la alcaldía Iztapalapa",
                "Seguridad",
                "Claudia Sheinbaum entrega patrullas Iztapalapa 01",
            ),
            (
                "Vinculan a Proceso al 'Choppersito', Presunto Generador de Violencia en Iztapalapa",
                "Seguridad",
                "Claudia Sheinbaum entrega patrullas Iztapalapa 03",
            ),
            (
                "Vinculan a proceso a Ismael N por extorsionar a comerciante en Iztapalapa",
                "Seguridad",
                "Claudia Sheinbaum entrega patrullas Iztapalapa 02",
            ),
        )
        for index, (title, category, topic) in enumerate(cases):
            with self.subTest(title=title):
                article = news.standardize({
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/photo-guard-{index}",
                    "source": "Medio de prueba",
                    "date": "2026-11-13",
                    "category": category,
                    "borough": "",
                })
                self.assertIsNotNone(article)
                wrong_photo = representative_photo(
                    f"wrong_context_{index}", category, topic, []
                )
                article["photo"] = wrong_photo
                self.assertLess(_photo_score(article, wrong_photo), 0)
                with patch.object(photos, "_pool", return_value=[wrong_photo]):
                    assign_photos([article])
                self.assertNotIn("photo", article)

    def test_current_feed_rejects_remaining_unrelated_nightlife_food_parts_and_process_photos(self):
        cases = (
            (
                "Antro Home Alone: fiesta en mansión de Polanco CDMX",
                "CDMX",
                "Capilla posa Virgen de Guadalupe en la fiesta del Jubileo en Iztacalco, Ciudad de México",
            ),
            (
                "Aseguran tres toneladas de autopartes presuntamente robadas en CDMX",
                "Seguridad",
                "Entrega Claudia Sheinbaum 113 nuevas patrullas en Gustavo A Madero 04",
            ),
            (
                "Vinculan a Proceso al 'Choppersito', Presunto Generador de Violencia en Iztapalapa",
                "Seguridad",
                "Metro Iztapalapa 02",
            ),
            (
                "Vinculan a proceso a Ismael N por extorsionar a comerciante en Iztapalapa",
                "Seguridad",
                "Adquisición patrullas para la Policía 03",
            ),
            (
                "Dónde comer chicharrones preparados y quesadillas de sesos baratos en Iztapalapa, CDMX",
                "CDMX",
                "Vistas de la Ciudad de México desde la Torre Latinoamericana 02",
            ),
        )
        for index, (title, category, topic) in enumerate(cases):
            with self.subTest(title=title):
                article = news.standardize({
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/current-photo-guard-{index}",
                    "source": "Medio de prueba",
                    "date": "2026-11-13",
                    "category": category,
                    "borough": "",
                })
                self.assertIsNotNone(article)
                wrong_photo = representative_photo(
                    f"current_wrong_context_{index}", category, topic, []
                )
                article["photo"] = wrong_photo
                self.assertLess(_photo_score(article, wrong_photo), 0)
                with patch.object(photos, "_pool", return_value=[wrong_photo]):
                    assign_photos([article])
                self.assertNotIn("photo", article)

    def test_market_c5_surveillance_story_rejects_covid_sanitation_photo(self):
        article = news.standardize({
            "title": (
                "Mercado Bramadero en Iztacalco será el primero conectado al C5; "
                "Brugada asegura que todos los mercados tendrán cámaras"
            ),
            "url": "https://news.google.com/rss/articles/market-c5-photo-regression",
            "source": "El Universal",
            "date": "2026-11-14",
            "category": "Seguridad",
        })
        self.assertIsNotNone(article)

        covid_sanitation = representative_photo(
            "market-covid-hygiene",
            "Servicios",
            "Medidas de sanidad en los mercados de la Ciudad de México durante la epidemia de COVID-19. 1",
            ["Mercados públicos Ciudad de México"],
        )
        article["photo"] = covid_sanitation
        self.assertLess(_photo_score(article, covid_sanitation), 0)
        with patch.object(photos, "_pool", return_value=[covid_sanitation]):
            assign_photos([article])
        self.assertNotIn("photo", article)

        surveillance = representative_photo(
            "market-security-cameras",
            "Seguridad",
            "Cámaras de videovigilancia instaladas en un mercado público de Iztacalco",
            ["C5", "cámaras de seguridad", "vigilancia de mercados"],
        )
        self.assertGreaterEqual(_photo_score(article, surveillance), 0)


    def test_metro_schedule_rejects_rain_operation_photo_and_uses_metro_context(self):
        title = (
            "¡Toma previsiones! Metro CDMX tendrá horario especial este lunes "
            "por aniversario de la Revolución Mexicana"
        )
        article = self.make_article(title, category="Metro", source="El Economista")
        unrelated = self.photo("commons_75263694")
        relevant = self.photo("archivo_metro_007")
        self.assertIsNotNone(unrelated)
        self.assertIsNotNone(relevant)
        self.assertIn("Operativo de Lluvias", unrelated["topic"])
        self.assertIn("Metro", relevant["topic"])

        self.assertLess(_photo_score(article, unrelated), 0)
        self.assertGreaterEqual(_photo_score(article, relevant), 0)
        with patch.object(photos, "_pool", return_value=[unrelated, relevant]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "archivo_metro_007")
        self.assertTrue(article["photo"]["author"])
        self.assertTrue(article["photo"]["license"])
        self.assertTrue(article["photo"]["licenseUrl"])
        self.assertTrue(article["photo"]["source"].startswith(
            "https://commons.wikimedia.org/wiki/File:"
        ))


    def test_defensive_driving_workshop_rejects_city_monument_and_uses_traffic_context(self):
        title = "Ofrecen taller gratuito de manejo defensivo y preventivo para mujeres en CDMX"
        article = self.make_article(title, source="El Sol de México")
        unrelated = self.photo("commons_33473121")
        relevant = self.photo("contexto_trafico_eje_central")
        self.assertIsNotNone(unrelated)
        self.assertIsNotNone(relevant)
        self.assertIn("Monumento a Colón", unrelated["topic"])
        self.assertIn("Tráfico vehicular", relevant["topic"])

        article["photo"] = unrelated
        self.assertLess(_photo_score(article, unrelated), 0)
        self.assertGreaterEqual(_photo_score(article, relevant), 0)
        with patch.object(photos, "_pool", return_value=[unrelated, relevant]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_trafico_eje_central")
        self.assertEqual(article["photo"]["kind"], "representativa")
        self.assertTrue(article["photo"]["author"])
        self.assertTrue(article["photo"]["license"])
        self.assertTrue(article["photo"]["licenseUrl"])
        self.assertTrue(article["photo"]["source"].startswith(
            "https://commons.wikimedia.org/wiki/File:"
        ))


    def test_delivery_neighbor_threat_story_rejects_police_graduation_photo(self):
        title = "De amenazas con pistola a destrozos: ¿qué pasó entre repartidores y vecinos en CDMX?"
        article = self.make_article(title, category="Seguridad", source="El Economista")
        graduation = self.photo("commons_75245989")
        patrol = self.photo("archivo_seguridad_002")
        self.assertIsNotNone(graduation)
        self.assertIsNotNone(patrol)
        self.assertIn("Graduación", graduation["topic"])
        self.assertIn("Patrulla vecinal", patrol["topic"])

        self.assertLess(_photo_score(article, graduation), 0)
        self.assertGreaterEqual(_photo_score(article, patrol), 0)
        with patch.object(photos, "_pool", return_value=[graduation, patrol]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "archivo_seguridad_002")
        self.assertTrue(article["photo"]["author"])
        self.assertTrue(article["photo"]["license"])
        self.assertTrue(article["photo"]["licenseUrl"])
        self.assertTrue(article["photo"]["source"].startswith(
            "https://commons.wikimedia.org/wiki/File:"
        ))



    def test_delivery_neighbor_threat_story_rejects_graduation_and_traffic_police_photos(self):
        title = "De amenazas con pistola a destrozos: ¿qué pasó entre repartidores y vecinos en CDMX?"
        article = self.make_article(title, category="Seguridad", source="El Economista")
        graduation = self.photo("commons_75245989")
        traffic_control = self.photo("commons_48010489")
        patrol = self.photo("archivo_seguridad_002")
        self.assertIsNotNone(graduation)
        self.assertIsNotNone(traffic_control)
        self.assertIsNotNone(patrol)
        self.assertIn("Graduación", graduation["topic"])
        self.assertIn("semáforo", traffic_control["topic"])
        self.assertIn("Patrulla vecinal", patrol["topic"])

        self.assertLess(_photo_score(article, graduation), 0)
        self.assertLess(_photo_score(article, traffic_control), 0)
        self.assertGreaterEqual(_photo_score(article, patrol), 0)
        with patch.object(photos, "_pool", return_value=[graduation, traffic_control, patrol]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "archivo_seguridad_002")
        self.assertTrue(article["photo"]["author"])
        self.assertTrue(article["photo"]["license"])
        self.assertTrue(article["photo"]["licenseUrl"])


    def test_vuelca_automovil_rejects_madero_landmark_and_uses_traffic_context(self):
        title = "Vuelca Automóvil y Deja una Persona Herida en la Colonia Vicente Guerrero, Iztapalapa"
        article = self.make_article(title, category="Movilidad", source="N+")
        madero = self.photo("commons_82750992")
        traffic = self.photo("contexto_trafico_eje_central")
        self.assertEqual(article["borough"], "Iztapalapa")
        self.assertIsNotNone(madero)
        self.assertIsNotNone(traffic)
        self.assertIn("Avenida Francisco I. Madero", madero["topic"])
        self.assertIn("Tráfico vehicular", traffic["topic"])

        self.assertLess(_photo_score(article, madero), 0)
        self.assertGreaterEqual(_photo_score(article, traffic), 0)
        with patch.object(photos, "_pool", return_value=[madero, traffic]):
            assign_photos([article])
        self.assertEqual(article["photo"]["id"], "contexto_trafico_eje_central")
        self.assertTrue(article["photo"]["author"])
        self.assertTrue(article["photo"]["license"])
        self.assertTrue(article["photo"]["licenseUrl"])



if __name__ == "__main__":
    unittest.main()
