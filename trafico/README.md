# Tráfico, marchas y cierres · CDMX AL MEMENTO

Etapa 7 del plan editorial. Página: `/trafico/`.

## Qué ofrece

- Enlaces directos al [Centro de Orientación Vial de la SSC](https://x.com/OVIALCDMX), la [Agenda de Movilizaciones](https://www.ssc.cdmx.gob.mx/ciudadania/agenda-de-movilizaciones-sociales) y el [C5](https://x.com/C5_CDMX).
- Titulares **periodísticos**, recopilados de Google News RSS, sobre marchas, cierres viales, bloqueos, obras e incidentes viales relacionados con CDMX.
- Hora y fecha de **publicación del titular**, su medio original, alcaldía únicamente si aparece en el titular, buscador y filtros por tema y alcaldía.
- Mostrar solo titulares de las **últimas 48 horas**, no como incidencias activas.
- Índice automático en `/api/trafico` mediante Cloudflare Pages Functions, caché de 15 minutos para consultas correctas; los errores transitorios no se guardan en caché y tres búsquedas acotadas de Google News.
- Respaldo mediante `news.json` si la API de titulares no devuelve noticias. Ese respaldo **tampoco** afirma estados del tráfico.

## Lo que NO hace

- No consulta ni reproduce una API pública de cierres activos confirmados por la SSC. Los artículos enlazados no sustituyen las fuentes oficiales.
- No muestra mapas de bloqueos activos ni rutas alternativas calculadas.
- No afirma que una marcha prevista se haya realizado ni que un cierre siga vigente.
- No presenta noticias de otras ciudades ni titulares anteriores a 48 horas como actuales.
- No requiere permiso de ubicación, cuenta de Google, Firebase, almacenamiento en navegador ni claves de API.
- No infiere calles o tramos: si la alcaldía no aparece en el titular, se muestra «No precisada».

## Fuentes y verificación

El Centro de Orientación Vial y la SSC publican información sobre afectaciones y alternativas viales. La Agenda de Movilizaciones de la SSC contiene actividades programadas, pero su programación no confirma cierres. Los canales de X pueden requerir inicio de sesión en esa plataforma. Ante una emergencia real, llama al 911.

La API solo devuelve títulos, medio, fecha, categoría inferida, alcaldía mencionada y el enlace a Google News. No almacena datos de tránsito como hecho comprobado ni reproduce cuerpos completos de los artículos.

El reloj de la interfaz muestra cuándo se consultaron los titulares, **no** la hora del cierre ni de la normalización de las vías. La fecha de cada tarjeta es la publicada por su medio.

## Pruebas

- `node --check --input-type=module < functions/api/trafico.js`
- `node --check assets/trafico.js`
- `node tests/test_trafico_api.mjs`
- `python -m unittest tests.test_traffic_page` o descubrimiento desde `tests/`.

Estas pruebas se ejecutan en el flujo existente de GitHub Actions cuando cambian archivos de tráfico. No se crea ningún workflow recurrente nuevo ni se altera la configuración de Firebase.

## Diagnóstico

Si la sección no tiene noticias, comprobar primero `/api/trafico`, cuyo objeto JSON devuelve `status`, `streams_consulted`, `checked_at` y `articles`. Si todos los flujos RSS fallan, devuelve `status: unavailable` y ningún aviso falso. El cliente intenta el respaldo `news.json`; si tampoco encuentra titulares pertinentes, muestra un mensaje de ausencia de titulares y conserva los accesos oficiales.

Los titulares se filtran por fecha, localización expresa y palabras clave. Este filtrado reduce errores, pero no reemplaza una revisión editorial de cada caso.
