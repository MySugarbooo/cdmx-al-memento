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
