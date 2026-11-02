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

    def test_criminal_groups_at_central_de_abasto_reject_theater_photo(self):
        title = "La Central de Abasto se ha convertido en un centro de operación de grupos criminales"
        self.assertEqual(news.category_by_headline(title, "CDMX"), "Seguridad")
        self.assertEqual(news.category_by_headline(title, "Gobierno"), "Seguridad")
        fixed = news.standardize(fake(title, "2026-11-02"))
        self.assertEqual(fixed["category"], "Seguridad")
        self.assertEqual(_photo_category(fixed), "Seguridad")
        # Imagen realmente publicada: puesta en escena teatral De Cachetito (2015).
        self.assertLess(news._photo_score(fixed, {
            "category": "Servicios", "topic": "MEX ED OBRA DE CACHETITO (20290223352)",
            "keywords": ["Obras públicas Ciudad de México"],
        }), 0)
        self.assertLess(news._photo_score(fixed, {
            "category": "CDMX", "topic": "Obra de teatro De Cachetito en plaza pública Ciudad de México",
        }), 0)
        self.assertLess(news._photo_score(fixed, {
            "category": "Seguridad", "topic": "Graduación de la Policía de la Ciudad de México",
            "keywords": ["Policía Ciudad de México"],
        }), 0)
        self.assertLess(news._photo_score(fixed, {
            "category": "Seguridad", "topic": "Entrega de nuevas patrullas de CDMX",
        }), 0)
        self.assertGreaterEqual(news._photo_score(fixed, {
            "category": "CDMX", "topic": "Central de Abasto de Ciudad de México",
        }), 0)
        self.assertGreaterEqual(news._photo_score(fixed, {
            "category": "CDMX", "topic": "Fiscalía y seguridad de Ciudad de México",
        }), 0)
        self.assertEqual(news.category_by_headline(
            "Feria cultural en la Central de Abasto", "CDMX"), "CDMX")

    def test_gasoline_price_rejects_unrelated_house_photo(self):
        title = "Ciudad de México: cuál es el precio de la gasolina este 1 de noviembre"
        article = fake(title, "2026-11-02")
        fixed = news.standardize(article)
        self.assertLess(news._photo_score(fixed, {
            "category": "CDMX", "topic": "Casa González de Cosío, Coyoacán, Ciudad de México",
        }), 0)
        self.assertGreaterEqual(news._photo_score(fixed, {
            "category": "CDMX", "topic": "Gasolinera y surtidor de combustible en Ciudad de México",
        }), 0)
        self.assertIn("este portal clasifica como CDMX", fixed["description"])
        self.assertNotIn("sección de CDMX del periódico", fixed["description"])

    def test_mobility_law_rejects_transit_payment_photo(self):
        title = "Urgen homologar ley de movilidad para evitar tragedias viales"
        self.assertEqual(news.category_by_headline(title, "Seguridad"), "Movilidad")
        article = fake(title, "2026-11-02")
        article["category"] = "Seguridad"
        fixed = news.standardize(article)
        self.assertEqual(fixed["category"], "Movilidad")
        self.assertLess(news._photo_score(fixed, {
            "category": "Movilidad", "topic": "Pago de Metrobús Ciudad de México",
            "keywords": ["Movilidad"],
        }), 0)
        self.assertGreaterEqual(news._photo_score(fixed, {
            "category": "Movilidad", "topic": "Tráfico vehicular y seguridad vial en CDMX",
        }), 0)
        self.assertEqual(news.category_by_headline("Operativo de seguridad en CDMX", "Seguridad"), "Seguridad")

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

    def test_formula_one_victory_requires_racing_photo(self):
        # La portada del 2 de noviembre mostraba una calle del Centro Histórico
        # para una victoria de Verstappen; la coincidencia "CDMX" no basta.
        for title in (
            "Gana Max Verstappen por sexta vez en CDMX",
            "Checo Pérez triunfa en el Gran Premio de México",
        ):
            article = {"title": title, "category": "CDMX"}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": "CDMX",
                    "topic": "Calles Seminario y Moneda Centro Histórico Ciudad de México 02",
                    "keywords": ["Centro Histórico Ciudad de México"],
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": "CDMX",
                    "topic": "Autódromo Hermanos Rodríguez, circuito de Fórmula 1",
                }), 0)

    def test_new_portada_photos_require_specific_subjects(self):
        # Cuatro emparejamientos incorrectos detectados el 2 de noviembre.
        cases = [
            ("Zonas altas de CDMX recibirán apoyos del nuevo programa invernal",
             "Centro Histórico de la Ciudad de México, Rostros de la Ciudad",
             "Entrega de cobijas y abrigo por frío invernal"),
            ("CDMX invierte 74 millones en rehabilitar puentes peatonales",
             "Casa Centro Histórico de la Ciudad de México 03",
             "Puente peatonal en avenida de Ciudad de México"),
            ("Montachoques en CDMX: cómo identificarlos y dónde denunciarlos",
             "Ángel de la Independencia y Torre HSBC CDMX",
             "Choque de automóviles en avenida de Ciudad de México"),
            ("MegaRodadaDelTerror: SSC CDMX remitió a 514 motocicletas a depósitos vehiculares",
             "Graduación de la Policía de la Ciudad de México",
             "Rodada de motociclistas por las calles de CDMX"),
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

    def test_montachoques_rejects_generic_avenue_photo(self):
        article = {"title": "Montachoques en CDMX: cómo identificarlos, qué hacer si eres víctima",
                   "category": "CDMX"}
        self.assertLess(news._photo_score(article, {
            "category": "CDMX",
            "topic": "Avenida Francisco I. Madero, Centro Histórico, Ciudad de México - Torre Latinoamericana",
        }), 0)
        self.assertGreaterEqual(news._photo_score(article, {
            "category": "CDMX",
            "topic": "Automóviles en tráfico vehicular de Ciudad de México",
        }), 0)

    def test_traffic_light_rail_and_rtp_require_matching_transport_photos(self):
        # Ejemplos detectados en la portada del 2 de noviembre: eran imágenes
        # representativas, pero mostraban un medio de transporte distinto.
        cases = [
            ("Gráfica del día: ¿Cuáles son las ciudades de México con más tráfico?",
             "Movilidad", "Tren ligero y metro en la estación Tasqueña 06",
             "Tráfico vehicular en Eje Central, Ciudad de México"),
            ("Gráfica del día: ¿Cuáles son las ciudades de México con más tráfico?",
             "Movilidad", "Trolebús de la Línea 2 sobre Avenida Yucatán",
             "Congestión de automóviles en Ciudad de México"),
            ("Alistan el Tren Ligero Río Hondo-Buenavista: conectará Naucalpan con CDMX",
             "Metro", "Estación Sevilla de la Línea 1 del Metro de la Ciudad de México",
             "Tren ligero y metro en la estación Tasqueña"),
            ("Ampliará RTP CDMX ruta para llegar al Metro Mixiuhca",
             "Metro", "Estación Pantitlán del Metro de la Ciudad de México",
             "Autobús RTP de la Ciudad de México"),
        ]
        for title, category, unrelated, relevant in cases:
            article = {"title": title, "category": category}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": category, "topic": unrelated,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": category, "topic": relevant,
                }), 0)

    def test_imss_planton_rejects_ecobici_photo_without_word_separator(self):
        # Caso real del 2 de noviembre: el descriptor EcoBiciCdMexico
        # no terminaba en límite de palabra y evadía la regla de protestas.
        protest = {
            "title": "¿Dónde Hay Plantones de Trabajadores y Jubilados del IMSS? Zonas de CDMX con Afectación",
            "category": "Movilidad",
        }
        for unrelated in ("EcoBiciCdMexico", "Talleres de EcoBici"):
            with self.subTest(photo=unrelated):
                self.assertLess(news._photo_score(protest, {
                    "category": "Movilidad", "topic": unrelated,
                }), 0)
        self.assertGreaterEqual(news._photo_score(protest, {
            "category": "Movilidad",
            "topic": "Protesta de trabajadores del IMSS en una avenida",
        }), 0)
        # El cambio no bloquea fotografías de bicicletas cuando la noticia
        # trata efectivamente de una rodada ciclista.
        cycling = {"title": "Rodada ciclista en Ciudad de México",
                   "category": "Movilidad"}
        self.assertGreaterEqual(news._photo_score(cycling, {
            "category": "Movilidad", "topic": "EcoBiciCdMexico",
        }), 0)

    def test_november_2_new_editorial_photo_mismatches(self):
        # Emparejamientos comprobados en news.json: son imágenes representativas,
        # pero ni la ubicación ni la categoría justifican un tema equivocado.
        cases = [
            ("Agenda de movilizaciones, rodadas y eventos en la CdMx para hoy 2 de noviembre 2026",
             "Seguridad", "Equipo de trabajo de los Bomberos CDMX",
             "Manifestación y protesta en avenida de la CDMX"),
            ("EN VIVO | Bloqueos, accidentes y manifestaciones hoy 2 de noviembre",
             "Movilidad", "Edificios Paseo de la Reforma CDMX",
             "Tráfico vehicular en una avenida de la CDMX"),
            ("80 toneladas de carne que huelen a muerte: carne podrida en frigorífico enferma a vecinos de Xochimilco",
             "CDMX", "Trajineras y canales de Xochimilco",
             "Frigorífico y carne en un mercado de la CDMX"),
            ("80 toneladas de carne que huelen a muerte: carne podrida en frigorífico enferma a vecinos de Xochimilco",
             "CDMX", "MX MM COYOACÁN - Mercado",
             "Frigorífico y carne en un mercado de la CDMX"),
            ("Megarrodada en CdMx deja 246 motociclistas detenidos y 514 motos",
             "CDMX", "Jeep policía CDMX",
             "Motociclistas en rodada por avenida de la CDMX"),
            ("Día de Muertos: recuerdos y nostalgia marcan las visitas a cementerios de la Ciudad de México",
             "CDMX", "Desfile de Catrinas in Mexico City 2026",
             "Visitas a un panteón con tumbas y ofrendas funerarias"),
            ("Día de muertos 2026: Actividades, conciertos y shows gratuitos por alcaldía en CDMX",
             "Cultura", "Cafetería del Museo Nacional de Antropología",
             "Festival de Día de Muertos con ofrendas y música"),
            ("Conciertos en la CDMX hoy 2 de noviembre: Los mejores eventos en Día de Muertos",
             "Cultura", "Desfile de Catrinas in Mexico City 2026",
             "Concierto de música en escenario"),
            ("Pulso CDMX / Día Mundial por el Derecho a Morir con Dignidad",
             "CDMX", "Calle de Donceles, Centro Histórico de la Ciudad de México",
             "Hospital y cuidados paliativos"),
        ]
        for title, category, unrelated, relevant in cases:
            article = {"title": title, "category": category}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": category, "topic": unrelated,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": category, "topic": relevant,
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
        # El medio publicó esta noticia en su sección CDMX, pero el cuerpo
        # identifica la agencia municipal de Juchitán, Oaxaca.
        oaxaca = "Asamblea comunitaria determina relevo de autoridades auxiliares en Álvaro Obregón"
        self.assertTrue(news.outside_cdmx_scope(oaxaca))
        self.assertEqual(news.identify_location(oaxaca),
                         ("", "Álvaro Obregón, Juchitán, Oaxaca (fuera de CDMX)"))
        oaxaca_article = news.standardize(fake(oaxaca, datetime.now(timezone.utc).date().isoformat()))
        self.assertEqual(oaxaca_article["borough"], "")
        self.assertEqual(news.homepage_articles([oaxaca_article], [], datetime.now(timezone.utc)), [])
        # No excluir asambleas reales de la alcaldía homónima.
        self.assertFalse(news.outside_cdmx_scope(
            "Asamblea vecinal en la alcaldía Álvaro Obregón CDMX"))
        self.assertFalse(news.outside_cdmx_scope(
            "Asamblea comunitaria determina relevo de autoridades auxiliares en Álvaro Obregón CDMX"))
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

    def test_violence_and_marches_override_wrong_rss_categories(self):
        self.assertEqual(news.category_by_headline(
            "Ataque armado en Tepito deja 2 muertos en pleno festejo de Día de Muertos en CDMX",
            "CDMX"), "Seguridad")
        self.assertEqual(_photo_category({
            "title": "Ataque armado en Tepito deja 2 muertos en Día de Muertos",
            "category": "CDMX",
        }), "Seguridad")
        self.assertEqual(news.category_by_headline(
            "Estas Son las Marchas, Concentraciones y Eventos en la CDMX para Este Lunes",
            "Seguridad"), "Movilidad")

    def test_violent_crime_arrest_and_crash_need_real_subject_match(self):
        arrest = {"title": "Detienen a tres hombres por obras irregulares en Tláhuac",
                  "category": "Seguridad", "borough": "Tláhuac"}
        self.assertLess(news._photo_score(arrest, {
            "category": "Seguridad", "topic": "Jeep policía CDMX",
        }), 0)
        self.assertGreaterEqual(news._photo_score(arrest, {
            "category": "Seguridad", "topic": "Fiscalía investiga detención en Tláhuac",
        }), 0)
        murder = {"title": "Asesina a Mujer y a Menor de 4 Años en Tepito",
                  "category": "Seguridad"}
        self.assertLess(news._photo_score(murder, {
            "category": "Seguridad", "topic": "Policía de tránsito Ciudad de México con automovilistas",
        }), 0)
        self.assertGreaterEqual(news._photo_score(murder, {
            "category": "Seguridad", "topic": "Investigación penal de Fiscalía CDMX",
        }), 0)
        crash = {"title": "Accidente en Iztacalco Hoy: Hay Autos Destrozados y una Motocicleta Aplastada",
                 "category": "Movilidad", "borough": "Iztacalco"}
        self.assertLess(news._photo_score(crash, {
            "category": "Movilidad",
            "topic": "Pavimentación en la carretera de los Dinamos en Magdalena Contreras 1941",
        }), 0)
        self.assertGreaterEqual(news._photo_score(crash, {
            "category": "Movilidad", "topic": "Tráfico vehicular con autos en avenida de CDMX",
        }), 0)

    def test_regenerated_photos_reject_ceremonies_and_other_borough_avenues(self):
        arrest = {"title": "Detienen a tres hombres por obras irregulares y cambio ilegal de uso de suelo en Tláhuac",
                  "category": "Seguridad", "borough": "Tláhuac"}
        self.assertLess(news._photo_score(arrest, {
            "category": "Seguridad", "topic": "Adquisición patrullas para la Policía 03",
        }), 0)
        self.assertGreaterEqual(news._photo_score(arrest, {
            "category": "Seguridad", "topic": "Operativo de Fiscalía en Tláhuac",
        }), 0)

        crash = {"title": "Accidente en Iztacalco Hoy: Hay Autos Destrozados y una Motocicleta Aplastada",
                 "category": "Movilidad", "borough": "Iztacalco"}
        self.assertLess(news._photo_score(crash, {
            "category": "CDMX",
            "topic": "Avenida Francisco I. Madero, Centro Histórico, Ciudad de México - Torre Latinoamericana",
        }), 0)
        self.assertGreaterEqual(news._photo_score(crash, {
            "category": "Movilidad", "topic": "Tráfico vehicular en avenida de Iztacalco",
        }), 0)

        murder = {"title": "Asesina a Mujer y a Menor de 4 Años en Tepito",
                  "category": "Seguridad"}
        self.assertLess(news._photo_score(murder, {
            "category": "Seguridad", "topic": "Graduación de la Policía de la Ciudad de México",
        }), 0)
        self.assertGreaterEqual(news._photo_score(murder, {
            "category": "Seguridad", "topic": "Investigación penal de Fiscalía CDMX",
        }), 0)

    def test_november_2_followup_photo_mismatches(self):
        # Nuevas asignaciones incongruentes tras regenerar news.json.
        cases = [
            ("Familias Visitan Panteones de CDMX para Adornar Tumbas con Cempasúchil",
             "CDMX", "Recepción de Marichuy Patricio en Ciudad Universitaria UNAM 06",
             "Cementerio con tumbas y ofrendas funerarias en CDMX"),
            ("Detienen a tres hombres por obras irregulares y cambio ilegal de uso de suelo en Tláhuac, CdMx",
             "Seguridad", "Claudia Sheinbaum entrega patrullas Iztapalapa 03",
             "Operativo de Fiscalía en Tláhuac"),
            ("Ataque armado en Tepito deja 2 muertos en pleno festejo de Día de Muertos en CDMX",
             "CDMX", "Desfile de Catrinas in Mexico City 2026",
             "Investigación de Fiscalía en CDMX"),
            ("Marchas en CDMX hoy 2 de noviembre: ¿Dónde y a qué hora habrá bloqueos?",
             "Movilidad", "Metrobús en Paseo de la Reforma",
             "Manifestación de personas en avenida CDMX"),
            ("Estas Son las Marchas, Concentraciones y Eventos en la CDMX para Este Lunes",
             "Movilidad", "Trolebús de la Línea 5 en Paseo de la Reforma",
             "Protestas y concentraciones en la CDMX"),
            ("Búsqueda de personas se realiza de manera individual, algunas desde 1952: Luis Gómez",
             "CDMX", "Ángel de la Independencia Ciudad de México",
             "Colectivo de búsqueda de personas desaparecidas"),
            ("Desciende deuda de estados; cinco concentran 54%, señala Auditoría",
             "CDMX", "Casa Centro Histórico de la Ciudad de México",
             "Auditoría de deuda y presupuesto público"),
            ("Accidente en Iztacalco Hoy: Hay Autos Destrozados y una Motocicleta Aplastada",
             "Movilidad", "Trolebús de la Línea 2 sobre Avenida Yucatán",
             "Tráfico vehicular de autos y motocicletas en avenida de Iztacalco"),
            ("Asesina a Mujer y a Menor de 4 Años en Tepito; Agresores Escapan en Bici Eléctrica",
             "Seguridad", "Protección civil CDMX",
             "Fiscalía e investigación penal en CDMX"),
        ]
        for title, category, unrelated, relevant in cases:
            article = {"title": title, "category": category}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": category, "topic": unrelated,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": category, "topic": relevant,
                }), 0)

    def test_november_2_arrests_crash_and_water_photo_mismatches(self):
        # Fotografías observadas en el índice público del 2 de noviembre.
        cases = [
            ("Accidente en Iztacalco Hoy: Hay Autos Destrozados y una Motocicleta Aplastada",
             "Movilidad", "Iztacalco",
             "Vista aérea del Autódromo Hermanos Rodríguez, Ciudad de México (fotografía de 2025)",
             "Tráfico de autos y motocicletas en avenida de Iztacalco"),
            ("Detienen a tres con más de cien dosis de droga en la Cdmx",
             "Seguridad", "",
             "Policía controlando el semáforo, Ciudad de México",
             "Operativo policial de detención en Ciudad de México"),
            ("Detienen a tres hombres por construcción irregular en suelo de conservación de Tláhuac",
             "Seguridad", "Tláhuac",
             "Nuevas patrullas para Cuajimalpa 02",
             "Operativo de Fiscalía en Tláhuac"),
            ("Detienen a tres hombres por construcción irregular en suelo de conservación de Tláhuac; ¿qué pasó?",
             "Seguridad", "Tláhuac",
             "Entrega Claudia Sheinbaum 113 nuevas patrullas en Gustavo A Madero 02",
             "Operativo de Fiscalía en Tláhuac"),
            ("Coyoacán sin agua las próximas 40 horas: LISTA de colonias afectadas",
             "CDMX", "Coyoacán",
             "Registro de agua. Primera Sección del Bosque de Chapultepec - 4",
             "Tuberías de abastecimiento de agua en Coyoacán"),
        ]
        for title, category, borough, unrelated, relevant in cases:
            article = {"title": title, "category": category, "borough": borough}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": category, "topic": unrelated,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": category, "topic": relevant,
                }), 0)

    def test_motorcycle_crash_does_not_use_church_photo(self):
        # Incongruencia comprobada en news.json del 2 de noviembre.
        crash = {
            "title": "Accidente en Azcapotzalco: motociclista choca contra camión en Aquiles Serdán",
            "category": "Movilidad", "borough": "Azcapotzalco",
        }
        self.assertLess(news._photo_score(crash, {
            "category": "CDMX", "topic": "Parroquia de Santa Catarina, Azcapotzalco",
        }), 0)
        self.assertGreaterEqual(news._photo_score(crash, {
            "category": "Movilidad", "topic": "Tráfico vehicular en avenida Azcapotzalco",
        }), 0)
        derrape = {"title": "Motociclista derrapa en avenida de CDMX",
                   "category": "Movilidad"}
        self.assertLess(news._photo_score(derrape, {
            "category": "CDMX", "topic": "Parroquia de Santa Catarina",
        }), 0)
        choque = {"title": "Choque entre camiones en CDMX", "category": "Movilidad"}
        self.assertGreaterEqual(news._photo_score(choque, {
            "category": "Movilidad", "topic": "Camión de carga en avenida",
        }), 0)

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



    def test_cdmx_headline_signal_blocks_unrelated_national_rss_results(self):
        # Titulares realmente observados en el índice público del 02-11-2026.
        unrelated = (
            "Trágico accidente en la carretera federal 307 deja una mujer sin vida y un hombre grave",
            "Tráfico colapsado, estrés y molestia: ¿Qué sucedió ayer en la Carretera Nacional?",
            "“Pudo haber omisiones, pero de ninguna manera traición a la patria”: afirma defensa de César Jáuregui sobre agentes de EEUU en Chihuahua",
            "Grecia Quiroz concluye en Uruapan el recorrido de velas que Carlos Manzo no pudo terminar",
            "SRE informa sobre fallecimiento de mexicano en accidente de tren Madrid-Sevilla",
            "Jesús Ochoa cuenta cómo fue su caída de un elevador",
            "Entre color, música y añoranza: Así se vive el Día de Muertos en México",
        )
        for title in unrelated:
            with self.subTest(title=title):
                self.assertFalse(news.headline_has_cdmx_signal(title))
                self.assertFalse(news.local_for_homepage({"title": title}))
        local = (
            "Choque en Eje Central deja vehículo destrozado en Gustavo A. Madero, CDMX",
            "Metro CDMX confirma horario del servicio este lunes",
            "Accidente vial en Xochimilco",
            "La Central de Abasto se ha convertido en un centro de operación de grupos criminales",
            "Feria de café de Veracruz se celebra en CDMX",
        )
        for title in local:
            with self.subTest(title=title):
                self.assertTrue(news.headline_has_cdmx_signal(title))
        self.assertEqual(news.outside_cdmx_location(
            "Accidente en la carretera federal 307"), "Carretera federal 307, sureste de México")
        self.assertEqual(news.outside_cdmx_location(
            "SRE informa sobre accidente de tren Madrid-Sevilla"), "España")
        self.assertEqual(news.outside_cdmx_location(
            "Agentes de EEUU en Chihuahua"), "Chihuahua")
        self.assertEqual(news.outside_cdmx_location(
            "Grecia Quiroz concluye en Uruapan su recorrido"), "Uruapan, Michoacán")

    def test_unrelated_rss_headline_is_archived_without_reaching_cdmx_homepage(self):
        now = datetime.now(timezone.utc)
        date = now.date().isoformat()
        outside = news.standardize(fake(
            "Trágico accidente en la carretera federal 307 deja una mujer sin vida", date))
        local = news.standardize(fake("Choque en Eje Central, CDMX", date))
        self.assertEqual(news.homepage_articles([outside, local], [], now), [local])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archivo"
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root / "alcaldias",
                                DEST=root / "news.json"):
                with patch.object(news, "assign_photos", return_value={"assigned": 0}):
                    news.consolidate_archive([outside, local], now - timedelta(days=365), "Prueba")
                saved = news.load_json(archive / (date[:7] + ".json"), {"articles": []})
                restored = news.fill_recent_from_archive([], now)
        self.assertEqual(len(saved["articles"]), 2)
        self.assertEqual([item["title"] for item in restored], [local["title"]])

    def test_protests_with_street_impacts_are_mobility_not_culture_or_crime(self):
        self.assertEqual(news.category_by_headline(
            "Manifestaciones en CDMX este 2 de noviembre: calles afectadas y horarios",
            "Cultura"), "Movilidad")
        self.assertEqual(news.category_by_headline(
            "¿Dónde hay plantones de trabajadores? Zonas de CDMX con afectación",
            "Seguridad"), "Movilidad")
        self.assertEqual(news.category_by_headline(
            "Las calles de la CDMX tendrán actividades, incluyendo marchas y plantones",
            "Cultura"), "Movilidad")


    def test_current_portada_photos_require_subject_not_only_cdmx_context(self):
        # Incongruencias observadas el 2 de noviembre en el índice público.
        cases = (
            ("Día de Muertos en CDMX: Panteones Reciben a Familias con Operativos de Seguridad",
             "Seguridad", "Desfile de Catrinas in Mexico City 2026",
             "Panteón con tumbas y ofrendas funerarias"),
            ("Manifestaciones en CDMX este 2 de noviembre: calles afectadas y horarios",
             "Movilidad", "Trolebús de la Línea 5 en Paseo de la Reforma",
             "Manifestación con bloqueo y tráfico en avenida"),
            ("Movilizaciones en la CDMX: cuatro concentraciones este lunes",
             "CDMX", "Fuente Alameda Central, Ciudad de México",
             "Concentración y protesta en calles de CDMX"),
            ("Del Campo a tu Colonia: venta directa de productos del suelo de conservación en CDMX",
             "CDMX", "Ciudad de México - Colonia Centro 6984",
             "Mercado de productores de verduras de Xochimilco"),
            ("De ARTZ Pedregal a Antara: las obras en CDMX de Javier Sordo Madaleno",
             "CDMX", "Obras remodelación Zócalo Ciudad de México 2017",
             "Arquitectura de centro comercial ARTZ Pedregal"),
            ("Muere mujer tras ser atropellada por conductor ebrio en Coyoacán",
             "Movilidad", "Trolebús de la Línea 2 sobre Avenida Yucatán",
             "Tráfico vehicular en Avenida Coyoacán"),
        )
        for title, category, wrong, appropriate in cases:
            article = {"title": title, "category": category}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": category, "topic": wrong,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": category, "topic": appropriate,
                }), 0)
        self.assertEqual(_photo_category({
            "title": "Día de Muertos en CDMX: Panteones Reciben a Familias con Operativos de Seguridad",
            "category": "Seguridad",
        }), "Seguridad")
        cycling = {
            "title": "Prevén movilizaciones, rodadas ciclistas y eventos por Día de Muertos en CDMX",
            "category": "Movilidad",
        }
        self.assertGreaterEqual(news._photo_score(cycling, {
            "category": "Movilidad", "topic": "Talleres de EcoBici",
        }), 0)
        protest = {
            "title": "Manifestaciones en CDMX este 2 de noviembre: calles afectadas y horarios",
            "category": "Movilidad",
        }
        self.assertLess(news._photo_score(protest, {
            "category": "Movilidad", "topic": "Ecobici Estación 8 - panoramio",
        }), 0)
        atropellamiento = {
            "title": "Muere mujer tras ser atropellada por conductor ebrio en Coyoacán",
            "category": "Movilidad",
        }
        self.assertLess(news._photo_score(atropellamiento, {
            "category": "Movilidad",
            "topic": "PAVIMENTACIÓN EN LA CARRETERA DE LOS DINAMOS EN LA MAGDALENA CONTRERAS FEBRERO 20 1941",
        }), 0)
        self.assertGreaterEqual(news._photo_score(atropellamiento, {
            "category": "Movilidad", "topic": "Tráfico vehicular en avenida de Coyoacán",
        }), 0)


    def test_november_2_live_editorial_regressions(self):
        # Incidencias confirmadas en news.json y HTML públicos del 2 de noviembre.
        shooting = {
            "title": "Tepito: una mujer y un niño murieron baleados en el cruce de Peñón y Tenochtitlán",
            "category": "Seguridad",
        }
        self.assertEqual(news.category_by_headline(shooting["title"], "CDMX"), "Seguridad")
        self.assertEqual(_photo_category(shooting), "Seguridad")
        self.assertLess(news._photo_score(shooting, {
            "category": "Seguridad",
            "topic": "Graduación de la Policía de la Ciudad de México -i---i- (37018695916)",
            "keywords": ["Policía Ciudad de México"],
        }), 0)
        self.assertGreaterEqual(news._photo_score(shooting, {
            "category": "Seguridad", "topic": "Investigación penal de Fiscalía CDMX",
        }), 0)

        rainwater = {
            "title": "La captación de agua de lluvia busca transformar la vida en el sur de la Ciudad de México",
            "category": "CDMX", "source": "ABC Noticias",
        }
        lead = news.summarize(rainwater)["lead"].lower()
        self.assertIn("captación", lead)
        self.assertNotIn("pronóstico", lead)
        self.assertIn("no de una previsión del tiempo", lead)
        self.assertLess(news._photo_score(rainwater, {
            "category": "Medio Ambiente", "topic": "Plantas con gotas de lluvia, Ciudad de México",
        }), 0)
        self.assertGreaterEqual(news._photo_score(rainwater, {
            "category": "Medio Ambiente", "topic": "Sistema de captación de agua de lluvia con cisterna",
        }), 0)

        prison = {
            "title": "Una Mujer acompañada por un menor, Intentan ingresar marihuana al Reclusorio Varonil Oriente en Iztapalapa; y los detienen",
            "category": "Seguridad", "borough": "Iztapalapa",
        }
        self.assertLess(news._photo_score(prison, {
            "category": "Seguridad", "topic": "Metro Iztapalapa 02",
        }), 0)
        self.assertGreaterEqual(news._photo_score(prison, {
            "category": "Seguridad", "topic": "Reclusorio Varonil Oriente Iztapalapa",
        }), 0)

        self.assertEqual(news.category_by_headline(
            "Movilizaciones en CDMX hoy 2 de noviembre: ¿Dónde habrá concentraciones, eventos y plantones?",
            "Seguridad"), "Movilidad")
        self.assertEqual(news.category_by_headline(
            "La Catrina monumental del Zócalo de la Ciudad de México rompe récord Guinness",
            "Gobierno"), "Cultura")


    def test_november_2_new_photo_mismatches_are_rejected(self):
        # Emparejamientos observados en el índice público a las 20:22 UTC.
        cases = (
            ("Mirna Vargas realiza caminata de CDMX a Xalapa buscando recuperar a su hija",
             "Jardin Escénico del Bosque de Chapultepec 01",
             "Caminata de madres buscadoras por personas desaparecidas"),
            ("Viajará comitiva de trabajadores del IMSS a CDMX para reforzar protesta sindical",
             "Calle de Donceles, Centro Histórico de la Ciudad de México",
             "Manifestación de trabajadores en protesta sindical"),
            ("CDMX te recuerda la mochila de emergencia en medio de llamado mundial a almacenar suministros",
             "Sala de Tesorería en Palacio Nacional - III",
             "Mochila de emergencia y suministros de protección civil"),
            ("EZLN señala que los tres órdenes de gobierno intentan impedir que se reúna con madres buscadoras en CDMX",
             "Calle Francisco I. Madero con Palacio Nacional al fondo",
             "Colectivo de madres buscadoras de personas desaparecidas"),
            ("Trabajo en CDMX: Embajada de Alemania abrió vacantes con salarios de 21 mil pesos",
             "Plaza de la Revolución y Monumento Revolución",
             "Oficinas de la Embajada de Alemania"),
            ("¡$1,500 al bimestre! Así es la Beca de Transporte para Universitarios que puedes pedir en CDMX",
             "Avenida Francisco I. Madero - Torre Latinoamericana",
             "Autobús de transporte para estudiantes universitarios"),
            ("Fuga de agua afecta ocho viviendas en Gustavo A. Madero; reparan tubería dañada",
             "Parroquia de Corpus Cristi Gustavo A Madero",
             "Tuberías de agua potable en reparación"),
            ("Mujer y menor de edad son asesinados a tiros en Tepito, alcaldía Cuauhtémoc",
             "Busto de Cuauhtémoc en el zócalo de la CDMX",
             "Investigación penal de Fiscalía CDMX"),
            ("VIDEO | Choque en Eje Central deja vehículo destrozado en Gustavo A. Madero, CDMX",
             "Trolebús de la Línea 2 sobre Avenida Yucatán",
             "Tráfico vehicular en avenida de Ciudad de México"),
        )
        for title, wrong, relevant in cases:
            article = {"title": title, "category": "CDMX"}
            with self.subTest(title=title):
                self.assertLess(news._photo_score(article, {
                    "category": "CDMX", "topic": wrong,
                }), 0)
                self.assertGreaterEqual(news._photo_score(article, {
                    "category": "CDMX", "topic": relevant,
                }), 0)


if __name__ == "__main__":
    unittest.main()
