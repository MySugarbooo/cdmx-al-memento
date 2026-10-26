"""Recuperación excepcional de titulares del 16 al 24 de octubre de 2026.

Preserva fecha y fuente originales; publica reportes retrospectivos separados
de la portada actual. No atribuye hechos adicionales ni duplica titulares.
"""
from __future__ import annotations

import concurrent.futures
import json
import re
import sys
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape

# Ejecutado como script desde scripts/: incluir la raíz del repositorio.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import update_news as news

START = date(2026, 10, 16)
END = date(2026, 10, 24)
STATE = news.ARCHIVE_DIR / "recuperacion-octubre-2026.json"
WINDOWS = ((date(2026, 10, 16), date(2026, 10, 19)),
           (date(2026, 10, 19), date(2026, 10, 22)),
           (date(2026, 10, 22), date(2026, 10, 25)))


def rss_task(args):
    start, end, query, category, borough = args
    params = urllib.parse.urlencode({
        "q": f"{query} after:{(start-timedelta(days=1)).isoformat()} before:{end.isoformat()}",
        "hl": "es-419", "gl": "MX", "ceid": "MX:es-419",
    })
    url = "https://news.google.com/rss/search?" + params
    req = urllib.request.Request(url, headers=news.HEADERS)
    found = []
    try:
        with urllib.request.urlopen(req, timeout=14) as stream:
            root = ET.fromstring(stream.read(2_000_000))
    except (OSError, ET.ParseError, ValueError) as exc:
        print("Consulta RSS no disponible:", query, str(exc)[:100])
        return False, found
    for node in root.findall(".//item")[:80]:
        source = news.clean(node.findtext("source"))
        title = news.normalize_title(node.findtext("title"), source)
        link = (node.findtext("link") or "").strip()
        if (not news.allowed(source) or len(title) < 20
                or news.JUNK.search(title) or not news.valid_link(link)):
            continue
        try:
            published = parsedate_to_datetime(node.findtext("pubDate")).astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            continue
        local_day = published.astimezone(news.MX).date()
        if not START <= local_day <= END:
            continue
        if borough and news.identify_location(title)[0] != borough:
            continue
        article = news.standardize({
            "title": title, "url": link, "source": source,
            "published_at": published.isoformat(timespec="seconds"),
            "category": category,
        })
        if article:
            found.append(article)
    return True, found


def build_tasks():
    tasks = []
    for start, end in WINDOWS:
        for category, query in news.GENERAL_FEEDS.items():
            tasks.append((start, end, query, category, None))
        for borough in news.BOROUGHS:
            term = borough.replace("La Magdalena Contreras", "Magdalena Contreras")
            tasks.append((start, end, f'"{term}" CDMX', "CDMX", borough))
    return tasks


def recover():
    if STATE.exists():
        print("Recuperación de octubre ya registrada; se conservan los reportes publicados.")
        return
    tasks = build_tasks()
    new_items = {}
    successful = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for ok, articles in pool.map(rss_task, tasks):
            if ok:
                successful += 1
            for article in articles:
                new_items.setdefault(news.article_key(article), article)
    now = datetime.now(timezone.utc)
    stamped = now.strftime("%Y-%m-%d %H:%M UTC")
    print("Consultas RSS exitosas:", successful, "de", len(tasks))
    print("Titulares históricos hallados:", len(new_items))
    if successful == 0:
        print("Sin acceso a fuentes RSS: se usarán solo titulares ya archivados.")

    # La consolidación conserva las noticias que ya estaban guardadas.
    news.consolidate_archive(list(new_items.values()),
                             now-timedelta(days=news.RETENTION_DAYS), stamped)
    archive = news.load_json(news.ARCHIVE_DIR / "2026-10.json", {"articles": []})
    by_date = defaultdict(list)
    for article in archive.get("articles", []):
        day = str(article.get("date", ""))
        if START.isoformat() <= day <= END.isoformat():
            by_date[day].append(article)
    reports = news.load_json(news.REPORTS, {"reports": []}).get("reports", [])
    counts = {}
    for day_offset in range((END-START).days + 1):
        day = (START + timedelta(days=day_offset)).isoformat()
        day_items = sorted(by_date[day], key=news.sort_key, reverse=True)
        counts[day] = len(day_items)
        if not day_items:
            continue
        parts = [
            '<p class="eyebrow">Recuperación histórica de noticias · ' + day + '</p>',
            '<h1>Noticias publicadas originalmente el ' + day + '</h1>',
            '<div class="notice">Recopilación reconstruida después de una falla técnica. '
            'Estas noticias NO son de hoy. Fechas y medios proceden de los metadatos RSS '
            'o del archivo conservado; no se han verificado los hechos de manera independiente. '
            'La alcaldía se indica solo cuando el titular la menciona.</div>',
            '<p><a href="/reportes/">Ver todos los reportes</a> · '
            '<a href="/archivo/">Consultar archivo mensual</a></p><ol>',
        ]
        for item in day_items[:100]:
            title = escape(str(item.get("title", "")))
            link = escape(item.get("local_url") or news.local_link(item), quote=True)
            source = escape(str(item.get("source", "Medio externo")))
            when = escape(str(item.get("published_at") or day))
            place = escape(str(item.get("location", "Ubicación no verificada")))
            parts.append(f'<li><a href="{link}">{title}</a> — {source} · {when} · {place}</li>')
        parts.append("</ol>")
        (news.REPORT_DIR / f"{day}.html").write_text(
            news.report_shell("Reporte " + day, "\n".join(parts)), encoding="utf-8")
        reports = [r for r in reports if r.get("date") != day]
        reports.append({"date": day, "url": f"/reportes/{day}.html", "count": len(day_items)})
    reports.sort(key=lambda r: str(r.get("date", "")), reverse=True)
    news.write_json(news.REPORTS, {"updated": stamped, "reports": reports})
    if any(counts.values()):
        news.write_json(STATE, {
            "periodo": [START.isoformat(), END.isoformat()],
            "recuperado_en": stamped,
            "consultas_exitosas": successful,
            "titulares_nuevos_encontrados": len(new_items),
            "titulares_por_dia_en_archivo": counts,
            "nota": "Publicación retrospectiva, no cobertura en directo.",
        })
    news.generate_report()
    print("Resumen de recuperación por fecha:", json.dumps(counts, ensure_ascii=False))
    if not any(counts.values()):
        raise RuntimeError("No se encontraron titulares verificables en el periodo; se intentará de nuevo.")


if __name__ == "__main__":
    recover()
