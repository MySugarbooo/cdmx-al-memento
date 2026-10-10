# Cuenta y Listo MX

Web independiente con 11 calculadoras interactivas, 8 guías originales, información editorial, contacto, privacidad y términos.

## Publicación gratuita sin cambiar CDMX AL MEMENTO

Este proyecto se encuentra en la rama `cuenta-y-listo` del repositorio `MySugarbooo/cdmx-al-memento`. La rama `main` conserva el periódico.

Para publicarlo en Cloudflare Pages:
1. En Workers & Pages, crea un **nuevo proyecto Pages** (no un Worker).
2. Elige **Import an existing Git repository** y selecciona `MySugarbooo/cdmx-al-memento`.
3. Project name sugerido: `cuentaylisto-mx` (si está disponible).
4. **Production branch: `cuenta-y-listo`**. Este es el paso importante para no publicar las noticias en vez de las calculadoras.
5. Framework preset: **None**; Build command: **vacío**; Build output directory: **.** (un punto); Root directory: raíz.
6. Deploy. Comprueba las calculadoras con los valores de ejemplo.

La URL puede variar: confirma la asignada en Cloudflare. No se garantiza que el nombre esté disponible.

## Google AdSense

No crees otra cuenta de AdSense. En **Sitios > Agregar sitio**, incorpora la URL que Cloudflare confirme y solicita su revisión solo cuando el contenido se encuentre listo. Hemos incluido la metaetiqueta de verificación `google-adsense-account` con `ca-pub-6521969406386261` y el `ads.txt` correspondiente. Los anuncios NO están habilitados; para servir publicidad tras la aprobación habrá que incorporar el script oficial y revisar el aviso de privacidad y consentimientos aplicables.

El sitio no garantiza aprobación, tráfico orgánico ni ingresos. Requiere mantenimiento y contenido de valor constante.

## Seguridad y privacidad

Las calculadoras se ejecutan en el navegador; no guardan datos ingresados ni registran usuarios. El formulario de contacto es un enlace mailto. No se incluyen paquetes JavaScript externos ni librerías de seguimiento.

## Fuentes usadas para contexto jurídico/fiscal de algunas guías

- [SAT, artículo 1 de la LIVA](https://wwwmat.sat.gob.mx/articulo/19848/articulo-1)
- [PROFECO, la propina es voluntaria](https://www.gob.mx/profeco/prensa/la-profeco-recuerda-a-las-y-los-consumidores-que-la-propina-es-voluntaria?idiom=es)
