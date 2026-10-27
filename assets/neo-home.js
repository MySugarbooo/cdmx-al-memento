/* CDMX AL MEMENTO · Portada visual inspirada en la referencia aportada.
   Conserva index.html, app.js, Firebase, anuncios, métricas y rutas originales.
   Sin cifras, conversaciones ni noticias inventadas. */
(() => {
'use strict';
const root=document.getElementById('contenido');
if(!root)return;
const boroughs=['Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras','Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'];
const quick=[['♟','Alcaldías','/alcaldias/'],['▥','CDMX','/cdmx/'],['⬟','Seguridad','/seguridad/'],['▤','Movilidad','/movilidad/'],['✿','Servicios','/servicios/'],['🐾','Animales','/animales/'],['▧','Fotografías','/creditos-fotograficos.html'],['♧','Comunidad','/comunidad/']];
const photoFallback={Metro:'/assets/fotos/metro.jpg',Movilidad:'/assets/fotos/movilidad.jpg',Seguridad:'/assets/fotos/seguridad.jpg',Gobierno:'/assets/fotos/gobierno.jpg',Cultura:'/assets/fotos/cultura.jpg',CDMX:'/assets/fotos/reforma.jpg'};
const mxDate=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',weekday:'long',day:'numeric',month:'long',year:'numeric'});
const shortDate=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',day:'numeric',month:'short',year:'numeric'});
const shortTime=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',hour:'2-digit',minute:'2-digit'});
const escapeDate=d=>{const date=new Date(d);return Number.isFinite(date.getTime())?shortDate.format(date):'Fecha por confirmar'};
const articleLink=a=>typeof a.local_url==='string'&&/^\/noticias\/\?/.test(a.local_url)?a.local_url:'/noticias/';
const photoUrl=a=>{
 if(a&&a.photo&&typeof a.photo.url==='string'&&/^\/assets\/fotos\/[a-zA-Z0-9_-]+\.jpe?g$/.test(a.photo.url))return a.photo.url;
 const chosen=window.CDMX_FOTOS&&typeof window.CDMX_FOTOS.forArticle==='function'?window.CDMX_FOTOS.forArticle(a):'';
 const result=window.CDMX_FOTOS&&typeof window.CDMX_FOTOS.src==='function'?window.CDMX_FOTOS.src(chosen):'';
 return /^\/assets\/fotos\/[a-zA-Z0-9_-]+\.jpe?g$/.test(result)?result:(photoFallback[a.category]||photoFallback.CDMX);
};
function el(tag,cls,txt){const x=document.createElement(tag);if(cls)x.className=cls;if(txt!==undefined)x.textContent=txt;return x}
const skyline='<svg class="neo-brand-mark" viewBox="0 0 100 85" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="neoRose" x1="0" x2="1"><stop stop-color="#ff8bcb"/><stop offset="1" stop-color="#ec2790"/></linearGradient></defs><g fill="url(#neoRose)"><path d="M4 79h92v4H4zM12 77V54l9-5 9 6v22zM34 77V25l8-5 7 9v48zM53 77V35l11-8 7 7v43zM76 77V47l8-4 5 8v26z"/><path d="M43 20l4-15 5 16-5 3zM45 4l3-4 2 4zM60 27l-2-15 7 7-1 11z"/><path d="M9 55l5-15 3 13zM38 27v-12h6v10zM80 47V34h4v11z"/></g><g fill="#ffd4e8"><rect x="40" y="38" width="3" height="8"/><rect x="60" y="42" width="3" height="6"/><rect x="80" y="55" width="3" height="7"/></g></svg>';
const boroughSvg='<svg viewBox="0 0 230 265" role="img" aria-label="Mosaico ilustrativo rosa inspirado en la forma de Ciudad de México; consulta el mapa oficial para límites precisos"><defs><clipPath id="neoShape"><path d="M108 8l26 21 17-6 7 25 22 16-3 23 31 24-13 26 17 33-22 12 1 31-25 8-7 28-28-8-28 14-28-16-30 1-13-26-20-13 12-34-14-26 13-24-7-24 29-9 7-29 20 3z"/></clipPath></defs><g clip-path="url(#neoShape)" stroke="#86254e" stroke-width="1"><path fill="#ec4793" d="M0 0h240v270H0z"/><path fill="#fa6aad" d="M5 8h100v52H5z"/><path fill="#cc3982" d="M105 0h115v67H105z"/><path fill="#fa81bb" d="M0 63h69v60H0z"/><path fill="#e74b94" d="M68 60h66v68H68z"/><path fill="#fd79b5" d="M134 66h116v65H134z"/><path fill="#aa3975" d="M0 121h59v75H0z"/><path fill="#c63d82" d="M57 126h71v65H57z"/><path fill="#f96eaa" d="M128 131h53v73h-53z"/><path fill="#df4f96" d="M181 132h58v65h-58z"/><path fill="#f68cbf" d="M0 194h88v70H0z"/><path fill="#ef5b9c" d="M88 193h61v74H88z"/><path fill="#b93e7b" d="M149 204h100v62H149z"/><path fill="#da3e88" d="M15 28l50 36-14 50-44-28z"/><path fill="#fd8fc3" d="M98 22l42 57-31 52-29-55z"/><path fill="#a73574" d="M31 169l54-39 25 37-45 52z"/><path fill="#eb4a90" d="M153 101l51 22-22 40-37-23z"/></g><path d="M108 8l26 21 17-6 7 25 22 16-3 23 31 24-13 26 17 33-22 12 1 31-25 8-7 28-28-8-28 14-28-16-30 1-13-26-20-13 12-34-14-26 13-24-7-24 29-9 7-29 20 3z" fill="none" stroke="#fbb4d5" stroke-width="2"/></svg>';
const shell=document.createElement('section');shell.id='neo-home';shell.setAttribute('aria-label','Portada de CDMX AL MEMENTO');
shell.innerHTML=[
'<header class="neo-head"><div class="neo-head-top"><div class="neo-head-status"><time id="neo-date"></time><span class="neo-visitor" id="neo-visitors">Visitas: consultando…</span></div>',
'<a class="neo-brand" href="/" aria-label="CDMX AL MEMENTO · inicio">',skyline,'<strong class="neo-brand-name">CDMX<em>AL MEMENTO</em></strong></a>',
'<div class="neo-head-actions"><form class="neo-search" id="neo-search-form" role="search"><input id="neo-search-input" type="search" placeholder="Buscar noticias..." aria-label="Buscar noticias"><button type="submit" aria-label="Buscar">⌕</button></form><button id="neo-theme" class="neo-circle" aria-label="Cambiar tema" title="Cambiar tema" type="button">☾</button><a class="neo-circle neo-user" href="/comunidad/" aria-label="Mi comunidad">♙</a></div></div>',
'<nav class="neo-nav" aria-label="Secciones del periódico"><a class="neo-active-link" href="/" aria-current="page">Portada</a><a href="/alcaldias/">Alcaldías</a><a href="/cdmx/">CDMX</a><a href="/seguridad/">Seguridad</a><a href="/movilidad/">Movilidad</a><a href="/servicios/">Servicios</a><a href="/animales/">Animales</a><a href="/creditos-fotograficos.html">Fotografías</a><a href="/comunidad/">Mi comunidad</a><span class="neo-nav-spacer"></span><span class="neo-social-nav"><a href="/archivo/" title="Archivo mensual">▤</a><a href="/mapa/" title="Mapa">⌖</a><a href="/comunidad/" title="Participa">♡</a></span></nav></header>',
'<div class="neo-dashboard">',
'<section class="neo-hero neo-box" aria-labelledby="neo-hero-title"><img id="neo-hero-img" class="neo-hero-image" src="/assets/fotos/reforma.jpg" alt="Fotografía de archivo de la Ciudad de México"><div class="neo-hero-inner"><span class="neo-kicker">DESTACADA</span><a id="neo-hero-title" class="neo-hero-title" href="/noticias/">Noticias de Ciudad de México</a><p class="neo-hero-description" id="neo-hero-description">Titulares actualizados desde medios identificados.</p><div class="neo-hero-bottom"><span id="neo-hero-category">⌖ CDMX</span><span id="neo-hero-date"></span><span class="neo-hero-source" id="neo-hero-source"></span><span class="neo-feature-like" id="neo-hero-like"></span></div><div class="neo-hero-credit" id="neo-hero-credit">Foto de archivo · no corresponde necesariamente al hecho noticioso</div></div><div class="neo-hero-controls"><button id="neo-hero-next" type="button" aria-label="Siguiente noticia destacada">›</button></div></section>',
'<section class="neo-map neo-box" aria-labelledby="neo-map-title"><h2 id="neo-map-title">Explora las alcaldías</h2><a href="/alcaldias/" class="neo-map-area" aria-label="Consultar las 16 alcaldías">',boroughSvg,'</a><a class="neo-map-link" href="/mapa/">Ver mapa interactivo ↗</a></section>',
'<aside class="neo-boroughs neo-box" aria-labelledby="neo-borough-title"><h2 id="neo-borough-title">Noticias por alcaldía</h2><ul id="neo-borough-list"></ul></aside>',
'<section class="neo-latest neo-box" aria-labelledby="neo-latest-title"><div class="neo-block-title"><h2 id="neo-latest-title">▣ Últimas noticias</h2><a href="/archivo/">Ver todas →</a></div><div class="neo-news-grid" id="neo-news-grid"></div><button class="neo-news-more" type="button" id="neo-news-more" hidden>Mostrar más noticias ↓</button><p id="neo-news-status" class="neo-feed-note">Titulares y fechas de medios externos · Fotos de archivo</p></section>',
'<aside class="neo-community neo-box" aria-labelledby="neo-community-title"><div class="neo-block-title"><h2 id="neo-community-title">Mi comunidad</h2><a href="/comunidad/#cdmx-comments-editor" class="neo-pill">＋ Publicar</a></div><div class="neo-community-tabs"><a href="/comunidad/">Recientes</a><a href="/comunidad/#forum-sort">Populares</a><a href="/comunidad/#cdmx-comments-editor">Preguntas</a></div><p class="neo-community-intro">Pregunta a tus vecinos, comenta y participa con tu cuenta de Google.</p><div id="neo-community-posts"><p class="neo-feed-note">Consultando conversaciones públicas…</p></div><div class="neo-community-footer"><a href="/comunidad/">Abrir el foro y responder ↗</a></div></aside>',
'<nav class="neo-links" id="neo-links" aria-label="Accesos rápidos"></nav>',
'</div><nav class="neo-dock" aria-label="Navegación del celular"><a class="neo-dock-active" href="/"><span>⌂</span>Inicio</a><a href="/alcaldias/"><span>▤</span>Alcaldías</a><a class="neo-dock-publish" href="/comunidad/#cdmx-comments-editor" aria-label="Publicar en la comunidad">＋</a><a href="/comunidad/"><span>♧</span>Comunidad</a><a href="/favoritos/"><span>♙</span>Guardados</a></nav>'
].join('');
const state={stories:[],current:0,filter:'',query:'',visible:8};
function initStatic(){
 const date=shell.querySelector('#neo-date');date.textContent=mxDate.format(new Date());
 const list=shell.querySelector('#neo-borough-list');
 for(const name of boroughs){const li=el('li');const a=el('a');a.href='/alcaldias/?alcaldia='+encodeURIComponent(name)+'#noticias-alcaldia';const arrow=el('span','', '›');a.append(document.createTextNode(name),arrow);li.append(a);list.append(li)}
 const links=shell.querySelector('#neo-links');
 for(const [icon,label,href] of quick){const a=el('a','neo-quick');a.href=href;const s=el('span','',icon);a.append(s,document.createTextNode(label));links.append(a)}
 shell.querySelector('#neo-hero-next').addEventListener('click',()=>{state.current=(state.current+1)%Math.min(state.stories.length,12);renderHero()});const more=shell.querySelector('#neo-news-more');more.addEventListener('click',()=>{state.visible+=8;renderNews()});if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{if(entries.some(x=>x.isIntersecting)&&!more.hidden){state.visible+=8;renderNews()}},{rootMargin:'160px'});observer.observe(more)}
 shell.querySelectorAll('[data-neo-filter]').forEach(btn=>btn.addEventListener('click',()=>{
   state.filter=state.filter===btn.dataset.neoFilter?'':btn.dataset.neoFilter;state.query='';shell.querySelector('#neo-search-input').value='';
   shell.querySelectorAll('[data-neo-filter]').forEach(b=>b.classList.toggle('neo-active-link',state.filter===b.dataset.neoFilter));
   shell.querySelector('.neo-nav a[href="/"]').classList.toggle('neo-active-link',!state.filter);
   renderNews();
 }));
 shell.querySelector('#neo-search-form').addEventListener('submit',e=>{
   e.preventDefault();const input=shell.querySelector('#neo-search-input');const form=e.currentTarget;
   if(matchMedia('(max-width:650px)').matches&&!form.classList.contains('neo-search-open')){form.classList.add('neo-search-open');input.focus();return}
   state.query=input.value.trim().toLocaleLowerCase('es-MX');state.filter='';renderNews();shell.querySelector('#neo-latest-title').scrollIntoView({behavior:'smooth',block:'start'});
 });
 shell.querySelector('#neo-theme').addEventListener('click',e=>{
   const on=document.documentElement.classList.toggle('neo-soft');
   e.currentTarget.textContent=on?'☀':'☾';e.currentTarget.setAttribute('aria-pressed',String(on));
 });
}
function renderHero(){
 const a=state.stories[state.current];if(!a)return;
 const img=shell.querySelector('#neo-hero-img');img.src=photoUrl(a);img.alt='Foto de archivo para contextualizar una nota sobre '+(a.category||'CDMX');img.onerror=()=>{img.onerror=null;img.src=photoFallback.CDMX};
 const title=shell.querySelector('#neo-hero-title');title.textContent=a.title;title.href=articleLink(a);
 shell.querySelector('#neo-hero-description').textContent=String(a.description||a.brief?.lead||'Consulta la nota y su fuente original para conocer más detalles.').slice(0,260);
 shell.querySelector('#neo-hero-category').textContent='⌖ '+(a.borough||a.category||'CDMX');
 const when=a.published_at||a.date;shell.querySelector('#neo-hero-date').textContent='▦ '+escapeDate(when)+(a.published_at?' · '+shortTime.format(new Date(a.published_at)):'');
 shell.querySelector('#neo-hero-source').textContent=a.source||'Medio externo';
 shell.querySelector('#neo-hero-credit').textContent='Foto de archivo'+(a.photo?.author?' · '+a.photo.author:'')+' · no corresponde necesariamente al hecho';
 const likes=shell.querySelector('#neo-hero-like');likes.replaceChildren();
 if(typeof window.CDMX_addArticleLike==='function')window.CDMX_addArticleLike(likes,a);
}
function renderNews(){
 const all=state.stories;
 const matched=all.filter(a=>(!state.filter||a.category===state.filter)&&(!state.query||(a.title+' '+(a.borough||'')+' '+(a.source||'')).toLocaleLowerCase('es-MX').includes(state.query)));
 const out=shell.querySelector('#neo-news-grid');out.replaceChildren();
 for(const a of matched.slice(0,state.visible)){
  const card=el('article','neo-news-card');
  const thumb=el('a','neo-thumb');thumb.href=articleLink(a);
  const img=el('img');img.src=photoUrl(a);img.alt='Foto de archivo relacionada con '+(a.category||'CDMX');img.loading='lazy';img.decoding='async';img.onerror=()=>{img.onerror=null;img.src=photoFallback.CDMX};
  const category=el('span','neo-category',a.category||'CDMX');thumb.append(img,category);
  const h=el('h3');const link=el('a','',a.title);link.href=articleLink(a);h.append(link);
  const meta=el('div','neo-card-meta',escapeDate(a.published_at||a.date)+' · '+(a.borough||a.source||'CDMX'));
  const credit=el('small','neo-credit',a.photo?.author?'Archivo: '+a.photo.author:'Imagen de archivo');
  card.append(thumb,h,meta,credit);
  out.append(card);
 }
 if(!matched.length)out.append(el('p','neo-feed-note','No hay noticias que coincidan. Prueba con otra búsqueda.'));const more=shell.querySelector('#neo-news-more');if(more)more.hidden=matched.length<=state.visible;
 shell.querySelector('#neo-news-status').textContent=(state.filter||state.query?'Resultados: '+matched.length+' · ':'')+'Actualización: '+(state.stories.length?'titulares del feed automático':'no disponible')+' · Fotografías de archivo, no necesariamente del hecho';
}
function mirrorVisits(){
 const target=shell.querySelector('#neo-visitors');const origin=document.getElementById('header-visitors-number');
 const update=()=>{const n=origin?.textContent?.trim()||'—';target.textContent=n==='—'?'Visitas: consultando…':'Visitas: '+n};
 update();if(origin)new MutationObserver(update).observe(origin,{subtree:true,childList:true,characterData:true});
}
async function communityPreview(){
 const out=shell.querySelector('#neo-community-posts');
 try{
  const cfg=window.CDMX_COMMENTS_FIREBASE;
  if(!cfg||!cfg.projectId)throw Error('Configuración no disponible');
  const [appmod,fs]=await Promise.all([
   import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js'),
   import('https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js')
  ]);
  const app=appmod.getApps().find(x=>x.name==='neo-community-view')||appmod.initializeApp(cfg,'neo-community-view');
  const db=fs.getFirestore(app);
  const q=fs.query(fs.collection(db,'community','main','comments'),fs.orderBy('createdAt','desc'),fs.limit(8));
  const docs=await fs.getDocs(q);
  const posts=docs.docs.map(d=>d.data()).filter(c=>typeof c.text==='string'&&!c.text.startsWith('[FORO:RESPUESTA:')).slice(0,3);
  out.replaceChildren();
  if(!posts.length){out.append(el('p','neo-community-intro','Aún no hay conversaciones visibles. ¡Inicia una pregunta!'));return}
  for(const post of posts){
   const a=el('a','neo-question');a.href='/comunidad/';
   const author=el('div','neo-question-title');
   const avatar=el('span','neo-avatar',(post.name||'V').slice(0,1).toUpperCase());
   const name=el('strong','',String(post.name||'Vecino').slice(0,60));
   author.append(avatar,name);a.append(author);
   let text=String(post.text||'').replace(/^\[FORO:PREGUNTA\]\s*/,'');
   const parts=text.split('\n');const heading=el('strong','',parts[0].slice(0,115));const snippet=el('p','',parts.slice(1).join(' ').slice(0,100));
   if(parts[0].trim())a.append(heading);if(snippet.textContent)a.append(snippet);
   const stamp=post.createdAt&&typeof post.createdAt.toDate==='function'?post.createdAt.toDate():null;
   if(stamp)a.append(el('small','',escapeDate(stamp)));
   out.append(a);
  }
 }catch(err){out.replaceChildren(el('p','neo-community-intro','Visita el foro para consultar preguntas, publicaciones y respuestas reales.'));}
}
async function start(){
 try{
  const resp=await fetch('/news.json?t='+Date.now(),{cache:'no-store'});
  if(!resp.ok)throw Error('feed no disponible');
  const feed=await resp.json();
  const articles=(Array.isArray(feed.articles)?feed.articles:[]).filter(a=>a&&typeof a.title==='string'&&/^https:\/\/news\.google\.com\//.test(a.url||'')&&/^\/noticias\/\?/.test(a.local_url||''));
  if(!articles.length)throw Error('feed vacío');
  state.stories=articles;
  initStatic();
  root.prepend(shell);
  try{const prev=sessionStorage.getItem('cdmx-neo-last-feature');const next=articles.slice(0,12).findIndex(a=>a.url!==prev);state.current=next<0?0:next;sessionStorage.setItem('cdmx-neo-last-feature',articles[state.current].url)}catch{state.current=0}
  renderHero();const incoming=new URLSearchParams(location.search).get('buscar');if(incoming){state.query=incoming.slice(0,90).trim().toLocaleLowerCase('es-MX');shell.querySelector('#neo-search-input').value=incoming.slice(0,90)}renderNews();
  document.documentElement.classList.add('neo-active');
  mirrorVisits();
  communityPreview();
 }catch(err){
  // La portada anterior permanece disponible ante fallos del feed, navegador o conexión.
  console.warn('La nueva portada no pudo iniciarse; se mantiene el diseño anterior.',err);
 }
}
start();
})();