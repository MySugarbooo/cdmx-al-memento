"""Fichas originales breves dentro del sitio.

La fuente automática disponible es un índice RSS de titulares; no dispone del
texto íntegro de cada reportaje. No recrear declaraciones, números ni escenas.
Cada nota explica el alcance, el interés público y lo que falta por confirmar.
Solo se marca como foto DEL HECHO una imagen con revisión editorial y licencia comprobadas.
Sin esa prueba se usan fotografías reales REPRESENTATIVAS, nunca evidencia atribuida.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
BOROUGH_PHOTOS=ROOT/"assets/alcaldias/fotos.json"
ARCHIVE_PHOTOS=ROOT/"assets/fotos/catalogo.json"
RECENT_PHOTOS=ROOT/"assets/fotos/recientes.json"
NEWS_PHOTOS=ROOT/"assets/fotos/indice-noticias-1100.json"
TOPIC_PHOTOS=ROOT/"assets/fotos/contexto-tematico.json"
VERIFIED_EVENTS=ROOT/"assets/fotos/hechos-verificados.json"

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

def _reported_angle(article):
    """Ideas específicas y atribuibles únicamente a lo expresado en el título."""
    title=str(article.get("title") or "")
    t=title.casefold()
    source=str(article.get("source") or "el medio de origen")
    borough=str(article.get("borough") or "")
    zone=(" en "+borough) if borough else " en la capital"

    if "alerta amber" in t or ("desaparec" in t and "años" in t):
        return (f"Una publicación de {source} informa sobre la búsqueda de una adolescente "
                f"y menciona la activación de una Alerta Amber{zone}. "
                "Por respeto a su privacidad, esta síntesis no reproduce datos personales "
                "adicionales ni especula sobre las circunstancias de la desaparición.")
    if ("atropell" in t or "arrollad" in t or "embiste" in t) and ("tráiler" in t or "trailer" in t):
        detained=" El encabezado también menciona la detención del conductor." if "detien" in t or "detenido" in t else ""
        return (f"De acuerdo con {source}, se reportó un atropellamiento con consecuencias mortales"
                f"{zone}, relacionado con un tráiler. "
                "Es una noticia que exige cuidado al informar sobre las personas afectadas."
                +detained)
    if "imss" in t and ("marcha" in t or "bloque" in t or "moviliza" in t):
        return (f"La cobertura de {source} se centra en movilizaciones de trabajadores "
                "del IMSS y en su posible o reportada repercusión sobre calles de Ciudad de México. "
                "Los trayectos y horarios deben revisarse en avisos recientes, pues una "
                "convocatoria no equivale a cierres confirmados durante todo el día.")
    if "marcha" in t or "concentraciones" in t or "bloqueos" in t:
        detail="una marcha y siete concentraciones" if "siete concentraciones" in t else "manifestaciones o bloqueos"
        return (f"Según la información destacada por {source}, {detail} forman parte de la "
                "jornada de movilidad capitalina. La ficha no demuestra por sí sola "
                "que todas las vías mencionadas sigan cerradas al momento de leerla.")
    if "metro" in t and ("línea a" in t or "linea a" in t) and ("rehabilit" in t or "arreglo" in t or "suspensi" in t):
        return (f"El medio {source} recoge advertencias y demandas sobre el mantenimiento de "
                "la Línea A del Metro. Hablar de una posible suspensión no significa "
                "que el tramo haya sido cerrado: se requiere consultar el aviso oficial.")
    if "metro" in t and ("retras" in t or "avance" in t or "estatus" in t or "estaciones" in t):
        lines=re.findall(r"\b(?:Línea|Líneas)\s+(?:[0-9AB]+(?:\s+y\s+[0-9AB]+)?)",title,re.I)
        which=(" El titular menciona "+", ".join(lines)+".") if lines else ""
        return (f"La nota de {source} reúne reportes sobre la circulación o los tiempos "
                "del Metro de Ciudad de México."+which+
                " La operación puede cambiar durante el día y los informes de usuarios "
                "no son equivalentes a un comunicado oficial.")
    if "lluvia" in t or "chubasco" in t or "clima" in t or "nublado" in t:
        conditions=("lluvias ligeras" if "ligera" in t else
                    "chubascos" if "chubasco" in t else
                    "lluvias" if "lluvia" in t else "condiciones meteorológicas")
        return (f"El pronóstico recogido por {source} se refiere a {conditions}{zone}. "
                "Se trata de una previsión, no de una constatación de lluvia en cada calle. "
                "Las condiciones pueden variar según la hora y la colonia.")
    if "gentrific" in t or "airbnb" in t or "rentas" in t or "vivienda" in t:
        return (f"El reportaje citado por {source} aborda los precios de vivienda o "
                f"los cambios residenciales{zone}. Las cifras y su metodología "
                "deben examinarse antes de concluir cuántas familias han sido desplazadas "
                "o qué tan representativos son determinados anuncios de renta.")
    if "energías renovables" in t or "energias renovables" in t:
        return (f"El medio {source} informa de una propuesta de colaboración entre la "
                "Ciudad de México y el Estado de México para impulsar energías renovables "
                "mediante incentivos privados. La ficha no confirma qué estímulos se "
                "aprobaron ni su fecha de entrada en vigor.")
    if "cempasúchil" in t or "cempasuchil" in t:
        return (f"La publicación de {source} pone el foco en dificultades que podrían "
                "afectar la comercialización del cempasúchil de Xochimilco. "
                "La producción de flor involucra a familias y productores locales; "
                "para explicar causas y alcances hacen falta los datos del reportaje.")
    if "afores" in t:
        return (f"Según {source}, una feria sobre administradoras del ahorro para el "
                "retiro se realiza o anuncia en Iztacalco. Antes de asistir conviene "
                "comprobar fechas, horarios y servicios directamente con la institución.")
    if "cultural" in t and ("asistencia" in t or "eventos" in t):
        return (f"La información que publica {source} analiza diferencias en la asistencia "
                "a eventos culturales por género. Para saber qué significa esta tendencia "
                "hacen falta los periodos, encuestas y metodología de la fuente.")
    if "concierto" in t:
        return (f"El medio {source} presenta conciertos o actividades musicales anunciadas "
                "en Ciudad de México. La programación, disponibilidad y costos pueden "
                "cambiar; comprueba los datos del organizador.")
    if "consultorios" in t and "issste" in t:
        return (f"El reporte atribuido a {source} habla de la incorporación de "
                "consultorios del ISSSTE en la capital. El dato del titular debe "
                "contrastarse con el comunicado institucional para conocer dónde "
                "operan y a qué pacientes atienden.")
    if "homicidio" in t and ("septiembre" in t or "62%" in t):
        return (f"Según cifras recogidas por {source}, las autoridades reportan "
                "una disminución de homicidios o delitos de alto impacto. "
                "Las comparaciones exigen conocer su periodo, fuente estadística y "
                "la forma en que se registraron los hechos.")
    if "autogobierno" in t or "penitenciarios" in t:
        return (f"{source} recoge declaraciones sobre la administración de los "
                "centros penitenciarios de la capital. El titular atribuye una postura "
                "a un funcionario; esa declaración debe diferenciarse de una "
                "evaluación independiente de la situación.")
    if "detien" in t or "caen dos" in t or "robar" in t or "asalt" in t:
        return (f"Una nota de {source} comunica un caso relacionado con una "
                f"detención o una presunta conducta delictiva{zone}. "
                "Es indispensable respetar la presunción de inocencia y no añadir "
                "acusaciones ni datos personales que el titular no acredita.")
    if "empleo" in t or "pérdida de empleos" in t:
        return (f"El medio {source} aborda una posible pérdida de empleos en "
                "la capital mediante una comparación con otra entidad. "
                "Los datos, el periodo y la metodología deben verificarse "
                "antes de sacar conclusiones sobre el mercado laboral.")
    if "reelegir" in t or "decretos" in t or "gobierno" in t:
        return (f"En su información, {source} aborda una decisión, declaración "
                "o debate relacionado con las instituciones de la ciudad. "
                "Conviene distinguir la intención anunciada de las resoluciones "
                "que hayan sido aprobadas y publicado oficialmente.")
    # Si el titular no encaja en una regla verificable, no inventar narrativa.
    return (f"La información publicada por {source} trata un asunto registrado "
            f"en la sección de {article.get('category') or 'CDMX'} del periódico. "
            "El encabezado contiene la referencia específica; sin acceso al cuerpo "
            "de la nota no corresponde agregar circunstancias que podrían ser falsas.")

def summarize(article):
    title=str(article.get("title") or "").strip()
    source=str(article.get("source") or "un medio periodístico").strip()
    category=str(article.get("category") or "CDMX")
    theme=TAGS.get(category,TAGS["CDMX"])
    first=_reported_angle(article)
    context=theme["importance"]
    pending=theme["verify"]+" El índice RSS no reproduce el reportaje íntegro, por lo que no añadimos nombres, cantidades ni circunstancias que aquí no podamos comprobar."
    return {"lead":first,"context":context,"pending":pending,
            "method":"Síntesis editorial propia elaborada a partir del titular y sus metadatos; no equivale a lectura del artículo íntegro."}

def _load(path,key):
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(key,[])
    except (OSError,ValueError,TypeError):
        return []

def verified_event_photo(article, catalog=None):
    """Requiere cotejo editorial explícito del hecho, autor, origen y licencia.

    Un título similar, una búsqueda en Commons o una foto subida recientemente
    NO demuestran por sí solos que la imagen corresponda al acontecimiento.
    """
    records = catalog if catalog is not None else _load(VERIFIED_EVENTS, "photos")
    if not isinstance(records, list):
        return None
    url = str(article.get("url") or "")
    title = str(article.get("title") or "").strip()
    if not url.startswith("https://news.google.com/rss/articles/") or not title:
        return None
    for p in records:
        if not isinstance(p, dict) or p.get("article_url") != url:
            continue
        if str(p.get("article_title") or "").strip().casefold() != title.casefold():
            continue
        if p.get("event_match_confirmed") is not True or p.get("rights_confirmed") is not True:
            continue
        image = str(p.get("url") or "")
        if not (re.fullmatch(r"/assets/fotos/[a-z0-9_-]+\.jpg", image)
                and (ROOT / image.lstrip("/")).is_file()
                or re.match(r"^https://(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/", image)):
            continue
        source = str(p.get("source") or "")
        evidence = str(p.get("evidence_url") or "")
        author = str(p.get("author") or "").strip()
        license_name = str(p.get("license") or "").strip()
        license_url = str(p.get("licenseUrl") or "")
        reviewer = str(p.get("reviewed_by") or "").strip()
        reviewed_at = str(p.get("reviewed_at") or "")
        if not (source.startswith("https://commons.wikimedia.org/wiki/File:")
                and evidence.startswith("https://")
                and author and len(author) <= 140 and reviewer
                and 0 < len(reviewer) <= 100):
            continue
        try:
            if not datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")).tzinfo:
                continue
        except (TypeError, ValueError):
            continue
        rights = re.fullmatch(r"CC BY(-SA)? (2\.0|2\.5|3\.0|4\.0)", license_name, re.I)
        if rights:
            slug = "by-sa" if rights.group(1) else "by"
            expected = f"https://creativecommons.org/licenses/{slug}/{rights.group(2)}/"
        elif license_name.upper() in ("CC0", "CC0 1.0"):
            expected = "https://creativecommons.org/publicdomain/zero/1.0/"
        else:
            continue
        if not license_url.startswith(expected):
            continue
        return {
            "id": "hecho_" + hashlib.sha256((url + source).encode()).hexdigest()[:20],
            "kind": "hecho", "verified": True,
            "url": image, "source": source, "author": author,
            "license": license_name, "licenseUrl": license_url,
            "topic": str(p.get("topic") or title)[:150],
            "evidence_url": evidence, "reviewed_at": reviewed_at,
        }
    return None


def _pool():
    catalog=_load(ARCHIVE_PHOTOS,"photos")
    recent=_load(RECENT_PHOTOS,"photos")
    borough=_load(BOROUGH_PHOTOS,"photos")
    photos=[]
    # La fototeca ampliada incluye 1,100 fotos con descriptores y créditos.
    # Buscar por tema es más preciso que asignar la primera imagen de una categoría.
    for item in (_load(TOPIC_PHOTOS,"photos")+_load(NEWS_PHOTOS,"photos")):
        if not isinstance(item,dict):
            continue
        photo_id=str(item.get("id") or "")
        url=str(item.get("url") or "")
        source=str(item.get("source") or "")
        if not re.fullmatch(r"[a-z0-9_]+",photo_id):
            continue
        if not (re.fullmatch(r"/assets/fotos/[a-z0-9_-]+\.jpg",url) or
                re.match(r"https://(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/",url)):
            continue
        if not (source.startswith("https://commons.wikimedia.org/wiki/File:")
                and item.get("author") and item.get("license")
                and str(item.get("licenseUrl") or "").startswith("https://creativecommons.org/")):
            continue
        keywords=item.get("keywords")
        photos.append(dict(
            id=photo_id,kind="representativa",url=url,
            category=item.get("category","CDMX"),borough="",
            topic=str(item.get("topic") or "")[:150],
            keywords=[str(word)[:100] for word in keywords[:8]] if isinstance(keywords,list) else [],
            author=item["author"],license=item["license"],
            licenseUrl=item["licenseUrl"],source=source))
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
        photos.append(dict(id=photo_id,kind="representativa",url="/assets/fotos/"+photo_id+".jpg",
                           category=item.get("category","CDMX"),borough="",
                           topic=item.get("topic") or filename,
                           author=item.get("author"),license=item.get("license"),
                           licenseUrl=item.get("licenseUrl",""),source=item["source"]))
    for item in recent:
        if not item.get("reviewed_location"):continue
        if not str(item.get("source","")).startswith("https://commons.wikimedia.org/wiki/File:"):continue
        url=str(item.get("url") or "")
        if not url.startswith(("https://thumb.wikimedia.org/wikipedia/commons/",
                               "https://upload.wikimedia.org/wikipedia/commons/")):continue
        photos.append(dict(id=item.get("id"),kind="representativa",url=url,category=item.get("category","CDMX"),
                           borough="",topic=item.get("topic") or "Ciudad de México",
                           author=item.get("author"),license=item.get("license"),
                           licenseUrl=item.get("licenseUrl",""),source=item["source"]))
    for item in borough:
        slug=str(item.get("slug") or "")
        if not re.fullmatch(r"[a-z-]+",slug):continue
        photos.append(dict(id="alcaldia_"+slug,kind="representativa",url="/assets/alcaldias/"+slug+".jpg",
                           category="CDMX",borough=item.get("name",""),
                           topic=item.get("caption","Ciudad de México"),
                           author=item.get("author"),license=item.get("license"),
                           licenseUrl=item.get("licenseUrl",""),source=item.get("source")))
    # Deduplicar por página original de Commons para evitar atribuciones distintas.
    unique={}
    for p in photos:
        src=p.get("source")
        if src and p.get("url") and p.get("author") and p.get("license"):
            unique.setdefault(src,p)
    return list(unique.values())


# No se usan fotografías de accidentes, manifestaciones particulares o
# emergencias anteriores como si ilustraran un nuevo hecho similar.
SENSITIVE_CONTEXT = re.compile(
    r"\b(?:incidente|colapso|accidente|siniestro|victimas|fallecidos|"
    r"marcha del orgullo|8 de marzo|manifestacion por|homenaje a)\b"
)

# Se inferiere el tema del titular antes de recurrir a la categoría RSS.
# En el feed general muchas noticias de Metro, clima o cultura figuran como CDMX.
SUBJECT_RULES = (
    (r"\b(?:metrobus|cablebus|trolebus|ecobici|ciclovia)\b", "Movilidad"),
    (r"\b(?:metro|linea \d{1,2}|linea [ab]|tren ligero)\b", "Metro"),
    (r"\b(?:perro|perrito|mascota|gato|animal|fauna|veterinari)\w*\b", "Medio Ambiente"),
    (r"\b(?:lluvia|tormenta|clima|inundacion|contaminacion|arbol|bosque)\w*\b", "Medio Ambiente"),
    (r"\b(?:hospital|clinica|drenaje|bache|basura|abasto|mercado|agua potable)\w*\b", "Servicios"),
    (r"\b(?:catrina|dia de muertos|cempasuchil|concierto|desfile|museo|"
     r"festival|exposicion|teatro|cultura)\w*\b", "Cultura"),
    (r"\b(?:hoy no circula|contingencia ambiental|holograma|verificacion vehicular|"
     r"marcha|bloqueo|trafico|carretera|movilidad|vialidad|"
     r"gran premio|formula 1|autodromo|circuito|automovili)\w*\b", "Movilidad"),
    (r"\b(?:policia|patrulla|fiscalia|robo|homicidio|detenid|"
     r"asalto|extorsion|delito|investigacion)\w*\b", "Seguridad"),
    (r"\b(?:alcalde|gobierno|congreso|presupuesto|secretaria)\w*\b", "Gobierno"),
)
STOP_WORDS = {
    "ciudad","mexico","cdmx","noticia","noticias","hoy","ayer","mañana",
    "este","esta","estos","estas","para","sobre","entre","ante","desde",
    "tras","segun","este","viernes","sabado","domingo","lunes","martes",
    "miercoles","jueves","octubre","noviembre","2026","2025","del","las",
    "los","una","uno","unos","unas","que","con","por","cuando","como",
    "cual","sera","seran","tiene","habra","hace","deja","al","la","el",
    "son","sus","todo","tambien","reportan","reporta","informa","nuevo",
    "nueva","capital","mexicana","mexicano","zona","calle","calles",
}
RELATED_WORDS = (
    (r"\b(?:perro|perrito|mascota|gato|animal|fauna)\w*\b",
     ("animal", "animales", "fauna", "mascota", "veterinario")),
    (r"\b(?:policia|patrulla|fiscalia|detenid|robo|asalto)\w*\b",
     ("policia", "patrulla", "seguridad")),
    (r"\b(?:lluvia|inundacion|tormenta|clima)\w*\b",
     ("lluvia", "agua", "clima", "nubes", "cielo")),
    (r"\b(?:marcha|protesta|manifestacion|bloqueo)\w*\b",
     ("movilidad", "vialidad", "reforma", "calle")),
    (r"\b(?:catrina|dia de muertos|desfile)\w*\b",
     ("catrina", "catrinas", "desfile")),
    (r"\b(?:automovili|formula 1|gran premio|autodromo|circuito)\w*\b",
     ("auto", "automovil", "vehiculo", "transito", "autodromo")),
    (r"\b(?:hoy no circula|contingencia ambiental|verificacion vehicular|holograma)\b",
     ("trafico", "vehicular", "automoviles", "autos", "transito", "movilidad")),
    (r"\b(?:hospital|clinica|imss|issste)\w*\b",
     ("hospital", "salud", "clinica", "imss", "issste")),
    (r"\b(?:desazolve|drenaje|agua potable)\w*\b",
     ("agua", "desazolve", "drenaje")),
)

def _photo_fold(text):
    text=unicodedata.normalize("NFKD",str(text or "").casefold())
    text="".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+",text))


def _photo_category(article):
    headline=_photo_fold(article.get("title"))
    for pattern,category in SUBJECT_RULES:
        if re.search(pattern,headline):
            return category
    return str(article.get("category") or "CDMX")


def _photo_score(article, photo):
    """Puntúa relación real con el título; nunca declara un hecho verificado."""
    headline=_photo_fold(article.get("title"))
    topic=_photo_fold(photo.get("topic"))
    keywords=_photo_fold(" ".join(str(x) for x in photo.get("keywords",[])))
    context=topic+" "+keywords
    category=_photo_category(article)
    photo_category=str(photo.get("category") or "CDMX")
    if not topic or SENSITIVE_CONTEXT.search(topic):
        return -10000
    # Una línea distinta del Metro es peor que una foto genérica del Metro.
    if category=="Metro":
        wanted=re.search(r"\blinea ([0-9]{1,2}|a|b)\b",headline)
        shown=re.search(r"\b(?:linea|line) ([0-9]{1,2}|a|b)\b",topic)
        if wanted and shown and wanted.group(1)!=shown.group(1):
            return -10000
    borough=_photo_fold(article.get("borough"))
    score=65 if photo_category==category else (12 if photo_category=="CDMX" else 0)
    if photo_category=="Alcaldías" and not borough:
        score-=30
    if borough and borough in topic:
        score+=170
    elif borough and borough in keywords:
        score+=100
    tokens={x for x in headline.split() if len(x)>3 and x not in STOP_WORDS}
    for word in tokens:
        if re.search(r"\b"+re.escape(word)+r"\b",topic):
            score+=34
        elif re.search(r"\b"+re.escape(word)+r"\b",keywords):
            score+=12
    for pattern,similar in RELATED_WORDS:
        if re.search(pattern,headline) and any(
            re.search(r"\b"+re.escape(word)+r"\b",topic) for word in similar
        ):
            score+=80
    if category=="Metro":
        wanted=re.search(r"\blinea ([0-9]{1,2}|a|b)\b",headline)
        shown=re.search(r"\b(?:linea|line) ([0-9]{1,2}|a|b)\b",topic)
        if wanted and shown and wanted.group(1)==shown.group(1):
            score+=220
    return score


def assign_photos(items):
    """Acontecimiento aprobado primero; si no, tema y lugar más próximos."""
    pool=_pool()
    reserved=set()
    verified_catalog=_load(VERIFIED_EVENTS,"photos")
    exact_count=0
    # Un orden estable evita cambios arbitrarios entre actualizaciones del feed.
    for a in items:
        exact=verified_event_photo(a,verified_catalog)
        if exact:
            a["photo"]=exact
            exact_count+=1
            continue
        # La imagen antigua no tiene preferencia sobre otra que represente mejor el tema.
        a.pop("photo",None)
        available=[p for p in pool if p.get("id") not in reserved]
        candidates=available or pool
        if not candidates:
            continue
        # La puntuación de pertinencia tiene prioridad absoluta sobre la variedad.
        best=max(candidates,key=lambda p:(
            _photo_score(a,p),
            # Desempate estable, sin elegir siempre el primer elemento de la categoría.
            hashlib.sha256((str(a.get("url"))+"|"+str(p.get("id"))).encode()).hexdigest(),
        ))
        if _photo_score(a,best)<0:
            continue
        a["photo"]=best
        reserved.add(best["id"])
    return {"available":len(pool),"assigned":sum(bool(a.get("photo")) for a in items),
            "unique":len({a["photo"]["id"] for a in items if a.get("photo")}),
            "del_hecho_verificadas":exact_count}
