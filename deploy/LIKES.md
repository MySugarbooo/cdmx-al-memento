# Activar Me gusta en el sitio existente

El frontend y `/api/likes` se publican con el despliegue habitual de GitHub a Cloudflare Pages. El contador necesita un binding D1; sin él devuelve 503 y la interfaz no inventa votos.

1. En Cloudflare, Storage & databases → D1 SQL database → Create database. Nombre sugerido: `cdmx-memento-likes`.
2. En la consola de esa base, ejecutar el contenido de `deploy/likes.sql`.
3. Workers & Pages → proyecto `cdmx-al-memento` → Settings → Bindings → Add → D1 database. Variable: `LIKES_DB`. Elegir la base creada y guardar en Production.
4. Reintentar el último despliegue de producción para que la función reciba el binding.
5. Abrir la portada. `/api/likes` debe responder JSON `{total: 0, liked: false}` inicialmente, con cookie HttpOnly. Probar dar like, recargar y quitarlo; comprobar el total desde otro navegador. No se requieren claves en el código ni Facebook.

No se agrega wrangler.json para no sobrescribir los ajustes existentes de Pages. No vincular una base de pruebas al entorno de producción.

## Comportamiento

- Un voto anónimo por cookie de navegador, no por persona verificada.
- Un total compartido y persistente en D1, incluso después de nuevas publicaciones.
- PUT idempotente (dar o quitar), restricción de origen y respuestas sin caché.
- Si una solicitud falla, se vuelve a consultar antes de permitir otro cambio.
- El total se actualiza al volver a la pestaña, cada minuto mientras esté visible y al votar.
- No hay contadores locales ni votos iniciales artificiales.
- El borrado de cookies permite volver a votar. Para contar personas verificadas haría falta autenticación.

Pruebas con SQLite real: `node --test tests/test_likes.mjs`.
