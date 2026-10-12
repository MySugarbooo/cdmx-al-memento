'use strict';
/* Directorio y archivo mensual: sin dependencias, sin imágenes de eventos inventadas. */
(() => {
 const BOROUGHS = [
  'La Magdalena Contreras','Álvaro Obregón','Azcapotzalco','Benito Juárez',
  'Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero',
  'Iztacalco','Iztapalapa','Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan',
  'Venustiano Carranza','Xochimilco'
 ];
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
   a.href=article.url;
   a.target='_blank';
   a.rel='noopener noreferrer nofollow';
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
  const directory=$('borough-directory'),container=$('borough-results'),
        status=$('borough-status'),header=$('borough-current'),archiveLink=$('borough-archive-link');
  const requested=params.get('alcaldia');
  let active=BOROUGHS.includes(requested)?requested:BOROUGHS[0];
  const entries=new Map();
  let loaded=false;
  function view(){
   header.textContent=active;
   archiveLink.href='/archivo/?alcaldia='+encodeURIComponent(active);
   directory.querySelectorAll('[data-borough]').forEach(a=>{
    const isActive=a.dataset.borough===active;
    a.classList.toggle('active',isActive);
    if(isActive)a.setAttribute('aria-current','true');
    else a.removeAttribute('aria-current');
   });
   if(!loaded){status.textContent='Consultando noticias disponibles…';return;}
   const data=entries.get(active)||{count:0,articles:[]};
   const rows=sortItems((Array.isArray(data.articles)?data.articles:[]).filter(a=>validExternal(a.url)));
   container.replaceChildren();
   rows.forEach(row=>container.append(articleCard(row)));
   if(!rows.length)empty(container,'Todavía no se han registrado titulares que mencionen esta alcaldía. Puedes revisar el archivo mensual.');
   status.textContent=Number(data.count||0)+' noticias registradas en los últimos 365 días. Se muestran hasta 24 de las más recientes.';
  }
  for(const [index,name] of BOROUGHS.entries()){
   const link=make('a','alcaldia-card'+(index<2?' principal':''));
   link.href='/alcaldias/?alcaldia='+encodeURIComponent(name);
   link.dataset.borough=name;
   link.append(make('span','borough-index',String(index+1).padStart(2,'0')),
     make('strong','',name),make('span','borough-arrow','↗'));
   link.addEventListener('click',event=>{
    event.preventDefault();active=name;
    const url=new URL(window.location.href);
    url.searchParams.set('alcaldia',name);
    history.replaceState(null,'',url);
    view();header.scrollIntoView({behavior:'smooth',block:'start'});
   });
   directory.append(link);
  }
  view();
  fetchJSON('/alcaldias/noticias.json').then(data=>{
   for(const item of Array.isArray(data.boroughs)?data.boroughs:[]){
    if(BOROUGHS.includes(item.name))entries.set(item.name,item);
   }
   loaded=true;view();
  }).catch(()=>{loaded=true;status.textContent='No se pudo cargar la lista de noticias. Intenta nuevamente.';});
 }
 if(document.body.dataset.page==='archive')archivePage();
 if(document.body.dataset.page==='borough')boroughPage();
})();
