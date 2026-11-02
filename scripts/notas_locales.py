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
    # Accidentes de motos, choques y siniestros: informar incluso si el hecho es
    # grave, sin inventar fallecimientos, lesiones, imágenes o circunstancias.
    if re.search(r"\b(?:accident\w*|choqu\w*|colisi[oó]n\w*|volcadur\w*|"
                 r"atropell\w*|arroll\w*|derrap\w*|siniestro vial)\b", t):
        vehicle=("una motocicleta" if re.search(r"\b(?:moto|motocicleta|motociclista)\w*\b", t)
                 else "un microbús" if re.search(r"\bmicrob[uú]s\b", t)
                 else "un autobús" if re.search(r"\bautob[uú]s\b", t)
                 else "vehículos" if re.search(r"\b(?:automovil|auto|camion|trailer|tráiler|vehiculo)\w*\b", t)
                 else "personas o vehículos involucrados")
        if re.search(r"\b(?:fallec\w*|muert\w*|murio|murieron|sin vida|pierde la vida|"
                     r"perdio la vida|fatal|mortal|muere|murio|murió|mata|matan|mat[oó])\b", t):
            outcome="El propio titular señala un fallecimiento, sin que esta ficha agregue cifras ni identidades."
        elif re.search(r"\b(?:herid\w*|lesionad\w*|hospitalizad\w*)\b", t):
            outcome="El propio titular menciona personas lesionadas, sin datos médicos adicionales verificados."
        else:
            outcome="El encabezado no permite determinar por sí solo si hubo personas lesionadas o fallecidas."
        return (f"De acuerdo con {source}, se informa de un hecho vial relacionado con "
                f"{vehicle}{zone}. {outcome} "
                "Se requiere consultar la nota original para conocer el punto exacto, las "
                "circunstancias y los reportes oficiales, sin atribuir responsabilidades sin pruebas.")
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
    if "expropi" in t and ("predio" in t or "vivienda" in t):
        return (f"Según {source}, el titular informa sobre una expropiación o su anuncio "
                f"relacionado con predios destinados a vivienda pública{zone}. "
                "La ubicación, situación jurídica y alcance de la medida deben "
                "comprobarse en documentos oficiales; el anuncio no prueba su ejecución.")
    if "vivienda pública" in t or "vivienda social" in t:
        return (f"El medio {source} informa sobre una iniciativa o medida relacionada "
                f"con vivienda pública{zone}. Su alcance, condiciones y estado "
                "de aprobación requieren consultar la publicación completa y fuentes oficiales.")
    if "gentrific" in t or "airbnb" in t or "rentas" in t:
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
    if ("centro" in t and ("evaluación laboral" in t or "evaluacion laboral" in t)) or ("inaugur" in t and "laboral" in t):
        return (f"De acuerdo con {source}, el titular informa de la inauguración "
                f"de un centro o servicio relacionado con evaluación laboral{zone}. "
                "Los servicios disponibles, requisitos y horarios requieren "
                "confirmación en la fuente y ante la institución responsable.")
    if "pérdida de empleos" in t or "perdida de empleos" in t:
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
    # Encabezar con el dato específico y comprobable del RSS, no con una
    # explicación genérica que pueda corresponder a otra noticia.
    first=(f"De acuerdo con {source}, el titular publicado es: «{title}». "
           + _reported_angle(article))
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


# Sí se informa sobre accidentes y hechos graves, incluso con material sensible
# verificado. Solo se evita presentar fotos de otros siniestros como si fueran actuales.
SENSITIVE_CONTEXT = re.compile(
    r"\b(?:incidente|colapso|accidente|siniestro|victimas|fallecidos|"
    r"marcha del orgullo|8 de marzo|manifestacion por|homenaje a)\b"
)

# Se inferiere el tema del titular antes de recurrir a la categoría RSS.
# En el feed general muchas noticias de Metro, clima o cultura figuran como CDMX.
SUBJECT_RULES = (
    # Las muertes violentas y condenas judiciales no son temas genéricos de CDMX.
    (r"\b(?:matan|balazos|asesinan|homicidio|condenad[oa]s?|condenan|prision)\b", "Seguridad"),
    # El RSS puede etiquetar temas recreativos o tecnológicos como Seguridad.
    (r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b", "Movilidad"),
    (r"\b(?:robot|robots|robotica|robotico|roboticos)\b", "CDMX"),
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
    (r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b",
     ("bici", "bicicleta", "bicicletas", "ciclista", "ciclistas", "ciclovia", "ecobici", "cicloton")),
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
    # "Poner en marcha" un programa no describe una marcha o protesta vial.
    headline=re.sub(r"\b(?:pone|ponen|puso|poner|puesta|entra|entro|entrara)\s+en\s+marcha\b",
                    "activa", headline)
    # Un aviso del Hoy No Circula no es una nota cultural aunque mencione Día de Muertos.
    if re.search(r"\bhoy no circula\b", headline):
        return "Movilidad"
    # Un operativo policial durante una festividad sigue siendo Seguridad.
    if re.search(r"\bpolicias?\b.*\b(?:cuidan|vigilan|operativo|despliegan)\b", headline):
        return "Seguridad"
    if re.search(r"\b(?:detienen|arrestan|capturan|aprehenden)\s+a\s+(?:\d+|un|una|dos|tres|cuatro|cinco|seis|personas|hombres|mujeres)\b", headline):
        return "Seguridad"
    for pattern,category in SUBJECT_RULES:
        if re.search(pattern,headline):
            return category
    return str(article.get("category") or "CDMX")


# Resguardos editoriales: una coincidencia geográfica o de categoría no basta.
# Si la fototeca no tiene contexto del tema, se prefiere publicar sin imagen.
STRICT_PHOTO_TOPICS = (
    # Un edificio turístico no representa retrasos de vuelos ni operaciones aéreas.
    (r"\b(?:aeropuerto|vuelos? demorados?|vuelos? retrasados?)\b",
     r"\b(?:aeropuerto|aeronautica|aviones?|aeronaves?|vuelos?|terminal aerea|pista de aterrizaje)\b"),
    # Una casa del Centro Histórico no ilustra puentes peatonales ni estafas viales.
    (r"\b(?:puentes? peatonales?|pasarelas? peatonales?)\b",
     r"\b(?:puentes?|pasarelas?|pasos? peatonales?|cruces? elevados?)\b"),
    (r"\bmontachoques\b",
     r"\b(?:choques?|automoviles?|autos?|vehiculos?|trafico|transito|vialidad|carretera|avenida|seguridad vial)\b"),
    # La captación de lluvia no es una imagen de pronóstico, frío o viento.
    (r"\b(?:clima|pronostico|rachas de viento|mananas frias|frente frio)\b",
     r"\b(?:clima|pronostico|meteorologia|temperatura|viento|frio|nubes?|cielo|tormenta|neblina)\b"),
    # Los choques y derrapes de motos, camiones o vehículos requieren contexto
    # de tránsito; compartir alcaldía no vuelve pertinente una iglesia.
    (r"\b(?:accident\w*|choc\w*|choqu\w*|colisi\w*|volcadur\w*|derrap\w*)\b.*\b(?:motociclist\w*|motociclet\w*|moto\w*|camion\w*|vehicul\w*|automovil\w*)\b|"
     r"\b(?:motociclist\w*|motociclet\w*|moto\w*|camion\w*|vehicul\w*|automovil\w*)\b.*\b(?:accident\w*|choc\w*|choqu\w*|colisi\w*|volcadur\w*|derrap\w*)\b",
     r"\b(?:motociclet\w*|motociclist\w*|motos?|camion\w*|vehicul\w*|automovil\w*|vehicular|trafico|transito|vialidad|carretera|avenida|cruce peatonal)\b"),
    # Atropellamientos y muertes viales no se ilustran con iglesias o plazas.
    (r"\b(?:atropell\w*|arroll\w*)\b",
     r"\b(?:microbus|autobus|vehiculos?|vehicular|trafico|transito|vialidad|carretera|avenida|peatones?|cruce peatonal)\b"),
    # Los operativos de vigilancia no se ilustran con museos sin relación.
    (r"\bpolicias?\b.*\b(?:cuidan|vigilan|operativo|despliegan)\b",
     r"\b(?:policias?|patrullas?|vigilancia|seguridad|operativo|agentes?)\b"),
    # Para detenciones de personas, una plaza de la misma alcaldía no basta.
    # En un operativo del Gran Premio también es pertinente el autódromo.
    (r"^(?!.*\b(?:gp de mexico|gran premio|formula 1|autodromo)\b).*\b(?:detienen|arrestan|capturan|aprehenden)\s+a\s+(?:\d+|un|una|dos|tres|cuatro|cinco|seis|personas|hombres|mujeres)\b",
     r"\b(?:policias?|patrullas?|fiscalia|justicia|tribunal|detencion|seguridad|investigacion penal)\b"),
    (r"\bempleo de mujeres\b",
     r"\b(?:empleo|trabajo|mujeres|oficinas?|economia|trabajadoras?)\b"),
    (r"\bmorena\b.*\b(?:militantes|reunio|asamblea)\b",
     r"\b(?:morena|militantes|asamblea|reunion|partido politico|politica)\b"),
    (r"\b(?:asamblea comunitaria|autoridades auxiliares)\b",
     r"\b(?:asamblea|comunitaria|vecinos|cabildo|reunion|autoridades auxiliares)\b"),
    (r"\b(?:juan atkins|pionero del techno)\b",
     r"\b(?:techno|musica|dj|vinilos?|discos?|escenario|concierto|musico|productor musical)\b"),
    # Envenenamiento de perros exige imagen canina, no fauna genérica.
    (r"\benvenenamientos?\b.*\b(?:perros?|mascotas?)\b",
     r"\b(?:perritos?|perros?|mascotas?|caninos?|veterinaria)\b"),
    (r"\b(?:perritos?|perros?|mascotas?|envenenamientos? de perros?)\b",
     r"\b(?:perritos?|perros?|mascotas?|caninos?|animales?|veterinaria)\b"),
    (r"\b(?:matan|balazos|asesinan|homicidio|condenad[oa]s?|condenan|prision|delitos? contra)\b",
     r"\b(?:fiscalia|justicia|tribunal|juzgado|penitenciario|prision|ministerio publico|investigacion penal)\b"),
    (r"\b(?:sin agua|falta de agua|suspension de agua|corte de agua)\b",
     r"\b(?:agua|tuberias?|acueducto|pozo|abastecimiento|red hidraulica|cisterna|pipas?|grifos?)\b"),
    (r"\b(?:fallece motociclista|muere motociclista|motociclistas? fallecidos?)\b",
     r"\b(?:motos?|motocicletas?|carretera|vialidad|trafico|transito|vehicular)\b"),
    (r"\b(?:bloquean? avenida|bloqueos? en avenida)\b",
     r"\b(?:manifestacion|protesta|bloqueo|colectivo de busqueda|personas desaparecidas)\b"),
    (r"\b(?:panteon|cementerio|tumba)\b",
     r"\b(?:panteon|cementerio|tumbas?|sepulturas?|mausoleo)\b"),
    (r"\b(?:desfile|catrinas?)\b",
     r"\b(?:desfile|catrinas?|comparsa|procesion|festival|dia de muertos)\b"),
    (r"\b(?:concierto|u2|bono)\b",
     r"\b(?:musica|concierto|escenario|bandas?|cantante|u2|guitarra|rock)\b"),
    (r"\blicencia de conducir\b",
     r"\b(?:licencia|conducir|vehiculos?|automoviles?|autos?|transito|tramite)\b"),
    (r"\bcalidad del aire\b",
     r"\b(?:contaminacion|smog|atmosfera|emisiones|contaminantes|calidad del aire|medicion ambiental)\b"),
)

def _photo_score(article, photo):
    """Puntúa relación real con el título; nunca declara un hecho verificado."""
    headline=_photo_fold(article.get("title"))
    topic=_photo_fold(photo.get("topic"))
    keywords=_photo_fold(" ".join(str(x) for x in photo.get("keywords",[])))
    context=topic+" "+keywords
    # El catálogo local no debe ilustrar noticias situadas fuera de la capital.
    # No presentar un templo o calle de CDMX como una finca de Veracruz.
    if "(fuera de CDMX)" in str(article.get("location") or ""):
        return -10000
    category=_photo_category(article)
    photo_category=str(photo.get("category") or "CDMX")
    if not topic or SENSITIVE_CONTEXT.search(topic):
        return -10000
    # No presentar patrullas o acciones policiales en noticias ajenas a Seguridad.
    if category!="Seguridad" and (
        photo_category=="Seguridad" or
        re.search(r"\b(?:patrullas?|policias?|fiscalia|detenciones?|armamento)\b", context)
    ):
        return -10000
    # Una clasificación RSS errónea no autoriza cambiar el tema de la imagen.
    if photo_category not in (category, "CDMX", "Alcaldías"):
        return -10000
    # El título y el descriptor deben compartir el asunto real de la nota.
    for headline_pattern, photo_pattern in STRICT_PHOTO_TOPICS:
        if re.search(headline_pattern, headline) and not re.search(photo_pattern, context):
            return -10000
    # Una graduación policial no ilustra una muerte violenta o sentencia penal.
    if (re.search(r"\b(?:matan|balazos|asesinan|homicidio|condenad[oa]s?|condenan|prision)\b", headline)
            and re.search(r"\b(?:graduacion|ceremonia de policia|entrega de patrullas)\b", topic)):
        return -10000
    # Una nota del Hoy No Circula requiere contexto vehicular, no fotos de la festividad.
    if re.search(r"\bhoy no circula\b", headline):
        if not re.search(r"\b(?:vehiculos?|vehicular|automoviles?|autos?|coches?|transito|trafico|vialidad|circulacion|hologramas?|verificacion vehicular|hoy no circula)\b", context):
            return -10000
    # Para noticias de ciclismo, exigir una fotografía relacionada con bicicletas.
    if re.search(r"\b(?:muevete en bici|paseo dominical|bicicletas?|ciclistas?|ciclismo|ciclovias?|ecobici|cicloton)\b", headline):
        if not re.search(r"\b(?:bici|bicicletas?|ciclistas?|ciclovias?|ecobici|cicloton)\b", context):
            return -10000
    # Distinguir noticias del circuito de avisos de cierres viales por el GP.
    # Una imagen del transporte público o una calle ajena no ilustra el evento.
    if re.search(r"\b(?:gp de mexico|gran premio|formula 1|autodromo)\b", headline):
        race_context = r"\b(?:formula 1|f1|gran premio|autodromo|circuito|carrera|monoplaza|piloto|automovilismo)\b"
        road_context = r"\b(?:vialidad|trafico|avenida|calles?|calzada|reforma|insurgentes|periferico|cierres? viales?)\b"
        road_closure = re.search(r"\b(?:calles? cerradas?|cierres?|alternativas viales|rutas alternas)\b", headline)
        if road_closure:
            if re.search(r"\b(?:metrobus|trolebus|ecobici|bicicletas?|estacion)\b", topic):
                return -10000
            if not (re.search(race_context, topic) or re.search(road_context, topic)):
                return -10000
        elif not re.search(race_context, topic):
            return -10000
    # Un rescate patrimonial de una fuente no se ilustra con rescates de viviendas.
    # Coincidir en el verbo "rescate" y en la alcaldía no basta.
    if (re.search(r"\bfuente [a-z]", headline)
            and re.search(r"\b(?:rescate|restauracion|rehabilitacion|premia|premio)\b", headline)):
        if not re.search(r"\b(?:fuentes?|esculturas?|monumentos?|patrimonio|plazas?|jardines?)\b", topic):
            return -10000
    # La Rodada del Terror y los corralones de motos requieren imágenes de motocicletas,
    # no una foto genérica de Protección Civil.
    if (re.search(r"\b(?:rodada del terror|mega rodada del terror|megarodadadelterror)\b", headline)
            or (re.search(r"\bcorralon\b", headline)
                and re.search(r"\b(?:motos?|motocicletas?|motociclistas?)\b", headline))):
        if not re.search(r"\b(?:motos?|motocicletas?|motociclistas?|rodada)\b", context):
            return -10000
    # Un incidente en pista de Fórmula 1 no es un incidente del Metrobús.
    if (re.search(r"\b(?:bottas|verstappen|hamilton|formula 1|f1)\b", headline)
            and re.search(r"\b(?:accidente|bandera roja|choque)\b", headline)):
        if not re.search(r"\b(?:formula 1|f1|autodromo|circuito|carrera|monoplaza|piloto|automovilismo)\b", topic):
            return -10000
    # La consulta infantil no se ilustra con una fotografía de cuarentena.
    if (re.search(r"\b(?:urnas?|consulta|votacion|elecciones?)\b", headline)
            and re.search(r"\b(?:ninos?|menores?|infancia|adolescentes?)\b", headline)):
        if not re.search(r"\b(?:urnas?|votacion|elecciones?|consulta|infancia|ninos?|menores?|escuelas?|estudiantes?|boletas?)\b", topic):
            return -10000
    # Un programa invernal requiere contexto de frío o asistencia social.
    if re.search(r"\b(?:temporada invernal|plan invernal|programa invernal|frente frio|cobijas?|vacunacion)\b", headline):
        if not re.search(r"\b(?:invierno|invernal|frio|cobijas?|albergue|vacunacion|abrigo|apoyo social|proteccion civil|clima|nubes|temperatura)\b", topic):
            return -10000
    # Los pilotos, abandonos y triunfos de F1 no se ilustran con paisajes turísticos.
    if (re.search(r"\b(?:alonso|bottas|verstappen|hamilton|antonelli|checo)\b", headline)
            and re.search(r"\b(?:abandon\w*|gran premio|formula 1|gp|carrera|piloto|campeon\w*|bandera roja|gana|gano|ganaron|ganador\w*|triunf\w*|victoria|venc\w*|podio|pole|sexta vez)\b", headline)):
        if not re.search(r"\b(?:formula 1|f1|gran premio|autodromo|circuito|carrera|monoplaza|piloto|automovilismo)\b", topic):
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
        # Los siniestros cotejados no deben ilustrarse con otra emergencia histórica.
        # Sin foto del hecho autenticada, el sitio utiliza su ilustración neutral.
        if a.get("editorial_verified") is True and a.get("sensitive_media") is True:
            a.pop("photo", None)
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
