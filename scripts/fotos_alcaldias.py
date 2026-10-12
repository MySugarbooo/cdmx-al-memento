#!/usr/bin/env python3
"""Fotografías REPRESENTATIVAS, con ubicación cotejada y licencia libre verificada.

Los nombres de archivo en seleccion.json corresponden a páginas de Wikimedia Commons
y están seleccionados por hitos que se encuentran en las alcaldías señaladas.
Nunca sustituir por una fotografía de otra ubicación.
"""
from __future__ import annotations
import io
import json
import re
import time
from html import unescape
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets" / "alcaldias"
SELECT = BASE / "seleccion.json"
OUT = BASE / "fotos.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = "CDMXAlMemento/3.0 (alcaldias image credits; sanchezaxochitl@gmail.com)"
LICENSE = re.compile(
    r"^https?://creativecommons\.org/(?:licenses/(?:by|by-sa)/"
    r"(?:2\.0|2\.5|3\.0|4\.0)|publicdomain/(?:zero|mark)/1\.0)/?", re.I
)
session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept": "application/json"})


def cleaned(value):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", str(value or "")))).strip()[:130]


def fetch_photo(filename):
    for attempt in range(3):
        try:
            response = session.get(API, params={
                "action": "query", "titles": "File:" + filename, "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata", "iiurlwidth": 960,
                "format": "json", "formatversion": 2,
            }, timeout=45)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing"):
                raise ValueError("Commons no contiene el archivo")
            info = next(iter(pages[0].get("imageinfo", [])), {})
            if info.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
                raise ValueError("El archivo no es una foto compatible")
            if info.get("width", 0) < 550 or info.get("height", 0) < 320:
                raise ValueError("Resolución de foto insuficiente")
            if info.get("size", 0) > 35_000_000:
                raise ValueError("Imagen original demasiado grande")
            metadata = info.get("extmetadata", {})
            license_url = metadata.get("LicenseUrl", {}).get("value", "")
            if not LICENSE.match(license_url):
                raise ValueError("No consta una licencia CC BY / BY-SA / CC0 válida: " + str(license_url))
            author = cleaned(metadata.get("Artist", {}).get("value"))
            if not author:
                author = cleaned(metadata.get("Credit", {}).get("value")) or "Autor de Wikimedia Commons"
            for url in dict.fromkeys(filter(None, (info.get("thumburl"), info.get("url")))):
                try:
                    downloaded = session.get(url, timeout=45, headers={
                        "User-Agent": UA, "Accept": "image/jpeg,image/webp,image/png,image/*"})
                    downloaded.raise_for_status()
                    data = downloaded.content
                    if not 3000 < len(data) < 35_000_000:
                        continue
                    with Image.open(io.BytesIO(data)) as raw:
                        image = ImageOps.exif_transpose(raw)
                        if image.width < 500 or image.height < 300:
                            continue
                        image.thumbnail((960, 630), Image.Resampling.LANCZOS)
                        buff = io.BytesIO()
                        image.convert("RGB").save(
                            buff, "JPEG", quality=79, optimize=True, progressive=True
                        )
                    if len(buff.getvalue()) < 3000:
                        continue
                    return {
                        "file": filename,
                        "source": "https://commons.wikimedia.org/wiki/File:"
                                  + quote(filename.replace(" ", "_"), safe=""),
                        "author": author, "license": cleaned(
                            metadata.get("LicenseShortName", {}).get("value")
                        ),
                        "licenseUrl": license_url,
                    }, buff.getvalue()
                except (requests.RequestException, OSError, ValueError) as exc:
                    print("Fallo de descarga:", filename, str(exc)[:110])
            raise ValueError("Wikimedia no permitió descargar la fotografía")
        except (requests.RequestException, ValueError, OSError) as exc:
            if attempt == 2:
                print("No se pudo obtener", filename, ":", str(exc)[:160])
            else:
                time.sleep(2 + attempt * 3)
    return None, None


def main():
    selection = json.loads(SELECT.read_text(encoding="utf-8"))["boroughs"]
    BASE.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    existing = {item["name"]: item for item in previous.get("photos", [])}
    entries, missed = [], []
    for item in selection:
        dst = BASE / (item["slug"] + ".jpg")
        kept = existing.get(item["name"])
        if kept and dst.exists() and dst.stat().st_size > 4000:
            entries.append(kept)
            print("Ya disponible:", item["name"])
            continue
        for candidate in item["candidates"]:
            metadata, pixels = fetch_photo(candidate)
            if pixels:
                dst.write_bytes(pixels)
                entries.append({
                    "name": item["name"],
                    "slug": item["slug"],
                    "caption": item["caption"],
                    **metadata,
                })
                print("Guardada:", item["name"], "→", candidate,
                      f"({len(pixels) // 1024} KB)")
                break
        else:
            missed.append(item["name"])
    if missed:
        raise SystemExit(
            "Faltan fotos representativas, no publicar resultados incompletos: "
            + ", ".join(missed)
        )
    if len(entries) != 16 or len({e["source"] for e in entries}) != 16:
        raise SystemExit("El catálogo no contiene 16 fotografías diferentes.")
    OUT.write_text(json.dumps({
        "version": 1, "description": "Fotografías de archivo de lugares concretos de cada alcaldía",
        "photos": entries
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("16 fotografías verificadas con autor y licencia, tamaño total:",
          sum((BASE / (p["slug"] + ".jpg")).stat().st_size for p in entries)//1024,
          "KB")


if __name__ == "__main__":
    main()
