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
    # Aprovechar agua de lluvia no equivale a un pronóstico meteorológico.
    if "captación de agua de lluvia" in t or "cosecha de lluvia" in t:
        return (f"El titular de {source} aborda la captación y aprovechamiento de agua pluvial{zone}. "
                "Se trata de una práctica o iniciativa relacionada con el uso del agua, "
                "no de una previsión del tiempo. Para conocer su alcance y resultados "
                "es necesario consultar el reportaje original.")
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
    return (f"La información publicada por {source} aborda un asunto que este portal "
            f"clasifica como {article.get('category') or 'CDMX'}. "
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
    (r"\b(?:grupos? criminales?|organizaciones? criminales?|crimen organizado)\b", "Seguridad"),
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
    # Los resultados deportivos del GP no deben heredar fotografías de tráfico.
    if re.search(r"\b(?:formula 1|gp ciudad de mexico|gran premio|nascar)\b", headline):
        if re.search(
            r"\b(?:cierres? viales?|calles? cerradas?|trafico|congestionamiento|"
            r"desvios?|rutas? alternas?|alternativas? viales?|transporte publico|"
            r"estacionamientos?)\b", headline
        ):
            return "Movilidad"
        return "CDMX"
    # Los ataques y homicidios prevalecen sobre menciones a festividades.
    if re.search(r"\b(?:ataque armado|balacera|asesina(?:n)?|asesinad\w*|asesinato)\b", headline):
        return "Seguridad"
    # Las víctimas de disparos son un tema de seguridad, aunque el RSS diga CDMX.
    if re.search(r"\b(?:balead\w*|balear\w*|balean|baleo)\b", headline):
        return "Seguridad"
    # Un operativo policial durante una festividad sigue siendo Seguridad.
    if re.search(r"\bpolicias?\b.*\b(?:cuidan|vigilan|operativo|despliegan)\b", headline):
        return "Seguridad"
    # Operativos de seguridad en panteones siguen siendo seguridad,
    # aunque el titular mencione la celebración de Día de Muertos.
    if re.search(r"\boperativos? de seguridad\b", headline):
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
    # Un riff anunciado por una banda requiere una imagen musical, no un monumento.
    (r"\briff\b",
     r"\b(?:musica|conciertos?|guitarras?|bandas?|escenarios?|rock|cantantes?|festivales?|auditorios?|estadios?)\b"),
    # Un taller de aviación en el AICM no se ilustra con una estación del Metro.
    (r"\b(?:aicm|mexicana de aviacion)\b",
     r"\b(?:aicm|aeropuertos?|aviones?|aeronaves?|aviacion|terminal aeroportuaria|pista de aterrizaje|hangar de mantenimiento|mantenimiento aeronautico)\b"),
    # La apertura de hoteles exige una imagen de hospedaje, no un jardín cercano.
    (r"\bhyatt\b",
     r"\b(?:hotel(?:es)?|hospedaje|alojamiento|resort|habitaciones?|recepcion|lobby)\b"),
    # Las rachas meteorológicas no se ilustran con una plaza sin contexto del clima.
    (r"\brachas?\b",
     r"\b(?:viento|rachas?|meteorologia|clima|nubes?|cielo nublado|tormenta|temperatura|frio)\b"),
    # La cobertura de la Anti-Unión requiere contexto de investigación, no ceremonia policial.
    (r"\banti[ -]?union\b",
     r"\b(?:fiscalia|investigacion penal|detencion|ministerio publico|justicia|operativo policial|patrulla)\b"),
    # Una ofrenda monumental no es la cafetería de un museo.
    (r"\bofrenda monumental\b",
     r"\b(?:ofrendas?|altares?|dia de muertos|catrinas?|decoracion funeraria)\b"),
    # Una agenda de eventos de Día de Muertos requiere contexto festivo real.
    (r"\b(?:eventos? gratis|actividades gratis|que hacer)\b.*\bdia de muertos\b",
     r"\b(?:dia de muertos|ofrendas?|altares?|catrinas?|festivales?|eventos?|conciertos?|desfiles?|celebraciones?)\b"),
    # No utilizar graduaciones policiales para remisiones de motocicletas.
    (r"\brodadas? del terror\b",
     r"\b(?:motos?|motocicletas?|motociclistas?|rodadas?|corralones?|deposito vehicular)\b"),
    # El saldo de visitantes durante Día de Muertos no es una entrada de cine histórica.
    (r"\b(?:saldo blanco\b.*\bdia de muertos|dia de muertos\b.*\bsaldo blanco)\b",
     r"\b(?:dia de muertos|panteones?|cementerios?|ofrendas?|catrinas?|celebracion|visitantes?|operativo de seguridad)\b"),
    (r"\bforo urbano mundial\b",
     r"\b(?:foro urbano|urbanismo|onu habitat|conferencias?|planeacion urbana|ciudades|vivienda|arquitectura)\b"),
    (r"\bnascar\b",
     r"\b(?:nascar|automovilismo|autodromo|carreras? de autos?|vehiculos? de carreras?|circuito de carreras?)\b"),
    (r"\bezln\b.*\bbuscadoras?\b",
     r"\b(?:ezln|zapatistas?|colectivos? de busqueda|madres? buscadoras?|personas desaparecidas|manifestaciones?|protestas?)\b"),
    # El mismo municipio no convierte un jardín o monumento en imagen de búsqueda.
    (r"\b(?:caminata\b.*\b(?:recuperar a su hija|buscando a su hija)|madres? buscadoras?)\b",
     r"\b(?:caminata|colectivos? de busqueda|familias? buscadoras?|madres? buscadoras?|personas desaparecidas|manifestacion|protesta)\b"),
    # Una protesta sindical exige manifestantes, no una calle turística.
    (r"\b(?:protesta sindical|comitiva de trabajadores)\b",
     r"\b(?:protestas?|manifestaciones?|sindical|trabajadores?|plantones?|marchas?)\b"),
    (r"\bmochila de emergencia\b",
     r"\b(?:mochilas?|emergencias?|proteccion civil|suministros?|botiquines?|evacuacion)\b"),
    # Titulares de empleo y becas no se ilustran con monumentos o avenidas.
    (r"\b(?:embajada\b.*\bvacantes?|vacantes?\b.*\bembajada)\b",
     r"\b(?:embajada|vacantes?|empleo|trabajo|oficinas?|alemania)\b"),
    (r"\bbeca de transporte\b",
     r"\b(?:becas?|universitarios?|estudiantes?|transporte|metro|autobuses?)\b"),
    # La rotura de una tubería no se representa con iglesias del mismo barrio.
    (r"\bfuga de agua\b",
     r"\b(?:fuga de agua|tuberias?|reparacion|fontaneria|agua potable|red hidraulica)\b"),
    # "Asesinados" y "asesinadas" no coincidían con el patrón "asesinan".
    (r"\b(?:asesinad\w*|asesina(?:n)?|homicidios?|balacera|ataque armado)\b",
     r"\b(?:fiscalia|investigacion penal|justicia|ministerio publico|peritos?|escena del crimen|operativo policial)\b"),
    # Fotos representativas deben corresponder al asunto, no solo a la ciudad.
    (r"\b(?:panteones?|cementerios?|camposantos?)\b",
     r"\b(?:panteones?|cementerios?|camposantos?|tumbas?|sepulturas?|ofrendas? funerarias?)\b"),
    (r"\b(?:movilizaciones?|manifestaciones?|plantones?|concentraciones?)\b",
     r"\b(?:movilizaciones?|manifestaciones?|plantones?|concentraciones?|protestas?|marchas?|bloqueos?|trafico|transito|vehicular|congestion|cierres? viales?|bicicletas?|ciclistas?|rodadas?|ecobici)\b"),
    (r"\bdel campo a tu colonia\b",
     r"\b(?:campo|mercados?|agricultura|productores?|verduras?|hortalizas?|cosecha|suelo de conservacion|venta directa|alimentos?)\b"),
    (r"\b(?:artz pedregal|antara)\b",
     r"\b(?:artz|antara|arquitectura|arquitectos?|centros? comerciales?|edificios?|construccion de edificios)\b"),
    # Visitar tumbas requiere contexto funerario, no actos políticos universitarios.
    (r"\b(?:visitan? panteones?|adornar tumbas|familias? visitan? panteones?)\b",
     r"\b(?:panteones?|cementerios?|tumbas?|sepulturas?|ofrendas? funerarias?)\b"),
    # Marchas anunciadas no se ilustran con vehículos de transporte público.
    (r"\bmarchas?\b.*\b(?:hoy|noviembre|bloqueos?|concentraciones?)\b",
     r"\b(?:manifestacion(?:es)?|protestas?|marchas?|bloqueos?|concentraciones?|movilizaciones?)\b"),
    # Una agresión letal no es una celebración ni una imagen genérica de rescate.
    (r"\b(?:ataque armado|balacera|asesina(?:n)?|asesinato)\b",
     r"\b(?:fiscalia|investigacion penal|justicia|ministerio publico|peritos?|escena del crimen|operativo policial)\b"),
    # Un tiroteo no se ilustra con una graduación o ceremonia policial.
    (r"\b(?:balead\w*|balear\w*|balean|baleo)\b",
     r"\b(?:fiscalia|investigacion penal|justicia|ministerio publico|peritos?|escena del crimen|operativo policial)\b"),
    # La captación de agua pluvial requiere sistemas de recolección, no gotas en plantas.
    (r"\b(?:captacion de agua de lluvia|cosecha de lluvia|recoleccion de agua pluvial)\b",
     r"\b(?:captacion|cosecha de lluvia|recoleccion|sistema pluvial|cisternas?|tinacos?|canaletas?|almacenamiento de agua|depositos? de agua|filtros? de agua)\b"),
    # Una detención en un reclusorio no se ilustra con una estación del Metro.
    (r"\breclusorio\b",
     r"\b(?:reclusorio|centro penitenciario|penitenciaria|prision|fiscalia|detencion|ministerio publico|operativo policial)\b"),
    # La búsqueda de desaparecidos no se ilustra con un monumento sin relación.
    (r"\b(?:busqueda de personas|personas desaparecidas)\b",
     r"\b(?:colectivos? de busqueda|personas desaparecidas|busqueda|fiscalia|familias? buscadoras?|protestas?|manifestaciones?)\b"),
    # Los datos de deuda pública requieren contexto económico o institucional.
    (r"\b(?:deuda de estados|deuda publica|deuda estatal)\b",
     r"\b(?:finanzas?|economia|presupuesto|deuda|bancos?|gobierno|auditoria|congreso)\b"),
    # La agenda de movilizaciones requiere una protesta o rodada, no bomberos.
    (r"\bagenda de (?:movilizaciones|marchas|bloqueos)\b",
     r"\b(?:manifestaciones?|protestas?|marchas?|bloqueos?|rodadas?|motocicletas?|motociclistas?|concentraciones?)\b"),
    # Un resumen de bloqueos y accidentes no se ilustra con edificios vacíos.
    (r"\bbloqueos?\b.*\b(?:accidentes?|manifestaciones?|hoy)\b",
     r"\b(?:bloqueos?|manifestaciones?|protestas?|trafico|transito|vialidad|accidentes?|vehicular)\b"),
    # Una noticia sanitaria sobre carne descompuesta no es turismo de Xochimilco.
    (r"\b(?:carne podrida|frigorifico|toneladas de carne)\b",
     r"\b(?:carne|frigorifico|carnicerias?|alimentos?|inspeccion sanitaria|refrigeracion)\b"),
    # Megarrodada sin el sufijo "del Terror" también exige motos.
    (r"\b(?:mega ?rodada|megarrodada)\b",
     r"\b(?:motos?|motocicletas?|motociclistas?|rodada)\b"),
    # Visitas a cementerios no son desfiles de Catrinas.
    (r"\bvisitas? a (?:cementerios?|panteones?|tumbas?)\b",
     r"\b(?:cementerios?|panteones?|tumbas?|sepulturas?|mausoleos?|ofrendas? funerarias?)\b"),
    # La cartelera de Día de Muertos no es la cafetería de un museo.
    (r"\b(?:actividades|conciertos?|shows?)\b.*\bdia de muertos\b|\bdia de muertos\b.*\b(?:actividades|conciertos?|shows?)\b",
     r"\b(?:conciertos?|musica|escenario|espectaculos?|ofrendas?|altares?|desfile|catrinas?|festival|dia de muertos|celebraciones?)\b"),
    # Un debate de salud y cuidados paliativos no es una calle cualquiera.
    (r"\b(?:derecho a morir|muerte digna)\b",
     r"\b(?:salud|hospital|medicina|cuidados paliativos|derechos|pacientes|bioetica|eutanasia)\b"),
    # Las casetas de acceso y peaje son infraestructura carretera, no estaciones de tren.
    (r"\b(?:casetas? de acceso|casetas? de peaje|trafico en (?:las )?casetas?)\b",
     r"\b(?:casetas?|peaje|autopistas?|carreteras?|plazas? de cobro|cuotas?)\b"),
    # Una nota sobre congestión en ciudades requiere tránsito vial, no trenes.
    (r"\bciudades?\b.*\b(?:mas|mayor) trafico\b",
     r"\b(?:trafico|vehicular|autos?|automoviles?|vehiculos?|congestion|congestionamiento|embotellamiento|transito)\b"),
    # Proyectos de Tren Ligero no se ilustran con vagones de líneas del Metro.
    (r"\btren ligero\b",
     r"\b(?:tren ligero|tranvia|ferrocarril ligero)\b"),
    # Una ampliación de ruta RTP requiere autobuses, no estaciones del Metro.
    (r"\brtp\b",
     r"\b(?:rtp|autobuses?|camiones?|transporte publico|bus)\b"),
    # Para crimen organizado, ni teatro ni graduaciones de policía o patrullas genéricas.
    (r"\b(?:grupos? criminales?|organizaciones? criminales?|crimen organizado)\b",
     r"\b(?:fiscalia|investigacion penal|crimen organizado|operativo policial|central de abasto)\b"),
    # Los precios de gasolina necesitan imagen de combustible o estación de servicio.
    (r"\b(?:precios? de (?:la )?gasolina|gasolineras?|combustibles?)\b",
     r"\b(?:gasolina|gasolineras?|combustibles?|estacion de servicio|surtidor|bomba de gasolina)\b"),
    # Una ley de seguridad vial no se ilustra con el pago de pasaje en Metrobús.
    (r"\b(?:ley de movilidad|tragedias viales)\b",
     r"\b(?:seguridad vial|transito|vialidad|trafico|vehicular|vehiculos?|automoviles?|carreteras?|cruces? peatonales?|peatones?|ciclistas?|siniestros? viales?|accidentes? viales?|senales? de transito)\b"),
    # Un edificio turístico no representa retrasos de vuelos ni operaciones aéreas.
    (r"\b(?:aeropuerto|vuelos? demorados?|vuelos? retrasados?)\b",
     r"\b(?:aeropuerto|aeronautica|aviones?|aeronaves?|vuelos?|terminal aerea|pista de aterrizaje)\b"),
    # Una casa del Centro Histórico no ilustra puentes peatonales ni estafas viales.
    (r"\b(?:puentes? peatonales?|pasarelas? peatonales?)\b",
     r"\b(?:puentes?|pasarelas?|pasos? peatonales?|cruces? elevados?)\b"),
    (r"\bmontachoques\b",
     r"\b(?:choques?|automoviles?|autos?|vehiculos?|trafico|transito|seguridad vial)\b"),
    # La captación de lluvia no es una imagen de pronóstico, frío o viento.
    (r"\b(?:temperaturas?|clima|pronostico|rachas de viento|mananas frias|frente frio)\b",
     r"\b(?:clima|pronostico|meteorologia|temperatura|viento|frio|nubes?|cielo|tormenta|neblina)\b"),
    # Los choques y derrapes de motos, camiones o vehículos requieren contexto
    # de tránsito; compartir alcaldía no vuelve pertinente una iglesia.
    (r"\b(?:accident\w*|choc\w*|choqu\w*|colisi\w*|volcadur\w*|derrap\w*)\b.*\b(?:motociclist\w*|motociclet\w*|moto\w*|camion\w*|vehicul\w*|automovil\w*)\b|"
     r"\b(?:motociclist\w*|motociclet\w*|moto\w*|camion\w*|vehicul\w*|automovil\w*)\b.*\b(?:accident\w*|choc\w*|choqu\w*|colisi\w*|volcadur\w*|derrap\w*)\b",
     r"\b(?:motociclet\w*|motociclist\w*|motos?|camion\w*|vehicul\w*|automovil\w*|vehicular|trafico|transito|vialidad|carretera|avenida|cruce peatonal)\b"),
    # Atropellamientos y muertes viales no se ilustran con iglesias o plazas.
    (r"\b(?:atropell\w*|arroll\w*)\b",
     r"\b(?:microbus|autobus|vehiculos?|vehicular|trafico|transito|vialidad|peatones?|cruce peatonal|automoviles?|autos?|coches?|atropellamientos?)\b"),
    # Los operativos de vigilancia no se ilustran con museos sin relación.
    (r"\bpolicias?\b.*\b(?:cuidan|vigilan|operativo|despliegan)\b",
     r"\b(?:policias?|patrullas?|vigilancia|seguridad|operativo|agentes?)\b"),
    # Para detenciones de personas, una plaza de la misma alcaldía no basta.
    # En un operativo del Gran Premio también es pertinente el autódromo.
    (r"^(?!.*\b(?:gp de mexico|gran premio|formula 1|autodromo)\b).*\b(?:detienen|arrestan|capturan|aprehenden)\s+a\s+(?:\d+|un|una|dos|tres|cuatro|cinco|seis|personas|hombres|mujeres)\b",
     r"\b(?:fiscalia|justicia|tribunal|detencion|investigacion penal|operativo policial|ministerio publico)\b"),
    (r"\bempleo de mujeres\b",
     r"\b(?:empleo|trabajo|mujeres|oficinas?|economia|trabajadoras?)\b"),
    (r"\bmorena\b.*\b(?:militantes|reunio|asamblea)\b",
     r"\b(?:morena|militantes|asamblea|reunion|partido politico|politica)\b"),
    (r"\b(?:asamblea comunitaria|autoridades auxiliares)\b",
     r"\b(?:asamblea|comunitaria|vecinos|cabildo|reunion|autoridades auxiliares)\b"),
    (r"\b(?:juan atkins|pionero del techno)\b",
     r"\b(?:techno|musica|dj|vinilos?|discos?|escenario|concierto|musico|productor musical)\b"),
    # Sloopy y Lobito son los perros del caso de envenenamiento en Xochimilco.
    (r"\b(?:sloopy|lobito)\b",
     r"\b(?:perros?|caninos?|mascotas?|veterinaria)\b"),
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
    (r"\b(?:conciertos?|u2|bono)\b",
     r"\b(?:musica|concierto|escenario|bandas?|cantante|u2|guitarra|rock)\b"),
    (r"\blicencia de conducir\b",
     r"\b(?:licencia|conducir|vehiculos?|automoviles?|autos?|transito|tramite)\b"),
    (r"\bcalidad del aire\b",
     r"\b(?:contaminacion|smog|atmosfera|emisiones|contaminantes|calidad del aire|medicion ambiental)\b"),

    # Un ataque de jauría necesita perros visibles; fauna genérica no basta.
    (r"\b(?:jauria|perros? atacan?|ataque de perros?)\b",
     r"\b(?:perros?|caninos?|mascotas?|veterinaria)\b"),
    # Un socavón exige contexto de pavimento o infraestructura dañada, no edificios turísticos.
    (r"\b(?:socavon(?:es)?|hundimiento(?:s)?|bache(?:s)?|colapso de (?:la )?(?:calle|pavimento|asfalto))\b",
     r"\b(?:socavon(?:es)?|hundimiento(?:s)?|bache(?:s)?|pavimento|asfalto|drenaje|alcantarilla|excavacion|obra vial)\b"),
    # Una caseta vandalizada requiere un acceso o puesto de vigilancia.
    (r"\bcaseta(?:s)? de (?:un )?(?:inmueble|vigilancia|acceso)\b",
     r"\b(?:caseta(?:s)?|vigilancia|guardia|control de acceso|porteria|entrada vigilada|seguridad privada)\b"),
    # Las líneas del Cablebús no se ilustran con estaciones de otra línea.
    (r"\b(?:cablebus|teleferico)\b",
     r"\b(?:cablebus|teleferico|cabinas?)\b"),
    # Un concierto necesita contexto musical o de su sede, no un monumento ajeno.
    (r"\b(?:karol g|setlist|conciertos?)\b",
     r"\b(?:karol g|setlist|conciertos?|escenario|musica|cantantes?|estadio|auditorio|festival|guitarra|banda)\b"),
    # Los verificentros requieren contexto de revisión vehicular.
    (r"\b(?:verificentros?|verificacion vehicular)\b",
     r"\b(?:verificentros?|verificacion vehicular|centro de verificacion|emisiones|vehiculos?|autos?|automoviles?)\b"),
    # Un foro metropolitano necesita contexto cívico o de planeación urbana.
    (r"\b(?:foro de pozmvm|pozmvm|foro urbano|cancelan foro)\b",
     r"\b(?:planeacion urbana|urbanismo|pozmvm|politica|partido|congreso|asamblea|foro urbano|foro metropolitano)\b"),
    # Los fraudes por internet requieren contexto digital, no una ceremonia policial.
    (r"\b(?:fraudes? en compras por internet|fraude cibernetico|policia cibernetica)\b",
     r"\b(?:ciberseguridad|internet|computadora|tecnologia|fraude|phishing|seguridad digital|redes|dispositivo)\b"),
    # Las iniciativas de reciclaje y lectura necesitan papel o contexto educativo.
    (r"\b(?:recicla para leer|reciclaje de papel|papel reciclado)\b",
     r"\b(?:papel|reciclaje|recicla|libros|lectura|biblioteca|escuela|educacion)\b"),
    # La detección de fugas de agua requiere infraestructura hidráulica.
    (r"\b(?:fugas? de agua|deteccion de fugas|detectar fugas de agua)\b",
     r"\b(?:agua|fuga|tuberias?|drenaje|sistema hidraulico|acueducto|cisterna|sensor|red hidraulica)\b"),
    # Las notas de sarampión y otras enfermedades requieren contexto sanitario.
    (r"\b(?:sarampion|dengue|influenza|covid|vacunacion|contagios?)\b",
     r"\b(?:sarampion|dengue|influenza|covid|vacunacion|vacunas?|centro de salud|hospital|clinica|medicos?|personal de salud|enfermeria|laboratorio|epidemiologia|virus)\b"),
    # Los ataques a automóviles requieren contexto vial o de vehículos.
    (r"\b(?:lanzan piedras contra autos?|ataques? contra autos?|piedras contra vehiculos?)\b",
     r"\b(?:autos?|vehiculos?|carretera|periferico|trafico|transito|vialidad|cruce)\b"),
    # Las amenazas con arma en inmuebles no se ilustran con bomberos o graduaciones.
    (r"\b(?:amenazas? con arma de fuego|amenaza con arma|irrumpen en unidad habitacional)\b",
     r"\b(?:arma|repartidor|motocicleta|unidad habitacional|caseta|guardia|vigilancia|escena del crimen|investigacion penal|operativo policial)\b"),
    # Los bloqueos anunciados por repartidores requieren protesta, reparto o vialidad.
    (r"\b(?:repartidores? anuncian? bloqueos?|repartidores? bloquean? zona|bloqueos? de repartidores?)\b",
     r"\b(?:bloqueo|protesta|manifestacion|repartidor|motocicleta|trafico|transito|vialidad|calle)\b"),
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
    # Admitir categorías temáticas solo cuando el descriptor coincide con la noticia.
    music_story = bool(re.search(r"\briff\b", headline))
    music_photo = bool(re.search(
        r"\b(?:musica|conciertos?|guitarras?|bandas?|escenarios?|rock|cantantes?|festivales?|auditorios?|estadios?)\b",
        context,
    ))
    weather_story = bool(re.search(r"\brachas?\b", headline))
    weather_photo = bool(re.search(
        r"\b(?:viento|rachas?|meteorologia|clima|nubes?|cielo nublado|tormenta|temperatura|frio)\b",
        context,
    ))
    animal_story = bool(re.search(
        r"\b(?:jauria|sloopy|lobito|perros?|perritos?|mascotas?)\b", headline
    ))
    animal_photo = bool(re.search(r"\b(?:perros?|caninos?|mascotas?)\b", context))
    themed_category = (
        (photo_category == "Cultura" and music_story and music_photo)
        or (photo_category == "Medio Ambiente" and (
            (weather_story and weather_photo) or (animal_story and animal_photo)
        ))
    )
    # Una categoría distinta no basta por sí sola para considerar pertinente una foto.
    if photo_category not in (category, "CDMX", "Alcaldías") and not themed_category:
        return -10000
    # Una convocatoria de marcha del IMSS no se ilustra con transporte público.
    if ("imss" in headline
            and re.search(r"\b(?:marchas?|protestas?|plantones?|movilizaciones?)\b", headline)
            and not re.search(r"\b(?:manifestantes?|protestas?|marchas?|plantones?|movilizaciones?|concentraciones?|sindicatos?|trabajadores?)\b", context)):
        return -10000
    # Las multas a bicicletas eléctricas o scooters no se ilustran con el logo EcoBici.
    if (re.search(r"\b(?:scooters?|monopatines?|bicicletas? electricas?)\b", headline)
            and "ecobici" not in headline
            and re.search(r"\becobici\w*\b", context)):
        return -10000
    # Una Catrina monumental no equivale a un desfile de disfraces.
    if (re.search(r"\bcatrina monumental\b", headline)
            and not re.search(r"\b(?:monumental|monumento|escultura|instalacion)\b", context)):
        return -10000
    # Los retrasos de Metro no se representan con obras antiguas sin relación.
    if (category == "Metro"
            and re.search(r"\b(?:retrasos?|demoras?|caos|avances?|operan|servicio)\b", headline)
            and not re.search(r"\b(?:obras?|construccion|remodelacion)\b", headline)
            and re.search(r"\b(?:obras?|construccion|remodelacion)\b", topic)):
        return -10000
    # El título y el descriptor deben compartir el asunto real de la nota.
    for headline_pattern, photo_pattern in STRICT_PHOTO_TOPICS:
        if re.search(headline_pattern, headline) and not re.search(photo_pattern, context):
            return -10000
    # Una protesta sin componente ciclista no se ilustra con estaciones de EcoBici.
    # Sí conservar imágenes de rodadas cuando el titular las menciona expresamente.
    if (re.search(r"\b(?:movilizaciones?|manifestaciones?|plantones?|concentraciones?)\b", headline)
            and not re.search(r"\b(?:rodadas?|ciclistas?|bicicletas?|ecobici)\b", headline)
            and re.search(r"\b(?:ecobici\w*|bicicletas?|ciclistas?|rodadas?)\b", topic)
            and not re.search(r"\b(?:protestas?|manifestaciones?|marchas?|bloqueos?|plantones?)\b", topic)):
        return -10000
    # Un choque vial no ocurrió en un autódromo solo por compartir alcaldía.
    if (re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and not re.search(r"\b(?:autodromo|formula 1|f1|gran premio|carrera|circuito|bottas|verstappen|hamilton|alonso|checo|antonelli)\b", headline)
            and re.search(r"\b(?:autodromo|formula 1|gran premio|pista de carreras)\b", topic)):
        return -10000
    # Choques de autos o motocicletas no se ilustran con trolebuses ni trenes.
    if (re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and re.search(r"\b(?:autos?|automovil\w*|vehicul\w*|motociclet\w*|motociclist\w*|motos?)\b", headline)
            and not re.search(r"\b(?:trolebus|metrobus|tren ligero|metro)\b", headline)
            and re.search(r"\b(?:trolebus|metrobus|tren ligero|estacion del metro)\b", topic)):
        return -10000
    # En choques de motos y autos, una carretera histórica o calle turística
    # no basta: se exige tráfico, vehículos o el lugar exacto de la alcaldía.
    borough=_photo_fold(article.get("borough"))
    if (re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and re.search(r"\b(?:autos?|automovil\w*|motociclet\w*|motociclist\w*|motos?)\b", headline)
            and not (borough and borough in topic)
            and not re.search(r"\b(?:motociclet\w*|motociclist\w*|motos?|autos?|automovil\w*|vehicular|trafico|transito|vialidad|choque)\b", topic)):
        return -10000
    # Una detención no se ilustra con entrega de patrullas o policía dirigiendo tráfico.
    if re.search(r"\b(?:detienen|detenido\w*|arrestan|capturan|aprehenden)\b", headline):
        if re.search(r"\b(?:entrega (?:de )?(?:nuevas? )?patrullas|nuevas? patrullas|graduacion|ceremonia|controlando el semaforo|policia de transito)\b", topic):
            return -10000
    # Un corte de agua no se ilustra con elementos decorativos de un parque.
    if re.search(r"\b(?:sin agua|falta de agua|corte de agua|suspension de agua)\b", headline):
        if re.search(r"\b(?:bosque de chapultepec|parque|jardin|fuente ornamental)\b", topic):
            return -10000
    # Patrullas compradas para otra alcaldía no documentan una detención.
    if (re.search(r"\b(?:detienen|detenido\w*|arrestan|capturan|aprehenden)\b", headline)
            and re.search(r"\b(?:adquisicion|compra|presentacion|entrega)\b.*\bpatrullas?\b", topic)):
        return -10000
    # Una ceremonia policial o un desfile no representa un asesinato o ataque.
    if (re.search(r"\b(?:asesina(?:n)?|asesinato|ataque armado|balacera|matan|homicidio|balead\w*|balear\w*|balean)\b", headline)
            and re.search(r"\b(?:graduacion|ceremonia|adquisicion|entrega de patrullas|proteccion civil|desfile|catrinas?)\b", topic)):
        return -10000
    # Una avenida turística de otra zona no ilustra un choque local.
    borough=_photo_fold(article.get("borough"))
    if (borough and re.search(r"\b(?:accident\w*|choqu\w*|choc\w*|colisi\w*|volcadur\w*|derrap\w*)\b", headline)
            and re.search(r"\b(?:autos?|automovil\w*|motociclet\w*|motociclist\w*|motos?)\b", headline)
            and re.search(r"\b(?:avenida|calle|paseo|centro historico|torre latinoamericana)\b", topic)
            and borough not in topic
            and not re.search(r"\b(?:trafico|transito|vehicular|vialidad|motos?|motociclet\w*|autos?|automovil\w*)\b", topic)):
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
        if not re.search(r"\b(?:bici|bicicletas?|ciclistas?|ciclovias?|ecobici\w*|cicloton)\b", context):
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
    # Los titulares pueden enumerar varias líneas: aceptar cualquiera de ellas,
    # pero nunca ilustrar la nota con una línea que no aparece en esa lista.
    metro_wanted_lines=set()
    metro_photo_line=None
    if category=="Metro":
        wanted=re.search(
            r"\b(?:lineas?|lines?)\s+((?:[0-9]{1,2}|a|b)(?:\s*(?:,|y)\s*(?:[0-9]{1,2}|a|b))*)",
            headline,
        )
        if wanted:
            metro_wanted_lines=set(
                re.findall(r"\b(?:[0-9]{1,2}|a|b)\b",wanted.group(1))
            )
        shown=re.search(r"\b(?:linea|line) ([0-9]{1,2}|a|b)\b",topic)
        metro_photo_line=shown.group(1) if shown else None
        if (metro_wanted_lines and metro_photo_line
                and metro_photo_line not in metro_wanted_lines):
            return -10000
    if re.search(r"\b(?:cablebus|teleferico)\b", headline):
        wanted_lines = set(re.findall(r"\blineas? ([0-9]{1,2})\b", headline))
        shown_lines = set(re.findall(r"\blinea ([0-9]{1,2})\b", topic))
        if wanted_lines and shown_lines and not wanted_lines.intersection(shown_lines):
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
    if category=="Metro" and metro_photo_line in metro_wanted_lines:
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
