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

 const selections=new Map();
 const normalize=id=>String(id||"");
 function src(id){const image=images[id];return image?(image.url||'/assets/fotos/'+id+'.jpg'):''}
 function source(id){
  const item=images[id];
  if(!item)return '';
  if(item.source&&/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(item.source))return item.source;
  return 'https://commons.wikimedia.org/wiki/File:'+encodeURIComponent(item.file.replace(/ /g,'_'));
 }
 function hash(input){let h=2166136261;for(const cp of String(input||'')){h^=cp.codePointAt(0);h=Math.imul(h,16777619)}return h>>>0}
 function pick(category,title){
  const group=candidates(category);
  return group.length?group[hash(title)%group.length]:'';
 }
 function addCatalog(catalog){
  if(!catalog||!Array.isArray(catalog.photos))return 0;
  let added=0;
  for(const item of catalog.photos){
   if(!item||!/^archivo_[a-z0-9_]{2,50}$/.test(item.id)||images[item.id])continue;
   if(typeof item.author!=='string'||typeof item.topic!=='string'||typeof item.license!=='string')continue;
   if(!/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(item.source||''))continue;
   const cat=groups[item.category]?item.category:'CDMX';
   images[item.id]={file:item.file,author:item.author.slice(0,140),topic:item.topic.slice(0,140),license:item.license,licenseUrl:item.licenseUrl||'',source:item.source,category:cat};
   groups[cat].push(item.id);added++;
  }
  return added;
 }
 function addRecentCatalog(catalog){
  if(!catalog||!Array.isArray(catalog.photos))return 0;
  let added=0;
  const today=Date.now();
  for(const item of catalog.photos){
   if(!item||!/^reciente_[a-f0-9]{16}$/.test(item.id)||images[item.id])continue;
   if(!groups[item.category]||!/^https:\/\/upload\.wikimedia\.org\/wikipedia\/commons\//.test(item.url||''))continue;
   if(!/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(item.source||''))continue;
   if(!/^https:\/\/creativecommons\.org\//.test(item.licenseUrl||''))continue;
   if(typeof item.author!=='string'||!item.author.trim()||typeof item.topic!=='string'||typeof item.license!=='string')continue;
   const uploaded=Date.parse(item.uploaded_at||'');
   // Nunca revivir fotografías cuya subida ya quedó fuera de la ventana editorial.
   if(!Number.isFinite(uploaded)||uploaded>today+86400000||today-uploaded>181*86400000)continue;
   images[item.id]={
    file:item.file,author:item.author.slice(0,130),topic:item.topic.slice(0,150),
    license:item.license,licenseUrl:item.licenseUrl,source:item.source,category:item.category,
    url:item.url,uploaded_at:item.uploaded_at,captured_at:item.captured_at||null
   };
   groups[item.category].unshift(item.id);
   added++;
  }
  return added;
 }
 function candidatesForArticle(category){
  const list=groups[category]||groups.CDMX;
  return [...list.filter(id=>Boolean(images[id]?.uploaded_at)),...list.filter(id=>!images[id]?.uploaded_at)];
 }
 function prepare(articles){
  selections.clear();
  const used=new Set(),waiting=[];
  // Primera vuelta: reservar una fotografía local distinta de la categoría correspondiente.
  for(const article of articles){
   const candidates=candidatesForArticle(article.category);
   const start=0;
   let choice='';
   for(let i=0;i<candidates.length;i++){
    const id=candidates[(start+i)%candidates.length];
    if(!used.has(id)){choice=id;break}
   }
   if(choice){used.add(choice);selections.set(article.url,choice)}
   else waiting.push(article);
  }
  // Segunda vuelta: usar otros puntos de la CDMX en los temas con menor disponibilidad.
  const all=Object.keys(images),general=groups.CDMX;
  for(const article of waiting){
   const begin=hash(article.title);
   const available=candidatesForArticle(article.category).concat(general,all.filter(id=>!general.includes(id)));
   let choice='';
   for(let i=0;i<available.length;i++){
    const id=available[(begin+i)%available.length];
    if(!used.has(id)){choice=id;break}
   }
   if(!choice)choice=pick(article.category,article.title);
   if(choice){used.add(choice);selections.set(article.url,choice)}
  }
  return {assigned:selections.size,distinct:new Set(selections.values()).size,available:all.length};
 }
 function forArticle(article){return selections.get(article.url)||pick(article.category,article.title)}
 function alternatives(category,exclude){
  const preferred=candidatesForArticle(category).concat(groups.CDMX);
  return [...new Set(preferred.concat(Object.keys(images)))].filter(id=>id!==exclude);
 }
 window.CDMX_FOTOS={images,groups,src,source,pick,addCatalog,addRecentCatalog,candidatesForArticle,prepare,forArticle,alternatives};
})();