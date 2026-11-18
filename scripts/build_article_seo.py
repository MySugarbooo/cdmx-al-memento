#!/usr/bin/env python3
"""Generate crawlable article summaries from the existing editorial news.json.
Run after the news feed has been updated. Does not change existing article URLs.
"""
import json
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from update_news import dedupe_homepage_events

BASE = "https://cdmx-al-memento.pages.dev"
SOURCE = ROOT / "news.json"
OUT = ROOT / "articulos"
SITEMAP = ROOT / "sitemap-articulos.xml"
EDITORIAL_PHOTO_OVERRIDES = {
    "/noticias/?id=534d17e7c38cfd83b7a1&mes=2026-11": {
        "id": "contexto_azcapotzalco_plaza_civica_2011",
        "kind": "representativa",
        "category": "Gobierno",
        "topic": "Panorámica de Plaza Cívica Fernando Montes de Oca y edificio delegacional de Azcapotzalco (archivo 2011); no evidencia del presupuesto 2027.",
        "keywords": [
            "Azcapotzalco",
            "presupuesto de alcaldía",
            "presupuesto 2027",
            "edificio delegacional",
            "Plaza Cívica Fernando Montes de Oca",
            "gobierno local",
            "alcaldía"
        ],
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Azcapotzalco_-_Panor%C3%A1mica_Plaza_C%C3%ADvica_Fernando_Montes_de_Oca.JPG/960px-Azcapotzalco_-_Panor%C3%A1mica_Plaza_C%C3%ADvica_Fernando_Montes_de_Oca.JPG",
        "source": "https://commons.wikimedia.org/wiki/File:Azcapotzalco_-_Panor%C3%A1mica_Plaza_C%C3%ADvica_Fernando_Montes_de_Oca.JPG",
        "author": "ProtoplasmaKid",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        "borough": "Azcapotzalco",
        "context": "Fotografía de archivo de la Plaza Cívica Fernando Montes de Oca y el edificio delegacional de Azcapotzalco; no muestra una sesión presupuestal ni acredita las cifras solicitadas.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=caebd6fdf4edab5ae26c&mes=2026-11": {
        "id": "contexto_patrullas_iztapalapa_denuncias",
        "category": "Seguridad",
        "topic": "Patrullas en Iztapalapa, foto de archivo; imagen representativa de seguridad pública, no documenta el secuestro reportado en Tlalpan ni identifica a personas involucradas.",
        "url": "/assets/fotos/archivo_seguridad_011.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Claudia_Sheinbaum_entrega_patrullas_Iztapalapa_02.jpg",
        "author": "Gobierno de la Ciudad de México",
        "license": "CC BY 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/4.0",
        "keywords": [
            "Iztapalapa",
            "patrullas",
            "seguridad",
            "denuncias"
        ],
        "borough": "Iztapalapa",
        "adaptation": "Foto de archivo de Wikimedia Commons; sin modificación.",
        "kind": "representativa",
        "context": "Fotografía de archivo de patrullas de la Ciudad de México; ilustra el tema de seguridad pública, no el hecho reportado."
    },
    "/noticias/?id=746166b9b292b1c7f60c&mes=2026-11": {
        "id": "contexto_santa_fe_cuajimalpa_denuncias",
        "kind": "representativa",
        "category": "Alcaldías",
        "topic": "Vista aérea de Centro Santa Fe, alcaldía Cuajimalpa, CDMX (archivo 2024); imagen de contexto de la zona, no muestra el bloqueo ni el tránsito del 17 de noviembre de 2026.",
        "file": "Centro Santa Fe - vista aérea.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a9/Centro_Santa_Fe_-_vista_a%C3%A9rea.jpg/960px-Centro_Santa_Fe_-_vista_a%C3%A9rea.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Centro_Santa_Fe_-_vista_a%C3%A9rea.jpg",
        "author": "ProtoplasmaKid",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        "keywords": [
            "Santa Fe",
            "Cuajimalpa",
            "Centro Santa Fe",
            "Ciudad de México",
            "denuncias por colonia"
        ],
        "captured_at": "2024-10-02",
        "context": "Vista aérea del Centro Santa Fe para ubicar la zona mencionada por La Jornada; no documenta la manifestación ni las afectaciones viales del día.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación.",
        "borough": "Cuajimalpa de Morelos"
    },
    "/noticias/?id=451fbd723d5e452167e8&mes=2026-11": {
        "id": "contexto_embarazo_representativo_niaid",
        "kind": "representativa",
        "category": "Salud",
        "topic": "Mujer embarazada, fotografía de archivo de NIAID (24/08/2018); imagen representativa del embarazo, no muestra a beneficiarias ni el programa de CDMX.",
        "file": "Pregnant woman (43338546905).jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/11/Pregnant_woman_%2843338546905%29.jpg/960px-Pregnant_woman_%2843338546905%29.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Pregnant_woman_(43338546905).jpg",
        "author": "NIAID",
        "license": "CC BY 2.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/2.0",
        "keywords": [
            "embarazo",
            "mujer embarazada",
            "salud materna",
            "programas sociales",
            "Mujeres Sanas e Infancias Protegidas"
        ],
        "captured_at": "2018-08-24",
        "uploaded_at": "2019-10-10",
        "context": "Fotografía de archivo de NIAID que representa el embarazo; no documenta el programa Mujeres Sanas e Infancias Protegidas ni identifica a sus beneficiarias.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=3225e4d7915c70c83136&mes=2026-11": {
        "id": "contexto_museo_historia_natural_2013",
        "kind": "representativa",
        "category": "Cultura",
        "topic": "Museo de Historia Natural y Cultura Ambiental, Segunda Sección del Bosque de Chapultepec, CDMX (20/01/2013); fotografía del recinto, no documenta la Noche de Museos ni la actividad de Harry Potter.",
        "file": "Museo de Historia Natural y Cultura Ambiental 04.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/60/Museo_de_Historia_Natural_y_Cultura_Ambiental_04.jpg/960px-Museo_de_Historia_Natural_y_Cultura_Ambiental_04.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Museo_de_Historia_Natural_y_Cultura_Ambiental_04.jpg",
        "author": "ProtoplasmaKid",
        "license": "CC BY-SA 3.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/3.0",
        "keywords": [
            "Museo de Historia Natural",
            "Noche de Museos",
            "Chapultepec",
            "Cultura",
            "Ciudad de México",
            "Harry Potter"
        ],
        "borough": "Miguel Hidalgo",
        "captured_at": "2013-01-20",
        "uploaded_at": "2013-01-21",
        "context": "Fotografía del exterior del Museo de Historia Natural y Cultura Ambiental en Chapultepec; muestra el recinto, no la actividad temática ni a sus asistentes.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=b5e636680f6dd0f0df25&mes=2026-11": {
        "id": "contexto_cineteca_nacional_2015",
        "kind": "representativa",
        "category": "Cultura",
        "topic": "Cineteca Nacional, Ciudad de México (14/02/2015); imagen representativa de un recinto cinematográfico, no es la sede de la proyección de Remain ni documenta el evento.",
        "file": "Cineteca Nacional, Ciudad de México.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/62/Cineteca_Nacional%2C_Ciudad_de_M%C3%A9xico.jpg/960px-Cineteca_Nacional%2C_Ciudad_de_M%C3%A9xico.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Cineteca_Nacional,_Ciudad_de_M%C3%A9xico.jpg",
        "author": "B.jars",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
        "keywords": [
            "cine",
            "Cineteca Nacional",
            "proyección cinematográfica",
            "Ciudad de México",
            "Remain",
            "M. Night Shyamalan"
        ],
        "borough": "Benito Juárez",
        "captured_at": "2015-02-14",
        "uploaded_at": "2015-11-29",
        "context": "Fotografía de archivo de la Cineteca Nacional; Infobae sitúa la función especial de Remain en Cinépolis Miguel Ángel de Quevedo 227, no en la Cineteca.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=3dc6cf266cdcd563bb01&mes=2026-11": {
        "id": "contexto_cineteca_nacional_2015",
        "kind": "representativa",
        "category": "Cultura",
        "topic": "Cineteca Nacional, Ciudad de México (14/02/2015); imagen representativa de un recinto cinematográfico, no es la sede de la proyección de Remain ni documenta el evento.",
        "file": "Cineteca Nacional, Ciudad de México.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/62/Cineteca_Nacional%2C_Ciudad_de_M%C3%A9xico.jpg/960px-Cineteca_Nacional%2C_Ciudad_de_M%C3%A9xico.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Cineteca_Nacional,_Ciudad_de_M%C3%A9xico.jpg",
        "author": "B.jars",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
        "keywords": [
            "cine",
            "Cineteca Nacional",
            "proyección cinematográfica",
            "Ciudad de México",
            "Remain",
            "M. Night Shyamalan"
        ],
        "borough": "Benito Juárez",
        "captured_at": "2015-02-14",
        "uploaded_at": "2015-11-29",
        "context": "Fotografía de archivo de la Cineteca Nacional; Infobae sitúa la función especial de Remain en Cinépolis Miguel Ángel de Quevedo 227, no en la Cineteca.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=3ba1e63aebcbe83062ef&mes=2026-11": {
        "id": "contexto_gallinero_chinampa_xochimilco",
        "kind": "representativa",
        "category": "Servicios",
        "topic": "Gallinero artesanal en una chinampa de Xochimilco (12/04/2018); imagen de contexto, no documenta el programa Gallinas en Casa de 2026.",
        "file": "Gallinero hecho a mano en chinampa.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Gallinero_hecho_a_mano_en_chinampa.jpg/960px-Gallinero_hecho_a_mano_en_chinampa.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Gallinero_hecho_a_mano_en_chinampa.jpg",
        "author": "Diego M.P.",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        "keywords": [
            "gallinas",
            "gallinero",
            "aves de corral",
            "ponedoras",
            "huevo",
            "Xochimilco",
            "chinampa"
        ],
        "borough": "Xochimilco",
        "captured_at": "2018-04-12",
        "context": "Fotografía de archivo de un gallinero artesanal con dos gallinas en una chinampa de Xochimilco; representa el tema de crianza de aves, no muestra a las personas beneficiarias ni la entrega de gallinas del programa de 2026.",
        "adaptation": "Fotografía original de Diego M.P. en Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=b146b3d1dafcb65af69e&mes=2026-11": {
        "id": "contexto_grin_escooter_cdmx_2019",
        "kind": "representativa",
        "category": "Movilidad",
        "topic": "Persona en scooter eléctrico Grin por carril ciclista de CDMX (23/10/2019); foto de archivo, no del trámite de 2026.",
        "file": "Grin e-scooter rider in Mexico City.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/57/Grin_e-scooter_rider_in_Mexico_City.jpg/1280px-Grin_e-scooter_rider_in_Mexico_City.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Grin_e-scooter_rider_in_Mexico_City.jpg",
        "author": "Sonia Medina",
        "license": "CC BY 3.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/3.0/",
        "keywords": ["scooter eléctrico", "scooter", "Grin", "micromovilidad", "carril ciclista", "Ciudad de México", "CDMX", "VEP", "VEMEPE", "motos eléctricas", "bicicletas eléctricas", "registro vehicular"],
        "borough": "",
        "captured_at": "2019-10-23",
        "uploaded_at": "2020-04-13",
        "context": "Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=61a29006a0c0e622c2f4&mes=2026-11": {
        "id": "contexto_grin_escooter_cdmx_2019",
        "kind": "representativa",
        "category": "Movilidad",
        "topic": "Persona en scooter eléctrico Grin por carril ciclista de CDMX (23/10/2019); foto de archivo, no del trámite de 2026.",
        "file": "Grin e-scooter rider in Mexico City.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/57/Grin_e-scooter_rider_in_Mexico_City.jpg/1280px-Grin_e-scooter_rider_in_Mexico_City.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Grin_e-scooter_rider_in_Mexico_City.jpg",
        "author": "Sonia Medina",
        "license": "CC BY 3.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/3.0/",
        "keywords": ["scooter eléctrico", "scooter", "Grin", "micromovilidad", "carril ciclista", "Ciudad de México", "CDMX", "VEP", "VEMEPE", "motos eléctricas", "bicicletas eléctricas", "registro vehicular"],
        "borough": "",
        "captured_at": "2019-10-23",
        "uploaded_at": "2020-04-13",
        "context": "Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "/noticias/?id=486d289d63499706dd71&mes=2026-11": {
        "id": "contexto_grin_escooter_cdmx_2019",
        "kind": "representativa",
        "category": "Movilidad",
        "topic": "Persona en scooter eléctrico Grin por carril ciclista de CDMX (23/10/2019); foto de archivo, no del trámite de 2026.",
        "file": "Grin e-scooter rider in Mexico City.jpg",
        "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/57/Grin_e-scooter_rider_in_Mexico_City.jpg/1280px-Grin_e-scooter_rider_in_Mexico_City.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org",
        "source": "https://commons.wikimedia.org/wiki/File:Grin_e-scooter_rider_in_Mexico_City.jpg",
        "author": "Sonia Medina",
        "license": "CC BY 3.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/3.0/",
        "keywords": ["scooter eléctrico", "scooter", "Grin", "micromovilidad", "carril ciclista", "Ciudad de México", "CDMX", "VEP", "VEMEPE", "motos eléctricas", "bicicletas eléctricas", "registro vehicular"],
        "borough": "",
        "captured_at": "2019-10-23",
        "uploaded_at": "2020-04-13",
        "context": "Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },

}

EDITORIAL_ARCHIVE_OVERRIDES = {
    "/noticias/?id=76ea8af5f775cd14991b&mes=2026-11": {
        "category": "Movilidad",
        "source_url": "https://sociedad-noticias.com/2026/11/18/motociclistas-repartidores-acuerdan-dialogo-con-autoridades-de-la-cdmx/",
        "description": "Sociedad Noticias informó que la Secretaría de Movilidad instaló la primera mesa de diálogo con motociclistas repartidores por aplicación para analizar la regulación de la actividad, crear un registro de operadores y mejorar la seguridad vial. La reunión fue encabezada por el secretario Héctor Ulises García Nieto y contó con la participación de cinco dependencias.",
        "brief": {
            "lead": "Sociedad Noticias reportó que la Semovi encabezó la primera mesa de diálogo con repartidores por aplicación para analizar la regulación de la actividad, crear un registro de operadores y atender la seguridad vial. Participaron representantes de cinco dependencias; las autoridades convocaron a una próxima reunión.",
            "context": "El diálogo puede definir cómo se registran y regulan quienes realizan entregas en motocicleta, incluidas las personas que trabajan por cuenta propia, y cómo se coordinan las medidas de movilidad, trabajo y seguridad vial.",
            "pending": "La nota informa que habrá una próxima reunión, pero no publica todavía un reglamento aprobado ni los requisitos finales del registro. Las propuestas deben distinguirse de las disposiciones vigentes.",
            "method": "Síntesis editorial basada en el artículo completo de Sociedad Noticias, firmado por Fausto Hernández; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=746166b9b292b1c7f60c&mes=2026-11": {
        "category": "Movilidad",
        "source_url": "https://www.jornada.com.mx/2026/11/18/capital/028n1cap",
        "description": "La Jornada reportó nueve movilizaciones y bloqueos en la Ciudad de México; uno de ellos cerró por más de cinco horas los accesos a Santa Fe, en Cuajimalpa, desde las 7:00 horas del 17 de noviembre.",
        "brief": {
            "lead": "La Jornada informó que una jornada de nueve movilizaciones incluyó un bloqueo en los accesos a Santa Fe que comenzó alrededor de las 7:00 y se prolongó poco más de cinco horas. El diario reportó que unas 400 personas participaron y que dijeron ser familiares de internos del penal federal 4 de Tepic; también atribuyó a autoridades la versión de que habrían sido convocadas y pagadas por personas cercanas a Lenin Canchola.",
            "context": "Los cierres afectaron avenidas como Vasco de Quiroga, Carlos Echanove, Juan Salvador Agraz, Mario Pani y Prolongación Reforma; la nota también reportó retrasos en el transporte público.",
            "pending": "La presunta relación de los convocantes con Lenin Canchola y los pagos es una versión atribuida por La Jornada a autoridades; no debe presentarse como una determinación judicial ni como un hecho probado.",
            "method": "Síntesis basada en la nota de La Jornada, firmada por Kevin Ruiz, Nayelli Ramírez, Jared Laureles, Carolina Gómez y Jessica Xantomila, publicada el 18 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=451fbd723d5e452167e8&mes=2026-11": {
        "source": "La Prensa",
        "source_url": "https://oem.com.mx/la-prensa/metropoli/apoyo-a-embarazadas-en-cdmx-registrate-por-whatsapp-y-recibe-hasta-4-mil-800-pesos-33185861",
        "description": "La Prensa informó que el programa Mujeres Sanas e Infancias Protegidas mantiene abierta la incorporación de mujeres embarazadas residentes en la Ciudad de México. El apoyo anunciado para 2026 es de hasta 4,800 pesos, dividido en cuatro pagos de 1,200 pesos.",
        "brief": {
            "lead": "La Prensa reportó que el programa Mujeres Sanas e Infancias Protegidas mantiene abierto el registro para mujeres embarazadas en CDMX y contempla hasta 4,800 pesos durante 2026, entregados en cuatro ministraciones de 1,200 pesos.",
            "context": "La nota señala que el programa prioriza a residentes de unidades territoriales con índices de desarrollo social bajo o muy bajo y solicita documentación que acredite residencia y embarazo.",
            "pending": "Los lugares disponibles, fechas de pago y requisitos vigentes deben confirmarse en los canales oficiales de la Secretaría de Bienestar e Igualdad Social; la nota periodística no sustituye las reglas del programa.",
            "method": "Síntesis basada en el artículo de La Prensa firmado por José Luis Pérez y publicado el 17 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=3225e4d7915c70c83136&mes=2026-11": {
        "category": "Cultura",
        "source_url": "https://www.infobae.com/mexico/2026/11/18/harry-potter-llega-al-museo-de-historia-natural-de-cdmx-para-la-ultima-noche-de-museos-de-2026/",
        "description": "Infobae informó que el Museo de Historia Natural y Cultura Ambiental realizará el 25 de noviembre una Noche de Museos inspirada en Harry Potter, con talleres, juegos y actividades presenciales de 18:00 a 20:30 horas.",
        "brief": {
            "lead": "Infobae reportó que el Museo de Historia Natural y Cultura Ambiental cerrará su calendario de Noche de Museos el miércoles 25 de noviembre con actividades inspiradas en Harry Potter, entre ellas selección de casas, elaboración de pociones, búsqueda de criaturas y talleres.",
            "context": "La jornada está programada de 18:00 a 20:30 en la Segunda Sección del Bosque de Chapultepec. La nota publica tarifas diferenciadas para la entrada y las visitas guiadas.",
            "pending": "Horarios, tarifas y disponibilidad pueden cambiar; conviene confirmarlos con el museo antes de acudir. La fotografía de la ficha es del recinto y no documenta el evento temático.",
            "method": "Síntesis basada en el artículo de Infobae firmado por Gisell Yazmin Pinzon Roldan, publicado el 18 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=b5e636680f6dd0f0df25&mes=2026-11": {
        "category": "Cultura",
        "source_url": "https://www.infobae.com/mexico/2026/11/18/m-night-shyamalan-anuncia-visita-a-cdmx-para-proyectar-remain-su-nueva-pelicula/",
        "description": "Infobae informó que M. Night Shyamalan realizará el 23 de noviembre una función especial de Remain en un Cinépolis de Miguel Ángel de Quevedo 227; el acceso se definirá mediante una dinámica en redes sociales, no por venta de boletos.",
        "brief": {
            "lead": "Infobae reportó que M. Night Shyamalan llegará a CDMX el 23 de noviembre para presentar Remain en Cinépolis de Miguel Ángel de Quevedo 227. Los pases se asignarán mediante una dinámica en redes sociales y no estarán a la venta.",
            "context": "La función especial se realizará antes del estreno comercial mexicano previsto para febrero de 2027 y la convocatoria está dirigida a personas residentes en la capital.",
            "pending": "La hora, el aforo y la asignación final de pases deben confirmarse con Cinépolis y Warner Bros. Pictures México. La foto de la ficha muestra la Cineteca Nacional como referencia cultural, no la sede de la función.",
            "method": "Síntesis basada en el artículo de Infobae firmado por Ignacio Izquierdo y publicado el 18 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=3dc6cf266cdcd563bb01&mes=2026-11": {
        "category": "Cultura",
        "source_url": "https://elpais.com/mexico/2026-11-18/m-night-shyamalan-elige-ciudad-de-mexico-para-su-primera-proyeccion-de-nunca-olvides-que-te-quiero.html",
        "description": "EL PAÍS informó que M. Night Shyamalan eligió la Ciudad de México para una función especial de Remain el 23 de noviembre y abrió una dinámica en redes sociales para asignar pases; su nota no precisa la sala ni el horario.",
        "brief": {
            "lead": "EL PAÍS reportó que Shyamalan eligió CDMX para la primera proyección de Remain el 23 de noviembre y convocó a sus seguidores a participar en una dinámica en redes para obtener pases.",
            "context": "La nota señala que el estreno comercial está previsto para febrero de 2027 y que la función especial se dirige a fans residentes en la capital.",
            "pending": "EL PAÍS no precisó sala ni horario en su publicación; esos datos no deben inferirse de otras notas. La fotografía de la ficha muestra la Cineteca Nacional como referencia cultural, no la sede confirmada.",
            "method": "Síntesis basada en el artículo de EL PAÍS firmado por Darinka Rodríguez y publicado el 18 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=3ba1e63aebcbe83062ef&mes=2026-11": {
        "source": "Eje Central",
        "source_url": "https://www.ejecentral.com.mx/nuestro-eje/gallinas-gratis-en-cdmx-asi-funcionara-el-programa-de-brugada-para-producir-huevo-en-casa",
        "description": "Eje Central informó que Gallinas en Casa busca impulsar la producción doméstica de huevo mediante la entrega de gallinas ponedoras a familias con espacio adecuado, principalmente en zonas rurales de la Ciudad de México. La jefa de Gobierno señaló que habrá asesoría técnica; al publicarse la nota aún no se habían detallado fechas de inscripción, requisitos específicos ni número de hogares beneficiarios.",
        "brief": {
            "lead": "Eje Central reportó que Gallinas en Casa contempla entregar gallinas ponedoras a familias con espacio suficiente para instalar un corral, principalmente en zonas rurales de CDMX. La jefa de Gobierno dijo que el objetivo es producir huevo para autoconsumo y fortalecer la soberanía alimentaria; también se prevé asesoría técnica.",
            "context": "El programa se coordinará con Casa Ecológica, que incluye captación de lluvia, calentadores solares y huertos. La iniciativa puede llegar a viviendas urbanas si cuentan con condiciones adecuadas para mantener las aves.",
            "pending": "Al momento de la publicación no se habían anunciado fechas de registro, requisitos específicos ni número de hogares beneficiarios. No debe presentarse como convocatoria abierta ni como entrega ya realizada.",
            "method": "Síntesis editorial basada en el artículo de Eje Central publicado el 18 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=b146b3d1dafcb65af69e&mes=2026-11": {
        "category": "Movilidad",
        "source": "López-Dóriga Digital",
        "source_url": "https://lopezdoriga.com/nacional/ya-debes-emplacar-tu-bici-electrica-o-scooter-cdmx-pospone-multas-y-anunciara-nueva-fecha/",
        "description": "López-Dóriga Digital informó que Semovi y la Secretaría de Seguridad Ciudadana ampliaron hasta nuevo aviso el plazo para registrar y emplacar vehículos eléctricos personales. Clara Brugada señaló que hay alrededor de 13 mil usuarios registrados y que la prórroga busca ampliar el padrón; el titular de Semovi informará sobre el proceso.",
        "brief": {
            "lead": "López-Dóriga Digital reportó que Semovi y SSC ampliaron hasta nuevo aviso el plazo para registrar y emplacar vehículos eléctricos personales. La jefa de Gobierno dijo que hay alrededor de 13 mil usuarios registrados y que la prórroga busca ampliar el padrón.",
            "context": "Los vehículos motorizados eléctricos personales que superan los 25 km/h requieren placas, tarjeta de circulación y licencia A1 o A2. Los vehículos eléctricos personales de menor potencia y velocidad deben obtener el Distintivo de Movilidad Eléctrica, según la clasificación explicada en la nota.",
            "pending": "La publicación no fija una nueva fecha límite ni una fecha de entrada en vigor de las multas; la prórroga se anunció hasta nuevo aviso. No debe presentarse una fecha de vencimiento que la autoridad todavía no comunicó.",
            "method": "Síntesis editorial basada en el artículo de López-Dóriga Digital publicado el 18 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=486d289d63499706dd71&mes=2026-11": {
        "category": "Movilidad",
        "source": "88.9 Noticias",
        "source_url": "https://889noticias.mx/noticias/semovi-cdmx-otorga-prorroga-indefinida-para-emplacamiento-de-vehiculos-electricos/",
        "description": "88.9 Noticias informó que Semovi amplió hasta nuevo aviso el plazo para registrar y emplacar los Vehículos de Movilidad Eléctrica Personal. La prórroga se anunció el 17 de noviembre, después de las manifestaciones de usuarios en Insurgentes contra el emplacamiento y las restricciones para circular por el carril ciclista. La nota no fija una nueva fecha límite.",
        "brief": {
            "lead": "88.9 Noticias reportó que Semovi extendió hasta nuevo aviso el plazo para registrar y emplacar los VEMEPE. La decisión se anunció después de las protestas de usuarios en Insurgentes; las autoridades no comunicaron una nueva fecha de vencimiento.",
            "context": "La regulación continúa vigente; la prórroga busca dar tiempo a los propietarios para completar el trámite. La nota no indica que la obligación haya sido cancelada.",
            "pending": "No se ha publicado una nueva fecha límite ni una fecha de aplicación de multas; la ampliación se anunció hasta nuevo aviso.",
            "method": "Síntesis editorial basada en el artículo de 88.9 Noticias publicado el 17 de noviembre de 2026; no equivale a verificación independiente."
        }
    },
    "/noticias/?id=61a29006a0c0e622c2f4&mes=2026-11": {
        "category": "Movilidad"
    },
    "/noticias/?id=c90abc294def53836a1f&mes=2026-11": {
        "category": "Movilidad"
    },
}
PHOTO_CREDIT_OVERRIDES = {
    "contexto_repartidores_motocicleta_cdmx": {
        "author": "Palacio de Correos de Mexico",
        "topic": "Carteros en motocicleta del Servicio Postal Mexicano, Ciudad de México (2013); imagen representativa de reparto en motocicleta, no del hecho actual"
    },
    "contexto_concierto_foro_sol_2023": {
        "topic": "Concierto de Muse en Foro Sol (hoy Estadio GNP), CDMX (23/01/2023); fotografía de archivo representativa de música en vivo, no corresponde a Garbage en el Zócalo ni al concierto sinfónico de Crepúsculo.",
        "context": "Fotografía de archivo de un concierto de Muse en Foro Sol; representa un espectáculo musical en CDMX, no documenta los eventos mencionados en las noticias.",
        "adaptation": "Miniatura oficial de Wikimedia Commons; sin modificación."
    },
    "contexto_teatro_metropolitan_2019": {
        "topic": "Teatro Metropólitan, Centro Histórico de CDMX (archivo 2019); fotografía del recinto como contexto cultural, no documenta la cartelera ni los conciertos del 18 de noviembre de 2026.",
        "adaptation": "Fotografía del recinto tomada el 19 de enero de 2019; imagen de contexto cultural, no documenta los eventos anunciados."
    },
}
VERIFIED_SOURCE_LINKS = {
    ("El Sol de México", "/noticias/?id=25c1757a6412faa605b8&mes=2026-11"):
        "https://oem.com.mx/elsoldemexico/metropoli/en-cdmx-15-colonias-de-6-alcaldias-concentran-denuncias-por-maltrato-animal-33109336",
    ("La Prensa", "/noticias/?id=8d8d42da02716a380ef2&mes=2026-11"):
        "https://oem.com.mx/la-prensa/metropoli/cdmx-busca-modernizar-la-atencion-prehospitalaria-con-plataforma-digital-de-la-ops-oms-inicia-prueba-piloto-con-tres-am-33136134",
    ("El Sol de San Juan del Río", "/noticias/?id=b37ba45fa2fa424b73bd&mes=2026-11"):
        "https://oem.com.mx/elsoldesanjuandelrio/policiaca/toma-precauciones-si-viajas-a-la-cdmx-autopista-57-esta-detenida-33095499",
    ("La Prensa", "/noticias/?id=00c19362c5f0468f82b1&mes=2026-11"):
        "https://oem.com.mx/la-prensa/policiaca/detienen-a-otro-presunto-maltratador-de-animales-en-tlalpan-33095643",
    ("La Prensa", "/noticias/?id=48ad03698ec605252a33&mes=2026-11"):
        "https://oem.com.mx/la-prensa/policiaca/mueren-dos-motociclistas-tras-chocar-contra-una-camioneta-en-venustiano-carranza-33118910",
    ("Sociedad Noticias", "/noticias/?id=edc8b9a3e45a18bf29ed&mes=2026-11"):
        "https://sociedad-noticias.com/2026/11/14/mueren-dos-motociclistas-tras-accidente-vial-en-venustiano-carranza/",
    ("N+", "/noticias/?id=0a3abec9941a9ad3518e&mes=2026-11"):
        "https://www.nmas.com.mx/ciudad-de-mexico/seguridad/asesinatos/asesinan-a-un-hombre-y-un-nino-de-10-anos-en-alcaldia-azcapotzalco-en-la-cdmx/",
    ("N+", "/noticias/?id=773453000efee780c489&mes=2026-11"):
        "https://www.nmas.com.mx/ciudad-de-mexico/seguridad/asesinan-a-balazos-a-un-hombre-y-a-un-menor-de-10-anos-en-azcapotzalco/",
    ("Ahora Noticias", "/noticias/?id=b06fd20ab5be9a500323&mes=2026-11"):
        "https://ahoranoticias.com.mx/nacional/rescatan-a-perrita-por-presunto-maltrato-animal-en-tlalpan/",
    ("Infobae", "/noticias/?id=086a68086514ac4b9e44&mes=2026-11"):
        "https://www.infobae.com/mexico/2026/11/12/detienen-a-presunto-abusador-sexual-de-animales-en-situacion-de-calle-en-cdmx-activistas-piden-que-las-investigaciones-lleguen-a-fondo/",
    ("Infobae", "/noticias/?id=8e02d29b62c66ba3eff6&mes=2026-11"):
        "https://www.infobae.com/mexico/2026/11/13/maria-leon-presento-su-nueva-era-de-villana-en-el-teatro-metropolitan-de-la-cdmx-entre-invitados-nostalgia-y-canciones-ineditas/",
    ("sdpnoticias", "/noticias/?id=842f4c3306f51b3ab9fc&mes=2026-11"):
        "https://www.sdpnoticias.com/estados/cdmx/mauricio-tabe-presenta-su-quinto-informe-de-gobierno-en-miguel-hidalgo/",
    ("Capital CDMX", "/noticias/?id=74914aa9a2dc0fd99b2f&mes=2026-11"):
        "https://capital-cdmx.org/presupuesto-cuidados-2027-cdmx-cuanto-dinero-llegara-anexo-31-desglose/",
    ("La Jornada", "/noticias/?id=9d50db4739705df961a7&mes=2026-11"):
        "https://www.jornada.com.mx/noticia/2026/11/13/politica/aicm-reporta-afectaciones-de-vuelos-hacia-y-desde-estados-unidos-tras-restriccion-a-operaciones-aereas",
    ("La Jornada", "/noticias/?id=3297b71001da632dcb3e&mes=2026-11"):
        "https://www.jornada.com.mx/noticia/2026/11/14/espectaculos/garbage-reune-a-mas-de-90-mil-personas-en-concierto-en-la-ciudad-de-mexico",
    ("Sociedad Noticias", "/noticias/?id=effab44940f001e64f19&mes=2026-11"):
        "https://sociedad-noticias.com/2026/11/15/garbage-reune-a-mas-de-90-mil-personas-en-el-zocalo-de-la-cdmx/",
    ("La Razón de México", "/noticias/?id=e5a213749a521cf90ee8&mes=2026-11"):
        "https://www.razon.com.mx/ciudad/2026/11/15/asisten-mas-de-90-mil-personas-a-concierto-de-garbage-en-el-zocalo-de-la-cdmx/",
    ("Hoy Tamaulipas", "/noticias/?id=5a9a1f1ebbab943a2f55&mes=2026-11"):
        "https://www.hoytamaulipas.net/notas/607182/El-Mante-presente-en-la-Asamblea-Nacional-de-Seguridad-Publica-Municipal-2025.html",
    ("El Sol de México", "/noticias/?id=6538cbdab54691ebcf27&mes=2026-11"):
        "https://oem.com.mx/elsoldemexico/metropoli/ofrecen-taller-gratuito-de-manejo-defensivo-y-preventivo-para-mujeres-en-cdmx-33130686",
    ("24-horas", "/noticias/?id=f321caba525de71a5543&mes=2026-11"):
        "https://24-horas.mx/cdmx/registro-emplacamiento-vemepe-vep-cdmx-costos-requisitos/",
    ("IMER Noticias", "/noticias/?id=cad284585f539df643d2&mes=2026-11"):
        "https://noticias.imer.mx/blog/activistas-y-defensores-de-animales-marcharon-para-exigir-el-fin-de-la-explotacion-animal-y-promover-el-veganismo-en-cdmx/",
    ("Maya Comunicación", "/noticias/?id=c14b74cd151a0ac26343&mes=2026-11"):
        "https://mayacomunicacion.com.mx/acta-de-nacimiento-cdmx/",
    ("Infobae", "/noticias/?id=5946c764181ff026c127&mes=2026-11"):
        "https://www.infobae.com/mexico/2026/11/17/concierto-tributo-a-depeche-mode-en-la-cdmx-horario-fecha-y-sede-del-evento-gratuito/",
}

VERIFIED_SOURCE_URLS = frozenset({
    "https://www.infobae.com/mexico/2026/11/15/garbage-en-el-zocalo-de-la-cdmx-asi-puedes-seguir-el-concierto-en-vivo-de-manera-gratuita/",
    "https://oem.com.mx/esto/futbol-americano/aficionados-de-san-francisco-49ers-en-cdmx-hablan-de-la-rivalidad-contra-dallas-cowboys-33151840",
    "https://www.infobae.com/mexico/2026/11/16/que-le-paso-a-karol-g-filtran-la-supuesta-enfermedad-que-la-habria-obligado-a-posponer-su-concierto-en-la-cdmx/",
    "https://www.infobae.com/mexico/2026/11/15/karol-g-en-cdmx-reprograma-su-concierto-de-hoy-domingo-15-de-noviembre-por-motivos-de-salud/",
    "https://www.infobae.com/mexico/2026/11/15/asi-esta-la-calidad-del-aire-de-la-cdmx-y-edomex-este-15-de-noviembre/",
    "https://www.billboard.com/espanol/noticias/karol-g-posterga-concierto-en-mexico-nueva-fecha-1236382613/",
    "https://elcongresista.mx/politica/cdmx/gobierno-cdmx-operativo-el-buen-fin",
    "https://www.tvazteca.com/aztecanoticias/vas-a-salir-por-el-puente-estos-autos-no-podran-circular-el-lunes-16-de-noviembre/",
    # URLs originales curadas para las fichas SEO del 16 de noviembre de 2026.
    "https://capital-cdmx.org/colonias-mas-denuncias-cuajimalpa-de-morelos-capital-ayuda-2026/",
    "https://capital-cdmx.org/colonias-mas-denuncias-venustiano-carranza-capital-ayuda-2026/",
    "https://elpais.com/mexico/2026-11-16/el-desfile-de-la-revolucion-en-ciudad-de-mexico-horario-ruta-y-contingentes.html",
    "https://www.sopitas.com/noticias/discriminacion-cdmx-copred-edis-2026/",
    "https://www.sopitas.com/musica/mural-gorillaz-mexico/",
    "https://www.tvazteca.com/aztecanoticias/desfile-del-20-de-noviembre-en-cdmx-ruta-horarios-y-alternativas-viales-por-cortes-a-la-circulacion/?outputType=amp",
    "https://www.diariodemorelos.com/noticias/reportan-trafico-intenso-en-mexico-acapulco-rumbo-cdmx-estos-son-puntos-afectados",
    "https://www.debate.com.mx/cdmx/inauguran-ruta-del-maiz-en-cdmx-conectara-topilejo-con-la-joya-por-4-pesos-20261116-0230.html",
    "https://www.debate.com.mx/cdmx/gallinas-ponedoras-en-cdmx-asi-sera-el-programa-de-apoyo-anunciado-por-clara-brugada-20261116-0225.html",
    "https://www.infobae.com/mexico/deportes/2026/11/16/america-femenil-se-saldria-de-la-cdmx-para-las-semifinales-ante-pumas-del-apertura-2026/",
    "https://mayacomunicacion.com.mx/acta-de-nacimiento-cdmx/",
    "https://mayacomunicacion.com.mx/cdmx-se-suma-al-frente-interestatal-de-seguridad-del-centro-del-pais/",
    "https://www.infobae.com/mexico/2026/11/17/concierto-tributo-a-depeche-mode-en-la-cdmx-horario-fecha-y-sede-del-evento-gratuito/",
    "https://voxpopulinoticias.com.mx/2026/11/belinda-recuerda-su-infancia-tras-cantar-con-karol-g-en-cdmx/",
    "https://oem.com.mx/la-prensa/finanzas/cuatro-alcaldias-concentran-77-4-por-ciento-del-valor-economico-de-cdmx-33177847",
    "https://oem.com.mx/la-prensa/metropoli/nancy-nunez-pide-casi-3-mil-millones-de-pesos-para-azcapotzalco-en-2027-33182113",
    "https://sociedad-noticias.com/2026/11/18/motociclistas-repartidores-acuerdan-dialogo-con-autoridades-de-la-cdmx/",
    "https://capital-cdmx.org/mas-de-1500-deportistas-participan-en-desfile-por-la-revolucion-mexicana-en-magdalena-contreras/",
    # Fuente directa de A21, consultada y cotejada para la ruta Aeroméxico–Montego Bay.
    "https://a21.com.mx/aerolineas/2026/11/18/conectara-aeromexico-ciudad-de-mexico-con-montego-bay-jamaica/",
    # Fuente directa de REPORTUR, consultada y cotejada para la carta de intención turística CDMX–Yucatán.
    "https://www.reportur.com/agencias/2026/11/18/cdmx-y-yucatan-mejoraran-su-imagen-y-diversificaran-mercados/",
    # Fuentes directas verificadas para las correcciones editoriales del 18 de noviembre de 2026.
    "https://www.jornada.com.mx/2026/11/18/capital/028n1cap",
    "https://oem.com.mx/la-prensa/metropoli/apoyo-a-embarazadas-en-cdmx-registrate-por-whatsapp-y-recibe-hasta-4-mil-800-pesos-33185861",
    "https://www.infobae.com/mexico/2026/11/18/harry-potter-llega-al-museo-de-historia-natural-de-cdmx-para-la-ultima-noche-de-museos-de-2026/",
    "https://www.infobae.com/mexico/2026/11/18/m-night-shyamalan-anuncia-visita-a-cdmx-para-proyectar-remain-su-nueva-pelicula/",
    "https://elpais.com/mexico/2026-11-18/m-night-shyamalan-elige-ciudad-de-mexico-para-su-primera-proyeccion-de-nunca-olvides-que-te-quiero.html",
    # Fuente directa verificada para el programa Gallinas en Casa, publicada por Eje Central el 18/11/2026.
    "https://www.ejecentral.com.mx/nuestro-eje/gallinas-gratis-en-cdmx-asi-funcionara-el-programa-de-brugada-para-producir-huevo-en-casa",
    # Fuente directa verificada para la prórroga de registro de scooters y bicis eléctricas, 18/11/2026.
    "https://lopezdoriga.com/nacional/ya-debes-emplacar-tu-bici-electrica-o-scooter-cdmx-pospone-multas-y-anunciara-nueva-fecha/",
    # Fuente directa verificada de 88.9 Noticias sobre la prórroga de emplacamiento, 17/11/2026.
    "https://889noticias.mx/noticias/semovi-cdmx-otorga-prorroga-indefinida-para-emplacamiento-de-vehiculos-electricos/",
})
SENSITIVE_MEDIA_TITLE = re.compile(
    r"\b(?:violaci[oó]n|abuso sexual|agresi[oó]n sexual|acoso sexual|violencia sexual|"
    r"maltrato animal|maltratador(?:es)? de animales?|abusador(?:es)? sexual(?:es)? de animales?|"
    r"crueldad animal|tortura animal|violencia contra animales?|"
    r"agresi[oó]n contra animales?|"
    r"(?:matar|matan|mat[oó]|mataron|asesinar|asesinan|asesin[oó]|"
    r"envenenar|envenenan|envenen[oó]|golpear|golpean|golpe[oó])\s+(?:a\s+(?:(?:los|las|un|una|unos|unas)\s+)?)?"
    r"(?:perros?|perritos?|gatos?|mascotas?|animales?)|"
    r"(?:perros?|perritos?|gatos?|mascotas?|animales?)\s+(?:maltratad[oa]s?|envenenad[oa]s?)|"
    r"envenenamiento de (?:perros?|perritos?|gatos?|mascotas?|animales?))\b",
    re.IGNORECASE,
)

def is_animal_abuse_statistics_report(item):
    title = str(item.get("title") or "").casefold()
    return (
        str(item.get("date") or "")[:10] == "2026-11-15"
        and item.get("source") == "El Sol de México"
        and bool(re.search(r"\b15 colonias de 6 alcald[ií]as concentran denuncias por maltrato animal\b", title))
    )


def is_sensitive_media(item):
    """Evita ilustraciones genéricas en incidentes violentos, no en reportajes estadísticos no gráficos."""
    if item.get("editorial_verified") is not True and is_animal_abuse_statistics_report(item):
        return False
    if item.get("sensitive_media") is True:
        return True
    return bool(SENSITIVE_MEDIA_TITLE.search(str(item.get("title") or "")))

def has_verified_event_photo(photo):
    return (isinstance(photo, dict) and photo.get("kind") == "hecho" and
            photo.get("verified") is True and bool(photo.get("evidence_url")))

def esc(value):
    return html.escape(str(value or ""), quote=True)

def article_id(item):
    match = re.fullmatch(r"/noticias/\?id=([a-f0-9]{20})&mes=\d{4}-\d{2}", item.get("local_url", ""))
    return match.group(1) if match else None

def render_photo(item):
    photo = EDITORIAL_PHOTO_OVERRIDES.get(item.get("local_url")) or item.get("photo")
    if not isinstance(photo, dict):
        return ""
    if is_sensitive_media(item) and not has_verified_event_photo(photo):
        return ""
    image_url = str(photo.get("url") or "")
    # HTTPS remoto o ruta local absoluta sin segmentos de recorrido ni URL de protocolo.
    parsed_image = urlparse(image_url)
    local_image = (image_url.startswith(("/assets/fotos/", "/assets/alcaldias/")) and
                   not image_url.startswith("//") and
                   not parsed_image.scheme and not parsed_image.netloc and
                   not parsed_image.query and not parsed_image.fragment and
                   all(part not in (".", "..") for part in parsed_image.path.split("/")) and
                   re.fullmatch(r"/assets/(?:fotos|alcaldias)/[a-zA-Z0-9_./-]+", parsed_image.path) is not None)
    if parsed_image.scheme != "https" and not local_image:
        return ""
    caption = "Imagen representativa; no corresponde necesariamente al hecho." if photo.get("kind") == "representativa" else "Fotografía asociada a la noticia."
    author = str(photo.get("author") or "Autor no identificado")
    license_name = str(photo.get("license") or "Licencia no especificada")
    credit = esc(author) + " · " + esc(license_name)
    license_url = str(photo.get("licenseUrl") or "")
    source_url = str(photo.get("source") or "")
    if urlparse(license_url).scheme == "https":
        credit += ' · <a href="' + esc(license_url) + '" rel="noopener noreferrer">Ver licencia</a>'
    if urlparse(source_url).scheme == "https":
        credit += ' · <a href="' + esc(source_url) + '" rel="noopener noreferrer">Origen de la imagen</a>'
    photo_topic = str(photo.get("topic") or "").strip()
    alt_text = photo_topic or (
        "Imagen representativa de Ciudad de México"
        if photo.get("kind") == "representativa"
        else "Fotografía relacionada con la noticia"
    )
    return ('<figure class="article-photo"><img src="' + esc(image_url) + '" alt="' +
            esc(alt_text) +
            '" loading="lazy" decoding="async" style="max-width:100%;height:auto">' +
            '<figcaption>' + esc(caption) + ' Crédito: ' + credit + '</figcaption></figure>')

def render(item, ident):
    title = esc(item["title"])
    photo_html = render_photo(item)
    if is_sensitive_media(item) and not photo_html:
        photo_html = '<p class="photo-notice">Sin fotografía verificada del hecho; no se utilizan imágenes de otros sucesos.</p>'
    brief = item.get("brief") or {}
    lead = esc(brief.get("lead") or item.get("description") or "")
    context = esc(brief.get("context") or "Consulta las fuentes y los avisos oficiales.")
    pending = esc(brief.get("pending") or "Los detalles requieren confirmación independiente.")
    method = esc(brief.get("method") or "Resumen basado en información atribuida a la fuente.")
    source = esc(item.get("source") or "Fuente identificada")
    date = esc(item.get("date") or "")
    # No presentar como CDMX una nota archivada cuya ubicación externa está confirmada.
    location = str(item.get("location") or "")
    location_label = esc(location or "CDMX")
    url = BASE + "/articulos/" + ident + "/"
    verified_source = VERIFIED_SOURCE_LINKS.get((item.get("source"), item.get("local_url")))
    original = item.get("source_url") or verified_source or item.get("url") or ""
    source_link = ""
    origin = urlparse(original)
    allowed_hosts = ("news.google.com", "commons.wikimedia.org")
    curated_hosts = ("comova.mx", "mayacomunicacion.com.mx", "www.elgrafico.mx")
    authorized = (origin.hostname in allowed_hosts or
                  (item.get("editorial_verified") is True and
                   origin.hostname in curated_hosts and origin.path != "/") or
                  (verified_source is not None and original == verified_source) or
                  original in VERIFIED_SOURCE_URLS)
    if origin.scheme == "https" and not origin.username and not origin.password and authorized:
        source_link = '<p class="source-top"><span>Fuente: ' + source + '</span> <a class="source-action" href="' + esc(original) + '" target="_blank" rel="nofollow noopener noreferrer">Ver fuente original ↗</a></p>'
    structured = json.dumps({"@context":"https://schema.org","@type":"NewsArticle","headline":item["title"],"datePublished":item.get("published_at") or item.get("date"),"author":{"@type":"Organization","name":"CDMX AL MEMENTO"},"publisher":{"@type":"Organization","name":"CDMX AL MEMENTO"},"mainEntityOfPage":url},ensure_ascii=False).replace("<","\\u003c")
    return f"""<!doctype html><html lang="es-MX"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | CDMX AL MEMENTO</title><meta name="description" content="{esc(brief.get('lead') or item.get('description') or '')[:155]}">
<link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:title" content="{title}">
<meta property="og:description" content="{lead[:155]}"><meta property="og:url" content="{url}">
<link rel="stylesheet" href="/styles.css"><style>.source-top{{display:flex;flex-wrap:wrap;align-items:center;gap:.65rem;padding:1rem;border-left:4px solid #de3186;background:rgba(222,49,134,.08);border-radius:12px}}.source-action{{display:inline-block;padding:.65rem 1rem;background:#ca2378;color:white!important;border-radius:999px;font-weight:700;text-decoration:none}}.article-photo img{{border-radius:14px}}.byline{{font-weight:700;color:#bc2778}}</style><script type="application/ld+json">{structured}</script></head>
<body><header><div class="wrap"><a href="/">CDMX AL MEMENTO</a> · <a href="/noticias/">Noticias</a></div></header>
<main class="wrap" id="contenido"><article>{source_link}<p>{location_label} · {date} · Fuente: {source}</p><h1>{title}</h1><p class="byline">Resumen y redacción: Amau Kisumi · CDMX AL MEMENTO</p>
{photo_html}<h2>Qué ocurrió y qué se sabe</h2><p>{lead}</p><h2>Por qué importa</h2><p>{context}</p><h2>Qué falta por confirmar</h2><p>{pending}</p>
<h2>Fuentes y método</h2><p>{method}</p><p>Esta síntesis no equivale a una verificación independiente de los hechos.</p>
<p><a href="{esc(item['local_url'])}">Ver noticia y comentarios en el periódico</a></p></article></main>
<footer><div class="wrap"><a href="/">Portada</a> · <a href="/politica-editorial.html">Política editorial</a></div></footer></body></html>"""

def recent_article_links(articles, limit=12):
    """Build crawlable recent links without repeating a known event."""
    limit = max(0, int(limit))
    if not limit:
        return []
    links = []
    seen_ids = set()
    for item in dedupe_homepage_events(articles):
        ident = article_id(item)
        if not ident or not item.get("title") or ident in seen_ids:
            continue
        seen_ids.add(ident)
        links.append((ident, item["title"]))
        if len(links) >= limit:
            break
    return links


def apply_editorial_record_overrides(records):
    """Keep archive records aligned with verified SEO photo and editorial overrides."""
    if not isinstance(records, list):
        raise RuntimeError("Formato de archivo mensual inválido")
    changed_records = 0
    for item in records:
        if not isinstance(item, dict):
            continue
        changed = False
        local_url = str(item.get("local_url") or "")
        photo_override = EDITORIAL_PHOTO_OVERRIDES.get(local_url)
        if photo_override and item.get("photo") != photo_override:
            item["photo"] = dict(photo_override)
            changed = True
        article_override = EDITORIAL_ARCHIVE_OVERRIDES.get(local_url)
        if article_override:
            for key, value in article_override.items():
                if item.get(key) != value:
                    item[key] = value
                    changed = True
        photo = item.get("photo")
        if isinstance(photo, dict):
            credit_override = PHOTO_CREDIT_OVERRIDES.get(photo.get("id"))
            if credit_override:
                for key, value in credit_override.items():
                    if photo.get(key) != value:
                        photo[key] = value
                        changed = True
        if changed:
            changed_records += 1
    return changed_records


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    articles = data.get("articles") or []
    feed_changed = apply_editorial_record_overrides(articles)
    if feed_changed:
        SOURCE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Applied editorial overrides to {feed_changed} current feed records")
    # Incluir hemeroteca: news.json solo contiene las noticias más recientes.
    manifest = ROOT / "archivo" / "meses.json"
    if manifest.is_file():
        months = json.loads(manifest.read_text(encoding="utf-8")).get("months", [])
        for month in months:
            month_name = month.get("month", "")
            if not re.fullmatch(r"\d{4}-\d{2}", month_name):
                continue
            archive_path = ROOT / "archivo" / (month_name + ".json")
            if not archive_path.is_file():
                raise RuntimeError("Archivo mensual ausente: " + str(archive_path))
            archived_data = json.loads(archive_path.read_text(encoding="utf-8"))
            if isinstance(archived_data, dict):
                archive_key = next(
                    (key for key in ("articles", "news", "items")
                     if isinstance(archived_data.get(key), list)),
                    None,
                )
                if archive_key is None:
                    raise RuntimeError("Formato de archivo mensual inválido: " + month_name)
                archived = archived_data[archive_key]
            elif isinstance(archived_data, list):
                archived = archived_data
            else:
                raise RuntimeError("Formato de archivo mensual inválido: " + month_name)
            changed_records = apply_editorial_record_overrides(archived)
            if changed_records:
                archive_path.write_text(
                    json.dumps(archived_data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(
                    f"Applied editorial archive overrides to {changed_records} "
                    f"records in {archive_path.name}"
                )
            articles.extend(archived)
    OUT.mkdir(exist_ok=True)
    urls = []
    recent_links = recent_article_links(articles, limit=12)
    seen_ids = set()
    for item in articles:
        ident = article_id(item)
        if not ident or not item.get("title"):
            continue
        if ident in seen_ids:
            continue  # La versión reciente tiene prioridad sobre la copia del archivo.
        seen_ids.add(ident)
        dest = OUT / ident
        dest.mkdir(exist_ok=True)
        (dest / "index.html").write_text(render(item, ident), encoding="utf-8")
        urls.append(BASE + "/articulos/" + ident + "/")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join("  <url><loc>" + esc(u) + "</loc></url>\n" for u in sorted(set(urls)))
    SITEMAP.write_text(xml + "</urlset>\n", encoding="utf-8")
    # Fail the workflow if any generated article or sitemap entry is missing.
    for ident in seen_ids:
        page = OUT / ident / "index.html"
        if not page.is_file() or (BASE + "/articulos/" + ident + "/") not in xml:
            raise RuntimeError("Missing generated article or sitemap URL: " + ident)
    if len(urls) != len(seen_ids):
        raise RuntimeError("Article count does not match unique identifiers")
    # Static HTML anchors are visible to crawlers without running JavaScript.
    link_html = '<ul class="seo-recent-articles">' + "".join(
        '<li><a href="/articulos/' + ident + '/">' + esc(title) + '</a></li>'
        for ident, title in recent_links
    ) + '</ul>'
    for relative in ("index.html", "archivo/index.html"):
        page = ROOT / relative
        original = page.read_text(encoding="utf-8")
        updated, replacements = re.subn(
            r"<!-- SEO_ARTICLES_START -->.*?<!-- SEO_ARTICLES_END -->",
            lambda match: "<!-- SEO_ARTICLES_START -->" + link_html + "<!-- SEO_ARTICLES_END -->",
            original, count=1, flags=re.DOTALL
        )
        if replacements != 1:
            raise RuntimeError("Missing SEO article links markers in " + relative)
        if updated != original:
            page.write_text(updated, encoding="utf-8")

    # Advertise the article sitemap only after its XML has been generated.
    robots = ROOT / "robots.txt"
    robots_text = robots.read_text(encoding="utf-8")
    article_sitemap = "Sitemap: " + BASE + "/sitemap-articulos.xml"
    if article_sitemap not in robots_text:
        robots.write_text(robots_text.rstrip() + "\n" + article_sitemap + "\n", encoding="utf-8")
    print(f"Generated {len(urls)} article pages and sitemap-articulos.xml")

if __name__ == "__main__":
    main()
