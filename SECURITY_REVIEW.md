# Revisión de seguridad — 2026-10-27

## Comprobado en el código
- `firebase/firestore.rules` YA existe. Permite leer comentarios, crear únicamente con usuario autenticado y UID coincidente, prohíbe actualizaciones y permite eliminar solo al autor. **No se ha verificado si esas reglas están desplegadas en Firebase**.
- Los textos del foro se insertan con `textContent`, no como HTML: defensa correcta frente a XSS en esas rutas.
- `assets/comments-config.js` contiene parámetros públicos de configuración de Firebase, **no son por sí solos credenciales secretas**.
- No hay límites de frecuencia verificables del lado del servidor para creación de publicaciones. Las validaciones JS se pueden eludir. Prioridad: abuso/spam.
- `_headers` añadido en esta rama. Requiere desplegar y verificar respuestas reales.

## Pasos para activar y verificar
1. En Firebase Console > Firestore Database > Rules, comparar las reglas desplegadas con `firebase/firestore.rules`. **No reemplazar sin probar con Rules Playground o Emulator**.
2. Probar: anónimo puede leer y no escribir; usuario A puede crear/borrar solo lo propio; usuario B no puede borrar de A; UID falso y campos adicionales son rechazados.
3. En Firebase Authentication, revisar dominios autorizados y proveedores activos. Retirar dominios que no se utilicen.
4. Habilitar App Check para Firestore tras probar compatibilidad web y considerar controles antispam del lado servidor. App Check no sustituye las reglas ni garantiza límites de publicación.
5. Tras desplegar `_headers`, verificar `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` y `Permissions-Policy` en el dominio real.
6. Revisar alertas de secret scanning y Dependabot en GitHub, si están disponibles. Rotar **solo** credenciales secretas realmente expuestas.
7. Antes de activar una CSP, inventariar scripts, Firebase, mapas y publicidad para evitar romper el portal.

## Estado
No se ha realizado una prueba de penetración ni comprobación autenticada de Firebase. Esta rama no se ha desplegado. No hay evidencia para afirmar vulnerabilidad crítica confirmada.
