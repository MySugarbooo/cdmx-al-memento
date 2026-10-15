"""Publica una selección automática de titulares sobre animales desde news.json.
No inventa reportajes ni atribuye fotografías a sucesos."""
import json
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "news.json"
DEST = ROOT / "animales" / "actualidad.html"
PATTERN = re.compile(r"\b(?:animal(?:es)?|perros?|gatos?|mascotas?|adopci[oó]n|rescate animal|maltrato animal|fauna|silvestre|aves?|ajolotes?|zool[oó]gic[oa]s?|veterinari[oa]s?|biodiversidad|esterilizaci[oó]n|refugio animal|especies)\b", re.I)

def build():
    try:
        payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    items = payload if isinstance(payload, list) else next(
        (payload[k] for k in ("articles", "news", "items") if isinstance(payload.get(k), list)), []
    )
    seen = set()
    cards = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=365)).date()
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", ""))
        date = str(item.get("date", ""))[:10]
        if not PATTERN.search(title) or not url.startswith("https://news.google.com/"):
            continue
        try:
            if datetime.fromisoformat(date).date() < cutoff:
                continue
        except ValueError:
            continue
        key = re.sub(r"\W+", "", title.casefold())
        if key in seen:
            continue
        seen.add(key)
        source = str(item.get("source", "Medio externo"))
        location = str(item.get("location", "Ubicación no confirmada"))
        cards.append(f'<article><small>{escape(date)} · {escape(source)} · {escape(location)}</small><h2>{escape(title)}</h2><p>Titular recopilado automáticamente. La información no se ha verificado de forma independiente; consulta la publicación original para conocer detalles, testimonios y posibles actualizaciones.</p><a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer nofollow">Leer noticia original ↗</a></article>')
        if len(cards) >= 40:
            break
    body = "\n".join(cards) if cards else "<p>No se encontraron titulares recientes de animales en las fuentes disponibles. Vuelve más tarde.</p>"
    doc = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Últimas noticias de animales | CDMX AL MEMENTO</title><meta name="description" content="Titulares recientes sobre animales y naturaleza en CDMX con fechas y fuentes originales."><style>body{{background:#101116;color:#faf4f8;font:16px/1.6 system-ui;margin:auto;max-width:950px;padding:24px}}a{{color:#ffa4ce}}article{{padding:20px;margin:20px 0;border:1px solid #6c4258;border-radius:16px;background:#22212a}}small{{color:#ffb6d6}}h1{{font-size:clamp(2rem,5vw,3rem)}}h2{{font-size:1.3rem}}.note{{background:#3b2733;padding:16px;border-radius:12px}}</style></head><body><nav><a href="/">Inicio</a> · <a href="/animales/">Animales y naturaleza</a></nav><h1>🐾 Últimas noticias de animales</h1><p class="note">Selección automatizada de titulares publicados por terceros. No es una investigación independiente ni se infiere la veracidad de una nota por aparecer aquí. La fecha es la que declara la fuente; la zona puede ser solo una mención en el titular.</p><main>{body}</main><footer>Actualizado por el recopilador del sitio. <a href="/politica-editorial.html">Política editorial</a>.</footer></body></html>'''
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(doc, encoding="utf-8")
    print("Titulares de animales:", len(cards))

if __name__ == "__main__":
    build()
