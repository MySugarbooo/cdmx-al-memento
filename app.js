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
function renderLeadStory(items){
 if(!leadStory.title)return;
 const now=Date.now(),freshAfter=now-72*60*60*1000;
 const newest=(Array.isArray(items)?items:[]).filter(a=>{
  const ts=Date.parse(a.published_at||'');
  return validLink(a.url)&&Number.isFinite(ts)&&ts>=freshAfter&&ts<=now+15*60*1000;
 }).sort((a,b)=>{
 const score=x=>{const age=(now-Date.parse(x.published_at))/3600000;const title=String(x.title||'').toLocaleLowerCase('es-MX');const important=/alerta|urgente|sismo|terremoto|inundaci[oó]n|incendio|explosi[oó]n|desaparecid|emergencia|evacuaci[oó]n|cierre|suspensi[oó]n|accidente|metro|bloqueo|manifestaci[oó]n|viral|tendencia|hist[oó]rico|protecci[oó]n civil/.test(title)?35:0;return important+Math.max(0,72-age)*1.4;};
 const diff=score(b)-score(a);return diff||Date.parse(b.published_at)-Date.parse(a.published_at);
 })[0];
 if(!newest){
  leadStory.kicker.textContent='SIN NOTICIA PRINCIPAL RECIENTE';
  leadStory.title.textContent='No hay titulares recientes disponibles para destacar';
  leadStory.summary.textContent='El recopilador todavía no proporciona una noticia con fecha reciente. Consulta los reportes anteriores sin confundirlos con noticias de hoy.';
  leadStory.meta.textContent='No se mostrará como actual ninguna noticia antigua.';
  leadStory.link.href='/reportes/';
  leadStory.link.textContent='Consultar reportes anteriores →';
  return;
 }
 leadStory.kicker.textContent=(newest.borough?newest.borough.toLocaleUpperCase('es-MX')+' · ':'')+
  'TITULAR RECIENTE · '+String(newest.category||'CDMX').toLocaleUpperCase('es-MX');
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
  renderLeadStory([]);
  if(status)status.textContent='No fue posible comprobar noticias nuevas. Consulta el archivo.';
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
  renderLeadStory([]);
  if(status)status.textContent='No fue posible cargar las noticias.';
  if(featuredGrid)featuredGrid.replaceChildren(element('p','muted','No fue posible cargar las noticias destacadas.'));
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
setInterval(()=>{if(document.visibilityState==='visible')refreshHomepageNews()},2*60*60*1000);
document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState==='visible')refreshHomepageNews();
});
