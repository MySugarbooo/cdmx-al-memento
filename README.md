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

El workflow `.github/workflows/news.yml` ejecuta pruebas y `python update_news.py` aproximadamente cada 3 horas cuando GitHub Actions está disponible. Lee RSS de Google News, recopila los temas de la capital y hace búsquedas adicionales para las 16 alcaldías. Fusiona las noticias nuevas con el archivo de meses anteriores, comprueba fechas y elimina los archivos mensuales que quedan vacíos. No almacena textos íntegros de artículos.

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
