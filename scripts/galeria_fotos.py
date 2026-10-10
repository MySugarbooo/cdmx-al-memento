#!/usr/bin/env python3
"""Construye una fototeca real, variada y local de CDMX desde Wikimedia Commons.

Busca imágenes geolocalizadas/temáticas, verifica la licencia y el formato real,
las optimiza como JPEG y crea un catálogo de créditos para la interfaz.
Las fotografías son DE ARCHIVO: no se anuncian como fotos del suceso noticioso.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from io import BytesIO
from pathlib import Path
import json
import re
import time
import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "assets" / "fotos"
OUTPUT = FOLDER / "catalogo.json"
MANIFEST = ROOT / "assets" / "fotos-manifest.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = "CDMXAlMemento/2.0 (Mexico City cultural photo archive; sanchezaxochitl@gmail.com)"

# Cuotas por tipo de noticia; las imágenes extra siempre son fotografías reales.
TARGETS = {"CDMX": 23, "Metro": 15, "Seguridad": 17, "Cultura": 13,
           "Gobierno": 11, "Movilidad": 9}
SEARCHES = {
 "Metro": [
  "Metro Ciudad de México station",
  "Mexico City Metro train station",
  "Metro CDMX Línea metro",
  "Mexico City metro platform",
 ],
 "Movilidad": [
  "Mexico City Metrobús buses",
  "Paseo de la Reforma traffic Mexico",
  "Ciudad de México ciclovía autobuses",
  "Mexico City road traffic cars",
 ],
 "Seguridad": [
  "Ciudad de México policía patrulla",
  "Mexico City police cars",
  "Policía CDMX Ciudad de Mexico",
  "Secretaría de Seguridad Ciudadana CDMX",
  "Mexico City streets buildings",
 ],
 "Cultura": [
  "Palacio de Bellas Artes Ciudad de México",
  "Mexico City museum architecture",
  "Ciudad de México Coyoacán cultural",
  "Mexico City architecture landmarks",
 ],
 "Gobierno": [
  "Palacio Nacional Ciudad de México",
  "Ciudad de México alcaldía gobierno edificio",
  "Mexico City government building",
  "Ciudad de México Zócalo palacio",
 ],
 "CDMX": [
  "Mexico City cityscape streets",
  "Ciudad de México centro histórico",
  "Mexico City Reforma city",
  "Ciudad de México calles edificios",
  "Mexico City skyline",
  "Mexico City public parks",
 ],
}
FALLBACK_SEARCHES = [
 "Ciudad de México plaza calles",
 "Mexico City architecture urban",
 "México city Chapultepec",
 "Mexico City cityscape buildings",
 "Ciudad de México aerial view",
 "Mexico City neighborhoods",
 "Mexico City historic streets",
]
BLOCKED = re.compile(
 r"(?:\.svg|\.pdf|\.djvu|\.ogg|map[a-z]*[_ -]|escudo|logo|flag|bandera|"
 r"coat.of.arms|diagram|screenshot|illustration|ilustraci[oó]n|"
 r"pictogram|cartoon|croquis|poster|afiche|banner|drawing|"
 r"plano(?:[_ -]|$)|mapa(?:[_ -]|$))", re.I)
LICENSE_PAT = re.compile(
 r"^https?://creativecommons\.org/(?:licenses/(?:by|by-sa)/"
 r"(?:2\.0|2\.5|3\.0|4\.0)|publicdomain/(?:zero|mark)/1\.0)/?", re.I)


def text_clean(value: str) -> str:
    value = re.sub(r"<[^>]*>", " ", str(value or ""))
    value = unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:140]


def request_json(session, params):
    for attempt in range(4):
        try:
            response = session.get(API, params=params, timeout=45)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            if attempt == 3:
                print("No se pudo consultar Wikimedia:", str(exc)[:150])
                return {}
            time.sleep(3 + attempt * 3)
    return {}


def discover(session, query: str, category: str):
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": 50,
        "prop": "imageinfo", "iiprop": "url|mime|size|sha1|extmetadata",
        "iiurlwidth": 820, "format": "json", "formatversion": 2
    }
    data = request_json(session, params)
    results = []
    for page in data.get("query", {}).get("pages", []):
        name = page.get("title", "").removeprefix("File:")
        if not re.search(r"\.(?:jpe?g|png|webp)$", name, re.I) or BLOCKED.search(name):
            continue
        info = next(iter(page.get("imageinfo", [])), {})
        mime = info.get("mime", "")
        if mime not in ("image/jpeg", "image/png", "image/webp"):
            continue
        if info.get("size", 0) > 32_000_000:
            continue
        if info.get("width", 0) < 550 or info.get("height", 0) < 350:
            continue
        ratio = info["width"] / info["height"]
        if not .8 <= ratio <= 3.3:
            continue
        meta = info.get("extmetadata", {})
        licurl = meta.get("LicenseUrl", {}).get("value", "")
        if not LICENSE_PAT.match(licurl):
            continue
        lic = text_clean(meta.get("LicenseShortName", {}).get("value", ""))
        if not lic or len(lic) > 45:
            continue
        author = text_clean(meta.get("Artist", {}).get("value", ""))
        if len(author) < 3 or len(author) > 125:
            author = text_clean(meta.get("Credit", {}).get("value", "")) or "Wikimedia Commons"
        results.append({
            "file": name,
            "source": "https://commons.wikimedia.org/wiki/File:" + requests.utils.quote(name.replace(" ", "_"), safe=""),
            "author": author, "license": lic, "licenseUrl": licurl,
            "topic": text_clean(name.rsplit(".", 1)[0].replace("_", " "))[:110],
            "category": category,
            "fingerprint": info.get("sha1") or name.casefold(),
            "thumb": info.get("thumburl") or info.get("url"),
            "original": info.get("url"),
        })
    print(f"Búsqueda {category!r} / {query!r}: {len(results)} fotografías con licencia verificable")
    return results


def download(candidate):
    # Descargar como imagen y validar realmente, nunca guardar páginas de error.
    links = [candidate["thumb"], candidate["original"]]
    for url in dict.fromkeys(filter(None, links)):
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=36,
                    headers={"User-Agent": UA, "Accept": "image/jpeg,image/webp,image/png,image/*"})
                response.raise_for_status()
                if len(response.content) < 2500 or len(response.content) > 33_000_000:
                    break
                with Image.open(BytesIO(response.content)) as raw:
                    if raw.width < 550 or raw.height < 350:
                        break
                    image = ImageOps.exif_transpose(raw)
                    image.thumbnail((850, 620), Image.Resampling.LANCZOS)
                    out = BytesIO()
                    image.convert("RGB").save(out, "JPEG", quality=76,
                                              optimize=True, progressive=True)
                payload = out.getvalue()
                if len(payload) < 3500:
                    break
                return candidate, payload
            except (requests.RequestException, OSError, ValueError):
                if attempt == 0:
                    time.sleep(1)
    return candidate, None


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    curated = json.loads(MANIFEST.read_text(encoding="utf-8"))["photos"]
    curated_by_cat = {}
    for p in curated:
        if (FOLDER / (p["id"] + ".jpg")).exists():
            curated_by_cat[p["category"]] = curated_by_cat.get(p["category"], 0) + 1

    known = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    entries = [p for p in known.get("photos", [])
               if re.fullmatch(r"archivo_[a-z0-9_]+", p.get("id", ""))
               and (FOLDER / (p["id"] + ".jpg")).exists()]
    all_known_files = {p["file"].casefold() for p in curated + entries}
    all_fingerprints = {p.get("fingerprint", p["file"].casefold()) for p in entries}
    for p in curated:
        all_fingerprints.add(p["file"].casefold())
    by_cat = {cat: curated_by_cat.get(cat, 0) + sum(p["category"] == cat for p in entries)
              for cat in TARGETS}
    counters = {cat: sum(p["category"] == cat for p in entries) for cat in TARGETS}
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/json"})

    def accept_photos(candidates, cat, needed):
        if needed <= 0:
            return 0
        fresh = []
        for p in candidates:
            fingerprint = p["fingerprint"]
            if p["file"].casefold() in all_known_files or fingerprint in all_fingerprints:
                continue
            all_known_files.add(p["file"].casefold())
            all_fingerprints.add(fingerprint)
            fresh.append(p)
        if not fresh:
            return 0
        chosen = fresh[:needed + 8]
        saved = 0
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(download, p) for p in chosen]
            for future in as_completed(futures):
                candidate, content = future.result()
                if content is None or saved >= needed:
                    continue
                counters[cat] += 1
                file_id = "archivo_" + cat.lower() + "_" + f"{counters[cat]:03d}"
                filename = FOLDER / (file_id + ".jpg")
                # Si un fallo de disco ocurre, no registrar un archivo inexistente.
                try:
                    filename.write_bytes(content)
                except OSError:
                    continue
                entry = {
                    k: candidate[k] for k in
                    ("file", "source", "author", "license", "licenseUrl",
                     "topic", "category", "fingerprint")
                }
                entry["id"] = file_id
                entries.append(entry)
                saved += 1
        by_cat[cat] += saved
        print(f"Descargadas: {cat}: +{saved} / {by_cat[cat]} de {TARGETS[cat]}")
        return saved

    for cat, target in TARGETS.items():
        for query in SEARCHES[cat]:
            if by_cat[cat] >= target:
                break
            candidates = discover(session, query, cat)
            accept_photos(candidates, cat, target - by_cat[cat])

    total = len(curated) + len(entries)
    if total < 70:
        print(f"Fototeca de {total} imágenes; completando con fotografías variadas de la capital.")
        for query in FALLBACK_SEARCHES:
            if total >= 75:
                break
            candidates = discover(session, query, "CDMX")
            accept_photos(candidates, "CDMX", min(12, 77 - total))
            total = len(curated) + len(entries)

    entries.sort(key=lambda p: p["id"])
    catalog = {"version": 1, "description": "Fotografías reales de archivo de CDMX, con autores y licencias",
               "photos": entries}
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {cat: sum(p["category"] == cat for p in entries) for cat in TARGETS}
    print("Fototeca total:", len(curated)+len(entries), "Curadas:", len(curated),
          "Nuevas:", len(entries), "Distribución nuevas:", counts)
    if len(curated) + len(entries) < 60:
        raise SystemExit("Menos de 60 fotos diferentes; no publicar galería incompleta.")

if __name__ == "__main__":
    main()
