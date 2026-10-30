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
/* Fototeca editorial validada (100 fotografías): se carga sin bloquear el feed. */
(()=>{
 const api=window.CDMX_FOTOS;if(!api)return;
 const norm=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const block=new Set(['ciudad','mexico','noticia','noticias','sobre','desde','para','entre','tras','ante','este','esta','varios','varias','alcaldia','alcaldias','gobierno','fotos','fotografia']);
 const validSource=url=>/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(String(url||''));
 const validImage=url=>/^\/assets\/fotos\/[a-z0-9_]+\.jpg$/i.test(String(url||''))||/^https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons\//.test(String(url||''));
 const validLicense=url=>/^https?:\/\/creativecommons\.org\//.test(String(url||''));
 const hash=x=>{let h=2166136261;for(const c of String(x||'')){h^=c.codePointAt(0);h=Math.imul(h,16777619)}return h>>>0};
 const selections=new Map();let ready=false;
 function categoryFor(a){const cat=String(a?.category||'CDMX');const title=norm(a?.title||'');
  if(title.includes('metrobus')||title.includes('metrobús'))return 'Movilidad';
  if(/\bmetro\b|linea del metro|estacion del metro/.test(title))return 'Metro';
  if(/policia|patrulla|detencion|homicidio|robo|seguridad/.test(title))return 'Seguridad';
  if(/museo|concierto|exposicion|festival|bellas artes/.test(title))return 'Cultura';
  return Array.isArray(api.groups[cat])?cat:'CDMX';
 }
 function scorePhoto(p,a,preferred){
  const title=norm(a?.title||''),borough=norm(a?.borough||''),text=norm(title+' '+borough);
  const subject=norm(p.topic+' '+(p.keywords||[]).join(' '));
  let score=p.category===preferred?35:0;
  if(p.category==='CDMX'&&preferred!=='CDMX')score+=2;
  if(borough.length>4&&subject.includes(borough))score+=45;
  const words=new Set(text.split(/[^a-z0-9]+/).filter(x=>x.length>=5&&!block.has(x)));
  let semantic=0;
  for(const word of words){if(subject.includes(word))semantic+=8}
  score+=Math.min(semantic,40);
  if(preferred==='Metro'&&/metro|estacion|tren/.test(subject))score+=9;
  if(preferred==='Movilidad'&&/metrobus|autobus|reforma|transporte/.test(subject))score+=9;
  if(preferred==='Seguridad'&&/patrulla|policia/.test(subject))score+=9;
  return score;
 }
 function choose(a,used){
  const preferred=categoryFor(a);
  const all=Object.keys(api.images);
  const relevant=all.filter(id=>api.images[id]?.category===preferred);
  const list=relevant.length?relevant:all;
  if(!list.length)return '';
  const seed=a?.url||a?.local_url||a?.title||'CDMX';
  return list.map(id=>({id,score:scorePhoto(api.images[id],a,preferred),salt:hash(seed+'#'+id)}))
    .sort((a,b)=>b.score-a.score||a.salt-b.salt)
    .find(x=>!used?.has(x.id))?.id||list[hash(seed)%list.length];
 }
 function forArticle(a){const key=String(a?.url||a?.local_url||a?.title||'');return selections.get(key)||choose(a,new Set())}
 function prepare(articles){selections.clear();const used=new Set();for(const a of articles||[]){const key=String(a?.url||a?.local_url||a?.title||'');const id=choose(a,used);if(id){used.add(id);selections.set(key,id)}}return {assigned:selections.size,distinct:new Set(selections.values()).size,available:Object.keys(api.images).length}}
 fetch('/assets/fotos/seleccion-100.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('fototeca HTTP '+r.status);return r.json()})
 .then(json=>{
  const items=Array.isArray(json.photos)?json.photos:[];
  if(items.length!==100)throw Error('El catálogo debe contener 100 fotografías');
  const seen=new Set();
  for(const p of items){if(!p||!/^([a-z0-9_]+)$/.test(p.id)||!validImage(p.url)||!validSource(p.source)||!validLicense(p.licenseUrl)||!p.author||!p.license||seen.has(p.id))throw Error('Fotografía no acreditada: '+(p?.id||'?'));seen.add(p.id)}
  for(const key of Object.keys(api.images))delete api.images[key];
  for(const key of Object.keys(api.groups))api.groups[key].length=0;
  for(const p of items){api.images[p.id]=p;if(!api.groups[p.category])api.groups[p.category]=[];api.groups[p.category].push(p.id)}
  api.forArticle=forArticle;api.prepare=prepare;api.pick=(cat,title)=>choose({category:cat,title},new Set());
  api.src=id=>api.images[id]?.url||'';api.source=id=>api.images[id]?.source||'';
  api.candidatesForArticle=cat=>(api.groups[cat]||api.groups.CDMX||[]).slice();
  api.alternatives=(cat,exclude)=>api.candidatesForArticle(cat).filter(id=>id!==exclude);
  api.addCatalog=()=>0;api.addRecentCatalog=()=>0;
  api.ready=true;ready=true;
  document.dispatchEvent(new Event('cdmx-fotos-ready'));
 }).catch(err=>{console.warn('Fototeca de 100 imágenes no disponible: se mantiene el respaldo local.',err)});
})();
