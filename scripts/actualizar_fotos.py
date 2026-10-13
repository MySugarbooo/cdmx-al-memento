"""Actualiza, como máximo una vez al día, fotos contextuales de CDMX con licencia libre.

Busca fotografías *subidas recientemente* a Wikimedia Commons. La fecha de subida
NO prueba cuándo se tomó la foto, ni su relación con un hecho noticioso.
No sustituye portadas de las noticias ni utiliza imágenes de medios sin permiso.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "assets" / "fotos" / "recientes.json"
ENDPOINT = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "CDMXAlMemento/3.0 (https://cdmx-al-memento.pages.dev/contacto.html; photos with attribution)"
CHECK_EVERY_HOURS = 23
MAX_AGE_DAYS = 180
MAX_PER_TOPIC = 4
# Archivos concretos cuya ubicación y fecha han sido revisadas en sus fichas de Commons.
# Sirven como base; además se siguen descubriendo nuevas imágenes diariamente.
CURATED = {
    'Metro': (
        'Metro Hangares (2026) 2.jpg',
        'Metro Terminal Aérea (2026) 1.jpg',
        'Metro Bellas Artes - Línea 2 del Metro de la Ciudad de México - 2026 - 03.jpg',
    ),
    'Movilidad': (
        'Metrobús Hidalgo L7 (2026).jpg',
        'Metrobús Manuela Saénz (701851600 1422559626579369 6048225853831060350 n).jpg',
    ),
    'Cultura': (
        'Marcha del Orgullo en la Ciudad de México, 2026 01.jpg',
        'Museo del Cacao & Chocolate, CDMX 2026.jpg',
    ),
    'CDMX': (
        'Edificios, Paseo de la Reforma (CDMX) 0131.jpg',
    ),
}

QUERIES = {
    "CDMX": ("Ciudad de México", "Mexico City"),
    "Metro": ("Metro Ciudad de México", "Metro CDMX"),
    "Movilidad": ("Metrobús Ciudad de México", "Paseo de la Reforma CDMX"),
    "Seguridad": ("Policía Ciudad de México", "Patrulla CDMX"),
    "Cultura": ("Bellas Artes Ciudad de México", "Museo CDMX"),
    "Gobierno": ("Palacio Nacional México", "Gobierno CDMX"),
}
KEYWORDS = {
    "Metro": ("metro", "estacion", "linea 1", "linea 2"),
    "Movilidad": ("metrobus", "metrobús", "transporte", "autobus", "autobús", "vialidad", "reforma"),
    "Seguridad": ("policia", "policía", "patrulla", "bomberos", "seguridad", "proteccion civil"),
    "Cultura": ("bellas artes", "museo", "mural", "cultura", "exposicion", "danza", "teatro"),
    "Gobierno": ("palacio nacional", "gobierno", "congreso", "secretaria", "alcaldia"),
}
LOCATION_WORDS = ("ciudad de mexico", "mexico city", "cdmx", "mexico df", "mexico, d.f.",
                  "distrito federal", "mexico city", "mexico-city", "ciudad de méxico")
LOCATION_LANDMARKS = ("zocalo tenochtitlan", "zócalo-tenochtitlan", "torre latinoamericana",
                      "paseo de la reforma", "angel de la independencia", "ángel de la independencia")
OTHER_PLACES = ("louisville", "kentucky", "zacatecas", "chihuahua", "san francisco",
                "california", "new york", "guadalajara", "monterrey", "puebla, mexico",
                "barranquilla", "bogota", "bogotá", "colombia", "medellin", "medellín",
                "palace of fine arts")


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def clean_html(value):
    parser = TextOnly()
    parser.feed(str(value or ""))
    return " ".join(html.unescape("".join(parser.parts)).split())


def fold(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def iso_date(value):
    match = re.match(r"^(\d{4})[-:/](\d{2})[-:/](\d{2})(?:[T\s]|$)", str(value or ""))
    if not match:
        return None
    try:
        return datetime(int(match[1]), int(match[2]), int(match[3]), tzinfo=timezone.utc)
    except ValueError:
        return None


def recent(time, now, days=MAX_AGE_DAYS):
    return bool(time and now - timedelta(days=days) <= time <= now + timedelta(days=1))


def licensed(meta):
    """Solo licencias Commons que permiten redistribución comercial con atribución."""
    label = clean_html(meta.get("LicenseShortName", {}).get("value", ""))
    url = clean_html(meta.get("LicenseUrl", {}).get("value", ""))
    normalized = re.sub(r"[\s_-]+", " ", label.upper()).strip()
    if normalized.startswith("CC0"):
        return "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"
    if re.fullmatch(r"CC BY(?: SA)? [234]\.0", normalized):
        if not url.startswith("https://creativecommons.org/licenses/"):
            return None
        if any(x in normalized for x in (" NC", " ND")):
            return None
        return label, url
    return None


def matches_place(title, category):
    """Filtro conservador: descarta sitios que no identifican explícitamente CDMX."""
    words = fold(title)
    if any(term in words for term in OTHER_PLACES):
        return False
    location = any(fold(x) in words for x in LOCATION_WORDS + LOCATION_LANDMARKS)
    if not location:
        return False
    if category == "CDMX":
        return True
    return any(fold(keyword) in words for keyword in KEYWORDS[category])


def candidate(page, category, now, verified_location=False):
    title = str(page.get("title", ""))
    if not title.startswith("File:") or not re.search(r"\.(jpe?g|png)$", title, re.I):
        return None
    filename = title[5:]
    if not verified_location and not matches_place(filename, category):
        return None
    # Un título que identifica un año anterior no se debe clasificar como
    # fotografía actual por el simple hecho de haber sido subida ahora.
    years = [int(y) for y in re.findall(r"(?<!\d)(20\d{2})(?!\d)", filename)]
    if years and max(years) < now.year:
        return None
    infos = page.get("imageinfo", [])
    if not infos:
        return None
    item = infos[0]
    uploaded = iso_date(item.get("timestamp", ""))
    # El upload es distinto a la toma: descartar fotografías explícitamente viejas.
    if not recent(uploaded, now, MAX_AGE_DAYS):
        return None
    metadata = item.get("extmetadata") or {}
    photo_date = iso_date(clean_html(metadata.get("DateTimeOriginal", {}).get("value", "")))
    if photo_date and not recent(photo_date, now, MAX_AGE_DAYS):
        return None
    license_info = licensed(metadata)
    if not license_info:
        return None
    author = clean_html(metadata.get("Artist", {}).get("value", ""))
    if not author or len(author) > 130:
        return None
    thumb = str(item.get("thumburl", ""))
    source = str(item.get("descriptionurl", ""))
    # Evitar servidores de terceros o enlaces arbitrarios.
    if not thumb.startswith(("https://upload.wikimedia.org/wikipedia/commons/",
                             "https://thumb.wikimedia.org/wikipedia/commons/thumb/")):
        return None
    if not source.startswith("https://commons.wikimedia.org/wiki/File:"):
        return None
    if int(item.get("width", 0) or 0) < 640 or int(item.get("height", 0) or 0) < 340:
        return None
    label, lic_url = license_info
    result = {
        "id": "reciente_" + hashlib.sha256(source.encode()).hexdigest()[:16],
        "reviewed_location": bool(verified_location),
        "category": category,
        "topic": clean_html(filename.rsplit(".", 1)[0].replace("_", " "))[:150],
        "file": filename,
        "url": thumb,
        "source": source,
        "author": author,
        "license": label,
        "licenseUrl": lic_url,
        "uploaded_at": uploaded.date().isoformat(),
        "captured_at": photo_date.date().isoformat() if photo_date else None,
    }
    return result


def request_photos(search):
    params = urllib.parse.urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": search,
        "gsrnamespace": "6",
        "gsrlimit": "30",
        "gsrsort": "create_timestamp_desc",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|timestamp|size",
        "iiurlwidth": "1100",
        "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|DateTimeOriginal",
        "format": "json",
        "formatversion": "2",
    })
    req = urllib.request.Request(ENDPOINT + "?" + params, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as response:
        payload = response.read(1_800_000)
    result = json.loads(payload)
    if "error" in result:
        raise ValueError("Wikimedia API: " + str(result["error"])[:150])
    return result.get("query", {}).get("pages", [])


def request_curated():
    """Obtiene los metadatos de archivos revisados y no los sustituye por copias locales."""
    titles = ["File:" + title for files in CURATED.values() for title in files]
    if not titles:
        return {}
    params = urllib.parse.urlencode({
        "action": "query", "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|timestamp|size",
        "iiurlwidth": "1100",
        "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|DateTimeOriginal",
        "format": "json", "formatversion": "2",
    })
    req = urllib.request.Request(ENDPOINT + "?" + params, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as response:
        result = json.loads(response.read(1_800_000))
    if "error" in result:
        raise ValueError("Wikimedia API: " + str(result["error"])[:150])
    return {page.get("title"): page for page in result.get("query", {}).get("pages", [])}


def load():
    try:
        obj = json.loads(DEST.read_text(encoding="utf-8"))
        if isinstance(obj, dict) and isinstance(obj.get("photos"), list):
            return obj
    except (OSError, ValueError):
        pass
    return {"photos": []}


def update(now=None, force=False):
    now = now or datetime.now(timezone.utc)
    old = load()
    checked = iso_date(str(old.get("checked_at", "")))
    # Solo cambia a diario; el workflow de titulares puede continuar cada hora.
    if not force and checked and now - checked < timedelta(hours=CHECK_EVERY_HOURS):
        print("Fotografías: consulta diaria ya realizada.")
        return old

    seen = set()
    photos = []
    successful_requests = 0
    try:
        curated_pages = request_curated()
        successful_requests += 1
    except (OSError, ValueError, KeyError) as exc:
        print("Wikimedia (selección contrastada):", str(exc)[:120])
        curated_pages = {}
    for category, queries in QUERIES.items():
        count = 0
        for filename in CURATED.get(category, ()):
            page = curated_pages.get("File:" + filename)
            result = candidate(page, category, now, verified_location=True) if page else None
            if result and result["source"] not in seen:
                seen.add(result["source"])
                photos.append(result)
                count += 1
        for phrase in queries:
            if count >= MAX_PER_TOPIC:
                break
            try:
                pages = request_photos(phrase)
                successful_requests += 1
            except (OSError, ValueError, KeyError) as e:
                print("Wikimedia no disponible para", category, str(e)[:120])
                continue
            # La API con generator=search no garantiza orden en pages:
            # elegir primero los nuevos por timestamp, no por pageid.
            pages.sort(key=lambda page: page.get("imageinfo", [{}])[0].get("timestamp", "") if page.get("imageinfo") else "", reverse=True)
            for page in pages:
                result = candidate(page, category, now)
                if not result or result["source"] in seen:
                    continue
                seen.add(result["source"])
                photos.append(result)
                count += 1
                if count >= MAX_PER_TOPIC:
                    break

    if successful_requests == 0:
        print("Fotos: servicio no disponible; se conserva selección anterior.")
        return old
    # Conservar el catálogo del día anterior si una búsqueda parcial no ofrece
    # resultados suficientes; nunca atribuirle una fecha de toma inventada.
    for old_photo in old.get("photos", []):
        if not isinstance(old_photo, dict) or old_photo.get("category") not in QUERIES:
            continue
        cat = old_photo["category"]
        if len([x for x in photos if x["category"] == cat]) >= MAX_PER_TOPIC:
            continue
        if old_photo.get("source") in seen:
            continue
        if not recent(iso_date(old_photo.get("uploaded_at")), now):
            continue
        photos.append(old_photo)
        seen.add(old_photo["source"])

    result = {
        "version": 1,
        "checked_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "Wikimedia Commons · fotografías contextuales con licencia libre",
        "note": "Fecha de subida a Commons, NO fecha verificada de captura ni fotografía del suceso.",
        "photos": photos,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if not DEST.exists() or DEST.read_text(encoding="utf-8") != rendered:
        DEST.write_text(rendered, encoding="utf-8")
    print("Fotos: ", len(photos), "imágenes recientes verificadas en", successful_requests, "consultas.")
    return result


if __name__ == "__main__":
    update()
