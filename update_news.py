"""Actualiza enlaces y titulares desde Google News RSS. No copia artículos."""
import json, urllib.request, urllib.parse, xml.etree.ElementTree as ET, re, html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
FEEDS={'Metro':'Metro CDMX','Movilidad':'tráfico vial Ciudad de México','Seguridad':'seguridad Ciudad de México','Cultura':'eventos culturales Ciudad de México','Gobierno':'gobierno Ciudad de México','CDMX':'noticias Ciudad de México'}
HEADERS={'User-Agent':'CDMXAlMemento/1.0 (news aggregator)'}
def clean(t):return re.sub(r'<[^>]*>','',html.unescape(t or '')).strip()
def update():
    out=[]; seen=set()
    for category,query in FEEDS.items():
        url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query+' when:2d','hl':'es-419','gl':'MX','ceid':'MX:es-419'})
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=18) as resp: root=ET.fromstring(resp.read())
            for item in root.findall('.//item')[:12]:
                title=clean(item.findtext('title')); link=item.findtext('link','').strip(); source=clean(item.findtext('source'))
                if not title or not link or title.lower() in seen:continue
                seen.add(title.lower())
                try:date=parsedate_to_datetime(item.findtext('pubDate')).astimezone(timezone.utc).isoformat()
                except Exception:date=''
                out.append({'title':title,'description':'Titular recopilado automáticamente. Consulta el texto completo y la información actualizada en el medio de origen.','url':link,'source':source or 'Google News','date':date[:10],'category':category,'sort':date})
        except Exception as exc:print('Feed falló:',category,exc)
    out.sort(key=lambda x:x['sort'],reverse=True)
    for a in out:a.pop('sort',None)
    if not out:raise RuntimeError('No hay titulares nuevos; se conserva el archivo anterior.')
    Path(__file__).with_name('news.json').write_text(json.dumps({'updated':datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),'articles':out[:60]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Actualizados',len(out),'titulares')
if __name__=='__main__':update()
