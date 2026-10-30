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

def esc(value):
    return html.escape(str(value or ""), quote=True)

def article_id(item):
    match = re.fullmatch(r"/noticias/\?id=([a-f0-9]{20})&mes=\d{4}-\d{2}", item.get("local_url", ""))
    return match.group(1) if match else None

def render(item, ident):
    title = esc(item["title"])
    brief = item.get("brief") or {}
    lead = esc(brief.get("lead") or item.get("description") or "")
    context = esc(brief.get("context") or "Consulta las fuentes y los avisos oficiales.")
    pending = esc(brief.get("pending") or "Los detalles requieren confirmación independiente.")
    method = esc(brief.get("method") or "Resumen basado en información atribuida a la fuente.")
    source = esc(item.get("source") or "Fuente identificada")
    date = esc(item.get("date") or "")
    url = BASE + "/articulos/" + ident + "/"
    original = item.get("url") or ""
    source_link = ""
    if urlparse(original).scheme == "https" and urlparse(original).hostname in ("news.google.com", "commons.wikimedia.org"):
        source_link = '<p><a href="' + esc(original) + '" rel="nofollow noopener noreferrer">Consultar fuente original</a></p>'
    structured = json.dumps({"@context":"https://schema.org","@type":"NewsArticle","headline":item["title"],"datePublished":item.get("published_at") or item.get("date"),"author":{"@type":"Organization","name":"CDMX AL MEMENTO"},"publisher":{"@type":"Organization","name":"CDMX AL MEMENTO"},"mainEntityOfPage":url},ensure_ascii=False).replace("<","\\u003c")
    return f"""<!doctype html><html lang="es-MX"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | CDMX AL MEMENTO</title><meta name="description" content="{esc(brief.get('lead') or item.get('description') or '')[:155]}">
<link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:title" content="{title}">
<meta property="og:description" content="{lead[:155]}"><meta property="og:url" content="{url}">
<link rel="stylesheet" href="/styles.css"><script type="application/ld+json">{structured}</script></head>
<body><header><div class="wrap"><a href="/">CDMX AL MEMENTO</a> · <a href="/noticias/">Noticias</a></div></header>
<main class="wrap" id="contenido"><article><p>CDMX · {date} · Fuente: {source}</p><h1>{title}</h1>
<p>{lead}</p><h2>Por qué importa</h2><p>{context}</p><h2>Qué falta por confirmar</h2><p>{pending}</p>
<h2>Fuentes y método</h2><p>{method}</p><p>Esta síntesis no equivale a una verificación independiente de los hechos.</p>
{source_link}<p><a href="{esc(item['local_url'])}">Ver noticia y comentarios en el periódico</a></p></article></main>
<footer><div class="wrap"><a href="/">Portada</a> · <a href="/politica-editorial.html">Política editorial</a></div></footer></body></html>"""

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    articles = data.get("articles") or []
    OUT.mkdir(exist_ok=True)
    urls = []
    for item in articles:
        ident = article_id(item)
        if not ident or not item.get("title"):
            continue
        dest = OUT / ident
        dest.mkdir(exist_ok=True)
        (dest / "index.html").write_text(render(item, ident), encoding="utf-8")
        urls.append(BASE + "/articulos/" + ident + "/")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join("  <url><loc>" + esc(u) + "</loc></url>\n" for u in sorted(set(urls)))
    SITEMAP.write_text(xml + "</urlset>\n", encoding="utf-8")
    print(f"Generated {len(urls)} article pages and sitemap-articulos.xml")

if __name__ == "__main__":
    main()
