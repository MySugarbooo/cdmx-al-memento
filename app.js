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
function articleVisual(a){
 const figure=element('div','news-visual');
 const first=photoLibrary?.forArticle(a);
 const photo=first?photoLibrary.images[first]:null;
 if(!photo){figure.append(element('span','photo-unavailable','Fotografía no disponible'));return figure}
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
  else{image.hidden=true;figure.append(element('span','photo-unavailable','Fotografía no disponible'))}
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
 const title=element('h3','',a.title);
 const description=element('p','',featured
   ?'Lee la cobertura completa y confirma los detalles con el medio que publicó esta noticia.'
   :'Titular recopilado automáticamente. Consulta la fuente original para obtener contexto.');
 const meta=articleMeta(a);
 const link=element('a','read','Leer noticia original ↗');
 link.href=a.url;link.target='_blank';link.rel='noopener noreferrer nofollow';
 inside.append(badge,title,description,meta,link);
 c.append(visual,inside);
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
  articles=news.value.articles.filter(a=>a&&typeof a.title==='string'&&validLink(a.url));
  photoLibrary?.prepare(articles);
  updated=String(news.value.updated||'sin fecha');render();
 }else{
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
