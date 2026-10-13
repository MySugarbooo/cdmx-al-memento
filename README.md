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

- Portada: tarjeta clicable en la columna derecha, antes de las alcaldías. En móvil, las noticias siguen primero.
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
Desde el 12 de octubre de 2026, la tarjeta clicable del mapa se presenta inmediatamente debajo del menú principal de la portada, **antes del hero, las noticias y la lista de alcaldías**, para que sea visible en PC y móvil sin tener que desplazarse. La vista compacta tiene su mapa geográfico real y abre `/mapa/` al pulsar cualquier parte de la tarjeta. Solo se muestra una vez en la portada; la lista de alcaldías permanece más abajo y los filtros conducen a noticias.


## Renovación diaria de fotografías de contexto

- En cada ejecución horaria, el workflow comprueba si toca la **consulta diaria** de imágenes mediante `scripts/actualizar_fotos.py`.
- Busca archivos **subidos durante los últimos 180 días** a Wikimedia Commons, asociados explícitamente con Ciudad de México y alguno de los seis temas, y verifica autor, permiso de reutilización (CC BY, CC BY-SA o CC0) y miniatura oficial. Si la fecha de captura consta y es antigua, descarta la imagen.
- Guarda metadatos y miniaturas, **sin copiar fotos de medios periodísticos**, en `assets/fotos/recientes.json`, con enlaces a sus créditos en `/creditos-fotograficos.html`.
- Prioriza las imágenes contextuales recientes en titulares, fotografías de portada, tarjetas de temas y galería, con el catálogo local como respaldo si el servicio no devuelve resultados o falla una imagen.
- **Precisión editorial:** fecha de subida a Commons ≠ fecha de toma ni fecha del acontecimiento. Ninguna foto de contexto demuestra que muestre el hecho de un titular.
- Si Wikimedia no devuelve archivos aptos, permanece la imagen de archivo; no se inventan fotografías ni procedencias. El número de imágenes puede variar por categoría.
