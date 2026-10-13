# CDMX AL MEMENTO

Portal de titulares de noticias de Ciudad de México, alojado en Cloudflare Pages:
https://cdmx-al-memento.pages.dev/

## Nuevas secciones

- **Noticias recientes**: `news.json`, actualizado por GitHub Actions.
- **Archivo mensual**: `/archivo/`, con JSON por mes y `/archivo/meses.json`. Los titulares se conservan **365 días**; el actualizador elimina los registros vencidos, incluso si todavía hay noticias más recientes en ese mismo mes.
- **16 alcaldías**: `/alcaldias/`, priorizando La Magdalena Contreras y Álvaro Obregón. Una noticia solo se asigna a una alcaldía si el nombre figura claramente en su titular.
- **Fecha y hora de publicación**: `published_at` es la hora extraída del RSS en UTC, visualizada en la zona `America/Mexico_City`. Nunca se inventa la hora de los registros históricos.
- **Reportes automáticos**: `/reportes/`, con depuración anual.
- **Diseño**: acentos de rosa mexicano claro sobre fondo oscuro.

## Actualización programada

El workflow `.github/workflows/news.yml` ejecuta pruebas y `python update_news.py` aproximadamente **cada hora** (minuto 17 UTC), sujeto a los retrasos o interrupciones ocasionales de GitHub Actions. Lee RSS de Google News, recopila los temas de la capital y hace búsquedas adicionales para las 16 alcaldías. Fusiona las noticias nuevas con el archivo de meses anteriores, comprueba fechas y elimina los archivos mensuales que quedan vacíos. No almacena textos íntegros de artículos.

Para forzar la actualización: GitHub → Actions → **Actualizar noticias CDMX AL MEMENTO** → Run workflow.

## Editorial y privacidad

Los titulares son recopilaciones de medios externos, sin verificación periodística independiente. **La hora es de publicación, no del suceso**. La alcaldía es una coincidencia en el titular, no una geolocalización confirmada. Cuando falta información de hora o ubicación, se indica expresamente. Las fotos son de archivo, no fotos de los hechos, y se atribuyen en `/creditos-fotograficos.html`.

Google AdSense utiliza el identificador `ca-pub-6521969406386261`; instalar el script no implica aprobación de la cuenta ni del dominio.

**Importante**: aunque las noticias caducadas se eliminan del sitio público y de la rama activa, el historial previo de commits en GitHub puede contener versiones anteriores. No se purga automáticamente ese historial.


## Historias y fotografías de las 16 alcaldías

En la página principal, la columna derecha de alcaldías enlaza a
\`/alcaldias/?alcaldia=NOMBRE#noticias-alcaldia\`. La antigua cuadrícula de
tarjetas en la portada de alcaldías ha sido sustituida por una **vista de
noticias a la izquierda e historia con foto a la derecha**, con un selector
compacto para cambiar de alcaldía. En móvil, las noticias aparecen primero
y la historia con su foto está inmediatamente después.

- \`assets/alcaldias/historias.json\`: reseñas históricas originales, lugares
  destacados y enlaces a fuentes institucionales para las 16 demarcaciones.
- \`assets/alcaldias/fotos.json\`: autor, licencia, título, origen y pie de foto
  de 16 fotografías verificadas, una por alcaldía.
- \`assets/alcaldias/<slug>.jpg\`: fotografías reales locales, redimensionadas
  para mantener la página rápida, que muestran lugares característicos de
  cada alcaldía; no representan los acontecimientos de los titulares.
- \`scripts/fotos_alcaldias.py\`: verifica ubicación preseleccionada, licencia
  Creative Commons, formato, resolución y descarga fotografías originales
  de Wikimedia Commons. El workflow se ejecuta al cambiar la selección.
- \`tests/test_profiles.py\`: comprueba historia, foto y navegación directa.

Los contenidos históricos son síntesis con fuentes enlazadas, no transcripciones
de artículos ajenos ni reportes periodísticos; el número de noticias por
alcaldía depende de las menciones explícitas del nombre en los titulares.

## Mapa ilustrado de la Ciudad de México

- Portada: mapa compacto debajo de «La ciudad nunca se detiene. Nosotros tampoco.», con enlace al mapa ampliado.
- Página completa: `/mapa/`, mapa Leaflet con base CARTO/OSM de apariencia suave, zoom, búsqueda de 11 monumentos representados con estampas SVG dibujadas para el proyecto.
- Capas con geometrías de referencia del **Atlas Público de Movilidad Integrada de SIGIRPC CDMX** (FeatureServer): Metro, Metrobús, RTP, Trolebús, Tren Ligero, Cablebús y transporte concesionado (corredores/servicios zonales).
- `functions/api/transporte.js`: función de Cloudflare Pages, consulta y limita la respuesta del servicio público. Si la función no está desplegada, el navegador intenta acceder directamente al atlas (sujeto a CORS).
- Los trazados son históricos/cartográficos de referencia: NO son seguimiento de camiones ni horarios en tiempo real. No se garantiza cobertura exhaustiva de microbuses/combis y las rutas pueden haber cambiado.
- La tarjeta mini `/mapa/mini.svg` es puramente ilustrativa, no un plano geográfico.
- Uso de datos sujetos a atribución: `https://serviciosatlas.sgirpc.cdmx.gob.mx/arcgis/rest/services/AtlasCapasPublicas/Movilidad_Integrada_CDMX/FeatureServer`; mapas de fondo © OpenStreetMap contributors y © CARTO.

### Vista previa cartográfica y modo ampliado (12-10-2026)
- `/mapa/preview.html`: mapa real pequeño (no diagrama decorativo) del centro de CDMX en un recuadro dentro de la portada, con estampas de monumentos y carga diferida.
- El mapa completo aparece primero en un cuadro compacto con botón **Ver mapa grande**, que lo expande a la pantalla del móvil o PC y permite cerrarlo con un botón (o Esc en PC).
- Los mapas usan **OpenStreetMap Standard** para evitar el aviso **API KEY REQUIRED** de CARTO. Se conserva la atribución visible y caché de mosaicos normal del navegador, sin predescargas.

En móvil, el recuadro del mapa precede a las noticias en la sección principal; la lista de las 16 alcaldías aparece tras las noticias. Los filtros del menú se desplazan expresamente a los titulares, sin detenerse en el mapa ni las alcaldías.

### Prominencia del mapa en Inicio
Desde el 12 de octubre de 2026, la tarjeta compacta del mapa se presenta debajo del título principal de la portada, para que sea visible en PC y móvil sin tener que desplazarse. La vista compacta tiene su mapa geográfico real y abre `/mapa/` al pulsar cualquier parte de la tarjeta. Solo se muestra una vez en la portada; la lista de alcaldías permanece más abajo y los filtros conducen a noticias.


## Renovación diaria de fotografías de contexto

- En cada ejecución horaria, el workflow comprueba si toca la **consulta diaria** de imágenes mediante `scripts/actualizar_fotos.py`.
- Busca archivos **subidos durante los últimos 180 días** a Wikimedia Commons, asociados explícitamente con Ciudad de México y alguno de los seis temas, y verifica autor, permiso de reutilización (CC BY, CC BY-SA o CC0) y miniatura oficial. Si la fecha de captura consta y es antigua, descarta la imagen.
- Guarda metadatos y miniaturas, **sin copiar fotos de medios periodísticos**, en `assets/fotos/recientes.json`, con enlaces a sus créditos en `/creditos-fotograficos.html`.
- Prioriza las imágenes contextuales recientes en titulares, fotografías de portada, tarjetas de temas y galería, con el catálogo local como respaldo si el servicio no devuelve resultados o falla una imagen.
- **Precisión editorial:** fecha de subida a Commons ≠ fecha de toma ni fecha del acontecimiento. Ninguna foto de contexto demuestra que muestre el hecho de un titular.
- Si Wikimedia no devuelve archivos aptos, permanece la imagen de archivo; no se inventan fotografías ni procedencias. El número de imágenes puede variar por categoría.


## CDMX CERCA DE TI: funciones para lectores (octubre 2026)

Se amplió el portal directamente en GitHub y Cloudflare Pages con estas páginas informativas originales:

- **Inicio**: resumen «Hoy en la CDMX», con seis titulares y fecha real de publicación cuando conste. Si todavía no hay notas del día, se indica expresamente que se muestran las más recientes.
- **/cerca/**: personalización por una de las 16 alcaldías (se guarda mediante `localStorage` únicamente en ese navegador), noticias que mencionan el nombre de la zona, enlaces a historias de las alcaldías y mapa. No utiliza GPS.
- **/movilidad/**: las 12 líneas del Metro con colores y terminales cartográficas de referencia, enlaces directos a Metro, Metrobús y SEMOVI y noticias relacionadas. **NO consulta ni certifica el estado en tiempo real**.
- **/avisos/**: enlaces oficiales de protección civil, calidad del aire y movilidad, con filtro transparente por palabras de los titulares (no son alertas operativas certificadas).
- **/favoritos/**: guardar/quitar titulares desde tarjetas y resúmenes, almacenados en el dispositivo, sin iniciar sesión y sin seguimiento.
- **Notificaciones voluntarias**: botón del lector que solicita el permiso explícito; el navegador compara titulares nuevos cada 15 minutos **solo mientras la página permanece abierta**. No se implementó Web Push persistente ni se prometen avisos de emergencia en segundo plano.
- **/mapa/**: además de Metro, transporte, monumentos y parques, capas de museos, patrimonio arqueológico y hospitales orientativos (no horarios, disponibilidad ni acceso de urgencias).
- **Accesibilidad y diseño**: enlaces de navegación claros, tarjetas adaptables, controles táctiles y reducción de movimiento cuando el navegador lo solicita.
- **Editorial/AdSense**: cuatro páginas de contexto original, enlaces a fuentes oficiales, descripción de la metodología, créditos fotográficos, títulos y metadatos, sitemap actualizado y privacidad transparente. Una mejora editorial no garantiza aprobación de AdSense.

El workflow horario sigue realizando la actualización de titulares y la comprobación diaria de fotos. Revisa también sintaxis de JavaScript y todas las pruebas unitarias antes de publicar nuevos datos. Las fotografías contextuales no necesariamente pertenecen al acontecimiento reportado.

**Enlaces y vigencia:** para saber si una línea está operando o una alerta sigue activa, el lector debe verificar en las fuentes oficiales. Las tarjetas de noticias son recopilaciones informativas de enlaces a medios externos, no informes propios.


## Tira rosa del clima por alcaldía (octubre de 2026)

- Una **tira horizontal animada y compacta** aparece en la parte superior de la portada, el mapa, alcaldías, guías, reportes y páginas informativas. Es adaptable al celular, se detiene cuando el cursor o foco está encima y respeta `prefers-reduced-motion`.
- Muestra **pronóstico meteorológico estimado**, temperatura, condiciones, humedad, viento, hora del pronóstico y alcaldía seleccionada. Nunca se inventan datos si el proveedor no responde.
- El selector de la propia tira usa `cdmx.memento.alcaldia.v1` en `localStorage` y se sincroniza en la misma pestaña con las noticias personalizadas de `/cerca/`. No se solicita ubicación GPS ni domicilio.
- El cliente `assets/clima-ticker.js` consulta exclusivamente `/api/clima?alcaldia=...`. La función de Cloudflare Pages `functions/api/clima.js` acepta solo las 16 alcaldías conocidas y consulta una coordenada representativa por cada una.
- Origen: **MET Norway Locationforecast 2.0** (`https://api.met.no/`), con atribución visible y enlace al proveedor. Sus datos CC BY admiten reutilización comercial con atribución. La función se identifica por `User-Agent` y reutiliza los datos de forma temporal según la vigencia de la respuesta para evitar consultas innecesarias. No se necesita una API key.
- Se intenta renovar la lectura cada **15 minutos** mientras la página está visible. La hora indicada es la hora del pronóstico; **no** es una medición instrumental tomada en la alcaldía ni una alerta meteorológica oficial.
- `tests/test_weather.py` verifica inclusión del widget, las 16 alcaldías, accesibilidad, atribución, código de integración y la plantilla de nuevos reportes.
