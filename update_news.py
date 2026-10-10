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



REPORTS = Path(__file__).with_name("reports.json")
REPORT_DIR = Path(__file__).with_name("reportes")
MAIL = "sanchezaxochitl@gmail.com"
SITE = "https://cdmx-al-memento.pages.dev"

def report_shell(title, body):
    from html import escape
    return (
      '<!doctype html><html lang="es"><head><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width,initial-scale=1">'
      '<title>'+escape(title)+' | CDMX AL MEMENTO</title>'
      '<link rel="stylesheet" href="/styles.css"></head><body>'
      '<header><div class="wrap"><div class="top"><a class="logo" href="/">CDMX <span>AL MEMENTO</span></a></div>'
      '<nav><a href="/">Noticias</a><a href="/reportes/">Reportes</a><a href="/guias/">Guías</a></nav></div></header>'
      '<main class="wrap prose">'+body+'</main><footer><div class="wrap"><a href="/contacto.html">Contacto</a> · '
      '<a href="mailto:'+MAIL+'">'+MAIL+'</a></div></footer></body></html>'
    )

def generate_report():
    from html import escape
    try:
        current = json.loads(DEST.read_text(encoding="utf-8"))
        rows = current.get("articles", [])
        entries = json.loads(REPORTS.read_text(encoding="utf-8")).get("reports", []) if REPORTS.exists() else []
        entries = [r for r in entries if isinstance(r, dict) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r.get("date","")))]
        REPORT_DIR.mkdir(exist_ok=True)
        local_day = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y-%m-%d")
        sources = {r.get("source","") for r in rows if isinstance(r,dict)}
        if len(rows) >= 8 and len(sources) >= 3:
            parts = [
              '<p class="eyebrow">Reporte de seguimiento automático · '+local_day+'</p>',
              '<h1>Noticias y titulares de la Ciudad de México</h1>',
              '<p>Selección automatizada de titulares, clasificada por temas y enlazada con las publicaciones originales.</p>',
              '<div class="notice">Este índice no es investigación independiente, ni verifica por sí mismo las noticias. '
              'Revisa la fecha y el contexto de cada fuente antes de tomar decisiones.</div>'
            ]
            for category in ("Metro","Movilidad","Seguridad","Cultura","Gobierno","CDMX"):
                group = [x for x in rows if x.get("category")==category][:8]
                if not group: continue
                parts.append('<h2>'+escape(category)+'</h2><ol>')
                for x in group:
                    link=x.get("url","")
                    if not link.startswith("https://news.google.com/"): continue
                    parts.append('<li><a target="_blank" rel="noopener noreferrer nofollow" href="'+escape(link,quote=True)+'">'
                      +escape(x.get("title",""))+'</a> — '+escape(x.get("source",""))+'</li>')
                parts.append('</ol>')
            parts.append('<p>Para solicitar correcciones escribe a <a href="mailto:'+MAIL+'">'+MAIL+'</a>.</p>')
            filename=local_day+".html"
            (REPORT_DIR/filename).write_text(report_shell("Reporte "+local_day,"\n".join(parts)),encoding="utf-8")
            entries=[e for e in entries if e.get("date")!=local_day]
            entries.append({"date":local_day,"url":"/reportes/"+filename,"count":len(rows)})
        entries.sort(key=lambda x:x["date"],reverse=True)
        entries=entries[:21]
        REPORTS.write_text(json.dumps({"updated":current.get("updated",""),"reports":entries},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        listing='<h1>Reportes automáticos de CDMX</h1><p>Índices de noticias publicados por medios externos. No son reportajes verificados de primera mano.</p><ul>'
        for e in entries:
            listing+='<li><a href="'+escape(e["url"],quote=True)+'">Reporte '+escape(e["date"])+'</a> · '+str(int(e.get("count",0)))+' titulares</li>'
        listing+='</ul>'
        (REPORT_DIR/"index.html").write_text(report_shell("Reportes diarios",listing),encoding="utf-8")
        sitemap_items=["","contacto.html","privacidad.html","sobre-nosotros.html","politica-editorial.html","creditos-fotograficos.html","guias/","reportes/"]
        sitemap_items += ["guias/"+v for v in ("estado-del-metro.html","alertas-por-lluvia.html","cierres-viales.html","tramites-cdmx.html")]
        sitemap_items += ["reportes/"+p.name for p in REPORT_DIR.glob("20??-??-??.html")]
        (DEST.parent/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + ''.join('<url><loc>'+SITE+'/'+escape(s)+'</loc></url>' for s in sitemap_items)+'</urlset>\n',encoding="utf-8")
        print("Reportes guardados:",len(entries))
    except Exception as exc:
        raise RuntimeError("La actualización de los reportes falló: "+str(exc)) from exc

if __name__ == "__main__":
    update()
    generate_report()

