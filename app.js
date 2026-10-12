'use strict';
const photoLibrary=window.CDMX_FOTOS;
let articles=[],category='',updated='';
const grid=document.getElementById('grid');
const featuredGrid=document.getElementById('featured-grid');
const featuredSection=document.getElementById('destacadas');
const search=document.getElementById('search');
const status=document.getElementById('status');
const reportList=document.getElementById('report-list');
function element(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function validLink(u){try{const p=new URL(u);return p.protocol==='https:'&&p.hostname==='news.google.com'}catch{return false}}
function articleVisual(a){
 const figure=element('div','news-visual');
 const first=photoLibrary?.forArticle(a);
 const photo=first?photoLibrary.images[first]:null;
 if(!photo){figure.append(element('span','photo-unavailable','Fotografía no disponible'));return figure}
 const image=document.createElement('img');
 image.loading='lazy';image.decoding='async';image.width=640;image.height=400;
 const label=element('span','visual-label','FOTO DE ARCHIVO');
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
  credit.textContent='© '+entry.author+' · '+entry.license;
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
 const isFront=!category&&!q;
 const front=isFront?featuredArticles(filtered):[];
 const featuredSet=new Set(front);
 if(featuredSection)featuredSection.hidden=!isFront||!front.length;
 if(featuredGrid){
  featuredGrid.replaceChildren();
  for(const [i,a] of front.entries()){if(validLink(a.url))featuredGrid.append(buildCard(a,true,i===0))}
 }
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
document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',ev=>{
 ev.preventDefault();category=el.dataset.filter||'';render();
 document.getElementById('noticias')?.scrollIntoView({behavior:'smooth',block:'start'});
}));
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
 fetch('/archivo/meses.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('months');return r.json()})
]).then(([news,reports,catalog,months])=>{
 if(catalog.status==='fulfilled')photoLibrary?.addCatalog(catalog.value);
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
