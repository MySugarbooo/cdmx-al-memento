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
   // El catálogo histórico contiene algunos archivos de otras ciudades.
   const title=String(item.file||'').toLocaleLowerCase('es-MX');
   if(/louisville|kentucky|zacatecas|chihuahua|san francisco|palace of fine arts/i.test(title))continue;
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
   if(!groups[item.category]||!/^https:\/\/(?:upload\.wikimedia\.org\/wikipedia\/commons\/|thumb\.wikimedia\.org\/wikipedia\/commons\/thumb\/)/.test(item.url||''))continue;
   if(!/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(item.source||''))continue;
   if(!/^https:\/\/creativecommons\.org\//.test(item.licenseUrl||''))continue;
   // Protección adicional para el navegador: rechazar imágenes de otras ciudades.
   const title=String(item.file||'').toLocaleLowerCase('es-MX');
   if(/louisville|kentucky|zacatecas|chihuahua|san francisco|barranquilla|bogot[aá]|colombia|medell[ií]n|california/.test(title))continue;
   if(!item.reviewed_location&&!/ciudad de m[eé]xico|cdmx|mexico city|distrito federal|z[oó]calo[- ]tenochtitlan|torre latinoamericana|paseo de la reforma/i.test(title))continue;
   if(/\b20\d{2}\b/.test(title)&&Math.max(...(title.match(/\b20\d{2}\b/g)||[]).map(Number))<new Date().getFullYear())continue;
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
   const start=hash(article.url)%candidates.length;
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
   const available=candidatesForArticle(article.category);
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
  const preferred=candidatesForArticle(category);
  return [...new Set(preferred)].filter(id=>id!==exclude);
 }
 window.CDMX_FOTOS={images,groups,src,source,pick,addCatalog,addRecentCatalog,candidatesForArticle,prepare,forArticle,alternatives};
})();
/* Fototeca editorial de 1,100 imágenes: no bloquea noticias si Wikimedia no responde. */
(()=>{
 const api=window.CDMX_FOTOS;
 if(!api)return;
 const norm=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const ignored=new Set(['ciudad','mexico','noticia','noticias','sobre','desde','para','entre','tras','ante','este','esta','varios','varias','alcaldia','alcaldias','fotografia','archivo','capital','tambien','reportan','reportan','sector','gobierno']);
 const hash=x=>{let h=2166136261;for(const cp of String(x||'')){h^=cp.codePointAt(0);h=Math.imul(h,16777619)}return h>>>0};
 const validSource=u=>/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(String(u||''));
 const validImage=u=>/^\/assets\/fotos\/[a-z0-9_]+\.jpg$/i.test(String(u||''))||/^https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons\//.test(String(u||''));
 const validLicense=u=>/^https:\/\/creativecommons\.org\//.test(String(u||''));
 const selections=new Map();
 const allKeys=[];
 function categoryFor(article){
  const text=norm(article?.title||'');
  if(/metrobus|metrob[uú]s|cablebus|cableb[uú]s|ecobici|ciclovia|autobus|trolebus|tr[aá]fico|vialidad/.test(text))return 'Movilidad';
  if(/\bmetro\b|\bestacion\b|\btren\b|linea 1|linea 2|linea 3|linea 12/.test(text))return 'Metro';
  if(/policia|patrulla|detencion|homicidio|asalto|robo|seguridad|fiscalia|bomberos|incendio/.test(text))return 'Seguridad';
  if(/lluvia|inundacion|tormenta|clima|aire|contaminacion|arboles|parque|medio ambiente/.test(text))return 'Medio Ambiente';
  if(/hospital|bache|drenaje|agua potable|basura|alumbrado|servicio publico|obras|pavimentacion/.test(text))return 'Servicios';
  if(/museo|concierto|exposicion|festival|bellas artes|teatro|cultura|danza/.test(text))return 'Cultura';
  const cat=String(article?.category||'CDMX');
  return api.groups[cat]?.length?cat:'CDMX';
 }
 function matchScore(item,article,category){
  const borough=norm(article?.borough||'');
  const title=norm(article?.title||'');
  const context=norm([item.topic,item.file,...(item.keywords||[])].join(' '));
  let score=item.category===category?55:item.category==='CDMX'?8:0;
  if(borough.length>5&&context.includes(borough))score+=115;
  const words=[...new Set(title.split(/[^a-z0-9]+/).filter(s=>s.length>4&&!ignored.has(s)))];
  for(const word of words){if(context.includes(word))score+=Math.min(word.length+3,16)}
  if(item.category==='Alcaldías'&&borough.length>5&&context.includes(borough))score+=35;
  return score;
 }
 function choose(article,used){
  const preferred=categoryFor(article),borough=norm(article?.borough||'');
  const pool=allKeys.filter(id=>{const p=api.images[id];
   return p.category===preferred||p.category==='CDMX'||(borough.length>5&&norm([p.topic,...(p.keywords||[])].join(' ')).includes(borough));
  });
  const chosen=pool.length?pool:allKeys;
  if(!chosen.length)return '';
  const seed=article?.url||article?.local_url||article?.title||'CDMX';
  let best='',bestScore=-Infinity;
  for(const id of chosen){if(used?.has(id))continue;const item=api.images[id];
   const score=matchScore(item,article,preferred)*100000+hash(seed+'|'+id)%100000;
   if(score>bestScore){best=id;bestScore=score}
  }
  return best||chosen[hash(seed)%chosen.length];
 }
 function forArticle(article){
  const key=String(article?.url||article?.local_url||article?.title||'');
  return selections.get(key)||choose(article,new Set());
 }
 function prepare(articles){
  selections.clear();const used=new Set();
  for(const item of (articles||[])){
   const key=String(item?.url||item?.local_url||item?.title||'');
   const id=choose(item,used);if(id){used.add(id);selections.set(key,id)}
  }
  return {assigned:selections.size,distinct:new Set(selections.values()).size,available:allKeys.length};
 }
 fetch('/assets/fotos/catalogo-editorial-1100.json',{cache:'no-cache'})
 .then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
 .then(data=>{
   const items=Array.isArray(data.photos)?data.photos:[];
   if(items.length<901||items.length!==data.count)throw Error('Cantidad de fotografías inconsistente');
   const ids=new Set(),files=new Set();
   for(const p of items){
    if(!p||!/^([a-z0-9_]+)$/.test(p.id)||ids.has(p.id)||files.has(norm(p.file))||
       !validImage(p.url)||!validSource(p.source)||!validLicense(p.licenseUrl)||!p.author||!p.license||!p.topic)
      throw Error('Metadatos fotográficos incompletos o repetidos');
    ids.add(p.id);files.add(norm(p.file));
   }
   for(const id of Object.keys(api.images))delete api.images[id];
   for(const cat of Object.keys(api.groups))api.groups[cat].length=0;
   for(const p of items){api.images[p.id]=p;allKeys.push(p.id);
    if(!api.groups[p.category])api.groups[p.category]=[];api.groups[p.category].push(p.id)}
   api.forArticle=forArticle;api.prepare=prepare;
   api.pick=(category,title)=>choose({category,title},new Set());
   api.src=id=>api.images[id]?.url||'';
   api.source=id=>api.images[id]?.source||'';
   api.candidatesForArticle=category=>(api.groups[category]||api.groups.CDMX||[]).slice();
   api.alternatives=(category,exclude)=>api.candidatesForArticle(category).filter(id=>id!==exclude);
   api.addCatalog=()=>0;api.addRecentCatalog=()=>0;
   api.ready=true;api.count=items.length;
   document.dispatchEvent(new Event('cdmx-fotos-ready'));
 }).catch(err=>console.warn('Fototeca ampliada no disponible; se conserva la selección local anterior.',err));
})();
