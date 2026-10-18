# ✦ Escribe Pro — editor de documentos para el navegador

Proyecto web estático, responsive y gratuito creado con **HTML, CSS y JavaScript puro**. No necesita cuentas, bases de datos remotas ni servidores.

## Funciones incluidas

- Crear, guardar, buscar, duplicar, renombrar y eliminar **varios documentos**.
- Guardado automático en **IndexedDB**, con respaldo alternativo en `localStorage` cuando sea posible.
- Texto enriquecido: negritas, cursivas, subrayado, tachado, títulos, colores, fuentes, tamaños, párrafos alineados, listas y sangrías.
- Insertar tablas, imágenes, enlaces, fechas, líneas y saltos de página.
- Ajustar el tamaño de imágenes seleccionadas al 25 %, 50 % y 100 % del ancho disponible.
- Opciones de papel **A4 y Carta**, interlineado, márgenes, encabezado, pie y numeración de páginas en DOCX e impresión compatible.
- Plantillas de **carta, currículum, informe y apuntes**.
- Buscar texto, buscar siguiente y reemplazar una o todas las coincidencias.
- Contador de palabras, caracteres y lectura; zoom; modo oscuro.
- Importación de archivos **DOCX, HTML y TXT**; exportación a **DOCX, HTML y TXT**.
- Imprimir o guardar **PDF** usando la ventana de impresión del navegador.
- Asistente local: convertir selección a mayúsculas/minúsculas, limpiar espacios, copiar texto y resumen **extractivo basado en frecuencias**.
- Diseño adaptable para móviles y computadoras.

## Cómo probarlo

1. Descarga y descomprime `escribe-pro.zip`.
2. Entra a la carpeta `escribe-pro/`.
3. Abre `index.html` en Chrome, Edge, Firefox o Safari modernos.
4. Para probar almacenamiento más estable, es recomendable publicarlo con GitHub Pages o servirlo con un servidor local, por ejemplo `python -m http.server 8000` y entrar a `http://localhost:8000`.

**Nota:** Para importar/exportar archivos DOCX, la aplicación debe poder cargar las bibliotecas `docx` y `mammoth` desde jsDelivr (requiere internet). Las demás herramientas no dependen de estas bibliotecas.

## Cómo publicarlo gratis en GitHub Pages

1. Ve a https://github.com y accede a tu cuenta.
2. Haz clic en el signo `+` y selecciona **New repository**.
3. Nombra el repositorio `escribe-pro`, elige **Public** y pulsa **Create repository**.
4. En el repositorio, selecciona **Add file → Upload files**.
5. **No subas el ZIP.** Sube directamente a la raíz del repositorio estos archivos:
   - `index.html`
   - `style.css`
   - `script.js`
   - `favicon.svg`
   - `README.md` (opcional)
6. Pulsa **Commit changes**.
7. Ve a **Settings → Pages**.
8. En **Build and deployment**, selecciona **Deploy from a branch**.
9. Elige la rama **main** y la carpeta **/(root)** y pulsa **Save**.
10. GitHub mostrará tu URL después del despliegue (puede tardar unos minutos):

   `https://TU-USUARIO.github.io/escribe-pro/`

En caso de que no aparezca, consulta las acciones de **Actions** y la configuración **Pages** del repositorio.

## Estructura

```text
escribe-pro/
├── index.html       # Componentes y menús
├── style.css        # Diseño responsive + impresión
├── script.js        # Editor, documentos, exportación y asistente
├── favicon.svg      # Icono de la página
└── README.md        # Documentación
```

## Privacidad y limitaciones

- Los documentos se guardan **únicamente en el navegador y dispositivo en el que trabajas**. Publicar la página con GitHub Pages **no sincroniza** los documentos entre computadoras ni los guarda en GitHub.
- Si borras los datos del sitio, usas modo privado o cambias de dispositivo, puedes perder los documentos. Descarga copias DOCX, HTML o TXT con frecuencia.
- Es un editor ligero, **no una réplica completa de Microsoft Word**. Los DOCX complejos pueden perder elementos de diseño en la importación/exportación, como márgenes específicos, tablas anidadas o estilos avanzados.
- La edición se hace en **un lienzo continuo**, no con paginación automática exacta. El contador de páginas es **aproximado**. Los saltos de página manuales se respetan al imprimir/exportar.
- La numeración automática al guardar PDF depende del motor de impresión del navegador (los navegadores recientes basados en Chromium suelen soportar las cajas de margen CSS).
- La corrección ortográfica es la del navegador y depende del idioma configurado. El asistente **no es una IA generativa** y no necesita API de pago.
- Al exportar DOCX, las imágenes externas alojadas en otras páginas pueden no incluirse. Para mejores resultados, insértalas desde el dispositivo. Imágenes WEBP pueden no exportarse a Word dependiendo de su compatibilidad.
- Se usa `document.execCommand` para el formato básico en `contenteditable`; aunque funciona en navegadores actuales, está obsoleto, por lo que a futuro convendría migrar a un motor de edición dedicado para casos avanzados.

## Personalización

En `style.css`, cambia `--accent` para modificar el color principal. En `script.js`, modifica el objeto `templates` para agregar o editar plantillas.

## Bibliotecas externas

- [docx.js](https://github.com/dolanmiu/docx), licencia MIT: generación de DOCX.
- [Mammoth](https://github.com/mwilliamson/mammoth.js), licencia BSD-2-Clause: lectura de DOCX.

Ambas se cargan únicamente en el cliente; no es necesaria una API propia.