'use strict';
/* Directorio y archivo mensual: sin dependencias, sin imágenes de eventos inventadas. */
(() => {
 const BOROUGHS = ["Álvaro Obregón","Azcapotzalco","Benito Juárez","Coyoacán","Cuajimalpa de Morelos","Cuauhtémoc","Gustavo A. Madero","Iztacalco","Iztapalapa","La Magdalena Contreras","Miguel Hidalgo","Milpa Alta","Tláhuac","Tlalpan","Venustiano Carranza","Xochimilco"];
 const TOPICS=['Metro','Movilidad','Seguridad','Cultura','Gobierno','CDMX'];
 const $=id=>document.getElementById(id);
 const make=(tag,cls,text)=>{
  const element=document.createElement(tag);
  if(cls)element.className=cls;
  if(text!==undefined)element.textContent=text;
  return element;
 };
 const fetchJSON=async url=>{
  const response=await fetch(url,{cache:'no-store'});
  if(!response.ok)throw Error('No está disponible el archivo solicitado.');
  return response.json();
 };
 const params=new URLSearchParams(window.location.search);
 const validExternal=url=>{
  try{const p=new URL(url);return p.protocol==='https:'&&p.hostname==='news.google.com'}catch{return false}
 };
 const dateFormat=new Intl.DateTimeFormat('es-MX',{
  timeZone:'America/Mexico_City',day:'2-digit',month:'long',year:'numeric'
 });
 const timeFormat=new Intl.DateTimeFormat('es-MX',{
  timeZone:'America/Mexico_City',hour:'2-digit',minute:'2-digit',hour12:false
 });
 function publication(article){
  const stamp=typeof article.published_at==='string'?article.published_at:'';
  if(/^\d{4}-\d{2}-\d{2}T/.test(stamp)){
   const date=new Date(stamp);
   if(Number.isFinite(date.getTime())){
    return {day:dateFormat.format(date),time:timeFormat.format(date),iso:stamp};
   }
  }
  const date=/^\d{4}-\d{2}-\d{2}$/.test(article.date||'')?
   article.date.split('-').reverse().join('/'):
   'Fecha no disponible';
  return {day:date,time:'Hora no disponible',iso:''};
 }
 function articleCard(article){
  const div=make('article','archive-note');
  const category=TOPICS.includes(article.category)?article.category:'CDMX';
  const badge=make('span','badge',category);
  const title=make('h3');
  const a=make('a','',article.title||'Noticia sin título');
  if(validExternal(article.url)){
   a.href=article.local_url||'/noticias/';
  }else{a.removeAttribute('href');}
  title.append(a);
  const details=make('div','date-location');
  const p=publication(article);
  const date=make('span','article-datetime','Publicado: '+p.day);
  if(p.iso){const time=document.createElement('time');time.dateTime=p.iso;time.textContent=' · '+p.time+' h (CDMX)';date.append(time);}
  else date.append(document.createTextNode(' · Hora no disponible'));
  const area=make('span','article-location','Zona: '+(article.location||'Ubicación no indicada'));
  const source=make('p','article-source','Medio: '+(article.source||'Fuente externa'));
  details.append(date,area);
  div.append(badge,title,details,source);
  return div;
 }
 const empty=(container,message)=>{
  if(container)container.replaceChildren(make('p','muted',message));
 };
 function sortItems(items){
  return [...items].sort((a,b)=>
   (b.published_at||b.date||'').localeCompare(a.published_at||a.date||''));
 }
 function fillBoroughSelect(){
  const select=$('archive-borough');
  if(!select)return;
  BOROUGHS.forEach(name=>{
   const option=document.createElement('option');option.value=name;option.textContent=name;
   select.append(option);
  });
  const requested=params.get('alcaldia')||'';
  if(BOROUGHS.includes(requested))select.value=requested;
 }
 function archivePage(){
  const select=$('archive-month'),category=$('archive-category'),borough=$('archive-borough'),
        search=$('archive-search'),container=$('archive-results'),status=$('archive-status'),
        prev=$('archive-prev'),next=$('archive-next'),pageLabel=$('archive-page-label');
  fillBoroughSelect();
  let articles=[],page=0,requestIndex=0;
  const PER_PAGE=24;
  function render(){
   const q=(search.value||'').toLocaleLowerCase('es-MX').trim();
   const filtered=articles.filter(a=>{
    if(category.value&&a.category!==category.value)return false;
    if(borough.value&&a.borough!==borough.value)return false;
    return [a.title,a.source,a.location,a.category].some(x=>
     String(x||'').toLocaleLowerCase('es-MX').includes(q));
   });
   const maxPage=Math.max(0,Math.ceil(filtered.length/PER_PAGE)-1);
   page=Math.min(page,maxPage);
   container.replaceChildren();
   filtered.slice(page*PER_PAGE,(page+1)*PER_PAGE).forEach(a=>container.append(articleCard(a)));
   if(!filtered.length)empty(container,
     'No se encontraron titulares con estos filtros en el mes seleccionado. Prueba otro mes o una búsqueda distinta.');
   status.textContent=filtered.length+' noticias · '+select.value+' · El archivo conserva como máximo 365 días.';
   prev.disabled=page===0;next.disabled=page>=maxPage;
   pageLabel.textContent=filtered.length?'Página '+(page+1)+' de '+(maxPage+1):'Sin resultados';
  }
  async function chooseMonth(){
   const month=select.value;
   page=0;
   if(!/^\d{4}-\d{2}$/.test(month))return;
   const request=++requestIndex;
   status.textContent='Cargando las noticias de '+month+'…';
   container.replaceChildren();
   try{
    const data=await fetchJSON('/archivo/'+month+'.json');
    if(request!==requestIndex)return;
    articles=Array.isArray(data.articles)?data.articles.filter(a=>validExternal(a.url)):[];
    render();
   }catch{
    if(request!==requestIndex)return;
    articles=[];empty(container,'No se pudo cargar ese mes. Intenta nuevamente.');
    status.textContent='Error al cargar el archivo de '+month;
    prev.disabled=true;next.disabled=true;pageLabel.textContent='';
   }
  }
  select.addEventListener('change',chooseMonth);
  [category,borough,search].forEach(el=>el.addEventListener(el===search?'input':'change',()=>{
   page=0;render();
  }));
  prev.addEventListener('click',()=>{page=Math.max(0,page-1);render();status.scrollIntoView({block:'start',behavior:'smooth'});});
  next.addEventListener('click',()=>{page++;render();status.scrollIntoView({block:'start',behavior:'smooth'});});
  fetchJSON('/archivo/meses.json').then(data=>{
   const months=Array.isArray(data.months)?data.months.filter(item=>/^\d{4}-\d{2}$/.test(item.month)):[];
   select.replaceChildren();
   if(!months.length){const option=make('option','', 'Todavía no hay meses archivados');option.value='';select.append(option);empty(container,'El primer archivo mensual aparecerá tras la próxima sincronización.');status.textContent='No hay registros disponibles todavía.';return;}
   for(const item of months){
    const option=document.createElement('option');
    option.value=item.month;option.textContent=item.month+' · '+Number(item.count||0)+' notas';
    select.append(option);
   }
   const requested=params.get('mes')||'';
   select.value=months.some(x=>x.month===requested)?requested:months[0].month;
   chooseMonth();
  }).catch(()=>{
   status.textContent='No fue posible consultar los meses archivados.';
   empty(container,'Vuelve a intentar más tarde.');
  });
 }
 function boroughPage(){
  const select=$('borough-selector'), container=$('borough-results'),
        status=$('borough-status'), heading=$('borough-current'),
        linkArchive=$('borough-archive-link'), storyTitle=$('borough-history-heading'),
        storySubtitle=$('borough-history-kicker'), storyText=$('borough-history-text'),
        landmarks=$('borough-landmarks'), sourceLinks=$('borough-history-links'),
        photo=$('borough-photo'), photoCaption=$('borough-photo-caption'),
        photoSource=$('borough-image-source'), photoLicense=$('borough-image-license');
  const requested=params.get('alcaldia');
  let active=BOROUGHS.includes(requested)?requested:'Cuauhtémoc';
  const entries=new Map(), histories=new Map(), photos=new Map();
  let newsReady=false, historyReady=false, photosReady=false, didAutoScroll=false;

  // Reemplaza la cuadrícula de 16 tarjetas por un selector compacto.
  for(const name of BOROUGHS){
   const option=document.createElement('option');
   option.value=name;option.textContent=name;select.append(option);
  }
  function safeOfficial(url){
   try{
    const u=new URL(url);
    return u.protocol==='https:'&&(
      u.hostname==='commons.wikimedia.org' ||
      u.hostname==='creativecommons.org' ||
      u.hostname.endsWith('.creativecommons.org') ||
      u.hostname==='cdmx.gob.mx' ||
      u.hostname.endsWith('.cdmx.gob.mx')
    );
   }catch{return false}
  }
  function displayHistory(){
   storyTitle.textContent='Historia de '+active;
   const story=histories.get(active);
   storyText.replaceChildren();landmarks.replaceChildren();sourceLinks.replaceChildren();
   if(!historyReady){
    storyText.append(make('p','muted','Cargando la historia de esta alcaldía…'));
    return;
   }
   if(!story){
    storySubtitle.textContent='';
    storyText.append(make('p','muted','Por el momento no hay una reseña histórica disponible.'));
    return;
   }
   storySubtitle.textContent=story.eyebrow||'NUESTRA HISTORIA';
   for(const paragraph of Array.isArray(story.history)?story.history:[]){
    storyText.append(make('p','',paragraph));
   }
   for(const place of Array.isArray(story.landmarks)?story.landmarks:[]){
    landmarks.append(make('li','',place));
   }
   for(const source of Array.isArray(story.sources)?story.sources:[]){
    if(!safeOfficial(source.url))continue;
    const link=make('a','',source.label||'Consultar fuente');
    link.href=source.url;
    link.target='_blank';
    link.rel='noopener noreferrer';
    sourceLinks.append(link);
   }
  }
  function displayPhoto(){
   const data=photos.get(active);
   photo.hidden=!data;
   photoCaption.textContent=data?data.caption:'Fotografía representativa no disponible';
   photoSource.hidden=photoLicense.hidden=!data;
   if(!data||!photosReady)return;
   const filename=String(data.slug||'');
   if(!/^[a-z0-9-]+$/.test(filename))return;
   // Solo mostrar fotos descargadas y validadas; sin reutilizar fotos de otras alcaldías.
   photo.src='/assets/alcaldias/'+filename+'.jpg';
   photo.alt='Fotografía de archivo: '+data.caption+'. No muestra un hecho noticioso.';
   photo.onerror=()=>{
    photo.hidden=true;
    photoCaption.textContent='Fotografía no disponible en este momento';
   };
   photoSource.href=safeOfficial(data.source)?data.source:'https://commons.wikimedia.org/';
   photoSource.textContent='© '+(data.author||'Wikimedia Commons')+' · fuente';
   photoLicense.href=safeOfficial(data.licenseUrl)?data.licenseUrl:'https://creativecommons.org/';
   photoLicense.textContent='Licencia '+(data.license||'Creative Commons');
  }
  function displayNews(){
   container.replaceChildren();
   if(!newsReady){
    status.textContent='Cargando los titulares de '+active+'…';
    return;
   }
   const data=entries.get(active)||{count:0,articles:[]};
   const rows=sortItems((Array.isArray(data.articles)?data.articles:[])
        .filter(a=>validExternal(a.url)));
   for(const article of rows)container.append(articleCard(article));
   if(!rows.length)empty(container,'Todavía no hay noticias archivadas que mencionen '+active+'. Puedes explorar otros meses.');
   const count=Math.max(0,Number(data.count)||0);
   status.textContent=count+' '+(count===1?'noticia registrada':'noticias registradas')+
      ' en los últimos 365 días · Se muestran hasta 24 titulares recientes.';
  }
  function view(){
   heading.textContent=active;
   document.title=active+' · historia y noticias | CDMX AL MEMENTO';
   select.value=active;
   linkArchive.href='/archivo/?alcaldia='+encodeURIComponent(active);
   displayPhoto();
   displayHistory();
   displayNews();
  }
  function change(name){
   if(!BOROUGHS.includes(name))return;
   active=name;
   const url=new URL(window.location.href);
   url.searchParams.set('alcaldia',name);
   url.hash='#noticias-alcaldia';
   history.replaceState(null,'',url);
   view();
   $('noticias-alcaldia')?.scrollIntoView({
    behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',
    block:'start'
   });
  }
  select.addEventListener('change',()=>change(select.value));
  window.addEventListener('popstate',()=>{
   const name=new URLSearchParams(window.location.search).get('alcaldia');
   active=BOROUGHS.includes(name)?name:'Cuauhtémoc';
   view();
  });
  view();
  Promise.allSettled([
    fetchJSON('/alcaldias/noticias.json'),
    fetchJSON('/assets/alcaldias/historias.json'),
    fetchJSON('/assets/alcaldias/fotos.json')
  ]).then(([news,historyData,photoData])=>{
   if(news.status==='fulfilled'){
    for(const item of Array.isArray(news.value.boroughs)?news.value.boroughs:[]){
     if(BOROUGHS.includes(item.name))entries.set(item.name,item);
    }
   }
   if(historyData.status==='fulfilled'){
    for(const item of Array.isArray(historyData.value.boroughs)?historyData.value.boroughs:[]){
     if(BOROUGHS.includes(item.name))histories.set(item.name,item);
    }
   }
   if(photoData.status==='fulfilled'){
    for(const item of Array.isArray(photoData.value.photos)?photoData.value.photos:[]){
     if(BOROUGHS.includes(item.name))photos.set(item.name,item);
    }
   }
   newsReady=true;historyReady=true;photosReady=true;
   view();
   // Las visitas desde la columna de la portada llegan directamente aquí.
   if(!didAutoScroll && window.location.hash==='#noticias-alcaldia'){
    didAutoScroll=true;
    requestAnimationFrame(()=>$('noticias-alcaldia')?.scrollIntoView({block:'start'}));
   }
  });
 }
 if(document.body.dataset.page==='archive')archivePage();
 if(document.body.dataset.page==='borough')boroughPage();
})();
