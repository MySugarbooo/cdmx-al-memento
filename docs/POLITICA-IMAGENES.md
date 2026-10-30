# Política editorial de imágenes — CDMX AL MEMENTO

## Reglas de publicación

1. **Foto del acontecimiento:** solo cuando el expediente `assets/fotos/hechos-verificados.json` enlaza exactamente la noticia del RSS con una fotografía comprobada del mismo hecho y con licencia comercial reutilizable. No basta que una foto figure en el artículo original ni que tenga un título parecido.
2. **Imagen representativa:** si no hay prueba suficiente o derechos claros, el sistema usa una fotografía de contexto relacionada con el tema o la alcaldía; se identifica expresamente como representativa y nunca como evidencia del hecho.
3. **Ilustración digital:** cuando la foto tampoco está disponible, se mantiene el recurso gráfico existente, identificado como ilustración.
4. **Créditos:** consignar autor, fuente de la obra y licencia, con enlaces de origen cuando estén disponibles. El titular de la noticia y los créditos de la foto son datos distintos.

No se descarga ni republica automáticamente una fotografía de un periódico por el solo hecho de que aparezca como `og:image`, en Google Noticias o en redes sociales. Citarla no sustituye contar con autorización o licencia válida.

## Registro de fotografías del hecho

Añadir a `assets/fotos/hechos-verificados.json` registros dentro de la lista `photos`, después de comprobar manualmente los documentos y las condiciones de uso:

```json
{
  "article_url": "https://news.google.com/rss/articles/IDENTIFICADOR",
  "article_title": "Título exacto de la noticia del RSS",
  "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/fotografia.jpg",
  "source": "https://commons.wikimedia.org/wiki/File:Fotografia.jpg",
  "evidence_url": "https://medio.example/cobertura-del-hecho",
  "author": "Nombre acreditado en Commons",
  "license": "CC BY-SA 4.0",
  "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
  "topic": "Descripción factual de la imagen",
  "event_match_confirmed": true,
  "rights_confirmed": true,
  "reviewed_by": "Editor responsable",
  "reviewed_at": "2026-10-30T15:00:00Z"
}
```

El registro de ejemplo es ilustrativo: no corresponde a una foto real y **no debe publicarse** sin sustituir y corroborar los datos.

### Validaciones automáticas

- Se exige URL exacta del artículo de Google News y su título, para evitar que una fotografía se adjudique a otra noticia.
- Se exige identificación explícita de la coincidencia, derechos, responsable editorial, fecha y enlace de evidencia.
- Solo se aceptan fotografías de Wikimedia Commons con URL de imagen permitida y licencias CC BY, CC BY-SA o CC0 que permitan reutilización comercial.
- Cualquier registro incompleto, licencia incompatible, enlace fuera de los dominios permitidos o expediente retirado vuelve automáticamente a la foto representativa.
- El catálogo general de fotos de contexto no puede sobreescribir una foto exacta aprobada.
- Si la foto falla al cargar, la interfaz cambia a una imagen representativa o recurso editorial, sin conservar la atribución de la foto fallida.

**Nota:** un programa no puede garantizar por sí solo que una foto representa el mismo hecho. El registro requiere revisión editorial real, y si no existe dicha revisión la imagen debe seguir identificada como representativa.
