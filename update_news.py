# Ejecución puntual solicitada el 2026-11-01; la programación horaria continúa.
"""Actualizador de noticias CDMX AL MEMENTO.

Recopila titulares de RSS, los ordena por fecha de publicación verificable,
conserva copias de índices mensuales durante 365 días y los elimina al vencer.
No atribuye una alcaldía si no está mencionada de manera inequívoca en el título.
No descarga ni reproduce el cuerpo protegido de los artículos.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.analisis_editorial import build_editorial
from scripts.notas_locales import local_link, summarize, assign_photos, _photo_score, is_sensitive_media, is_coyotepec_highway_crash, INFOBAE_COYOTEPEC_HIGHWAY_CRASH_SOURCE_URL, is_san_juan_del_rio_autopista57_closure, SENSITIVE_MEDIA_TITLE, SAN_JUAN_DEL_RIO_AUTOPISTA57_SOURCE_URL, is_infobae_tlalpan_animal_abuse, is_la_prensa_tlalpan_animal_case, INFOBAE_TLALPAN_ANIMAL_SOURCE_URL, LA_PRENSA_TLALPAN_ANIMAL_SOURCE_URL, is_imagen_tlalpan_dog_rescue, is_huixtla_migrant_caravan, is_vc_fatal_trailer_incident, EL_GRAFICO_VC_TRAILER_SOURCE_URL, is_infobae_ballet_zapatilla, INFOBAE_BALLET_ZAPATILLA_SOURCE_URL, is_infobae_maria_leon_concert, INFOBAE_MARIA_LEON_CONCERT_SOURCE_URL, is_pulque_barbacoa_fair, is_mauricio_tabe_fifth_report, SDPNOTICIAS_MAURICIO_TABE_REPORT_SOURCE_URL, is_radio_formula_casa_ecologica, RADIO_FORMULA_CASA_ECOLOGICA_SOURCE_URL, is_capital_cdmx_care_budget, CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "news.json"
ARCHIVE_DIR = ROOT / "archivo"
CURATED_INCIDENTS = ROOT / "editorial" / "accidentes-verificados-2026-11.json"
CURATED_HOSTS = frozenset({"comova.mx", "mayacomunicacion.com.mx", "www.elgrafico.mx"})
BOROUGH_DIR = ROOT / "alcaldias"
REPORT_DIR = ROOT / "reportes"
REPORTS = ROOT / "reports.json"
MX = ZoneInfo("America/Mexico_City")
SITE = "https://cdmx-al-memento.pages.dev"
MAIL = "sanchezaxochitl@gmail.com"
RETENTION_DAYS = 365

def clear_sensitive_context_photos(items):
    """Retira del archivo fotos representativas de titulares sensibles."""
    removed = 0
    for item in items:
        if not isinstance(item, dict) or not is_sensitive_media(item):
            continue
        item["sensitive_media"] = True
        photo = item.get("photo")
        documented = (
            isinstance(photo, dict)
            and photo.get("kind") == "hecho"
            and photo.get("verified") is True
            and bool(photo.get("evidence_url"))
        )
        if photo and not documented:
            item.pop("photo", None)
            removed += 1
    return removed


ARCHIVE_VERSION_FIELDS = (
    "title", "description", "url", "source", "date", "published_at",
    "category", "borough", "location", "local_url", "source_url", "brief", "photo",
    "editorial_verified", "sensitive_media",
)

BOROUGHS = (
    "La Magdalena Contreras", "Álvaro Obregón", "Azcapotzalco",
    "Benito Juárez", "Coyoacán", "Cuajimalpa de Morelos",
    "Cuauhtémoc", "Gustavo A. Madero", "Iztacalco", "Iztapalapa",
    "Miguel Hidalgo", "Milpa Alta", "Tláhuac", "Tlalpan",
    "Venustiano Carranza", "Xochimilco",
)
GENERAL_FEEDS = {
    "Metro": "Metro CDMX",
    "Movilidad": "tráfico cierres viales Ciudad de México",
    "Seguridad": "seguridad Ciudad de México",
    "Cultura": "eventos culturales Ciudad de México",
    "Gobierno": "gobierno Ciudad de México",
    "CDMX": "noticias Ciudad de México",
}
# Cobertura vecinal: buscar el hecho en medios, sin importar posts sin verificar.
LOCAL_EVENT_QUERIES = (
    "CDMX inundaciones encharcamientos lluvias protección civil",
    "CDMX incendio fuga de gas choque emergencia",
    # Accidentes viales: cobertura específica sin excluir hechos con víctimas.
    "CDMX motociclista accidente moto derrape choque",
    "CDMX choque volcadura atropellamiento colisión vial",
    "CDMX accidente carretera motocicleta lesionados fallecidos",
    "CDMX colonias falta de agua cierre vial vecinos",
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CDMXAlMemento/2.0; news aggregator)"}
SOCIAL_SOURCES = {
    "facebook", "instagram", "tiktok", "youtube", "twitter", "x.com", "threads",
    "reddit", "pinterest", "whatsapp", "telegram", "linkedin", "kwai",
}
JUNK = re.compile(r"https?://|www\.|\b(?:bit\.ly|tinyurl\.com|mile\.io|t\.co)/", re.I)
SPACES = re.compile(r"\s+")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
# Texto mencionado en un titular: no equivale a la ubicación verificada del incidente.
ALIASES = {
    "La Magdalena Contreras": ("la magdalena contreras", "magdalena contreras"),
    "Álvaro Obregón": ("alvaro obregon",),
    "Azcapotzalco": ("azcapotzalco",),
    "Benito Juárez": ("benito juarez",),
    "Coyoacán": ("coyoacan",),
    "Cuajimalpa de Morelos": ("cuajimalpa de morelos", "cuajimalpa"),
    "Cuauhtémoc": ("cuauhtemoc",),
    "Gustavo A. Madero": ("gustavo a madero", "gustavo a. madero"),
    "Iztacalco": ("iztacalco",),
    "Iztapalapa": ("iztapalapa",),
    "Miguel Hidalgo": ("miguel hidalgo",),
    "Milpa Alta": ("milpa alta",),
    "Tláhuac": ("tlahuac",),
    "Tlalpan": ("tlalpan",),
    "Venustiano Carranza": ("venustiano carranza",),
    "Xochimilco": ("xochimilco",),
}


def clean(value):
    value = re.sub(r"<[^>]*>", "", html.unescape(str(value or "")))
    return SPACES.sub(" ", value).strip()


def fold(value):
    value = unicodedata.normalize("NFKD", clean(value).casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def outside_cdmx_location(title):
    """Identifica solo hechos con lugar externo inequívoco en el titular."""
    words = " " + fold(title) + " "
    # fold() elimina la puntuación: el verbo "exigen" identifica la segunda
    # cláusula y distingue la protesta en Xalapa de las referencias a Puebla/CDMX.
    if (re.search(r"\bprotest\w*\s+en\s+xalapa\s+exigen\b", words)
            and re.search(r"\b(?:puebla|cdmx|ciudad de mexico)\b", words)):
        return "Xalapa, Veracruz"
    # Un titular turístico sobre fincas de Veracruz puede mencionar CDMX solo
    # como referencia de distancia; eso no convierte el lugar en noticia local.
    if (re.search(r"\bfincas? de cafe de veracruz\b", words)
            and (not re.search(r"\b(?:cdmx|ciudad de mexico)\b", words)
                 or re.search(r"\ba \d+ horas?(?: y media)? de (?:cdmx|ciudad de mexico)\b", words))):
        return "Veracruz"
    # Meganoticias (01-11-2026): esta asamblea de autoridades auxiliares
    # ocurrió en la agencia municipal de Juchitán, Oaxaca, no en la alcaldía
    # homónima de CDMX. La coincidencia exacta evita excluir otras asambleas.
    if (re.search(r"\basamblea comunitaria determina relevo de autoridades auxiliares en alvaro obregon\b", words)
            and not re.search(r"\b(?:cdmx|ciudad de mexico)\b", words)):
        return "Álvaro Obregón, Juchitán, Oaxaca"
    # Mantener titulares que sí mencionen CDMX junto a otras regiones.
    if any(" " + name + " " in words for name in ("cdmx", "ciudad de mexico")):
        return ""
    if " carretera a laredo " in words and " escobedo " in words:
        return "Escobedo, Nuevo León"
    # Estas referencias geográficas son externas, aunque el RSS proceda
    # de una búsqueda sobre la capital. Conservar la noticia en el archivo.
    if " carretera federal 307 " in words:
        return "Carretera federal 307, sureste de México"
    if " madrid sevilla " in words:
        return "España"
    if " en chihuahua " in words:
        return "Chihuahua"
    if " en uruapan " in words:
        return "Uruapan, Michoacán"
    # Un accidente ocurrido en España no es una incidencia vial de CDMX,
    # aunque el medio mencione a personas mexicanas afectadas.
    if re.search(r"\b(?:accidente|choque|descarrilamiento)\b.{0,90}\ben espana\b", words):
        return "España"
    return ""


def outside_cdmx_scope(title):
    return bool(outside_cdmx_location(title))


def identify_location(title, date=None):
    words = " " + fold(title) + " "
    # Infobae confirma la sede de La Zapatilla de Cristal en Utopía Mixiuhca, Iztacalco.
    if " zapatilla de cristal " in words and " ballet " in words:
        return "Iztacalco", (
            "Utopía Mixiuhca, Viaducto Río de la Piedad 6, colonia Granjas México, "
            "Iztacalco, Ciudad de México"
        )
    # Infobae y POSTA coinciden en la sede de la Feria del Pulque y la Barbacoa.
    if " feria " in words and " pulque " in words and " barbacoa " in words:
        return "La Magdalena Contreras", (
            "Explanada de la Alcaldía La Magdalena Contreras, José Moreno Salido s/n, "
            "colonia Barranca Seca, Ciudad de México"
        )
    # La Línea 1 del Cablebús opera entre Indios Verdes y Cuautepec, en Gustavo A. Madero.
    if " cablebus " in words and " linea 1 " in words:
        return "Gustavo A. Madero", "Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús)"
    # La volcadura del 12 de noviembre ocurrió en Santa María Totoltepec,
    # Toluca; la afectación vial fue hacia CDMX, no dentro de una alcaldía capitalina.
    if (date == "2026-11-12"
            and " paseo tollocan " in words
            and " pipa " in words
            and re.search(r"\b(?:volcadur|vuelc)\w*\b", words)):
        return "", "Santa María Totoltepec, Toluca, Estado de México (fuera de CDMX)"
    if (date in {"2026-11-11", "2026-11-12"}
            and " pipa " in words and " mexico pachuca " in words):
        return "", "Ecatepec, Estado de México (fuera de CDMX)"
    external = outside_cdmx_location(title)
    if external:
        return "", external + " (fuera de CDMX)"
    words = " " + fold(title) + " "
    found = []
    for borough, aliases in ALIASES.items():
        for alias in aliases:
            name = fold(alias)
            if " " + name + " " not in words:
                continue
            # Nombres de personajes no son automáticamente ubicaciones.
            # Exigir contexto geográfico para las alcaldías homónimas.
            if borough in ("Cuauhtémoc", "Benito Juárez", "Miguel Hidalgo",
                           "Álvaro Obregón", "Venustiano Carranza", "Gustavo A. Madero"):
                contextual_location = re.search(
                    r"\b(?:alcaldia|demarcacion|colonia|zona|delegacion|"
                    r"en la alcaldia|en la colonia|en|hacia|desde)\s+(?:de\s+)?"+re.escape(name)+r"\b",
                    words,
                )
                ranked_alcaldia = re.search(
                    r"\b" + re.escape(name) + r"\s+es\s+la\s+"
                    r"(?:primera|segunda|tercera|cuarta|quinta|sexta|septima|octava|novena|decima|\d+\.?)\s+alcaldia\b",
                    words,
                )
                if not (contextual_location or ranked_alcaldia):
                    continue
            found.append(borough)
            break
    # Si nombra varias demarcaciones no elegir una como lugar de los hechos.
    if len(found) == 1:
        return found[0], found[0] + " (mencionada en el titular)"
    if any(" " + x + " " in words for x in (
        "cdmx", "ciudad de mexico", "capital del pais"
    )):
        return "", "Ciudad de México (sin alcaldía identificada)"
    return "", "Ubicación no indicada por el titular"


def headline_has_cdmx_signal(title):
    """Exige una referencia local en el titular; la búsqueda RSS no basta.

    Google News puede devolver noticias de Chihuahua, Michoacán o España al
    buscar «Metro CDMX». Los titulares ambiguos permanecen en el histórico,
    pero no se presentan como noticias de la capital sin contexto comprobable.
    """
    if outside_cdmx_scope(title):
        return False
    words = " " + fold(title) + " "
    anchors = (
        "cdmx", "ciudad de mexico", "capital del pais", "metrobus",
        "cablebus", "ecobici", "tren suburbano", "eje central",
        "paseo de la reforma", "circuito interior", "aicm",
        "autodromo hermanos rodriguez", "central de abasto",
        "tepito",
    )
    if any(" " + anchor + " " in words for anchor in anchors):
        return True
    borough, _ = identify_location(title)
    return bool(borough)


def local_for_homepage(article):
    title = article.get("title", "")
    return (not outside_cdmx_scope(title)
            and (article.get("editorial_verified") is True
                 or headline_has_cdmx_signal(title)))


def allowed(source):
    name = clean(source).lower()
    return bool(name) and not any(
        s == name or s in name.split() for s in SOCIAL_SOURCES
    ) and not any(
        x in name for x in ("facebook.com", "instagram.com", "youtube.com", "tiktok.com", "x.com")
    )


def normalize_title(title, source):
    title = clean(title)
    if source and title.lower().endswith(" - " + source.lower()):
        title = title[: -(len(source) + 3)].strip()
    return title


def valid_link(url, editorial_verified=False):
    parts = urllib.parse.urlparse(str(url))
    if parts.scheme != "https" or parts.username or parts.password:
        return False
    if parts.hostname == "news.google.com":
        return True
    # Enlaces externos adicionales: exclusivamente fichas revisadas en el repositorio.
    return editorial_verified is True and parts.hostname in CURATED_HOSTS and bool(parts.path.strip("/"))


def published_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError, TypeError):
        return None


def category_by_headline(title, feed_category, source=""):
    """Corrige etiquetas RSS evidentes sin inventar ubicaciones o hechos."""
    normalized = fold(title)
    normalized_source = fold(source)
    # Delitos y detenciones no deben heredar una categoría de Metro o CDMX
    # por el feed RSS: robos, secuestros y maltrato animal son Seguridad.
    if re.search(
        r"\b(?:abuso sexual|violencia sexual|agresion sexual|acoso sexual|"
        r"abusador(?:es)? sexual(?:es)?|maltratador(?:es)?(?: de animales?)?|"
        r"maltrato animal|crueldad animal|robo|robos|roban|robado|robada|robaron|robar|"
        r"asalto|asaltan|secuestro|secuestrad[oa]s?|"
        r"privacion(?: ilegal)? de (?:la )?libertad)\b",
        normalized,
    ):
        return "Seguridad"
    # Conciertos, intérpretes, estrenos y alfombras de cine pertenecen a Cultura.
    if re.search(
        r"\b(?:cantantes?|cantautores?|canta|cantar|gira musical|canciones? ineditas|musica en vivo|"
        r"teatro metropolitan|alfombra|premiere|estreno|reparto|actores?|actrices?)\b",
        normalized,
    ):
        return "Cultura"
    # Las noticias sobre infraestructura escolar no deben heredar la categoría Metro del RSS.
    if re.search(
        r"\b(?:educacion|educativo|educativa|infraestructura escolar|infraestructura en primarias?|"
        r"primarias?|secundarias?|preparatorias?|planteles? escolares?|domos? escolares?|madres? de familia)\b",
        normalized,
    ):
        return "CDMX"
    # Las jornadas de adopción son información de la ciudad, no del Metro.
    if re.search(r"\b(?:caravana de adopcion|adopcion de mascotas|perritos? rescatados buscan hogar)\b", normalized):
        return "CDMX"
    # Los asuntos del Congreso y del Plan General de Desarrollo son Gobierno.
    if re.search(
        r"\b(?:congreso capitalino|congreso(?: de la| de)? cdmx|congreso de la ciudad de mexico|"
        r"asamblea legislativa|plan general de desarrollo)\b",
        normalized,
    ):
        return "Gobierno"
    # El Anexo 31 y el presupuesto federal de cuidados son materia de Gobierno.
    if re.search(r"\bpresupuesto de cuidados 2027\b", normalized):
        return "Gobierno"
    if (re.search(r"\bautopista\s+57\b", normalized)
            and re.search(r"\b(?:detenida|cerrada|bloqueada|filas?|trafico|accidentes?)\b", normalized)):
        return "Movilidad"
    # Las explosiones y fugas de gas son emergencias de Seguridad, no CDMX genérico.
    if re.search(
        r"\b(?:explosion(?:es)? de (?:un )?tanque de gas|explosion(?:es)? de gas|fugas? de gas|incendios?|estalla\s+(?:un\s+)?tanque(?:\s+de\s+gas)?)\b",
        normalized,
    ):
        return "Seguridad"
    # La agenda de NFL y fútbol americano en CDMX es deportiva, no del Metro.
    if re.search(r"\b(?:nfl|futbol americano|san francisco 49ers|minnesota vikings)\b", normalized):
        if re.search(r"\b(?:cierres? viales?|calles? cerradas?|trafico|congestionamiento|desvios?|rutas? alternas?|alternativas? viales?)\b", normalized):
            return "Movilidad"
        return "CDMX"
    # El automovilismo es deporte, no un aviso de tránsito ni del Metro.
    # Solo sus cierres y afectaciones viales pertenecen a Movilidad.
    if re.search(r"\b(?:formula 1|gp ciudad de mexico|gran premio|nascar)\b", normalized):
        if re.search(
            r"\b(?:cierres? viales?|calles? cerradas?|trafico|congestionamiento|"
            r"desvios?|rutas? alternas?|alternativas? viales?|transporte publico|"
            r"estacionamientos?)\b", normalized
        ):
            return "Movilidad"
        return "CDMX"
    # Los planes de electrificación del transporte público son materia de Movilidad.
    if (re.search(r"\b(?:transporte(?: publico)?|movilidad)\b", normalized)
            and re.search(r"\b(?:electrico|electrica|electrificacion)\b", normalized)):
        return "Movilidad"
    # La vigilancia y el alumbrado reportados por una alcaldía son asuntos de Seguridad.
    if (re.search(r"\b(?:vigilancia|alumbrado|luminarias?|vigilad[oa]s?)\b", normalized)
            and re.search(r"\b(?:tabe|miguel hidalgo)\b", normalized)):
        return "Seguridad"
    # Los festivales de cine pertenecen a Cultura.
    if re.search(r"\b(?:cine de barrio|festival(?: de)? cine)\b", normalized):
        return "Cultura"
    # Los avisos operativos del Cablebús pertenecen a Movilidad, no a CDMX genérico.
    if re.search(r"\bcablebus\b", normalized):
        return "Movilidad"
    # El estado del Metrobús pertenece a Movilidad, no a la categoría general.
    if re.search(r"\bmetrobus\b", normalized):
        return "Movilidad"
    # Fotogenia es un festival cultural; no debe quedarse en CDMX genérico.
    if re.search(r"\bfotogenia\b", normalized):
        return "Cultura"
    # El balance de cinco años de Mauricio Tabe describe gestión de una alcaldía, no un incidente de Seguridad.
    if (re.search(r"\btabe\b", normalized)
            and re.search(r"\b(?:cinco anos de cambio|cinco anos de gobierno|quinto balance|quinto informe de gobierno)\b", normalized)):
        return "Gobierno"
    # Las declaraciones del alcalde de Coyoacán sobre cambios en la demarcación son materia de Gobierno.
    if (re.search(r"\bgiovani gutierrez\b", normalized)
            and re.search(r"\b(?:cambiado|mejorado|rostro)\b", normalized)):
        return "Gobierno"
    # Los informes de la Contraloría sobre fiscalización son materia de Gobierno.
    if re.search(r"\bcontraloria\b", normalized):
        return "Gobierno"
    # Los operativos de autoridades en Plaza Meave son asuntos de Seguridad.
    if (re.search(r"\bplaza meave\b", normalized)
            and re.search(r"\b(?:operativo|decomis\w*|incaut\w*|aseguran|mercancia apocrifa|pirateria)\b", normalized)):
        return "Seguridad"
    # Los decomisos de autopartes vinculados al robo de vehículos son Seguridad.
    if (re.search(r"\b(?:decomis\w*|incaut\w*|asegur\w*)\b", normalized)
            and re.search(r"\b(?:autopartes|piezas de autos|robo de autos|vehiculos robados)\b", normalized)):
        return "Seguridad"
    # Los comunicados de la SSC sobre operativos y despliegues policiales
    # son Seguridad aunque el RSS los haya recogido en el feed del Metro.
    if (
        re.search(r"\b(?:ssc|secretaria de seguridad ciudadana)\b", normalized + " " + normalized_source)
        and re.search(r"\b(?:operativo|vigilancia|despliegue|policias?)\b", normalized)
    ):
        return "Seguridad"
    # Los recortes presupuestales de apoyos públicos a población LGBTTTIQ+ son decisiones de Gobierno.
    if (feed_category in {"CDMX", "Gobierno"}
            and re.search(r"\b(?:lgbtttiq|lgbtq?|diversidad sexual)\b", normalized)
            and re.search(r"\b(?:recorta|recorte|reduce|reduccion|disminuye|apoyo|presupuesto|beneficiarios|programa social|accion social)\b", normalized)):
        return "Gobierno"
    # Un comunicado del EZLN sobre el gobierno no es una incidencia del Metro.
    if (re.search(r"\bezln\b", normalized)
            and re.search(r"\b(?:buscadoras?|gobierno|movilizacion)\b", normalized)):
        return "Gobierno"
    # Las visitas de Día de Muertos no son delitos por mencionar "saldo blanco".
    if (re.search(r"\bdia de muertos\b", normalized)
            and re.search(r"\b(?:visitantes?|saldo blanco|conmemoracion)\b", normalized)
            and not re.search(r"\b(?:homicidio|ataques? armados?|balacera)\b", normalized)):
        return "Cultura"
    # Los grupos criminales son materia de seguridad, aunque el RSS use CDMX.
    if (feed_category in {"CDMX", "Gobierno"}
            and re.search(r"\b(?:grupos? criminales?|organizaciones? criminales?|crimen organizado)\b", normalized)):
        return "Seguridad"
    # Robos de infraestructura y bienes no deben quedarse como CDMX genérico.
    if (feed_category in {"CDMX", "Gobierno", "Cultura"}
            and re.search(r"\b(?:robo|robos|roban|robado|robada|robaron|robar)\b", normalized)
            and re.search(r"\b(?:cable|alumbrado|vehiculo|vehiculos|auto|autopartes|celular|casa|vivienda|negocio|comercio|mercancia|tienda|dinero|joyas|equipo|carga|medidor|tuberia|materiales)\b", normalized)):
        return "Seguridad"
    # Una agresión violenta no es Cultura por mencionar el Día de Muertos.
    if (feed_category in {"CDMX", "Gobierno", "Cultura"}
            and re.search(r"\b(?:ejecutan|ejecutad\w*|ejecucion|ataques? armados?|balacera|asesina(?:n)? a|asesinad\w*|asesinato)\b", normalized)):
        return "Seguridad"
    # Las agresiones por disparos se clasifican como Seguridad aunque el RSS diga CDMX.
    if (feed_category in {"CDMX", "Gobierno", "Cultura"}
            and re.search(r"\b(?:balead\w*|balear\w*|balean|baleo)\b", normalized)):
        return "Seguridad"
    # Las movilizaciones de repartidores y conductores son Movilidad,
    # salvo cuando el titular describe una amenaza o agresión concreta.
    if re.search(r"\b(?:repartidores?|conductores? de aplicacion)\b", normalized):
        security_signal = re.search(
            r"\b(?:arma|armado|ataques? armados?|amenaz\w*|vandaliz\w*|robo|asalto|detienen|homicidio|balacera|agresion)\b",
            normalized,
        )
        movement_signal = re.search(
            r"\b(?:movilizacion(?:es)?|manifestacion(?:es)?|protest\w*|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|toman|calles? cerraran|afectacion vial)\b",
            normalized,
        )
        if security_signal:
            return "Seguridad"
        if movement_signal:
            return "Movilidad"
    # Manifestaciones, plantones y concentraciones anunciadas no son delitos.
    if (re.search(r"\bmovilizaciones\b", normalized)
            and re.search(r"\b(?:hoy|plantones|concentraciones|bloqueos|marchas)\b", normalized)
            and not re.search(r"\b(?:ataques? armados?|balacera|detienen|homicidio)\b", normalized)):
        return "Movilidad"
    # Una Catrina monumental y su récord pertenecen a la agenda cultural.
    if (re.search(r"\bcatrina\b", normalized)
            and re.search(r"\b(?:monumental|record guinness|zocalo)\b", normalized)
            and not re.search(r"\b(?:ataques? armados?|balacera|detienen)\b", normalized)):
        return "Cultura"
    # Manifestaciones y plantones con calles u horarios afectados son movilidad.
    if (re.search(r"\b(?:manifestaciones|plantones|marchas)\b", normalized)
            and re.search(r"\b(?:calles|afectadas|afectacion|horarios|bloqueos)\b", normalized)):
        return "Movilidad"
    # Las marchas y concentraciones anunciadas son información vial, no un delito.
    if (re.search(r"\bmarchas?\b.*\b(?:hoy|noviembre|bloqueos?|concentraciones?)\b", normalized)
            and not re.search(r"\b(?:detienen|policias?|operativo policial|balacera|ataques? armados?)\b", normalized)):
        return "Movilidad"
    # Etiquetas editoriales inequívocas aunque el feed general use "CDMX".
    if (feed_category in {"CDMX", "Gobierno"}
            and re.search(r"\b(?:matan a balazos|asesinan a|homicidio|condenad[oa]s?|condenan|prision)\b", normalized)):
        return "Seguridad"
    if (re.search(r"\b(?:gran desfile de dia de muertos|desfile de catrinas)\b", normalized)
            and not re.search(r"\b(?:policias?|detienen|seguridad|operativo)\b", normalized)):
        return "Cultura"
    if re.search(r"\bcolectivo de busqueda\b.*\bbloquea(?:n)? avenida\b", normalized):
        return "Movilidad"
    if re.search(r"\b(?:fallece motociclista|muere motociclista|motociclistas? fallecidos?)\b", normalized):
        return "Movilidad"
    # Secuestros y privaciones de la libertad son Seguridad aunque el RSS diga CDMX.
    if re.search(r"\b(?:secuestro|secuestrador(?:es)?|secuestrad[oa]s?|privacion de la libertad)\b", normalized):
        return "Seguridad"
    # Los delitos contra empresas, comercios y negocios pertenecen a Seguridad.
    if re.search(r"\bdelitos?\s+(?:contra|a)\s+(?:empresas?|comercios?|negocios?)\b", normalized):
        return "Seguridad"
    # Una muerte por atropellamiento o arrastre de un tráiler es un siniestro vial.
    if (re.search(r"\b(?:muere|murio|fallece|fallecio)\b", normalized)
            and re.search(r"\b(?:arrastrad\w*|atropellad\w*|arrollad\w*)\b", normalized)
            and re.search(r"\b(?:trailer|tractocamion|camion)\b", normalized)):
        return "Movilidad"
    # Los trenes interurbanos y sus obras son información de Movilidad.
    if (re.search(r"\b(?:tren|ferrocarril)\b", normalized)
            and re.search(r"\b(?:pachuca|guadalajara)\b", normalized)):
        return "Movilidad"
    # Una detención de personas es seguridad, aunque el RSS venga de Gobierno.
    # Exigir "a" y una referencia humana evita confundirla con obras detenidas.
    if (feed_category in {"Gobierno", "CDMX"}
            and re.search(r"\b(?:detienen|arrestan|capturan|aprehenden)\s+a\s+(?:\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|varios|varias|hombre|mujer|sujeto|individuo|persona|joven|menor|personas|hombres|mujeres)\b", normalized)):
        return "Seguridad"
    # Una ley de movilidad es un asunto vial aunque el RSS la clasifique como Seguridad.
    if re.search(r"\bley de movilidad\b", normalized):
        return "Movilidad"
    # La restricción vehicular sigue siendo Movilidad aunque el titular mencione festividades.
    if re.search(r"\bhoy no circula\b", normalized):
        return "Movilidad"
    if re.search(r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b", normalized):
        return "Movilidad"
    # Las marchas de motociclistas son movilidad aunque el RSS provenga del feed del Metro.
    if (re.search(r"\b(?:motociclistas?|motocicletas?|motos?)\b", normalized)
            and re.search(r"\b(?:march\w*|movilizacion(?:es)?|concentraciones?|rodada|bloqueos?)\b", normalized)):
        return "Movilidad"
    # Los cierres y rutas alternas son movilidad, no operativos policiales.
    # Evitar imágenes de patrullas cuando un feed de Seguridad incluye tráfico.
    if (re.search(r"\b(?:calles cerradas|cierres? vial(?:es)?|alternativas? vial(?:es)?|rutas? alternas?|desvios? vial(?:es)?)\b", normalized)
            and not re.search(r"\b(?:balacera|homicidio|asalto|delito|detenidos?|detienen|persecucion policial)\b", normalized)):
        return "Movilidad"
    # Distinguir siniestros viales de delitos, aunque provengan de otro feed RSS.
    if re.search(r"\b(?:accidentes?|choques?|colisiones?|volcaduras?|vuelc\w*|atropell\w*|arroll\w*|derrap\w*|percances? viales?|siniestros? viales?)\b", normalized):
        if re.search(r"\b(?:homicidio|balacera|asalto|atentado|delito|persecucion policial)\b", normalized):
            return "Seguridad"
        return "Movilidad"
    if (feed_category == "Seguridad"
            and re.search(r"\b(?:robot|robots|robotica|robotico|roboticos)\b", normalized)
            and not re.search(r"\b(?:policias?|patrullas?|fiscalia|delito|detenidos?)\b", normalized)):
        return "CDMX"
    # Si el titular identifica expresamente al Gobierno de la Ciudad de México,
    # clasificarlo como Gobierno aunque el RSS lo haya agrupado en CDMX.
    # Las reglas específicas de Seguridad y Movilidad anteriores conservan prioridad.
    if (feed_category in {"CDMX", "Gobierno"}
            and re.search(r"\bgobierno de la ciudad de mexico\b", normalized)):
        return "Gobierno"
    # La agenda de artes escénicas y gastronomía no debe heredar etiquetas de Metro o CDMX.
    if re.search(r"\b(?:ballet|danza clasica|cirque du soleil|feria (?:regional )?del pulque|pulque y la barbacoa)\b", normalized):
        return "Cultura"
    # La captación pluvial y los programas de ecotecnias son iniciativas ambientales,
    # no pronósticos meteorológicos por mencionar agua de lluvia.
    if re.search(
        r"\b(?:captar agua de lluvia|captacion de agua de lluvia|captacion de lluvia|"
        r"calentadores solares|captacion pluvial|cosecha de lluvia|casa ecologica|ecotecnias?)\b",
        normalized,
    ):
        return "Medio Ambiente"
    # Los avisos de lluvia intensa pertenecen a Medio Ambiente, salvo las afectaciones de transporte ya clasificadas arriba.
    if re.search(r"\b(?:alerta por diluvio|alerta por lluvias?)\b", normalized):
        return "Medio Ambiente"
    return feed_category


def standardize(article):
    """Relee noticias antiguas sin inventar la hora que no venía en el RSS."""
    if not isinstance(article, dict):
        return None
    title = clean(article.get("title"))[:320]
    url = article.get("url")
    curated = article.get("editorial_verified") is True
    source = clean(article.get("source"))[:110]
    date = str(article.get("date", ""))
    published = published_datetime(article.get("published_at"))
    if published:
        date = published.astimezone(MX).date().isoformat()
    if not title or not valid_link(url, curated) or not DAY_RE.fullmatch(date):
        return None
    try:
        datetime.fromisoformat(date)
    except ValueError:
        return None
    borough, location = identify_location(title, date)
    if is_infobae_ballet_zapatilla({"title": title, "source": source, "date": date}):
        borough = "Iztacalco"
        location = (
            "Utopía Mixiuhca, Viaducto Río de la Piedad 6, colonia Granjas México, "
            "Iztacalco, Ciudad de México"
        )
    elif is_infobae_maria_leon_concert({"title": title, "source": source, "date": date}):
        borough = ""
        location = "Teatro Metropólitan, Ciudad de México"
    elif is_pulque_barbacoa_fair({"title": title, "date": date}):
        borough = "La Magdalena Contreras"
        location = (
            "Explanada de la Alcaldía La Magdalena Contreras, José Moreno Salido s/n, "
            "colonia Barranca Seca, Ciudad de México"
        )
    if is_coyotepec_highway_crash({"title": title, "source": source, "date": date}):
        borough = ""
        location = "Coyotepec, Estado de México (fuera de CDMX)"
    if is_san_juan_del_rio_autopista57_closure({"title": title, "source": source, "date": date}):
        borough = ""
        location = "San Juan del Río, Querétaro (fuera de CDMX)"
    if is_huixtla_migrant_caravan({"title": title, "source": source, "date": date}):
        borough = ""
        location = "Huixtla, Chiapas (fuera de CDMX)"
    if is_vc_fatal_trailer_incident({"title": title, "source": source, "date": date}):
        borough = "Venustiano Carranza"
        location = "Venustiano Carranza, Ciudad de México"
    normalized_title = "".join(
        ch for ch in unicodedata.normalize("NFKD", title)
        if not unicodedata.combining(ch)
    ).casefold()
    if "tren" in normalized_title and "pachuca" in normalized_title:
        borough = ""
        location = "Ruta CDMX–Pachuca (estación o tramo exacto no indicado)"
    elif "tren" in normalized_title and "guadalajara" in normalized_title:
        borough = ""
        location = "Proyecto ferroviario CDMX–Guadalajara (tramo de obra no indicado)"
    if ("busqueda metropolitana" in normalized_title
            and "morelos" in normalized_title and "edomex" in normalized_title):
        borough = ""
        location = "Ámbito metropolitano: Morelos, CDMX y Estado de México (sede no indicada)"
    if is_infobae_tlalpan_animal_abuse({"title": title, "source": source, "date": date}):
        borough = "Tlalpan"
        location = "Tlalpan (confirmada en la nota original)"
    if is_radio_formula_casa_ecologica({"title": title, "source": source, "date": date}):
        borough = "Álvaro Obregón"
        location = "Santa Rosa Xochiac, alcaldía Álvaro Obregón, Ciudad de México"
    category = article.get("category") if article.get("category") in GENERAL_FEEDS else "CDMX"
    category = category_by_headline(title, category, source)
    result = {
        "title": title,
        "description": "",
        "url": url,
        "source": source or "Medio externo",
        "date": date,
        "published_at": published.isoformat(timespec="seconds").replace("+00:00", "Z") if published else None,
        "category": category,
        "borough": borough,
        "location": location,
    }
    result["local_url"] = local_link(result)
    if is_infobae_maria_leon_concert(result):
        result["source_url"] = INFOBAE_MARIA_LEON_CONCERT_SOURCE_URL
    elif is_infobae_ballet_zapatilla(result):
        result["source_url"] = INFOBAE_BALLET_ZAPATILLA_SOURCE_URL
    elif is_coyotepec_highway_crash(result) and source.casefold() == "infobae":
        result["source_url"] = INFOBAE_COYOTEPEC_HIGHWAY_CRASH_SOURCE_URL
    elif is_san_juan_del_rio_autopista57_closure(result):
        # La publicación original identifica al medio regional y a su firma;
        # se conserva la URL RSS para no cambiar el identificador local.
        result["source"] = "El Sol de San Juan del Río"
        result["source_url"] = SAN_JUAN_DEL_RIO_AUTOPISTA57_SOURCE_URL
    elif is_la_prensa_tlalpan_animal_case(result):
        result["source"] = "La Prensa"
        result["source_url"] = LA_PRENSA_TLALPAN_ANIMAL_SOURCE_URL
    elif is_infobae_tlalpan_animal_abuse(result):
        result["source_url"] = INFOBAE_TLALPAN_ANIMAL_SOURCE_URL
    elif is_vc_fatal_trailer_incident(result):
        result["source_url"] = EL_GRAFICO_VC_TRAILER_SOURCE_URL
    elif is_mauricio_tabe_fifth_report(result):
        result["source_url"] = SDPNOTICIAS_MAURICIO_TABE_REPORT_SOURCE_URL
    elif is_capital_cdmx_care_budget(result):
        result["source_url"] = CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL
    elif is_radio_formula_casa_ecologica(result):
        result["source_url"] = RADIO_FORMULA_CASA_ECOLOGICA_SOURCE_URL
    versions = article.get("alternate_versions")
    if isinstance(versions, list):
        preserved = []
        for version in versions:
            if not isinstance(version, dict) or version.get("url") != url:
                continue
            version_title = clean(version.get("title"))[:320]
            version_date = str(version.get("date") or "")
            if not version_title or not DAY_RE.fullmatch(version_date):
                continue
            preserved.append({
                key: version[key] for key in ARCHIVE_VERSION_FIELDS if key in version
            })
        if preserved:
            result["alternate_versions"] = preserved
    if curated:
        source_brief = article.get("brief")
        required = ("lead", "context", "pending", "method")
        if not isinstance(source_brief, dict) or not all(
            isinstance(source_brief.get(key), str) and source_brief[key].strip()
            for key in required
        ):
            return None
        result["brief"] = {key: clean(source_brief[key])[:2200] for key in required}
        result["editorial_verified"] = True
        result["sensitive_media"] = article.get("sensitive_media") is True
        if isinstance(article.get("location"), str) and article["location"].strip():
            result["location"] = clean(article["location"])[:180]
    else:
        result["brief"] = summarize(result)  # Recalcular fichas RSS al ajustar reglas.
    # La ficha histórica de Infobae sobre Huixtla tuvo un resumen heredado de
    # El Financiero; al normalizarla, rehacer la atribución con la fuente enlazada.
    if is_huixtla_migrant_caravan(result) and source.casefold() == "infobae":
        result["brief"] = summarize(result)
    if (isinstance(article.get("photo"), dict) and
            not (curated and result.get("sensitive_media") is True)):
        result["photo"] = article["photo"]
    # Fotografías de accidentes de archivo pueden ser solo contexto; no
    # conservarlas tras la revisión editorial si no documentan ese hecho.
    result["description"] = result["brief"]["lead"]
    return result


def article_key(article):
    return fold(article.get("title", ""))[:250] + "|" + str(article.get("date", ""))


def archive_record_key(article):
    """Una sola ficha por URL y mes; los cambios de titular quedan preservados."""
    month = str(article.get("date") or "")[:7]
    url = str(article.get("url") or "").strip()
    if MONTH_RE.fullmatch(month) and url:
        return month, "url", url
    return month, "title", article_key(article)


def archive_version_snapshot(article):
    return {
        key: article[key] for key in ARCHIVE_VERSION_FIELDS if key in article
    }


def merge_archive_records(first, second):
    """Consolida versiones del mismo enlace sin perder titulares ni metadatos."""
    primary, other = (
        (second, first) if sort_key(second) >= sort_key(first) else (first, second)
    )
    merged = dict(primary)
    for field in ("photo", "borough", "location", "published_at", "brief", "description", "source_url"):
        if not merged.get(field) and other.get(field):
            merged[field] = other[field]

    versions = []
    for record in (first, second):
        if isinstance(record.get("alternate_versions"), list):
            versions.extend(
                version for version in record["alternate_versions"]
                if isinstance(version, dict)
            )
        versions.append(archive_version_snapshot(record))

    def signature(version):
        brief = version.get("brief") if isinstance(version.get("brief"), dict) else {}
        photo = version.get("photo") if isinstance(version.get("photo"), dict) else {}
        return (
            version.get("title"), version.get("date"), version.get("published_at"),
            version.get("source"), version.get("category"), version.get("description"),
            brief.get("lead"), photo.get("id"),
        )

    # La firma primaria se calcula antes de completar campos con la versión anterior;
    # así no se vuelve a guardar la ficha vigente como una versión alternativa.
    current_signature = signature(primary)
    seen = set()
    alternate_versions = []
    for version in versions:
        version_signature = signature(version)
        if not version_signature[0] or version_signature == current_signature or version_signature in seen:
            continue
        seen.add(version_signature)
        alternate_versions.append({
            key: version[key] for key in ARCHIVE_VERSION_FIELDS if key in version
        })
    if alternate_versions:
        merged["alternate_versions"] = alternate_versions
    else:
        merged.pop("alternate_versions", None)
    return merged


def gather():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=3)
    seen = {}
    successful = 0

    def read_feed(search, category, expect_borough=None, max_items=24):
        nonlocal successful
        rss = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": search + " when:3d", "hl": "es-419", "gl": "MX", "ceid": "MX:es-419"
        })
        try:
            req = urllib.request.Request(rss, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                root = ET.fromstring(resp.read(2_000_000))
            successful += 1
        except (OSError, ET.ParseError, ValueError) as exc:
            print("RSS temporalmente no disponible:", search, str(exc)[:100])
            return
        for item in root.findall(".//item")[:max_items]:
            source = clean(item.findtext("source"))
            title = normalize_title(item.findtext("title"), source)
            link = (item.findtext("link") or "").strip()
            if not allowed(source) or not title or len(title) < 20 or JUNK.search(title) or not valid_link(link):
                continue
            if not headline_has_cdmx_signal(title):
                continue
            try:
                stamp = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc)
            except (ValueError, TypeError, OverflowError):
                continue
            if not cutoff <= stamp <= now + timedelta(minutes=15):
                continue
            borough, _ = identify_location(title)
            if expect_borough and borough != expect_borough:
                continue
            article = standardize({
                "title": title, "url": link, "source": source,
                "published_at": stamp.isoformat(timespec="seconds"),
                "category": category,
            })
            if not article:
                continue
            key = article_key(article)
            if key not in seen:
                seen[key] = article

    for category, query in GENERAL_FEEDS.items():
        read_feed(query, category, max_items=30)
    for query in LOCAL_EVENT_QUERIES:
        read_feed(query, "CDMX", max_items=20)
    # Búsquedas puntuales para dar cobertura a las 16 alcaldías.
    # Solo se etiqueta la alcaldía si aparece explícitamente en el titular.
    for borough in BOROUGHS:
        query = '"' + borough.replace("La Magdalena Contreras", "Magdalena Contreras") + '" CDMX'
        read_feed(query, "CDMX", expect_borough=borough, max_items=14)
    items = sorted(seen.values(), key=sort_key, reverse=True)
    print("Feeds recibidos:", successful, "; nuevos titulares distintos:", len(items))
    return items


def sort_key(item):
    published = published_datetime(item.get("published_at"))
    if published:
        return published
    try:
        return datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc)
    except (ValueError, KeyError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def still_valid(item, cutoff):
    return sort_key(item) >= cutoff


def load_json(path, fallback):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else fallback
    except (OSError, ValueError):
        return fallback


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def sanitize_outside_cdmx_versions(article):
    """Corrige las versiones históricas sin conservar ubicación o fotos engañosas."""
    location = str(article.get("location") or "")
    if "(fuera de CDMX)" not in location:
        return 0
    versions = article.get("alternate_versions")
    if not isinstance(versions, list):
        return 0

    repaired = 0
    for version in versions:
        if not isinstance(version, dict):
            continue
        before = json.dumps(version, ensure_ascii=False, sort_keys=True)
        version["location"] = location
        version["borough"] = article.get("borough", "")
        version["category"] = article.get("category", "CDMX")
        version_article = {**article, **version}
        version_article["location"] = location
        version_article["borough"] = article.get("borough", "")
        version_article["category"] = article.get("category", "CDMX")
        brief = summarize(version_article)
        version["brief"] = brief
        version["description"] = brief["lead"]

        photo = version.get("photo")
        documented = (
            isinstance(photo, dict)
            and photo.get("kind") == "hecho"
            and photo.get("verified") is True
            and bool(photo.get("evidence_url"))
        )
        if isinstance(photo, dict) and not documented:
            version.pop("photo", None)
        after = json.dumps(version, ensure_ascii=False, sort_keys=True)
        if before != after:
            repaired += 1
    return repaired


def photo_needs_refresh(item):
    """Detecta imágenes contextuales obsoletas, incluso si su puntaje no es negativo."""
    photo = item.get("photo") if isinstance(item, dict) else None
    if not isinstance(photo, dict) or photo.get("kind") == "hecho":
        return False
    if is_mauricio_tabe_fifth_report(item):
        return photo.get("id") != "contexto_teatro_angela_peralta"
    return _photo_score(item, photo) < 0


def prioritize_photo_refresh(items, limit=24):
    """Atiende primero las tres fotografías incongruentes confirmadas en la revisión."""
    priority_prefixes = (
        "repartidores anuncian dos bloqueos estrategicos",
        "presupuesto de cuidados 2027",
        "cuantos tianguis hay en cdmx",
    )
    priority = [
        item for item in items
        if any(fold(item.get("title")).startswith(prefix) for prefix in priority_prefixes)
    ]
    priority_keys = {item.get("local_url") or item.get("url") for item in priority}
    recent = [
        item for item in items
        if (item.get("local_url") or item.get("url")) not in priority_keys
    ]
    priority.sort(key=sort_key, reverse=True)
    recent.sort(key=sort_key, reverse=True)
    return (priority + recent)[:max(0, limit)]


def consolidate_archive(new_items, cutoff, updated):
    """Deduplica el histórico y elimina incluso archivos mensuales ya vencidos."""
    ARCHIVE_DIR.mkdir(exist_ok=True)
    BOROUGH_DIR.mkdir(exist_ok=True)
    existing = {}
    for path in ARCHIVE_DIR.glob("????-??.json"):
        if not MONTH_RE.fullmatch(path.stem):
            continue
        month = load_json(path, {"articles": []})
        for raw in month.get("articles", []):
            item = standardize(raw)
            if item and still_valid(item, cutoff):
                key = archive_record_key(item)
                if key in existing:
                    existing[key] = merge_archive_records(existing[key], item)
                else:
                    existing[key] = item
    # Migrar el índice de la portada ANTES de sobrescribirlo.
    prior = load_json(DEST, {"articles": []})
    for raw in prior.get("articles", []):
        item = standardize(raw)
        if item and still_valid(item, cutoff):
            key = archive_record_key(item)
            if key in existing:
                existing[key] = merge_archive_records(existing[key], item)
            else:
                existing[key] = item
    for item in new_items:
        if still_valid(item, cutoff):
            key = archive_record_key(item)
            old = existing.get(key)
            if not old:
                existing[key] = item
            else:
                # Conservar la versión más reciente y guardar las anteriores en el JSON.
                existing[key] = merge_archive_records(old, item)

    normalized_versions = sum(
        sanitize_outside_cdmx_versions(item) for item in existing.values()
    )
    if normalized_versions:
        print("Versiones alternativas fuera de CDMX normalizadas:", normalized_versions)

    # Retirar también las fotos de contexto que ya estaban guardadas en la
    # hemeroteca para titulares sensibles. No basta con proteger el feed nuevo.
    sensitive_photos_removed = clear_sensitive_context_photos(existing.values())
    if sensitive_photos_removed:
        print("Fotografías de contexto retiradas de noticias sensibles:", sensitive_photos_removed)

    # Reparar también fotografías antiguas incongruentes después de corregir
    # la clasificación RSS. Conservar fotografías del hecho verificadas.
    mismatched = [
        item for item in existing.values()
        if photo_needs_refresh(item)
    ]
    missing = [item for item in existing.values()
               if not item.get("photo") and not is_sensitive_media(item)]
    # Priorizar las tres discrepancias editoriales confirmadas y conservar
    # el límite de 24 reemplazos por ejecución; después, atender las más recientes.
    refresh = prioritize_photo_refresh(mismatched, limit=24)
    batch = refresh + missing[:max(0, 300 - len(refresh))]
    if batch:
        stats = assign_photos(batch)
        print("Fotografías del archivo (lote):", len(batch), "revisadas;",
              len(refresh), "incongruentes reconsideradas;",
              stats["assigned"], "asignadas;",
              len(mismatched) - len(refresh), "incongruentes pendientes;",
              len(missing) - (len(batch) - len(refresh)), "sin foto pendientes")

    by_month = defaultdict(list)
    by_borough = defaultdict(list)
    for item in existing.values():
        by_month[item["date"][:7]].append(item)
        if item["borough"]:
            by_borough[item["borough"]].append(item)
    for filename in ARCHIVE_DIR.glob("????-??.json"):
        if filename.stem not in by_month:
            filename.unlink()
    months = []
    for month in sorted(by_month, reverse=True):
        items = sorted(by_month[month], key=sort_key, reverse=True)
        url = "/archivo/" + month + ".json"
        target = ARCHIVE_DIR / (month + ".json")
        previous = load_json(target, {})
        # Los meses anteriores no se reescriben si las noticias no cambiaron.
        stamp = previous.get("updated", updated) if previous.get("articles") == items else updated
        write_json(target, {"month": month, "updated": stamp, "articles": items})
        months.append({"month": month, "url": url, "count": len(items)})
    write_json(ARCHIVE_DIR / "meses.json", {
        "updated": updated, "retention_days": RETENTION_DAYS, "months": months
    })
    borough_output = []
    for name in BOROUGHS:
        items = sorted(by_borough[name], key=sort_key, reverse=True)
        borough_output.append({
            "name": name, "count": len(items), "articles": items[:24]
        })
    write_json(BOROUGH_DIR / "noticias.json", {
        "updated": updated, "boroughs": borough_output
    })
    print("Archivo:", sum(len(x) for x in by_month.values()),
          "titulares conservados en", len(months), "meses")
    return months


def fill_recent_from_archive(items, now, limit=60):
    """Rescata titulares recientes si el RSS trae menos noticias que la portada.

    El archivo mensual sigue siendo la fuente de respaldo aunque existan
    algunas noticias editoriales verificadas: no basta con comprobar
    `if not items`, porque esas noticias ocultaban caídas completas del RSS.
    """
    if len(items) >= limit:
        return items
    cutoff = now - timedelta(days=3)
    combined = {article_key(item): item for item in items}
    for path in ARCHIVE_DIR.glob("????-??.json"):
        if not MONTH_RE.fullmatch(path.stem):
            continue
        for raw in load_json(path, {"articles": []}).get("articles", []):
            item = standardize(raw)
            if not item or not local_for_homepage(item):
                continue
            stamp = sort_key(item)
            if not cutoff <= stamp <= now + timedelta(minutes=15):
                continue
            combined.setdefault(article_key(item), item)
    result = sorted(combined.values(), key=sort_key, reverse=True)[:limit]
    if len(result) > len(items):
        print("Portada: recuperados", len(result) - len(items),
              "titulares recientes del archivo ante RSS insuficiente.")
    return result


def editorial_event_key(article):
    """Identifica solo coberturas repetidas del mismo hecho inequívoco.

    No fusiona la hemeroteca: distintas fuentes conservan sus registros.
    """
    title = fold(article.get("title", ""))
    if (re.search(r"\bcoyoacan\b", title)
            and re.search(r"\bsaldo blanco\b", title)
            and re.search(r"\bdia de muertos\b", title)):
        return ("coyoacan-dia-muertos-saldo-blanco", article.get("date"))
    return None


def dedupe_homepage_events(items):
    """Evita reiterar un mismo suceso en portada, sin borrar fuentes."""
    result = []
    seen_events = set()
    for article in items:
        event = editorial_event_key(article)
        if event is not None:
            if event in seen_events:
                continue
            seen_events.add(event)
        result.append(article)
    return result


def merge_recent_previous_feed(items, previous_articles, now, limit=60):
    """Conserva noticias recientes del último feed publicado ante una caída parcial del RSS."""
    cutoff = now - timedelta(days=3)
    combined = {
        article_key(item): item
        for item in items
        if isinstance(item, dict)
    }
    previous = previous_articles if isinstance(previous_articles, list) else []
    for raw in previous:
        item = standardize(raw)
        if not item or not local_for_homepage(item):
            continue
        published = sort_key(item)
        if not cutoff <= published <= now + timedelta(minutes=15):
            continue
        combined.setdefault(article_key(item), item)
    merged = sorted(combined.values(), key=sort_key, reverse=True)[:max(0, int(limit))]
    recovered = max(0, len(merged) - len(items))
    if recovered:
        print(
            "Portada: se conservaron", recovered,
            "titulares recientes del último feed publicado ante RSS insuficiente."
        )
    return merged


def homepage_articles(items, reviewed, now, limit=60):
    """Mostrar temporalmente accidentes relevantes cotejados, sin fijarlos para siempre."""
    front = [item for item in items if local_for_homepage(item)][:limit]
    if not front:
        return front
    visible = {item["url"] for item in front}
    for article in sorted((item for item in reviewed if local_for_homepage(item)),
                          key=sort_key, reverse=True):
        if article["url"] in visible:
            continue
        published = sort_key(article)
        age = now - published
        if not timedelta(0) <= age <= timedelta(hours=48):
            continue
        if len(front) >= limit:
            removed = front.pop()
            visible.discard(removed["url"])
        front.append(article)
        visible.add(article["url"])
    return sorted(front, key=sort_key, reverse=True)


def build_homepage_feed(candidates):
    """Conserva titulares válidos y una sola ficha por fuente y enlace local."""
    visible = []
    used_photos = set()
    for article in candidates:
        photo = article.get("photo")
        title_sensitive = bool(
            SENSITIVE_MEDIA_TITLE.search(str(article.get("title") or ""))
        )
        if not isinstance(photo, dict):
            article.pop("photo", None)
            if title_sensitive:
                visible.append(article)
            continue
        photo_url = str(photo.get("url") or "")
        documented = (
            photo.get("kind") == "hecho"
            and photo.get("verified") is True
            and bool(photo.get("evidence_url"))
        )
        contextual = photo.get("kind") == "representativa"
        # Solo los titulares sensibles identificados por tema permanecen en
        # portada sin foto; el flag editorial también se usa para otros casos
        # que deben quedarse exclusivamente en la hemeroteca.
        if title_sensitive and not documented:
            article.pop("photo", None)
            visible.append(article)
            continue
        if contextual and _photo_score(article, photo) < 0:
            article.pop("photo", None)
            if title_sensitive:
                visible.append(article)
            continue
        trusted_url = (
            photo_url.startswith("/assets/fotos/")
            or photo_url.startswith("https://thumb.wikimedia.org/wikipedia/commons/")
            or photo_url.startswith("https://upload.wikimedia.org/wikipedia/commons/")
        )
        complete_credit = all(
            photo.get(key) for key in ("author", "license", "licenseUrl", "source")
        )
        valid_photo = (
            trusted_url
            and photo_url not in used_photos
            and complete_credit
            and (documented or contextual)
        )
        if not valid_photo:
            article.pop("photo", None)
            if title_sensitive:
                visible.append(article)
            continue
        visible.append(article)
        used_photos.add(photo_url)

    # Un mismo RSS puede entregar varios titulares para el mismo enlace.
    # El archivo mensual ya conserva esas variantes; en portada debe existir
    # una sola ficha y un solo identificador local por noticia. candidates
    # llega ordenado por fecha descendente, así que se conserva la versión
    # elegible más reciente sin borrar las variantes históricas.
    unique_visible = []
    seen_source_urls = set()
    seen_local_urls = set()
    for article in visible:
        source_url = str(article.get("url") or "").strip()
        local_url = str(article.get("local_url") or "").strip()
        if source_url and source_url in seen_source_urls:
            continue
        if local_url and local_url in seen_local_urls:
            continue
        if source_url:
            seen_source_urls.add(source_url)
        if local_url:
            seen_local_urls.add(local_url)
        unique_visible.append(article)

    return dedupe_homepage_events(unique_visible)


def homepage_fallback_payload(articles, now=None, limit=12):
    """Prepara el respaldo incrustado de portada con noticias de hoy o ayer."""
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(MX).date()
    yesterday = today - timedelta(days=1)
    candidates = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        published = sort_key(article)
        day = published.astimezone(MX).date()
        if day not in (today, yesterday):
            continue
        title = str(article.get("title") or "")
        if re.search(r"\b(?:hoy|en vivo)\b", title, re.I) and day != today:
            continue
        candidates.append(article)
    candidates.sort(key=sort_key, reverse=True)
    return [dict(article) for article in candidates[:max(0, int(limit))]]


def refresh_homepage_fallback(index_path, articles, now=None):
    """Actualiza el JSON de respaldo de portada sin tocar el diseño HTML."""
    path = Path(index_path)
    if not path.is_file():
        raise RuntimeError(f"No existe el HTML de portada: {path}")
    html_content = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<script id="embedded-news-fallback" type="application/json">)(.*?)(</script>)',
        re.S,
    )
    match = pattern.search(html_content)
    if not match:
        raise RuntimeError("No se encontró embedded-news-fallback en index.html")
    payload = homepage_fallback_payload(articles, now)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    encoded = encoded.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    updated = html_content[:match.start(2)] + encoded + html_content[match.end(2):]
    if updated != html_content:
        path.write_text(updated, encoding="utf-8")
    return len(payload)


def update():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RETENTION_DAYS)
    previous_data = load_json(DEST, {"articles": []})
    previous_articles = (
        previous_data.get("articles", [])
        if isinstance(previous_data, dict) else []
    )
    updated = now.strftime("%Y-%m-%d %H:%M UTC")
    items = gather()
    # Integrar reportes editoriales cotejados con fuentes y resúmenes originales.
    # Persisten entre ejecuciones y en la hemeroteca sin simular enlaces de Google News.
    curated_data = load_json(CURATED_INCIDENTS, {"articles": []})
    reviewed = []
    for raw in curated_data.get("articles", []):
        entry = standardize(raw)
        if entry and entry.get("editorial_verified") and still_valid(entry, cutoff):
            reviewed.append(entry)
    curated_keys = {article_key(entry) for entry in reviewed}
    curated_urls = {entry["url"] for entry in reviewed}
    items = sorted(
        reviewed + [item for item in items if article_key(item) not in curated_keys
                    and item.get("url") not in curated_urls],
        key=sort_key, reverse=True,
    )
    # Fallback únicamente si siguen siendo recientes; nunca mostrar noticias caducadas.
    if not items:
        old = load_json(DEST, {"articles": []})
        items = [
            item for raw in old.get("articles", [])
            if (item := standardize(raw)) and local_for_homepage(item)
            and sort_key(item) >= now - timedelta(days=3)
        ]
        print("Utilizando solo noticias todavía recientes que ya estaban guardadas.")
    # Unas pocas noticias editoriales no deben ocultar una caída del RSS.
    items = fill_recent_from_archive(items, now)
    items = merge_recent_previous_feed(items, previous_articles, now)
    picture_stats = assign_photos(items[:60])
    print("Fotografías verificadas para portada:", picture_stats)
    consolidate_archive(items, cutoff, updated)
    # El feed conserva titulares aunque no tengan fotografía.
    # La portada JS muestra imágenes acreditadas y también noticias sensibles sin foto.
    candidates = homepage_articles(items, reviewed, now)
    visible = build_homepage_feed(candidates)
    write_json(DEST, {"updated": updated, "articles": visible})
    # Mantiene sincronizado el respaldo HTML para cuando falle la descarga del feed.
    fallback_count = refresh_homepage_fallback(ROOT / "index.html", visible, now)
    print("Respaldo estático de portada:", fallback_count, "noticias recientes.")
    with_photo = sum(bool(article.get("photo")) for article in visible)
    print(
        "Feed de portada:", len(visible), "titulares;",
        with_photo, "con fotografía acreditada;",
        len(visible) - with_photo, "sin fotografía."
    )


def report_shell(title, body):
    from html import escape
    match = re.fullmatch(r"Reporte (\\d{4}-\\d{2}-\\d{2})", title)
    canonical = SITE + ("/reportes/" + match.group(1) + ".html" if match else "/reportes/")
    weather = (
        '<div id="weather-ribbon" class="weather-ribbon" role="region" aria-label="Clima estimado en la CDMX">'
        '<a class="weather-ribbon__brand" href="/cerca/">🌸 CLIMA</a>'
        '<div class="weather-ribbon__window"><div id="weather-ribbon-track" class="weather-ribbon__track">'
        '<div class="weather-ribbon__set"><span class="weather-chip">⛅ Consultando clima de CDMX…</span></div>'
        '</div></div>'
        '<span class="weather-sr-only" id="weather-screen-reader" role="status" aria-live="polite"></span></div>'
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + escape(title) + ' | CDMX AL MEMENTO</title>'
        '<meta name="description" content="Análisis editorial de los titulares de CDMX con tesis, evidencia enlazada, opinión diferenciada y límites de verificación.">'
        '<link rel="canonical" href="' + escape(canonical, quote=True) + '">'
        '<link rel="stylesheet" href="/styles.css">'
        '<link rel="stylesheet" href="/assets/explora.css?v=3">'
        '<link rel="stylesheet" href="/assets/clima-ticker.css?v=4">'
        '<link rel="stylesheet" href="/assets/premium-2026.css?v=1"></head><body>'
        + weather +
        '<header><div class="wrap"><div class="top"><a class="logo" href="/">CDMX <span>AL MEMENTO</span></a></div>'
        '<nav><a href="/">Noticias</a><a href="/archivo/">Archivo mensual</a>'
        '<a href="/alcaldias/">Alcaldías</a></nav></div></header>'
        '<main class="wrap prose">' + body + '</main><footer><div class="wrap">'
        '<a href="/politica-editorial.html">Política editorial</a> · '
        '<a href="mailto:' + MAIL + '">' + MAIL + '</a></div></footer>'
        '<script src="/assets/clima-ticker.js?v=4" defer></script>'
        '<script src="/assets/page-transitions.js?v=1" defer></script></body></html>'
    )


def generate_report():
    from html import escape
    current = load_json(DEST, {"articles": []})
    rows = current.get("articles", [])
    entries = load_json(REPORTS, {"reports": []}).get("reports", [])
    today = datetime.now(MX).date()
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).astimezone(MX).date()

    REPORT_DIR.mkdir(exist_ok=True)
    for file in REPORT_DIR.glob("????-??-??.html"):
        try:
            day = datetime.strptime(file.stem, "%Y-%m-%d").date()
            if day < cutoff_date:
                file.unlink()
        except ValueError:
            continue
    entries = [
        item for item in entries if isinstance(item, dict)
        and DAY_RE.fullmatch(str(item.get("date", "")))
        and datetime.strptime(item["date"], "%Y-%m-%d").date() >= cutoff_date
        and (REPORT_DIR / (item["date"] + ".html")).exists()
    ]
    local_day = today.isoformat()
    sources = {x.get("source") for x in rows if isinstance(x, dict)}
    if len(rows) >= 8 and len(sources) >= 3:
        parts = [
            '<p class="eyebrow">Reporte de seguimiento automático · ' + local_day + '</p>',
            '<h1>Titulares recientes de Ciudad de México</h1>',
            '<p>Resumen automatizado con enlaces a medios externos y fecha de publicación.</p>',
            '<div class="notice">No constituye investigación ni verificación independiente. '
            'La alcaldía se infiere exclusivamente cuando el titular la menciona.</div>',
            build_editorial(rows, datetime.now(timezone.utc)),
            '<div class="report-separation"><h2>Los titulares originales, por tema</h2>'
            '<p>Este listado sirve para seguir cada noticia en su medio de origen. '
            'La lectura editorial anterior no añade hechos que estos titulares no acrediten.</p></div>',
        ]
        for category in GENERAL_FEEDS:
            group = [x for x in rows if x.get("category") == category
                     and (category != "Metro" or re.search(
                         r"\\bmetro\\b|\\bmetrob[uú]s\\b|l[ií]nea\\s+(?:[1-9]|1[02]|A|B)\\b",
                         x.get("title", ""), re.I))
                     and (category != "Seguridad" or re.search(
                         r"seguridad|ssc|polic[ií]a|detien|homicid|robo|asalto|"
                         r"delit|denunci|prisi[oó]n|penitenciari|fiscal[ií]a",
                         x.get("title", ""), re.I))][:9]
            if not group:
                continue
            parts.append('<h2>' + escape(category) + '</h2><ol>')
            for article in group:
                url = article.get("url")
                if not valid_link(url):
                    continue
                pub = published_datetime(article.get("published_at"))
                when = pub.astimezone(MX).strftime("%d/%m/%Y %H:%M") if pub else article.get("date", "Fecha no indicada")
                loc = article.get("location", "Ubicación no indicada")
                parts.append(
                    '<li><a target="_blank" rel="noopener noreferrer nofollow" href="' +
                    escape(article.get("local_url") or local_link(article), quote=True) + '">' + escape(article.get("title", "")) +
                    '</a> — ' + escape(article.get("source", "")) +
                    ' · Publicada: ' + escape(when) +
                    ' · Zona: ' + escape(loc) + '</li>'
                )
            parts.append("</ol>")
        parts.append('<p>Solicita correcciones escribiendo a <a href="mailto:' + MAIL + '">' + MAIL + '</a>.</p>')
        fname = local_day + ".html"
        (REPORT_DIR / fname).write_text(
            report_shell("Reporte " + local_day, "\n".join(parts)), encoding="utf-8"
        )
        entries = [item for item in entries if item["date"] != local_day]
        entries.append({
            "date": local_day, "url": "/reportes/" + fname, "count": len(rows)
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    write_json(REPORTS, {"updated": current.get("updated", ""), "reports": entries})
    listing = ('<h1>Reportes y análisis editoriales de CDMX</h1>'
               '<p>Cada entrega separa una tesis de lectura, lo que permiten afirmar '
               'los titulares, lo que falta por comprobar, la opinión editorial '
               'y los enlaces originales. El texto es una lectura automatizada, '
               'no investigación independiente ni reportaje de campo.</p>'
               '<p>Recopilaciones con fuentes externas; los reportes antiguos se retiran '
               'después de 365 días. <a href="/archivo/">Consultar archivo mensual de noticias</a>.</p><ul>')
    for item in entries:
        listing += '<li><a href="' + escape(item["url"], quote=True) + '">Reporte ' + \
            escape(item["date"]) + '</a> · ' + str(int(item.get("count", 0))) + ' titulares</li>'
    listing += '</ul>'
    (REPORT_DIR / "index.html").write_text(
        report_shell("Reportes diarios", listing), encoding="utf-8"
    )

    urls = [
        "", "contacto.html", "privacidad.html", "sobre-nosotros.html",
        "politica-editorial.html", "creditos-fotograficos.html",
        "guias/", "reportes/", "archivo/", "alcaldias/", "mapa/",
        "cerca/", "movilidad/", "trafico/", "aire/", "avisos/", "cdmx/", "seguridad/", "servicios/", "fotografias/",
        "noticias/", "descubre/", "estadisticas/", "agenda/", "negocios/", "herramientas/", "publicidad/", "comunidad/", "reportes-ciudadanos/", "herramientas/calendario-laboral.html",
    ]
    urls += [
        "guias/" + name for name in (
            "estado-del-metro.html", "alertas-por-lluvia.html",
            "cierres-viales.html", "tramites-cdmx.html"
        )
    ]
    urls += ["alcaldias/" + p.name + "/" for p in sorted((ROOT / "alcaldias").iterdir())
             if p.is_dir() and (p / "index.html").is_file()]
    urls += ["descubre/" + p.name for p in sorted((ROOT / "descubre").glob("*.html")) if p.name != "index.html"]
    urls += ["reportes/" + p.name for p in sorted(REPORT_DIR.glob("????-??-??.html"))]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
        "".join('<url><loc>' + SITE + '/' + escape(p) + '</loc></url>' for p in urls) +
        '</urlset>\n', encoding="utf-8"
    )
    print("Reportes vigentes:", len(entries))


if __name__ == "__main__":
    update()
    generate_report()
