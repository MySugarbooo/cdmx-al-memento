# Mi comunidad · Google Auth + Firestore

## Estado real de la seguridad

Las reglas fuente están en `firebase/firestore.rules`, pero **GitHub/Cloudflare Pages no aplican automáticamente reglas a Firebase**. La persona administradora debe publicar ese archivo en Firebase Console > Build > Firestore Database > Rules > Publish. **Sin ese paso el sistema de reportes puede devolver `permission-denied` y se mantendrán las reglas que ya estaban activas**.

No incluyas credenciales de servicio, llaves privadas ni cuentas administrativas en el repositorio.

## Activación segura

1. En Firebase Console, selecciona el proyecto `cdmx-al-memento`.
2. Authentication > Sign-in method: habilita Google. Facebook no se anuncia ni se ofrece en el foro actual.
3. Authentication > Settings > Authorized domains: verifica `cdmx-al-memento.pages.dev`.
4. Firestore Database > Rules: pega el contenido íntegro de `firestore.rules`, comprueba que no se pierdan otras colecciones que uses y pulsa **Publish**.
5. Valida una publicación y respuesta con una cuenta Google real y desde incógnito. La colección es `community/main/comments`.
6. El formulario reporta en `community/main/reports`: solo una denuncia por usuario y comentario, con lectura restringida a moderadores. Verifica que las denuncias no sean públicas.
7. Las reglas no ofrecen por sí mismas un límite real de publicaciones por minuto. Para protección robusta contra bots y abuso, prepara Firebase App Check y un backend confiable (Cloud Functions) para imponer límites; el enfriamiento de 15 segundos del navegador solo mejora la experiencia, no es defensa contra ataques.

## Identidad y fotos

Las nuevas publicaciones incluyen `uid`, nombre del token de Google, texto y fecha del servidor. Si el token trae la imagen verificada `picture`, se incorpora `photoURL`; las reglas aceptan esa URL únicamente si coincide con la del token. Si las reglas antiguas siguen activas, el cliente intenta publicar sin `photoURL` para no interrumpir el servicio.

Las publicaciones antiguas se conservan sin modificarse. Las fotos que no estaban guardadas no se pueden recuperar retroactivamente de Firebase Authentication desde el navegador de otra persona: seguirán usando una inicial.

## Moderación

Los reportes se guardan en una colección privada. Un moderador con la **custom claim** `moderator: true` tiene panel para ver reportes, eliminar publicaciones denunciadas y cerrar reportes. Solo un entorno de administración con **Firebase Admin SDK** debe asignar esa custom claim, nunca el JavaScript público.

En un entorno de administración autenticado, consulta las claims anteriores del usuario y consérvalas al asignar `moderator: true` (no sobrescribas otros roles). El usuario moderador debe renovar su token volviendo a iniciar sesión para ver el panel. El ID de usuario se obtiene de Authentication > Users; **nunca publiques UIDs ni tokens de servicio en GitHub**.

Para bloquear un usuario, el administrador puede crear con privilegios de servidor un documento `communityBans/{uid}`. Las reglas impiden que usuarios normales creen o lean esa lista.

## Compatibilidad e historial

La estructura de mensajes previa se conserva:
- `[FORO:PREGUNTA] título\ntexto`
- `[FORO:RESPUESTA:ID] texto`
- Los mensajes anteriores sin prefijo siguen visibles.

La interfaz consulta 100 documentos por página y ofrece **Cargar conversaciones anteriores**. Búsqueda, contadores y clasificación corresponden a los documentos ya cargados (no es búsqueda global de Firestore). Las respuestas de preguntas eliminadas siguen disponibles en un grupo explícito, sin permitir responder a una pregunta inexistente.

## Pruebas recomendadas antes de abrir a muchos usuarios

- Cuenta anónima: leer sí; escribir y denunciar no.
- Cuenta Google: escribir, responder, reportar una vez por comentario, borrar solo contenidos propios.
- Cuenta distinta: no borrar mensajes ajenos ni asumir nombre/avatar falsos.
- Moderador: consultar reportes privados, borrar contenido denunciado, cerrar reporte.
- Usuarios bloqueados: no escribir ni reportar, pero sí leer el foro.
- Dejar la página abierta durante nuevas publicaciones y usar **Cargar conversaciones anteriores** varias veces; comprobar que no haya duplicados y que la búsqueda muestre solo contenido cargado.

Si una regla no se ha desplegado, no debe afirmarse que el endurecimiento está activo en producción.

## Asignar cuenta de moderación por correo Google (sin publicar contraseñas)

El correo identifica una cuenta **verificada** en Firebase Authentication; escribirlo públicamente nunca concede privilegios. El rol real se asigna mediante la custom claim firmada `moderator: true`. No compartas contraseñas, tokens ni claves JSON.

Desde **Google Cloud Shell** en el proyecto **cdmx-al-memento**, con permisos administrativos de Firebase Authentication:

```bash
gcloud config set project cdmx-al-memento
# Usa credenciales temporales de una cuenta de servicio autorizada.
# Sustituye SERVICE_ACCOUNT_EMAIL por el correo real de tu cuenta de servicio de Firebase.
gcloud auth application-default login --impersonate-service-account=SERVICE_ACCOUNT_EMAIL
git clone https://github.com/MySugarbooo/cdmx-al-memento.git
cd cdmx-al-memento
npm install --no-save firebase-admin
node firebase/asignar-moderador.mjs --email CORREO_DE_GOOGLE --grant
```

El último comando solo **simula**: comprueba que la cuenta Google existe y está verificada. Para conceder el rol tras revisar los resultados:

```bash
node firebase/asignar-moderador.mjs --email CORREO_DE_GOOGLE --grant --apply
```

Para revocarlo: `--revoke --apply`. El script mantiene los demás roles existentes. La cuenta debe cerrar su sesión de Mi comunidad y volver a entrar para renovar el token y mostrar el panel privado.

El **correo para recibir alertas** es una función distinta: en la web actual las denuncias se guardan en Firestore y aparecen en el panel de moderación, pero no envían mensajes automáticos. Para notificaciones por email se necesita una función de servidor o proveedor externo y credenciales privadas. No coloques claves de administrador ni contraseñas en el JavaScript público.

**Importante:** Firebase Authentication no acepta las credenciales de usuario predeterminadas del cliente OAuth de gcloud para el Admin SDK. Por eso el ejemplo usa suplantación temporal de una cuenta de servicio (service account impersonation), no una clave JSON. La cuenta de Google que ejecuta el comando necesita el permiso IAM **Service Account Token Creator**, y la cuenta de servicio seleccionada necesita permisos de administración de Firebase Authentication. Puedes encontrar la cuenta de servicio en Firebase Console → Configuración del proyecto → Cuentas de servicio. Si falla por IAM, revisa esos permisos antes de seguir. No descargues ni publiques credenciales de servicio.
