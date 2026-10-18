# Contador compartido de Me gusta

Estado: preparado para activar con D1 en Cloudflare Pages.

1. Crear una base D1 gratuita llamada cdmx-site-likes.
2. En cdmx-al-memento, configurar una vinculación D1 de producción llamada LIKES_DB a esa base.
3. Publicar esta revisión. La función crea automáticamente la tabla site_likes.
4. Comprobar GET /api/likes, dos POST consecutivos con la misma cookie y lectura desde otro navegador.

El contador arranca vacío. Solo sube por una pulsación explícita. Se evita un segundo voto en el mismo navegador mediante una cookie propia aleatoria, HttpOnly, Secure y SameSite=Lax. No se almacenan IP ni datos personales declarados. Los fallos muestran una advertencia y nunca inventan totales. El bloqueo es por navegador, no una garantía de una persona por voto.

La interfaz se incluye en portada, índice de noticias, alcaldías y la nota de Tortas Don Pepe. Comparte un total del sitio.
