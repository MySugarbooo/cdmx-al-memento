"""Fichas originales breves dentro del sitio.

La fuente automática disponible es un índice RSS de titulares; no dispone del
texto íntegro de cada reportaje. No recrear declaraciones, números ni escenas.
Cada nota explica el alcance, el interés público y lo que falta por confirmar.
Las imágenes son fotos reales DE CONTEXTO, nunca fotografías de los hechos.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
BOROUGH_PHOTOS=ROOT/"assets/alcaldias/fotos.json"
ARCHIVE_PHOTOS=ROOT/"assets/fotos/catalogo.json"
RECENT_PHOTOS=ROOT/"assets/fotos/recientes.json"

TAGS={
 "Metro":{
   "focus":"el servicio de transporte del Metro y las personas que utilizan su red",
   "importance":"Los cambios en este sistema pueden afectar los horarios, las conexiones y la planeación de los viajes cotidianos.",
   "verify":"El estado operativo, las estaciones y las alternativas de traslado deben comprobarse en los avisos actuales del Metro."
 },
 "Movilidad":{
   "focus":"la movilidad de la capital y las condiciones de traslado",
   "importance":"Esta información puede resultar útil para organizar recorridos, entregas, trabajo, clases y citas.",
   "verify":"Antes de modificar un itinerario hay que contrastar el lugar, el horario y los avisos recientes de las autoridades de movilidad."
 },
 "Seguridad":{
   "focus":"la seguridad y la convivencia en los espacios de la ciudad",
   "importance":"Una noticia sobre seguridad afecta a personas y comunidades; conviene informar sin especular ni convertir a nadie en culpable antes de una resolución.",
   "verify":"Se necesita contrastar el informe de las autoridades, las circunstancias y el estado de cualquier investigación."
 },
 "Cultura":{
   "focus":"la vida cultural, el patrimonio y las actividades de la ciudad",
   "importance":"La actividad cultural abre oportunidades de encuentro, aprendizaje y disfrute para habitantes y visitantes.",
   "verify":"Los accesos, boletos, sedes, cupos y horarios deben consultarse con la institución organizadora."
 },
 "Gobierno":{
   "focus":"decisiones públicas e instituciones de la capital",
   "importance":"Las decisiones administrativas pueden influir en servicios, trámites y derechos; conviene conocer sus condiciones y a quiénes afectan.",
   "verify":"Es indispensable consultar los acuerdos, comunicados o documentos oficiales antes de dar una medida por vigente."
 },
 "CDMX":{
   "focus":"un asunto de interés público relacionado con la Ciudad de México",
   "importance":"Conocer qué se publica sobre la ciudad ayuda a seguir temas que afectan a vecinas, vecinos y visitantes.",
   "verify":"Los detalles, la ubicación y las posibles actualizaciones requieren corroboración en la publicación completa o ante la instancia correspondiente."
 },
}

def local_link(article):
    token=hashlib.sha256(str(article.get("url") or "").encode()).hexdigest()[:20]
    date=str(article.get("date") or "")[:7]
    return "/noticias/?id="+token+"&mes="+date

def summarize(article):
    title=str(article.get("title") or "").strip()
    source=str(article.get("source") or "un medio periodístico").strip()
    category=str(article.get("category") or "CDMX")
    theme=TAGS.get(category,TAGS["CDMX"])
    q=title.endswith("?") or title.startswith(("¿","Qué ","Cómo ","Cuándo ","Dónde "))
    if q:
        first=(f"La publicación de {source} plantea una pregunta sobre {theme['focus']}. "
               "El encabezado invita a conocer una respuesta que no puede darse por comprobada solo con el índice de noticias.")
    elif re.search(r"\b(podr[ií]a|posible|prev[eé]|planea|busca|alerta|advierte|pronostic|habr[ií]a)\b",title,re.I):
        first=(f"El medio {source} informa sobre una propuesta, advertencia o posibilidad vinculada con "
               f"{theme['focus']}. La manera en que se presenta el asunto no equivale a una confirmación de que ya ocurrió.")
    else:
        first=(f"De acuerdo con un titular publicado por {source}, el tema de actualidad está relacionado con "
               f"{theme['focus']}. La atribución corresponde al medio citado, no a una comprobación independiente de nuestra redacción.")
    location=str(article.get("borough") or "").strip()
    if location:
        first+=f" El encabezado menciona {location}; esa referencia no demuestra por sí misma dónde ocurrieron todos los hechos."
    context=theme["importance"]
    pending=theme["verify"]+" El índice RSS no reproduce el reportaje íntegro, por lo que no añadimos nombres, cantidades ni circunstancias que aquí no podamos comprobar."
    # Se preserva el título como tal para que el lector conozca el hecho
    # comunicado por la fuente, y la interpretación no lo presente como
    # reportaje propio.
    return {"lead":first,"context":context,"pending":pending,
            "method":"Síntesis editorial propia elaborada a partir del titular y sus metadatos; no equivale a lectura del artículo íntegro."}

def _load(path,key):
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(key,[])
    except (OSError,ValueError,TypeError):
        return []

def _pool():
    catalog=_load(ARCHIVE_PHOTOS,"photos")
    recent=_load(RECENT_PHOTOS,"photos")
    borough=_load(BOROUGH_PHOTOS,"photos")
    photos=[]
    # Excluye piezas con lugar no identificado, fuera de CDMX o duplicados.
    unsuitable=re.compile(r"louisville|kentucky|zacatecas|chihuahua|san francisco|"
                          r"california|el paso street|paleando nieve|old new city|"
                          r"cloudy \(|aesthetic|harmony \(|valle destrucci[oó]n|"
                          r"v of \(|last sunlight|palace of fine arts \(",re.I)
    for item in catalog:
        photo_id=str(item.get("id") or "")
        if not re.fullmatch(r"archivo_[a-z0-9_]+",photo_id):continue
        filename=str(item.get("file") or "")
        if unsuitable.search(filename):continue
        if not str(item.get("source","")).startswith("https://commons.wikimedia.org/wiki/File:"):continue
        photos.append(dict(id=photo_id,url="/assets/fotos/"+photo_id+".jpg",
                           category=item.get("category","CDMX"),borough="",
                           topic=item.get("topic") or filename,
                           author=item.get("author"),license=item.get("license"),
                           source=item["source"]))
    for item in recent:
        if not item.get("reviewed_location"):continue
        if not str(item.get("source","")).startswith("https://commons.wikimedia.org/wiki/File:"):continue
        url=str(item.get("url") or "")
        if not url.startswith(("https://thumb.wikimedia.org/wikipedia/commons/",
                               "https://upload.wikimedia.org/wikipedia/commons/")):continue
        photos.append(dict(id=item.get("id"),url=url,category=item.get("category","CDMX"),
                           borough="",topic=item.get("topic") or "Ciudad de México",
                           author=item.get("author"),license=item.get("license"),source=item["source"]))
    for item in borough:
        slug=str(item.get("slug") or "")
        if not re.fullmatch(r"[a-z-]+",slug):continue
        photos.append(dict(id="alcaldia_"+slug,url="/assets/alcaldias/"+slug+".jpg",
                           category="CDMX",borough=item.get("name",""),
                           topic=item.get("caption","Ciudad de México"),
                           author=item.get("author"),license=item.get("license"),source=item.get("source")))
    # Fotografías históricas de contexto cuya procedencia y licencias figuran
    # en el archivo fotos.js; mismas imágenes que la página ya usa.
    # Evitar duplicados de Commons por URL original y contenido.
    base=_load(ROOT/"assets/fotos/catalogo.json","photos")
    unique={}
    for p in photos:
        src=p.get("source")
        if src and p.get("url") and p.get("author") and p.get("license"):
            unique.setdefault(src,p)
    return list(unique.values())

def assign_photos(items):
    """Una imagen REAL distinta para cada noticia de la portada (hasta 60)."""
    pool=_pool()
    reserved=set()
    # Primero mantener imágenes previamente asignadas cuando sean del catálogo.
    known={p["id"]:p for p in pool}
    for a in items:
        prev=a.get("photo")
        if isinstance(prev,dict) and prev.get("id") in known and prev["id"] not in reserved:
            a["photo"]=known[prev["id"]]
            reserved.add(prev["id"])
    for a in items:
        prev=a.get("photo")
        if isinstance(prev,dict) and prev.get("id") in reserved:continue
        borough=str(a.get("borough") or "")
        category=str(a.get("category") or "CDMX")
        ordered=(
            [p for p in pool if borough and p["borough"]==borough]+
            [p for p in pool if p["category"]==category]+
            [p for p in pool if p["category"]=="CDMX"]+
            pool
        )
        choice=next((p for p in ordered if p["id"] not in reserved),None)
        if choice:
            a["photo"]=choice
            reserved.add(choice["id"])
        else:
            a.pop("photo",None) # Jamás prometer una imagen distinta si se agotaron.
    return {"available":len(pool),"assigned":sum(bool(a.get("photo")) for a in items),
            "unique":len({a["photo"]["id"] for a in items if a.get("photo")})}
