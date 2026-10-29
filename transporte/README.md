# Estado de Metro y Metrobús · CDMX AL MEMENTO

La sección `/movilidad/` muestra las incidencias publicadas en el **tablero público de incidentes de movilidad de CDMX**, integrado en los sitios oficiales:

- Metro: https://www.metro.cdmx.gob.mx/la-red/estado-del-servicio
- Metrobús: https://metrobus.cdmx.gob.mx/ServicioMB
- Fuente subyacente: https://incidentesmovilidad.cdmx.gob.mx/public/bandejaEstadoServicio.xhtml

Este sitio **no está afiliado** a los operadores. Una consulta correcta no demuestra que la fuente haya actualizado sus incidencias recientemente, y la indicación oficial «Servicio Regular» **no confirma** trenes/autobuses circulando en este instante (en especial fuera de horario).

## Arquitectura y costo

1. La página solicita `/api/estado-transporte` a una **Cloudflare Pages Function** en `functions/api/estado-transporte.js`.
2. El servidor consulta por HTTPS los registros oficiales para `stc` y `mb`. El tablero usa PrimeFaces, requiere recuperar la segunda página del Metro y reconocer las líneas A/B a través de los iconos oficiales.
3. Se valida el número total declarado de registros, las 12 líneas del Metro y las 7 del Metrobús; se conservan múltiples incidencias en una línea. Si falta una línea o falla la consulta, **no** se publica un estado parcial como si fuera correcto.
4. La respuesta completa puede reutilizarse hasta **5 minutos** en caché de Cloudflare; un error, hasta 90 segundos.
5. Si la consulta falla, el navegador puede consultar `/transporte/estado.json` como respaldo. El sitio descarta cualquier dato con más de **90 minutos** y muestra «Sin verificación reciente» y enlaces oficiales.

La caché evita crear cientos de despliegues mensuales y no requiere servicios de pago, claves de API ni nuevas reglas de Firebase.

**No hay sondeo automático sin visitantes**: cuando alguien consulta la página se actualizan los datos si la caché ya caducó. La actualización en pantalla no es segundo a segundo.

## Respaldo manual de GitHub Actions

`.github/workflows/transporte.yml` ejecuta la consulta y actualiza el archivo estático cuando alguien inicia manualmente el workflow desde GitHub Actions. No tiene cron de publicación frecuente para evitar agotar la cuota de compilaciones de Cloudflare Pages.

Este respaldo utiliza `observatorio==0.1.0`, biblioteca libre **MIT** de felipao-mx: https://github.com/felipao-mx/observatorio. La biblioteca resuelve la paginación PrimeFaces y detecta consultas incompletas; nuestro script `scripts/estado_transporte.py` aplica sus propias comprobaciones adicionales y nunca sobrescribe un archivo con resultados incompletos.

## Calidad y límites editoriales

- `checked_at` es la **hora de consulta**, no la fecha de publicación o modificación del incidente.
- El estado puede cambiar antes de una nueva consulta; para viajar debe revisarse también el sitio oficial.
- Los incidentes se presentan como texto atribuido al tablero oficial, sin inventar motivos, lugares ni tiempos estimados.
- Una etiqueta «Servicio regular reportado» **no** significa que esté abierto, que circule un vehículo o que no existan problemas no reportados.
- No se almacenan ubicaciones GPS, nombres de viajeros ni identificadores de personas.
- Si el tablero oficial cambia estructura, la página mostrará un estado desconocido en lugar de afirmar que el servicio opera con normalidad.
- La página de Metrobús también tiene avisos separados de mantenimiento programado y elevadores; el tablero de incidentes **no** necesariamente incluye esos avisos. Consulte el enlace oficial para conocerlos.

Las pruebas están en `tests/test_transport_status.py` y `tests/test_transporte_api.mjs`.

## Diagnóstico

Si todas las líneas muestran «Sin verificación reciente», comprobar:

1. `/api/estado-transporte`: `status: "ok"` y diecinueve líneas únicas (más filas si una línea tiene varias incidencias).
2. `/transporte/estado.json`: respaldo estático, si se activó manualmente.
3. Disponibilidad del servidor oficial y errores de Cloudflare Pages Functions.
4. Que se conserven todas las líneas y la segunda página PrimeFaces. Nunca cambiar a «Servicio Regular» por defecto.
