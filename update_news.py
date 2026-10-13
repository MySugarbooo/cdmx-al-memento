"""Actualizador de noticias CDMX AL MEMENTO.

Recopila titulares de RSS, los ordena por fecha de publicación verificable,
conserva copias de índices mensuales durante 365 días y los elimina al vencer.
No atribuye una alcaldía si no está mencionada de manera inequívoca en el título.
No descarga ni reproduce el cuerpo protegido de los artículos.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "news.json"
ARCHIVE_DIR = ROOT / "archivo"
BOROUGH_DIR = ROOT / "alcaldias"
REPORT_DIR = ROOT / "reportes"
REPORTS = ROOT / "reports.json"
MX = ZoneInfo("America/Mexico_City")
SITE = "https://cdmx-al-memento.pages.dev"
MAIL = "sanchezaxochitl@gmail.com"
RETENTION_DAYS = 365

BOROUGHS = (
    "La Magdalena Contreras", "Álvaro Obregón", "Azcapotzalco",
    "Benito Juárez", "Coyoacán", "Cuajimalpa de Morelos",
    "Cuauhtémoc", "Gustavo A. Madero", "Iztacalco", "Iztapalapa",
    "Miguel Hidalgo", "Milpa Alta", "Tláhuac", "Tlalpan",
    "Venustiano Carranza", "Xochimilco",
)
GENERAL_FEEDS = {
    "Metro": "Metro CDMX",
    "Movilidad": "tráfico cierres viales Ciudad de México",
    "Seguridad": "seguridad Ciudad de México",
    "Cultura": "eventos culturales Ciudad de México",
    "Gobierno": "gobierno Ciudad de México",
    "CDMX": "noticias Ciudad de México",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CDMXAlMemento/2.0; news aggregator)"}
SOCIAL_SOURCES = {
    "facebook", "instagram", "tiktok", "youtube", "twitter", "x.com", "threads",
    "reddit", "pinterest", "whatsapp", "telegram", "linkedin", "kwai",
}
JUNK = re.compile(r"https?://|www\.|\b(?:bit\.ly|tinyurl\.com|mile\.io|t\.co)/", re.I)
SPACES = re.compile(r"\s+")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
# Texto mencionado en un titular: no equivale a la ubicación verificada del incidente.
ALIASES = {
    "La Magdalena Contreras": ("la magdalena contreras", "magdalena contreras"),
    "Álvaro Obregón": ("alvaro obregon",),
    "Azcapotzalco": ("azcapotzalco",),
    "Benito Juárez": ("benito juarez",),
    "Coyoacán": ("coyoacan",),
    "Cuajimalpa de Morelos": ("cuajimalpa de morelos", "cuajimalpa"),
    "Cuauhtémoc": ("cuauhtemoc",),
    "Gustavo A. Madero": ("gustavo a madero", "gustavo a. madero"),
    "Iztacalco": ("iztacalco",),
    "Iztapalapa": ("iztapalapa",),
    "Miguel Hidalgo": ("miguel hidalgo",),
    "Milpa Alta": ("milpa alta",),
    "Tláhuac": ("tlahuac",),
    "Tlalpan": ("tlalpan",),
    "Venustiano Carranza": ("venustiano carranza",),
    "Xochimilco": ("xochimilco",),
}


def clean(value):
    value = re.sub(r"<[^>]*>", "", html.unescape(str(value or "")))
    return SPACES.sub(" ", value).strip()


def fold(value):
    value = unicodedata.normalize("NFKD", clean(value).casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def identify_location(title):
    words = " " + fold(title) + " "
    found = [
        borough for borough, aliases in ALIASES.items()
        if any(" " + fold(alias) + " " in words for alias in aliases)
    ]
    # Si nombra varias demarcaciones no elegir una como lugar de los hechos.
    if len(found) == 1:
        return found[0], found[0] + " (mencionada en el titular)"
    if any(" " + x + " " in words for x in (
        "cdmx", "ciudad de mexico", "capital del pais"
    )):
        return "", "Ciudad de México (sin alcaldía identificada)"
    return "", "Ubicación no indicada por el titular"


def allowed(source):
    name = clean(source).lower()
    return bool(name) and not any(
        s == name or s in name.split() for s in SOCIAL_SOURCES
    ) and not any(
        x in name for x in ("facebook.com", "instagram.com", "youtube.com", "tiktok.com", "x.com")
    )


def normalize_title(title, source):
    title = clean(title)
    if source and title.lower().endswith(" - " + source.lower()):
        title = title[: -(len(source) + 3)].strip()
    return title


def valid_link(url):
    parts = urllib.parse.urlparse(str(url))
    return parts.scheme == "https" and parts.hostname == "news.google.com"


def published_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError, TypeError):
        return None


def standardize(article):
    """Relee noticias antiguas sin inventar la hora que no venía en el RSS."""
    if not isinstance(article, dict):
        return None
    title = clean(article.get("title"))[:320]
    url = article.get("url")
    source = clean(article.get("source"))[:110]
    date = str(article.get("date", ""))
    published = published_datetime(article.get("published_at"))
    if published:
        date = published.astimezone(MX).date().isoformat()
    if not title or not valid_link(url) or not DAY_RE.fullmatch(date):
        return None
    try:
        datetime.fromisoformat(date)
    except ValueError:
        return None
    borough, location = identify_location(title)
    category = article.get("category") if article.get("category") in GENERAL_FEEDS else "CDMX"
    return {
        "title": title,
        "description": "Consulta los detalles y las actualizaciones en el medio original.",
        "url": url,
        "source": source or "Medio externo",
        "date": date,
        "published_at": published.isoformat(timespec="seconds").replace("+00:00", "Z") if published else None,
        "category": category,
        "borough": borough,
        "location": location,
    }


def article_key(article):
    return fold(article.get("title", ""))[:250] + "|" + str(article.get("date", ""))


def gather():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=3)
    seen = {}
    successful = 0

    def read_feed(search, category, expect_borough=None, max_items=24):
        nonlocal successful
        rss = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": search + " when:3d", "hl": "es-419", "gl": "MX", "ceid": "MX:es-419"
        })
        try:
            req = urllib.request.Request(rss, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                root = ET.fromstring(resp.read(2_000_000))
            successful += 1
        except (OSError, ET.ParseError, ValueError) as exc:
            print("RSS temporalmente no disponible:", search, str(exc)[:100])
            return
        for item in root.findall(".//item")[:max_items]:
            source = clean(item.findtext("source"))
            title = normalize_title(item.findtext("title"), source)
            link = (item.findtext("link") or "").strip()
            if not allowed(source) or not title or len(title) < 20 or JUNK.search(title) or not valid_link(link):
                continue
            try:
                stamp = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc)
            except (ValueError, TypeError, OverflowError):
                continue
            if not cutoff <= stamp <= now + timedelta(minutes=15):
                continue
            borough, _ = identify_location(title)
            if expect_borough and borough != expect_borough:
                continue
            article = standardize({
                "title": title, "url": link, "source": source,
                "published_at": stamp.isoformat(timespec="seconds"),
                "category": category,
            })
            if not article:
                continue
            key = article_key(article)
            if key not in seen:
                seen[key] = article

    for category, query in GENERAL_FEEDS.items():
        read_feed(query, category, max_items=30)
    # Búsquedas puntuales para dar cobertura a las 16 alcaldías.
    # Solo se etiqueta la alcaldía si aparece explícitamente en el titular.
    for borough in BOROUGHS:
        query = '"' + borough.replace("La Magdalena Contreras", "Magdalena Contreras") + '" CDMX'
        read_feed(query, "CDMX", expect_borough=borough, max_items=14)
    items = sorted(seen.values(), key=sort_key, reverse=True)
    print("Feeds recibidos:", successful, "; nuevos titulares distintos:", len(items))
    return items


def sort_key(item):
    published = published_datetime(item.get("published_at"))
    if published:
        return published
    try:
        return datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc)
    except (ValueError, KeyError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def still_valid(item, cutoff):
    return sort_key(item) >= cutoff


def load_json(path, fallback):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else fallback
    except (OSError, ValueError):
        return fallback


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def consolidate_archive(new_items, cutoff, updated):
    """Deduplica el histórico y elimina incluso archivos mensuales ya vencidos."""
    ARCHIVE_DIR.mkdir(exist_ok=True)
    BOROUGH_DIR.mkdir(exist_ok=True)
    existing = {}
    for path in ARCHIVE_DIR.glob("????-??.json"):
        if not MONTH_RE.fullmatch(path.stem):
            continue
        month = load_json(path, {"articles": []})
        for raw in month.get("articles", []):
            item = standardize(raw)
            if item and still_valid(item, cutoff):
                existing[article_key(item)] = item
    # Migrar el índice de la portada ANTES de sobrescribirlo.
    prior = load_json(DEST, {"articles": []})
    for raw in prior.get("articles", []):
        item = standardize(raw)
        if item and still_valid(item, cutoff):
            existing.setdefault(article_key(item), item)
    for item in new_items:
        if still_valid(item, cutoff):
            key = article_key(item)
            old = existing.get(key)
            # Conservar el timestamp real cuando una versión antigua solo tenía fecha.
            if not old or (item.get("published_at") and not old.get("published_at")):
                existing[key] = item

    by_month = defaultdict(list)
    by_borough = defaultdict(list)
    for item in existing.values():
        by_month[item["date"][:7]].append(item)
        if item["borough"]:
            by_borough[item["borough"]].append(item)
    for filename in ARCHIVE_DIR.glob("????-??.json"):
        if filename.stem not in by_month:
            filename.unlink()
    months = []
    for month in sorted(by_month, reverse=True):
        items = sorted(by_month[month], key=sort_key, reverse=True)
        url = "/archivo/" + month + ".json"
        target = ARCHIVE_DIR / (month + ".json")
        previous = load_json(target, {})
        # Los meses anteriores no se reescriben si las noticias no cambiaron.
        stamp = previous.get("updated", updated) if previous.get("articles") == items else updated
        write_json(target, {"month": month, "updated": stamp, "articles": items})
        months.append({"month": month, "url": url, "count": len(items)})
    write_json(ARCHIVE_DIR / "meses.json", {
        "updated": updated, "retention_days": RETENTION_DAYS, "months": months
    })
    borough_output = []
    for name in BOROUGHS:
        items = sorted(by_borough[name], key=sort_key, reverse=True)
        borough_output.append({
            "name": name, "count": len(items), "articles": items[:24]
        })
    write_json(BOROUGH_DIR / "noticias.json", {
        "updated": updated, "boroughs": borough_output
    })
    print("Archivo:", sum(len(x) for x in by_month.values()),
          "titulares conservados en", len(months), "meses")
    return months


def update():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RETENTION_DAYS)
    updated = now.strftime("%Y-%m-%d %H:%M UTC")
    items = gather()
    # Fallback únicamente si siguen siendo recientes; nunca mostrar noticias caducadas.
    if not items:
        old = load_json(DEST, {"articles": []})
        items = [
            item for raw in old.get("articles", [])
            if (item := standardize(raw)) and sort_key(item) >= now - timedelta(days=3)
        ]
        print("Utilizando solo noticias todavía recientes que ya estaban guardadas.")
    consolidate_archive(items, cutoff, updated)
    write_json(DEST, {"updated": updated, "articles": items[:60]})
    print("Portada: ", min(60, len(items)), "noticias con fecha, hora disponible y zona indicada")


def report_shell(title, body):
    from html import escape
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + escape(title) + ' | CDMX AL MEMENTO</title>'
        '<link rel="stylesheet" href="/styles.css"></head><body>'
        '<header><div class="wrap"><div class="top"><a class="logo" href="/">CDMX <span>AL MEMENTO</span></a></div>'
        '<nav><a href="/">Noticias</a><a href="/archivo/">Archivo mensual</a>'
        '<a href="/alcaldias/">Alcaldías</a></nav></div></header>'
        '<main class="wrap prose">' + body + '</main><footer><div class="wrap">'
        '<a href="/politica-editorial.html">Política editorial</a> · '
        '<a href="mailto:' + MAIL + '">' + MAIL + '</a></div></footer></body></html>'
    )


def generate_report():
    from html import escape
    current = load_json(DEST, {"articles": []})
    rows = current.get("articles", [])
    entries = load_json(REPORTS, {"reports": []}).get("reports", [])
    today = datetime.now(MX).date()
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).astimezone(MX).date()

    REPORT_DIR.mkdir(exist_ok=True)
    for file in REPORT_DIR.glob("????-??-??.html"):
        try:
            day = datetime.strptime(file.stem, "%Y-%m-%d").date()
            if day < cutoff_date:
                file.unlink()
        except ValueError:
            continue
    entries = [
        item for item in entries if isinstance(item, dict)
        and DAY_RE.fullmatch(str(item.get("date", "")))
        and datetime.strptime(item["date"], "%Y-%m-%d").date() >= cutoff_date
        and (REPORT_DIR / (item["date"] + ".html")).exists()
    ]
    local_day = today.isoformat()
    sources = {x.get("source") for x in rows if isinstance(x, dict)}
    if len(rows) >= 8 and len(sources) >= 3:
        parts = [
            '<p class="eyebrow">Reporte de seguimiento automático · ' + local_day + '</p>',
            '<h1>Titulares recientes de Ciudad de México</h1>',
            '<p>Resumen automatizado con enlaces a medios externos y fecha de publicación.</p>',
            '<div class="notice">No constituye investigación ni verificación independiente. '
            'La alcaldía se infiere exclusivamente cuando el titular la menciona.</div>',
        ]
        for category in GENERAL_FEEDS:
            group = [x for x in rows if x.get("category") == category][:9]
            if not group:
                continue
            parts.append('<h2>' + escape(category) + '</h2><ol>')
            for article in group:
                url = article.get("url")
                if not valid_link(url):
                    continue
                pub = published_datetime(article.get("published_at"))
                when = pub.astimezone(MX).strftime("%d/%m/%Y %H:%M") if pub else article.get("date", "Fecha no indicada")
                loc = article.get("location", "Ubicación no indicada")
                parts.append(
                    '<li><a target="_blank" rel="noopener noreferrer nofollow" href="' +
                    escape(url, quote=True) + '">' + escape(article.get("title", "")) +
                    '</a> — ' + escape(article.get("source", "")) +
                    ' · Publicada: ' + escape(when) +
                    ' · Zona: ' + escape(loc) + '</li>'
                )
            parts.append("</ol>")
        parts.append('<p>Solicita correcciones escribiendo a <a href="mailto:' + MAIL + '">' + MAIL + '</a>.</p>')
        fname = local_day + ".html"
        (REPORT_DIR / fname).write_text(
            report_shell("Reporte " + local_day, "\n".join(parts)), encoding="utf-8"
        )
        entries = [item for item in entries if item["date"] != local_day]
        entries.append({
            "date": local_day, "url": "/reportes/" + fname, "count": len(rows)
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    write_json(REPORTS, {"updated": current.get("updated", ""), "reports": entries})
    listing = ('<h1>Reportes automáticos de CDMX</h1>'
               '<p>Recopilaciones con fuentes externas; los reportes antiguos se retiran '
               'después de 365 días. <a href="/archivo/">Consultar archivo mensual de noticias</a>.</p><ul>')
    for item in entries:
        listing += '<li><a href="' + escape(item["url"], quote=True) + '">Reporte ' + \
            escape(item["date"]) + '</a> · ' + str(int(item.get("count", 0))) + ' titulares</li>'
    listing += '</ul>'
    (REPORT_DIR / "index.html").write_text(
        report_shell("Reportes diarios", listing), encoding="utf-8"
    )

    urls = [
        "", "contacto.html", "privacidad.html", "sobre-nosotros.html",
        "politica-editorial.html", "creditos-fotograficos.html",
        "guias/", "reportes/", "archivo/", "alcaldias/", "mapa/",
        "cerca/", "movilidad/", "avisos/",
    ]
    urls += [
        "guias/" + name for name in (
            "estado-del-metro.html", "alertas-por-lluvia.html",
            "cierres-viales.html", "tramites-cdmx.html"
        )
    ]
    urls += ["reportes/" + p.name for p in sorted(REPORT_DIR.glob("????-??-??.html"))]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
        "".join('<url><loc>' + SITE + '/' + escape(p) + '</loc></url>' for p in urls) +
        '</urlset>\n', encoding="utf-8"
    )
    print("Reportes vigentes:", len(entries))


if __name__ == "__main__":
    update()
    generate_report()
