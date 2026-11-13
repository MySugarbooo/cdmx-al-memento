"""Garantiza noticias leíbles aquí, fotografías únicas y atribución responsable."""
import json
import unittest
from pathlib import Path
from scripts.notas_locales import assign_photos, local_link, summarize, is_sensitive_media, RADIO_FORMULA_CASA_ECOLOGICA_SOURCE_URL
from scripts.build_article_seo import article_id, render
from update_news import category_by_headline, standardize, photo_needs_refresh, CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL

ROOT=Path(__file__).resolve().parents[1]

class LocalNewsTests(unittest.TestCase):
    def make(self,i,category):
        return {"title":f"El Metro de CDMX reporta avance de la línea {i} de transporte",
                "url":"https://news.google.com/rss/articles/sample"+str(i),
                "source":"Periódico de prueba","date":"2026-10-13",
                "category":category,"borough":""}

    def test_huixtla_migrant_caravan_is_external_and_rejects_wheelchair_basketball_photo(self):
        article = {
            "title": "Caravana migrante ‘Dios con nosotros’ llega a Huixtla: Más de 500 personas avanzan por Chiapas rumbo a CDMX",
            "url": "https://news.google.com/rss/articles/migrant-huixtla-regression",
            "source": "El Financiero",
            "date": "2026-11-12",
            "published_at": "2026-11-12T21:20:44Z",
            "category": "CDMX",
            "borough": "",
            "photo": {
                "id": "contexto_baloncesto_silla_ruedas",
                "kind": "representativa",
                "url": "https://upload.wikimedia.org/wikipedia/commons/e/e0/2010_World_Wheelchair_Basketball_Championship_Mexico_and_UK.jpg",
                "category": "CDMX",
                "topic": "Partido de baloncesto en silla de ruedas entre México y Gran Bretaña; Campeonato Mundial 2010, Birmingham, Reino Unido",
                "keywords": ["deporte adaptado", "baloncesto en silla de ruedas", "México"],
                "author": "2010 World Wheelchair Basketball Championship",
                "license": "CC BY 2.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/2.0/",
                "source": "https://commons.wikimedia.org/wiki/File:2010_World_Wheelchair_Basketball_Championship_Mexico_and_UK.jpg",
            },
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["location"], "Huixtla, Chiapas (fuera de CDMX)")
        self.assertEqual(result["borough"], "")
        self.assertEqual(result["category"], "CDMX")
        self.assertIn("Huixtla, Chiapas", result["brief"]["lead"])
        self.assertIn("destino del recorrido", result["brief"]["lead"])
        self.assertIn("fuera de CDMX", result["brief"]["context"])
        assign_photos([result])
        self.assertNotIn("photo", result)
        rendered = render(result, article_id(result))
        self.assertNotIn('<figure class="article-photo">', rendered)

    def test_el_morenito_fatal_trailer_crash_is_mobility_and_has_no_context_photo(self):
        article = {
            "title": "\"El Morenito\" muere tras ser arrastrado varios metros por un tráiler, en Venustiano Carranza",
            "url": "https://news.google.com/rss/articles/el-morenito-trailer-regression",
            "source": "El Gráfico",
            "date": "2026-11-12",
            "published_at": "2026-11-12T15:24:00Z",
            "category": "CDMX",
            "borough": "Venustiano Carranza",
            "photo": {
                "id": "commons_old_cdmx_streets",
                "kind": "representativa",
                "url": "/assets/fotos/archivo_cdmx_001.jpg",
                "category": "CDMX",
                "topic": "Ciudad de México, calles y plazas 1986 07",
                "author": "Autor de prueba",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Ciudad_de_Mexico_calles_y_plazas.jpg",
            },
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Movilidad")
        self.assertEqual(result["borough"], "Venustiano Carranza")
        self.assertTrue(is_sensitive_media(result))
        self.assertIn("avenida del Taller", result["brief"]["lead"])
        self.assertIn("Lorenzo Boturini", result["brief"]["lead"])
        self.assertEqual(
            result["source_url"],
            "https://www.elgrafico.mx/la-roja/2026/11/12/el-morenito-muere-tras-ser-arrastrado-varios-metros-por-un-trailer-en-venustiano-carranza/?outputType=amp",
        )
        assign_photos([result])
        self.assertNotIn("photo", result)
        rendered = render(result, article_id(result))
        self.assertIn("Sin fotografía verificada del hecho", rendered)
        self.assertNotIn('<figure class="article-photo">', rendered)

    def test_security_mobility_and_intercity_train_categories_are_specific(self):
        cases = (
            ("Caen tres secuestradores en la alcaldía Venustiano Carranza", "CDMX", "Seguridad"),
            ("Policías de la CDMX rescataron a un hombre secuestrado en La Merced", "Metro", "Seguridad"),
            ("Caen 35.6% los delitos contra empresas y comercios en CDMX, presume Pablo Vázquez", "CDMX", "Seguridad"),
            ("\"El Morenito\" muere tras ser arrastrado varios metros por un tráiler, en Venustiano Carranza", "CDMX", "Movilidad"),
            ("Llega a México el primer tren de la ruta CDMX-Pachuca; tendrá capacidad para 893 pasajeros", "CDMX", "Movilidad"),
        )
        for title, feed_category, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(category_by_headline(title, feed_category), expected)

    def test_coyotepec_highway_crash_is_external_and_has_no_unrelated_photo(self):
        article = {
            "title": "Fuerte Accidente de 3 Autobuses y Tractocamión en la México-Querétaro: Cierran Hacia CDMX",
            "url": "https://news.google.com/rss/articles/CBMi5AFBVV95cUxPaHl6T3o0cHRKSWoxRDh3ZXNDNmtjNE5PWWtxWjFaX2hVczAzazVJMFlodzR1elFyeGtoQVhMUEo0a29FbkRSTFF3dDhCZFBQa3U0SkNiMmR2SEthZTEzaWxTMFktVTlBZ1BiUUpNdDBMNEctVm1LcElyWjlKQjdrZFEzc1JHdXU1LUZFdmdzRkZqbDAwZ1IxbFg2bGVieUN6UVdpd1JRODhuRHBMUTJfR3FKSzk4eEZyQUNWY1lkNWpJZWNHZXN6VEREUXNpT3ExNjQyaGk2aG5oaWZGMnJNQWNqQ2U?oc=5",
            "source": "N+",
            "date": "2026-11-12",
            "published_at": "2026-11-12T15:41:49Z",
            "category": "Movilidad",
            "borough": "",
            "photo": {
                "id": "commons_155112880",
                "kind": "representativa",
                "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/44/Estaci%C3%B3n_Moctezuma_de_la_L%C3%ADnea_12_del_Troleb%C3%BAs_de_la_Ciudad_de_M%C3%A9xico.jpg/960px-Estaci%C3%B3n_Moctezuma_de_la_L%C3%ADnea_12_del_Troleb%C3%BAs_de_la_Ciudad_de_M%C3%A9xico.jpg",
                "category": "Movilidad",
                "topic": "Estación Moctezuma de la Línea 12 del Trolebús de la Ciudad de México",
                "author": "ProtoplasmaKid",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Estaci%C3%B3n_Moctezuma_de_la_L%C3%ADnea_12_del_Troleb%C3%BAs_de_la_Ciudad_de_M%C3%A9xico.jpg"
            }
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["location"], "Coyotepec, Estado de México (fuera de CDMX)")
        self.assertEqual(result["borough"], "")
        self.assertTrue(is_sensitive_media(result))
        self.assertIn("Coyotepec", result["brief"]["lead"])
        self.assertIn("27 personas lesionadas", result["brief"]["lead"])
        self.assertNotIn("en la capital", result["brief"]["lead"].casefold())
        self.assertIn("fuera de la capital", result["brief"]["context"])
        assign_photos([result])
        self.assertNotIn("photo", result)
        self.assertTrue(result["sensitive_media"])

    def test_san_juan_del_rio_autopista57_is_mobility_and_has_no_police_photo(self):
        article = {
            "title": "Toma precauciones si viajas a la CDMX, autopista 57 está detenida",
            "url": "https://news.google.com/rss/articles/CBMiwAFBVV95cUxPUW96UDJITEFHWWhYTThWclZlQmh1cGcyUW5lTngtRzNTcmJ5M0pjaUZRN1RHbDZOZmRVblQ4NjNfN09PWXpHSHFOX3RRcTBvOE5PZEtxU2NfVXFqWDBqb0d2anpFa2dIb1lUdm9tazFOSGJyWElIRFRnbkQzamdXdUc3YW5uMjd3dkNxVFRRNDVYTDBfV291VDJZbzU5TTk4UnF3aVhwRGR0TkRPSmhNdC1QeHhoRTFmdnlpdHQ3clk?oc=5",
            "source": "El Sol de México",
            "date": "2026-11-12",
            "published_at": "2026-11-12T17:19:57Z",
            "category": "CDMX",
            "borough": "",
            "photo": {
                "id": "archivo_seguridad_005",
                "kind": "representativa",
                "url": "/assets/fotos/archivo_seguridad_005.jpg",
                "category": "Seguridad",
                "topic": "Jeep policia cdmx",
                "author": "Gobierno de la Ciudad de México",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Jeep_policia_cdmx.jpg",
            },
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Movilidad")
        self.assertEqual(result["location"], "San Juan del Río, Querétaro (fuera de CDMX)")
        self.assertEqual(result["borough"], "")
        self.assertEqual(result["source"], "El Sol de San Juan del Río")
        self.assertEqual(result["source_url"], "https://oem.com.mx/elsoldesanjuandelrio/policiaca/toma-precauciones-si-viajas-a-la-cdmx-autopista-57-esta-detenida-33095499")
        self.assertEqual(result["local_url"], "/noticias/?id=b37ba45fa2fa424b73bd&mes=2026-11")
        self.assertIn("Mario Luna / Diario de Querétaro", result["brief"]["lead"])
        self.assertIn("El Sol de San Juan del Río", result["brief"]["method"])
        self.assertIn("fuera de la Ciudad de México", result["brief"]["context"])
        self.assertNotIn("kilómetros", result["brief"]["lead"].casefold())
        self.assertTrue(is_sensitive_media(result))
        assign_photos([result])
        self.assertNotIn("photo", result)
        self.assertTrue(result["sensitive_media"])
        rendered = render(result, article_id(result))
        self.assertIn('href="https://oem.com.mx/elsoldesanjuandelrio/policiaca/toma-precauciones-si-viajas-a-la-cdmx-autopista-57-esta-detenida-33095499"', rendered)
        self.assertIn("Fuente: El Sol de San Juan del Río", rendered)
        self.assertNotIn("Fuente: El Sol de México", rendered)

    def test_sensitive_animal_abuse_titles_never_receive_context_photos(self):
        titles = (
            "Detienen a presunto abusador sexual de animales en situación de calle en CDMX",
            "Detienen a otro presunto maltratador de animales en Tlalpan",
            "Detienen a acusado de maltrato animal en Tlalpan",
            "Detienen a hombre acusado de maltratar perros en CDMX tras recibir golpiza de vecinos en Tlalpan",
        )
        for index, title in enumerate(titles):
            with self.subTest(title=title):
                article = {
                    "title": title,
                    "url": f"https://news.google.com/rss/articles/animal-sensitive-{index}",
                    "source": "Medio de prueba",
                    "date": "2026-11-12",
                    "category": "CDMX",
                    "borough": "",
                    "photo": {
                        "id": f"animal-context-{index}",
                        "kind": "representativa",
                        "url": "/assets/fotos/archivo_seguridad_005.jpg",
                        "category": "Seguridad",
                        "topic": "Animales Bosque de Tlalpan",
                        "author": "Autor de prueba",
                        "license": "CC BY-SA 4.0",
                        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                        "source": "https://commons.wikimedia.org/wiki/File:Animales_Bosque_de_Tlalpan.jpg",
                    },
                }
                result = standardize(article)
                self.assertIsNotNone(result)
                self.assertTrue(is_sensitive_media(result))
                assign_photos([result])
                self.assertNotIn("photo", result)
                self.assertTrue(result["sensitive_media"])
                rendered = render(result, article_id(result))
                self.assertIn("Sin fotografía verificada del hecho", rendered)
                self.assertNotIn('<figure class="article-photo">', rendered)

    def test_crime_headlines_override_inherited_metro_and_cdmx_categories(self):
        cases = (
            (
                "Detienen a presunto abusador sexual de animales en situación de calle en CDMX",
                "Metro",
            ),
            ("Detienen a otro presunto maltratador de animales en Tlalpan", "CDMX"),
            ("Detienen a acusado de maltrato animal en Tlalpan", "CDMX"),
            (
                "Pasajeros denuncian robos durante viajes solicitados por aplicación en CDMX",
                "Metro",
            ),
            (
                "Policías de la CDMX rescataron a un hombre secuestrado en Venustiano Carranza",
                "Metro",
            ),
        )
        for title, feed_category in cases:
            with self.subTest(title=title):
                self.assertEqual(
                    category_by_headline(title, feed_category, "Infobae"),
                    "Seguridad",
                )

    def test_imagen_tlalpan_dog_rescue_is_security_and_not_a_detention(self):
        article = {
            "title": "Vecinos rescatan a perrita de presunto abuso sexual por un hombre en Tlalpan, CDMX",
            "url": "https://news.google.com/rss/articles/CBMi2AFBVV95cUxNUEQ2cV9wblUya0JiMGd0ZWotSk4xakZoa3ZzUHJkYlgwcVpJbzFQZkI0R29TVURoTF9WM2VSN2xqTng4RlhCV3dsaEpPeDg1ZWsyc0NNcnh4R29HSHF3Sm5FcnJiUFZCYkhiZklGMTlSb1VoSGFEVVNDLTU0ZEp2UjUyamNjMU1TTlk1ZHBGZnVHMkFCck1mVDhRTmZSbG03eS1mNXlmOFcxRFNVQU5tVW9XYmVLc2NURUdKYlJnVmFzb2xkUzZuZ3loN0xkZl94QVJMb3BzS3U?oc=5",
            "source": "Imagen Televisión",
            "date": "2026-11-12",
            "published_at": "2026-11-12T21:07:53Z",
            "category": "CDMX",
            "borough": "Tlalpan",
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Seguridad")
        self.assertEqual(result["borough"], "Tlalpan")
        self.assertIn("Tlalpan", result["location"])
        self.assertIn("vecinos rescataron a una perrita", result["brief"]["lead"])
        self.assertIn("no informa de una detención", result["brief"]["lead"])
        self.assertNotIn("detuvo a un hombre", result["brief"]["lead"])
        self.assertTrue(is_sensitive_media(result))
        assign_photos([result])
        self.assertNotIn("photo", result)
        rendered = render(result, article_id(result))
        self.assertIn("Sin fotografía verificada del hecho", rendered)
        self.assertNotIn('<figure class="article-photo">', rendered)

    def test_infobae_animal_case_uses_confirmed_tlalpan_location_and_source(self):
        article = {
            "title": "Detienen a presunto abusador sexual de animales en situación de calle en CDMX: activistas piden que las investigaciones lleguen a fondo",
            "url": "https://news.google.com/rss/articles/CBMiiAJBVV95cUxPSXVkQ1ZPWkZMSDVzVml6NXNfTGFpVnFCaVFWc0dBMGEwaWFVSjJ0SHlUc1VTemtjeXUzYkJiQWd2eEw3a2ZIMEFWay1hdGVCaFhPU3pkYzNJb3BMemNlZkhUSVlHWUJyRUJRNkZ2ZGRESVBsZVNCREdNSG5VVUZ5RjBZZXlqMjQwSEs0ZjBZdmFDQml2YXctNDE1NkJlcm1DWG9GY1FVZWszaXVRVVRxeS1hYWFSanBEVkZ3SDRDWUljY1F1NU93RjZoTlZaU2VJdUVacDItc0FyNF9halpOTFgyRm1HNnlrNlB4NEtybmttWGZ0RnZUVkstZkM3ZEYxVlliakNOX1bSAaMCQVVfeXFMTWViNFhLekl3bHBQbmxGYmlQTFpVcGJCOXdDMy1wdl8wNlJnTjFXTXJtRWhwR0NWb2k1UDRmWUhxa1VGMm5HcjNmZjlKZUw3YUtPZFJ1Vmswd3Uwdk0tMkxKbGxNZ0t1b3VqX2N0VGdlMU1RNlZYQXhrRTJPaE5sTUVpTFBsLXAwZ2pUVkl5YmxZS3VwbDhGeTE3OUFrWDRtc3I0aGptSWJhbk14d0ZFZjJTVHVxY3Z4TWZnUXJHMzFEN3Q3VWxCeHBjUFNmVmkxaFdoaWlGWXdmSFk4bFNzdlpjQ1AzZW92T3FncGVDUVhEVkFaeVloUEV0NndRalNqWXNZMWRNWlEtcUNFTDRQRWxEbjlFSjlwaDZsZm1kQnBJTTBF?oc=5",
            "source": "Infobae",
            "date": "2026-11-12",
            "published_at": "2026-11-12T19:57:00Z",
            "category": "Metro",
            "borough": "",
            "photo": {
                "id": "animal-context-infobae",
                "kind": "representativa",
                "url": "/assets/fotos/archivo_seguridad_005.jpg",
                "category": "Alcaldías",
                "topic": "Animales Bosque de Tlalpan",
                "author": "Autor de prueba",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Animales_Bosque_de_Tlalpan.jpg",
            },
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Seguridad")
        self.assertEqual(result["borough"], "Tlalpan")
        self.assertIn("Tlalpan", result["location"])
        self.assertEqual(result["source_url"], "https://www.infobae.com/mexico/2026/11/12/detienen-a-presunto-abusador-sexual-de-animales-en-situacion-de-calle-en-cdmx-activistas-piden-que-las-investigaciones-lleguen-a-fondo/")
        self.assertEqual(result["local_url"], "/noticias/?id=086a68086514ac4b9e44&mes=2026-11")
        self.assertIn("Pedregal de San Nicolás", result["brief"]["lead"])
        self.assertTrue(is_sensitive_media(result))
        assign_photos([result])
        self.assertNotIn("photo", result)
        rendered = render(result, article_id(result))
        self.assertIn('href="https://www.infobae.com/mexico/2026/11/12/detienen-a-presunto-abusador-sexual-de-animales-en-situacion-de-calle-en-cdmx-activistas-piden-que-las-investigaciones-lleguen-a-fondo/"', rendered)
        self.assertIn("Fuente: Infobae", rendered)
        self.assertIn("Sin fotografía verificada del hecho", rendered)

    def test_la_prensa_animal_case_corrects_source_and_preserves_article_key(self):
        article = {
            "title": "Detienen a otro presunto maltratador de animales en Tlalpan",
            "url": "https://news.google.com/rss/articles/CBMiqwFBVV95cUxQazczY2xhczU2emVhMzZobG9lNGNYWm0zcHJWR19GLUJTT2s4UnRVd0lFemJ4OV9WLWdtcTNKcms1SV9DZ0VZZjlCdUhLSGdFYjN3elBRX3dGcktMRmpzckdUbnRGdXFkUGlqUURPeTVKN1p2SDU0X1JtazhwMWFNMVRtNUE5QkNUZHBKSkRDdVJYX2xTNlFDdXN0clRsMjBzMHlONGVLZmoxeVk?oc=5",
            "source": "El Sol de México",
            "date": "2026-11-12",
            "published_at": "2026-11-12T17:21:11Z",
            "category": "CDMX",
            "borough": "Tlalpan",
            "photo": {
                "id": "animal-context-la-prensa",
                "kind": "representativa",
                "url": "/assets/fotos/archivo_seguridad_005.jpg",
                "category": "Alcaldías",
                "topic": "Animales Bosque de Tlalpan",
                "author": "Autor de prueba",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Animales_Bosque_de_Tlalpan.jpg",
            },
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Seguridad")
        self.assertEqual(result["source"], "La Prensa")
        self.assertEqual(result["source_url"], "https://oem.com.mx/la-prensa/policiaca/detienen-a-otro-presunto-maltratador-de-animales-en-tlalpan-33095643")
        self.assertEqual(result["local_url"], "/noticias/?id=00c19362c5f0468f82b1&mes=2026-11")
        self.assertIn("Ministerio Público", result["brief"]["lead"])
        self.assertTrue(is_sensitive_media(result))
        assign_photos([result])
        self.assertNotIn("photo", result)
        rendered = render(result, article_id(result))
        self.assertIn('href="https://oem.com.mx/la-prensa/policiaca/detienen-a-otro-presunto-maltratador-de-animales-en-tlalpan-33095643"', rendered)
        self.assertIn("Fuente: La Prensa", rendered)
        self.assertIn("Sin fotografía verificada del hecho", rendered)

    def test_distinct_real_photos_for_sixty_news(self):
        groups=["CDMX","Metro","Seguridad","Movilidad","Cultura","Gobierno"]
        items=[self.make(i,groups[i%len(groups)]) for i in range(60)]
        stats=assign_photos(items)
        self.assertGreaterEqual(stats["available"],60)
        self.assertEqual(stats["assigned"],60)
        self.assertEqual(stats["unique"],60)
        for item in items:
            photo=item["photo"]
            self.assertTrue(photo["author"])
            self.assertTrue(photo["license"])
            self.assertIn("https://commons.wikimedia.org/wiki/File:",photo["source"])
            self.assertTrue(photo["url"].startswith(("/assets/","https://thumb.wikimedia.org","https://upload.wikimedia.org")))

    def test_local_link_based_on_original_url(self):
        article=self.make(1,"Metro")
        link=local_link(article)
        self.assertRegex(link,r"^/noticias/\?id=[a-f0-9]{20}&mes=2026-10$")
        self.assertEqual(link,local_link(article))
        self.assertNotEqual(link,local_link(self.make(2,"Metro")))

    def test_sources_are_named_and_facts_not_invented(self):
        article=self.make(1,"Metro")
        brief=summarize(article)
        self.assertIn("Periódico de prueba",brief["lead"])
        self.assertIn("Metro",brief["lead"])
        self.assertIn("deben comprobarse",brief["pending"])
        self.assertIn("titular",brief["method"])
        self.assertNotIn("entrevistamos",brief["lead"])

    def test_tv_azteca_liveblog_does_not_misattribute_google_news_headline(self):
        article = {
            "title": "Explosión de gas en local de Azcapotzalco: Baches, socavones y otras afectaciones en CDMX hoy",
            "url": "https://news.google.com/rss/articles/example-tvazteca-liveblog",
            "source": "TV Azteca",
            "date": "2026-11-11",
            "category": "Seguridad",
            "borough": "Azcapotzalco",
        }
        brief = summarize(article)
        self.assertIn("Google News muestra el encabezado", brief["lead"])
        self.assertIn("Accidentes, afectaciones y percances en CDMX | EN VIVO", brief["lead"])
        self.assertIn("actualización del 11 de noviembre de 2026 a las 20:17", brief["lead"])
        self.assertIn("explosión por acumulación de gas", brief["lead"])
        self.assertNotIn("el titular publicado es", brief["lead"].casefold())
        self.assertIn("otros percances viales", brief["context"])
        self.assertIn("no constituye verificación independiente", brief["method"])

    def test_fatal_microbus_headline_is_not_described_as_unknown_outcome(self):
        article = {
            "title": "Microbús Atropella y Mata a un Hombre en Situación de Calle en Azcapotzalco",
            "url": "https://news.google.com/rss/articles/example-fatal-microbus",
            "source": "N+", "date": "2026-11-01",
            "category": "Movilidad", "borough": "Azcapotzalco",
        }
        lead = summarize(article)["lead"]
        self.assertIn("un microbús", lead)
        self.assertIn("El propio titular señala un fallecimiento", lead)
        self.assertNotIn("no permite determinar", lead)
        article["title"] = "Choque entre dos vehículos en Azcapotzalco"
        self.assertIn("no permite determinar", summarize(article)["lead"])

    def test_metrobús_only_headline_is_not_summarized_as_metro(self):
        article = {
            "title": "Estado de las estaciones del Metrobús en esta última hora del 11 de noviembre",
            "url": "https://news.google.com/rss/articles/example-metrobus-only",
            "source": "Infobae", "date": "2026-11-11",
            "category": "Movilidad", "borough": "",
        }
        lead = summarize(article)["lead"]
        self.assertIn("servicio del Metrobús de Ciudad de México", lead)
        self.assertNotIn("Metro de Ciudad de México", lead)

    def test_combined_transit_headline_names_each_service(self):
        article = {
            "title": "¿Hay atrasos en Metro CDMX, Metrobús y Tren Suburbano? Estado del servicio hoy",
            "url": "https://news.google.com/rss/articles/example-multiple-transit",
            "source": "Eje Central", "date": "2026-11-11",
            "category": "Movilidad", "borough": "",
        }
        lead = summarize(article)["lead"]
        self.assertIn("Metro, Metrobús y Tren Suburbano", lead)
        self.assertNotIn("solo", lead.casefold())

    def test_capital_government_plan_headline_is_classified_as_government(self):
        title = ("EN UN HECHO HISTÓRICO, APRUEBA GOBIERNO DE LA CIUDAD DE MÉXICO "
                 "EL PROYECTO DEL PLAN GENERAL DE DESARROLLO 2025-2045 "
                 "Y LO ENVÍA AL CONGRESO LOCAL.")
        self.assertEqual(category_by_headline(title, "CDMX"), "Gobierno")
        # Una regla general de Gobierno no debe ocultar una detención específica.
        security_title = "Detienen a un hombre tras operativo del Gobierno de la Ciudad de México"
        self.assertEqual(category_by_headline(security_title, "CDMX"), "Seguridad")

    def test_radio_formula_casa_ecologica_is_environmental_and_uses_direct_source(self):
        article = {
            "title": "Calentadores solares y captación de lluvia: el plan de CDMX para ahorrar en casa",
            "url": "https://news.google.com/rss/articles/radio-formula-casa-ecologica",
            "source": "Radio Fórmula",
            "date": "2026-11-12",
            "published_at": "2026-11-12T22:38:28Z",
            "category": "Gobierno",
            "borough": "",
        }
        self.assertEqual(
            category_by_headline(article["title"], "Gobierno", "Radio Fórmula"),
            "Medio Ambiente",
        )
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Medio Ambiente")
        self.assertEqual(result["borough"], "Álvaro Obregón")
        self.assertIn("Santa Rosa Xochiac", result["location"])
        self.assertEqual(result["source_url"], RADIO_FORMULA_CASA_ECOLOGICA_SOURCE_URL)
        self.assertIn("19 mil viviendas", result["brief"]["lead"])
        self.assertIn("356 millones de pesos", result["brief"]["lead"])
        self.assertIn("10 mil hogares", result["brief"]["lead"])
        self.assertNotIn("pronóstico", result["brief"]["lead"].casefold())
        self.assertIn("La Jornada", result["brief"]["method"])
        self.assertIn("radioformula.com.mx", result["brief"]["method"])

    def test_capital_cdmx_care_budget_summary_and_direct_source_are_accurate(self):
        article = {
            "title": "Presupuesto de cuidados 2027: ¿cuánto llegará a la CDMX y cómo se puede comprobar?",
            "url": "https://news.google.com/rss/articles/CBMinAFBVV95cUxOTDJNRVpCdi1nMjVIQVJTb21HLVBXS3dLN19neF9vcVI5RE9ua3ktTW5HUURqaVlKRTRIeHZjVFlCbkFqQng2WnZ1VHFvNDhmQ0lqcDFpa255aExqVDUwLW95MHBYd2hVR0RFdHFsRUpoVUZFRkY1blZLVWdzeU56RW9PcUtBUnVKQnRUNUZMamxGdVpPNXRFbndrYlY?oc=5",
            "source": "Capital CDMX",
            "date": "2026-11-12",
            "published_at": "2026-11-13T04:30:03Z",
            "category": "CDMX",
            "borough": "",
        }
        self.assertEqual(category_by_headline(article["title"], "CDMX", "Capital CDMX"), "Gobierno")
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Gobierno")
        self.assertEqual(result["source_url"], CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL)
        lead = result["brief"]["lead"]
        self.assertIn("475,959.7 millones de pesos", lead)
        self.assertIn("no permite determinar cuánto corresponde a la Ciudad de México", lead)
        self.assertNotIn("detención", lead.casefold())
        self.assertNotIn("conducta delictiva", lead.casefold())
        self.assertIn("múltiples programas", result["brief"]["context"])
        self.assertIn(CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL, result["brief"]["method"])
        article_html = render(result, article_id(result))
        self.assertIn(CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL, article_html)

    def test_ssc_buen_fin_operativo_is_security_and_uses_official_facts(self):
        title = ("2999: La SSC implementará un operativo de seguridad, vigilancia y vialidad "
                 "por el “Buen Fin 2026”, con la participación más de 16 mil policías en la ciudad de México")
        source = "Secretaría de Seguridad Ciudadana de la CDMX"
        self.assertEqual(category_by_headline(title, "Metro", source), "Seguridad")
        article = {
            "title": title,
            "url": "https://news.google.com/rss/articles/example-ssc-buen-fin",
            "source": source,
            "date": "2026-11-11",
            "category": "Seguridad",
            "borough": "",
        }
        brief = summarize(article)
        self.assertIn("16,300 policías", brief["lead"])
        self.assertIn("16 alcaldías", brief["lead"])
        self.assertIn("13 al 17 de noviembre de 2026", brief["lead"])
        self.assertIn("comunicado oficial de la SSC", brief["method"])
        self.assertNotIn("clasifica como Metro", brief["lead"])
        self.assertIn("ajuste del operativo", brief["pending"])
        self.assertNotIn("El índice RSS", brief["pending"])
        self.assertIn("seguridad", brief["context"].casefold())

    def test_reader_is_internal_and_signed(self):
        html=(ROOT/"noticias/index.html").read_text(encoding="utf-8")
        js=(ROOT/"assets/noticias-locales.js").read_text(encoding="utf-8")
        self.assertIn("Por Amau Kisumi",html)
        self.assertIn('id="local-story-photo"',html)
        self.assertIn("article.brief?.lead",js)
        self.assertIn("function selectedPhoto(x)",js)
        self.assertIn("const rights=selectedPhoto(article)||{}",js)
        self.assertIn("safeExternal(rights.source)",js)
        self.assertIn("origin.href=rights.source",js)
        self.assertIn("Consultar la fuente original",js)
        self.assertIn('title.textContent=article.title',js)
        self.assertIn("id='+id+'&mes='+month",js)
        self.assertIn("section.append(source)",js)

    def test_home_and_portals_open_local_pages(self):
        home=(ROOT/"app.js").read_text(encoding="utf-8")
        portal=(ROOT/"assets/portal.js").read_text(encoding="utf-8")
        archive=(ROOT/"assets/hemeroteca.js").read_text(encoding="utf-8")
        updater=(ROOT/"update_news.py").read_text(encoding="utf-8")
        self.assertIn("a.local_url||'/noticias/'",home)
        self.assertIn("Leer resumen de Amau Kisumi",home)
        self.assertIn("a.local_url||'/noticias/'",portal)
        self.assertIn("article.local_url||'/noticias/'",archive)
        self.assertIn("assign_photos(items[:60])",updater)
        self.assertIn('"local_url"',updater)
        self.assertIn("summarize(result)",updater)

    def test_recent_operativo_and_government_headlines_are_classified_correctly(self):
        cases = (
            ("Tabe en Miguel Hidalgo: cinco años de cambio", "Seguridad", "Gobierno"),
            ("Hemos cambiado y mejorado el rostro de Coyoacán: Giovani Gutierrez", "CDMX", "Gobierno"),
            ("Contraloría de la Cdmx detecta observaciones por 839 mdp en fiscalización", "CDMX", "Gobierno"),
            ("¿Qué pasó en Plaza Meave hoy? Autoridades de CDMX realizan operativo", "CDMX", "Seguridad"),
            ("Decomisan 3 toneladas de autopartes en Alcaldía Cuauhtémoc", "CDMX", "Seguridad"),
        )
        for title, feed_category, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(category_by_headline(title, feed_category), expected)


    def test_plural_armed_attacks_against_delivery_riders_are_security(self):
        title = "Agrupación de repartidores de aplicación documenta al menos 20 ataques armados en CDMX"
        self.assertEqual(category_by_headline(title, "CDMX", "La Jornada"), "Seguridad")

    def test_pipes_before_paving_proposal_uses_drainage_or_public_works_photo(self):
        article = {
            "title": "Diputada Miriam Saldaña propone revisar las tuberías antes de pavimentar en la CDMX",
            "url": "https://news.google.com/rss/articles/example-pipes-before-paving",
            "source": "Partido del Trabajo",
            "date": "2026-11-12",
            "category": "CDMX",
            "borough": "",
        }
        stats = assign_photos([article])
        self.assertEqual(stats["assigned"], 1)
        photo = article["photo"]
        context = " ".join([photo.get("topic", ""), *photo.get("keywords", [])]).casefold()
        self.assertRegex(
            context,
            r"\b(?:tuberias?|drenaje|pavimentacion|pavimento|asfalto|alcantarillas?|red hidraulica|infraestructura hidraulica|obra vial|desazolve|supervision de obras)\b",
        )
        self.assertNotRegex(context, r"\bcarnavales?\b")
        self.assertEqual(photo["kind"], "representativa")
        self.assertEqual(photo["category"], "Servicios")
        self.assertTrue(photo["author"])
        self.assertTrue(photo["license"])
        self.assertTrue(photo["licenseUrl"])
        self.assertTrue(photo["source"].startswith("https://commons.wikimedia.org/wiki/File:"))

    def test_mauricio_tabe_report_has_attributed_summary_and_licensed_venue_photo(self):
        article = standardize({
            "title": "Mauricio Tabe presenta su Quinto Informe de Gobierno en Miguel Hidalgo",
            "url": "https://news.google.com/rss/articles/CBMisgFBVV95cUxNdXhhemVjeGhBRjlvT25FUGl5TlpXSGZlTmFHNk9Ga21zUjA5YTQ0TTBNamUxWWg4czY1NUM3MDg2RFhVUDUwVmNRTy1zQUtEbmd3TnJwYkR3aUpRdjd0czlRek9mY3ZjbGh6bmpVdHFieGZZcHFFUk5zekZZQnNNYVVEQ0ZTMGJQdkt3a1EzQURLS01Sb1FYV1A0NC1iVnFMcmVCeVV5SG1kdDRTNGpRZUp3?oc=5",
            "source": "sdpnoticias",
            "date": "2026-11-12",
            "published_at": "2026-11-12T18:35:37Z",
            "category": "Gobierno",
        })
        self.assertIsNotNone(article)
        self.assertEqual(article["borough"], "Miguel Hidalgo")
        self.assertEqual(
            article["local_url"],
            "/noticias/?id=842f4c3306f51b3ab9fc&mes=2026-11",
        )
        self.assertEqual(article["source_url"], "https://www.sdpnoticias.com/estados/cdmx/mauricio-tabe-presenta-su-quinto-informe-de-gobierno-en-miguel-hidalgo/")
        self.assertIn("Blindar MH", article["brief"]["lead"])
        self.assertIn("1,770 cámaras", article["brief"]["lead"])
        self.assertIn("150 calles", article["brief"]["lead"])
        self.assertIn("no se verifican de forma independiente", article["brief"]["pending"])
        self.assertIn("La Prensa", article["brief"]["method"])

        article["photo"] = {
            "id": "commons_93188323",
            "kind": "representativa",
            "category": "CDMX",
            "topic": "Registro de agua. Primera Sección del Bosque de Chapultepec - 4",
            "keywords": ["Medio Ambiente"],
            "author": "ProtoplasmaKid",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
            "source": "https://commons.wikimedia.org/wiki/File:Registro_de_agua._Primera_Secci%C3%B3n_del_Bosque_de_Chapultepec_-_4.jpg",
            "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fd/Registro_de_agua._Primera_Secci%C3%B3n_del_Bosque_de_Chapultepec_-_4.jpg/960px-Registro_de_agua._Primera_Secci%C3%B3n_del_Bosque_de_Chapultepec_-_4.jpg",
        }
        self.assertTrue(photo_needs_refresh(article))
        assign_photos([article])
        photo = article["photo"]
        self.assertFalse(photo_needs_refresh(article))
        self.assertEqual(photo["id"], "contexto_teatro_angela_peralta")
        self.assertEqual(photo["author"], "Secretaría de Cultura Ciudad de México")
        self.assertEqual(photo["license"], "CC BY 2.0")
        self.assertIn("fotografía de 2019", photo["topic"])
        catalog = json.loads((ROOT / "assets/fotos/catalogo-editorial-1100.json").read_text(encoding="utf-8"))
        catalog_photo = next(p for p in catalog["photos"] if p["id"] == "contexto_teatro_angela_peralta")
        self.assertEqual(catalog_photo["uploaded_at"], "2020-01-13")
        self.assertEqual(catalog_photo["captured_at"], "2019-02-10")
        self.assertEqual(catalog_photo["context"], "Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.")

        rendered = render(article, article_id(article))
        self.assertIn('href="https://www.sdpnoticias.com/estados/cdmx/mauricio-tabe-presenta-su-quinto-informe-de-gobierno-en-miguel-hidalgo/"', rendered)
        self.assertIn("Secretaría de Cultura Ciudad de México", rendered)
        self.assertIn("CC BY 2.0", rendered)
        self.assertIn("Imagen representativa; no corresponde necesariamente al hecho.", rendered)



    def test_infobae_coyotepec_school_bus_crash_is_external_and_photo_free(self):
        article = {
            "title": "Alumnos viajaban de paseo a la CDMX y fueron impactados por tráiler: difunden video del choque en la México-Querétaro",
            "url": "https://news.google.com/rss/articles/infobae-coyotepec-regression",
            "source": "Infobae",
            "date": "2026-11-12",
            "published_at": "2026-11-13T01:23:00Z",
            "category": "Movilidad",
            "borough": "",
            "photo": {
                "id": "reforma_context_photo",
                "kind": "representativa",
                "url": "/assets/fotos/regression-test.jpg",
                "category": "Movilidad",
                "topic": "Paseo de la Reforma",
                "keywords": ["Metrobús Paseo de la Reforma CDMX"],
                "author": "Autor de prueba",
                "license": "CC BY 2.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/2.0/",
                "source": "https://commons.wikimedia.org/wiki/File:MX_MM_PASEO_DE_LA_REFORMA.jpg",
            },
        }
        result = standardize(article)
        self.assertIsNotNone(result)
        self.assertEqual(result["location"], "Coyotepec, Estado de México (fuera de CDMX)")
        self.assertEqual(result["borough"], "")
        self.assertEqual(result["category"], "Movilidad")
        self.assertIn("27 personas lesionadas", result["brief"]["lead"])
        self.assertIn("reapertura", result["brief"]["lead"].casefold())
        self.assertIn("fuera de la capital", result["brief"]["context"])
        self.assertEqual(
            result["source_url"],
            "https://www.infobae.com/mexico/2026/11/13/alumnos-viajaban-de-paseo-a-la-cdmx-y-fueron-impactados-por-trailer-difunden-video-del-choque-en-la-mexico-queretaro/",
        )
        self.assertTrue(is_sensitive_media(result))
        assign_photos([result])
        self.assertNotIn("photo", result)
        rendered = render(result, article_id(result))
        self.assertNotIn('<figure class="article-photo">', rendered)

    def test_rainwater_harvesting_story_is_not_misclassified_as_weather(self):
        result = standardize({
            "title": "CDMX instalará miles de sistemas para captar agua de lluvia en Álvaro Obregón",
            "url": "https://news.google.com/rss/articles/rainwater-harvesting-regression",
            "source": "Enfoque Noticias",
            "date": "2026-11-12",
            "published_at": "2026-11-13T01:25:17Z",
            "category": "CDMX",
        })
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Medio Ambiente")
        self.assertIn("captación y aprovechamiento", result["brief"]["lead"].casefold())
        self.assertNotIn("pronóstico", result["brief"]["lead"].casefold())
        self.assertNotIn("previsión del tiempo", result["brief"]["lead"].casefold())

if __name__=="__main__":
    unittest.main()
