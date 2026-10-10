#!/usr/bin/env python3
"""Descarga imágenes REALES de Wikimedia Commons y comprueba su formato antes de publicarlas.

Solo corre en GitHub Actions o por ejecución manual. Las imágenes alojadas localmente
evitan URLs externos erróneos y permiten un sitio rápido y estable.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
import json
import random
import time
import requests
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "assets" / "fotos"
MANIFEST = ROOT / "assets" / "fotos-manifest.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = "CDMXAlMemento/1.0 (photography verification; contact: sanchezaxochitl@gmail.com)"
REQUIRED = {"reforma","metro","movilidad","seguridad","cultura","gobierno"}
session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept": "application/json, image/jpeg, image/*;q=0.8"})

def download_photo(photo: dict) -> bytes:
    title = "File:" + photo["file"]
    params = {"action":"query","prop":"imageinfo","titles":title,
              "iiprop":"url","iiurlwidth":1050,"format":"json","formatversion":2}
    errors = []
    for attempt in range(4):
        try:
            response = session.get(API,params=params,timeout=35)
            response.raise_for_status()
            pages = response.json().get("query",{}).get("pages",[])
            if not pages or pages[0].get("missing"):
                raise RuntimeError("Archivo no encontrado en Wikimedia Commons: " + title)
            imageinfo = pages[0].get("imageinfo",[{}])[0]
            if not imageinfo.get("url"):
                raise RuntimeError("API no devolvió URL para " + title)
            candidates = [imageinfo.get("thumburl"),imageinfo.get("url")]
            # Special:Redirect/file utiliza el nombre canónico, sin hashes manuales.
            candidates.append("https://commons.wikimedia.org/wiki/Special:Redirect/file/"+quote(photo["file"])+"?width=1050")
            for url in filter(None,candidates):
                try:
                    image_response = session.get(url,timeout=50,headers={"Accept":"image/avif,image/webp,image/jpeg,image/*"})
                    image_response.raise_for_status()
                    data = image_response.content
                    if len(data) < 3000:
                        raise ValueError("respuesta vacía o no válida")
                    with Image.open(BytesIO(data)) as check:
                        check.verify()
                    return data
                except Exception as err:
                    errors.append(str(err)[:160])
            raise RuntimeError("No se pudo descargar foto válida desde las URLs de la API.")
        except Exception as err:
            errors.append(str(err)[:170])
            if attempt<3:time.sleep(3+attempt*2)
    raise RuntimeError(photo["id"]+" · "+"; ".join(errors[-5:]))

def main():
    photos=json.loads(MANIFEST.read_text(encoding="utf-8"))["photos"]
    DEST.mkdir(parents=True,exist_ok=True)
    completed,failed=[],[]
    for photo in photos:
        output=DEST/(photo["id"]+".jpg")
        try:
            content=download_photo(photo)
            with Image.open(BytesIO(content)) as raw:
                image=ImageOps.exif_transpose(raw).convert("RGB")
                image.thumbnail((1100,850),Image.Resampling.LANCZOS)
                # Guardamos fotos comprimidas, nunca la página de error HTML.
                image.save(output,"JPEG",quality=78,optimize=True,progressive=True)
            with Image.open(output) as valid:
                valid.verify()
            completed.append(photo["id"])
            print(f"✅ {photo['id']}: {output.stat().st_size // 1024} KB")
        except Exception as exc:
            failed.append(photo["id"])
            print(f"❌ {photo['id']}: {exc}")
    print("Fotos descargadas:",len(completed),"de",len(photos))
    missing=sorted(REQUIRED-set(completed))
    if missing:
        raise SystemExit("Error: faltan fotografías necesarias: "+", ".join(missing))
    if failed:
        print("Aviso: faltan fotos secundarias, revisar antes de publicar:",", ".join(failed))
    else:
        print("Todas las fotografías están verificadas.")

if __name__ == "__main__":
    main()
