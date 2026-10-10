'use strict';
/* Archivo fotográfico abierto: créditos en /creditos-fotograficos.html.
   Fotografías documentales históricas, NO imágenes del suceso noticioso. */
(function(){
const images={
  "reforma": {
    "file": "Mexico_City_Reforma_skyline.jpg",
    "hash": "6/66",
    "author": "Jonathan Salvador",
    "license": "4.0",
    "topic": "Panorama de Reforma y Chapultepec",
    "cat": "CDMX",
    "alt": "Fotografía panorámica de Reforma y Chapultepec, Ciudad de México"
  },
  "angel": {
    "file": "Angel_of_Independence_Mexico_City.jpg",
    "hash": "e/e4",
    "author": "Jpesch95",
    "license": "4.0",
    "topic": "Ángel de la Independencia",
    "cat": "CDMX",
    "alt": "Fotografía del Ángel de la Independencia en Ciudad de México"
  },
  "zocalo": {
    "file": "Vista_del_zócalo_de_Ciudad_de_México_desde_la_Torre_Latinoamericana.jpg",
    "hash": "9/9d",
    "author": "A01701617",
    "license": "4.0",
    "topic": "Vista del Zócalo",
    "cat": "CDMX",
    "alt": "Fotografía aérea del Zócalo vista desde la Torre Latinoamericana"
  },
  "metro": {
    "file": "Metro_Ciudad_de_Mexico_Estacion_San_Lazaro.JPG",
    "hash": "0/08",
    "author": "ProtoplasmaKid",
    "license": "3.0",
    "topic": "Estación San Lázaro del Metro",
    "cat": "Metro",
    "alt": "Fotografía de la estación San Lázaro del Metro de la Ciudad de México"
  },
  "metro2": {
    "file": "Metro_de_la_Ciudad_de_México_-_1.jpg",
    "hash": "e/e9",
    "author": "ProtoplasmaKid",
    "license": "4.0",
    "topic": "Metro de Ciudad de México",
    "cat": "Metro",
    "alt": "Fotografía aérea de instalaciones del Metro de Ciudad de México"
  },
  "movilidad": {
    "file": "Paseo_de_la_Reforma,_CDMX_191022.jpg",
    "hash": "0/03",
    "author": "Juan Carlos Fonseca Mata",
    "license": "4.0",
    "topic": "Metrobús en Paseo de la Reforma",
    "cat": "Movilidad",
    "alt": "Fotografía de un Metrobús frente a la Cámara de Senadores en Paseo de la Reforma"
  },
  "seguridad": {
    "file": "Patrulla_cdmx.jpg",
    "hash": "f/fd",
    "author": "RainerRowe",
    "license": "4.0",
    "topic": "Patrulla de Ciudad de México",
    "cat": "Seguridad",
    "alt": "Fotografía de archivo de una patrulla en Ciudad de México"
  },
  "cultura": {
    "file": "Palacio_de_Bellas_Artes,_Mexico_City,_MX.jpg",
    "hash": "c/c8",
    "author": "Timothy Neesam",
    "license": "4.0",
    "topic": "Palacio de Bellas Artes",
    "cat": "Cultura",
    "alt": "Fotografía del Palacio de Bellas Artes de Ciudad de México"
  },
  "cultura2": {
    "file": "Palacio_de_Bellas_Artes_-_Mexico_City_-_01.jpg",
    "hash": "f/f8",
    "author": "Jarek Tuszyński",
    "license": "4.0",
    "topic": "Bellas Artes",
    "cat": "Cultura",
    "alt": "Fotografía de la fachada del Palacio de Bellas Artes"
  },
  "gobierno": {
    "file": "Palacio_Nacional_Ciudad_de_México.jpg",
    "hash": "f/fd",
    "author": "MichaelCamacho",
    "license": "4.0",
    "topic": "Palacio Nacional",
    "cat": "Gobierno",
    "alt": "Fotografía de la fachada del Palacio Nacional en Ciudad de México"
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
function src(id,width=640){const x=images[id];if(!x)return '';const name=encodeURIComponent(x.file).replace(/%2F/g,'/');return 'https://upload.wikimedia.org/wikipedia/commons/thumb/'+x.hash+'/'+name+'/'+width+'px-'+name}
function source(id){const x=images[id];return x?'https://commons.wikimedia.org/wiki/File:'+encodeURIComponent(x.file):''}
function pick(category,title){const group=groups[category]||groups.CDMX;let h=0;for(const ch of String(title||''))h=((h*31)+ch.codePointAt(0))>>>0;return group[h%group.length]}
window.CDMX_FOTOS={images,groups,src,source,pick};
})();