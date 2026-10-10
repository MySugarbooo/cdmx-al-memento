# Cat y las Estrellas Perdidas

Un juego de plataformas 2D original en español. Cat es la heroína de Lunaria, una joven aventurera con bufanda mágica que debe recuperar cuatro constelaciones para volver a encender las estrellas.

## Funcionalidad
- **16 niveles**, agrupados en 4 capítulos con historias propias.
- Juego 100 % en JavaScript y Canvas, sin servidor ni dependencias para jugar.
- Personaje Cat ilustrado por el motor Canvas, con doble salto, tres corazones, enemigos, pinchos, destellos, estrella especial, cristales de guardado y portales.
- Música y efectos chiptune originales, sintetizados con Web Audio. Empieza tras interacción del usuario; se puede silenciar.
- Controles de teclado (A/D, flechas, W, Espacio, P, M, R) y controles táctiles en móvil.
- Progreso guardado localmente: niveles desbloqueados, estrellas, mejor puntuación de cada nivel, punto de control, preferencias musicales, final completado.
- Guardado seguro con fallback si localStorage no está disponible.
- Mapa de niveles con etapas bloqueadas y rejugables, pausa y reinicio.
- Páginas legales, contacto, seis guías originales, preguntas frecuentes y sitemap.
- Todo funciona sin librerías externas salvo tipografía Google Fonts; AdSense usa el script oficial.

## Publicación gratuita con Cloudflare Pages
Repositorio: `MySugarbooo/cdmx-al-memento`
Rama de producción **independiente**: `cat-estrellas`.
Crear un proyecto nuevo de Pages desde el mismo repositorio y ajustar:

- Nombre sugerido: `cat-estrellas` (si está disponible)
- Production branch: `cat-estrellas`
- Framework preset: `None`
- Build command: dejar vacío
- Output directory: `.`
- Root directory: raíz

El dominio sugerido es `https://cat-estrellas.pages.dev/` y **no estará confirmado hasta que Cloudflare lo asigne**. Si asigna otro, editar `robots.txt` y `sitemap.xml`.

Antes de crear el proyecto independiente, puede existir una vista previa en `https://cat-estrellas.cdmx-al-memento.pages.dev/` si Cloudflare despliega ramas de preview del proyecto existente. Esto NO equivale a tener un proyecto final independiente.

## Publicidad
Ya instalado el script oficial de Google AdSense para el editor `ca-pub-6521969406386261`, metaetiqueta y archivo `ads.txt`.
**No implica aprobación**: hay que añadir el dominio final en la sección `Sitios` de la misma cuenta AdSense y solicitar revisión. La ubicación y presentación de anuncios depende de Google. Evitar anuncios superpuestos a los controles; considerar exclusiones apropiadas y consentimiento publicitario donde corresponda. No ofrecer recompensas por clics en anuncios.

## Privacidad y almacenamiento
`localStorage` utiliza la clave `cat-lunaria-save-v1`. La partida se conserva solo en el navegador. Los proveedores de hosting, fuentes y anuncios pueden procesar datos técnicos, como indica `privacidad.html`.

Contacto: `sanchezaxochitl@gmail.com`.

## Mantenimiento
Para crear más niveles, editar `assets/levels.js`. Música `assets/audio.js`, motor `assets/game.js`, diseño `assets/site.css`. Cambiar textos legales o de privacidad si se agregan servicios externos. 
