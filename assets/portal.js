'use strict';
/* Herramientas de lectura local: sin cuentas, rastreadores ni claves externas.
   Noticias recopiladas del RSS: NO son alertas oficiales de operación en vivo. */
(()=>{
 const KEY_BOROUGH='cdmx.memento.alcaldia.v1',KEY_FAV='cdmx.memento.favoritos.v1';
 const BOROUGHS=["La Magdalena Contreras","Álvaro Obregón","Azcapotzalco","Benito Juárez","Coyoacán","Cuajimalpa de Morelos","Cuauhtémoc","Gustavo A. Madero","Iztacalco","Iztapalapa","Miguel Hidalgo","Milpa Alta","Tláhuac","Tlalpan","Venustiano Carranza","Xochimilco"];
 const $=id=>document.getElementById(id);
 const validArticle=a=>a&&typeof a.title==='string'&&typeof a.url==='string'&&/^https:\/\/news\.google\.com\//.test(a.url);
 const cleanBorough=name=>BOROUGHS.includes(name)?name:'';
 const stored=(key)=>{try{return localStorage.getItem(key)}catch{return null}};
 const save=(key,value)=>{try{localStorage.setItem(key,value);return true}catch{return false}};
 const chooseBorough=()=>cleanBorough(stored(KEY_BOROUGH));
 const dateMX=value=>{
  const d=new Date(value);
  if(!Number.isFinite(d.getTime()))return 'Fecha no indicada';
  return new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'medium'}).format(d);
 };
 const safeURL=u=>typeof u==='string'&&/^https:\/\/news\.google\.com\//.test(u)?u:'';
 let feed=null;
 const feedPromise=fetch('/news.json?t='+Date.now(),{cache:'no-store'}).then(r=>{
  if(!r.ok)throw Error('No se pudieron obtener los titulares');
  return r.json();
 }).then(data=>{
  feed={updated:String(data.updated||''),articles:(Array.isArray(data.articles)?data.articles:[]).filter(validArticle)};
  return feed;
 }).catch(()=>{
  feed={updated:'No disponible',articles:[]};
  return feed;
 });
 function markBorough(container){
  const name=chooseBorough();
  if(!container)return;
  container.textContent=name?'Alcaldía guardada: '+name:'Elige una alcaldía. Tu elección se guarda únicamente en este navegador.';
 }
 function syncSelects(){
  for(const select of document.querySelectorAll('[data-borough-select]')){
   if(!select.options.length){
    const empty=document.createElement('option');empty.value='';empty.textContent='Todas las alcaldías';select.append(empty);
    for(const name of BOROUGHS){
     const opt=document.createElement('option');opt.value=name;opt.textContent=name;select.append(opt);
    }
   }
   select.value=chooseBorough();
  }
  document.querySelectorAll('[data-selected-borough]').forEach(markBorough);
 }
 function selectBorough(name){
  const selected=cleanBorough(name);
  save(KEY_BOROUGH,selected);
  syncSelects();
  if(feed){renderToday();renderBorough();}
  window.dispatchEvent(new CustomEvent('cdmx:borough-changed',{detail:{borough:selected}}));
 }
 // Al cambiar la alcaldía desde la tira del clima, actualiza también las noticias
 // de la portada o de "CDMX cerca de ti" sin recargar la página.
 window.addEventListener('cdmx:borough-changed',()=>{
  syncSelects();
  if(feed){renderToday();renderBorough();}
 });
 function linkToBorough(name){
  return '/alcaldias/?alcaldia='+encodeURIComponent(name)+'#noticias-alcaldia';
 }
 function empty(container,message){
  if(!container)return;
  const li=document.createElement('li');li.className='portal-info';li.textContent=message;
  container.replaceChildren(li);
 }
 function fillStories(id,items,limit=5){
  const el=$(id);if(!el)return;
  const rows=items.filter(validArticle).slice(0,limit);
  if(!rows.length){
   empty(el,'Sin titulares en esta selección por ahora. Consulta las fuentes oficiales o selecciona otra sección.');
   return;
  }
  el.replaceChildren();
  for(const a of rows){
   const li=document.createElement('li'),link=document.createElement('a'),small=document.createElement('small');
   link.textContent=a.title;link.href=a.url;link.target='_blank';link.rel='noopener noreferrer nofollow';
   small.textContent=(a.source||'Medio externo')+' · '+(a.published_at?dateMX(a.published_at):a.date||'Fecha no indicada')+' · '+(a.category||'CDMX');
   const saveButton=document.createElement('button');
   saveButton.type='button';saveButton.className='fav-save';
   saveButton.dataset.favoriteUrl=a.url;
   saveButton.dataset.favoriteTitle=a.title;
   saveButton.dataset.favoriteCategory=a.category||'CDMX';
   saveButton.dataset.favoriteSource=a.source||'Medio externo';
   li.append(link,small,saveButton);el.append(li);
  }
  refreshSaveButtons();
 }
 function todayMX(date){
  const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Mexico_City',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date);
  const get=type=>parts.find(p=>p.type===type)?.value||'';
  return get('year')+'-'+get('month')+'-'+get('day');
 }
 function renderToday(){
  if(!feed)return;
  const now=new Date(),date=todayMX(now),borough=chooseBorough();
  const label=$('portal-date');if(label)label.textContent=new Intl.DateTimeFormat('es-MX',{dateStyle:'full',timeZone:'America/Mexico_City'}).format(now);
  let stories=feed.articles.filter(a=>a.date===date);
  // El tablero nunca inventa un resumen: titulares enlazados, con sus fuentes.
  const actuallyToday=stories.length>0;
  if(!actuallyToday)stories=feed.articles;
  const featured=[];
  const used=new Set();
  const desired=borough?stories.filter(a=>a.borough===borough):stories;
  for(const a of desired){
   if(!used.has(a.category)){featured.push(a);used.add(a.category)}
   if(featured.length>=6)break;
  }
  for(const a of stories){if(featured.length>=6)break;if(!featured.some(x=>x.url===a.url))featured.push(a);}
  fillStories('portal-today-list',featured,6);
  const notice=$('portal-today-note');
  if(notice)notice.textContent=(actuallyToday?'Titulares publicados hoy':'Todavía no hay titulares con fecha de hoy; se muestran los más recientes disponibles')+
    ' · Actualización del recopilador: '+(feed.updated||'sin fecha')+' · Fotos de contexto, no del suceso.';
 }
 function renderBorough(){
  const area=chooseBorough();
  const label=$('portal-borough-heading');
  if(label)label.textContent=area?'Noticias de '+area:'Tu alcaldía, tus noticias';
  const more=$('portal-borough-more');
  if(more)more.href=area?linkToBorough(area):'/alcaldias/';
  if(feed)fillStories('portal-borough-list',area?feed.articles.filter(a=>a.borough===area):feed.articles.slice(0,8),6);
  const map=$('portal-nearby-map');
  if(map)map.href='/mapa/'+(area==='La Magdalena Contreras'?'?lugar=los-dinamos':'');
 }
 function renderTransport(){
  if(!feed)return;
  fillStories('portal-metro-news',feed.articles.filter(a=>a.category==='Metro'),7);
  fillStories('portal-mobility-news',feed.articles.filter(a=>a.category==='Movilidad'),6);
 }
 const alertPattern=/lluvia|inundaci[oó]n|tormenta|contingencia|calidad del aire|cierre vial|bloqueo|manifestaci[oó]n|afectaci[oó]n|sismo|protecci[oó]n civil|alerta amarilla|alerta naranja|alerta roja|suspensi[oó]n|sin servicio|retrasos|estaci[oó]n cerrada/i;
 function renderAlerts(){
  if(!feed)return;
  const recent=feed.articles.filter(a=>alertPattern.test(a.title)).slice(0,9);
  fillStories('portal-alert-list',recent,9);
  const el=$('portal-alert-stamp');
  if(el)el.textContent='Titulares recopilados: '+feed.updated+'. No son alertas oficiales en tiempo real.';
 }
 const metroLines=[
  {id:'1',color:'#e55f9f',route:'Observatorio – Pantitlán'},
  {id:'2',color:'#2362a8',route:'Cuatro Caminos – Tasqueña'},
  {id:'3',color:'#b9a522',route:'Indios Verdes – Universidad'},
  {id:'4',color:'#67afa4',route:'Martín Carrera – Santa Anita'},
  {id:'5',color:'#dbbb25',route:'Politécnico – Pantitlán'},
  {id:'6',color:'#d44b51',route:'El Rosario – Martín Carrera'},
  {id:'7',color:'#db7b32',route:'El Rosario – Barranca del Muerto'},
  {id:'8',color:'#328f6b',route:'Garibaldi/Lagunilla – Constitución de 1917'},
  {id:'9',color:'#8a6753',route:'Tacubaya – Pantitlán'},
  {id:'12',color:'#ae9962',route:'Mixcoac – Tláhuac'},
  {id:'A',color:'#873e99',route:'Pantitlán – La Paz'},
  {id:'B',color:'#a2a6ae',route:'Buenavista – Ciudad Azteca'}
 ];
 function renderLines(){
  const root=$('portal-metro-lines');if(!root)return;
  root.replaceChildren();
  for(const line of metroLines){
   const card=document.createElement('div');card.className='metro-line-card';
   const btn=document.createElement('button');btn.type='button';
   const mark=document.createElement('span');mark.className='metro-line-indicator';mark.style.background=line.color;
   const strong=document.createElement('strong');strong.textContent='Línea '+line.id;
   const small=document.createElement('small');small.textContent=line.route;
   btn.append(mark,strong,small);
   btn.addEventListener('click',()=>{
    for(const item of root.children)item.removeAttribute('data-active');
    card.dataset.active='true';
    const info=$('portal-metro-selection');
    if(info)info.textContent='Línea '+line.id+': '+line.route+'. Es una referencia de la red, NO confirma servicio normal ni tiempos de llegada. Consulta el STC antes de viajar.';
   });
   card.append(btn);root.append(card);
  }
 }
 function readFavorites(){
  try{
   const result=JSON.parse(stored(KEY_FAV)||'[]');
   return Array.isArray(result)?result.filter(x=>x&&safeURL(x.url)&&typeof x.title==='string').slice(0,150):[];
  }catch{return [];}
 }
 function writeFavorites(rows){save(KEY_FAV,JSON.stringify(rows.slice(0,150)));}
 function isSaved(url){return readFavorites().some(x=>x.url===url);}
 function toggleFavorite(item){
  if(!safeURL(item.url))return false;
  const old=readFavorites();
  const found=old.some(x=>x.url===item.url);
  writeFavorites(found?old.filter(x=>x.url!==item.url):[{
   url:item.url,title:String(item.title||'Noticia').slice(0,340),
   source:String(item.source||'Medio externo').slice(0,100),
   category:String(item.category||'CDMX').slice(0,40),
   date:String(item.date||new Date().toISOString().slice(0,10)).slice(0,28)
  },...old]);
  refreshSaveButtons();renderFavorites();
  return !found;
 }
 function attachSaveButtons(){
  // Procesa también tarjetas insertadas dinámicamente tras una actualización o pestaña.
  for(const card of document.querySelectorAll('.card,.featured-card')){
   if(card.querySelector('.fav-save'))continue;
   const link=card.querySelector('a.read[href^="https://news.google.com/"]');
   if(!link)continue;
   const title=card.querySelector('h3')?.textContent||'Noticia';
   const category=card.querySelector('.badge')?.textContent||'CDMX';
   const source=(card.querySelector('.article-source')?.textContent||'').replace(/^Medio:\s*/,'');
   const button=document.createElement('button');button.className='fav-save';button.type='button';
   button.dataset.favoriteUrl=link.href;
   button.dataset.favoriteTitle=title;
   button.dataset.favoriteCategory=category;
   button.dataset.favoriteSource=source;
   button.setAttribute('aria-label','Guardar noticia en favoritos');
   const inside=card.querySelector('.inside');
   (inside||card).append(button);
  }
  refreshSaveButtons();
 }
 function refreshSaveButtons(){
  const urls=new Set(readFavorites().map(x=>x.url));
  document.querySelectorAll('.fav-save').forEach(btn=>{
   const active=urls.has(btn.dataset.favoriteUrl);
   const label=active?'♥ Guardada':'♡ Guardar';
   if(btn.textContent!==label)btn.textContent=label;
   btn.setAttribute('aria-pressed',String(active));
   btn.setAttribute('aria-label',active?'Quitar de favoritos':'Guardar noticia en favoritos');
  });
  const count=$('portal-favorite-count');if(count)count.textContent=readFavorites().length+' noticias guardadas en este navegador';
 }
 function renderFavorites(){
  const el=$('portal-favorites-list');if(!el)return;
  el.replaceChildren();
  const rows=readFavorites();
  if(!rows.length){empty(el,'Todavía no has guardado noticias. Pulsa ♡ Guardar en cualquier titular para verlo aquí.');return;}
  for(const item of rows){
   const li=document.createElement('li');li.className='portal-favorite-item';
   const main=document.createElement('div'),link=document.createElement('a'),detail=document.createElement('small');
   link.href=item.url;link.textContent=item.title;link.target='_blank';link.rel='noopener noreferrer nofollow';
   detail.textContent=[item.source,item.category,item.date].filter(Boolean).join(' · ');
   main.append(link,detail);
   const remove=document.createElement('button');remove.type='button';remove.className='portal-btn';remove.textContent='Quitar';
   remove.addEventListener('click',()=>toggleFavorite(item));
   li.append(main,remove);el.append(li);
  }
 }
 let lastSeen=new Set();
 let noticeEnabled=false;
 function matchingNotifications(items){
  const borough=chooseBorough();
  const fourHours=Date.now()-4*60*60*1000;
  return items.filter(a=>validArticle(a)&&alertPattern.test(a.title)&&
   (!borough||a.borough===borough)&&
   (a.published_at&&Date.parse(a.published_at)>fourHours));
 }
 function enableNotifications(){
  const info=$('portal-notification-status');
  if(!('Notification' in window)){if(info)info.textContent='Este navegador no ofrece notificaciones web.';return;}
  if(!window.isSecureContext){if(info)info.textContent='Se requiere HTTPS para activar las notificaciones.';return;}
  Notification.requestPermission().then(permission=>{
   noticeEnabled=permission==='granted';
   if(info)info.textContent=noticeEnabled?
    'Activadas solo mientras esta página esté abierta. El navegador no recibirá avisos al cerrarla.':
    'No se han activado las notificaciones. Puedes seguir leyendo normalmente.';
  }).catch(()=>{if(info)info.textContent='El navegador no permitió solicitar notificaciones.'});
 }
 async function pollNotifications(){
  if(document.visibilityState!=='visible'||!noticeEnabled)return;
  try{
   const r=await fetch('/news.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)return;
   const data=await r.json();
   const current=(Array.isArray(data.articles)?data.articles:[]).filter(validArticle);
   const news=matchingNotifications(current).filter(a=>!lastSeen.has(a.url));
   lastSeen=new Set(current.map(a=>a.url));
   if(!news.length)return;
   const story=news[0];const note=new Notification('CDMX AL MEMENTO · '+(story.category||'Noticia'),{
    body:story.title,tag:'cdmx-memento-nuevo',icon:'/favicon.svg'
   });
   note.onclick=()=>{window.focus();window.open(story.url,'_blank','noopener');note.close()};
  }catch{/* Si la red falla, no inventar ni repetir notificaciones. */}
 }
 document.addEventListener('click',e=>{
  const btn=e.target.closest?.('.fav-save');if(!btn)return;
  toggleFavorite({url:btn.dataset.favoriteUrl,title:btn.dataset.favoriteTitle,
   source:btn.dataset.favoriteSource,category:btn.dataset.favoriteCategory,date:new Date().toISOString().slice(0,10)});
 });
 document.querySelectorAll('[data-borough-select]').forEach(select=>select.addEventListener('change',()=>selectBorough(select.value)));
 $('portal-enable-notifications')?.addEventListener('click',enableNotifications);
 $('portal-clear-favorites')?.addEventListener('click',()=>{writeFavorites([]);renderFavorites();refreshSaveButtons()});
 syncSelects();renderLines();renderFavorites();
 // MutationObserver sobre noticias: guardar funciona en portada, tema y destacados.
 const cardsRoot=document.querySelector('main');
 if(cardsRoot){
  let queued=false;
  new MutationObserver(()=>{
   if(queued)return;
   queued=true;requestAnimationFrame(()=>{queued=false;attachSaveButtons()});
  }).observe(cardsRoot,{childList:true,subtree:true});
  attachSaveButtons();
 }
 feedPromise.then(data=>{
  lastSeen=new Set(data.articles.map(a=>a.url));
  renderToday();renderBorough();renderTransport();renderAlerts();
  const btn=$('portal-enable-notifications');
  if(btn&&'Notification' in window&&Notification.permission==='granted'){
   const note=$('portal-notification-status');
   if(note)note.textContent='Permiso concedido. Pulsa Activar para recibir avisos mientras tengas la pestaña abierta.';
  }
 });
 window.setInterval(pollNotifications,15*60*1000);
 window.CDMX_PORTAL={BOROUGHS,selectBorough,readFavorites,toggleFavorite};
})();
