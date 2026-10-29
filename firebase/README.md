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

## Votos útiles y mejores respuestas (etapa 3)

Los votos de Mi comunidad usan dos rutas de Firestore:

- `community/main/votes/{commentId}/users/{uid}`: un registro por usuario y publicación. Solo su dueño puede consultar, crear o eliminar su propio registro; la enumeración de votantes está prohibida.
- `community/main/voteTotals/{commentId}`: únicamente el número total de votos, visible al público.

Una transacción actualiza ambos documentos de forma atómica. Las reglas usan `getAfter` y `existsAfter` para impedir incrementos manuales o votos falsos. El botón permite retirar el voto; al volver a votar solo se conserva un registro. Las respuestas con más votos útiles de cada hilo cargado se colocan primero y reciben una etiqueta. **La popularidad no significa que la información esté verificada.**

**Paso obligatorio de despliegue:** este repositorio no controla automáticamente las reglas activas de Firebase. Tras publicar el JavaScript en Cloudflare Pages, abre Firebase Console del proyecto `cdmx-al-memento` > Firestore Database > Rules, revisa el archivo fuente completo `firebase/firestore.rules` y publícalo. Sin publicar las reglas, el foro detectará `permission-denied` en los votos y los deshabilitará, sin interrumpir preguntas, respuestas ni moderación. Es importante **reemplazar las reglas completas, no pegar únicamente la nueva sección**, para no perder las reglas anteriores.

Pruebas funcionales sugeridas después de activar las reglas:

1. Sin iniciar sesión: leer el foro y el número de votos, pero no emitir votos.
2. Cuenta Google A: votar una respuesta y confirmar que el número sube uno; retirarlo y confirmar que baja uno.
3. Cuenta Google B: votar la misma respuesta y comprobar que los votos independientes se suman.
4. Intentar modificar el contador o votar a nombre de otra cuenta con una petición no autorizada: Firestore debe rechazarlo.
5. Comprobar que los reportes siguen siendo privados y que el panel de moderación mantiene sus permisos.

**Límite conocido:** al eliminar una publicación, Firestore no borra automáticamente los documentos de votos asociados. Se requiere una tarea de limpieza privilegiada para purgarlos definitivamente. La interfaz no vuelve a contabilizar votos de publicaciones que ya no existen.

## Moderación

Los reportes se guardan en una colección privada. Un moderador con la **custom claim** `moderator: true` tiene panel para ver reportes, eliminar publicaciones denunciadas y cerrar reportes. Solo un entorno de administración con **Firebase Admin SDK** debe asignar esa custom claim, nunca el JavaScript público.

En un entorno de administración autenticado, consulta las claims anteriores del usuario y consérvalas al asignar `moderator: true` (no sobrescribas otros roles). El usuario moderador debe renovar su token volviendo a iniciar sesión para ver el panel. El ID de usuario se obtiene de Authentication > Users; **nunca publiques UIDs ni tokens de servicio en GitHub**.

Para bloquear un usuario, el administrador puede crear con privilegios de servidor un documento `communityBans/{uid}`. Las reglas impiden que usuarios normales creen o lean esa lista.

## Etapa 5 · Filtros e historial privado de decisiones

El panel `/moderacion/` conserva el acceso por el claim firmado `moderator: true`, el nombre y la fotografía de la cuenta de Google. Añade búsqueda y filtros por motivo, visualización de varias denuncias sobre una misma publicación, notas internas e historial de decisiones. La repetición de reportes **no demuestra una infracción**.

El registro nuevo se guarda exclusivamente en `community/main/moderationActions/{id}` con:

- `actorUid`: la cuenta moderadora que toma la decisión;
- `reportId`, `commentId`, `reason`, `action` (`dismiss` o `remove`), `note` (hasta 240 caracteres) y `createdAt` (fecha/hora del servidor).

Las reglas dejan leer el historial **solo a moderadores** y crear registros **solo al moderador que ejecuta la acción**. La creación requiere cerrar el reporte en la misma transacción, y en caso de retirada también borrar la publicación. Los clientes no pueden modificar ni eliminar entradas ya creadas. Un administrador con privilegios de servidor sí puede gestionar los datos, por lo que esto no reemplaza un sistema forense de auditoría independiente.

**Activación obligatoria para registrar decisiones:**
1. Copia el archivo **completo** `firebase/firestore.rules` a Firebase Console > Firestore Database > Rules y publícalo. **No borres** las reglas de moderación, votos, publicaciones o denuncias existentes.
2. Vuelve al panel, inicia sesión con Google y selecciona **Actualizar historial**. Debe aparecer que el historial privado está activo.
3. Con una denuncia de prueba, comprueba una decisión autorizada y verifica que aparece en el historial. No borres publicaciones reales solo para probar.
4. En una cuenta sin permiso, el panel debe mostrar acceso denegado y Firestore debe rechazar la lectura del historial.

**Compatibilidad:** si la lectura del historial falla (por ejemplo, porque las nuevas reglas aún no se publicaron), el panel permite las acciones anteriores con una confirmación que avisa expresamente que no quedarán en el historial. El historial registra **solo las decisiones hechas desde este panel a partir de la activación**; no reconstruye decisiones anteriores ni registra las eliminaciones hechas desde el propio foro u otras interfaces.

Las notas internas y los UID de las cuentas moderadoras son privados. No incluyas correos, domicilios ni otras claves personales en las notas. No se guardan copias del texto de publicaciones eliminadas en el registro. No hay depuración automática configurada para `moderationActions`; se deberá definir una política de retención y limpieza administrada si el volumen crece.

La opción **Contacto** se utiliza para solicitar revisión de decisiones; no existe aún un sistema de apelaciones con identificador de caso ni garantías de respuesta automática.

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

## Etapa 9: reportes ciudadanos por colonia

Página independiente: `/reportes-ciudadanos/`. **No confundir con `/reportes/`**, que conserva los análisis editoriales de noticias.

**Se requiere publicar las reglas completas de Firestore actualizadas.** GitHub, Cloudflare y sus despliegues no modifican las reglas del proyecto Firebase. Abrir:
https://console.firebase.google.com/project/cdmx-al-memento/firestore/rules
y copiar el archivo **entero** `firebase/firestore.rules` desde la rama `main`; después pulsar Publicar. No pegar únicamente el bloque de reportes, porque se perderían los permisos del foro, los votos y la moderación anterior.

### Esquema de datos y visibilidad

- `citizenReports/{reportId}`: registro privado. Contiene `uid`, `borough`, `colonia`, `category`, `title`, `description`, `status`, `createdAt`, `updatedAt` y `moderatedBy`. Lectura solo de su dueño o de una cuenta con rol `moderator: true`. Nuevo reporte siempre `pending`. No se acepta nombre, correo, teléfono, URL de foto, GPS, contenido multimedia ni campos adicionales en este documento.
- `citizenReportsPublic/{reportId}`: reflejo público **sin UID ni datos de autenticación**. Contiene únicamente `borough`, `colonia`, `category`, `title`, `description`, `status`, `createdAt` y `updatedAt`. Solo un moderador autorizado puede crear este reflejo cuando cambia de `pending` a `published` en el **mismo lote atómico**. La igualdad se comprueba con `getAfter()`.
- Un moderador puede pasar de `published` a `closed` (cierre editorial, no reparación comprobada), o descartar desde `pending` o retirar una publicación. La actualización del privado y la del reflejo público deben ser atómicas; los clientes no pueden alterar los reportes de otros usuarios.
- El propietario puede borrar su reporte privado solo cuando esté `pending` o `rejected`. Después de publicarlo, debe solicitar su retiro a moderación. La fecha de creación y el contenido original son inmutables; la fecha de actualización y el UID moderador se registran en los cambios.
- El usuario de Google no necesita un rol nuevo. **Los mismos moderadores actuales** pueden aprobar y retirar reportes; el rol se asigna en el servidor, nunca desde el navegador.

### Cómo probar después de publicar las reglas

1. En incógnito, sin iniciar sesión: abrir `/reportes-ciudadanos/` y comprobar que la lista pública carga, pero el formulario esté oculto. Un visitante NO debe poder leer `citizenReports` de otra cuenta.
2. Cuenta Google normal: entrar, crear un reporte inocuo de prueba («Prueba de alumbrado en mi colonia», sin domicilios ni PII). Debe aparecer **solo** en «Mis reportes», con estado `pending`, no en la lista pública.
3. Cuenta moderadora: abrir la misma página, verificar que se muestra «Revisión editorial», y aprobar el reporte. Debe aparecer públicamente sin UID, nombre ni correo; y el propietario debe ver el cambio de estado.
4. Cuenta moderadora: «Cerrar seguimiento» y luego «Retirar de la web»; confirmar que el cierre no dice que la avería fue reparada. Si hay errores `permission-denied`, comprobar primero el archivo completo de reglas publicado.
5. Intentar escribir directamente en `citizenReportsPublic` desde una cuenta normal: debe ser denegado. Intentar marcar un envío privado como publicado o modificar otro usuario debe ser denegado.
6. Revisar que la comunidad, votos, denuncias del foro e historial de moderación siguen funcionando.

### Limitaciones de seguridad

La revisión de contenido es manual. El enfriamiento de 60 segundos en JavaScript **no** es un límite real en el servidor; las reglas por sí solas no pueden imponer una cuota fiable de publicaciones por minuto. Antes de escalar el servicio es recomendable implementar **Firebase App Check + Cloud Functions u otro backend confiable con cuotas por UID**, y considerar revisión reforzada de datos personales antes de publicar. Las reglas de Firestore no filtran palabras sensibles en un campo libre y un moderador debe revisar cada publicación.
