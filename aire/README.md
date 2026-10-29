# Aire y clima · CDMX AL MEMENTO (etapa 8)

Página: `/aire/`, con acceso desde portada, Avisos y Mi alcaldía.

## Tres fuentes distintas, tres significados

1. **Índice AIRE Y SALUD oficial (SEDEMA / Aire CDMX):** se consulta `https://www.aire.cdmx.gob.mx/ultima-hora-reporte.php`, con respaldo de `default.php`. La API `/api/aire` extrae categoría (BUENA, ACEPTABLE, MALA, MUY MALA, EXTREMADAMENTE MALA), riesgo, contaminante y **hora de la fuente**. El índice es **general**: el reporte ligero de estaciones tiene campos de calidad vacíos; por eso NO se representa el mismo índice como medición de cada alcaldía.
2. **Pronóstico meteorológico por alcaldía:** el endpoint existente `/api/clima?alcaldia=...` consulta **MET Norway Locationforecast 2.0** (CC BY 4.0) para una coordenada representativa de las 16 alcaldías. Incluye temperatura, humedad, viento y cantidad prevista de precipitación a 1 o 6 horas, cuando el modelo la proporciona. El pronóstico no es una medición local de campo y la cantidad prevista de lluvia **no es una probabilidad**. MET Norway: https://api.met.no/ y https://api.met.no/doc/
3. **Comunicados de contingencia:** `/api/contingencias` lee titulares de comunicados de la **Comisión Ambiental de la Megalópolis (CAMe)**: `https://www.gob.mx/comisionambiental/es/archivo/prensa`. Cada aviso muestra la fecha de publicación y acceso a la fuente. Las activaciones/suspensiones históricas no describen la situación **vigente**; nunca se infiere si hay contingencia activa por el índice general o la existencia de un comunicado antiguo.

## Seguridad, frescura y privacidad

- El servidor devuelve `status: unavailable` y la UI **no coloca un semáforo** si el índice oficial tiene una antigüedad superior a 150 minutos, la fecha es inválida, la fuente cambia de formato o faltan contaminantes verificables.
- El índice conserva `reported_at` de la fuente y `checked_at` de la consulta por separado. La caché exitosa es de 10 minutos; los errores no se almacenan.
- Los comunicados CAMe son archivos públicos fechados y se cachean 30 minutos. No se anuncia «contingencia activa» o «suspendida actualmente» sin una verificación vigente.
- El clima usa pronósticos con fecha y descarta valores atrasados (más de 3 horas), irreales o sin atribución. La API existente se amplió sin renombrar campos usados por la cinta meteorológica.
- Se consulta solo una de las coordenadas **predefinidas de referencia** por alcaldía, nunca la ubicación GPS, una dirección ni coordenadas suministradas por el visitante.
- El selector puede reutilizar la preferencia local `cdmx.memento.alcaldia.v1`, guardada solo en el navegador cuando el visitante elige alcaldía; no se envía el valor como perfil personal ni a Firebase.
- No requiere nuevas claves de API, cuentas de usuario, permisos de Firebase, cobros ni cambios en AdSense.
- No se guarda una base histórica personal de síntomas o actividad. Las recomendaciones de salud son generales y enlazan al material oficial; no son indicaciones médicas individualizadas.

## Diagnóstico

1. Abrir `/api/aire`. Un resultado válido debe tener `status: ok`, `air.category`, `air.risk`, `air.pollutants`, `air.reported_at` reciente. Si muestra `unavailable`, revisar el reporte oficial directamente y sus fechas; **no ajustar el índice a mano**.
2. Abrir `/api/clima?alcaldia=Cuauht%C3%A9moc` y comprobar que la fecha del pronóstico sea reciente. Los campos nuevos `precipitation_mm` y `precipitation_window_hours` pueden ser `null`.
3. Abrir `/api/contingencias` y comprobar `advisories`. Los eventos antiguos se identifican como históricos, incluso si el último dice «SE SUSPENDE».
4. Revisar funciones de Cloudflare Pages, despliegue y errores 404 en los archivos `/assets/aire.js` y `/assets/aire.css`.

## Pruebas

- `node --check assets/aire.js`
- `node --check --input-type=module < functions/api/aire.js`
- `node --check --input-type=module < functions/api/contingencias.js`
- `node tests/test_aire_api.mjs`
- `python -m unittest discover -s tests -p 'test_air_page.py' -v`

Las pruebas de regresión se integraron en el workflow de GitHub Actions que ya actualiza noticias. No se reemplazó ninguna regla de Firebase ni se cambiaron las operaciones del foro.

## Fuentes editoriales

- Índice aire y salud CDMX: https://www.aire.cdmx.gob.mx/ultima-hora-reporte.php
- Explicación de bandas y recomendaciones: https://www.gob.mx/aire/recomendaciones.html
- Boletines oficiales CAMe: https://www.gob.mx/comisionambiental/es/archivo/prensa
- Pronósticos meteorológicos MET Norway: https://api.met.no/
