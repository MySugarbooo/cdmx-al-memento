# CDMX AL MEMENTO
Portal estático y agregador de titulares de noticias de CDMX. Diseño responsivo y espacios reservados para publicidad.

## Publicación gratis
1. Crea un repositorio público en GitHub y sube todos los archivos, incluida la carpeta `.github`.
2. En GitHub > Actions > Actualizar titulares CDMX, ejecuta `Run workflow` para generar `news.json`.
3. En Settings > Actions > General, configura Workflow permissions como **Read and write permissions** para permitir el commit automático.
4. Activa GitHub Pages (Settings > Pages > Deploy from a branch > main / root). Tu sitio tendrá una URL `usuario.github.io/repositorio`.
5. GitHub Actions intenta actualizar titulares cada 3 horas (puede retrasarse, fallar o pausarse). Comprueba su ejecución periódicamente.

## Importante
- La página es un **agregador**: enlaza a los medios; no reproduce artículos ni afirma verificar independientemente los hechos.
- Los feeds RSS de terceros pueden cambiar o bloquear solicitudes. Se necesita mantenimiento y seguimiento de errores.
- No incluye cuenta de Gmail, envío de correo ni anuncios reales. AdSense requiere sitio público, contenido y aprobación; antes de solicitarlo, añade política de privacidad, contacto real y páginas editoriales.
- Para monetizar conviene publicar reportajes originales y no depender solo de titulares externos.
- Nunca subas contraseñas ni credenciales al repositorio.


Noticias iniciales incluidas: 6 enlaces con fuentes del 7-9 de octubre de 2026. Las actualizaciones posteriores se hacen con Google News RSS mediante GitHub Actions; requieren subir el proyecto a GitHub y habilitar Actions. No se ha publicado en internet ni activado AdSense.
