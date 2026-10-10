# UMBRAL 9: Ecos del Vacío

**FPS jugable, original y gratuito**, creado desde cero con HTML5 Canvas, raycasting en JavaScript y Web Audio. No utiliza motores comerciales, bibliotecas gráficas ni servicios de juego externos.

> En 2189, Darío Vega entra a ÍCARO-9 porque recibe una señal de socorro grabada con su propia voz... desde mañana. Lo que encuentra allí recuerda a la tripulación, pero nunca fue humano.

## Incluye

- Primera persona 3D por raycasting de 480 rayos a resolución 960×540, texturas generadas con Canvas y criaturas de tipo billboard dibujadas proceduralmente.
- **6 misiones** completas divididas en 3 actos; escenarios, mensajes, registros y desenlaces únicos.
- **3 armas**: P9 Pulso, carabina automática AR-6 y dispersor TH-12. Munición, recarga y mira asistida visualmente.
- **5 tipos de criaturas** (Acechador, Vidente, Bruto, Matriz, Heraldo), con persecución, proyectiles y daño.
- Objetivos por misión: recuperar memorias, derrotar al jefe cuando corresponda, y alcanzar la salida.
- Música ambiental de 6 composiciones suaves de ciencia ficción, sintetizadas mediante Web Audio; efectos para disparos, daños y hallazgos. Sin canciones externas ni derechos de música comercial.
- Guardado en localStorage tras completar las misiones y de los registros que vas recuperando; ajustes de audio, armas desbloqueadas por avance.
- Soporte para teclado/ratón (pointer lock), pantalla completa y controles táctiles de móvil (joystick, apuntar arrastrando y botones de disparar, esquivar, recargar y cambiar de arma).
- Página de privacidad, contacto y términos. **Sin anuncios por ahora**.

## Controles

| Acción | Tecla |
|---|---|
| Avanzar / retroceder | W / S |
| Desplazarse lateralmente | A / D |
| Mirar | Ratón (clic en juego para capturar), flechas izquierda/derecha o arrastrar en pantalla táctil |
| Disparar | Clic izquierdo o botón táctil |
| Recargar | R |
| Cambiar arma | 1, 2, 3 |
| Esquivar | Espacio |
| Correr | Mayús |
| Interactuar | E (las memorias también se recogen al acercarte) |
| Pausar | P o Esc |
| Música | M |

## Cómo jugar

1. Abre `index.html` en un navegador actual o sirve la carpeta estática desde un servidor HTTP.
2. Selecciona «Iniciar operación». Se mostrará el prólogo de cada misión.
3. Recoge las memorias (objetos azules en habitaciones laterales) y neutraliza al jefe en misiones 3 y 6.
4. Cruza el portal luminoso del extremo opuesto a la entrada para desbloquear la siguiente misión.
5. Tu progreso se conserva automáticamente **en este navegador** al concluir un nivel; los registros recogidos se conservan al encontrarlos. No se sincroniza entre dispositivos.

## Publicar GRATIS en Cloudflare Pages

1. Importa GitHub `MySugarbooo/cdmx-al-memento`.
2. Rama de producción independiente **`umbral-9`**.
3. Nombre de proyecto recomendado `umbral-9` si está disponible.
4. Framework: `None`; directorio de salida `.`; comando de compilación vacío.
5. Cambia los enlaces en `sitemap.xml` y `robots.txt` si Cloudflare te asigna un dominio distinto al previsto.

La web está lista para añadir AdSense después de completar la revisión editorial y de contenido, pero **no incluye código de anuncios, banners ni `ads.txt` por ahora**.

## Privacidad y mantenimiento

- Guarda una sola clave en localStorage: `umbral9-progress-v1`.
- No hay cuentas, perfiles, descargas de datos de juego ni subida de datos a un backend.
- `assets/world.js`: datos, mapas, guiones de misiones. `assets/game.js`: mecánicas, controles, enemigos, progreso. `assets/renderer.js`: motor 3D. `assets/audio.js`: música original. `assets/style.css`: interfaz.
- Correo: sanchezaxochitl@gmail.com.

© 2026. Historia, gráficos y música creados para el juego. No está afiliado con Halo, Doom ni sus titulares.
