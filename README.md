# RitmoCroma

Visualizador musical con once modos, ondas, cajas que laten, espectros y partículas sincronizados con el audio. Procesamiento privado con Web Audio, carga de canciones locales, lista de reproducción, controles de color y micrófono opcional.

Sitio estático independiente. Archivo `index.html` autónomo: todo CSS y JS integrado. Sin back-end, cuentas, anuncios ni recopilación de audio.

Para publicar en Cloudflare Pages usa el repositorio `MySugarbooo/cdmx-al-memento`, rama `ritmocroma`, preset None, sin build command, output `.`.

## Actualización: efectos orgánicos y optimización

Se conservan Aurora, Espectro, Órbita, Pulse Boxes, Ondas, Galaxia, Medusas de luz y Jardín cristal. Se sustituyeron Lluvia estelar, Túnel infinito y Luciérnagas por **Loto bioluminiscente**, **Corales de neón** y **Polen cristalino**.

La visualización es local y responde en vivo al análisis de graves, medios y agudos. Mejoras de rendimiento: tope de 45 FPS y DPR 1,35 en pantallas compactas, 60 FPS y DPR máximo 1,8 en pantallas amplias; se pausa el renderizado en pestañas ocultas, se reduce la geometría de Medusas y Jardín, y los tres efectos nuevos usan cantidades fijas de formas y partículas sin efectos borrosos por elemento.
