"""Previene asignar fotos de patrullas a noticias de ciclismo o tecnología."""
import unittest

from scripts.notas_locales import _photo_category, _photo_score, assign_photos
import update_news as news
from update_news import category_by_headline


class PhotoRelevanceTests(unittest.TestCase):
    def test_rss_category_uses_obvious_headline_subject(self):
        self.assertEqual(category_by_headline(
            "Muévete en Bici este 1 de noviembre", "Seguridad"), "Movilidad")
        self.assertEqual(category_by_headline(
            "Un robot en el centro de la Ciudad de México", "Seguridad"), "CDMX")
        self.assertEqual(category_by_headline(
            "Policía utiliza robot para investigar un robo", "Seguridad"), "Seguridad")

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


if __name__ == "__main__":
    unittest.main()
