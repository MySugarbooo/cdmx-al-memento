"""Genera dieciséis guías editoriales estáticas y accesibles desde datos acreditados.

Se preservan todas las alcaldías sin destacar una como predeterminada. El
contenido de contexto procede de las historias locales del proyecto, las
fotografías se atribuyen a Commons y los consejos se redactan por zona.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "descubre"
STORIES = ROOT / "assets/alcaldias/historias.json"
PHOTOS = ROOT / "assets/alcaldias/fotos.json"
SITE = "https://cdmx-al-memento.pages.dev"
DATE = "2026-10-13"

# Cada texto es propio de la zona: no se mezclan rutas ni se inventan horarios.
NOTES = {
 "alvaro-obregon": (
  "San Ángel invita a conocer calles y plazas que conservan la escala de un pueblo anterior a las grandes avenidas. La visita es una oportunidad para observar el patrimonio sin apurarse.",
  "Plaza San Jacinto sirve como referencia para explorar el centro de San Ángel. Busca detalles de la arquitectura y respeta las actividades de los vecinos.",
  "Museo de El Carmen y Chimalistac ofrecen otras capas de historia, pero conviene confirmar los horarios del museo y elegir las distancias antes de caminar.",
  "Los barrios históricos y las áreas al poniente de esta alcaldía requieren recorridos distintos. No los consideres una sola ruta a pie."
 ),
 "azcapotzalco": (
  "El centro de Azcapotzalco permite observar el encuentro entre antiguos barrios, plazas y una ciudad transformada por la industria y el transporte.",
  "Comienza en el centro histórico y dedica tiempo al Jardín Hidalgo. Son referencias útiles para reconocer la vida cotidiana de la demarcación.",
  "Las parroquias y los barrios originarios conservan memoria de distintas épocas. Comprueba cuáles templos permiten visitas y respeta sus actividades.",
  "La visita se disfruta mejor con un trayecto corto. Comprueba la ruta de regreso antes de entrar a calles o colonias que no conoces."
 ),
 "benito-juarez": (
  "Benito Juárez muestra cómo parques, antiguas poblaciones y colonias urbanas pueden convivir en un mismo territorio.",
  "Parque Hundido ofrece una parada verde dentro de la ciudad; observa la topografía y la relación del parque con las avenidas.",
  "Mixcoac y Xoco son referencias de la antigua organización de pueblos. Conviene visitarlos como recorridos distintos para prestar atención a su historia.",
  "Si atraviesas avenidas de alto tránsito, utiliza cruces señalizados. Verifica accesos a parques y distancias antes de salir."
 ),
 "coyoacan": (
  "Coyoacán conserva plazas y calles relacionadas con una larga historia cultural. No hace falta intentar visitar todos los museos el mismo día.",
  "Comienza en Jardín Centenario y observa cómo la plaza articula la circulación de habitantes, visitantes y comercio local.",
  "La Parroquia de San Juan Bautista y La Conchita muestran entornos religiosos y barriales diferentes. Respeta las actividades comunitarias.",
  "Los museos más populares pueden requerir reservar o comprar entrada antes de llegar; consulta siempre sus sitios oficiales."
 ),
 "cuajimalpa": (
  "Cuajimalpa combina pueblos de montaña, paisajes boscosos y corredores de urbanización reciente que conviene explorar por separado.",
  "Recorre el centro de Cuajimalpa para acercarte a la vida local y reconocer el contraste con el desarrollo del poniente.",
  "Desierto de los Leones es una salida de naturaleza distinta de una visita urbana. Consulta senderos habilitados y condiciones ambientales; San Pablo Chimalpa representa otro entorno comunitario.",
  "No supongas que los tres sitios son caminables entre sí. Prepara traslados, abrigo y calzado apropiados."
 ),
 "cuauhtemoc": (
  "Cuauhtémoc reúne vestigios de México-Tenochtitlan, espacios virreinales y colonias modernas. Conviene distribuir la visita en varias jornadas.",
  "El Centro Histórico permite observar el trazado de la antigua capital y edificios de distintas etapas alrededor del Zócalo.",
  "Bellas Artes y Tlatelolco explican otras historias: patrimonio artístico y memoria de la ciudad. Cada lugar merece tiempo suficiente.",
  "Para entrar a museos comprueba el calendario del recinto. Entre avenidas y plazas hay gran afluencia peatonal."
 ),
 "gustavo-a-madero": (
  "La Villa y el Tepeyac dan identidad histórica al norte de la ciudad mediante peregrinaciones, barrios y paisaje.",
  "La Basílica de Guadalupe es un espacio religioso activo; consulta sus indicaciones y respeta celebraciones y peregrinos.",
  "El Cerro del Tepeyac y Sierra de Guadalupe son contextos naturales distintos. Revisa accesos oficiales y evita senderos no autorizados.",
  "La afluencia aumenta mucho en ciertas fechas religiosas. Revisa transporte y restricciones viales antes de acudir."
 ),
 "iztacalco": (
  "Iztacalco conserva una memoria lacustre de canales, islotes y barrios originarios que sobreviven en nombres y tradiciones.",
  "El Templo de San Matías sirve como punto de referencia para imaginar el antiguo pueblo y su transformación urbana.",
  "Los barrios tradicionales y el antiguo canal de La Viga muestran cómo el agua marcó la forma de la ciudad. El canal ya no es un corredor navegable continuo.",
  "Esta exploración se aprecia más como recorrido histórico de barrio que como turismo de grandes monumentos."
 ),
 "iztapalapa": (
  "Iztapalapa combina cerros, zonas arqueológicas y tradiciones comunitarias conocidas en toda la capital.",
  "Cerro de la Estrella es una referencia natural y cultural. Verifica condiciones del parque y qué áreas están abiertas.",
  "Santuario de La Cuevita y los ocho barrios históricos muestran memorias y prácticas comunitarias; no son únicamente escenarios turísticos.",
  "Si deseas asistir a una celebración, consulta las reglas de movilidad y protege el paso de habitantes y participantes."
 ),
 "magdalena-contreras": (
  "La Magdalena Contreras permite comprender el papel del agua, los bosques y los pueblos en el surponiente de la capital.",
  "Los Dinamos y el río Magdalena son referencias naturales. Los senderos no tienen siempre la misma dificultad ni acceso.",
  "La Magdalena Atlitic y San Nicolás Totolapan recuerdan la presencia de comunidades vinculadas al entorno forestal.",
  "Para caminar en el bosque, consulta primero accesos, clima, reglas ambientales y tiempo de regreso. Los pueblos requieren otro recorrido."
 ),
 "miguel-hidalgo": (
  "El paisaje de Chapultepec y la historia de Tacubaya ofrecen distintas maneras de leer el poniente de CDMX.",
  "Bosque de Chapultepec es muy extenso: elige sección y senderos antes de intentar recorrer varios museos.",
  "El Castillo de Chapultepec y el antiguo pueblo de Tacubaya cuentan épocas distintas y merecen visitas separadas.",
  "Consulta entradas y horarios oficiales, especialmente si deseas entrar al castillo o a instituciones culturales."
 ),
 "milpa-alta": (
  "Milpa Alta conserva pueblos originarios y paisajes productivos que forman parte esencial de la diversidad de la capital.",
  "Villa Milpa Alta permite acercarse al centro cívico y a la organización de una alcaldía con amplia vida comunitaria.",
  "San Pablo Oztotepec y los campos de nopal evocan prácticas locales. Los cultivos son propiedad productiva y no sitios de libre acceso.",
  "Los traslados pueden ser largos. Respeta parcelas, verifica transporte y confirma calendarios de celebraciones."
 ),
 "tlahuac": (
  "Tláhuac conecta pueblos originarios con la memoria de los antiguos lagos del sureste del valle.",
  "San Pedro Tláhuac sirve como punto de partida para comprender cómo se organiza el territorio de sus pueblos.",
  "San Andrés Mixquic y los canales son referencias culturales y ambientales; las chinampas son espacios de trabajo, no decorados turísticos.",
  "En fiestas tradicionales confirma horarios y rutas oficiales. Nunca ingreses a zonas productivas privadas sin permiso."
 ),
 "tlalpan": (
  "Tlalpan reúne arqueología, centros de antiguos pueblos y una zona montañosa que requiere otra preparación.",
  "Cuicuilco permite apreciar una de las historias más tempranas del poblamiento de la cuenca. Consulta al INAH antes de visitarlo.",
  "El centro histórico de Tlalpan y el Ajusco son dos experiencias muy distintas: una caminata urbana y una excursión de montaña.",
  "Separa recorridos para evitar traslados excesivos; en el Ajusco revisa clima, senderos autorizados y equipo necesario."
 ),
 "venustiano-carranza": (
  "Mercados históricos y edificios institucionales ayudan a comprender la identidad comercial y urbana de Venustiano Carranza.",
  "El Palacio de Lecumberri es una referencia de la historia institucional de la capital. Comprueba su modalidad de acceso.",
  "La Merced y Jamaica son mercados que siguen funcionando para sus comunidades; camina sin bloquear las zonas de carga o el comercio.",
  "Los mercados pueden estar llenos: revisa accesos, horarios y conexiones de transporte antes de salir."
 ),
 "xochimilco": (
  "Xochimilco se entiende mejor a través de sus canales y chinampas, pero también conserva patrimonio religioso y vida de pueblo.",
  "Los canales y trajineras permiten conocer un paisaje cultural que necesita protección. Revisa embarcaderos autorizados.",
  "Las chinampas son espacios agrícolas y de conservación. El Templo de San Bernardino revela otra parte de la historia local.",
  "Confirma tarifas y reglas antes de navegar, no arrojes residuos al agua y respeta el trabajo de agricultores."
 )
}


def e(value):
    return html.escape(str(value or ""), quote=True)


def build():
    histories=json.loads(STORIES.read_text(encoding="utf-8"))["boroughs"]
    photos={p["slug"]:p for p in json.loads(PHOTOS.read_text(encoding="utf-8"))["photos"]}
    slugs=set()
    DEST.mkdir(parents=True, exist_ok=True)
    for item in histories:
        slug=item["slug"]
        if slug not in NOTES or slug in slugs:
            raise ValueError("Falta una nota única o está duplicada: "+slug)
        slugs.add(slug)
        name=item["name"]
        intro,point1,point2,advice=NOTES[slug]
        photo=photos.get(slug)
        source_list="".join('<li><a href="'+e(s["url"])+'" target="_blank" rel="noopener noreferrer">'+e(s.get("label",s["url"]))+' ↗</a></li>' for s in item.get("sources",[]))
        legend=('<figure class="explore-photo"><img src="/assets/alcaldias/'+e(slug)+'.jpg" width="850" height="540" alt="'+e(photo["caption"])+'" loading="lazy" decoding="async">'
                '<figcaption>'+e(photo["caption"])+' · '+e(photo["author"])+' · '+e(photo["license"])+' · '
                '<a href="'+e(photo["source"])+'" target="_blank" rel="noopener noreferrer">Ver licencia y fotografía original ↗</a></figcaption></figure>') if photo else ""
        places="".join('<li><strong>'+e(place)+'</strong> · Punto cultural o histórico para investigar antes de acudir.</li>' for place in item["landmarks"])
        article={
            "@context":"https://schema.org","@type":"Article",
            "headline":"Qué conocer en "+name+": historia y rutas culturales",
            "datePublished":DATE,"dateModified":DATE,"inLanguage":"es-MX",
            "author":{"@type":"Organization","name":"CDMX AL MEMENTO"},
            "publisher":{"@type":"Organization","name":"CDMX AL MEMENTO"},
            "mainEntityOfPage":SITE+"/descubre/"+slug+".html"
        }
        title="Qué conocer en "+name+" | CDMX AL MEMENTO"
        desc="Guía cultural e histórica de "+name+": "+", ".join(item["landmarks"])+". Lugares, consejos y fuentes."
        content=(
            '<!doctype html><html lang="es-MX"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+e(title)+'</title><meta name="description" content="'+e(desc)+'">'
            '<meta name="theme-color" content="#141623"><link rel="canonical" href="'+SITE+'/descubre/'+e(slug)+'.html">'
            '<link rel="icon" type="image/svg+xml" href="/favicon.svg">'
            '<link rel="stylesheet" href="/styles.css?v=20261013-cercadeti">'
            '<link rel="stylesheet" href="/assets/portal.css?v=1">'
            '<link rel="stylesheet" href="/assets/explora.css?v=1">'
            '<link rel="stylesheet" href="/assets/clima-ticker.css?v=4">'
            '<script type="application/ld+json">'+json.dumps(article,ensure_ascii=False).replace("<","\\u003c")+'</script>'
            '</head><body><a class="skip" href="#contenido">Saltar al contenido</a>'
            '<div id="weather-ribbon" class="weather-ribbon" role="region" aria-label="Clima estimado por alcaldía">'
            '<a class="weather-ribbon__brand" href="/cerca/">🌸 CLIMA</a>'
            '<div class="weather-ribbon__window"><div class="weather-ribbon__track" id="weather-ribbon-track">'
            '<div class="weather-ribbon__set"><span class="weather-chip">🌤️ Consultando el clima…</span></div></div></div>'
            '<span class="weather-sr-only" id="weather-screen-reader" role="status" aria-live="polite"></span></div>'
            '<header><div class="wrap"><div class="top"><a class="logo" href="/">CDMX <span>AL MEMENTO</span></a></div>'
            '<nav><a href="/">Noticias</a><a href="/descubre/">16 alcaldías</a><a href="/agenda/">Agenda</a>'
            '<a href="/negocios/">Comercios</a><a href="/herramientas/">Herramientas</a><a href="/mapa/">Mapa</a></nav></div></header>'
            '<main id="contenido" class="wrap"><nav class="explore-breadcrumb">'
            '<a href="/">Inicio</a> › <a href="/descubre/">Descubre</a> › '+e(name)+'</nav>'
            '<section class="explore-hero"><p class="eyebrow">GUÍA CULTURAL · 16 ALCALDÍAS</p>'
            '<h1>Qué conocer en '+e(name)+': historia y lugares</h1><p>'+e(intro)+'</p></section>'
            '<div class="explore-cols"><article class="explore-article">'
            '<p class="explore-tag">GUÍA EDITORIAL · OCTUBRE DE 2026</p>'+legend
            '<h2>Historia e identidad de '+e(name)+'</h2>'
            +''.join('<p>'+e(paragraph)+'</p>' for paragraph in item["history"])+
            '<h2>Tres maneras de explorar el territorio</h2><p>'+e(point1)+'</p><p>'+e(point2)+'</p>'
            '<ul>'+places+'</ul><h2>Cómo planear tu visita</h2><p>'+e(advice)+'</p>'
            '<p>No todas las referencias de esta guía están cerca entre sí: usa el mapa para calcular distancias reales. '
            'Los horarios de entrada, los cierres, la disponibilidad de servicios y los precios pueden cambiar. '
            'Verifícalos en la institución responsable antes de salir.</p>'
            '<h2>Un recorrido respetuoso</h2><p>El patrimonio de cada alcaldía también es el espacio cotidiano '
            'de vecinos, comerciantes y comunidades. Evita entrar a terrenos agrícolas sin permiso, respeta '
            'las ceremonias y deposita los residuos en los lugares habilitados. Para visitar áreas '
            'naturales, comprueba el clima y los senderos autorizados.</p>'
            '<h2>Fuentes y contexto</h2><p>Esta guía sintetiza fuentes públicas y ofrece recomendaciones '
            'para planear una visita; no confirma horarios ni inventa eventos.</p>'
            '<ul>'+source_list+
            '<li><a href="https://cartelera.cdmx.gob.mx/" target="_blank" rel="noopener noreferrer">Cartelera oficial CDMX ↗</a></li></ul>'
            '</article><aside class="explore-side"><p class="explore-tag">MÁS INFORMACIÓN</p><h2>'+e(name)+'</h2>'
            '<ul class="explore-linklist"><li><a href="/alcaldias/?alcaldia='+e(name)+'#noticias-alcaldia">Noticias locales ↗</a></li>'
            '<li><a href="/agenda/">Agenda y eventos ↗</a></li>'
            '<li><a href="/mapa/">Mapa interactivo ↗</a></li>'
            '<li><a href="/negocios/">Directorio comercial ↗</a></li>'
            '<li><a href="/descubre/">Explorar las 16 alcaldías ↗</a></li></ul>'
            '<p class="explore-note">Todas las alcaldías cuentan con el mismo espacio editorial, '
            'sin posiciones pagadas entre las guías.</p></aside></div></main>'
            '<footer><div class="wrap">CDMX AL MEMENTO · '
            '<a href="/privacidad.html">Privacidad</a> · <a href="/politica-editorial.html">Política editorial</a> · '
            '<a href="/publicidad/">Publicidad y transparencia</a></div></footer>'
            '<script defer src="/assets/clima-ticker.js?v=4"></script></body></html>'
        )
        target=DEST/(slug+".html")
        if not target.exists() or target.read_text(encoding="utf-8")!=content:
            target.write_text(content,encoding="utf-8")
    if len(slugs)!=16:
        raise ValueError("Se esperaban exactamente 16 alcaldías")
    print("Guías creadas o revisadas:",len(slugs))


if __name__=="__main__":
    build()
