'use strict';
/* Imágenes JPEG almacenadas en Cloudflare Pages. Fuente y licencia en /creditos-fotograficos.html. */
(function(){
 const images={
  "reforma": {
    "file": "Mexico City Reforma skyline.jpg",
    "author": "Jonathan Salvador",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Paseo de la Reforma y Chapultepec",
    "category": "CDMX"
  },
  "angel": {
    "file": "El angel y la torre.jpg",
    "author": "Angel david villaceballos avila",
    "license": "CC0 1.0",
    "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/deed.es",
    "topic": "Ángel de la Independencia en la noche",
    "category": "CDMX"
  },
  "zocalo": {
    "file": "Vista del zócalo de Ciudad de México desde la Torre Latinoamericana.jpg",
    "author": "A01701617",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Zócalo visto desde la Torre Latinoamericana",
    "category": "CDMX"
  },
  "metro": {
    "file": "Metro CDMX IMG 0231 (25900065922).jpg",
    "author": "Gobierno CDMX",
    "license": "CC0 1.0",
    "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/deed.es",
    "topic": "Metro de Ciudad de México",
    "category": "Metro"
  },
  "metro2": {
    "file": "Metro de la Ciudad de México - 1.jpg",
    "author": "ProtoplasmaKid",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Vista aérea del Metro de Ciudad de México",
    "category": "Metro"
  },
  "movilidad": {
    "file": "Paseo de la Reforma, CDMX 191022.jpg",
    "author": "Juan Carlos Fonseca Mata",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Metrobús en Paseo de la Reforma",
    "category": "Movilidad"
  },
  "seguridad": {
    "file": "Patrulla cdmx.jpg",
    "author": "RainerRowe",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Patrulla de Ciudad de México",
    "category": "Seguridad"
  },
  "cultura": {
    "file": "Palacio de Bellas Artes, Mexico City, MX.jpg",
    "author": "Timothy Neesam",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Palacio de Bellas Artes",
    "category": "Cultura"
  },
  "cultura2": {
    "file": "Palacio de Bellas Artes - Mexico City - 01.jpg",
    "author": "Jarek Tuszyński",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Palacio de Bellas Artes al anochecer",
    "category": "Cultura"
  },
  "gobierno": {
    "file": "Palacio Nacional Ciudad de México.jpg",
    "author": "MichaelCamacho",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/deed.es",
    "topic": "Fachada del Palacio Nacional",
    "category": "Gobierno"
  }
};
 const groups={
  "Metro": [
    "metro",
    "metro2"
  ],
  "Movilidad": [
    "movilidad",
    "reforma"
  ],
  "Seguridad": [
    "seguridad"
  ],
  "Cultura": [
    "cultura",
    "cultura2"
  ],
  "Gobierno": [
    "gobierno"
  ],
  "CDMX": [
    "reforma",
    "angel",
    "zocalo"
  ]
};
 function src(id){return images[id]?'/assets/fotos/'+id+'.jpg':''}
 function source(id){return images[id]?'https://commons.wikimedia.org/wiki/File:'+encodeURIComponent(images[id].file.replace(/ /g,'_')):''}
 function pick(category,title){const group=groups[category]||groups.CDMX;let h=0;for(const cp of String(title||''))h=((h*31)+cp.codePointAt(0))>>>0;return group[h%group.length]}
 window.CDMX_FOTOS={images,groups,src,source,pick};
})();