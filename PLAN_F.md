# Plan F — CDMX AL MEMENTO

Actualizado: 2026-10-26. Se ejecuta por etapas para evitar romper funcionalidades.

## Etapa 1 — Noticias y estabilidad (cambios de código guardados; falta verificar producción)
- [x] Portada inicial con noticia e ilustración integradas en HTML.
- [x] Evitar que la noticia principal cambie inesperadamente tras la primera carga de datos, utilizando un identificador de visita.
- [x] Respaldo de noticias publicadas si falla la consulta principal.
- [x] Corregir el cálculo del tiempo de lectura.
- [ ] Comprobar publicación en Cloudflare y prueba real en iPhone.
- [ ] Verificar el recopilador programado: antigüedad del feed, errores de acciones y actualización de archivos.

## Etapa 2 — Comunidad y participación (cambios de código guardados; falta verificar producción)
- [x] Tarjetas de comentarios, avatares y autenticación existente.
- [x] Publicación compatible con los campos permitidos por Firestore.
- [x] Botón Responder que menciona a una persona en el editor; **no son hilos anidados**.
- [x] Compartir noticias por WhatsApp desde las tarjetas.
- [ ] Reacciones persistentes, respuestas anidadas y moderación con reglas Firestore y pruebas de permisos.
- [ ] Fotos públicas de Google en comentarios antiguos (requiere consentimiento y actualizar reglas/almacenamiento).

## Etapa 3 — Diseño e imágenes
- [x] Colores rosa/oscuro y diseño adaptativo existentes.
- [ ] Auditoría visual en pantallas de 320px, iPhone y escritorio.
- [ ] Imágenes temáticas propias por noticia con licencia y atribución correctas, etiqueta ilustrativa.
- [ ] Conectar generación de caricaturas IA en servidor con cuotas y revisión editorial; no afirmar que existe hasta comprobarlo.
- [ ] Optimización de tamaños y carga para evitar bloqueos visuales.

## Etapa 4 — Monetización
- [x] Integración existente de AdSense en cabecera.
- [ ] Confirmar aprobación y cuenta desde notificación oficial de Google.
- [ ] Ubicar anuncios entre noticias sin dificultar la lectura ni confundirlos con noticias.
- [ ] Revisar políticas, consentimiento cuando proceda, CLS, Core Web Vitals y ads.txt.

## Etapa 5 — Automatización y mantenimiento
- [x] Existe seguimiento programado del estado del sitio y GitHub Actions mediante automatización de ChatGPT.
- [ ] Probar que la acción de noticias finaliza correctamente y que el contenido realmente se actualiza.
- [ ] Detección y reporte de errores de datos, imágenes, comentarios y sus dependencias.
- [ ] Panel editorial para aprobar imágenes/noticias, auditar fuentes y revisar fallos.

## Reglas de publicación
- Preservar enlaces, autenticación, contadores, mapas y noticias publicadas.
- Una ilustración jamás debe hacerse pasar por fotografía real del suceso.
- No publicar noticias inventadas, fechas incorrectas o titulares sensacionalistas.
- Los cambios guardados en GitHub no demuestran por sí solos su despliegue en Cloudflare.
- Si una modificación necesita credenciales, servicios de pago o configuración externa, señalar la dependencia antes de darla por terminada.
