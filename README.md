# ComprimeFácil MX — Herramientas gratuitas

Cuarto proyecto web independiente preparado para la misma cuenta AdSense del usuario.

## Funciones

- Imágenes JPG, PNG, WebP: reducción de dimensiones y/o calidad y conversión cuando se elige.
- PDF: reescritura básica sin aplanar (pdf-lib), o aplanado de páginas a JPEG con pdf.js y jsPDF. El aplanado destruye texto seleccionable, enlaces y formularios; se explica explícitamente en el sitio.
- DOCX: recodificación conservadora de imágenes internas y recomprimido ZIP; no admite DOC antiguo.
- TXT, MD, CSV, JSON, RTF: salida ZIP sin pérdida.
- Se descarga un resultado solo si ocupa menos que el archivo original, sin prometer porcentajes.
- Hasta 12 archivos y 40 MB por archivo, con limitaciones adicionales para PDF de muchas páginas.
- Procesamiento del contenido realizado en el navegador, sin enviar archivos a un backend.
- Dependencias JS externas desde cdnjs: pdf-lib 1.17.1, pdf.js 3.11.174, jsPDF 2.5.2, JSZip 3.10.1. La conexión es necesaria para obtener las bibliotecas.

## Publicación gratuita en Cloudflare

Este sitio está en la rama `comprimefacil-mx` del repositorio `MySugarbooo/cdmx-al-memento`. Es una rama con árbol independiente. No elegir `main` ni `cuenta-y-listo` ni `texto-claro`.

Crear un **nuevo proyecto Cloudflare Pages** importando el repositorio existente:

- Project name: `comprimefacil-mx` (si disponible)
- Production branch: `comprimefacil-mx`
- Framework preset: None
- Build command: vacío
- Build output directory: `.`
- Root directory: raíz

La URL final prevista es `https://comprimefacil-mx.pages.dev`, condicionada a que Cloudflare asigne ese nombre. Si es distinto, actualizar robots.txt y sitemap.xml.

## Monetización

Incluidos identificador `ca-pub-6521969406386261`, script de Google AdSense y archivo `ads.txt`.
Para habilitar anuncios debe agregarse el dominio final en **Sitios** de la misma cuenta existente de Google AdSense, solicitar la revisión y esperar la aprobación. No existe garantía de que Google lo apruebe ni de que genere ingresos.
Revisar la política de privacidad y configurar una CMP cuando sea exigible según regiones de visitantes.

Contacto directo: `sanchezaxochitl@gmail.com`.

## Mantenimiento editorial

Se incluyeron guías originales sobre formatos, calidad y privacidad. Las funciones son permanentes y no necesitan artículos diarios; conviene revisarlas y probarlas periódicamente y actualizar versiones de bibliotecas por seguridad.
