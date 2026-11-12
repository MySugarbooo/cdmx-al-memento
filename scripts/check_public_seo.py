#!/usr/bin/env python3
"""Validate public news, archive, article pages, credits and SEO deployment."""
from html.parser import HTMLParser
import html
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from pathlib import Path
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cdmx-al-memento.pages.dev"
DEPLOY_ATTEMPTS = 18
DEPLOY_RETRY_SECONDS = 10


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("/articulos/"):
                self.hrefs.append(href)


def fetch(path, timeout=25):
    req = Request(BASE + path, headers={"User-Agent": "CDMX-SEO-HealthCheck/2.0"})
    with urlopen(req, timeout=timeout) as response:
        data = response.read()
        if response.status != 200:
            raise ValueError(f"{path}: HTTP {response.status}")
        return data


def fetch_until(path, validator, *, attempts=DEPLOY_ATTEMPTS,
                delay=DEPLOY_RETRY_SECONDS, timeout=25):
    """Wait for Cloudflare Pages to serve the same snapshot that main generated."""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            data = fetch(path, timeout=timeout)
            validator(data)
            return data
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                print(
                    f"WAIT {path}: {exc} "
                    f"(intento {attempt}/{attempts}); esperando publicación de Pages."
                )
                time.sleep(delay)
    raise ValueError(
        f"Cloudflare Pages no publicó una versión coherente de {path} "
        f"tras {attempts} intentos: {last_error}"
    )


def load_local_json(relative):
    path = ROOT / relative
    if not path.is_file():
        raise ValueError(f"Falta el archivo local requerido: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_digest(value):
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def archive_records(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("articles", "news", "items"):
            if isinstance(value.get(key), list):
                return value[key]
    raise ValueError("El archivo mensual no contiene una lista de noticias")


def article_id(item):
    local_url = str(item.get("local_url") or "")
    match = re.fullmatch(
        r"/noticias/\?id=([a-f0-9]{20})&mes=\d{4}-\d{2}", local_url
    )
    return match.group(1) if match else None


def validate_feed(data):
    if not isinstance(data, dict) or not isinstance(data.get("articles"), list):
        raise ValueError("/news.json: formato de feed inválido")
    if not data.get("updated"):
        raise ValueError("/news.json: falta la fecha de actualización")
    articles = data["articles"]
    if not articles:
        raise ValueError("/news.json: feed vacío")
    source_urls = []
    local_urls = []
    for index, item in enumerate(articles):
        if not isinstance(item, dict):
            raise ValueError(f"/news.json: artículo {index} no es un objeto")
        for field in ("title", "url", "source", "date", "category", "location", "local_url"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"/news.json: artículo {index} sin {field}")
        if not item["url"].startswith("https://"):
            raise ValueError(f"/news.json: URL externa no HTTPS en artículo {index}")
        if not item["local_url"].startswith("/noticias/"):
            raise ValueError(f"/news.json: enlace local inválido en artículo {index}")
        source_urls.append(item["url"])
        local_urls.append(item["local_url"])
        photo = item.get("photo")
        if photo is not None:
            if not isinstance(photo, dict):
                raise ValueError(f"/news.json: fotografía inválida en artículo {index}")
            for field in ("url", "author", "license", "licenseUrl", "source"):
                if not isinstance(photo.get(field), str) or not photo[field].strip():
                    raise ValueError(
                        f"/news.json: fotografía sin {field} en artículo {index}"
                    )
            if not photo["licenseUrl"].startswith("https://"):
                raise ValueError(f"/news.json: licencia no HTTPS en artículo {index}")
            if not photo["source"].startswith("https://"):
                raise ValueError(f"/news.json: origen fotográfico no HTTPS en artículo {index}")
    if len(source_urls) != len(set(source_urls)):
        raise ValueError("/news.json: enlaces originales duplicados")
    if len(local_urls) != len(set(local_urls)):
        raise ValueError("/news.json: enlaces internos duplicados")
    return articles


def parse_sitemap(data, label):
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"{label}: XML inválido: {exc}") from exc
    if not root.tag.endswith("urlset"):
        raise ValueError(f"{label}: XML root is not urlset")
    locs = [
        (node.text or "").strip()
        for node in root.iter()
        if node.tag.endswith("loc")
    ]
    if not locs or not all(locs):
        raise ValueError(f"{label}: no contiene direcciones loc")
    if len(locs) != len(set(locs)):
        raise ValueError(f"{label}: contiene URLs duplicadas")
    if not all(urlparse(url).netloc == urlparse(BASE).netloc for url in locs):
        raise ValueError(f"{label}: contiene una URL fuera del dominio público")
    return set(locs)


def validate_article_html(item, data):
    html = data.decode("utf-8")
    for field in ("title", "location", "date", "source"):
        value = str(item.get(field) or "")
        if value and html.escape(value, quote=True) not in html:
            raise ValueError(f"el artículo público no contiene el campo {field}")
    photo = item.get("photo")
    if isinstance(photo, dict):
        for field in ("author", "license"):
            value = str(photo.get(field) or "")
            if value and html.escape(value, quote=True) not in html:
                raise ValueError(f"el artículo público no contiene el crédito {field}")
    elif item.get("sensitive_media") is True:
        if "Sin fotografía verificada del hecho" not in html:
            raise ValueError("la noticia sensible no muestra el aviso de fotografía")
    return True


def check_public_data():
    local_news = load_local_json("news.json")
    articles = validate_feed(local_news)
    local_manifest = load_local_json("archivo/meses.json")
    if local_manifest.get("retention_days") != 365:
        raise ValueError("archivo/meses.json: la retención ya no es de 365 días")
    months = local_manifest.get("months")
    if not isinstance(months, list) or not months:
        raise ValueError("archivo/meses.json: no hay meses indexados")

    def same_json_validator(expected, label):
        expected_digest = canonical_digest(expected)

        def validate(data):
            actual = json.loads(data.decode("utf-8"))
            if canonical_digest(actual) != expected_digest:
                raise ValueError(f"{label}: el contenido público no coincide con main")
        return validate

    fetch_until("/news.json", same_json_validator(local_news, "/news.json"))
    print(
        f"OK /news.json: {len(articles)} noticias, enlaces únicos y créditos completos"
    )
    fetch_until(
        "/archivo/meses.json",
        same_json_validator(local_manifest, "/archivo/meses.json"),
    )
    archive_total = 0
    for month in months:
        name = str(month.get("month") or "")
        if not re.fullmatch(r"\d{4}-\d{2}", name):
            raise ValueError("archivo/meses.json: nombre de mes inválido")
        relative = f"archivo/{name}.json"
        local_archive = load_local_json(relative)
        count = len(archive_records(local_archive))
        expected_count = int(month.get("count") or 0)
        if count != expected_count:
            raise ValueError(
                f"{relative}: main contiene {count} registros, índice declara {expected_count}"
            )
        fetch_until(
            str(month.get("url") or f"/{relative}"),
            same_json_validator(local_archive, relative),
            timeout=45,
        )
        archive_total += count
        print(f"OK /{relative}: {count} registros coinciden con main")

    local_main_sitemap = parse_sitemap(
        (ROOT / "sitemap.xml").read_bytes(), "sitemap.xml local"
    )
    local_article_sitemap = parse_sitemap(
        (ROOT / "sitemap-articulos.xml").read_bytes(),
        "sitemap-articulos.xml local",
    )

    def sitemap_validator(expected, label):
        def validate(data):
            actual = parse_sitemap(data, label)
            if actual != expected:
                missing = len(expected - actual)
                extra = len(actual - expected)
                raise ValueError(
                    f"{label}: contenido distinto de main ({missing} faltantes, {extra} sobrantes)"
                )
        return validate

    fetch_until(
        "/sitemap.xml",
        sitemap_validator(local_main_sitemap, "/sitemap.xml"),
    )
    print(f"OK /sitemap.xml: {len(local_main_sitemap)} URLs coinciden con main")
    fetch_until(
        "/sitemap-articulos.xml",
        sitemap_validator(local_article_sitemap, "/sitemap-articulos.xml"),
    )
    print(
        f"OK /sitemap-articulos.xml: {len(local_article_sitemap)} URLs coinciden con main"
    )

    targets = []
    for item in articles[:3]:
        if article_id(item):
            targets.append(item)
    cablebus = next(
        (item for item in articles if "cablebús" in item["title"].casefold()),
        None,
    )
    if cablebus and cablebus not in targets and article_id(cablebus):
        targets.append(cablebus)
    for item in targets:
        ident = article_id(item)
        path = f"/articulos/{ident}/"
        if BASE + path not in local_article_sitemap:
            raise ValueError(f"{path}: el artículo no está incluido en el sitemap local")
        fetch_until(
            path,
            lambda data, article=item: validate_article_html(article, data),
        )
        print(f"OK {path}: título, ubicación y créditos coinciden con news.json")

    photo_index = load_local_json("assets/fotos/indice-noticias-1100.json")
    photo_count = int(photo_index.get("count") or len(photo_index.get("photos") or []))

    def validate_credits(data):
        html = data.decode("utf-8")
        if f"{photo_count:,}" not in html:
            raise ValueError(
                f"/creditos-fotograficos.html: el catálogo público no muestra {photo_count:,} imágenes"
            )
        if "atribuciones" not in html.casefold() or "licencia" not in html.casefold():
            raise ValueError("/creditos-fotograficos.html: faltan atribuciones o licencias")

    fetch_until("/creditos-fotograficos.html", validate_credits)
    print(
        f"OK /creditos-fotograficos.html: {photo_count:,} imágenes con atribuciones"
    )
    print(f"OK hemeroteca: {archive_total} registros en {len(months)} meses")


def check_community():
    html = fetch("/comunidad/").decode("utf-8")
    required = {
        'id="cdmx-comments"': "contenedor de comentarios",
        'id="forum-search"': "buscador del foro",
        'id="forum-question-title"': "editor de preguntas",
        "comments-config.js": "configuración pública de Firebase",
        "comments.js": "cliente de comentarios",
    }
    missing = [label for marker, label in required.items() if marker not in html]
    if missing:
        raise ValueError("/comunidad/: faltan elementos: " + ", ".join(missing))
    print("OK /comunidad/: foro, comentarios y scripts de acceso presentes")


def check_engagement():
    path = (
        "/api/engagement?article="
        "%2Fnoticias%2F%3Fid%3Db37ba45fa2fa424b73bd%26mes%3D2026-11"
    )
    req = Request(BASE + path, headers={"User-Agent": "CDMX-SEO-HealthCheck/2.0"})
    try:
        with urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if response.status != 200:
                raise ValueError(f"/api/engagement: HTTP {response.status}")
            if not all(key in payload for key in ("visitors", "likes", "liked")):
                raise ValueError("/api/engagement: faltan contadores en la respuesta")
            print("OK /api/engagement: visitantes y Me gusta responden")
    except HTTPError as exc:
        if exc.code == 503:
            print(
                "::warning:: /api/engagement devolvió HTTP 503; LIKES_DB o sus tablas "
                "no están disponibles y los contadores reales no pudieron verificarse."
            )
        else:
            raise


def main():
    for path in ("/", "/archivo/"):
        parser = Links()
        parser.feed(fetch(path).decode("utf-8"))
        if not parser.hrefs:
            raise ValueError(f"{path}: no static article links found")
        print(f"OK {path}: {len(parser.hrefs)} article links")
    check_public_data()
    check_community()
    check_engagement()
    print("Public SEO content checks passed")


if __name__ == "__main__":
    main()
