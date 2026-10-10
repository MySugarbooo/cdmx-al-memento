"""Publica hasta 60 titulares recientes de CDMX tomados de Google News RSS.

No copia el texto de los artículos ni genera reportajes. Filtra fuentes sociales,
spam y duplicados para mejorar la calidad del agregador.
"""
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = {
    "Metro": "Metro CDMX",
    "Movilidad": "tráfico cierres viales Ciudad de México",
    "Seguridad": "seguridad Ciudad de México",
    "Cultura": "eventos culturales Ciudad de México",
    "Gobierno": "gobierno Ciudad de México",
    "CDMX": "noticias Ciudad de México",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CDMXAlMemento/1.1; news aggregator)"}
SOCIAL_SOURCES = {
    "facebook", "instagram", "tiktok", "youtube", "twitter", "x.com", "threads",
    "reddit", "pinterest", "whatsapp", "telegram", "linkedin", "kwai",
}
# Filtra títulos que claramente son anuncios, enlaces de redes o publicaciones ajenas
# a un titular periodístico. No pretende evaluar la veracidad de una noticia.
JUNK = re.compile(r"https?://|www\.|\b(?:bit\.ly|tinyurl\.com|mile\.io|t\.co)/", re.I)
SPACES = re.compile(r"\s+")
DEST = Path(__file__).with_name("news.json")


def clean(value):
    value = re.sub(r"<[^>]*>", "", html.unescape(value or ""))
    return SPACES.sub(" ", value).strip()


def allowed(source):
    name = clean(source).lower()
    return bool(name) and not any(s == name or s in name.split() for s in SOCIAL_SOURCES) and not any(
        x in name for x in ("facebook.com", "instagram.com", "youtube.com", "tiktok.com", "x.com")
    )


def normalize_title(title, source):
    # Google News suele añadir « - nombre del medio». Quitar solo si coincide.
    title = clean(title)
    if source and title.lower().endswith(" - " + source.lower()):
        title = title[: -(len(source) + 3)].strip()
    return title


def collect():
    now = datetime.now(timezone.utc)
    earliest = now - timedelta(days=3)
    results = []
    seen = set()
    for category, query in FEEDS.items():
        rss = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": query + " when:3d", "hl": "es-419", "gl": "MX", "ceid": "MX:es-419"
        })
        try:
            request = urllib.request.Request(rss, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=20) as response:
                root = ET.fromstring(response.read())
        except (OSError, ET.ParseError, ValueError) as exc:
            print(f"No se pudo consultar {category}: {exc}")
            continue
        for item in root.findall(".//item")[:25]:
            source = clean(item.findtext("source"))
            title = normalize_title(item.findtext("title"), source)
            link = (item.findtext("link") or "").strip()
            if not allowed(source) or not title or JUNK.search(title) or len(title) < 20:
                continue
            if not link.startswith("https://news.google.com/"):
                # RSS de Google News enlaza al artículo a través de news.google.com.
                # Evitar enlaces inesperados insertados en el feed.
                continue
            try:
                published = parsedate_to_datetime(item.findtext("pubDate"))
                published = published.astimezone(timezone.utc)
            except (TypeError, ValueError, OverflowError):
                continue
            if not earliest <= published <= now + timedelta(minutes=15):
                continue
            key = re.sub(r"[^\wáéíóúñ]", "", title.lower())
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "title": title,
                "description": "Consulta la cobertura completa y las actualizaciones en el medio de origen.",
                "url": link,
                "source": source,
                "date": published.date().isoformat(),
                "category": category,
                "sort": published,
            })
    results.sort(key=lambda row: row["sort"], reverse=True)
    return results[:60]


def update():
    results = collect()
    if not results:
        raise RuntimeError("No se encontraron titulares válidos. Se conserva news.json sin modificar.")
    for row in results:
        row.pop("sort")
    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "articles": results,
    }
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardadas {len(results)} noticias recientes de fuentes no sociales")


if __name__ == "__main__":
    update()
