"""Notas de lectura editorial cuidadosa sobre titulares de medios enlazados.

No descarga textos protegidos, no simula entrevistas ni presenta los titulares
como hechos verificados. Solo elabora una tesis temática cuando al menos dos
medios identificables publicaron notas pertinentes sobre el mismo asunto.
"""
from __future__ import annotations

import html
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

MX = ZoneInfo("America/Mexico_City")


def norm(value):
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", str(value or "").lower())
        if not unicodedata.combining(ch)
    )


# Conclusiones interpretativas prudentes; nunca equivalen a afirmar
# que la noticia se verificó ni reemplazan una fuente primaria.
THEMES = [
    {
        "id": "metro-a",
        "title": "La Línea A del Metro: informar sin convertir advertencias en cierres",
        "match": lambda t: "linea a" in t and bool(re.search(r"metro|servicio|sindic|rehabilit|suspensi", t)),
        "thesis": "Una advertencia sobre mantenimiento o sobre una posible suspensión merece seguimiento público, pero no puede difundirse como si el servicio ya estuviera cerrado. La distinción entre una petición, un riesgo y una medida confirmada es esencial para quienes dependen del transporte.",
        "evidence": "Los medios seleccionados mencionan la Línea A y plantean advertencias o preocupaciones relacionadas con su servicio. Esa coincidencia acredita que el tema ha sido cubierto por medios distintos; no demuestra por sí sola que una suspensión se haya ejecutado.",
        "unknown": "Hace falta consultar directamente los avisos actuales del Metro, las fechas y tramos precisos afectados, y distinguir las declaraciones sindicales de las decisiones operativas. La cobertura periodística enlazada puede haber cambiado desde su publicación.",
        "opinion": "Consideramos que una persona que sale a trabajar, estudiar o cuidar a alguien necesita información sin alarmismo. Informar con empatía implica no sembrar miedo por un cierre no confirmado y, al mismo tiempo, tomar en serio las inquietudes sobre mantenimiento.",
        "conclusion": "El asunto amerita vigilancia y preguntas concretas sobre mantenimiento y comunicación del servicio; los titulares reunidos no permiten afirmar un cierre efectivo.",
        "official": ("Red del Metro CDMX · fuente oficial de referencia", "https://www.metro.cdmx.gob.mx/la-red"),
    },
    {
        "id": "movilizaciones-imss",
        "title": "Marchas y movilidad: escuchar las demandas y cuidar los traslados",
        "match": lambda t: "imss" in t and bool(re.search(r"marcha|moviliz|bloqueo|protest|manifest", t)),
        "thesis": "Una convocatoria o un operativo alrededor de una manifestación no equivale automáticamente a un bloqueo confirmado. La noticia debe explicar qué anunciaron los actores involucrados y qué autoridades han informado sobre la movilidad.",
        "evidence": "Varios titulares abordan movilizaciones relacionadas con el IMSS y sus posibles efectos en las vialidades. Son versiones publicadas por sus respectivos medios: no constituyen por sí solas el registro del tránsito en tiempo real.",
        "unknown": "Deben comprobarse el recorrido definitivo, la hora, los cierres vigentes y si la protesta continúa. Para organizar un traslado es preferible consultar avisos oficiales recientes y no depender de un encabezado antiguo.",
        "opinion": "El derecho a expresarse y la necesidad de llegar a una consulta médica, a la escuela o al empleo no deberían presentarse como una rivalidad entre personas. Una cobertura responsable escucha las demandas y ofrece datos útiles a quienes pueden verse afectados.",
        "conclusion": "La cobertura coincidente justifica seguir el desarrollo de la jornada, pero no autoriza a afirmar que todas las calles anunciadas permanecen cerradas.",
        "official": ("Secretaría de Seguridad Ciudadana de CDMX", "https://www.ssc.cdmx.gob.mx/"),
    },
    {
        "id": "clima-lluvias",
        "title": "Pronósticos de lluvia: comprender el riesgo antes de compartir alertas",
        "match": lambda t: bool(re.search(r"lluvia|chubasc|torment|inundac", t)) and
                           bool(re.search(r"cdmx|ciudad de mexico|valle de mexico|alcald", t)),
        "thesis": "La posibilidad de lluvias no debe confundirse con una emergencia en cada colonia. Un pronóstico se interpreta con hora y zona, mientras que una alerta oficial requiere consultar a la autoridad responsable.",
        "evidence": "Dos o más medios recientes mencionan condiciones de lluvia para la capital. Esa presencia en varios titulares es una señal de cobertura meteorológica, no una medición independiente de precipitaciones en todas las alcaldías.",
        "unknown": "Faltan ubicación precisa, intensidad, vigencia y actualizaciones oficiales antes de dar instrucciones locales. La Ciudad de México no tiene el mismo clima simultáneamente en todos sus barrios.",
        "opinion": "Queremos que las familias puedan prevenirse sin vivir entre mensajes alarmistas. Una advertencia útil debe ayudar a decidir si llevar paraguas o reconsiderar un trayecto, y reconocer cuándo no tenemos información suficiente.",
        "conclusion": "La lectura responsable es revisar pronósticos locales y avisos oficiales; los encabezados por sí solos no confirman inundaciones ni riesgos específicos.",
        "official": ("Secretaría de Gestión Integral de Riesgos y Protección Civil", "https://www.proteccioncivil.cdmx.gob.mx/"),
    },
    {
        "id": "vivienda-ciudad",
        "title": "Vivienda y gentrificación: atender las experiencias sin simplificar cifras",
        "match": lambda t: bool(re.search(r"gentrific|vivienda|alquiler|rentas? ", t)) and
                           bool(re.search(r"cdmx|cuauhtemoc|ciudad de mexico|condesa|roma", t)),
        "thesis": "Hablar del costo de vivir en la ciudad exige separar testimonios, estimaciones y datos oficiales. Una cifra citada en un titular no basta para describir por sí sola la situación de todas las familias.",
        "evidence": "Los artículos reunidos tratan preocupaciones por vivienda o transformaciones de barrios. Sus cifras, definiciones y periodos deben revisarse en los reportajes originales antes de presentarlos como hechos consolidados.",
        "unknown": "Para comparar información se necesitan fuentes estadísticas, metodología, fecha del dato y delimitación territorial. Los términos desplazamiento y cambio de residencia no siempre se usan con el mismo significado.",
        "opinion": "Detrás de una discusión sobre vivienda hay vecinas y vecinos con vínculos afectivos, trabajo y redes de apoyo. Merecen una cobertura respetuosa, sin reducir sus experiencias a un número ni atribuir intenciones sin pruebas.",
        "conclusion": "La inquietud merece documentación y escucha, no generalizaciones basadas en un único encabezado.",
        "official": ("INEGI · fuentes estadísticas", "https://www.inegi.org.mx/"),
    },
]


def recent_articles(rows, now):
    cutoff = now - timedelta(hours=42)
    kept = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", ""))
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "news.google.com":
            continue
        source = str(item.get("source") or "").strip()
        if not source or source.lower() == "medio externo":
            continue
        try:
            date = datetime.fromisoformat(str(item.get("published_at", "")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if date.tzinfo is None or not cutoff <= date.astimezone(timezone.utc) <= now + timedelta(minutes=15):
            continue
        if len(str(item.get("title", ""))) < 15:
            continue
        kept.append(item)
    return kept


def choose_topic(rows, now):
    articles = recent_articles(rows, now)
    candidates = []
    for priority, theme in enumerate(THEMES):
        matches = [a for a in articles if theme["match"](norm(a["title"]))]
        distinct = {}
        for article in matches:
            key = norm(article["source"]).removeprefix("www.")
            if key not in distinct:
                distinct[key] = article
        if len(distinct) >= 2:
            sample = list(distinct.values())[:4]
            latest = max(datetime.fromisoformat(a["published_at"].replace("Z", "+00:00")) for a in sample)
            candidates.append((latest, -priority, theme, sample))
    if candidates:
        chosen = max(candidates, key=lambda c: (c[0], c[1]))
        return chosen[2], chosen[3]
    return None, articles


def _link(article):
    from html import escape
    url = escape(str(article["url"]), quote=True)
    medium = escape(str(article["source"]))
    timestamp = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00")).astimezone(MX)
    published = timestamp.strftime("%d/%m/%Y %H:%M")
    return (
        '<li><a target="_blank" rel="noopener noreferrer nofollow" href="' + url + '">'
        + medium + '</a> · ' + published +
        ' · <small>Nota de origen: ' + escape(str(article["title"])[:170]) + '</small></li>'
    )


def build_editorial(rows, now=None):
    """Produce un análisis atribuido con tesis, evidencia, límites y postura.

    No convierte los titulares en prueba de hechos. Si faltan dos medios
    distintos sobre un asunto, genera reflexión metodológica, no una noticia.
    """
    now = now or datetime.now(timezone.utc)
    theme, matches = choose_topic(rows, now)
    if theme:
        title = theme["title"]
        thesis = theme["thesis"]
        evidence = theme["evidence"]
        unknown = theme["unknown"]
        opinion = theme["opinion"]
        conclusion = theme["conclusion"]
        official_label, official_url = theme["official"]
        citations = matches
        count_text = "Fuentes periodísticas relacionadas con este asunto"
    else:
        title = "La información que merece nuestra confianza debe poder comprobarse"
        thesis = (
            "Publicar rápido tiene valor cuando el lector puede distinguir lo que un "
            "medio asegura, lo que sigue sin confirmarse y qué documento o autoridad "
            "podría aclararlo. La variedad de titulares no constituye evidencia de "
            "un mismo acontecimiento."
        )
        evidence = (
            "El resumen reúne temas distintos publicados por medios identificables. "
            "No detectamos al menos dos medios independientes sobre uno de los "
            "asuntos específicos revisados, así que evitamos presentar una "
            "conclusión fáctica sobre un caso concreto."
        )
        unknown = (
            "Antes de convertir cada titular en un hecho verificado faltaría leer "
            "el reportaje original, contrastarlo con fuentes primarias y revisar "
            "si hubo correcciones o nuevos datos."
        )
        opinion = (
            "La persona que consulta noticias merece respeto y claridad, "
            "especialmente cuando la información afecta a su familia o sus "
            "traslados. Es preferible reconocer una duda que inventar seguridad."
        )
        conclusion = (
            "La mejor lectura de este corte es seguir fuentes identificadas y "
            "admitir los límites de una selección automatizada de titulares."
        )
        official_label = official_url = ""
        distinct = {}
        for article in matches:
            key = norm(article["source"]).removeprefix("www.")
            if key not in distinct:
                distinct[key] = article
        citations = list(distinct.values())[:3]
        count_text = "Ejemplos de titulares recientes para consultar directamente"
    e = html.escape
    source_html = (
        '<ol>' + "".join(_link(a) for a in citations) + '</ol>'
        if citations else '<p>No hay suficientes fuentes recientes para afirmar un hecho concreto.</p>'
    )
    if official_url:
        source_html += (
            '<p><strong>Para contrastar:</strong> <a href="' +
            e(official_url, quote=True) +
            '" target="_blank" rel="noopener noreferrer">' + e(official_label) +
            ' ↗</a>. Enlace de referencia; no se afirma haber consultado su estado en vivo.</p>'
        )
    return (
        '<section class="editorial-thesis" aria-labelledby="editorial-thesis-title">'
        '<p class="eyebrow">✒️ LECTURA EDITORIAL · ELABORACIÓN AUTOMATIZADA, NO REPORTAJE DE CAMPO</p>'
        '<h2 id="editorial-thesis-title">' + e(title) + '</h2>'
        '<p class="editorial-byline"><strong>Por Amau Kisumi</strong> · Columna editorial de CDMX AL MEMENTO</p>'
        '<h3>Tesis editorial</h3><p>' + e(thesis) + '</p>'
        '<h3>Qué aportan los titulares</h3><p>' + e(evidence) + '</p>'
        '<h3>Qué falta por comprobar</h3><p>' + e(unknown) + '</p>'
        '<h3>Nuestra opinión editorial · expresamente identificada</h3><p>' + e(opinion) + '</p>'
        '<h3>Conclusión razonada</h3><p>' + e(conclusion) + '</p>'
        '<h3>' + e(count_text) + '</h3>' + source_html +
        '<p class="evidence-notice">Fuentes: titulares y fechas publicados por sus medios en RSS de Google Noticias. '
        'No se ha revisado el contenido completo de los artículos, no hemos '
        'entrevistado testigos ni verificado hechos sobre el terreno. La tesis '
        'y la opinión son interpretaciones editoriales; no son declaraciones '
        'atribuidas a las fuentes. Las fechas indican publicación, no cuándo '
        'ocurrieron los acontecimientos.</p></section>'
    )
