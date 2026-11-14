"""Fichas originales breves dentro del sitio.

La fuente automática disponible es un índice RSS de titulares; no dispone del
texto íntegro de cada reportaje. No recrear declaraciones, números ni escenas.
Cada nota explica el alcance, el interés público y lo que falta por confirmar.
Solo se marca como foto DEL HECHO una imagen con revisión editorial y licencia comprobadas.
Sin esa prueba se usan fotografías reales REPRESENTATIVAS, nunca evidencia atribuida.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
BOROUGH_PHOTOS=ROOT/"assets/alcaldias/fotos.json"
ARCHIVE_PHOTOS=ROOT/"assets/fotos/catalogo.json"
RECENT_PHOTOS=ROOT/"assets/fotos/recientes.json"
NEWS_PHOTOS=ROOT/"assets/fotos/indice-noticias-1100.json"
TOPIC_PHOTOS=ROOT/"assets/fotos/contexto-tematico.json"
VERIFIED_EVENTS=ROOT/"assets/fotos/hechos-verificados.json"

SENSITIVE_MEDIA_TITLE = re.compile(
    r"\b(?:violaci[oó]n|abuso sexual|agresi[oó]n sexual|acoso sexual|violencia sexual|"
    r"maltrato animal|maltratador(?:es)? de animales?|"
    r"maltrat\w*\s+(?:(?:a|de)\s+)?(?:perros?|perritos?|gatos?|mascotas?|animales?)|"
    r"abusador(?:es)? sexual(?:es)? de animales?|"
    r"crueldad animal|tortura animal|violencia contra animales?|"
    r"agresi[oó]n contra animales?|"
    r"(?:matar|matan|mat[oó]|mataron|asesinar|asesinan|asesin[oó]|"
    r"envenenar|envenenan|envenen[oó]|golpear|golpean|golpe[oó])\s+(?:a\s+(?:(?:los|las|un|una|unos|unas)\s+)?)?"
    r"(?:perros?|perritos?|gatos?|mascotas?|animales?)|"
    r"(?:perros?|perritos?|gatos?|mascotas?|animales?)\s+(?:maltratad[oa]s?|envenenad[oa]s?)|"
    r"envenenamiento de (?:perros?|perritos?|gatos?|mascotas?|animales?))\b",
    re.IGNORECASE,
)


def is_coyotepec_highway_crash(article):
    """Identifica las coberturas del choque múltiple del 12/11/2026 en Coyotepec."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = str(article.get("source") or "").strip().casefold()
    if str(article.get("date") or "") != "2026-11-12" or "mexico-queretaro" not in title:
        return False
    nplus = (
        (source == "n+" or source.startswith("n+ "))
        and "3 autobuses" in title
        and "tractocamion" in title
    )
    infobae = (
        source == "infobae"
        and "alumnos viajaban de paseo" in title
        and "impactados por trailer" in title
        and "choque" in title
    )
    return nplus or infobae


SAN_JUAN_DEL_RIO_AUTOPISTA57_SOURCE_URL = "https://oem.com.mx/elsoldesanjuandelrio/policiaca/toma-precauciones-si-viajas-a-la-cdmx-autopista-57-esta-detenida-33095499"
INFOBAE_COYOTEPEC_HIGHWAY_CRASH_SOURCE_URL = "https://www.infobae.com/mexico/2026/11/13/alumnos-viajaban-de-paseo-a-la-cdmx-y-fueron-impactados-por-trailer-difunden-video-del-choque-en-la-mexico-queretaro/"
LA_PRENSA_TLALPAN_ANIMAL_SOURCE_URL = "https://oem.com.mx/la-prensa/policiaca/detienen-a-otro-presunto-maltratador-de-animales-en-tlalpan-33095643"
INFOBAE_TLALPAN_ANIMAL_SOURCE_URL = "https://www.infobae.com/mexico/2026/11/12/detienen-a-presunto-abusador-sexual-de-animales-en-situacion-de-calle-en-cdmx-activistas-piden-que-las-investigaciones-lleguen-a-fondo/"
EL_GRAFICO_VC_TRAILER_SOURCE_URL = "https://www.elgrafico.mx/la-roja/2026/11/12/el-morenito-muere-tras-ser-arrastrado-varios-metros-por-un-trailer-en-venustiano-carranza/?outputType=amp"
INFOBAE_BALLET_ZAPATILLA_SOURCE_URL = "https://www.infobae.com/mexico/2026/11/12/funcion-gratis-del-ballet-la-zapatilla-de-cristal-llega-a-cdmx-fecha-y-sede/"
INFOBAE_MARIA_LEON_CONCERT_SOURCE_URL = "https://www.infobae.com/mexico/2026/11/13/maria-leon-presento-su-nueva-era-de-villana-en-el-teatro-metropolitan-de-la-cdmx-entre-invitados-nostalgia-y-canciones-ineditas/"
INFOBAE_PULQUE_BARBACOA_SOURCE_URL = "https://www.infobae.com/mexico/2026/11/06/la-feria-del-pulque-y-la-barbacoa-2026-llegara-a-la-magdalena-contreras-en-cdmx-fechas-horarios-y-como-llegar/"
POSTA_PULQUE_BARBACOA_SOURCE_URL = "https://www.posta.com.mx/cdmx/feria-del-pulque-y-la-barbacoa-2026-fechas-y-entrada-gratis/vl2276243"
SDPNOTICIAS_MAURICIO_TABE_REPORT_SOURCE_URL = "https://www.sdpnoticias.com/estados/cdmx/mauricio-tabe-presenta-su-quinto-informe-de-gobierno-en-miguel-hidalgo/"
LA_PRENSA_MAURICIO_TABE_REPORT_SOURCE_URL = "https://oem.com.mx/la-prensa/metropoli/mauricio-tabe-presenta-su-quinto-informe-presume-avances-en-seguridad-y-cambios-en-miguel-hidalgo-33088214"
RADIO_FORMULA_CASA_ECOLOGICA_SOURCE_URL = "https://www.radioformula.com.mx/cdmx/calentadores-solares-y-captacion-de-lluvia-el-plan-de-cdmx-para-ahorrar-en-casa-20261112-0088.html"
LA_JORNADA_CASA_ECOLOGICA_SOURCE_URL = "https://www.jornada.com.mx/noticia/2026/11/12/capital/lanza-cdmx-programa-de-ecotecnias-para-10-mil-viviendas-en-alvaro-obregon"
CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL = "https://capital-cdmx.org/presupuesto-cuidados-2027-cdmx-cuanto-dinero-llegara-anexo-31-desglose/"


def is_radio_formula_casa_ecologica(article):
    """Identifica la nota de Radio Fórmula del programa Casa Ecológica del 12/11/2026."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "radio formula"
        and "calentadores solares" in title
        and "captacion de lluvia" in title
    )


def is_capital_cdmx_care_budget(article):
    """Identifica el análisis del Anexo 31 publicado por Capital CDMX el 12/11/2026."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "capital cdmx"
        and "presupuesto de cuidados 2027" in title
    )


def is_infobae_ballet_zapatilla(article):
    """Identifica la agenda de ballet de Infobae del 28 de noviembre en Iztacalco."""
    title = _photo_fold(article.get("title"))
    source = _photo_fold(article.get("source"))
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "infobae"
        and "ballet" in title
        and "zapatilla de cristal" in title
    )


def is_infobae_maria_leon_concert(article):
    """Identifica la cobertura de Infobae sobre el concierto de María León del 12/11/2026."""
    title = _photo_fold(article.get("title"))
    source = _photo_fold(article.get("source"))
    return (
        str(article.get("date") or "") == "2026-11-13"
        and source == "infobae"
        and "maria leon" in title
        and "era de villana" in title
        and "teatro metropolitan" in title
    )


def is_jose_cardenas_rocazos(article):
    """Identifica la nota de José Cárdenas sobre ataques a automovilistas en Periférico."""
    title = _photo_fold(article.get("title"))
    source = _photo_fold(article.get("source"))
    return (
        str(article.get("date") or "") == "2026-11-13"
        and source == "jose cardenas"
        and "rocazos" in title
    )


def is_pulque_barbacoa_fair(article):
    """Identifica la Feria del Pulque y la Barbacoa anunciada para el 13-15 de noviembre."""
    title = _photo_fold(article.get("title"))
    return (
        str(article.get("date") or "") == "2026-11-12"
        and "feria" in title
        and "pulque" in title
        and "barbacoa" in title
    )


def is_imagen_tlalpan_dog_rescue(article):
    """Identifica el titular de Imagen TV sobre el rescate de una perrita en Tlalpan."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "imagen television"
        and title.startswith("vecinos rescatan a perrita de presunto abuso sexual por un hombre en tlalpan")
    )


def is_infobae_tlalpan_animal_abuse(article):
    """Identifica la nota de Infobae cuyo cuerpo ubica el caso en Tlalpan."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "infobae"
        and title.startswith("detienen a presunto abusador sexual de animales en situacion de calle en cdmx")
    )


def is_la_prensa_tlalpan_animal_case(article):
    """Identifica el artículo de La Prensa atribuido por error a otro medio OEM."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold().strip()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source in {"el sol de mexico", "la prensa"}
        and title == "detienen a otro presunto maltratador de animales en tlalpan"
    )


def is_san_juan_del_rio_autopista57_closure(article):
    """Identifica el aviso de la autopista 57 ubicado en San Juan del Río."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source in {"el sol de mexico", "el sol de san juan del rio"}
        and "autopista 57" in title
        and "esta detenida" in title
    )


def is_huixtla_migrant_caravan(article):
    """Identifica las dos versiones publicadas sobre la caravana ubicada en Huixtla."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    original_el_financiero = (
        str(article.get("date") or "") == "2026-11-12"
        and source == "el financiero"
        and "caravana migrante" in title
        and "huixtla" in title
        and "chiapas" in title
        and "rumbo a cdmx" in title
    )
    updated_infobae = (
        str(article.get("date") or "") == "2026-11-13"
        and source == "infobae"
        and "caravana con 500 migrantes acampa en huixtla" in title
        and "chiapas" in title
        and "avanzar a cdmx" in title
    )
    return original_el_financiero or updated_infobae


def is_vc_fatal_trailer_incident(article):
    """Identifica el siniestro fatal de El Gráfico en Venustiano Carranza."""
    title = unicodedata.normalize("NFKD", str(article.get("title") or ""))
    title = "".join(ch for ch in title if not unicodedata.combining(ch)).casefold()
    source = unicodedata.normalize("NFKD", str(article.get("source") or ""))
    source = "".join(ch for ch in source if not unicodedata.combining(ch)).casefold().strip()
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "el grafico"
        and "morenito" in title
        and "trailer" in title
        and "arrastrado" in title
    )


def is_sensitive_media(article):
    """Impide fotos de contexto en noticias sensibles o accidentes graves sin imagen verificada."""
    return (
        article.get("sensitive_media") is True
        or bool(SENSITIVE_MEDIA_TITLE.search(str(article.get("title") or "")))
        or is_coyotepec_highway_crash(article)
        or is_san_juan_del_rio_autopista57_closure(article)
        or is_vc_fatal_trailer_incident(article)
    )


TAGS={
 "Metro":{
   "focus":"el servicio de transporte del Metro y las personas que utilizan su red",
   "importance":"Los cambios en este sistema pueden afectar los horarios, las conexiones y la planeación de los viajes cotidianos.",
   "verify":"El estado operativo, las estaciones y las alternativas de traslado deben comprobarse en los avisos actuales del Metro."
 },
 "Movilidad":{
   "focus":"la movilidad de la capital y las condiciones de traslado",
   "importance":"Esta información puede resultar útil para organizar recorridos, entregas, trabajo, clases y citas.",
   "verify":"Antes de modificar un itinerario hay que contrastar el lugar, el horario y los avisos recientes de las autoridades de movilidad."
 },
 "Seguridad":{
   "focus":"la seguridad y la convivencia en los espacios de la ciudad",
   "importance":"Una noticia sobre seguridad afecta a personas y comunidades; conviene informar sin especular ni convertir a nadie en culpable antes de una resolución.",
   "verify":"Se necesita contrastar el informe de las autoridades, las circunstancias y el estado de cualquier investigación."
 },
 "Cultura":{
   "focus":"la vida cultural, el patrimonio y las actividades de la ciudad",
   "importance":"La actividad cultural abre oportunidades de encuentro, aprendizaje y disfrute para habitantes y visitantes.",
   "verify":"Los accesos, boletos, sedes, cupos y horarios deben consultarse con la institución organizadora."
 },
 "Gobierno":{
   "focus":"decisiones públicas e instituciones de la capital",
   "importance":"Las decisiones administrativas pueden influir en servicios, trámites y derechos; conviene conocer sus condiciones y a quiénes afectan.",
   "verify":"Es indispensable consultar los acuerdos, comunicados o documentos oficiales antes de dar una medida por vigente."
 },
 "CDMX":{
   "focus":"un asunto de interés público relacionado con la Ciudad de México",
   "importance":"Conocer qué se publica sobre la ciudad ayuda a seguir temas que afectan a vecinas, vecinos y visitantes.",
   "verify":"Los detalles, la ubicación y las posibles actualizaciones requieren corroboración en la publicación completa o ante la instancia correspondiente."
 },
}

def local_link(article):
    token=hashlib.sha256(str(article.get("url") or "").encode()).hexdigest()[:20]
    date=str(article.get("date") or "")[:7]
    return "/noticias/?id="+token+"&mes="+date

def _reported_angle(article):
    """Ideas específicas atribuidas al titular o a un comunicado oficial cotejado."""
    title=str(article.get("title") or "")
    t=title.casefold()
    source=str(article.get("source") or "el medio de origen")
    borough=str(article.get("borough") or "")
    zone=(" en "+borough) if borough else " en la capital"

    # La ficha de la SSC se cotejó con su comunicado oficial del 11 de noviembre.
    # Atribuir cifras y calendario a la dependencia; no presentarlo como balance de incidentes.
    if ("buen fin 2026" in t and "ssc" in t and "operativo" in t and "polic" in t):
        return (
            f"El comunicado oficial de {source} anuncia un operativo preventivo con 16,300 policías "
            "en las 16 alcaldías, del 13 al 17 de noviembre de 2026. El despliegue comenzará "
            "a las 05:00 del viernes 13 y continuará hasta el martes 17, al término de las "
            "actividades comerciales de cada jornada. La vigilancia se concentrará en zonas "
            "comerciales, bancos, nodos de transporte y corredores de alta afluencia; es un "
            "despliegue anunciado, no un balance de incidentes."
        )

    if ("lgbtttiq" in t and "apoyo" in t
            and re.search(r"\b(?:recorta|recorte|reduce|reducen|reduccion)\b", t)
            and source.casefold().replace(" ", "") in {"24-horas", "24horas"}):
        return (
            f"La nota de {source} informa que la acción social «Orgullo de la transformación» "
            "de la alcaldía Iztapalapa tendrá 400 beneficiarios en 2026, frente a 1,400 en 2025. "
            "El texto atribuye a los lineamientos publicados en la Gaceta Oficial un presupuesto "
            "de alrededor de siete millones de pesos en 2025 y de 1.2 millones en 2026; "
            "también indica un pago único de tres mil pesos para cada persona seleccionada. "
            "El 83% del titular se refiere al recorte presupuestal, no a la reducción de beneficiarios."
        )

    if "alerta amber" in t or ("desaparec" in t and "años" in t):
        return (f"Una publicación de {source} informa sobre la búsqueda de una adolescente "
                f"y menciona la activación de una Alerta Amber{zone}. "
                "Por respeto a su privacidad, esta síntesis no reproduce datos personales "
                "adicionales ni especula sobre las circunstancias de la desaparición.")
    # La volcadura del 11 de noviembre ocurrió en Ecatepec, Estado de México;
    # la afectación fue hacia CDMX. Corroborado por El Sol, La Jornada, UnoTV y DigitalMex.
    if (article.get("date") in {"2026-11-11", "2026-11-12"}
            and re.search(r"\bpipa\b", t)
            and re.search(r"m[eé]xico[- ]pachuca", t)):
        injury = (
            f" El titular de {source} menciona al menos dos personas lesionadas."
            if re.search(r"\bal menos\s+2\s+lesionad", t)
            else ""
        )
        return (
            injury
            + f"Las coberturas de El Sol de México, La Jornada, UnoTV y DigitalMex ubican la volcadura de una pipa de gas "
            "en la autopista México-Pachuca, a la altura de San Pedro Xalostoc/Santa Clara, "
            "Ecatepec, Estado de México. La afectación fue en dirección a la Ciudad de México; "
            "el hecho ocurrió fuera de la capital. No añadimos causas ni un saldo distinto al "
            "que cada publicación atribuye a sus propias fuentes."
        )

    # La volcadura del 12 de noviembre fue en Toluca, Estado de México;
    # la vía afectada se dirige a CDMX. Contraste con SéUno Noticias y el
    # comunicado municipal Com. 1217/2026, sin atribuir el hecho a la capital.
    if (article.get("date") == "2026-11-12"
            and "paseo tollocan" in t
            and re.search(r"\bpipa\b", t)
            and re.search(r"\b(?:volcadur|vuelc)\w*\b", t)):
        return (
            f"De acuerdo con {source}, se reporta la volcadura de una pipa en Paseo Tollocan "
            "con dirección a la Ciudad de México. SéUno Noticias ubica el hecho en los carriles "
            "laterales, antes del puente de Pilares, a la altura de Santa María Totoltepec, "
            "Toluca, Estado de México. La cobertura informa que Bomberos de Toluca y Metepec "
            "atendían la emergencia y que los carriles laterales hacia CDMX permanecían cerrados. "
            "Al citar el comunicado municipal Com. 1217/2026, no reportó personas lesionadas "
            "al momento de su publicación. El incidente ocurrió fuera de CDMX, aunque afectó "
            "el acceso hacia la capital."
        )

    # Accidentes de motos, choques y siniestros: informar incluso si el hecho es
    # grave, sin inventar fallecimientos, lesiones, imágenes o circunstancias.
    if re.search(r"\b(?:accident\w*|choqu\w*|chocar|chocan|chocaron|choco|colisi[oó]n\w*|volcadur\w*|vuelc\w*|"
                 r"atropell\w*|arroll\w*|derrap\w*|siniestro vial)\b", t):
        vehicle=("una motocicleta" if re.search(r"\b(?:moto|motocicleta|motociclista)\w*\b", t)
                 else "un microbús" if re.search(r"\bmicrob[uú]s\b", t)
                 else "un autobús" if re.search(r"\bautob[uú]s\b", t)
                 else "una pipa de gas" if re.search(r"\b(?:pipas? de gas|gas lp)\b", t)
                 else "vehículos" if re.search(r"\b(?:automovil|auto|camion|trailer|tráiler|vehiculo)\w*\b", t)
                 else "personas o vehículos involucrados")
        if re.search(r"\b(?:mueren|murieron|fallecen|fallecieron|perdieron la vida|muertos|muertas|fallecidos|fallecidas)\b", t):
            outcome="El propio titular señala más de un fallecimiento, sin que esta ficha agregue cifras ni identidades."
        elif re.search(r"\b(?:fallec\w*|muert\w*|murio|sin vida|pierde la vida|"
                        r"perdio la vida|fatal|mortal|muere|murio|murió|mata|matan|mat[oó])\b", t):
            outcome="El propio titular señala un fallecimiento, sin que esta ficha agregue cifras ni identidades."
        elif re.search(r"\b(?:herid\w*|lesionad\w*|hospitalizad\w*)\b", t):
            outcome="El propio titular menciona personas lesionadas, sin datos médicos adicionales verificados."
        else:
            outcome="El encabezado no permite determinar por sí solo si hubo personas lesionadas o fallecidas."
        return (f"De acuerdo con {source}, se informa de un hecho vial relacionado con "
                f"{vehicle}{zone}. {outcome} "
                "Se requiere consultar la nota original para conocer el punto exacto, las "
                "circunstancias y los reportes oficiales, sin atribuir responsabilidades sin pruebas.")
    if ("imss" in t and re.search(r"\bprotest\w*\s+en\s+xalapa\s*;", t)):
        return (
            f"La nota de {source} sitúa la protesta de trabajadores del IMSS en Xalapa, Veracruz. "
            "El titular menciona agresiones contra compañeros en Puebla y CDMX, pero no confirma "
            "que la movilización haya ocurrido en esas ciudades. Consulta la publicación original "
            "para conocer los detalles de las demandas."
        )
    if "imss" in t and ("marcha" in t or "bloque" in t or "moviliza" in t):
        return (f"La cobertura de {source} se centra en movilizaciones de trabajadores "
                "del IMSS y en su posible o reportada repercusión sobre calles de Ciudad de México. "
                "Los trayectos y horarios deben revisarse en avisos recientes, pues una "
                "convocatoria no equivale a cierres confirmados durante todo el día.")
    if "marcha" in t or "concentraciones" in t or "bloqueos" in t:
        detail="una marcha y siete concentraciones" if "siete concentraciones" in t else "manifestaciones o bloqueos"
        return (f"Según la información destacada por {source}, {detail} forman parte de la "
                "jornada de movilidad capitalina. La ficha no demuestra por sí sola "
                "que todas las vías mencionadas sigan cerradas al momento de leerla.")
    has_metro = bool(re.search(r"\bmetro\b", t))
    has_metrobus = bool(re.search(r"\bmetrob[uú]s\b", t))
    has_tren_suburbano = bool(re.search(r"\btren suburbano\b", t))
    if has_metro and ("línea a" in t or "linea a" in t) and ("rehabilit" in t or "arreglo" in t or "suspensi" in t):
        return (f"El medio {source} recoge advertencias y demandas sobre el mantenimiento de "
                "la Línea A del Metro. Hablar de una posible suspensión no significa "
                "que el tramo haya sido cerrado: se requiere consultar el aviso oficial.")
    if ((has_metro or has_metrobus or has_tren_suburbano)
            and ("retras" in t or "atras" in t or "avance" in t or "estatus" in t
                 or "estaciones" in t or "estado del servicio" in t)):
        services = []
        if has_metro:
            services.append("Metro")
        if has_metrobus:
            services.append("Metrobús")
        if has_tren_suburbano:
            services.append("Tren Suburbano")
        if len(services) == 1:
            service_description = {
                "Metro": "del Metro de Ciudad de México",
                "Metrobús": "del Metrobús de Ciudad de México",
                "Tren Suburbano": "del Tren Suburbano",
            }[services[0]]
            description = "el servicio " + service_description
        else:
            service_names = ", ".join(services[:-1]) + " y " + services[-1]
            description = "los servicios de " + service_names + " en Ciudad de México"
        return (f"La nota de {source} reúne reportes sobre {description}. "
                "La operación puede cambiar durante el día y los informes de usuarios "
                "no son equivalentes a un comunicado oficial.")
    # Aprovechar agua de lluvia no equivale a un pronóstico meteorológico.
    if (
        "captación de agua de lluvia" in t
        or "captacion de agua de lluvia" in t
        or "captar agua de lluvia" in t
        or "captación pluvial" in t
        or "captacion pluvial" in t
        or "captación de lluvia" in t
        or "captacion de lluvia" in t
        or "calentadores solares" in t
        or "cosecha de lluvia" in t
    ):
        return (f"El titular de {source} aborda la captación y aprovechamiento de agua pluvial{zone}. "
                "Se trata de una práctica o iniciativa relacionada con el uso del agua; "
                "no es un aviso meteorológico. Para conocer su alcance y resultados "
                "es necesario consultar el reportaje original.")
    if "lluvia" in t or "chubasco" in t or "clima" in t or "nublado" in t:
        conditions=("lluvias ligeras" if "ligera" in t else
                    "chubascos" if "chubasco" in t else
                    "lluvias" if "lluvia" in t else "condiciones meteorológicas")
        return (f"El pronóstico recogido por {source} se refiere a {conditions}{zone}. "
                "Se trata de una previsión, no de una constatación de lluvia en cada calle. "
                "Las condiciones pueden variar según la hora y la colonia.")
    if "expropi" in t and ("predio" in t or "vivienda" in t):
        return (f"Según {source}, el titular informa sobre una expropiación o su anuncio "
                f"relacionado con predios destinados a vivienda pública{zone}. "
                "La ubicación, situación jurídica y alcance de la medida deben "
                "comprobarse en documentos oficiales; el anuncio no prueba su ejecución.")
    if "vivienda pública" in t or "vivienda social" in t:
        return (f"El medio {source} informa sobre una iniciativa o medida relacionada "
                f"con vivienda pública{zone}. Su alcance, condiciones y estado "
                "de aprobación requieren consultar la publicación completa y fuentes oficiales.")
    if "gentrific" in t or "airbnb" in t or "rentas" in t:
        return (f"El reportaje citado por {source} aborda los precios de vivienda o "
                f"los cambios residenciales{zone}. Las cifras y su metodología "
                "deben examinarse antes de concluir cuántas familias han sido desplazadas "
                "o qué tan representativos son determinados anuncios de renta.")
    if "energías renovables" in t or "energias renovables" in t:
        return (f"El medio {source} informa de una propuesta de colaboración entre la "
                "Ciudad de México y el Estado de México para impulsar energías renovables "
                "mediante incentivos privados. La ficha no confirma qué estímulos se "
                "aprobaron ni su fecha de entrada en vigor.")
    if "cempasúchil" in t or "cempasuchil" in t:
        return (f"La publicación de {source} pone el foco en dificultades que podrían "
                "afectar la comercialización del cempasúchil de Xochimilco. "
                "La producción de flor involucra a familias y productores locales; "
                "para explicar causas y alcances hacen falta los datos del reportaje.")
    if "afores" in t:
        return (f"Según {source}, una feria sobre administradoras del ahorro para el "
                "retiro se realiza o anuncia en Iztacalco. Antes de asistir conviene "
                "comprobar fechas, horarios y servicios directamente con la institución.")
    if "cultural" in t and ("asistencia" in t or "eventos" in t):
        return (f"La información que publica {source} analiza diferencias en la asistencia "
                "a eventos culturales por género. Para saber qué significa esta tendencia "
                "hacen falta los periodos, encuestas y metodología de la fuente.")
    if re.search(r"\b(?:obras? de teatro|cartelera teatral|funciones? de teatro)\b", t):
        period = " en noviembre" if "noviembre" in t else ""
        return (f"La nota de {source} reúne recomendaciones de obras de teatro para ver "
                f"en Ciudad de México{period}. La ficha no detalla títulos, sedes, horarios "
                "ni disponibilidad; conviene consultar la cartelera original antes de asistir.")
    if "concierto" in t:
        return (f"El medio {source} presenta conciertos o actividades musicales anunciadas "
                "en Ciudad de México. La programación, disponibilidad y costos pueden "
                "cambiar; comprueba los datos del organizador.")
    if "consultorios" in t and "issste" in t:
        return (f"El reporte atribuido a {source} habla de la incorporación de "
                "consultorios del ISSSTE en la capital. El dato del titular debe "
                "contrastarse con el comunicado institucional para conocer dónde "
                "operan y a qué pacientes atienden.")
    if "homicidio" in t and ("septiembre" in t or "62%" in t):
        return (f"Según cifras recogidas por {source}, las autoridades reportan "
                "una disminución de homicidios o delitos de alto impacto. "
                "Las comparaciones exigen conocer su periodo, fuente estadística y "
                "la forma en que se registraron los hechos.")
    if "autogobierno" in t or "penitenciarios" in t:
        return (f"{source} recoge declaraciones sobre la administración de los "
                "centros penitenciarios de la capital. El titular atribuye una postura "
                "a un funcionario; esa declaración debe diferenciarse de una "
                "evaluación independiente de la situación.")
    if "detien" in t or "caen dos" in t or "robar" in t or "asalt" in t:
        return (f"Una nota de {source} comunica un caso relacionado con una "
                f"detención o una presunta conducta delictiva{zone}. "
                "Es indispensable respetar la presunción de inocencia y no añadir "
                "acusaciones ni datos personales que el titular no acredita.")
    if ("centro" in t and ("evaluación laboral" in t or "evaluacion laboral" in t)) or ("inaugur" in t and "laboral" in t):
        return (f"De acuerdo con {source}, el titular informa de la inauguración "
                f"de un centro o servicio relacionado con evaluación laboral{zone}. "
                "Los servicios disponibles, requisitos y horarios requieren "
                "confirmación en la fuente y ante la institución responsable.")
    if "pérdida de empleos" in t or "perdida de empleos" in t:
        return (f"El medio {source} aborda una posible pérdida de empleos en "
                "la capital mediante una comparación con otra entidad. "
                "Los datos, el periodo y la metodología deben verificarse "
                "antes de sacar conclusiones sobre el mercado laboral.")
    if "reelegir" in t or "decretos" in t or "gobierno" in t:
        return (f"En su información, {source} aborda una decisión, declaración "
                "o debate relacionado con las instituciones de la ciudad. "
                "Conviene distinguir la intención anunciada de las resoluciones "
                "que hayan sido aprobadas y publicado oficialmente.")
    # Si el titular no encaja en una regla verificable, no inventar narrativa.
    return (f"La información publicada por {source} aborda un asunto que este portal "
            f"clasifica como {article.get('category') or 'CDMX'}. "
            "El encabezado contiene la referencia específica; sin acceso al cuerpo "
            "de la nota no corresponde agregar circunstancias que podrían ser falsas.")

def is_mauricio_tabe_fifth_report(article):
    """Identifica el informe de gobierno de Mauricio Tabe publicado el 12/11/2026."""
    title = _photo_fold(article.get("title"))
    source = _photo_fold(article.get("source"))
    return (
        str(article.get("date") or "") == "2026-11-12"
        and source == "sdpnoticias"
        and "mauricio tabe" in title
        and "quinto informe" in title
        and "miguel hidalgo" in title
    )


AICM_FLIGHT_SUSPENSION_SOURCE_URL = (
    "https://www.jornada.com.mx/noticia/2026/11/13/politica/"
    "aicm-reporta-afectaciones-de-vuelos-hacia-y-desde-estados-unidos-tras-restriccion-a-operaciones-aereas"
)


def is_la_jornada_aicm_flight_suspension(article):
    """Identifica el reporte del AICM sobre los vuelos afectados el 13/11/2026."""
    title = _photo_fold(article.get("title"))
    source = _photo_fold(article.get("source"))
    return (
        source == "la jornada"
        and str(article.get("date") or "") == "2026-11-13"
        and "aicm" in title
        and "10 mil 293 pasajeros" in title
        and "73 vuelos" in title
        and "suspension" in title
    )


def summarize(article):
    title=str(article.get("title") or "").strip()
    source=str(article.get("source") or "un medio periodístico").strip()
    category=str(article.get("category") or "CDMX")
    theme=TAGS.get(category,TAGS["CDMX"])
    folded_title=_photo_fold(title)
    if is_la_jornada_aicm_flight_suspension(article):
        return {
            "lead": (
                "La Jornada informó que la suspensión temporal de vuelos hacia y desde Estados Unidos "
                "afectó a 10,293 pasajeros y 73 vuelos del AICM: 29 demorados y 44 cancelados. "
                "Según la nota, después de reabrirse el espacio aéreo estadounidense, las operaciones "
                "se normalizarían de manera paulatina."
            ),
            "context": (
                "La afectación alcanzó a personas con vuelos entre el AICM y Estados Unidos. "
                "El medio reportó que el aeropuerto recomendó consultar directamente con las aerolíneas "
                "el estado de cada itinerario."
            ),
            "pending": (
                "Las cifras corresponden al reporte publicado el 13 de noviembre de 2026. "
                "La disponibilidad, los horarios y la regularización posterior deben confirmarse "
                "con el AICM, la AFAC y cada aerolínea."
            ),
            "method": (
                "Síntesis basada en la nota original de La Jornada del 13 de noviembre de 2026: "
                + AICM_FLIGHT_SUSPENSION_SOURCE_URL
                + ". Las cifras se atribuyen al reporte del AICM reproducido por el medio; "
                "no constituyen una verificación independiente."
            ),
        }
    if is_infobae_maria_leon_concert(article):
        return {
            "lead": (
                "Infobae informó que María León presentó «Era de Villana» en el Teatro Metropólitan "
                "de Ciudad de México la noche del 12 de noviembre de 2026. El reportaje sitúa el inicio "
                "a las 21:30 y el cierre a las 23:25; describe canciones de su etapa en Playa Limbo, "
                "su carrera solista y temas inéditos de su próximo álbum."
            ),
            "context": (
                "La nota menciona como invitados a Mar Lara, Julia Medina, Cristina León y Edwin Luna. "
                "También describe músicos, bailarines e interpretación en lengua de señas durante la presentación."
            ),
            "pending": (
                "La presentación ya ocurrió. El reportaje no confirma fechas futuras, disponibilidad de boletos "
                "ni nuevas sedes; esos datos requieren información posterior del organizador."
            ),
            "method": (
                "Síntesis basada en Infobae, 13 de noviembre de 2026: "
                + INFOBAE_MARIA_LEON_CONCERT_SOURCE_URL
                + ". Los horarios, invitados y repertorio se atribuyen al reportaje y no constituyen "
                "verificación independiente."
            ),
        }
    if is_capital_cdmx_care_budget(article):
        return {
            "lead": (
                "Capital CDMX informó que el Anexo 31, «Consolidación de una Sociedad de Cuidados», "
                "reúne 475,959.7 millones de pesos para 2027. El monto es nacional: la información "
                "publicada no permite determinar cuánto corresponde a la Ciudad de México ni cuántas "
                "familias capitalinas recibirán servicios."
            ),
            "context": (
                "El anexo agrupa recursos de múltiples programas y dependencias; no es una transferencia "
                "directa a la capital. Capital CDMX señala que el monto aumenta alrededor de 1.6% en "
                "términos nominales, pero disminuye 1.6% en términos reales frente a 2026."
            ),
            "pending": (
                "La nota no ofrece un desglose que permita asignar una cantidad a CDMX o a una alcaldía. "
                "Para comprobar el efecto local hacen falta datos por programa y territorio, padrones, "
                "ubicaciones de servicios, convenios y reportes de ejecución; no debe repartirse el total "
                "nacional por población ni presentarse como dinero ya recibido por las familias."
            ),
            "method": (
                "Síntesis basada en la publicación original de Capital CDMX del 12 de noviembre de 2026: "
                + CAPITAL_CDMX_CARE_BUDGET_SOURCE_URL
                + ". El monto y la variación presupuestaria se atribuyen al medio; no constituyen una "
                "auditoría independiente ni un desglose del gasto destinado a la capital."
            ),
        }
    if is_radio_formula_casa_ecologica(article):
        return {
            "lead": (
                "Radio Fórmula informó que el programa Casa Ecológica contempla instalar "
                "sistemas de captación pluvial, calentadores solares y huertos en 19 mil "
                "viviendas de la capital. Para 2025 y 2026 reportó una inversión de 356 "
                "millones de pesos; en Álvaro Obregón, la meta anunciada es beneficiar "
                "a 10 mil hogares."
            ),
            "context": (
                "La presentación se realizó en Santa Rosa Xochiac, alcaldía Álvaro Obregón. "
                "La iniciativa busca reducir el consumo de agua y gas y apoyar la producción "
                "de alimentos en los hogares."
            ),
            "pending": (
                "La inversión, las viviendas y las instalaciones descritas son cifras y metas "
                "atribuidas al Gobierno de la Ciudad de México y a la cobertura periodística; "
                "no deben presentarse como equipos ya instalados en cada hogar. Los avances "
                "por colonia requieren confirmación de la Secretaría del Medio Ambiente."
            ),
            "method": (
                "Síntesis basada en Radio Fórmula, 12 de noviembre de 2026: "
                + RADIO_FORMULA_CASA_ECOLOGICA_SOURCE_URL
                + ". Se contrastaron ubicación y objetivos con La Jornada, 12 de noviembre "
                "de 2026: " + LA_JORNADA_CASA_ECOLOGICA_SOURCE_URL
                + ". Las cifras se atribuyen a las fuentes y no constituyen una auditoría independiente."
            ),
        }
    if is_mauricio_tabe_fifth_report(article):
        return {
            "lead": (
                "Durante su Quinto Informe de Gobierno en Miguel Hidalgo, Mauricio Tabe dijo "
                "que la estrategia Blindar MH duplicó el presupuesto de seguridad y triplicó "
                "la presencia de policías y patrullas. También reportó 1,770 cámaras y la "
                "reiluminación de 150 calles en un año. Son cifras y resultados expuestos por "
                "el alcalde, no una verificación independiente."
            ),
            "context": (
                "El balance presentado incluyó seguridad, iluminación, recuperación de parques "
                "y espacios públicos y programas sociales para mujeres. La cobertura de La Prensa "
                "también recoge la clausura de una obra en Sócrates 211 por un nivel excedente."
            ),
            "pending": (
                "Las cifras de seguridad, cámaras y calles intervenidas se atribuyen a Mauricio "
                "Tabe y no se verifican de forma independiente en estas notas. Para confirmarlas "
                "se requieren los indicadores oficiales, el presupuesto aprobado y los expedientes "
                "públicos de las obras."
            ),
            "method": (
                "Síntesis basada en la nota de SDP Noticias del 12 de noviembre de 2026: "
                + SDPNOTICIAS_MAURICIO_TABE_REPORT_SOURCE_URL
                + " y contraste de cobertura con La Prensa: "
                + LA_PRENSA_MAURICIO_TABE_REPORT_SOURCE_URL
                + ". Las cifras se atribuyen al alcalde; no constituyen una auditoría independiente."
            ),
        }
    if (re.search(r"\bcablebus\b", folded_title)
            and re.search(r"\blinea 1\b", folded_title)
            and re.search(r"\bsuspend\w*\b", folded_title)
            and re.search(r"\blluvia\b", folded_title)):
        return {
            "lead": (
                f"El titular de {source} informa que, durante la alerta por lluvia fuerte en CDMX, "
                "la Línea 1 del Cablebús suspendió el servicio. El índice RSS no precisa la hora "
                "ni las estaciones afectadas."
            ),
            "context": (
                "La Línea 1 conecta Indios Verdes y Cuautepec, en la alcaldía Gustavo A. Madero. "
                "La afectación corresponde a la movilidad del norte de la capital."
            ),
            "pending": (
                "El titular y el índice RSS no indican la hora exacta de suspensión, las estaciones "
                "afectadas ni cuándo se reanudó el servicio. El estado operativo debe verificarse en "
                "los avisos del Servicio de Transportes Eléctricos antes de viajar."
            ),
            "method": (
                "Síntesis basada en el titular de N+ y en la ficha oficial del Servicio de Transportes "
                "Eléctricos sobre la ruta de Línea 1: https://www.ste.cdmx.gob.mx/cablebus. "
                "No equivale a lectura íntegra de la nota ni confirma el estado actual del servicio."
            ),
        }
    if is_infobae_ballet_zapatilla(article):
        return {
            "lead": (
                "Infobae informó que la función gratuita de «La Zapatilla de Cristal», a cargo "
                "de Ballet House Classical Art, está programada para el 28 de noviembre de 2026 "
                "a las 13:00 horas en Utopía Mixiuhca, Viaducto Río de la Piedad 6, colonia "
                "Granjas México, alcaldía Iztacalco. Según la nota, el acceso será libre y no "
                "requiere registro ni boleto."
            ),
            "context": (
                "La sede es Utopía Mixiuhca, en Iztacalco. La actividad corresponde a la agenda "
                "cultural de la ciudad; no es una noticia del Sistema de Transporte Colectivo Metro."
            ),
            "pending": (
                "La fecha, el horario y las condiciones de acceso pueden cambiar. Conviene "
                "confirmarlos con la sede o la organización antes de asistir; la gratuidad y "
                "la ausencia de registro se atribuyen a la publicación de Infobae."
            ),
            "method": (
                "Síntesis basada en la nota de Infobae del 12 de noviembre de 2026: "
                + INFOBAE_BALLET_ZAPATILLA_SOURCE_URL
                + ". La fecha, hora, sede y condiciones de acceso se atribuyen a ese medio; "
                "no se presenta como confirmación independiente del organizador."
            ),
        }
    if is_pulque_barbacoa_fair(article):
        return {
            "lead": (
                "La 22.ª Feria Regional del Pulque y la Barbacoa se realizará del 13 al 15 de "
                "noviembre de 2026, de 8:00 a 19:00 horas, en la explanada de la Alcaldía "
                "La Magdalena Contreras, José Moreno Salido s/n, colonia Barranca Seca. "
                "El acceso al recinto será gratuito; los alimentos, bebidas y artesanías "
                "se pagan por consumo."
            ),
            "context": (
                "El encuentro reúne barbacoa, pulque natural y curado, antojitos, artesanías "
                "y música en vivo. Es una actividad gastronómica y cultural de La Magdalena Contreras."
            ),
            "pending": (
                "La cartelera musical y la oferta de cada puesto pueden cambiar. Se recomienda "
                "confirmar horarios y actividades con la alcaldía antes de acudir; la entrada "
                "gratuita no significa que los alimentos o bebidas sean gratuitos."
            ),
            "method": (
                "Síntesis de datos coincidentes en Infobae, 6 de noviembre de 2026: "
                + INFOBAE_PULQUE_BARBACOA_SOURCE_URL
                + " y POSTA México, 6 de noviembre de 2026: "
                + POSTA_PULQUE_BARBACOA_SOURCE_URL
                + ". La imagen, cuando se muestra, es ilustrativa y no corresponde a la feria."
            ),
        }
    if is_huixtla_migrant_caravan(article):
        if source.casefold() == "infobae":
            return {
                "lead": (
                    "Infobae informó que la caravana migrante «Dios con nosotros», integrada por cerca "
                    "de 500 personas según estimaciones citadas por el medio, permaneció en Huixtla, "
                    "Chiapas, y esperaba a otros integrantes antes de continuar hacia Escuintla y la "
                    "Ciudad de México. La capital es un destino previsto, no el lugar donde ocurrió la llegada."
                ),
                "context": (
                    "La ubicación del hecho es Huixtla, Chiapas, fuera de CDMX. Infobae señala que el grupo "
                    "descansó en el barrio Guadalupe y que la ruta prevista continuaría por la carretera "
                    "costera hacia Escuintla."
                ),
                "pending": (
                    "Las estimaciones variaron durante el recorrido: Infobae citó cerca de 500 personas "
                    "en Huixtla y señaló que, al sumarse otros contingentes, el total podría acercarse "
                    "a 1,500. El número y la ruta requieren actualización con autoridades y coberturas "
                    "posteriores; no se presentan como un conteo oficial."
                ),
                "method": (
                    "Síntesis editorial basada en la publicación de Infobae del 13 de noviembre de 2026, "
                    "que atribuye las estimaciones a diarios locales y cita coberturas de Diario de Chiapas "
                    "y Diario del Sur. No equivale a verificación independiente del número de personas "
                    "ni de su itinerario."
                ),
            }
        return {
            "lead": (
                "El Financiero reportó que la caravana migrante «Dios con nosotros» llegó a Huixtla, "
                "Chiapas, y que más de 500 personas avanzaban por ese estado rumbo a CDMX. "
                "La referencia a la capital es el destino del recorrido, no el lugar donde ocurrió la llegada."
            ),
            "context": (
                "La ubicación indicada por el titular es Huixtla, Chiapas, fuera de CDMX. "
                "La nota se conserva por la relación del recorrido con la capital, pero no se presenta "
                "como un hecho ocurrido en una alcaldía."
            ),
            "pending": (
                "El tamaño del contingente y su itinerario pueden cambiar. El índice RSS no reproduce "
                "el reportaje íntegro; cualquier actualización de la ruta debe corroborarse con autoridades "
                "migratorias y coberturas posteriores."
            ),
            "method": (
                "Síntesis editorial basada en el titular y los metadatos de El Financiero del 12 de noviembre "
                "de 2026. No equivale a lectura íntegra del reportaje ni a verificación independiente del "
                "número de personas."
            ),
        }
    if is_vc_fatal_trailer_incident(article):
        return {
            "lead": (
                "El Gráfico informó que un hombre conocido como «El Morenito» murió después de ser "
                "atropellado y arrastrado por un tráiler en el cruce de avenida del Taller y Lorenzo Boturini, "
                "colonia Lorenzo Boturini, alcaldía Venustiano Carranza. El medio atribuyó al operador un "
                "presunto cruce de semáforo en rojo; esa versión se atribuye al reportaje y no se presenta "
                "como determinación oficial."
            ),
            "context": (
                "El hecho ocurrió en Venustiano Carranza y corresponde a un siniestro vial fatal. "
                "Se omite la descripción gráfica del accidente y no se atribuye responsabilidad penal."
            ),
            "pending": (
                "La mecánica del accidente y cualquier responsabilidad deben confirmarse con la FGJCDMX "
                "y los informes de tránsito. La versión sobre el semáforo en rojo es la que atribuye "
                "El Gráfico al reporte, no una resolución judicial."
            ),
            "method": (
                "Síntesis editorial basada en la publicación de Tania Aguilar en El Gráfico, "
                "12 de noviembre de 2026: " + EL_GRAFICO_VC_TRAILER_SOURCE_URL
                + ". No constituye verificación independiente."
            ),
        }
    # Encabezar con el dato específico y comprobable del RSS, no con una
    # explicación genérica que pueda corresponder a otra noticia.
    first=(f"De acuerdo con {source}, el titular publicado es: «{title}». "
           + _reported_angle(article))
    context=theme["importance"]
    pending=theme["verify"]+" El índice RSS no reproduce el reportaje íntegro, por lo que no añadimos nombres, cantidades ni circunstancias que aquí no podamos comprobar."
    method="Síntesis editorial propia elaborada a partir del titular y sus metadatos; no equivale a lectura del artículo íntegro."
    if is_coyotepec_highway_crash(article) and _photo_fold(source) == "infobae":
        return {
            "lead": (
                "Infobae reportó que el choque múltiple ocurrió el 12 de noviembre en Coyotepec, "
                "Estado de México, cuando un tractocamión impactó a tres autobuses que transportaban "
                "estudiantes rumbo al Bosque de Chapultepec. La nota reportó al menos 27 personas "
                "lesionadas y señaló que CAPUFE confirmó la reapertura de la autopista hacia CDMX "
                "tras casi cuatro horas de cierre."
            ),
            "context": (
                "El hecho ocurrió en Coyotepec, Estado de México, fuera de la capital. La referencia "
                "a CDMX corresponde al destino del viaje y al sentido de la autopista, no al lugar "
                "del choque."
            ),
            "pending": (
                "Infobae reportó que aún persistía carga vehicular después de la reapertura. El estado "
                "actual debe comprobarse con CAPUFE antes de viajar; la nota no establece una causa "
                "definitiva del accidente."
            ),
            "method": (
                "Síntesis editorial basada en la nota de Infobae consultada el 13 de noviembre de "
                "2026: " + INFOBAE_COYOTEPEC_HIGHWAY_CRASH_SOURCE_URL
                + ". El saldo y la reapertura se atribuyen al medio; no se presentan como una "
                "verificación independiente de CDMX AL MEMENTO."
            ),
        }
    if is_coyotepec_highway_crash(article):
        return {
            "lead": (
                "N+ informó que tres autobuses de turismo y un tractocamión chocaron el 12 de "
                "noviembre de 2026 en el kilómetro 49+100 de la autopista México-Querétaro, "
                "a la altura de Coyotepec, Estado de México. La nota reportó al menos 27 "
                "personas lesionadas y el cierre total de la vía hacia CDMX; CAPUFE realizaba "
                "maniobras para retirar las unidades y limpiar la carretera."
            ),
            "context": (
                "El siniestro ocurrió en Coyotepec, Estado de México, fuera de la capital. "
                "Es relevante para quienes viajan hacia CDMX porque el cierre afectó el sentido "
                "de ingreso a la ciudad."
            ),
            "pending": (
                "El saldo de personas lesionadas y la reapertura pueden cambiar. Antes de salir, "
                "consulta los avisos vigentes de CAPUFE y Guardia Nacional; N+ señaló como "
                "alternativas la carretera libre San Miguel Jagüeyes y el Circuito Exterior "
                "Mexiquense."
            ),
            "method": (
                "Síntesis editorial basada en la nota de N+ publicada el 12 de noviembre de "
                "2026: https://www.nmas.com.mx/estado-de-mexico/seguridad/accidentes/"
                "accidente-mexico-queretaro-hoy-12-noviembre-2026-choque-autobuses-pasajeros-"
                "cierre-cdmx/. El saldo y las condiciones viales son datos atribuidos al medio, "
                "no una verificación independiente de CDMX AL MEMENTO."
            ),
        }
    if is_imagen_tlalpan_dog_rescue(article):
        return {
            "lead": (
                "Imagen Televisión reportó que vecinos rescataron a una perrita en Tlalpan tras "
                "señalamientos de presunto abuso sexual por parte de un hombre. El titular no informa "
                "de una detención ni de una resolución judicial; no añadimos esos datos."
            ),
            "context": (
                "El caso se ubica en Tlalpan y se refiere a un presunto delito contra un animal; "
                "la información debe evitar detalles gráficos y respetar la presunción de inocencia."
            ),
            "pending": (
                "No se dispone aquí del reportaje íntegro ni de confirmación oficial sobre el estado "
                "de la perrita, la investigación o una posible detención; esos datos deben corroborarse "
                "con la SSC, FGJCDMX y PAOT."
            ),
            "method": (
                "Síntesis editorial basada en el titular y los metadatos de Imagen Televisión del "
                "12 de noviembre de 2026; no equivale a lectura del reportaje íntegro ni a verificación "
                "independiente."
            ),
        }
    if is_infobae_tlalpan_animal_abuse(article):
        return {
            "lead": (
                "Infobae informó que la SSC detuvo a un hombre tras un reporte de agresión en la "
                "colonia Pedregal de San Nicolás Cuarta Sección, alcaldía Tlalpan. La nota recoge "
                "señalamientos de vecinos y activistas por presunta violencia contra animales; "
                "la responsabilidad no está establecida y corresponde a las autoridades determinarla."
            ),
            "context": (
                "El caso se ubica en Tlalpan. La detención informada por la SSC debe distinguirse "
                "de los señalamientos de vecinos y activistas, que siguen sujetos a investigación."
            ),
            "pending": (
                "La situación jurídica del detenido y el estado de las denuncias ante PAOT y FGJCDMX "
                "deben confirmarse con esas autoridades."
            ),
            "method": (
                "Síntesis editorial basada en Infobae, 12 de noviembre de 2026: "
                "https://www.infobae.com/mexico/2026/11/12/detienen-a-presunto-abusador-sexual-de-animales-en-situacion-de-calle-en-cdmx-activistas-piden-que-las-investigaciones-lleguen-a-fondo/. Se distingue la detención informada por la SSC de los señalamientos "
                "de terceros; no se presentan como hechos probados."
            ),
        }
    if is_la_prensa_tlalpan_animal_case(article):
        return {
            "lead": (
                "La Prensa informó que efectivos de la SSC intervinieron para rescatar a un hombre "
                "de ser linchado y lo pusieron a disposición del Ministerio Público. El titular "
                "relaciona la detención con presuntos señalamientos de maltrato animal en Tlalpan; "
                "no se trata de una sentencia."
            ),
            "context": (
                "El caso se ubica en Tlalpan y debe informarse como una detención por señalamientos, "
                "no como una responsabilidad probada."
            ),
            "pending": (
                "La situación jurídica del detenido y el avance de la investigación deben confirmarse "
                "con la SSC y la FGJCDMX."
            ),
            "method": (
                "Síntesis editorial basada en la publicación de La Prensa del 12 de noviembre de 2026, "
                "firmada por Rodrigo Alarcon: https://oem.com.mx/la-prensa/policiaca/detienen-a-otro-presunto-maltratador-de-animales-en-tlalpan-33095643. El extracto visible no reproduce "
                "el reportaje íntegro y no constituye una verificación independiente."
            ),
        }
    if is_san_juan_del_rio_autopista57_closure(article):
        return {
            "lead": (
                "La publicación de El Sol de San Juan del Río, firmada por Mario Luna / Diario de Querétaro, "
                "informa que cierres producidos por accidentes mantienen filas kilométricas de vehículos "
                "en la autopista 57, en territorio de San Juan del Río, Querétaro. El extracto no precisa "
                "el número de accidentes, el tramo exacto ni su duración, por lo que no añadimos esas cifras."
            ),
            "context": (
                "La afectación descrita está en San Juan del Río, Querétaro, fuera de la Ciudad de México. "
                "El aviso es relevante para quienes viajan hacia CDMX por la autopista 57."
            ),
            "pending": (
                "El punto exacto, la duración de los cierres y la situación actual deben confirmarse "
                "con CAPUFE y Guardia Nacional antes de viajar."
            ),
            "method": (
                "Síntesis editorial basada en la publicación de El Sol de San Juan del Río del 12 de "
                "noviembre de 2026, firmada por Mario Luna / Diario de Querétaro: "
                "https://oem.com.mx/elsoldesanjuandelrio/policiaca/toma-precauciones-si-viajas-a-la-cdmx-autopista-57-esta-detenida-33095499. El extracto visible no reproduce el reportaje íntegro y no constituye "
                "una verificación independiente."
            ),
        }
    if (article.get("date") == "2026-11-12"
            and "paseo tollocan" in title.casefold()
            and re.search(r"\bpipa\b", title.casefold())
            and re.search(r"\b(?:volcadur|vuelc)\w*\b", title.casefold())):
        return {
            "lead": first,
            "context": (
                "La volcadura ocurrió en Toluca, Estado de México; el cierre de los carriles "
                "laterales afectaba a quienes se dirigían hacia la Ciudad de México. No fue "
                "un incidente ocurrido dentro de una alcaldía capitalina."
            ),
            "pending": (
                "La cobertura de SéUno Noticias, publicada a las 08:46 del 12 de noviembre, "
                "indicó que no había personas lesionadas reportadas en el comunicado citado. "
                "La reapertura de los carriles y el estado posterior del contenedor requieren "
                "una actualización de las autoridades de Toluca."
            ),
            "method": (
                "Síntesis editorial basada en el titular de Diario Evolución y el contraste "
                "con SéUno Noticias del 12 de noviembre de 2026 (08:46), que cita el comunicado "
                "municipal Com. 1217/2026: "
                "https://seunonoticias.mx/2026/11/12/que-paso-en-paseo-tollocan-pipa-vuelca-antes-de-pilares/. "
                "No constituye una verificación independiente del comunicado."
            ),
        }
    if (
        source.casefold() == "la jornada"
        and _photo_fold(title) == _photo_fold("CDMX: 95% de la población no puede comprar vivienda")
    ):
        return {
            "lead": (
                "El reportaje de La Jornada precisa que el 95% de la población no puede adquirir "
                "la oferta de vivienda de alto costo en la zona central de CDMX; no se refiere a "
                "toda la oferta habitacional de la ciudad. Cita el Indicador Banorte de Precios "
                "de la Vivienda (Inbaprevi): $59,829 por m² en CDMX frente a $32,495 a nivel "
                "nacional, y recoge análisis sobre especulación del suelo y desplazamiento residencial."
            ),
            "context": (
                "El encarecimiento del suelo y de la vivienda condiciona el acceso a la compra "
                "y la permanencia de residentes en colonias centrales."
            ),
            "pending": (
                "Las cifras son las citadas por La Jornada a partir del Inbaprevi y del análisis "
                "de Monopolio; deben leerse con el indicador y el periodo que menciona el reportaje. "
                "El 95% alude a la oferta cara de la zona central, no a toda vivienda disponible en CDMX."
            ),
            "method": (
                "Síntesis editorial propia basada en el reportaje completo de La Jornada, publicado "
                "el 12 de noviembre de 2026; no constituye una verificación independiente de los "
                "indicadores ni de las declaraciones."
            ),
        }
    if (article.get("date") in {"2026-11-11", "2026-11-12"}
            and re.search(r"\bpipa\b", title.casefold())
            and re.search(r"m[eé]xico[- ]pachuca", title.casefold())):
        method = ("Síntesis editorial propia. La ubicación se contrastó con coberturas de "
                  "El Sol de México, La Jornada, UnoTV y DigitalMex del 11 de noviembre de 2026; "
                  "no equivale a lectura íntegra de la fuente original.")
    if (
        source.casefold() == "tv azteca"
        and "explosión de gas en local de azcapotzalco" in title.casefold()
        and "baches, socavones" in title.casefold()
    ):
        # El encabezado de Google News describe un bloque de una página en vivo;
        # no es el título real de la página de TV Azteca ni una nota exclusiva.
        first = (
            f"Google News muestra el encabezado: «{title}». "
            "La página original de TV Azteca se titula "
            "«Accidentes, afectaciones y percances en CDMX | EN VIVO» y reúne varios incidentes. "
            "En su actualización del 11 de noviembre de 2026 a las 20:17, el medio reportó "
            "una explosión por acumulación de gas en un local de Azcapotzalco y señaló que "
            "los servicios de emergencia estaban en el lugar. La misma página reúne otros "
            "accidentes y afectaciones viales; no es una nota dedicada exclusivamente a la explosión."
        )
        context = (
            "Es importante distinguir la emergencia por gas de los otros percances viales "
            "incluidos en la misma cobertura, para no mezclar incidentes ni sus datos."
        )
        pending = (
            "El saldo de personas lesionadas, la causa exacta, los daños y la situación posterior "
            "deben comprobarse en las actualizaciones de TV Azteca y los avisos de las autoridades; "
            "el primer reporte no confirma por sí solo el desenlace."
        )
        method = (
            "Síntesis editorial propia basada en el encabezado de Google News y la página en vivo "
            "de TV Azteca, consultada el 11 de noviembre de 2026; no constituye verificación independiente."
        )
    elif ("buen fin 2026" in title.casefold() and "ssc" in title.casefold()
            and "seguridad ciudadana" in source.casefold()):
        method="Síntesis editorial basada en el comunicado oficial de la SSC publicado el 11 de noviembre de 2026; cifras y calendario atribuidos a la dependencia, sin verificación independiente."
        pending="El horario, los puntos de vigilancia y cualquier ajuste del operativo deben confirmarse en los avisos de la SSC durante el Buen Fin. El comunicado describe un despliegue previsto; no es un balance de incidentes."
    elif ("lgbtttiq" in title.casefold() and source.casefold().replace(" ", "") in {"24-horas", "24horas"}):
        method="Síntesis editorial basada en el cuerpo de la nota de 24-horas; los datos se atribuyen al medio y a los lineamientos que cita, sin verificación independiente."
    return {"lead":first,"context":context,"pending":pending,"method":method}

def _load(path,key):
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(key,[])
    except (OSError,ValueError,TypeError):
        return []

def verified_event_photo(article, catalog=None):
    """Requiere cotejo editorial explícito del hecho, autor, origen y licencia.

    Un título similar, una búsqueda en Commons o una foto subida recientemente
    NO demuestran por sí solos que la imagen corresponda al acontecimiento.
    """
    records = catalog if catalog is not None else _load(VERIFIED_EVENTS, "photos")
    if not isinstance(records, list):
        return None
    url = str(article.get("url") or "")
    title = str(article.get("title") or "").strip()
    if not url.startswith("https://news.google.com/rss/articles/") or not title:
        return None
    for p in records:
        if not isinstance(p, dict) or p.get("article_url") != url:
            continue
        if str(p.get("article_title") or "").strip().casefold() != title.casefold():
            continue
        if p.get("event_match_confirmed") is not True or p.get("rights_confirmed") is not True:
            continue
        image = str(p.get("url") or "")
        if not (re.fullmatch(r"/assets/fotos/[a-z0-9_-]+\.jpg", image)
                and (ROOT / image.lstrip("/")).is_file()
                or re.match(r"^https://(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/", image)):
            continue
        source = str(p.get("source") or "")
        evidence = str(p.get("evidence_url") or "")
        author = str(p.get("author") or "").strip()
        license_name = str(p.get("license") or "").strip()
        license_url = str(p.get("licenseUrl") or "")
        reviewer = str(p.get("reviewed_by") or "").strip()
        reviewed_at = str(p.get("reviewed_at") or "")
        if not (source.startswith("https://commons.wikimedia.org/wiki/File:")
                and evidence.startswith("https://")
                and author and len(author) <= 140 and reviewer
                and 0 < len(reviewer) <= 100):
            continue
        try:
            if not datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")).tzinfo:
                continue
        except (TypeError, ValueError):
            continue
        rights = re.fullmatch(r"CC BY(-SA)? (2\.0|2\.5|3\.0|4\.0)", license_name, re.I)
        if rights:
            slug = "by-sa" if rights.group(1) else "by"
            expected = f"https://creativecommons.org/licenses/{slug}/{rights.group(2)}/"
        elif license_name.upper() in ("CC0", "CC0 1.0"):
            expected = "https://creativecommons.org/publicdomain/zero/1.0/"
        else:
            continue
        if not license_url.startswith(expected):
            continue
        return {
            "id": "hecho_" + hashlib.sha256((url + source).encode()).hexdigest()[:20],
            "kind": "hecho", "verified": True,
            "url": image, "source": source, "author": author,
            "license": license_name, "licenseUrl": license_url,
            "topic": str(p.get("topic") or title)[:150],
            "evidence_url": evidence, "reviewed_at": reviewed_at,
        }
    return None


def _pool():
    catalog=_load(ARCHIVE_PHOTOS,"photos")
    recent=_load(RECENT_PHOTOS,"photos")
    borough=_load(BOROUGH_PHOTOS,"photos")
    photos=[]
    # La fototeca ampliada incluye 1,117 fotos con descriptores y créditos.
    # Buscar por tema es más preciso que asignar la primera imagen de una categoría.
    for item in (_load(TOPIC_PHOTOS,"photos")+_load(NEWS_PHOTOS,"photos")):
        if not isinstance(item,dict):
            continue
        photo_id=str(item.get("id") or "")
        url=str(item.get("url") or "")
        source=str(item.get("source") or "")
        if not re.fullmatch(r"[a-z0-9_]+",photo_id):
            continue
        if not (re.fullmatch(r"/assets/fotos/[a-z0-9_-]+\.jpg",url) or
                re.match(r"https://(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/",url)):
            continue
        if not (source.startswith("https://commons.wikimedia.org/wiki/File:")
                and item.get("author") and item.get("license")
                and str(item.get("licenseUrl") or "").startswith("https://creativecommons.org/")):
            continue
        keywords=item.get("keywords")
        photos.append(dict(
            id=photo_id,kind="representativa",url=url,
            category=item.get("category","CDMX"),borough="",
            topic=str(item.get("topic") or "")[:150],
            keywords=[str(word)[:100] for word in keywords[:8]] if isinstance(keywords,list) else [],
            author=item["author"],license=item["license"],
            licenseUrl=item["licenseUrl"],source=source))
    # Excluye piezas con lugar no identificado, fuera de CDMX o duplicados.
    unsuitable=re.compile(r"louisville|kentucky|zacatecas|chihuahua|san francisco|"
                          r"california|el paso street|paleando nieve|old new city|"
                          r"cloudy \(|aesthetic|harmony \(|valle destrucci[oó]n|"
                          r"v of \(|last sunlight|palace of fine arts \(",re.I)
    for item in catalog:
        photo_id=str(item.get("id") or "")
        if not re.fullmatch(r"archivo_[a-z0-9_]+",photo_id):continue
        filename=str(item.get("file") or "")
        if unsuitable.search(filename):continue
        if not str(item.get("source","")).startswith("https://commons.wikimedia.org/wiki/File:"):continue
        photos.append(dict(id=photo_id,kind="representativa",url="/assets/fotos/"+photo_id+".jpg",
                           category=item.get("category","CDMX"),borough="",
                           topic=item.get("topic") or filename,
                           author=item.get("author"),license=item.get("license"),
                           licenseUrl=item.get("licenseUrl",""),source=item["source"]))
    for item in recent:
        if not item.get("reviewed_location"):continue
        if not str(item.get("source","")).startswith("https://commons.wikimedia.org/wiki/File:"):continue
        url=str(item.get("url") or "")
        if not url.startswith(("https://thumb.wikimedia.org/wikipedia/commons/",
                               "https://upload.wikimedia.org/wikipedia/commons/")):continue
        photos.append(dict(id=item.get("id"),kind="representativa",url=url,category=item.get("category","CDMX"),
                           borough="",topic=item.get("topic") or "Ciudad de México",
                           author=item.get("author"),license=item.get("license"),
                           licenseUrl=item.get("licenseUrl",""),source=item["source"]))
    for item in borough:
        slug=str(item.get("slug") or "")
        if not re.fullmatch(r"[a-z-]+",slug):continue
        photos.append(dict(id="alcaldia_"+slug,kind="representativa",url="/assets/alcaldias/"+slug+".jpg",
                           category="CDMX",borough=item.get("name",""),
                           topic=item.get("caption","Ciudad de México"),
                           author=item.get("author"),license=item.get("license"),
                           licenseUrl=item.get("licenseUrl",""),source=item.get("source")))
    # Deduplicar por página original de Commons para evitar atribuciones distintas.
    unique={}
    for p in photos:
        src=p.get("source")
        if src and p.get("url") and p.get("author") and p.get("license"):
            unique.setdefault(src,p)
    return list(unique.values())


# Sí se informa sobre accidentes y hechos graves, incluso con material sensible
# verificado. Solo se evita presentar fotos de otros siniestros como si fueran actuales.
SENSITIVE_CONTEXT = re.compile(
    r"\b(?:incidente|colapso|accidente|siniestro|victimas|fallecidos|"
    r"marcha del orgullo|8 de marzo|manifestacion por|homenaje a)\b"
)

# Se inferiere el tema del titular antes de recurrir a la categoría RSS.
# En el feed general muchas noticias de Metro, clima o cultura figuran como CDMX.
SUBJECT_RULES = (
    (r"\b(?:grupos? criminales?|organizaciones? criminales?|crimen organizado)\b", "Seguridad"),
    # Las muertes violentas y condenas judiciales no son temas genéricos de CDMX.
    (r"\b(?:ejecutan|ejecutad\w*|ejecucion|matan|balazos|asesinan|homicidio|condenad[oa]s?|condenan|prision)\b", "Seguridad"),
    # Las explosiones de gas e incendios se tratan como emergencias, no como baches o drenaje.
    (r"\b(?:pipas? de gas|gas lp|explosion(?:es)? de gas|tanques? de gas|fugas? de gas|acumulacion de gas|estalla\s+(?:un\s+)?tanque(?:\s+de\s+gas)?|incendios?)\b", "Seguridad"),
    # El RSS puede etiquetar temas recreativos o tecnológicos como Seguridad.
    (r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b", "Movilidad"),
    (r"\b(?:robot|robots|robotica|robotico|roboticos)\b", "CDMX"),
    (r"\b(?:metrobus|cablebus|trolebus|ecobici|ciclovia)\b", "Movilidad"),
    (r"\b(?:metro|linea \d{1,2}|linea [ab]|tren ligero)\b", "Metro"),
    (r"\b(?:perro|perrito|mascota|gato|animal|fauna|veterinari)\w*\b", "Medio Ambiente"),
    (r"\b(?:lluvia|tormenta|clima|inundacion|contaminacion|arbol|bosque)\w*\b", "Medio Ambiente"),
    (r"\b(?:hospital|clinica|drenaje|bache|basura|abasto|mercado|agua potable)\w*\b", "Servicios"),
    (r"\b(?:catrina|dia de muertos|cempasuchil|concierto|desfile|museo|"
     r"festival|exposicion|teatro|cultura)\w*\b", "Cultura"),
    (r"\b(?:hoy no circula|contingencia ambiental|holograma|verificacion vehicular|"
     r"marcha|bloqueo|trafico|carretera|movilidad|vialidad|"
     r"gran premio|formula 1|autodromo|circuito|automovili)\w*\b", "Movilidad"),
    (r"\b(?:policia|patrulla|fiscalia|robo|homicidio|detenid|"
     r"asalto|extorsion|delito|investigacion)\w*\b", "Seguridad"),
    (r"\b(?:alcalde|gobierno|congreso|presupuesto|secretaria)\w*\b", "Gobierno"),
)
STOP_WORDS = {
    "ciudad","mexico","cdmx","noticia","noticias","hoy","ayer","mañana",
    "este","esta","estos","estas","para","sobre","entre","ante","desde",
    "tras","segun","este","viernes","sabado","domingo","lunes","martes",
    "miercoles","jueves","octubre","noviembre","2026","2025","del","las",
    "los","una","uno","unos","unas","que","con","por","cuando","como",
    "cual","sera","seran","tiene","habra","hace","deja","al","la","el",
    "son","sus","todo","tambien","reportan","reporta","informa","nuevo",
    "nueva","capital","mexicana","mexicano","zona","calle","calles",
}
RELATED_WORDS = (
    (r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b",
     ("bici", "bicicleta", "bicicletas", "ciclista", "ciclistas", "ciclovia", "ecobici", "cicloton")),
    (r"\b(?:perro|perrito|mascota|gato|animal|fauna)\w*\b",
     ("animal", "animales", "fauna", "mascota", "veterinario")),
    (r"\b(?:policia|patrulla|fiscalia|detenid|robo|asalto)\w*\b",
     ("policia", "patrulla", "seguridad")),
    (r"\b(?:lluvia|inundacion|tormenta|clima)\w*\b",
     ("lluvia", "agua", "clima", "nubes", "cielo")),
    (r"\b(?:marcha(?:s)?|protest\w*|manifestacion(?:es)?|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|movilizacion(?:es)?|concentracion(?:es)?|planton(?:es)?)\b",
     ("marcha", "protesta", "manifestacion", "manifestantes", "bloqueo",
      "movilizacion", "concentracion", "planton", "cacerolazo",
      "trabajadores", "repartidores", "motociclistas")),
    (r"\b(?:catrina|dia de muertos|desfile)\w*\b",
     ("catrina", "catrinas", "desfile")),
    (r"\b(?:automovili|formula 1|gran premio|autodromo|circuito)\w*\b",
     ("auto", "automovil", "vehiculo", "transito", "autodromo")),
    (r"\b(?:hoy no circula|contingencia ambiental|verificacion vehicular|holograma)\b",
     ("trafico", "vehicular", "automoviles", "autos", "transito", "movilidad")),
    (r"\b(?:hospital|clinica|imss|issste)\w*\b",
     ("hospital", "salud", "clinica", "imss", "issste")),
    (r"\b(?:desazolve|drenaje|agua potable)\w*\b",
     ("agua", "desazolve", "drenaje")),
    (r"\b(?:pipas? de gas|gas lp|tanques? de gas|fugas? de gas|explosiones? de gas)\b",
     ("bomberos", "pipas", "gas", "tanques", "camiones cisterna")),
    (r"\b(?:chinampas?|arca tierra|lucio usobiaga)\b",
     ("canales", "xochimilco", "chinampas", "agricultura", "hortalizas")),
    (r"\b(?:dia del soltero|single(?:s)? day)\b",
     ("mercado", "mercados", "compras", "tiendas", "ofertas", "comercio")),
)

def _photo_fold(text):
    text=unicodedata.normalize("NFKD",str(text or "").casefold())
    text="".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+",text))

# Ubicaciones inequívocas dentro de las alcaldías. Si una foto declara otra
# demarcación, no debe ilustrar una noticia localizada en una distinta.
PHOTO_BOROUGH_ALIASES = {
    "la magdalena contreras": ("la magdalena contreras", "magdalena contreras"),
    "alvaro obregon": ("alvaro obregon",),
    "azcapotzalco": ("azcapotzalco",),
    "benito juarez": ("benito juarez",),
    "coyoacan": ("coyoacan",),
    "cuajimalpa de morelos": ("cuajimalpa de morelos", "cuajimalpa"),
    "cuauhtemoc": ("cuauhtemoc", "condesa", "parque espana", "colonia roma", "roma norte", "roma sur"),
    "gustavo a madero": ("gustavo a madero", "gustavo amadero"),
    "iztacalco": ("iztacalco",),
    "iztapalapa": ("iztapalapa",),
    "miguel hidalgo": ("miguel hidalgo", "chapultepec", "bosque de chapultepec"),
    "milpa alta": ("milpa alta",),
    "tlahuac": ("tlahuac",),
    "tlalpan": ("tlalpan", "bosque de tlalpan"),
    "venustiano carranza": ("venustiano carranza",),
    "xochimilco": ("xochimilco", "canales de xochimilco", "chinampas"),
}


def _photo_category(article):
    headline=_photo_fold(article.get("title"))
    # "Poner en marcha" un programa no describe una marcha o protesta vial.
    headline=re.sub(r"\b(?:pone|ponen|puso|poner|puesta|entra|entro|entrara)\s+en\s+marcha\b",
                    "activa", headline)
    # Las recomendaciones de obras teatrales pertenecen a Cultura.
    if re.search(r"\b(?:obras? de teatro|cartelera teatral|funciones? de teatro)\b", headline):
        return "Cultura"
    # Los conciertos y las notas sobre cantantes pertenecen a Cultura.
    if re.search(r"\b(?:cantantes?|cantautores?|gira musical|canciones? ineditas|musica en vivo|teatro metropolitan|garbage|shirley manson)\b", headline):
        return "Cultura"
    if re.search(r"\b(?:pokemon go|k/da|wild rift|league of legends|riot games)\b", headline):
        return "Cultura"
    if re.search(r"\b(?:feria (?:del )?empleo|feria de empleo|vacantes?|reclutamiento|bolsa de trabajo)\b", headline):
        return "Servicios"
    if re.search(r"\b(?:feria de mujeres emprendedoras|mujeres emprendedoras|emprendimiento femenino)\b", headline):
        return "Servicios"
    if (re.search(r"\b(?:aeropuerto|aicm)\b", headline)
            and re.search(r"\b(?:vuelos?|afectaciones?|salidas?|llegadas?)\b", headline)):
        return "Movilidad"
    if (re.search(r"\bmercados?\b", headline)
            and re.search(r"\b(?:recibiran|un millon de pesos|mejorar sus instalaciones|inversion)\b", headline)):
        return "Servicios"
    if (re.search(r"\bc5\b", headline)
            and re.search(r"\b(?:camaras?|vigilar|vigilara|vigilancia)\b", headline)):
        return "Seguridad"
    if (re.search(r"\bmarchas?\b", headline)
            and re.search(r"\b(?:colaps\w*|trafico|puntos de partida|cierres?|bloqueos?)\b", headline)):
        return "Movilidad"
    # Los planes de electrificación del transporte público son materia de Movilidad.
    if (re.search(r"\b(?:transporte(?: publico)?|movilidad)\b", headline)
            and re.search(r"\b(?:electrico|electrica|electrificacion)\b", headline)):
        return "Movilidad"
    # Los informes de vigilancia y alumbrado de una alcaldía corresponden a Seguridad.
    if (re.search(r"\b(?:vigilancia|alumbrado|luminarias?|vigilad[oa]s?)\b", headline)
            and re.search(r"\b(?:tabe|miguel hidalgo)\b", headline)):
        return "Seguridad"
    # Agenda de ballet, circo y ferias gastronómicas: Cultura, aunque el RSS diga Metro o CDMX.
    if re.search(r"\b(?:ballet|danza clasica|cirque du soleil|feria (?:regional )?del pulque|pulque y la barbacoa)\b", headline):
        return "Cultura"
    # Los festivales de cine pertenecen a Cultura.
    if re.search(r"\b(?:cine de barrio|festival(?: de)? cine)\b", headline):
        return "Cultura"
    # Un aviso del Hoy No Circula no es una nota cultural aunque mencione Día de Muertos.
    if re.search(r"\bhoy no circula\b", headline):
        return "Movilidad"
    # Los resultados deportivos del GP no deben heredar fotografías de tráfico.
    if re.search(r"\b(?:formula 1|gp ciudad de mexico|gran premio|nascar)\b", headline):
        if re.search(
            r"\b(?:cierres? viales?|calles? cerradas?|trafico|congestionamiento|"
            r"desvios?|rutas? alternas?|alternativas? viales?|transporte publico|"
            r"estacionamientos?)\b", headline
        ):
            return "Movilidad"
        return "CDMX"
    # Los ataques y homicidios prevalecen sobre menciones a festividades.
    if re.search(r"\b(?:ataques? armados?|balacera|asesina(?:n)?|asesinad\w*|asesinato)\b", headline):
        return "Seguridad"
    # Las víctimas de disparos son un tema de seguridad, aunque el RSS diga CDMX.
    if re.search(r"\b(?:balead\w*|balear\w*|balean|baleo)\b", headline):
        return "Seguridad"
    # Un operativo policial durante una festividad sigue siendo Seguridad.
    if re.search(r"\bpolicias?\b.*\b(?:cuidan|vigilan|operativo|despliegan)\b", headline):
        return "Seguridad"
    # Operativos de seguridad en panteones siguen siendo seguridad,
    # aunque el titular mencione la celebración de Día de Muertos.
    if re.search(r"\boperativos? de seguridad\b", headline):
        return "Seguridad"
    if re.search(r"\b(?:detienen|arrestan|capturan|aprehenden)\s+a\s+(?:\d+|un|una|dos|tres|cuatro|cinco|seis|personas|hombres|mujeres)\b", headline):
        return "Seguridad"
    if re.search(r"\b(?:secuestro|secuestrador(?:es)?|secuestrad[oa]s?|privacion de la libertad)\b", headline):
        return "Seguridad"
    if re.search(r"\bdelitos?\s+(?:contra|a)\s+(?:empresas?|comercios?|negocios?)\b", headline):
        return "Seguridad"
    if (re.search(r"\b(?:muere|murio|fallece|fallecio)\b", headline)
            and re.search(r"\b(?:arrastrad\w*|atropellad\w*|arrollad\w*)\b", headline)
            and re.search(r"\b(?:trailer|tractocamion|camion)\b", headline)):
        return "Movilidad"
    for pattern,category in SUBJECT_RULES:
        if re.search(pattern,headline):
            return category
    return str(article.get("category") or "CDMX")


# Resguardos editoriales: una coincidencia geográfica o de categoría no basta.
# Si la fototeca no tiene contexto del tema, se prefiere publicar sin imagen.
STRICT_PHOTO_TOPICS = (
    # Mantener primero la regla de gas: el titular puede incluir un segundo asunto tras dos puntos.
    (r"\b(?:pipas? de gas|gas lp|explosion(?:es)? de gas|tanques? de gas|fugas? de gas|acumulacion de gas|estalla\s+(?:un\s+)?tanque(?:\s+de\s+gas)?|incendios?)\b",
     r"\b(?:gas|tanques?|cilindros?|fugas?|bomberos|incendios?|extintores?|locales? comerciales?|mercados?|cocinas?|alimentos?)\b"),
    # Ballet y circo requieren una imagen de artes escénicas de ese tipo; un Metro o monumento no basta.
    (r"\b(?:ballet|zapatilla de cristal|danza clasica)\b",
     r"\b(?:ballet|bailarinas?|bailarines?|danza clasica|coreografia de ballet|escenario de ballet)\b"),
    (r"\b(?:cirque du soleil|espectaculo echo)\b",
     r"\b(?:cirque du soleil|circo|acrobatas?|acrobacias?|malabaristas?|espectaculo circense|carpa de circo)\b"),
    # Una feria gastronómica requiere comida o bebida; una danza o fachada de alcaldía no la representa.
    (r"\b(?:feria (?:regional )?del pulque|feria del pulque y la barbacoa|pulque y la barbacoa)\b",
     r"\b(?:pulque|barbacoa|tacos de barbacoa|consome|feria gastronomica|puestos de comida)\b"),
    # Una alerta meteorológica no se ilustra con un sistema de captación de agua de lluvia.
    (r"\b(?:alerta por diluvio|alerta por lluvias?)\b",
     r"\b(?:operativo (?:de )?lluvias?|tormentas?|inundaciones?|calles? anegadas?|lluvia en calles?)\b"),
    # La electrificación del transporte exige una imagen de un sistema o vehículo de transporte.
    (r"\b(?:transporte(?: publico)?|movilidad)\b.*\b(?:electrico|electrica|electrificacion)\b",
     r"\b(?:trolebus|metrobus|autobus(?:es)?|tren ligero|metro|cablebus|electromovilidad|vehiculos? electricos?)\b"),
    # La vigilancia requiere contexto policial; el alumbrado requiere luminarias.
    # Las notas sobre cámaras en mercados requieren una imagen de un mercado, no una patrulla.
    (r"^(?=.*\bmercados?\b)(?=.*\b(?:c5|camaras?|vigilancia|conectad[oa]s?)\b)",
     r"\b(?:mercados?|mercado publico|mercado de abasto|tianguis|puestos)\b"),
    # La vigilancia general requiere contexto policial; los mercados tienen una regla propia.
    (r"^(?!.*\bmercados?\b).*\b(?:vigilancia|vigilad[oa]s?)\b",
     r"\b(?:patrullas?|policias?|camaras? de vigilancia|vigilancia policial|mujeres|apoyos? a mujeres)\b"),
    (r"^(?=.*\b(?:nuevas? luminarias?|80 mil luminarias|luminarias?|alumbrado|iluminacion|iluminadas?)\b)(?!.*\b(?:vigilancia|vigilad[oa]s?|patrullas?|policias?|robo|roban|robaron|cable|cables|sustraccion|asalto|homicidio|asesinad\w*)\b)",
     r"\b(?:alumbrado|luminarias?|iluminacion|faroles?|postes? de luz)\b"),
    # Un festival de cine requiere una imagen cinematográfica, no un museo genérico.
    (r"\b(?:cine de barrio|festival(?: de)? cine)\b",
     r"\b(?:bosquecinema|cine|cinema|cineclub|cineteca|proyecciones?|peliculas?|filmoteca)\b"),
    # El deporte adaptado requiere una imagen de la disciplina, no un monumento genérico.
    (r"\b(?:deporte adaptado|discapacidad motriz|baloncesto en silla de ruedas)\b",
     r"\b(?:deporte adaptado|deportistas?|baloncesto|silla de ruedas|paralimpic\w*|discapacidad motriz|atletas?|gimnasio|cancha|competencia deportiva)\b"),
    # Un riff anunciado por una banda requiere una imagen musical, no un monumento.
    (r"\briff\b",
     r"\b(?:musica|conciertos?|guitarras?|bandas?|escenarios?|rock|cantantes?|festivales?|auditorios?|estadios?)\b"),
    # Un taller de aviación en el AICM no se ilustra con una estación del Metro.
    (r"\b(?:aicm|mexicana de aviacion)\b",
     r"\b(?:aicm|aeropuertos?|aviones?|aeronaves?|aviacion|terminal aeroportuaria|pista de aterrizaje|hangar de mantenimiento|mantenimiento aeronautico)\b"),
    # La apertura de hoteles exige una imagen de hospedaje, no un jardín cercano.
    (r"\bhyatt\b",
     r"\b(?:hotel(?:es)?|hospedaje|alojamiento|resort|habitaciones?|recepcion|lobby)\b"),
    # Las rachas meteorológicas no se ilustran con una plaza sin contexto del clima.
    (r"\brachas?\b",
     r"\b(?:viento|rachas?|meteorologia|clima|nubes?|cielo nublado|tormenta|temperatura|frio)\b"),
    # La cobertura de la Anti-Unión requiere contexto de investigación, no ceremonia policial.
    (r"\banti[ -]?union\b",
     r"\b(?:fiscalia|investigacion penal|detencion|ministerio publico|justicia|operativo policial|patrulla)\b"),
    # Las intervenciones de la FGR en oficinas del INE requieren contexto institucional o de investigación,
    # no fotografías de graduaciones policiales. Una patrulla puede usarse solo como imagen representativa.
    (r"\b(?:fgr|fiscalia general de la republica|instituto nacional electoral|oficinas? de administracion del ine)\b",
     r"\b(?:fgr|fiscalia|ministerio publico|investigacion penal|operativo policial|patrullas?|instituto nacional electoral|oficinas? del ine|edificio del ine)\b"),
    # Una ofrenda monumental no es la cafetería de un museo.
    (r"\bofrenda monumental\b",
     r"\b(?:ofrendas?|altares?|dia de muertos|catrinas?|decoracion funeraria)\b"),
    # Una agenda de eventos de Día de Muertos requiere contexto festivo real.
    (r"\b(?:eventos? gratis|actividades gratis|que hacer)\b.*\bdia de muertos\b",
     r"\b(?:dia de muertos|ofrendas?|altares?|catrinas?|festivales?|eventos?|conciertos?|desfiles?|celebraciones?)\b"),
    # No utilizar graduaciones policiales para remisiones de motocicletas.
    (r"\brodadas? del terror\b",
     r"\b(?:motos?|motocicletas?|motociclistas?|rodadas?|corralones?|deposito vehicular)\b"),
    # El saldo de visitantes durante Día de Muertos no es una entrada de cine histórica.
    (r"\b(?:saldo blanco\b.*\bdia de muertos|dia de muertos\b.*\bsaldo blanco)\b",
     r"\b(?:dia de muertos|panteones?|cementerios?|ofrendas?|catrinas?|celebracion|visitantes?|operativo de seguridad)\b"),
    (r"\bforo urbano mundial\b",
     r"\b(?:foro urbano|urbanismo|onu habitat|conferencias?|planeacion urbana|ciudades|vivienda|arquitectura)\b"),
    (r"\bnascar\b",
     r"\b(?:nascar|automovilismo|autodromo|carreras? de autos?|vehiculos? de carreras?|circuito de carreras?)\b"),
    (r"\bezln\b.*\bbuscador(?:es|a|as)?\b",
     r"\b(?:ezln|zapatistas?|colectivos? de busqueda|madres? buscadoras?|personas desaparecidas|manifestaciones?|protestas?)\b"),
    # El mismo municipio no convierte un jardín o monumento en imagen de búsqueda.
    (r"\b(?:caminata\b.*\b(?:recuperar a su hija|buscando a su hija)|madres? buscadoras?)\b",
     r"\b(?:caminata|colectivos? de busqueda|familias? buscadoras?|madres? buscadoras?|personas desaparecidas|manifestacion|protesta)\b"),
    # Una protesta sindical exige manifestantes, no una calle turística.
    (r"\b(?:protesta sindical|comitiva de trabajadores)\b",
     r"\b(?:protestas?|manifestaciones?|sindical|trabajadores?|plantones?|marchas?)\b"),
    (r"\bmochila de emergencia\b",
     r"\b(?:mochilas?|emergencias?|proteccion civil|suministros?|botiquines?|evacuacion)\b"),
    # Titulares de empleo y becas no se ilustran con monumentos o avenidas.
    (r"\b(?:embajada\b.*\bvacantes?|vacantes?\b.*\bembajada)\b",
     r"\b(?:embajada|vacantes?|empleo|trabajo|oficinas?|alemania)\b"),
    # Una feria del empleo requiere una fotografía de una feria laboral, no una estación del Metro.
    (r"^(?!.*\bembajada\b).*\b(?:feria (?:del )?empleo|feria de empleo|vacantes?|reclutamiento|bolsa de trabajo)\b",
     r"\b(?:feria (?:del )?empleo|empleo|vacantes?|reclutamiento|bolsa de trabajo|job fair)\b"),
    # Una feria de mujeres emprendedoras requiere contexto de emprendimiento o negocios.
    (r"\b(?:feria de mujeres emprendedoras|mujeres emprendedoras|emprendimiento femenino)\b",
     r"\b(?:empresarias?|emprendedoras?|emprendimiento|negocios?|comercio local)\b"),
    (r"\bbeca de transporte\b",
     r"\b(?:becas?|universitarios?|estudiantes?|transporte|metro|autobuses?)\b"),
    # Las notas sobre tuberías y pavimentación requieren contexto de drenaje u obra vial.
    # Una calle genérica o una fotografía de carnavales no es una ilustración pertinente.
    (r"\b(?:tuberias?|pavimentar|pavimentacion|pavimento|asfalto)\b",
     r"\b(?:tuberias?|drenaje|pavimentacion|pavimento|asfalto|alcantarillas?|red hidraulica|infraestructura hidraulica|obra vial|desazolve|supervision de obras)\b"),
    # La rotura de una tubería no se representa con iglesias del mismo barrio.
    (r"\bfuga de agua\b",
     r"\b(?:fuga de agua|tuberias?|reparacion|fontaneria|agua potable|red hidraulica)\b"),
    # "Asesinados" y "asesinadas" no coincidían con el patrón "asesinan".
    (r"\b(?:asesinad\w*|asesina(?:n)?|homicidios?|balacera|ataques? armados?)\b",
     r"\b(?:policias?|patrullas?|fiscalia|investigacion penal|justicia|ministerio publico|peritos?|escena del crimen|operativo policial|repartidores?|conductores? de aplicacion|motociclistas?)\b"),
    # Fotos representativas deben corresponder al asunto, no solo a la ciudad.
    (r"\b(?:panteones?|cementerios?|camposantos?)\b",
     r"\b(?:panteones?|cementerios?|camposantos?|tumbas?|sepulturas?|ofrendas? funerarias?)\b"),
    (r"\b(?:movilizacion(?:es)?|manifestacion(?:es)?|planton(?:es)?|concentracion(?:es)?|protest\w*|marcha(?:s)?|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar))\b",
     r"\b(?:movilizacion(?:es)?|manifestacion(?:es)?|planton(?:es)?|concentracion(?:es)?|protest\w*|manifestantes?|marcha(?:s)?|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|cacerolazo|repartidores?|trabajadores?|motociclistas?|trafico|transito|vehicular|congestion|cierres? viales?|bicicletas?|ciclistas?|rodadas?|ecobici)\b"),
    (r"\b(?:repartidores?|conductores? de aplicacion)\b.*\b(?:toman|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|calles? cerraran)\b",
     r"\b(?:repartidores?|conductores?|manifestantes?|protest\w*|marcha(?:s)?|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|cacerolazo|movilizacion(?:es)?|trabajadores?|motociclistas?)\b"),
    (r"\bdel campo a tu colonia\b",
     r"\b(?:campo|mercados?|agricultura|productores?|verduras?|hortalizas?|cosecha|suelo de conservacion|venta directa|alimentos?)\b"),
    (r"\b(?:artz pedregal|antara)\b",
     r"\b(?:artz|antara|arquitectura|arquitectos?|centros? comerciales?|edificios?|construccion de edificios)\b"),
    # Visitar tumbas requiere contexto funerario, no actos políticos universitarios.
    (r"\b(?:visitan? panteones?|adornar tumbas|familias? visitan? panteones?)\b",
     r"\b(?:panteones?|cementerios?|tumbas?|sepulturas?|ofrendas? funerarias?)\b"),
    # Marchas anunciadas no se ilustran con vehículos de transporte público.
    (r"\bmarchas?\b.*\b(?:hoy|noviembre|bloqueos?|concentraciones?)\b",
     r"\b(?:manifestacion(?:es)?|protestas?|marchas?|bloqueos?|concentraciones?|movilizaciones?)\b"),
    # Una agresión letal no es una celebración ni una imagen genérica de rescate.
    (r"\b(?:ataques? armados?|balacera|asesina(?:n)?|asesinato)\b",
     r"\b(?:policias?|patrullas?|fiscalia|investigacion penal|justicia|ministerio publico|peritos?|escena del crimen|operativo policial|repartidores?|conductores? de aplicacion|motociclistas?)\b"),
    # Un tiroteo no se ilustra con una graduación o ceremonia policial.
    (r"\b(?:balead\w*|balear\w*|balean|baleo)\b",
     r"\b(?:fiscalia|investigacion penal|justicia|ministerio publico|peritos?|escena del crimen|operativo policial)\b"),
    # La captación de agua pluvial requiere sistemas de recolección, no gotas en plantas.
    (r"\b(?:captar agua de lluvia|captacion de agua de lluvia|cosecha de lluvia|recoleccion de agua pluvial)\b",
     r"\b(?:captacion|cosecha de lluvia|recoleccion|sistema pluvial|cisternas?|tinacos?|canaletas?|almacenamiento de agua|depositos? de agua|filtros? de agua)\b"),
    # Una detención en un reclusorio no se ilustra con una estación del Metro.
    (r"\breclusorio\b",
     r"\b(?:reclusorio|centro penitenciario|penitenciaria|prision|fiscalia|detencion|ministerio publico|operativo policial)\b"),
    # La búsqueda de desaparecidos no se ilustra con un monumento sin relación.
    (r"\b(?:busqueda de personas|personas desaparecidas)\b",
     r"\b(?:colectivos? de busqueda|personas desaparecidas|busqueda|fiscalia|familias? buscadoras?|protestas?|manifestaciones?)\b"),
    # Los datos de deuda pública requieren contexto económico o institucional.
    (r"\b(?:deuda de estados|deuda publica|deuda estatal)\b",
     r"\b(?:finanzas?|economia|presupuesto|deuda|bancos?|gobierno|auditoria|congreso)\b"),
    # La agenda de movilizaciones requiere una protesta o rodada, no bomberos.
    (r"\bagenda de (?:movilizaciones|marchas|bloqueos)\b",
     r"\b(?:manifestaciones?|protestas?|marchas?|bloqueos?|rodadas?|motocicletas?|motociclistas?|concentraciones?)\b"),
    # Un resumen de bloqueos y accidentes no se ilustra con edificios vacíos.
    (r"\bbloqueos?\b.*\b(?:accidentes?|manifestaciones?|hoy)\b",
     r"\b(?:bloqueos?|manifestaciones?|protestas?|trafico|transito|vialidad|accidentes?|vehicular)\b"),
    # Una noticia sanitaria sobre carne descompuesta no es turismo de Xochimilco.
    (r"\b(?:carne podrida|frigorifico|toneladas de carne)\b",
     r"\b(?:carne|frigorifico|carnicerias?|alimentos?|inspeccion sanitaria|refrigeracion)\b"),
    # Megarrodada sin el sufijo "del Terror" también exige motos.
    (r"\b(?:mega ?rodada|megarrodada)\b",
     r"\b(?:motos?|motocicletas?|motociclistas?|rodada)\b"),
    # Visitas a cementerios no son desfiles de Catrinas.
    (r"\bvisitas? a (?:cementerios?|panteones?|tumbas?)\b",
     r"\b(?:cementerios?|panteones?|tumbas?|sepulturas?|mausoleos?|ofrendas? funerarias?)\b"),
    # La cartelera de Día de Muertos no es la cafetería de un museo.
    (r"\b(?:actividades|conciertos?|shows?)\b.*\bdia de muertos\b|\bdia de muertos\b.*\b(?:actividades|conciertos?|shows?)\b",
     r"\b(?:conciertos?|musica|escenario|espectaculos?|ofrendas?|altares?|desfile|catrinas?|festival|dia de muertos|celebraciones?)\b"),
    # Un debate de salud y cuidados paliativos no es una calle cualquiera.
    (r"\b(?:derecho a morir|muerte digna)\b",
     r"\b(?:salud|hospital|medicina|cuidados paliativos|derechos|pacientes|bioetica|eutanasia)\b"),
    # Las casetas de acceso y peaje son infraestructura carretera, no estaciones de tren.
    (r"\b(?:casetas? de acceso|casetas? de peaje|trafico en (?:las )?casetas?)\b",
     r"\b(?:casetas?|peaje|autopistas?|carreteras?|plazas? de cobro|cuotas?)\b"),
    # Una nota sobre congestión en ciudades requiere tránsito vial, no trenes.
    (r"\bciudades?\b.*\b(?:mas|mayor) trafico\b",
     r"\b(?:trafico|vehicular|autos?|automoviles?|vehiculos?|congestion|congestionamiento|embotellamiento|transito)\b"),
    # Proyectos de Tren Ligero no se ilustran con vagones de líneas del Metro.
    (r"\btren ligero\b",
     r"\b(?:tren ligero|tranvia|ferrocarril ligero)\b"),
    # Una ampliación de ruta RTP requiere autobuses, no estaciones del Metro.
    (r"\brtp\b",
     r"\b(?:rtp|autobuses?|camiones?|transporte publico|bus)\b"),
    # Para crimen organizado, ni teatro ni graduaciones de policía o patrullas genéricas.
    (r"\b(?:grupos? criminales?|organizaciones? criminales?|crimen organizado)\b",
     r"\b(?:fiscalia|investigacion penal|crimen organizado|operativo policial|central de abasto)\b"),
    # Los precios de gasolina necesitan imagen de combustible o estación de servicio.
    (r"\b(?:precios? de (?:la )?gasolina|gasolineras?|combustibles?)\b",
     r"\b(?:gasolina|gasolineras?|combustibles?|estacion de servicio|surtidor|bomba de gasolina)\b"),
    # Una ley de seguridad vial no se ilustra con el pago de pasaje en Metrobús.
    (r"\b(?:ley de movilidad|tragedias viales)\b",
     r"\b(?:seguridad vial|transito|vialidad|trafico|vehicular|vehiculos?|automoviles?|carreteras?|cruces? peatonales?|peatones?|ciclistas?|siniestros? viales?|accidentes? viales?|senales? de transito)\b"),
    # Un edificio turístico no representa retrasos de vuelos ni operaciones aéreas.
    (r"\b(?:aeropuerto|vuelos? demorados?|vuelos? retrasados?)\b",
     r"\b(?:aeropuerto|aeronautica|aviones?|aeronaves?|vuelos?|terminal aerea|pista de aterrizaje)\b"),
    # Una casa del Centro Histórico no ilustra puentes peatonales ni estafas viales.
    (r"\b(?:puentes? peatonales?|pasarelas? peatonales?)\b",
     r"\b(?:puentes?|pasarelas?|pasos? peatonales?|cruces? elevados?)\b"),
    (r"\bmontachoques\b",
     r"\b(?:choques?|automoviles?|autos?|vehiculos?|trafico|transito|seguridad vial)\b"),
    # La captación de lluvia no es una imagen de pronóstico, frío o viento.
    (r"\b(?:temperaturas?|clima|pronostico|rachas de viento|mananas frias|frente frio)\b",
     r"\b(?:clima|pronostico|meteorologia|temperatura|viento|frio|nubes?|cielo|tormenta|neblina)\b"),
    # Los choques y derrapes de motos, camiones o vehículos requieren contexto
    # de tránsito; compartir alcaldía no vuelve pertinente una iglesia.
    (r"\b(?:accident\w*|choc\w*|choqu\w*|colisi\w*|volcadur\w*|derrap\w*)\b.*\b(?:motociclist\w*|motociclet\w*|moto\w*|camion\w*|vehicul\w*|automovil\w*)\b|"
     r"\b(?:motociclist\w*|motociclet\w*|moto\w*|camion\w*|vehicul\w*|automovil\w*)\b.*\b(?:accident\w*|choc\w*|choqu\w*|colisi\w*|volcadur\w*|derrap\w*)\b",
     r"\b(?:motociclet\w*|motociclist\w*|motos?|camion\w*|vehicul\w*|automovil\w*|vehicular|trafico|transito|vialidad|carretera|avenida|cruce peatonal)\b"),
    # Atropellamientos y muertes viales no se ilustran con iglesias o plazas.
    (r"\b(?:atropell\w*|arroll\w*)\b",
     r"\b(?:microbus|autobus|vehiculos?|vehicular|trafico|transito|vialidad|peatones?|cruce peatonal|automoviles?|autos?|coches?|atropellamientos?)\b"),
    # Los operativos de vigilancia no se ilustran con museos sin relación.
    (r"\bpolicias?\b.*\b(?:cuidan|vigilan|operativo|despliegan)\b",
     r"\b(?:policias?|patrullas?|vigilancia|seguridad|operativo|agentes?)\b"),
    # Para detenciones de personas, una plaza de la misma alcaldía no basta.
    # En un operativo del Gran Premio también es pertinente el autódromo.
    (r"^(?!.*\b(?:gp de mexico|gran premio|formula 1|autodromo)\b).*\b(?:detienen|arrestan|capturan|aprehenden)\s+a\s+(?:\d+|un|una|dos|tres|cuatro|cinco|seis|personas|hombres|mujeres)\b",
     r"\b(?:fiscalia|justicia|tribunal|detencion|investigacion penal|operativo policial|ministerio publico)\b"),
    (r"\bempleo de mujeres\b",
     r"\b(?:empleo|trabajo|mujeres|oficinas?|economia|trabajadoras?)\b"),
    (r"\bmorena\b.*\b(?:militantes|reunio|asamblea)\b",
     r"\b(?:morena|militantes|asamblea|reunion|partido politico|politica)\b"),
    (r"\b(?:asamblea comunitaria|autoridades auxiliares)\b",
     r"\b(?:asamblea|comunitaria|vecinos|cabildo|reunion|autoridades auxiliares)\b"),
    (r"\b(?:juan atkins|pionero del techno)\b",
     r"\b(?:techno|musica|dj|vinilos?|discos?|escenario|concierto|musico|productor musical)\b"),
    # Sloopy y Lobito son los perros del caso de envenenamiento en Xochimilco.
    (r"\b(?:sloopy|lobito)\b",
     r"\b(?:perros?|caninos?|mascotas?|veterinaria)\b"),
    # Envenenamiento de perros exige imagen canina, no fauna genérica.
    (r"\b(?:envenenamientos?\b.*\b(?:perros?|mascotas?)|(?:perritos?|perros?|mascotas?)\s+envenenad[oa]s?)\b",
     r"\b(?:perritos?|perros?|mascotas?|caninos?|veterinaria)\b"),
    (r"\b(?:perritos?|perros?|mascotas?)\b",
     r"\b(?:perritos?|perros?|mascotas?|caninos?|animales?|veterinaria)\b"),
    (r"\b(?:ejecutan|ejecutad\w*|ejecucion|matan|balazos|asesinan|homicidio|condenad[oa]s?|condenan|prision|delitos? contra)\b",
     r"\b(?:fiscalia|justicia|tribunal|juzgado|penitenciario|prision|ministerio publico|investigacion penal|policias?|patrullas?|operativo policial)\b"),
    (r"\b(?:sin agua|falta de agua|suspension de agua|corte de agua)\b",
     r"\b(?:agua|tuberias?|acueducto|pozo|abastecimiento|red hidraulica|cisterna|pipas?|grifos?)\b"),
    (r"\b(?:fallece motociclista|muere motociclista|motociclistas? fallecidos?)\b",
     r"\b(?:motos?|motocicletas?|carretera|vialidad|trafico|transito|vehicular)\b"),
    (r"\b(?:bloquean? avenida|bloqueos? en avenida)\b",
     r"\b(?:manifestacion|protesta|bloqueo|colectivo de busqueda|personas desaparecidas)\b"),
    (r"\b(?:panteon|cementerio|tumba)\b",
     r"\b(?:panteon|cementerio|tumbas?|sepulturas?|mausoleo)\b"),
    (r"\b(?:desfile|catrinas?)\b",
     r"\b(?:desfile|catrinas?|comparsa|procesion|festival|dia de muertos)\b"),
    (r"\b(?:conciertos?|u2|bono)\b",
     r"\b(?:musica|concierto|escenario|bandas?|cantante|u2|guitarra|rock)\b"),
    (r"\blicencia de conducir\b",
     r"\b(?:licencia|conducir|vehiculos?|automoviles?|autos?|transito|tramite)\b"),
    (r"\bcalidad del aire\b",
     r"\b(?:contaminacion|smog|atmosfera|emisiones|contaminantes|calidad del aire|medicion ambiental)\b"),

    # Un ataque de jauría necesita perros visibles; fauna genérica no basta.
    (r"\b(?:jauria|perros? atacan?|ataque de perros?)\b",
     r"\b(?:perros?|caninos?|mascotas?|veterinaria)\b"),
    # Un socavón exige contexto de pavimento o infraestructura dañada, no edificios turísticos.
    (r"\b(?:socavon(?:es)?|hundimiento(?:s)?|bache(?:s)?|colapso de (?:la )?(?:calle|pavimento|asfalto))\b",
     r"\b(?:socavon(?:es)?|hundimiento(?:s)?|bache(?:s)?|pavimento|asfalto|drenaje|alcantarilla|excavacion|obra vial)\b"),
    # Una caseta vandalizada requiere un acceso o puesto de vigilancia.
    (r"\bcaseta(?:s)? de (?:un )?(?:inmueble|vigilancia|acceso)\b",
     r"\b(?:caseta(?:s)?|vigilancia|guardia|control de acceso|porteria|entrada vigilada|seguridad privada)\b"),
    # Las líneas del Cablebús no se ilustran con estaciones de otra línea.
    (r"\b(?:cablebus|teleferico)\b",
     r"\b(?:cablebus|teleferico|cabinas?)\b"),
    # Los anuncios de conciertos, giras o varias fechas necesitan contexto musical,
    # no fotografías de carnavales, monumentos u otros actos culturales.
    (r"\b(?:karol g|tame impala|setlist|conciertos?|regresa a mexico|regresan a mexico|dos noches en cdmx|giras?|tours?|shows?|presentaciones? en cdmx|fechas? en cdmx)\b",
     r"\b(?:karol g|tame impala|setlist|conciertos?|escenario|musica|cantantes?|estadio|auditorio|guitarra|banda|rock|musica en vivo|gira|tour)\b"),
    # Los verificentros requieren contexto de revisión vehicular.
    (r"\b(?:verificentros?|verificacion vehicular)\b",
     r"\b(?:verificentros?|verificacion vehicular|centro de verificacion|emisiones|vehiculos?|autos?|automoviles?)\b"),
    # Un foro metropolitano necesita contexto cívico o de planeación urbana.
    (r"\b(?:foro de pozmvm|pozmvm|foro urbano|cancelan foro)\b",
     r"\b(?:planeacion urbana|urbanismo|pozmvm|politica|partido|congreso|asamblea|foro urbano|foro metropolitano)\b"),
    # Los fraudes por internet requieren contexto digital, no una ceremonia policial.
    (r"\b(?:fraudes? en compras por internet|fraude cibernetico|policia cibernetica)\b",
     r"\b(?:ciberseguridad|internet|computadora|tecnologia|fraude|phishing|seguridad digital|redes|dispositivo)\b"),
    # Las iniciativas de reciclaje y lectura necesitan papel o contexto educativo.
    (r"\b(?:recicla para leer|reciclaje de papel|papel reciclado)\b",
     r"\b(?:papel|reciclaje|recicla|libros|lectura|biblioteca|escuela|educacion)\b"),
    # La detección de fugas de agua requiere infraestructura hidráulica.
    (r"\b(?:fugas? de agua|deteccion de fugas|detectar fugas de agua)\b",
     r"\b(?:agua|fuga|tuberias?|drenaje|sistema hidraulico|acueducto|cisterna|sensor|red hidraulica)\b"),
    # Las notas de sarampión y otras enfermedades requieren contexto sanitario.
    (r"\b(?:sarampion|dengue|influenza|covid|vacunacion|contagios?)\b",
     r"\b(?:sarampion|dengue|influenza|covid|vacunacion|vacunas?|centro de salud|hospital|clinica|medicos?|personal de salud|enfermeria|laboratorio|epidemiologia|virus)\b"),
    # Los ataques a automóviles requieren contexto vial o de vehículos.
    (r"\b(?:lanzan piedras contra autos?|ataques? contra autos?|piedras contra vehiculos?)\b",
     r"\b(?:autos?|vehiculos?|carretera|periferico|trafico|transito|vialidad|cruce)\b"),
    # Las amenazas con arma en inmuebles no se ilustran con bomberos o graduaciones.
    (r"\b(?:amenazas? con arma de fuego|amenaza con arma|irrumpen en unidad habitacional)\b",
     r"\b(?:arma|repartidor|motocicleta|unidad habitacional|caseta|guardia|vigilancia|escena del crimen|investigacion penal|operativo policial)\b"),
    # Los bloqueos anunciados por repartidores requieren protesta, reparto o vialidad.
    (r"\b(?:repartidores? anuncian? bloqueos?|repartidores? bloquean? zona|bloqueos? de repartidores?)\b",
     r"\b(?:bloqueo|protesta|manifestacion|repartidor|motocicleta|trafico|transito|vialidad|calle)\b"),
     # Las instalaciones de toboganes requieren una imagen de juegos o arte interactivo.
    (r"\b(?:toboganes? gigantes|obra de arte interactiva.*toboganes?)\b",
     r"\b(?:toboganes?|resbaladillas?|instalacion interactiva|arte publico interactivo|parque de diversiones|juegos infantiles)\b"),
    # Un torneo de sumo requiere contexto de lucha japonesa, no un monumento de la ciudad.
    (r"\b(?:sumo|torneo de sumo|lucha japonesa|luchadores? de sumo)\b",
     r"\b(?:sumo|lucha japonesa|rikishi|torneo de sumo|luchadores? de sumo)\b"),
    # Consejos sobre cajeros automáticos requieren un cajero, tarjeta o contexto bancario.
    (r"\b(?:cajeros? automaticos?|alteraciones en cajeros?|fraudes? .*cajeros? automaticos?)\b",
     r"\b(?:cajero automatico|atm|terminal bancaria|tarjeta bancaria|retiro de efectivo|lector de tarjeta|dinero en efectivo|banco)\b"),
    # Los trenes interurbanos requieren una fotografía ferroviaria, no un monumento de CDMX.
    (r"\b(?:primer tren|tren de pasajeros|ruta cdmx[- ]pachuca|tren ciudad de mexico[- ]guadalajara|ruta ciudad de mexico[- ]pachuca)\b",
     r"\b(?:tren de pasajeros|ferrocarril|locomotora|vagones?|vias? ferreas|tren interurbano|tren de larga distancia)\b"),
    # Una caravana migrante no se ilustra con deportes u otros asuntos sin relación.
    (r"\b(?:caravana migrante|caravana de migrantes?|migrantes? avanzan)\b",
     r"\b(?:caravana migrante|caravana de migrantes?|migrantes?|personas migrantes|refugiados?|migracion|estacion migratoria|albergue migrante)\b"),
    # La búsqueda metropolitana requiere contexto de búsqueda de personas, no una graduación policial.
    (r"\b(?:busqueda metropolitana|busqueda metropolitana triple frontera|fiscalias? de morelos.*cdmx.*edomex)\b",
     r"\b(?:busqueda de personas|personas desaparecidas|colectivos? de busqueda|familias? buscadoras?|rastreo|busqueda de campo)\b"),
    # NFL y fútbol americano requieren contexto deportivo, no Metro ni un monumento.
     (r"\b(?:nfl|futbol americano|san francisco 49ers|minnesota vikings)\b",
      r"\b(?:american football|futbol americano|field goal|emparrillado|balon de futbol americano|partido de futbol americano)\b"),
    # Una pipa de gas volcada requiere contexto de combustible o respuesta de bomberos.
    (r"\b(?:pipas? de gas|gas lp|tanques? de gas|fugas? de gas|explosiones? de gas)\b",
     r"\b(?:pipas?|gas|bomberos|incendios?|tanques?|cilindros?|fugas?|explosiones?|camiones? cisterna|camiones? tanque)\b"),
    # Las chinampas requieren canales de Xochimilco o agricultura chinampera, no una plaza.
    (r"\b(?:chinampas?|arca tierra|lucio usobiaga)\b",
     r"\b(?:chinampas?|canales? de xochimilco|agricultura chinampera|cultivos? chinamperos?|hortalizas?|productores? de xochimilco|suelo de conservacion)\b"),
    # El Día del Soltero necesita contexto de comercio, compras u ofertas.
    (r"\b(?:dia del soltero|single(?:s)? day)\b",
     r"\b(?:mercados?|compras?|tiendas?|ofertas?|descuentos?|comercio|centros? comerciales?|escaparates?|ventas?)\b"),
    # Los trámites de licencias y control vehicular requieren contexto de SEMOVI o conducción.
    (r"\b(?:licencia permanente|licencia de conducir|modulos? de licencias?|tramites? de licencias?)\b",
     r"\b(?:licencia(?:s)? de conducir|licencia permanente|modulos? de licencias?|tramite vehicular|semovi|control vehicular|examen de manejo|secretaria de movilidad|oficinas? de la secretaria de movilidad)\b"),
    # La publicidad exterior requiere anuncios en fachadas; una oficina de SEMOVI no es contexto.
    (r"\b(?:empresas? de publicidad|publicidad exterior|anuncios? publicitarios?|anuncios? en edificios?|espectaculares?)\b",
     r"\b(?:publicidad exterior|anuncios? publicitarios?|anuncios? en edificios?|publicidad en fachadas|espectaculares?|advertising on the side of buildings)\b"),
    # Un ranking de seguridad de una alcaldía no se ilustra con un teatro o monumento.
    (r"\b(?:alcaldia mas segura|segunda alcaldia mas segura|mas segura de cdmx|ranking de seguridad)\b",
     r"\b(?:patrullas?|policias?|camaras? de vigilancia|vigilancia policial|seguridad ciudadana)\b"),
    # La seguridad estructural requiere edificios, inmuebles o reconstrucción.
    (r"\b(?:seguridad de las construcciones|seguridad estructural|edificios anteriores a 1985|reformas? de construcciones?)\b",
     r"\b(?:edificios?|construcciones?|inmuebles?|estructuras?|reconstruccion|rehabilitacion|inspecciones? estructurales?)\b"),
    # Las noticias sobre cadenas de tiendas requieren contexto de comercio minorista.
    (r"\b(?:tiendas? neto|neto.{0,50}tiendas?|tiendas?.{0,50}neto|cadena de tiendas|sucursales? de neto)\b",
     r"\b(?:tiendas?|abarrotes|supermercados?|comercio minorista|conveniencia|mercados?|establecimientos? mercantiles?)\b"),
    # La arquitectura hostil requiere bancas o jardineras diseñadas para impedir el uso.
    (r"\b(?:arquitectura hostil|bancas? que impiden recostarse|jardineras? con puas)\b",
     r"\b(?:arquitectura hostil|jardineras? hostiles?|jardineras? con puas|bancas? anti.?descanso|comercio ambulante)\b"),
    # Los clubes de pádel requieren una cancha o equipo deportivo, no una iglesia del barrio.
    (r"\b(?:padel|clubes? de padel)\b",
     r"\b(?:padel|raquetas?|canchas? de padel|tenis|clubes? deportivos?)\b"),
    # Un refugio animal requiere contexto de animales, no interiores de oficinas.
    (r"\b(?:refugio franciscano|refugio de animales|albergue de animales)\b",
     r"\b(?:perros?|perritos?|animales?|mascotas?|refugio animal)\b"),
    # Una marcha de motociclistas requiere una motocicleta; una protesta genérica no basta.
    (r"\b(?:mottu|motociclistas?.{0,50}march\w*|marcha de motociclistas?|movilizacion de motociclistas?)\b",
     r"\b(?:motocicletas?|motociclistas?|motos?|motorcycle)\b"),
    # Los decomisos de consolas/videojuegos en Plaza Meave requieren contexto de mercancía, no patrullas.
    (r"(?=.*\bplaza meave\b)(?=.*\b(?:videojuegos?|consolas?|pirateria|mercancia apocrifa|decomis\w*|aseguran|incaut\w*)\b)",
     r"\b(?:videojuegos?|consolas?|mercancia apocrifa|pirateria|decomiso|incautacion|aseguramiento|semar|impi)\b"),
    # Un operativo genérico en Plaza Meave puede usar contexto policial o del sitio.
    (r"^(?!.*\b(?:videojuegos?|consolas?|pirateria|mercancia apocrifa|decomis\w*|aseguran|incaut\w*)\b).*\bplaza meave\b",
     r"\b(?:plaza meave|policias?|patrullas?|operativo|pirateria|mercancia apocrifa|semar)\b"),
    # Una petición de no manifestarse se ilustra con una marcha, no con carnavales.
    (r"\b(?:no manifestarse|manifestarse|marchar a cdmx)\b",
     r"\b(?:marchas?|protestas?|manifestantes?|cacerolazo|planton(?:es)?|bloqueos?|movilizaciones?)\b"),
    # Una jornada de búsqueda requiere colectivos o personas desaparecidas, no jardines genéricos.
    (r"\b(?:colectivos? en jornada de busqueda|jornada de busqueda|colectivos? de busqueda)\b(?!.*\b(?:bloque\w*|protest\w*|manifest\w*|march\w*|planton\w*|movilizacion\w*)\b)",
     r"\b(?:colectivos? de busqueda|personas desaparecidas|madres? buscadoras?|familias? buscadoras?|busqueda de campo|rastreo|fiscalia)\b"),
    # Un informe de gobierno de una alcaldía necesita contexto de esa demarcación.
    (r"\btabe.*\binforme de gobierno\b",
     r"\b(?:miguel hidalgo|chapultepec|bosque de chapultepec|alcaldia miguel hidalgo)\b"),
    # Las notas del Congreso local requieren el recinto legislativo, no una avenida homónima.
    (r"\b(?:congreso capitalino|congreso de la cdmx|congreso de la ciudad de mexico)\b",
     r"\b(?:congreso de la ciudad de mexico|palacio legislativo|donceles|recinto legislativo|sala de sesiones)\b"),
    (r"\bplan general de desarrollo\b",
     r"\b(?:plan general de desarrollo|planeacion urbana|urbanismo|recinto legislativo|congreso de la ciudad de mexico|palacio legislativo|donceles|sala de sesiones|mapa urbano|documento de planeacion)\b"),
    # Las iniciativas de justicia ambiental necesitan paisaje o biodiversidad, no un palacio.
    (r"\b(?:justicia ambiental|proteger la biodiversidad|biodiversidad)\b",
     r"\b(?:parque ecologico|bosque|viveros|jardin escenico|biodiversidad|flora|fauna|areas verdes|ecosistema)\b"),
    # Los programas de casa ecológica requieren una ecotecnia visible o captación de lluvia/solar.
    (r"\b(?:casa ecologica|ecotecnias?|calentadores? solares?|captadores? de agua|sistemas? de captacion)\b",
     r"\b(?:cosecha de lluvia|captacion de agua|calentadores? solares?|paneles? solares?|energia solar|ecotecnias?|casa ecologica|sistemas? de captacion|cisternas?)\b"),
    # Una guía de Pueblos Mágicos no se ilustra con una calle del Centro de CDMX.
    (r"\b(?:pueblos? magicos?|escapada de tres dias|escapadas? a pueblos)\b",
     r"\b(?:pueblos? magicos?|tepotzotlan|tepoztlan|valle de bravo|malinalco|taxco|huasca|real del monte|atlixco|tlayacapan|cholula)\b"),
    # Un fallecimiento dentro del CCH Sur no se ilustra con una banca de Coyoacán.
    (r"\bcch sur\b",
     r"\b(?:cch sur|colegio de ciencias y humanidades sur|cch)\b"),
    # Una nota de límites metropolitanos necesita mapa o contexto territorial.
    (r"\b(?:edomex.*cdmx.*valle de mexico|valle de mexico.*diferencias|territorios comprenden)\b",
     r"\b(?:mapa|cartografia|zona metropolitana|valle de mexico|territorio|edomex|estado de mexico)\b"),
    # La compra o expansión de cadenas farmacéuticas requiere una farmacia, no una foto cultural.
    (r"\b(?:farmacias? del ahorro|benavides|cadena de farmacias?)\b",
     r"\b(?:farmacias?|boticas?|medicamentos?|droguerias?)\b"),
    # Una nota sobre una orquesta necesita contexto musical, incluido un coro representativo.
    (r"\b(?:orquesta|aniversario musical)\b",
     r"\b(?:orquestas?|musica|conciertos?|guitarras?|bandas?|coros?|coral|escenarios?|cantantes?|festivales?|auditorios?|estadios?)\b"),
    # La banda Garbage requiere una foto de concierto o música en vivo.
    (r"\b(?:garbage|shirley manson)\b",
     r"\b(?:conciertos?|musica en vivo|bandas?|escenarios?|rock|cantantes?|festivales?|auditorios?|estadios?)\b"),
    # Pokémon Go es un juego móvil; una consola genérica no basta como contexto.
    (r"\bpokemon go\b",
     r"\b(?:pokemon go|juegos? moviles?|smartphone|realidad aumentada|jugadores? con celular)\b"),
    # Las afectaciones de vuelos requieren aviones o instalaciones aeroportuarias.
    (r"\b(?:aeropuerto|aicm)\b.*\b(?:vuelos?|afectaciones?|salidas?|llegadas?)\b",
     r"\b(?:aeropuertos?|aviones?|aeronaves?|aviacion|terminal aeroportuaria|pista de aterrizaje|aicm|terminal 1|terminal 2)\b"),
    # Un cierre o suspensión del espacio aéreo requiere contexto aeroportuario o de aeronaves.
    (r"\b(?:cierre|suspension|restriccion)\b.{0,40}\b(?:aereo|espacio aereo|vuelos?|pasajeros?)\b",
     r"\b(?:aeropuertos?|aviones?|aeronaves?|aviacion|terminal aeroportuaria|pista de aterrizaje|aicm|terminal 1|terminal 2)\b"),
    # Las obras hidráulicas requieren agua o infraestructura hídrica, no remodelación urbana genérica.
    (r"\b(?:obras? hidraulicas?|infraestructura hidraulica|inversion en obras hidraulicas?)\b",
     r"\b(?:obras? hidraulicas?|infraestructura hidraulica|agua potable|drenaje|alcantarillado|red hidraulica|planta de tratamiento|bombeo|captacion de agua|saneamiento|sistema de agua|pozos?)\b"),
    # Un antro o fiesta en mansión requiere señales de vida nocturna; una fiesta religiosa no basta.
    (r"\b(?:antro|discoteca|club nocturno|fiesta en (?:una )?mansion|mansion de polanco|home alone)\b",
     r"\b(?:antros?|discotecas?|clubes? nocturnos?|bares?|vida nocturna|mansiones?|salones? de fiestas?|pistas? de baile|dj|disc jockey|musica electronica|fiesta nocturna|fiesta privada|club de baile)\b"),
    # Las denuncias por fraude requieren contexto financiero o de investigación, no una graduación policial.
    (r"\b(?:denuncias? por fraude|tasa de denuncias por fraude|fraude|estafas?)\b",
     r"\b(?:fraude|estafas?|fraude cibernetico|delitos? financieros?|delitos? ciberneticos?|ciberseguridad|phishing|compras? por internet|investigacion penal|fiscalia|ministerio publico|tarjetas?|bancos?|finanzas?|denuncias? por fraude|documentos?)\b"),
    # La extorsión atribuida a cárceles requiere contexto penitenciario o de investigación.
    (r"\b(?:extorsiones? en .*carceles?|extorsiones? .*centros? penitenciarios?|carceles? .*extorsiones?)\b",
     r"\b(?:extorsion|carceles?|reclusorios?|centros? penitenciarios?|penitenciarias?|prisiones?|cobro de piso|investigacion penal|fiscalia|ministerio publico)\b"),
    # Un aseguramiento de autopartes exige piezas o instalaciones de autopartes; una entrega de patrullas no basta.
    (r"\b(?:autopartes?|refacciones?|deshuesaderos?)\b",
     r"\b(?:autopartes?|refacciones?|deshuesaderos?|piezas? de (?:autos?|vehiculos?)|almacen de autopartes|decomiso de autopartes|cateo de autopartes|vehiculos? asegurados|bodega de autopartes|taller de autopartes|desmantelamiento de vehiculos|piezas? de motor|patrullas?)\b"),
    # Una vinculación a proceso requiere contexto judicial o de investigación, no transporte ni compra de patrullas.
    (r"\b(?:vinculan a proceso|vinculado a proceso|vinculacion a proceso|procesan|proceso penal|audiencia inicial|prision preventiva)\b",
     r"\b(?:juzgad[oa]s?|tribunales?|fiscalia|ministerio publico|audiencias?|reclusorios?|centros? penitenciarios?|prisiones?|carceles?|investigacion penal|carpeta de investigacion|peritos?|escena del crimen|sala de juicio|jueces?|imputacion|procesos? judiciales?)\b"),
    # Una guía de comida exige platillos o establecimientos gastronómicos, no panorámicas urbanas.
    (r"\b(?:donde comer|que comer|chicharrones? preparados?|quesadillas?|sesos|antojitos|restaurantes?|gastronomia|comida)\b",
     r"\b(?:comida|alimentos?|chicharron(?:es)?|quesadillas?|sesos|antojitos|restaurantes?|gastronomia|platillos?|cocina|puestos? de comida|fonda|taqueria|mercado gastronomico|cocineras?|comercios? de alimentos?)\b"),

)

def _photo_score(article, photo):
    """Puntúa relación real con el título; nunca declara un hecho verificado."""
    raw_headline=str(article.get("title") or "")
    headline=_photo_fold(raw_headline)
    headline_for_photos=re.sub(
        r"\b(?:pone|ponen|puso|poner|puesta|entra|entro|entrara)\s+en\s+marcha\b",
        "activa", headline,
    )
    topic=_photo_fold(photo.get("topic"))
    # Las advertencias negativas no describen el tema de la imagen:
    # "no del bloqueo actual" no convierte una foto de reparto en foto de protesta.
    topic=re.sub(r"\bno\b[^;.)]*", "", topic)
    keywords=_photo_fold(" ".join(str(x) for x in photo.get("keywords",[])))
    context=topic+" "+keywords
    theater_story = bool(re.search(
        r"\b(?:obras? de teatro|cartelera teatral|funciones? de teatro)\b", headline
    ))
    theater_photo = bool(re.search(
        r"\b(?:teatros?|obras? teatrales?|cartelera teatral|escenario teatral|actores?|actrices?|dramaturgia)\b",
        context,
    ))
    # Una cartelera teatral no se ilustra con una maceta o un monumento cultural genérico.
    if theater_story and not theater_photo:
        return -10000
    # Una nota sobre el modelo de seguridad de Saltillo no debe ilustrarse
    # con patrullas de otra alcaldía de CDMX. Sin foto contextual de Saltillo,
    # es preferible no mostrar imagen antes que sugerir un operativo distinto.
    saltillo_model_story = bool(
        re.search(r"\bmodelo de seguridad\b", headline)
        and re.search(r"\bsaltillo\b", headline)
    )
    saltillo_security_photo = bool(
        re.search(r"\b(?:saltillo|coahuila)\b", context)
        and re.search(r"\b(?:seguridad|policias?|patrullas?|operativos?)\b", context)
    )
    if saltillo_model_story and not saltillo_security_photo:
        return -10000
    # El artículo describe ataques a automovilistas en Periférico: una vista del Zócalo
    # no aporta contexto vial. La foto se rotula como representativa, no del ataque.
    if is_jose_cardenas_rocazos(article):
        return 5000 if photo.get("id") == "contexto_periferico_sur_2015" else -10000
    # Una noticia sobre repartidores exige una imagen de repartidores o mensajeros;
    # una protesta distinta no es contexto suficiente.
    delivery_story = bool(re.search(
        r"\b(?:repartidor(?:es|a|as)?|conductores? de aplicacion|mensajeros?|carteros?|servicio postal mexicano|reparto de paqueteria|delivery riders?)\b",
        headline,
    ))
    delivery_photo = bool(re.search(
        r"\b(?:repartidor(?:es|a|as)?|conductores? de aplicacion|mensajeros?|carteros?|servicio postal mexicano|reparto de paqueteria|delivery riders?)\b",
        context,
    ))
    motorcycle_story = bool(re.search(
        r"\b(?:motocicletas?|motociclistas?|motos?)\b", headline
    ))
    vehicle_crash_story = bool(
        re.search(
            r"\b(?:vuelca|volcadura|derrap\w*|choque|colision|accidente vial|"
            r"accidente de transito|siniestro vial|atropellamiento)\b",
            headline,
        )
        and re.search(
            r"\b(?:automovil|auto|vehiculo|camioneta|motocicleta|motociclistas?|moto)\b",
            headline,
        )
    )
    vehicle_road_photo = bool(re.search(
        r"\b(?:trafico vehicular|transito vehicular|vialidad|carretera|autopista|"
        r"avenida|calzada|carriles?|accidente vial|choque|volcadura|derrape|"
        r"automovilistas)\b",
        context,
    ))
    if vehicle_crash_story and not vehicle_road_photo:
        return -10000
    if (photo.get("id") == "contexto_repartidores_motocicleta_cdmx"
            and not delivery_story):
        return -10000
    if (photo.get("id") == "contexto_motocicleta_zocalo_brigada_2017"
            and not motorcycle_story):
        return -10000
    delivery_security_story = bool(re.search(
        r"\b(?:ataques? armados?|arma|armado|amenaz\w*|vandaliz\w*|robo|asalto|agresion|homicidio|balacera)\b",
        headline,
    ))
    delivery_security_photo = bool(re.search(
        r"\b(?:policias?|patrullas?|seguridad|fiscalia|investigacion penal|operativo policial)\b",
        context,
    ))
    # En ataques o amenazas a repartidores puede usarse contexto policial;
    # en bloqueos o protestas se exige una imagen de repartidores.
    if delivery_story and not delivery_photo and not (
        delivery_security_story and delivery_security_photo
    ):
        return -10000
    # Una marcha por derechos animales no debe ilustrarse con una protesta de otra causa.
    animal_rights_march_story = bool(
        re.search(r"\b(?:marcha|manifestacion|protesta)\b", headline)
        and re.search(r"\b(?:derechos de los animales|bienestar animal|proteccion animal)\b", headline)
    )
    animal_rights_march_photo = bool(
        re.search(r"\b(?:marcha|manifestacion|protesta)\b", context)
        and re.search(r"\b(?:derechos de los animales|bienestar animal|proteccion animal|animales?)\b", context)
    )
    if animal_rights_march_story and not animal_rights_march_photo:
        return -10000

    # Una nota sobre cámaras de seguridad en mercados exige contexto de videovigilancia;
    # una foto de higiene por COVID no representa la instalación de cámaras del C5.
    market_surveillance_story = bool(
        re.search(r"\b(?:c5|camaras?|videovigilancia|circuito cerrado|monitoreo)\b", headline)
        and re.search(r"\bmercados?\b", headline)
    )
    market_surveillance_photo = bool(re.search(
        r"\b(?:camaras? de (?:seguridad|vigilancia|videovigilancia)|videovigilancia|"
        r"circuito cerrado|centro de monitoreo|c5|vigilancia (?:en|de) mercados?|"
        r"camaras? (?:de seguridad )?en mercados?)\b",
        context,
    ))
    if market_surveillance_story and not market_surveillance_photo:
        return -10000

    # Los tianguis no se ilustran con monumentos ni con mercados públicos distintos.
    tianguis_story = bool(re.search(r"\btianguis\b", headline))
    tianguis_photo = bool(re.search(
        r"\b(?:tianguis|mercados? sobre ruedas|comercio ambulante|puestos callejeros|vendedores ambulantes)\b",
        context,
    ))
    if tianguis_story and not tianguis_photo:
        return -10000
    # Un presupuesto del sistema de cuidados requiere contexto de servicios de cuidado.
    care_budget_story = bool(re.search(
        r"\b(?:presupuesto de cuidados|sistema (?:nacional|publico) de cuidados|servicios de cuidado|personas cuidadoras|cuidado infantil)\b",
        headline,
    ))
    care_photo = bool(re.search(
        r"\b(?:cuidados?|personas cuidadoras|guarderias?|estancias infantiles|centros de cuidado|cuidado infantil|servicios de cuidado|atencion a personas mayores)\b",
        context,
    ))
    if care_budget_story and not care_photo:
        return -10000
    # Las noticias sobre Profeco y atención al consumidor requieren una imagen
    # del mismo servicio; una protesta ajena no es contexto editorial suficiente.
    profeco_story = bool(re.search(
        r"\b(?:profeco|proteccion al consumidor|modulos? de atencion|modulos? de quejas)\b",
        headline,
    ))
    profeco_photo = bool(re.search(
        r"\b(?:profeco|proteccion al consumidor|atencion al consumidor|"
        r"modulos? de (?:atencion|quejas)|quejas? de consumo|consumidores?)\b",
        context,
    ))
    if profeco_story and not profeco_photo:
        return -10000
    # No cruzar fotografías de una línea del Cablebús con otra.
    cablebus_story_line = (
        re.search(r"\blinea\s+([123])\b", headline)
        if re.search(r"\bcablebus\b", headline) else None
    )
    if cablebus_story_line and re.search(r"\bcablebus\b", context):
        photo_line = re.search(r"\blinea\s+([123])\b", context)
        if photo_line and photo_line.group(1) != cablebus_story_line.group(1):
            return -10000
        cablebus_station_lines = {
            "1": ("indios verdes", "ticoman", "la pastora", "campos revolucion", "tlalpexco", "cuautepec"),
            "2": ("constitucion de 1917", "quetzalcoatl", "las torres buenavista", "xalpa",
                  "lomas de la estancia", "san miguel teotongo", "santa marta"),
            "3": ("los pinos", "panteon dolores", "parcur", "colegio de arquitectos",
                  "cineteca nacional bodega de arte", "vasco de quiroga"),
        }
        for line, stations in cablebus_station_lines.items():
            if line != cablebus_story_line.group(1) and any(
                re.search(r"\b" + re.escape(station) + r"\b", context)
                for station in stations
            ):
                return -10000
    if photo.get("id") == "contexto_carretera_guerrero" and not (
        re.search(r"\bcarretera\b", headline)
        and re.search(r"\bguerrero\b", headline)
    ):
        return -10000
    article_borough=_photo_fold(article.get("borough"))
    article_borough_key = next(
        (borough for borough, aliases in PHOTO_BOROUGH_ALIASES.items()
         if article_borough == borough or article_borough in aliases),
        "",
    )
    if article_borough_key:
        photo_boroughs = set()
        for borough, aliases in PHOTO_BOROUGH_ALIASES.items():
            # "Avenida Álvaro Obregón" está en Roma Norte (Cuauhtémoc);
            # el nombre de la avenida no demuestra que la foto sea de la alcaldía.
            if borough == "alvaro obregon" and re.search(r"\bavenida alvaro obregon\b", context):
                actual_area = re.search(
                    r"\b(?:alcaldia|delegacion) alvaro obregon\b|"
                    r"\b(?:san angel|las aguilas|lomas de santa fe|contadero|"
                    r"olivar del conde|jalalpa|axotla|tizapan|santa fe)\b",
                    context,
                )
                if not actual_area:
                    continue
            if any(re.search(r"\b"+re.escape(alias)+r"\b",context) for alias in aliases):
                photo_boroughs.add(borough)
        food_event_story = bool(re.search(
            r"\b(?:feria (?:regional )?del pulque|feria del pulque y la barbacoa|pulque y la barbacoa)\b",
            headline,
        ))
        food_photo = bool(re.search(
            r"\b(?:barbacoa|tacos de barbacoa|pulque|consome)\b", context
        ))
        if (photo_boroughs and article_borough_key not in photo_boroughs
                and not (food_event_story and food_photo)):
            return -10000
    # Los boletos y documentos históricos solo ilustran noticias sobre esos objetos.
    ticket_photo = bool(re.search(
        r"\b(?:boletos?|tickets?|entradas?|recibos?|credenciales?|pasaportes?)\b", context
    ))
    ticket_story = bool(re.search(
        r"\b(?:boletos?|tickets?|entradas?|recibos?|credenciales?|pasaportes?|cine|peliculas?|taquilla|pases? de acceso)\b",
        headline,
    ))
    if ticket_photo and not ticket_story:
        return -10000
    lgbt_story = bool(re.search(r"\b(?:lgbtttiq|lgbtq?|diversidad sexual)\b", headline))
    lgbt_photo = bool(re.search(r"\b(?:lgbtttiq|lgbtq?|diversidad sexual|marcha del orgullo|orgullo lgbt)\b", context))
    # Las notas de renta, compra o acceso a vivienda requieren contexto residencial.
    housing_story = bool(re.search(
        r"\b(?:rentas?|rentar|rentan|alquiler|mercado inmobiliario|inmobiliari[oa]s?|precios? de vivienda|compra de vivienda|comprar vivienda|venta de vivienda|crisis habitacional|vivienda social|vivienda asequible)\b",
        headline,
    ))
    housing_photo = bool(re.search(
        r"\b(?:unidades habitacionales|viviendas?|departamentos?|edificios residenciales|conjuntos habitacionales|condominios?|casa centro historico|casa en la avenida|casa gonzalez de cosio)\b",
        context,
    ))
    housing_units_photo = bool(re.search(r"\bunidades habitacionales\b", context))
    # Una foto de marcha del orgullo solo se admite para una nota del mismo tema;
    # las demás imágenes sensibles siguen bloqueadas como contexto genérico.
    if not topic:
        return -10000
    if (SENSITIVE_CONTEXT.search(topic)
            and not (lgbt_story and lgbt_photo)
            and not (housing_story and housing_units_photo)):
        return -10000
    # El catálogo local no debe ilustrar noticias situadas fuera de la capital.
    # No presentar un templo o calle de CDMX como una finca de Veracruz.
    if "(fuera de CDMX)" in str(article.get("location") or ""):
        return -10000
    category=_photo_category(article)
    photo_category=str(photo.get("category") or "CDMX")
    # Un festival de fotografía no se ilustra con obras de remodelación urbana.
    photography_event_story = bool(re.search(r"\bfotogenia\b", headline))
    construction_photo = bool(re.search(
        r"\b(?:remodelacion|construccion|demolicion|obra publica|obras publicas|maquinaria pesada|bacheo|pavimentacion)\b",
        context,
    ))
    if photography_event_story and construction_photo:
        return -10000
    # Una foto de bomberos o rescate solo corresponde a una emergencia mencionada en el titular.
    emergency_photo = bool(re.search(
        r"\b(?:bomberos?|incendios?|explosion(?:es)?|pipas? de gas|gas lp|tanques? de gas|proteccion civil|rescate)\b",
        context,
    ))
    emergency_story = bool(re.search(
        r"\b(?:bomberos?|incendios?|explosion(?:es)?|pipas? de gas|gas lp|tanques? de gas|proteccion civil|rescate|emergencias?|siniestros?)\b",
        headline,
    ))
    # «Rescate de unidades habitacionales» describe rehabilitación de vivienda,
    # no una escena de emergencia; admitirlo solo para notas del mercado inmobiliario.
    if (emergency_photo and not emergency_story
            and not (housing_story and housing_units_photo)):
        return -10000
    source=_photo_fold(article.get("source"))
    police_operation_story = bool(
        re.search(r"\b(?:ssc|secretaria de seguridad ciudadana)\b", headline + " " + source)
        and re.search(r"\b(?:operativo|vigilancia|despliegue|policias?)\b", headline)
    )
    police_context = bool(re.search(
        r"\b(?:policias?|patrullas?|vigilancia policial|policia de transito)\b", context
    ))
    # Para una intervención de la FGR en oficinas del INE, una foto de entrega
    # de patrullas de otra alcaldía no aporta contexto suficiente.
    fgr_ine_story = bool(re.search(
        r"\b(?:fgr|fiscalia general de la republica|instituto nacional electoral|oficinas? de administracion del ine)\b",
        headline,
    ))
    if fgr_ine_story and re.search(
        r"\b(?:adquisicion|compra|presentacion|entrega|nuevas? patrullas?)\b", topic
    ):
        return -10000
    if police_operation_story and not police_context:
        return -10000
    # En robos, asaltos y extorsiones, la coincidencia de alcaldía no basta:
    # exigir una imagen con contexto de seguridad antes de puntuar el lugar.
    crime_story = bool(re.search(
        r"\b(?:robo|robos|roban|robado|robada|robaron|robar|decomis\w*|incaut\w*|asalt\w*|ataques? armados?|extorsion|extorsionan|ejecutan|ejecutad\w*|ejecucion|asesina(?:n)?|asesinad\w*|asesinato|homicidio|matan|balazos|balacera|secuestro|secuestrador(?:es)?|secuestrad[oa]s?|privacion de la libertad|delitos?\s+(?:contra|a)\s+(?:empresas?|comercios?|negocios?))\b",
        headline,
    ))
    # "Asegura que" es una declaración, no un aseguramiento policial.
    # Solo tratar "asegurar" como incautación cuando el titular identifica bienes u objetos.
    seizure_story = bool(re.search(
        r"\b(?:aseguran|aseguraron|aseguramiento|asegurad[oa]s?)\s+(?:\d+\s+)?"
        r"(?:armas?|drogas?|estupefacientes|mercancia|vehiculos?|objetos?|bienes?|sustancias?|paquetes?)\b",
        headline,
    ))
    crime_story = crime_story or seizure_story
    crime_context = bool(re.search(
        r"\b(?:policias?|patrullas?|repartidores?|conductores? de aplicacion|motociclistas?|fiscalia|detencion|operativo policial|"
        r"ministerio publico|investigacion penal|escena del crimen)\b",
        context,
    ))
    meave_goods_story = bool(
        re.search(r"\bplaza meave\b", headline)
        and re.search(r"\b(?:videojuegos?|consolas?|mercancia apocrifa|pirateria|decomis\w*|aseguran|incaut\w*)\b", headline)
    )
    meave_goods_photo = bool(re.search(
        r"\b(?:videojuegos?|consolas?|mercancia apocrifa|pirateria)\b", context
    ))
    if (crime_story and not crime_context
            and not (meave_goods_story and meave_goods_photo)):
        return -10000
    # Una graduación policial no representa un robo ni un operativo de vigilancia.
    if (crime_story or police_operation_story) and re.search(r"\bgraduacion\b", topic):
        return -10000
    # La policía de tránsito y sus automovilistas no ilustran un robo a comercio.
    if crime_story and re.search(
        r"\b(?:policia de transito|policia de trafico|transito|automovilistas?|semaforo|controlando el semaforo|policia controlando el semaforo)\b",
        context,
    ):
        return -10000
    # Los delitos cibernéticos requieren contexto de seguridad informática,
    # no una fotografía genérica de Protección Civil o de una patrulla.
    digital_story = bool(re.search(
        r"\b(?:delitos? ciberneticos|ciberdelitos|fraudes? ciberneticos?|fraudes? digitales?|delitos? digitales?|ciberataques?|phishing|policia cibernetica)\b",
        headline,
    ))
    cybersecurity_photo = bool(re.search(
        r"\b(?:ciberseguridad|seguridad digital|seguridad informatica|phishing)\b",
        context,
    ))
    if cybersecurity_photo and not digital_story:
        return -10000
    digital_context = bool(re.search(
        r"\b(?:ciberseguridad|seguridad digital|seguridad informatica|internet|computadoras?|laptops?|ordenadores?|tecnologia|phishing|fraudes?|redes|dispositivos?)\b",
        context,
    ))
    if digital_story and not digital_context:
        return -10000
    # No presentar patrullas o acciones policiales en noticias ajenas a Seguridad.
    if category!="Seguridad" and (
        photo_category=="Seguridad" or
        re.search(r"\b(?:patrullas?|policias?|fiscalia|detenciones?|armamento)\b", context)
    ):
        return -10000
    # Admitir categorías temáticas solo cuando el descriptor coincide con la noticia.
    music_story = bool(re.search(
        r"\b(?:riff|musica|orquestas?|coros?|coral|conciertos?|bandas?|cantantes?|canta|cantar|aniversario musical|"
        r"canciones? ineditas|teatro metropolitan|maria leon|era de villana|"
        r"tame impala|karol g|regresa a mexico|regresan a mexico|dos noches en cdmx|"
        r"giras?|tours?|shows?|presentaciones? en cdmx|fechas? en cdmx|garbage|shirley manson)\b",
        headline,
    ))
    music_photo = bool(re.search(
        r"\b(?:musica|orquestas?|conciertos?|guitarras?|bandas?|coros?|coral|rock|cantantes?|"
        r"escenario|festival|teatro metropolitan|auditorio nacional|palacio de los deportes)\b",
        context,
    ))
    game_story = bool(re.search(
        r"\b(?:pokemon go|videojuegos?|juegos? moviles?|realidad aumentada|k/da|wild rift|riot games|league of legends)\b",
        headline,
    ))
    game_photo = bool(re.search(
        r"\b(?:pokemon|videojuegos?|consolas?|juegos? moviles?|realidad aumentada|jugadores? con celular|smartphones?|juego en (?:un )?smartphone|gaming)\b",
        context,
    ))
    if game_story and not game_photo:
        return -10000
    market_funding_story = bool(
        re.search(r"\bmercados? de cdmx recibiran un millon de pesos\b", headline)
        or (
            re.search(r"\bmercado bramadero\b", headline)
            and re.search(r"\b(?:recursos|inversion|presupuesto|mejoras?)\b", headline)
        )
    )
    market_funding_photo = bool(
        re.search(r"\b(?:mercados?|mercado publico|mercado de abasto)\b", context)
        and not re.search(r"\b(?:covid|sanidad|epidemia)\b", context)
    )
    market_c5_story = bool(
        re.search(r"\bmercados?\b", headline)
        and re.search(r"\b(?:c5|camaras?|vigilancia|conectad[oa]s?)\b", headline)
    )
    market_c5_photo = bool(re.search(
        r"\b(?:mercados?|mercado publico|mercado de abasto|tianguis|puestos)\b",
        context,
    ))
    if market_funding_story and not market_funding_photo:
        return -10000
    if market_c5_story and not market_c5_photo:
        return -10000
    if music_story and not music_photo:
        return -10000
    # La nota de María León requiere contexto de concierto, no solo música o un coro.
    concert_photo = bool(re.search(r"\b(?:conciertos?|musica en vivo|bandas?|cantantes?|guitarras?|palacio de los deportes|auditorio nacional|teatro metropolitan|escenario|festival)\b", context))
    if is_infobae_maria_leon_concert(article) and not concert_photo:
        return -10000
    # Un coro o una fotografía musical no representa asuntos ajenos a la música.
    if music_photo and not music_story:
        return -10000
    if music_story and not music_photo:
        return -10000
    # No confundir captación/cosecha de lluvia con una alerta meteorológica.
    water_harvesting_story = bool(re.search(
        r"\b(?:captacion de agua(?: de lluvia)?|cosecha de lluvia|captar agua de lluvia|sistemas? de captacion(?: pluvial| de agua)?|sistemas? para captar agua)\b",
        headline,
    ))
    # Cuando el titular trata de una suspensión de transporte por lluvia,
    # una foto de la línea afectada es más pertinente que una foto meteorológica.
    transit_service_weather_story = bool(
        re.search(r"\b(?:metro|metrobus|cablebus|trolebus)\b", headline)
        and re.search(r"\b(?:suspende|suspendio|sin servicio|interrump\w*|reanuda|servicio)\b", headline)
    )
    weather_story = bool(re.search(
        r"\b(?:prevision(?:es)?|pronosticos?|meteorolog\w*|estado del tiempo|clima|"
        r"rachas?|lluvias?|llover|precipitacion|viento|tormenta|temperatura|frio|calor)\b",
        headline,
    )) and not water_harvesting_story and not transit_service_weather_story
    weather_photo = bool(re.search(
        r"\b(?:viento|rachas?|meteorologia|clima|nubes?|cielo nublado|tormenta|temperatura|frio|operativo.{0,40}lluvias?|lluvias?.{0,40}operativo)\b",
        context,
    ))
    if weather_story and not weather_photo:
        return -10000
    animal_story = bool(re.search(
        r"\b(?:jauria|sloopy|lobito|perros?|perritos?|mascotas?|refugio franciscano|refugio de animales|albergue de animales|cacomixtles?)\b",
        headline,
    ))
    animal_photo = bool(re.search(
        r"\b(?:perros?|caninos?|mascotas?|animales?|cacomixtles?|bassariscus|fauna urbana)\b",
        context,
    ))
    # Una noticia de fauna no debe ilustrarse con drenaje, pavimento u otra infraestructura.
    if animal_story and not animal_photo:
        return -10000

    road_incident_story = bool(re.search(
        r"\b(?:accident\w*|choqu\w*|colision\w*|volcadur\w*|siniestro vial|atropell\w*|derrap\w*)\b",
        headline,
    ))
    motorsport_photo = bool(re.search(
        r"\b(?:autodromo|formula 1|f1|gran premio|automovilismo|pista de carreras)\b",
        context,
    ))
    road_traffic_photo = bool(re.search(
        r"\b(?:trafico(?: vehicular)?|transito vehicular|vialidad|congestion vehicular|circulacion vehicular|camion(?:es)?|camionetas?|microbus(?:es)?|autobus(?:es)?|vehiculos? de carga)\b",
        context,
    ))
    trailer_story = bool(re.search(r"\b(?:trailers?|tractocamiones?)\b", headline))
    waste_truck_photo = bool(re.search(
        r"\b(?:camiones? de limpia|recoleccion de basura|servicio de limpia)\b",
        context,
    ))
    if trailer_story and waste_truck_photo:
        return -10000
    motorcycle_photo = bool(re.search(r"\b(?:motocicletas?|motociclistas?|motos?)\b", context))
    # Los accidentes de automovilismo no deben pasar por el filtro de tránsito urbano.
    motorsport_story = bool(re.search(
        r"\b(?:formula 1|f1|gran premio|gp de mexico|autodromo|automovilismo|bottas|verstappen|hamilton|antonelli|checo|alonso|nascar)\b",
        headline,
    ))
    if road_incident_story and not motorsport_story and not (road_traffic_photo or motorcycle_photo):
        return -10000
    # Un autódromo no es contexto para un choque de tránsito en una avenida.
    if road_incident_story and motorsport_photo and not motorsport_story:
        return -10000
    if lgbt_story and not lgbt_photo:
        return -10000
    protest_story = bool(
        re.search(
            r"\b(?:movilizacion(?:es)?|manifestacion(?:es)?|manifestar\w*|planton(?:es)?|concentracion(?:es)?|protest\w*|marcha(?:s)?|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar))\b",
            headline_for_photos,
        )
        or re.search(
            r"\b(?:repartidores?|conductores? de aplicacion)\b.*\b(?:toman|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|calles? cerraran)\b",
            headline_for_photos,
        )
    )
    protest_photo = bool(re.search(
        r"\b(?:movilizacion(?:es)?|manifestacion(?:es)?|planton(?:es)?|concentracion(?:es)?|protest\w*|manifestantes?|marcha(?:s)?|bloque(?:o|os|a|an|aron|ando|ado|ada|ados|adas|ar)|cacerolazo|repartidores?|trabajadores?|motociclistas?)\b",
        context,
    ))
    infrastructure_story = bool(re.search(
        r"\b(?:tuberias?|pavimentar|pavimentacion|pavimento|asfalto)\b",
        headline,
    ))
    infrastructure_photo = bool(re.search(
        r"\b(?:tuberias?|drenaje|pavimentacion|pavimento|asfalto|alcantarillas?|red hidraulica|infraestructura hidraulica|obra vial|desazolve|supervision de obras)\b",
        context,
    ))
    # Las noticias de educación necesitan una escuela o espacio de aprendizaje,
    # no un monumento o una vista genérica de la ciudad.
    education_story = bool(re.search(
        r"\b(?:educacion|educativo|educativa|escuelas?|primarias?|secundarias?|preparatorias?|"
        r"planteles?|colegios?|infraestructura escolar|infraestructura en primarias?|"
        r"madres de familia|domos? escolares?|preescolar|guarderias?)\b",
        headline,
    ))
    education_photo = bool(re.search(
        r"\b(?:escuelas?|primarias?|secundarias?|preparatorias?|planteles?|"
        r"infraestructura escolar|preescolar|kinder|guarderias?|jardin de ninos|"
        r"aulas?|alumn[oa]s?|estudiantes?)\b",
        context,
    ))
    if education_story and not education_photo:
        return -10000
    environmental_story = bool(re.search(
        r"\b(?:justicia ambiental|proteger la biodiversidad|biodiversidad)\b",
        headline,
    ))
    environmental_photo = bool(re.search(
        r"\b(?:parque ecologico|bosque|viveros|jardin escenico|biodiversidad|flora|fauna|areas verdes|ecosistema)\b",
        context,
    ))
    eco_story = bool(re.search(
        r"\b(?:casa ecologica|ecotecnias?|calentadores? solares?|captadores? de agua|captar agua de lluvia|sistemas? para captar agua|sistemas? de captacion)\b",
        headline,
    ))
    eco_photo = bool(re.search(
        r"\b(?:cosecha de lluvia|captacion de agua|calentadores? solares?|paneles? solares?|energia solar|ecotecnias?|casa ecologica|sistemas? de captacion|cisternas?)\b",
        context,
    ))
    if education_story and not education_photo:
        return -10000
    # Las notas de renta y mercado inmobiliario no se ilustran con monumentos.
    if housing_story and not housing_photo:
        return -10000
    # La recaudación y el predial requieren contexto de tesorería o finanzas públicas;
    # un monumento de la ciudad no ilustra una comparación fiscal.
    tax_story = bool(re.search(
        r"\b(?:predial|recaudacion|impuestos?|ingresos tributarios|finanzas publicas)\b",
        headline,
    ))
    tax_photo = bool(re.search(
        r"\b(?:predial|recaudacion|impuestos?|tesoreria|finanzas publicas|ingresos tributarios)\b",
        context,
    ))
    if tax_story and not tax_photo:
        return -10000
    # Una chelería o bar requiere una imagen de bares, cantinas o cerveza.
    bar_business_story = bool(re.search(
        r"\b(?:chelerias?|cervecerias?|cantinas?|bares?|bar de barrio)\b",
        headline,
    ))
    bar_business_photo = bool(re.search(
        r"\b(?:chelerias?|cervecerias?|cantinas?|bares?|cerveza|restaurantes?)\b",
        context,
    ))
    if bar_business_story and not bar_business_photo:
        return -10000
    # La nota sobre tamaleros o comida callejera no se ilustra con monumentos.
    street_food_story = bool(re.search(
        r"\b(?:tamaler[oa]s?|tamales?|antojitos|comida callejera|puestos? de comida|vendedores? ambulantes)\b",
        headline,
    ))
    street_food_photo = bool(re.search(
        r"\b(?:tamales?|tamaler[oa]s?|antojitos|comida callejera|puestos? de comida|vendedores? ambulantes|mercado de alimentos)\b",
        context,
    ))
    if street_food_story and not street_food_photo:
        return -10000
    # Las notas sobre DiDi/Uber requieren contexto de transporte por aplicación.
    ride_hailing_story = bool(re.search(
        r"\b(?:didi|uber|plataformas? de transporte|conductores? de aplicacion)\b",
        headline,
    ))
    ride_hailing_photo = bool(re.search(
        r"\b(?:didi|uber|taxi|vehiculos? de plataforma|conductores? de aplicacion|autos? de plataforma)\b",
        context,
    ))
    if ride_hailing_story and not ride_hailing_photo:
        return -10000
    # Una iniciativa del Congreso no se ilustra con Palacio Nacional.
    legislative_story = bool(re.search(
        r"\b(?:congreso|asamblea legislativa|legislativ[oa]|camara de diputados|senado)\b",
        headline,
    ))
    # La coincidencia debe identificar un recinto o una sesión legislativa,
    # no una avenida cuyo nombre contiene la palabra «Congreso».
    legislative_photo = bool(re.search(
        r"\b(?:congreso de (?:la ciudad de mexico|la cdmx|cdmx)|congreso cdmx|"
        r"asamblea legislativa|palacio legislativo|camara de diputados|"
        r"recinto legislativo|salon de plenos|sesion del congreso)\b",
        context,
    ))
    if legislative_story and not legislative_photo:
        return -10000
    # El Plan General de Desarrollo exige cartografía o contexto de planeación urbana.
    planning_story = (
        _photo_fold(article.get("category")) != "seguridad"
        and bool(re.search(
            r"\b(?:plan general de desarrollo|pgd|uso de suelo|ordenamiento territorial|expropiacion|desarrollo urbano|planeacion urbana|banco de suelo)\b",
            headline,
        ))
    )
    planning_photo = bool(re.search(
        r"\b(?:plan general de desarrollo|pgd|uso de suelo|ordenamiento territorial|expropiacion|desarrollo urbano|planeacion urbana|mapa urbano|banco de suelo)\b",
        context,
    )) or legislative_photo
    if planning_story and not planning_photo:
        return -10000
    # Las caravanas y noticias de migración requieren personas migrantes o albergues.
    migration_story = bool(re.search(
        r"\b(?:caravana.{0,50}migrantes?|migrantes?|refugiados?)\b",
        headline,
    ))
    migration_photo = bool(re.search(
        r"\b(?:caravana migrante|migrantes?|refugiados?|albergues? migratorios?|estaciones? migratorias?)\b",
        context,
    ))
    if migration_story and not migration_photo:
        return -10000
    # Actores, estrenos y alfombras rojas requieren contexto de cine o espectáculo.
    entertainment_person_story = bool(re.search(
        r"\b(?:alfombra|premiere|estreno|reparto|actores?|actrices?|canta|interpreta)\b",
        headline,
    ))
    entertainment_photo = bool(re.search(
        r"\b(?:alfombra roja|premiere|estreno|reparto|actores?|actrices?|cine|cineteca|conciertos?|musica en vivo|escenario|filmoteca)\b",
        context,
    ))
    if entertainment_person_story and not entertainment_photo:
        return -10000
    themed_category = (
        (photo_category == "Seguridad" and game_story and game_photo)
        or (photo_category == "Servicios" and market_funding_story and market_funding_photo)
        or (photo_category == "Servicios" and market_c5_story and market_c5_photo)
        or (photo_category == "Cultura" and music_story and music_photo)
        or (photo_category == "Medio Ambiente" and (
            (weather_story and weather_photo) or (animal_story and animal_photo)
        ))
        or (protest_story and protest_photo)
        or (lgbt_story and lgbt_photo)
        or (infrastructure_story and infrastructure_photo)
        or (education_story and education_photo)
        or (housing_story and housing_photo)
        or (tax_story and tax_photo)
        or (environmental_story and environmental_photo)
        or (eco_story and eco_photo)
        or (delivery_story and delivery_photo)
        or (bar_business_story and bar_business_photo)
        or (street_food_story and street_food_photo)
        or (ride_hailing_story and ride_hailing_photo)
        or (legislative_story and legislative_photo)
        or (planning_story and planning_photo)
        or (migration_story and migration_photo)
        or (entertainment_person_story and entertainment_photo)
        or (motorcycle_story and motorcycle_photo)
        or (road_incident_story and road_traffic_photo)
    )
    # Una categoría distinta no basta por sí sola para considerar pertinente una foto.
    if photo_category not in (category, "CDMX", "Alcaldías") and not themed_category:
        return -10000
    # Una convocatoria de marcha del IMSS no se ilustra con transporte público.
    if ("imss" in headline
            and re.search(r"\b(?:marchas?|protestas?|plantones?|movilizaciones?)\b", headline)
            and not re.search(r"\b(?:manifestantes?|protestas?|marchas?|plantones?|movilizaciones?|concentraciones?|sindicatos?|trabajadores?)\b", context)):
        return -10000
    # Las multas a bicicletas eléctricas o scooters no se ilustran con el logo EcoBici.
    if (re.search(r"\b(?:scooters?|monopatines?|bicicletas? electricas?)\b", headline)
            and "ecobici" not in headline
            and re.search(r"\becobici\w*\b", context)):
        return -10000
    # Una Catrina monumental no equivale a un desfile de disfraces.
    if (re.search(r"\bcatrina monumental\b", headline)
            and not re.search(r"\b(?:monumental|monumento|escultura|instalacion)\b", context)):
        return -10000
    # Los retrasos de Metro no se representan con obras antiguas sin relación.
    if (category == "Metro"
            and re.search(r"\b(?:retrasos?|demoras?|caos|avances?|operan|servicio)\b", headline)
            and not re.search(r"\b(?:obras?|construccion|remodelacion)\b", headline)
            and re.search(r"\b(?:obras?|construccion|remodelacion)\b", topic)):
        return -10000
    # Una entrega, adquisición o presentación de patrullas no ilustra un decomiso de autopartes.
    autoparts_story = bool(re.search(
        r"\b(?:autopartes?|refacciones?|deshuesaderos?|piezas? de (?:autos?|vehiculos?))\b",
        headline,
    ))
    patrol_procurement_photo = bool(re.search(
        r"\b(?:adquisicion|compra|presentacion|entrega|graduacion|ceremonia|nuevas?)\b.{0,60}\b(?:patrullas?|policias?)\b",
        topic,
    ))
    if autoparts_story and patrol_procurement_photo:
        return -10000
    # En titulares en vivo, el texto tras dos puntos puede resumir otros asuntos;
    # para la pertinencia visual se prioriza el hecho principal antes de los dos puntos.
    gas_emergency = bool(re.search(STRICT_PHOTO_TOPICS[0][0], headline_for_photos))
    strict_headline = _photo_fold(raw_headline.split(":", 1)[0]) if gas_emergency else headline_for_photos
    # «Bosques al asfalto» es una metáfora sobre fauna urbana, no pavimentación.
    strict_headline = re.sub(r"\bbosques al asfalto\b", "bosques", strict_headline)
    # Una noticia sobre carretera en Guerrero puede usar una foto contextual de esa misma región,
    # aunque el titular también mencione protestas en CDMX. No es una foto del proyecto anunciado.
    guerrero_road_story = bool(
        re.search(r"\bcarretera\b", headline_for_photos)
        and re.search(r"\bguerrero\b", headline_for_photos)
    )
    guerrero_road_photo = bool(
        re.search(r"\bcarretera\b", context)
        and re.search(r"\bguerrero\b", context)
    )
    # El título y el descriptor deben compartir el asunto real de la nota.
    for headline_pattern, photo_pattern in STRICT_PHOTO_TOPICS:
        if re.search(headline_pattern, strict_headline) and not re.search(photo_pattern, context):
            if "protest" in headline_pattern and guerrero_road_story and guerrero_road_photo:
                continue
            return -10000
    # Una amenaza sin protesta requiere contexto de seguridad, no un simulacro.
    threat_story = bool(re.search(r"\b(?:amenaz\w*|vecino armado)\b", headline_for_photos))
    threat_photo = bool(re.search(
        r"\b(?:policias?|patrullas?|seguridad|fiscalia|investigacion penal|operativo policial)\b",
        context,
    ))
    if threat_story and not protest_story and not threat_photo:
        return -10000
    # Una protesta sin componente ciclista no se ilustra con estaciones de EcoBici.
    # Sí conservar imágenes de rodadas cuando el titular las menciona expresamente.
    if (re.search(r"\b(?:movilizaciones?|manifestaciones?|plantones?|concentraciones?|protest\w*|marchas?)\b", headline)
            and not re.search(r"\b(?:rodadas?|ciclistas?|bicicletas?|ecobici)\b", headline)
            and re.search(r"\b(?:ecobici\w*|bicicletas?|ciclistas?|rodadas?)\b", topic)
            and not re.search(r"\b(?:protestas?|manifestaciones?|marchas?|bloqueos?|plantones?)\b", topic)):
        return -10000
    # Un choque vial no ocurrió en un autódromo solo por compartir alcaldía.
    if (re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and not re.search(r"\b(?:autodromo|formula 1|f1|gran premio|carrera|circuito|bottas|verstappen|hamilton|alonso|checo|antonelli)\b", headline)
            and re.search(r"\b(?:autodromo|formula 1|gran premio|pista de carreras)\b", topic)):
        return -10000
    # Choques de autos o motocicletas no se ilustran con trolebuses ni trenes.
    if (re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and re.search(r"\b(?:autos?|automovil\w*|vehicul\w*|motociclet\w*|motociclist\w*|motos?)\b", headline)
            and not re.search(r"\b(?:trolebus|metrobus|tren ligero|metro)\b", headline)
            and re.search(r"\b(?:trolebus|metrobus|tren ligero|estacion del metro)\b", topic)):
        return -10000
    # En choques de motos y autos, una carretera histórica o calle turística
    # no basta: se exige tráfico, vehículos o el lugar exacto de la alcaldía.
    borough=_photo_fold(article.get("borough"))
    if (re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and re.search(r"\b(?:autos?|automovil\w*|motociclet\w*|motociclist\w*|motos?)\b", headline)
            and not (borough and borough in topic)
            and not re.search(r"\b(?:motociclet\w*|motociclist\w*|motos?|autos?|automovil\w*|vehicular|trafico|transito|vialidad|choque)\b", topic)):
        return -10000
    # Una detención no se ilustra con entrega de patrullas o policía dirigiendo tráfico.
    if re.search(r"\b(?:detienen|detenido\w*|arrestan|capturan|aprehenden|procesan|vinculan a proceso)\b", headline):
        if re.search(r"\b(?:entrega (?:de )?(?:nuevas? )?patrullas|nuevas? patrullas|graduacion|ceremonia|controlando el semaforo|policia de transito)\b", topic):
            return -10000
    # Un corte de agua no se ilustra con elementos decorativos de un parque.
    if re.search(r"\b(?:sin agua|falta de agua|corte de agua|suspension de agua)\b", headline):
        if re.search(r"\b(?:bosque de chapultepec|parque|jardin|fuente ornamental)\b", topic):
            return -10000
    # Patrullas compradas para otra alcaldía no documentan una detención.
    if (re.search(r"\b(?:detienen|detenido\w*|arrestan|capturan|aprehenden)\b", headline)
            and re.search(r"\b(?:adquisicion|compra|presentacion|entrega)\b.*\bpatrullas?\b", topic)):
        return -10000
    # Una ceremonia policial o un desfile no representa un asesinato o ataque.
    if (re.search(r"\b(?:asesina(?:n)?|asesinato|ataques? armados?|balacera|matan|homicidio|balead\w*|balear\w*|balean)\b", headline)
            and re.search(r"\b(?:graduacion|ceremonia|adquisicion|entrega de patrullas|proteccion civil|desfile|catrinas?)\b", topic)):
        return -10000
    # Una avenida turística de otra zona no ilustra un choque local.
    borough=_photo_fold(article.get("borough"))
    if (borough and re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and re.search(r"\b(?:autos?|automovil\w*|motociclet\w*|motociclist\w*|motos?)\b", headline)
            and re.search(r"\b(?:avenida|calle|paseo|centro historico|torre latinoamericana)\b", topic)
            and borough not in topic
            and not re.search(r"\b(?:trafico|transito|vehicular|vialidad|motos?|motociclet\w*|autos?|automovil\w*)\b", topic)):
        return -10000
    # Una graduación policial no ilustra una muerte violenta o sentencia penal.
    if (re.search(r"\b(?:ejecutan|ejecutad\w*|ejecucion|matan|balazos|asesinan|homicidio|condenad[oa]s?|condenan|prision)\b", headline)
            and re.search(r"\b(?:graduacion|ceremonia de policia|(?:adquisicion|compra|presentacion|entrega)\b.*\b(?:nuevas?\s+)?patrullas?|entrega de patrullas)\b", topic)):
        return -10000
    # Una nota del Hoy No Circula requiere contexto vehicular, no fotos de la festividad.
    if re.search(r"\bhoy no circula\b", headline):
        if not re.search(r"\b(?:vehiculos?|vehicular|automoviles?|autos?|coches?|transito|trafico|vialidad|circulacion|hologramas?|verificacion vehicular|hoy no circula)\b", context):
            return -10000
    # Para noticias de ciclismo, exigir una fotografía relacionada con bicicletas.
    if re.search(r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b", headline):
        if not re.search(r"\b(?:bici|bicicletas?|ciclistas?|ciclovias?|ecobici\w*|cicloton)\b", context):
            return -10000
    # Distinguir noticias del circuito de avisos de cierres viales por el GP.
    # Una imagen del transporte público o una calle ajena no ilustra el evento.
    if re.search(r"\b(?:gp de mexico|gran premio|formula 1|autodromo)\b", headline):
        race_context = r"\b(?:formula 1|f1|gran premio|autodromo|circuito|carrera|monoplaza|piloto|automovilismo)\b"
        road_context = r"\b(?:vialidad|trafico|avenida|calles?|calzada|reforma|insurgentes|periferico|cierres? viales?)\b"
        road_closure = re.search(r"\b(?:calles? cerradas?|cierres?|alternativas viales|rutas alternas)\b", headline)
        if road_closure:
            if re.search(r"\b(?:metrobus|trolebus|ecobici|bicicletas?|estacion)\b", topic):
                return -10000
            if not (re.search(race_context, topic) or re.search(road_context, topic)):
                return -10000
        elif not re.search(race_context, topic):
            return -10000
    # Un rescate patrimonial de una fuente no se ilustra con rescates de viviendas.
    # Coincidir en el verbo "rescate" y en la alcaldía no basta.
    if (re.search(r"\bfuente [a-z]", headline)
            and re.search(r"\b(?:rescate|restauracion|rehabilitacion|premia|premio)\b", headline)):
        if not re.search(r"\b(?:fuentes?|esculturas?|monumentos?|patrimonio|plazas?|jardines?)\b", topic):
            return -10000
    # La Rodada del Terror y los corralones de motos requieren imágenes de motocicletas,
    # no una foto genérica de Protección Civil.
    if (re.search(r"\b(?:rodada del terror|mega rodada del terror|megarodadadelterror)\b", headline)
            or (re.search(r"\bcorralon\b", headline)
                and re.search(r"\b(?:motos?|motocicletas?|motociclistas?)\b", headline))):
        if not re.search(r"\b(?:motos?|motocicletas?|motociclistas?|rodada)\b", context):
            return -10000
    # Un incidente en pista de Fórmula 1 no es un incidente del Metrobús.
    if (re.search(r"\b(?:bottas|verstappen|hamilton|formula 1|f1)\b", headline)
            and re.search(r"\b(?:accidente|bandera roja|choque)\b", headline)):
        if not re.search(r"\b(?:formula 1|f1|autodromo|circuito|carrera|monoplaza|piloto|automovilismo)\b", topic):
            return -10000
    # La consulta infantil no se ilustra con una fotografía de cuarentena.
    if (re.search(r"\b(?:urnas?|consulta|votacion|elecciones?)\b", headline)
            and re.search(r"\b(?:ninos?|menores?|infancia|adolescentes?)\b", headline)):
        if not re.search(r"\b(?:urnas?|votacion|elecciones?|consulta|infancia|ninos?|menores?|escuelas?|estudiantes?|boletas?)\b", topic):
            return -10000
    # Un programa invernal requiere contexto de frío o asistencia social.
    if re.search(r"\b(?:temporada invernal|plan invernal|programa invernal|frente frio|cobijas?|vacunacion)\b", headline):
        if not re.search(r"\b(?:invierno|invernal|frio|cobijas?|albergue|vacunacion|abrigo|apoyo social|proteccion civil|clima|nubes|temperatura)\b", topic):
            return -10000
    # Los pilotos, abandonos y triunfos de F1 no se ilustran con paisajes turísticos.
    if (re.search(r"\b(?:alonso|bottas|verstappen|hamilton|antonelli|checo)\b", headline)
            and re.search(r"\b(?:abandon\w*|gran premio|formula 1|gp|carrera|piloto|campeon\w*|bandera roja|gana|gano|ganaron|ganador\w*|triunf\w*|victoria|venc\w*|podio|pole|sexta vez)\b", headline)):
        if not re.search(r"\b(?:formula 1|f1|gran premio|autodromo|circuito|carrera|monoplaza|piloto|automovilismo)\b", topic):
            return -10000
    # Una línea distinta del Metro es peor que una foto genérica del Metro.
    # Los titulares pueden enumerar varias líneas: aceptar cualquiera de ellas,
    # pero nunca ilustrar la nota con una línea que no aparece en esa lista.
    metro_wanted_lines=set()
    metro_photo_line=None
    if category=="Metro":
        wanted=re.search(
            r"\b(?:lineas?|lines?)\s+((?:[0-9]{1,2}|a|b)(?:\s*(?:,|\by\b)?\s*(?:[0-9]{1,2}|a|b))*)",
            headline,
        )
        if wanted:
            metro_wanted_lines=set(
                re.findall(r"\b(?:[0-9]{1,2}|a|b)\b",wanted.group(1))
            )
        shown=re.search(r"\b(?:linea|line) ([0-9]{1,2}|a|b)\b",topic)
        metro_photo_line=shown.group(1) if shown else None
        if (metro_wanted_lines and metro_photo_line
                and metro_photo_line not in metro_wanted_lines):
            return -10000
    if re.search(r"\b(?:cablebus|teleferico)\b", headline):
        wanted_lines = set(re.findall(r"\blineas? ([0-9]{1,2})\b", headline))
        shown_lines = set(re.findall(r"\blinea ([0-9]{1,2})\b", topic))
        if wanted_lines and shown_lines and not wanted_lines.intersection(shown_lines):
            return -10000
    borough=_photo_fold(article.get("borough"))
    score=65 if photo_category==category else (12 if photo_category=="CDMX" else 0)
    if road_incident_story and road_traffic_photo:
        score += 220
    cinema_story=bool(re.search(r"\b(?:cine de barrio|festival(?: de)? cine)\b",headline))
    cinema_photo=bool(re.search(
        r"\b(?:bosquecinema|cine|cinema|cineclub|cineteca|proyecciones?|peliculas?|filmoteca)\b",
        context,
    ))
    if cinema_story and cinema_photo:
        score += 120
    if police_operation_story and police_context:
        score += 180
    if lgbt_story and lgbt_photo:
        score += 240
    if photo_category=="Alcaldías" and not borough:
        score-=30
    if borough and borough in topic:
        score+=170
    elif borough and borough in keywords:
        score+=100
    tokens={x for x in headline_for_photos.split() if len(x)>3 and x not in STOP_WORDS}
    for word in tokens:
        if re.search(r"\b"+re.escape(word)+r"\b",topic):
            score+=34
        elif re.search(r"\b"+re.escape(word)+r"\b",keywords):
            score+=12
    for pattern,similar in RELATED_WORDS:
        if re.search(pattern,headline_for_photos) and any(
            re.search(r"\b"+re.escape(word)+r"\b",topic) for word in similar
        ):
            score+=80
    if category=="Metro" and metro_photo_line in metro_wanted_lines:
        score+=220
    if infrastructure_story and infrastructure_photo:
        score+=180
    if education_story and education_photo:
        score+=220
    if housing_story and housing_photo:
        score+=220
    if environmental_story and environmental_photo:
        score+=180
    if eco_story and eco_photo:
        score+=180
    if tax_story and tax_photo:
        score+=180
    if delivery_story and delivery_photo:
        score+=120
    if bar_business_story and bar_business_photo:
        score+=100
    if street_food_story and street_food_photo:
        score+=100
    if ride_hailing_story and ride_hailing_photo:
        score+=120
    if legislative_story and legislative_photo:
        score+=120
    if planning_story and planning_photo:
        score+=120
    if music_story and music_photo:
        score+=120
    if theater_story and theater_photo:
        score+=160
    if weather_story and weather_photo:
        score+=80
    if motorcycle_story and motorcycle_photo:
        score+=120
    if migration_story and migration_photo:
        score+=120
    if entertainment_person_story and entertainment_photo:
        score+=120
    return score


def assign_photos(items):
    """Conserva fotos representativas acreditadas del feed salvo que exista una opción mejor."""
    pool = _pool()
    reserved = set()
    verified_catalog = _load(VERIFIED_EVENTS, "photos")
    exact_count = 0

    def has_complete_credit(photo):
        if not isinstance(photo, dict) or photo.get("kind") != "representativa":
            return False
        photo_url = str(photo.get("url") or "").strip()
        return (
            bool(photo_url)
            and (
                photo_url.startswith(("https://", "http://"))
                or photo_url.startswith("/assets/fotos/")
            )
            and all(str(photo.get(key) or "").strip() for key in (
                "source", "author", "license", "licenseUrl"
            ))
            and str(photo.get("source") or "").startswith(("https://", "http://"))
            and str(photo.get("licenseUrl") or "").startswith(("https://", "http://"))
        )

    # Un orden estable evita cambios arbitrarios entre actualizaciones del feed.
    for article in items:
        exact = verified_event_photo(article, verified_catalog)
        if exact:
            article["photo"] = exact
            if exact.get("id"):
                reserved.add(exact["id"])
            exact_count += 1
            continue

        # Los titulares sensibles nunca reciben fotografías de contexto.
        if is_sensitive_media(article):
            article["sensitive_media"] = True
            article.pop("photo", None)
            continue

        existing = article.get("photo")
        existing_score = (
            _photo_score(article, existing) if has_complete_credit(existing) else -10000
        )
        available = [photo for photo in pool if photo.get("id") not in reserved]

        def best_candidate(candidates):
            if not candidates:
                return None, -10000
            candidate = max(candidates, key=lambda photo: (
                _photo_score(article, photo),
                # Desempate estable, sin elegir siempre el primer elemento de la categoría.
                hashlib.sha256(
                    (str(article.get("url")) + "|" + str(photo.get("id"))).encode()
                ).hexdigest(),
            ))
            return candidate, _photo_score(article, candidate)

        best, best_score = best_candidate(available)
        # Si las fotos aún no usadas no sirven para este tema, permite reutilizar
        # la mejor foto pertinente ya reservada en vez de dejar la noticia sin imagen.
        if best_score < 0 and len(available) < len(pool):
            fallback, fallback_score = best_candidate(pool)
            if fallback_score > best_score:
                best, best_score = fallback, fallback_score

        # Si no hay reemplazo pertinente, conserva la foto anterior solo si
        # sigue siendo pertinente y tiene autor, licencia y fuente completos.
        if existing_score >= 0 and (best is None or best_score <= existing_score):
            if existing.get("id"):
                reserved.add(existing["id"])
            article["photo"] = existing
            continue

        if best is not None and best_score >= 0:
            article["photo"] = best
            if best.get("id"):
                reserved.add(best["id"])
        else:
            article.pop("photo", None)

    return {
        "available": len(pool),
        "assigned": sum(bool(article.get("photo")) for article in items),
        "unique": len({
            article["photo"]["id"] for article in items
            if isinstance(article.get("photo"), dict) and article["photo"].get("id")
        }),
        "del_hecho_verificadas": exact_count,
    }

