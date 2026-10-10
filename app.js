'use strict';
const icons={Metro:'🚇',Movilidad:'🚦',Seguridad:'🛡️',Cultura:'🎭',Gobierno:'🏛️',CDMX:'🏙️'};
const categoryImages={Metro:'metro',Movilidad:'movilidad',Seguridad:'seguridad',Cultura:'cultura',Gobierno:'gobierno',CDMX:'cdmx'};
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
 const image=document.createElement('img');
 const category=categoryImages[a.category]||'cdmx';
 image.src='/assets/imagenes/'+category+'.svg';
 image.alt='Ilustración editorial sobre '+(a.category||'Ciudad de México')+', no fotografía de la noticia';
 image.loading='lazy';image.decoding='async';image.width=800;image.height=500;
 const label=element('span','visual-label','IMAGEN ILUSTRATIVA');
 figure.append(image,label);
 return figure;
}
function buildCard(a,featured=false,large=false){
 const c=element('article',featured?'card featured-card'+(large?' featured-main':''):'card');
 const visual=articleVisual(a),inside=element('div','inside');
 const badge=element('span','badge',a.category||'CDMX');
 const title=element('h3','',a.title);
 const description=element('p','',featured
   ?'Lee la cobertura completa y confirma los detalles con el medio que publicó esta noticia.'
   :'Titular recopilado automáticamente. Consulta la fuente original para obtener contexto.');
 const meta=element('div','meta',(a.source||'Fuente externa')+' · '+(a.date||''));
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
document.querySelectorAll('img[data-fallback]').forEach(img=>{
 img.addEventListener('error',()=>{img.src=img.dataset.fallback;img.removeAttribute('data-fallback')},{once:true});
});
Promise.allSettled([
 fetch('/news.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('news');return r.json()}),
 fetch('/reports.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error('reports');return r.json()})
]).then(([news,reports])=>{
 if(news.status==='fulfilled'&&Array.isArray(news.value.articles)){
  articles=news.value.articles.filter(a=>a&&typeof a.title==='string'&&validLink(a.url));
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
});
