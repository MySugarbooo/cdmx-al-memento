#!/usr/bin/env python3
"""Generate crawlable article summaries from the existing editorial news.json.
Run after the news feed has been updated. Does not change existing article URLs.
"""
import json
import html
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cdmx-al-memento.pages.dev"
SOURCE = ROOT / "news.json"
OUT = ROOT / "articulos"
SITEMAP = ROOT / "sitemap-articulos.xml"
VERIFIED_SOURCE_LINKS = {
    ("El Sol de San Juan del Río", "/noticias/?id=b37ba45fa2fa424b73bd&mes=2026-11"):
        "https://oem.com.mx/elsoldesanjuandelrio/policiaca/toma-precauciones-si-viajas-a-la-cdmx-autopista-57-esta-detenida-33095499",
    ("La Prensa", "/noticias/?id=00c19362c5f0468f82b1&mes=2026-11"):
        "https://oem.com.mx/la-prensa/policiaca/detienen-a-otro-presunto-maltratador-de-animales-en-tlalpan-33095643",
    ("La Prensa", "/noticias/?id=48ad03698ec605252a33&mes=2026-11"):
        "https://oem.com.mx/la-prensa/policiaca/mueren-dos-motociclistas-tras-chocar-contra-una-camioneta-en-venustiano-carranza-33118910",
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
    ("Hoy Tamaulipas", "/noticias/?id=5a9a1f1ebbab943a2f55&mes=2026-11"):
        "https://www.hoytamaulipas.net/notas/607182/El-Mante-presente-en-la-Asamblea-Nacional-de-Seguridad-Publica-Municipal-2025.html",
}
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

def is_sensitive_media(item):
    """Evita ilustraciones genéricas en noticias sobre violencia sexual o crueldad animal."""
    return (item.get("sensitive_media") is True or
            bool(SENSITIVE_MEDIA_TITLE.search(str(item.get("title") or ""))))

def has_verified_event_photo(photo):
    return (isinstance(photo, dict) and photo.get("kind") == "hecho" and
            photo.get("verified") is True and bool(photo.get("evidence_url")))

def esc(value):
    return html.escape(str(value or ""), quote=True)

def article_id(item):
    match = re.fullmatch(r"/noticias/\?id=([a-f0-9]{20})&mes=\d{4}-\d{2}", item.get("local_url", ""))
    return match.group(1) if match else None

def render_photo(item):
    photo = item.get("photo")
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
    return ('<figure class="article-photo"><img src="' + esc(image_url) + '" alt="' +
            esc("Imagen representativa de " + str(item.get("category") or "Ciudad de México") if photo.get("kind") == "representativa" else "Fotografía relacionada con la noticia") +
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
    original = item.get("source_url") or item.get("url") or ""
    source_link = ""
    origin = urlparse(original)
    allowed_hosts = ("news.google.com", "commons.wikimedia.org")
    curated_hosts = ("comova.mx", "mayacomunicacion.com.mx", "www.elgrafico.mx")
    verified_source = VERIFIED_SOURCE_LINKS.get((item.get("source"), item.get("local_url")))
    authorized = (origin.hostname in allowed_hosts or
                  (item.get("editorial_verified") is True and
                   origin.hostname in curated_hosts and origin.path != "/") or
                  (verified_source is not None and original == verified_source))
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

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    articles = data.get("articles") or []
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
            archived = json.loads(archive_path.read_text(encoding="utf-8"))
            if isinstance(archived, dict):
                archived = archived.get("articles", archived.get("news", []))
            if not isinstance(archived, list):
                raise RuntimeError("Formato de archivo mensual inválido: " + month_name)
            articles.extend(archived)
    OUT.mkdir(exist_ok=True)
    urls = []
    recent_links = []
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
        if len(recent_links) < 12:
            recent_links.append((ident, item["title"]))
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
