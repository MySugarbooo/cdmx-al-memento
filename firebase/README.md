# Activación de comentarios Google/Facebook

La interfaz está publicada en cada noticia individual, pero **no puede operar sin un proyecto de autenticación y una base de datos configurados por la persona propietaria**.

1. Crear un proyecto en Firebase Console y registrar una aplicación web.
2. En Authentication > Sign-in method, activar Google y Facebook. Para Facebook es necesario crear una aplicación en Meta for Developers y configurar el ID, secreto y URL de redirección OAuth que indica Firebase. No publicar esos secretos en GitHub.
3. Añadir `cdmx-al-memento.pages.dev` a los dominios autorizados de Firebase Authentication.
4. Crear Cloud Firestore en modo de producción y desplegar las reglas de `firebase/firestore.rules`. **No utilizar reglas abiertas**.
5. Pegar únicamente los valores **públicos** de la configuración web de Firebase en `assets/comments-config.js` (apiKey, authDomain, projectId, appId). Estos identificadores no son secretos.
6. Abrir una noticia con URL `/noticias/?id=<20 caracteres hex>&mes=AAAA-MM` y comprobar inicio de sesión, publicación, lectura y eliminación.

Cada comentario se asocia a la noticia, muestra el nombre público de la cuenta y admite hasta 1000 caracteres. Las reglas permiten borrar solo los comentarios propios. Para moderación centralizada, denuncias, protección antispam y límites por usuario hacen falta herramientas adicionales (Cloud Functions/App Check y consola de administración) antes de una apertura a gran escala.
