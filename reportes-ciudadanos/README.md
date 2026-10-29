# Reportes ciudadanos · CDMX AL MEMENTO (etapa 9)

Página pública: `https://cdmx-al-memento.pages.dev/reportes-ciudadanos/`.

La etapa 9 crea un espacio comunitario para **reportes vecinales de servicios públicos**, separado del antiguo directorio `/reportes/` de análisis de noticias. La sección no está afiliada al Gobierno de CDMX y **no abre un folio de SUAC**.

## Funcionamiento

1. Una persona inicia sesión mediante Google Firebase Authentication, elige una de las 16 alcaldías, colonia opcional, categoría, título y descripción. No hay campos para domicilios completos, teléfono, correo o subida de fotografías.
2. El reporte se guarda en **`citizenReports/{id}`**, privado entre el titular y moderadores, con `status: pending`.
3. Un moderador con el mismo **custom claim `moderator: true`** ya usado en el foro puede aprobarlo o descartarlo.
4. La aprobación crea simultáneamente una copia en **`citizenReportsPublic/{id}`** sin UID de autor; los navegadores públicos consultan **exclusivamente esta segunda colección**.
5. El moderador puede cerrar el seguimiento editorial (`closed`) o retirar de la web (`rejected`). Cerrado no equivale a que el gobierno haya reparado un problema.
6. El titular puede consultar sus reportes con Google y retirar un envío pendiente o descartado. La consulta privada se filtra por su UID desde Firestore.
7. La lista pública admite filtros por alcaldía, categoría y texto, y no trata una publicación como hecho verificado.

## Publicación imprescindible de reglas

**Sin publicar las reglas nuevas el formulario no funciona.** GitHub y Cloudflare Pages **no publican reglas de Firebase**.

Abrir https://console.firebase.google.com/project/cdmx-al-memento/firestore/rules y pegar **el contenido completo** de:
https://github.com/MySugarbooo/cdmx-al-memento/blob/main/firebase/firestore.rules

Después pulsar **Publicar**. No sustituir únicamente el apartado nuevo, porque se perderían comentarios, votos, denuncias y auditorías de moderación existentes.

La seguridad de las dos colecciones no depende de ocultar la UI. Firestore aplica:
- Envíos privados solo del dueño autenticado con Google y no bloqueado.
- `create` en el privado solo como `pending` con `createdAt`/ `updatedAt` del servidor y esquema acotado.
- `update` del privado exclusivamente por moderador; solo estado, fecha y UID del moderador.
- `create/update/delete` público solo por moderador y **con reflejo de la actualización privada en el mismo batch**, verificado con `getAfter()`.
- Copia pública con campos exactos, sin `uid`, `email`, `name`, `photoURL` ni otros datos de autenticación.
- Se conservan literalmente reglas existentes de comentarios, votos, reportes del foro, historial privado y bloqueos.

## Cómo probar sin publicar información personal

- En incógnito, abrir la sección sin iniciar sesión: se ve lista pública, pero no el formulario.
- Con una cuenta Google normal, enviar un texto **claramente de prueba**, sin nombre ni domicilio particular; comprobar que aparece solo en Mis reportes.
- Con cuenta moderadora, usar sección Revisión editorial: aprobar el reporte. Confirmar que la lista pública muestra texto y colonia pero **no identidad**.
- Marcar «Cerrar seguimiento», luego «Retirar de la web»; comprobar que desaparece de la lista.
- Verificar en otra cuenta que los registros pendientes/rechazados siguen privados. El contenido del foro anterior debe seguir disponible.
- Si aparece `permission-denied`, verificar el despliegue de reglas completas y el token del rol moderador. **No publicar reglas abiertas de prueba.**

## Limitaciones

El enfriamiento de 60 segundos en el navegador solo reduce envíos accidentales; **no detiene a un atacante** que llame directamente a Firestore. Se requiere App Check y una cuota real impuesta desde un backend confiable para una protección robusta contra spam. La revisión manual debe evitar publicar datos identificables de terceros o acusaciones. El sistema no envía reportes a autoridades y no permite subir archivos para evitar imágenes sensibles.

**Canal gubernamental:** [SUAC](https://atencionciudadana.cdmx.gob.mx/), LOCATEL *0311, teléfono 55 5658 1111. Para emergencias: **911**.

## Comprobaciones técnicas

- `node --check assets/reportes-ciudadanos.js`
- `node tests/test_citizen_reports.mjs`
- `python -m unittest discover -s tests -p 'test_citizen_reports.py' -v`
- `firebase/firestore.rules` — revisar mediante la consola Firebase Rules / simulador de reglas antes de habilitar usuarios.

La ausencia de datos de autor en la copia pública es una barrera de privacidad; **no garantiza que un texto libre no contenga información personal**. La identidad del usuario sigue siendo procesada por Firebase Authentication y su UID se conserva en el registro privado.
