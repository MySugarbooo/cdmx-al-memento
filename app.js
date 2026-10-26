'use strict';
const photoLibrary=window.CDMX_FOTOS;
let articles=[],category='',updated='';
const grid=document.getElementById('grid');
const featuredGrid=document.getElementById('featured-grid');
const featuredSection=document.getElementById('destacadas');
const search=document.getElementById('search');
const status=document.getElementById('status');
const currentTopic=document.getElementById('current-topic');
const homeView=document.getElementById('home-view');
const topicStage=document.getElementById('topic-stage');
const topicStageGrid=document.getElementById('topic-stage-grid');
const topicStageHeading=document.getElementById('topic-stage-heading');
const topicStageDescription=document.getElementById('topic-stage-description');
const topicStageCount=document.getElementById('topic-stage-count');
const newsSlidePanel=document.getElementById('news-slide-panel');
const reportList=document.getElementById('report-list');
const editorialLatest=document.getElementById('editorial-latest-link');
function element(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function validLink(u){try{const p=new URL(u);return p.protocol==='https:'&&p.hostname==='news.google.com'}catch{return false}}
// La noticia principal de la portada procede del mismo feed que las demás notas.
// Nunca fijar un titular antiguo en el HTML ni presentarlo como noticia de hoy.
const leadStory={
 kicker:document.getElementById('lead-story-kicker'),
 title:document.getElementById('lead-story-title'),
 summary:document.getElementById('lead-story-summary'),
 meta:document.getElementById('lead-story-meta'),
 link:document.getElementById('lead-story-link')
};
function drawLeadIllustration(article){
 const target=document.getElementById('lead-story-art');if(!target)return;
 if(!article){target.replaceChildren();return;}
 const title=String(article.title||'');const lower=title.toLocaleLowerCase('es-MX');
 const theme=/metro|tren|estaci[oó]n/.test(lower)?'metro':/gasolina|combustible/.test(lower)?'gas':/seguridad|polic[ií]a|operativo|accidente/.test(lower)?'security':/lluvia|clima|inundaci[oó]n/.test(lower)?'rain':'city';
 const svgParts={
 city:'<path d="M65 290V170h90v120M190 290V95h120v195M340 290V145h110v145M490 290V80h120v210M645 290V170h85v120" fill="#403455" stroke="#fff" stroke-width="8"/><path d="M220 120h55m-55 35h55m-55 35h55m-55 35h55m295-110h60m-60 40h60m-60 40h60" stroke="#ffdbed" stroke-width="14"/>',
 metro:'<rect x="180" y="85" width="440" height="220" rx="45" fill="#493a62" stroke="white" stroke-width="12"/><rect x="230" y="125" width="340" height="90" rx="14" fill="#b8e5ee"/><circle cx="270" cy="265" r="19" fill="#ffd3e9"/><circle cx="530" cy="265" r="19" fill="#ffd3e9"/><path d="M210 345h380" stroke="#fff" stroke-width="12"/>',
 gas:'<rect x="230" y="95" width="225" height="230" rx="18" fill="#493a62" stroke="#fff" stroke-width="10"/><rect x="260" y="130" width="165" height="90" rx="10" fill="#b8e5ee"/><path d="M455 145q110 0 100 95v45" fill="none" stroke="#fff" stroke-width="14"/><circle cx="550" cy="305" r="18" fill="#ffd3e9"/>',
 security:'<path d="M400 65l175 65v110q-20 90-175 135-155-45-175-135V130z" fill="#493a62" stroke="#fff" stroke-width="12"/><path d="M400 140v155m-75-80h150" stroke="#ffd3e9" stroke-width="22"/>',
 rain:'<path d="M260 215q-80-65 0-120 60-50 120 0 90-60 145 30 95 15 40 90z" fill="#fff" opacity=".8"/><path d="M290 260l-25 55m125-55l-25 55m125-55l-25 55" stroke="#b8e5ee" stroke-width="20" stroke-linecap="round"/>'};
 const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 390"><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#24203e"/><stop offset="1" stop-color="#b56b9b"/></linearGradient></defs><rect width="800" height="390" rx="22" fill="url(#bg)"/><circle cx="680" cy="80" r="125" fill="#fff" opacity=".10"/>'+svgParts[theme]+'<rect x="0" y="345" width="800" height="45" fill="#201b34" opacity=".85"/><text x="400" y="373" fill="#fff" font-size="19" font-family="Arial,sans-serif" text-anchor="middle">ILUSTRACIÓN DIGITAL · NO ES FOTO REAL</text></svg>';
 const img=document.createElement('img');img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);img.alt='Ilustración vectorial de contexto para: '+title;img.loading='eager';img.decoding='async';
 const credit=document.createElement('small');credit.textContent='Ilustración original creada con código · CDMX AL MEMENTO';
 const link=document.createElement('a');link.href=article.local_url||article.url||'#';link.className='lead-art-click';link.setAttribute('aria-label','Leer noticia: '+title);link.append(img);const badge=document.createElement('span');badge.className='lead-art-badge';badge.textContent='VER NOTICIA ↗';link.append(badge);target.replaceChildren(link,credit);
}
function renderLeadStory(items){
 if(!leadStory.title)return;
 const now=Date.now();
 const mxDay=date=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/Mexico_City',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
 const today=mxDay(new Date(now));
 const yesterday=mxDay(new Date(now-24*60*60*1000));
 const published=(Array.isArray(items)?items:[]).filter(a=>{
  const ts=Date.parse(a.published_at||'');
  return validLink(a.url)&&(!Number.isFinite(ts)||ts<=now+15*60*1000);
 });
 const fromDay=day=>published.filter(a=>Number.isFinite(Date.parse(a.published_at||''))&&mxDay(new Date(a.published_at))===day);
 const todayNews=fromDay(today),yesterdayNews=fromDay(yesterday);
 const candidates=todayNews.length?todayNews:yesterdayNews.length?yesterdayNews:published;
 // Se elige una portada distinta en cada visita, evitando repetir la anterior si hay opciones.
 const lastKey='cdmx-last-cover';
 let previous='';try{previous=localStorage.getItem(lastKey)||''}catch(e){}
 const importance=a=>{const title=String(a.title||'').toLowerCase();const age=(now-Date.parse(a.published_at||''))/3600000;return (/alerta|urgente|sismo|evacuaci[oó]n|suspensi[oó]n|cierre|inundaci[oó]n|protecci[oó]n civil/.test(title)?12:0)+(/metro|movilidad|seguridad|agua|transporte|salud/.test(title)?4:0)-Math.max(0,Number.isFinite(age)?age:72)/12};
 const ranked=[...candidates].sort((a,b)=>importance(b)-importance(a));
 const shortlist=ranked.slice(0,Math.min(5,ranked.length));
 const initialCover=(()=>{try{return sessionStorage.getItem('cdmx-visit-cover')||''}catch{return ''}})();
 const chosenOnEntry=candidates.find(a=>a.url===initialCover);
 const pool=shortlist.length>1?shortlist.filter(a=>a.url!==previous):shortlist;
 const random=pool.length?(globalThis.crypto?.getRandomValues?crypto.getRandomValues(new Uint32Array(1))[0]/4294967296:Math.random()):0;
 const newest=chosenOnEntry||(pool.length?pool[Math.floor(random*pool.length)]:null);
 if(newest){try{localStorage.setItem(lastKey,newest.url);sessionStorage.setItem('cdmx-visit-cover',newest.url)}catch(e){}}
 if(!newest){
  drawLeadIllustration(null);
  leadStory.kicker.textContent='SIN NOTICIAS PUBLICADAS DISPONIBLES';
  leadStory.title.textContent='No hay noticias publicadas disponibles para destacar';
  leadStory.summary.textContent='No hay noticias publicadas disponibles en el listado. Consulta el archivo.';
  leadStory.meta.textContent='Las noticias se mostrarán con su fecha original.';
  leadStory.link.href='/reportes/';
  leadStory.link.textContent='Consultar reportes anteriores →';
  return;
 }
 drawLeadIllustration(newest);
 const articleText=String(newest.brief?.lead||newest.summary||'');
 const readingMinutes=Math.max(1,Math.ceil((articleText.split(/\s+/).filter(Boolean).length+String(newest.title||'').split(/\s+/).length)/180));
 const editorial=document.getElementById('lead-editorial-extras');
 if(editorial){editorial.replaceChildren();
  const fast=element('p','lead-read-time','⏱️ Lectura aproximada: '+readingMinutes+' min');editorial.append(fast);
  const heading=element('h3','lead-extras-heading','En breve');editorial.append(heading);
  const list=element('ul','lead-quick-points');
  const points=[String(newest.title||''),String(newest.brief?.lead||'').trim(), 'Fuente: '+String(newest.source||'medio externo')+' · '+String(newest.published_at||'').slice(0,10)].filter(Boolean);
  for(const point of points.slice(0,3))list.append(element('li','',point.slice(0,210)));
  editorial.append(list);
  const related=candidates.filter(a=>a.url!==newest.url&&(a.category===newest.category||a.borough&&a.borough===newest.borough)).slice(0,3);
  if(related.length){editorial.append(element('h3','lead-extras-heading','Noticias relacionadas'));const rel=element('div','lead-related');for(const a of related){const link=element('a','',String(a.title||'').slice(0,125)+' ↗');link.href=a.local_url||a.url;rel.append(link)}editorial.append(rel)}
  if(shortlist.length>1){editorial.append(element('h3','lead-extras-heading','Otras noticias destacadas'));const carousel=element('div','lead-mini-carousel');for(const a of shortlist){const link=element('a','lead-mini-item',String(a.title||'').slice(0,95));link.href=a.local_url||a.url;carousel.append(link)}editorial.append(carousel)}
 }
 const breaking=/alerta|urgente|sismo|evacuaci[oó]n|suspensi[oó]n|cierre|inundaci[oó]n|protecci[oó]n civil/i.test(newest.title||'') && Number.isFinite(Date.parse(newest.published_at||'')) && now-Date.parse(newest.published_at)<6*3600000;
 leadStory.kicker.textContent=(breaking?'🔴 ÚLTIMA HORA · ':'')+(newest.borough?newest.borough.toLocaleUpperCase('es-MX')+' · ':'')+
  (todayNews.length?'NOTICIA DE HOY':yesterdayNews.length?'NOTICIA DE AYER':'NOTICIA DE ARCHIVO')+' · '+String(newest.category||'CDMX').toLocaleUpperCase('es-MX');
 leadStory.title.textContent=newest.title;
 leadStory.summary.textContent=newest.brief?.lead||
  'Titular recopilado de una fuente externa. Consulta la publicación original para verificar los detalles.';
 const when=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'medium',timeStyle:'short'})
  .format(new Date(newest.published_at));
 leadStory.meta.textContent='Fuente: '+(newest.source||'Medio externo')+
  ' · Publicado: '+when+' · Zona: '+(newest.location||'No precisada en el titular')+
  '. Resumen automatizado; consulta la fuente original.';
 leadStory.link.href=/^\/noticias\/\?id=[a-f0-9]{20}&mes=\d{4}-\d{2}$/.test(newest.local_url||'')
  ?newest.local_url:'/noticias/';
 leadStory.link.textContent='Leer la noticia y sus fuentes →';
}
function applyNewsFeed(feed){
 if(!feed||!Array.isArray(feed.articles))throw Error('Formato de noticias incorrecto');
 articles=feed.articles.filter(a=>a&&typeof a.title==='string'&&validLink(a.url));
 photoLibrary?.prepare(articles);
 updated=String(feed.updated||'sin fecha');
 render();
 renderLeadStory(articles);
}
let newsRefreshInProgress=false;
async function refreshHomepageNews(){
 if(newsRefreshInProgress)return;
 newsRefreshInProgress=true;
 try{
  const res=await fetch('/news.json?t='+Date.now(),{cache:'no-store'});
  if(!res.ok)throw Error('Noticias no disponibles');
  applyNewsFeed(await res.json());
 }catch(error){
  // Sin confirmación reciente no hay que seguir mostrando la nota principal anterior.
  if(articles.length)renderLeadStory(articles);else showEmbeddedNews();
  if(status)status.textContent='No se pudo comprobar si hay noticias nuevas. Se mantienen las publicadas.';
 }finally{newsRefreshInProgress=false}
}
function illustratedFallback(a,figure){
 const category=String(a.category||'CDMX');
 const scenes={Metro:['#203451','#b3d5ef','🚇'],Movilidad:['#284c57','#bde4e2','🚌'],Seguridad:['#26394f','#b8d2ef','🚓'],Cultura:['#543c61','#efd0ec','🎭'],Gobierno:['#3e4b65','#d6deed','🏛️'],CDMX:['#3b435f','#f6c4da','🏙️']};
 const [dark,light,icon]=scenes[category]||scenes.CDMX;
 const svg='<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="'+dark+'"/><stop offset="1" stop-color="'+light+'"/></linearGradient></defs><rect width="800" height="500" fill="url(#g)"/><circle cx="650" cy="90" r="105" fill="#fff" opacity=".15"/><path d="M0 410 L120 300 210 350 330 220 440 320 560 240 680 320 800 250 V500 H0Z" fill="#fff" opacity=".18"/><rect x="52" y="52" width="696" height="396" rx="24" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="4"/><text x="400" y="245" font-size="115" text-anchor="middle">'+icon+'</text><text x="400" y="325" fill="#fff" font-family="Arial,sans-serif" font-size="36" font-weight="bold" text-anchor="middle">ILUSTRACIÓN DE CONTEXTO</text><text x="400" y="365" fill="#fff" font-family="Arial,sans-serif" font-size="25" text-anchor="middle">'+category.replace(/[&<>"]/g,'')+'</text></svg>';
 figure.replaceChildren();
 const img=document.createElement('img');img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);img.alt='Ilustración digital de contexto sobre '+category+'. No es fotografía del acontecimiento.';img.loading='lazy';img.width=800;img.height=500;
 const label=element('span','visual-label','ILUSTRACIÓN DIGITAL · NO ES FOTO REAL');
 const credit=element('span','photo-credit-inline','© CDMX AL MEMENTO · Ilustración generada mediante código');
 figure.append(img,label,credit);
}
function articleVisual(a){
 const figure=element('div','news-visual');
 const assignedPhoto=a.photo;
 if(assignedPhoto&&assignedPhoto.url&&(/^\/assets\/(?:fotos|alcaldias)\/[a-z0-9_-]+\.jpg$/.test(assignedPhoto.url)||
  /^https:\/\/(?:thumb|upload)\.wikimedia\.org\/wikipedia\/commons\//.test(assignedPhoto.url))){
  const image=document.createElement('img');
  image.src=assignedPhoto.url;image.loading='lazy';image.decoding='async';image.width=640;image.height=400;
  image.alt='Fotografía real de contexto: '+(assignedPhoto.topic||'Ciudad de México')+'. No representa necesariamente el hecho.';
  image.onerror=()=>{illustratedFallback(a,figure)};
  const label=element('span','visual-label','FOTOGRAFÍA REAL DE CONTEXTO');
  const credit=element('a','photo-credit-inline','© '+(assignedPhoto.author||'Wikimedia Commons')+' · '+(assignedPhoto.license||'Licencia en Commons'));
  if(/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(assignedPhoto.source||'')){
   credit.href=assignedPhoto.source;credit.target='_blank';credit.rel='noopener noreferrer';
  }
  figure.append(image,label,credit);return figure;
 }
 const first=photoLibrary?.forArticle(a);
 const photo=first?photoLibrary.images[first]:null;
 if(!photo){illustratedFallback(a,figure);return figure}
 const image=document.createElement('img');
 image.loading='lazy';image.decoding='async';image.width=640;image.height=400;
 const label=element('span','visual-label','FOTOGRAFÍA DE CONTEXTO');
 const credit=element('a','photo-credit-inline');
 credit.target='_blank';credit.rel='noopener noreferrer';credit.title='Origen y licencia de la fotografía';
 let active=first;
 const attempted=new Set();
 function display(id){
  active=id;attempted.add(id);
  const entry=photoLibrary.images[id];
  image.src=photoLibrary.src(id);
  image.alt='Fotografía de archivo: '+entry.topic+'. No muestra el suceso descrito.';
  image.dataset.photoId=id;
  credit.textContent='© '+entry.author+' · '+entry.license+
   (entry.uploaded_at?' · Subida a Commons: '+entry.uploaded_at:'');

  credit.href=photoLibrary.source(id);
 }
 image.addEventListener('error',()=>{
  const next=photoLibrary.alternatives(a.category,active).find(id=>!attempted.has(id));
  if(next)display(next);
  else{illustratedFallback(a,figure)}
 });
 display(first);
 figure.append(image,label,credit);
 return figure;
}
// Cambiar también las fotografías de portada y temas cuando haya nuevas
// imágenes verificadas. En caso de error, restaurar la foto y atribución anterior.
function refreshStaticPhotos(){
 if(!photoLibrary?.candidatesForArticle)return;
 const rotation={};
 for(const img of document.querySelectorAll('img[data-fallback-photo]')){
  const oldSrc=img.getAttribute('src')||'';
  const match=oldSrc.match(/^\/assets\/fotos\/([a-z0-9_]+)\.jpg$/);
  if(!match)continue;
  const original=photoLibrary.images[match[1]];
  const cat=original?.category||'CDMX';
  const fresh=photoLibrary.candidatesForArticle(cat).filter(id=>photoLibrary.images[id]?.uploaded_at);
  if(!fresh.length)continue;
  const nextId=fresh[(rotation[cat]||0)%fresh.length];
  rotation[cat]=(rotation[cat]||0)+1;
  const updated=photoLibrary.images[nextId];
  const container=img.closest('.hero-main-photo,.topic-card,.resource-image,.photo-tile');
  const credits=container?.querySelector('.hero-photo-label small,.topic-photo-credit,.photo-credit-over,figcaption span');
  const caption=img.closest('figure')?.querySelector('figcaption strong');
  const oldCredits=credits?.cloneNode(true);
  const oldCaption=caption?.textContent;
  const oldAlt=img.alt;
  const creditText='© '+updated.author+' · '+updated.license+' · Wikimedia Commons';
  const rollback=()=>{
   if(credits&&oldCredits)credits.replaceWith(oldCredits);
   if(caption&&oldCaption)caption.textContent=oldCaption;
   img.alt=oldAlt;
   img.src=oldSrc;
  };
  img.addEventListener('error',rollback,{once:true});
  img.alt='Fotografía de contexto de '+cat+': '+updated.topic+'. No representa necesariamente la noticia.';
  if(caption)caption.textContent=updated.topic;
  if(credits){
   credits.replaceChildren(document.createTextNode(creditText+' · '));
   const link=document.createElement('a');
   link.href=updated.source;
   link.target='_blank';
   link.rel='noopener noreferrer';
   link.textContent='Fuente y licencia ↗';
   credits.append(link);
  }
  img.src=photoLibrary.src(nextId);
 }
}
function articleMeta(a){
 const meta=element('div','meta date-location');
 const source=element('span','article-source','Medio: '+(a.source||'Fuente externa'));
 const stamp=typeof a.published_at==='string'&&/^\d{4}-\d{2}-\d{2}T/.test(a.published_at)
   ?new Date(a.published_at):null;
 const validTime=stamp&&Number.isFinite(stamp.getTime());
 let day='Fecha no disponible',hour='Hora no disponible';
 if(validTime){
  day=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',day:'2-digit',month:'short',year:'numeric'}).format(stamp);
  hour=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',hour:'2-digit',minute:'2-digit',hour12:false}).format(stamp)+' h';
 }else if(/^\d{4}-\d{2}-\d{2}$/.test(a.date||'')){
  day=a.date.split('-').reverse().join('/');
 }
 const date=element('span','article-datetime','Publicado: '+day+' · '+hour);
 const location=element('span','article-location','Zona: '+(a.location||'No especificada en el titular'));
 meta.append(source,date,location);
 return meta;
}
function buildCard(a,featured=false,large=false){
 const c=element('article',featured?'card featured-card'+(large?' featured-main':''):'card');
 const visual=articleVisual(a),inside=element('div','inside');
 const badge=element('span','badge',a.category||'CDMX');
 const title=element('h3');
 const headingLink=element('a','headline-link',a.title);
 headingLink.href=a.local_url||'/noticias/';
 title.append(headingLink);
 const description=element('p','',a.brief?.lead||'Lee la síntesis de la información disponible en nuestro periódico.');
 const meta=articleMeta(a);
 const link=element('a','read','Leer resumen de Amau Kisumi →');
 link.href=a.local_url||'/noticias/';
 inside.append(badge,title,description,meta,link);
 c.append(visual,inside);
 window.CDMX_addArticleLike?.(c,a);
 return c;
}
function featuredArticles(items){
 const used=new Set(),chosen=[];
 for(const a of items){if(!used.has(a.category)){chosen.push(a);used.add(a.category);if(chosen.length>=3)break}}
 for(const a of items){if(chosen.length>=3)break;if(!chosen.includes(a))chosen.push(a)}
 return chosen;
}
function render(){
 const q=(search?.value||'').toLocaleLowerCase('es-MX').trim();
 const filtered=articles.filter(a=>(!category||a.category===category)&&[a.title,a.source,a.category].some(v=>String(v||'').toLocaleLowerCase('es-MX').includes(q)));
 // Las categorías se abren en la PRIMERA pantalla: nunca se viaja hacia abajo.
 if(category){
  const label='Noticias de '+category;
  if(topicStageHeading)topicStageHeading.textContent=label;
  if(topicStageDescription)topicStageDescription.textContent=topicDescriptions[category]||
   'Consulta las noticias recientes de la Ciudad de México y sus medios originales.';
  if(topicStageCount)topicStageCount.textContent=articles.length?
    filtered.length+' noticias disponibles · Última actualización: '+updated:
    'Preparando titulares…';
  if(topicStageGrid){
   topicStageGrid.replaceChildren();
   for(const a of filtered){if(validLink(a.url))topicStageGrid.append(buildCard(a))}
   if(articles.length&&!filtered.length){
    topicStageGrid.append(element('p','muted','Todavía no hay noticias en este tema. Prueba otro del menú superior.'));
   }
  }
  syncTopicTabs();
  return;
 }
 const isFront=!category&&!q;
 const front=isFront?featuredArticles(filtered):[];
 const featuredSet=new Set(front);
 if(featuredSection)featuredSection.hidden=!isFront||!front.length;
 if(featuredGrid){
  featuredGrid.replaceChildren();
  for(const [i,a] of front.entries()){if(validLink(a.url))featuredGrid.append(buildCard(a,true,i===0))}
 }
 if(currentTopic)currentTopic.textContent=category?'Noticias de '+category:'Última hora · Todas las noticias';
 if(status)status.textContent=filtered.length?
  filtered.length+' noticias disponibles · Última sincronización: '+updated:
  'No hay noticias para esta búsqueda. Prueba otro tema.';
 if(grid){grid.replaceChildren();for(const a of filtered){if(!validLink(a.url)||featuredSet.has(a))continue;grid.append(buildCard(a))}}
 document.querySelectorAll('[data-filter]').forEach(el=>{
  const active=el.dataset.filter===category;
  el.classList.toggle('active',active);
  if(el.tagName==='BUTTON')el.setAttribute('aria-pressed',String(active));
 });
}
search?.addEventListener('input',render);
// El encabezado se mantiene visible; las noticias se renderizan en una vista superior,
 // no en la sección de noticias ubicada más abajo en la portada.
// Desplazar el menú a la izquierda o derecha en función de la pestaña elegida.
const topNav=document.getElementById('menu-superior');
const navReducedMotion=()=>Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
function centerNavItem(item){
 if(!topNav||!item||!topNav.contains(item))return;
 const relativeLeft=item.getBoundingClientRect().left-topNav.getBoundingClientRect().left+topNav.scrollLeft;
 const desired=relativeLeft-(topNav.clientWidth-item.offsetWidth)/2;
 topNav.scrollTo({left:Math.max(0,Math.min(topNav.scrollWidth-topNav.clientWidth,desired)),behavior:navReducedMotion()?'auto':'smooth'});
}
document.querySelectorAll('[data-nav-shift]').forEach(button=>button.addEventListener('click',()=>{
 if(!topNav)return;
 const direction=Number(button.dataset.navShift)||1;
 topNav.scrollBy({left:direction*Math.max(180,topNav.clientWidth*.7),behavior:navReducedMotion()?'auto':'smooth'});
}));
// Flechas disponibles también en computadora si el menú no cabe en la pantalla.
function updateNavControls(){
 if(!topNav)return;
 const wrap=topNav.closest('.nav-carousel');
 if(!wrap)return;
 wrap.classList.remove('is-overflowing');
 const overflowing=topNav.scrollWidth>topNav.clientWidth+4;
 wrap.classList.toggle('is-overflowing',overflowing);
}
window.addEventListener('resize',updateNavControls,{passive:true});
window.requestAnimationFrame(updateNavControls);
document.fonts?.ready?.then(updateNavControls);
// Las pestañas funcionan como páginas de contenido horizontal bajo el menú.
const topicOrder=['','Metro','Seguridad','Movilidad','Cultura','Gobierno','CDMX'];
const topicDescriptions={
 Metro:'Estado del Metro y noticias sobre sus líneas, estaciones y usuarios.',
 Seguridad:'Información sobre seguridad pública y sucesos reportados en la capital.',
 Movilidad:'Metrobús, transporte, vialidades y movilidad en Ciudad de México.',
 Cultura:'Museos, patrimonio, exposiciones, actividades y vida cultural.',
 Gobierno:'Anuncios oficiales, servicios públicos, decisiones y políticas.',
 CDMX:'Lo que ocurre en la Ciudad de México, más allá de un solo tema.'
};
let topicSwitchToken=0,activeTopicAnimation=null,pendingTopicScroll=null;
const topicStagePrev=document.getElementById('topic-stage-prev');
const topicStageNext=document.getElementById('topic-stage-next');
function syncTopicTabs(selected=category){
 document.querySelectorAll('[data-filter]').forEach(el=>{
  const active=el.dataset.filter===selected;
  el.classList.toggle('active',active);
  if(el.tagName==='BUTTON')el.setAttribute('aria-pressed',String(active));
  if(el.tagName==='A'&&el.closest('#menu-superior')){
   if(active)el.setAttribute('aria-current','page');
   else el.removeAttribute('aria-current');
  }
 });
 const currentIndex=topicOrder.indexOf(selected);
 if(topicStagePrev)topicStagePrev.disabled=currentIndex<=0;
 if(topicStageNext)topicStageNext.disabled=currentIndex===topicOrder.length-1;
}
function displayTopic(next){
 category=next;
 if(topicStage)topicStage.hidden=!next;
 if(homeView)homeView.hidden=Boolean(next);
 render();
}
function cancelTopicTransition(){
 if(pendingTopicScroll!==null){window.clearTimeout(pendingTopicScroll);pendingTopicScroll=null;}
 if(!activeTopicAnimation)return;
 for(const animation of activeTopicAnimation.animations){
  animation.onfinish=null;
  animation.cancel();
 }
 activeTopicAnimation.ghost?.remove();
 activeTopicAnimation=null;
}
function changeTopic(requested){
 const next=topicOrder.includes(requested)?requested:'';
 const before=category;
 const direction=topicOrder.indexOf(next)>topicOrder.indexOf(before)?1:-1;
 const navItem=Array.from(topNav?.querySelectorAll('a[data-filter]')||[]).find(el=>el.dataset.filter===next);
 if(navItem)centerNavItem(navItem);
 if(next===before){syncTopicTabs(next);return;}
 const token=++topicSwitchToken;
 cancelTopicTransition();
 if(search)search.value='';
 syncTopicTabs(next);
 const swap=()=>{
  if(token!==topicSwitchToken)return;
  pendingTopicScroll=null;
  const outgoing=before?topicStage:homeView;
  const canAnimate=Boolean(outgoing&&typeof outgoing.animate==='function'&&!navReducedMotion());
  if(!canAnimate){displayTopic(next);return;}
  // Se conservan ambas vistas durante el movimiento: no hay teletransporte.
  const bounds=outgoing.getBoundingClientRect();
  const ghost=outgoing.cloneNode(true);
  ghost.removeAttribute('id');
  ghost.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));
  ghost.querySelectorAll('iframe,video').forEach(el=>el.remove());
  ghost.classList.add('topic-transition-ghost');
  Object.assign(ghost.style,{
   position:'fixed',top:bounds.top+'px',left:bounds.left+'px',
   width:bounds.width+'px',height:Math.min(bounds.height,Math.max(180,window.innerHeight-bounds.top+12))+'px',
   margin:'0',pointerEvents:'none',overflow:'hidden',zIndex:'18',
   backfaceVisibility:'hidden'
  });
  document.body.append(ghost);
  displayTopic(next);
  const incoming=next?topicStage:homeView;
  if(!incoming){ghost.remove();return;}
  const travel=Math.max(window.innerWidth+18,bounds.width+18);
  const duration=720;
  const leave=ghost.animate([
   {transform:'translateX(0)',opacity:1},
   {transform:'translateX('+(-direction*travel)+'px)',opacity:1}
  ],{duration,easing:'cubic-bezier(.22,.61,.36,1)',fill:'both'});
  const arrive=incoming.animate([
   {transform:'translateX('+(direction*travel)+'px)',opacity:1},
   {transform:'translateX(0)',opacity:1}
  ],{duration,easing:'cubic-bezier(.22,.61,.36,1)',fill:'both'});
  activeTopicAnimation={animations:[leave,arrive],ghost};
  arrive.onfinish=()=>{
   if(token!==topicSwitchToken)return;
   cancelTopicTransition();
  };
 };
 // Si la persona lee más abajo, volver al encabezado DESLIZANDO el documento.
 if(window.scrollY>24&&!navReducedMotion()){
  const distance=window.scrollY;
  window.scrollTo({top:0,behavior:'smooth'});
  pendingTopicScroll=window.setTimeout(swap,Math.min(580,310+distance*.2));
 }else{
  if(window.scrollY>16)window.scrollTo({top:0,behavior:'auto'});
  swap();
 }
}
// Las páginas independientes (mapa, hemeroteca, etc.) conservan sus enlaces.
topNav?.querySelectorAll('a:not([data-filter])').forEach(el=>el.addEventListener('click',()=>centerNavItem(el)));
document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',event=>{
 event.preventDefault();changeTopic(el.dataset.filter||'');
}));
topicStagePrev?.addEventListener('click',()=>changeTopic(topicOrder[Math.max(0,topicOrder.indexOf(category)-1)]));
topicStageNext?.addEventListener('click',()=>changeTopic(topicOrder[Math.min(topicOrder.length-1,topicOrder.indexOf(category)+1)]));
// También se pueden recorrer las páginas con un gesto horizontal en celular.
let swipeStart=null;
topicStage?.addEventListener('touchstart',event=>{
 if(event.touches.length===1)swipeStart={x:event.touches[0].clientX,y:event.touches[0].clientY};
},{passive:true});
topicStage?.addEventListener('touchend',event=>{
 if(!swipeStart||event.changedTouches.length!==1)return;
 const dx=event.changedTouches[0].clientX-swipeStart.x;
 const dy=event.changedTouches[0].clientY-swipeStart.y;
 swipeStart=null;
 if(Math.abs(dx)<85||Math.abs(dy)>55)return;
 const current=topicOrder.indexOf(category);
 const target=Math.min(topicOrder.length-1,Math.max(0,current+(dx<0?1:-1)));
 if(target!==current)changeTopic(topicOrder[target]);
},{passive:true});
document.querySelectorAll('img[data-fallback-photo]').forEach(img=>{
 const alternative=img.dataset.fallbackPhoto;
 img.addEventListener('error',()=>{
  if(alternative){img.removeAttribute('data-fallback-photo');img.src=photoLibrary?.src(alternative,img.getAttribute('width')||640)||'';}
  else img.hidden=true;
 },{once:true});
});
function showEmbeddedNews(){
 try{const node=document.getElementById('embedded-news-fallback');const list=JSON.parse(node?.textContent||'[]');if(!Array.isArray(list)||!list.length)return false;applyNewsFeed({articles:list,updated:'Archivo publicado'});return true;}catch(e){return false;}
}
showEmbeddedNews();
Promise.allSettled([
 fetch('/news.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('news');return r.json()}),
 fetch('/reports.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('reports');return r.json()}),
 fetch('/assets/fotos/catalogo.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('catalog');return r.json()}),
 fetch('/archivo/meses.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('months');return r.json()}),
 fetch('/assets/fotos/recientes.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('recent');return r.json()})
]).then(([news,reports,catalog,months,recent])=>{
 if(catalog.status==='fulfilled')photoLibrary?.addCatalog(catalog.value);
 if(recent.status==='fulfilled')photoLibrary?.addRecentCatalog(recent.value);
 refreshStaticPhotos();
 if(news.status==='fulfilled'&&Array.isArray(news.value.articles)){
  applyNewsFeed(news.value);
 }else{
  if(!articles.length&&!showEmbeddedNews())renderLeadStory([]);
  if(status)status.textContent='Mostrando noticias publicadas disponibles.';
  if(featuredGrid&&!featuredGrid.children.length)featuredGrid.replaceChildren(element('p','muted','No fue posible cargar las noticias destacadas.'));
 }
 if(reportList){
  reportList.replaceChildren();
  const data=reports.status==='fulfilled'&&Array.isArray(reports.value.reports)?reports.value.reports:[];
  if(editorialLatest){
   const latest=data.find(x=>/^\/reportes\/\d{4}-\d{2}-\d{2}\.html$/.test(x.url));
   if(latest){
    editorialLatest.href=latest.url;
    editorialLatest.textContent='Leer la tesis, opinión y fuentes · '+latest.date+' ↗';
   }else{
    editorialLatest.href='/reportes/';
    editorialLatest.textContent='Explorar reportes y sus fuentes ↗';
   }
  }
  for(const x of data.slice(0,5)){
   if(!/^\/reportes\/\d{4}-\d{2}-\d{2}\.html$/.test(x.url))continue;
   const li=element('li'),a=element('a','','Reporte del '+x.date);
   a.href=x.url;li.append(a,document.createTextNode(' · '+Number(x.count||0)+' titulares'));reportList.append(li);
  }
  if(!reportList.children.length)reportList.append(element('li','','El primer reporte aparecerá cuando haya suficientes titulares y fuentes.'));
 }
 const monthList=document.getElementById('archive-month-list');
 if(monthList){
  monthList.replaceChildren();
  const list=months.status==='fulfilled'&&Array.isArray(months.value.months)
   ?months.value.months.filter(m=>/^\d{4}-\d{2}$/.test(m.month)):[];
  for(const item of list.slice(0,4)){
   const a=element('a','archive-month-link');
   a.href='/archivo/?mes='+encodeURIComponent(item.month);
   const monthDate=new Date(item.month+'-01T12:00:00Z');
   const label=new Intl.DateTimeFormat('es-MX',{month:'long',year:'numeric',timeZone:'UTC'}).format(monthDate);
   a.append(element('span','',label),element('small','',Number(item.count||0)+' notas ↗'));
   monthList.append(a);
  }
  if(!list.length){
   const link=element('a','archive-month-link','Explorar el archivo mensual ↗');
   link.href='/archivo/';monthList.append(link);
  }
 }
});

// Mientras la portada permanezca abierta, actualizar noticias sin recargar la página.
setInterval(()=>{if(document.visibilityState==='visible')refreshHomepageNews()},15*60*1000);
document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState==='visible')refreshHomepageNews();
});
