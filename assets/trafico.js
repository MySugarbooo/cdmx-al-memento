/* Etapa 7 · información vial: prensa reciente + accesos oficiales.
 * Ningún titular se etiqueta como cierre vigente ni como confirmación oficial.
 */
(()=>{
'use strict';
const $=id=>document.getElementById(id),root=$('traffic-list'),status=$('traffic-status');
const type=$('traffic-type'),borough=$('traffic-borough'),search=$('traffic-search');
const reload=$('traffic-reload'),more=$('traffic-more'),total=$('traffic-total');
const boroughCount=$('traffic-borough-count'),lastChecked=$('traffic-last-checked');
if(!root||!status||!type||!borough||!search||!reload||!more||!total||!boroughCount||!lastChecked)return;

const BOROUGHS=['Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras','Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'];
const names={marchas:'Marchas y concentraciones',cierres:'Bloqueos y cierres',obras:'Obras y carriles',incidentes:'Incidentes viales'};
const dateFmt=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'medium',timeStyle:'short'});
const hourFmt=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',hour:'2-digit',minute:'2-digit'});
const norm=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const txt=(tag,value,cls)=>{const el=document.createElement(tag);if(value!==undefined)el.textContent=String(value);if(cls)el.className=cls;return el};
let articles=[],provenance='none',consulted=null,visible=9,loading=false,lastLoad=0;
const maxAge=48*60*60*1000;

function classify(title){
 const t=norm(title);
 if(/\b(marcha|marchas|manifestacion|manifestantes|movilizacion|protesta|concentracion)\b/.test(t))return 'marchas';
 if(/\b(choque|accidente|volcadura|percance|inundacion|socavon)\b/.test(t)&&/\b(vial|avenida|calzada|carretera|autopista|calle|transito|circulacion|periferico|insurgentes)\b/.test(t))return 'incidentes';
 if(/\b(obra|obras|repavimentacion|mantenimiento|reparacion|carriles)\b/.test(t)&&/\b(vial|cierre|calle|avenida|calzada|transito|circulacion|carriles|autopista|periferico)\b/.test(t))return 'obras';
 if(/\b(cierre|cierres|cerrada|cerrado|bloqueo|bloqueos|corte|afectacion|afectaciones|trafico)\b/.test(t)&&/\b(vial|calle|calles|avenida|calzada|carriles|circulacion|carretera|autopista|reforma|periferico|insurgentes|bloqueo|bloqueos|trafico)\b/.test(t))return 'cierres';
 return null;
}
function matchingBorough(title){
 const t=norm(title);
 return BOROUGHS.find(name=>t.includes(norm(name)))||'No precisada';
}
function likelyCDMX(title){
 const t=norm(title);
 const local=/\b(cdmx|ciudad de mexico|capital mexicana|capital del pais|paseo de la reforma|eje central|circuito interior|calzada de tlalpan)\b/.test(t)||BOROUGHS.some(name=>t.includes(norm(name)));
 const outside=/\b(xalapa|veracruz|guadalajara|monterrey|puebla|cancun|queretaro|morelia|tijuana|oaxaca|merida|zacatecas)\b/.test(t);
 return local&&(!outside||BOROUGHS.some(name=>t.includes(norm(name))));
}
function allowedURL(value){
 try{
  const u=new URL(String(value||''));
  return u.protocol==='https:'&&u.hostname==='news.google.com'&&u.pathname.startsWith('/rss/articles/')?u.href:'';
 }catch{return ''}
}
function allowLocal(value){
 return typeof value==='string'&&/^\/noticias\/\?id=[a-f0-9]{20}&mes=20\d\d-(0[1-9]|1[0-2])$/.test(value)?value:'';
}
function recent(item){
 const time=Date.parse(item?.published_at||'');
 return Number.isFinite(time)&&time<=Date.now()+300000&&Date.now()-time<=maxAge;
}
function valid(row){
 return row&&typeof row.title==='string'&&row.title.trim().length>8&&recent(row)&&names[row.type]&&allowedURL(row.url);
}
function fromArchive(data){
 const input=Array.isArray(data?.articles)?data.articles:[];
 return input.filter(x=>x&&typeof x.title==='string'&&likelyCDMX(x.title)).map(a=>({
  title:String(a.title).slice(0,240),
  published_at:a.published_at,
  source:String(a.source||'Medio de comunicación').slice(0,95),
  type:classify(a.title),
  borough:matchingBorough(a.title),
  url:a.url,
  local_url:allowLocal(a.local_url)
 })).filter(valid);
}
function normalizeApi(data){
 if(data?.schema!==1||data?.status!=='ok'||!Array.isArray(data.articles))return [];
 const time=Date.parse(data.checked_at||'');
 if(!Number.isFinite(time)||Date.now()-time>60*60*1000||time>Date.now()+5*60*1000)return [];
 return data.articles.filter(valid).map(a=>({
  title:String(a.title).slice(0,240),
  published_at:a.published_at,
  source:String(a.source||'Medio de comunicación').slice(0,95),
  type:a.type,
  borough:BOROUGHS.includes(a.borough)?a.borough:'No precisada',
  url:allowedURL(a.url)
 }));
}
function unique(rows){
 const found=new Set(),result=[];
 for(const item of rows.sort((a,b)=>Date.parse(b.published_at)-Date.parse(a.published_at))){
  const key=norm(item.title).replace(/[^a-z0-9]/g,'').slice(0,140);
  if(found.has(key))continue;found.add(key);result.push(item);
 }
 return result.slice(0,60);
}
function refillBoroughs(){
 const value=borough.value;
 borough.replaceChildren();
 const all=txt('option','Todas las zonas');all.value='all';borough.append(all);
 const avail=BOROUGHS.filter(name=>articles.some(a=>a.borough===name));
 for(const name of avail){const o=txt('option',name);o.value=name;borough.append(o)}
 borough.value=avail.includes(value)?value:'all';
}
function render(){
 const filtered=articles.filter(item=>
  (type.value==='all'||item.type===type.value)&&
  (borough.value==='all'||item.borough===borough.value)&&
  (!search.value.trim()||norm([item.title,item.source,item.borough].join(' ')).includes(norm(search.value.trim())))
 );
 root.replaceChildren();
 for(const item of filtered.slice(0,visible)){
  const card=txt('article',undefined,'traffic-card');
  const head=txt('div',undefined,'traffic-card-top');
  head.append(txt('span',names[item.type],'traffic-card-kind'));
  const when=txt('time',dateFmt.format(new Date(item.published_at))+' · publicación del medio');
  when.dateTime=item.published_at;head.append(when);card.append(head);
  card.append(txt('h3',item.title));
  card.append(txt('p','Alcaldía: '+(item.borough==='No precisada'?'no identificada con certeza en el titular':item.borough+' (mencionada en el titular)'),'traffic-card-desc'));
  const meta=txt('div','Fuente: '+item.source,'traffic-card-source');card.append(meta);
  const url=allowedURL(item.url);
  if(url){
   const a=txt('a','Consultar titular y fuente ↗','traffic-card-link');
   a.href=url;a.target='_blank';a.rel='noopener noreferrer nofollow';
   card.append(a);
  }
  if(item.local_url){
   const a=txt('a',' · Leer ficha en CDMX AL MEMENTO','traffic-card-link');
   a.href=item.local_url;card.append(a);
  }
  root.append(card);
 }
 if(!filtered.length){
  const message=articles.length?
   'No hay titulares que coincidan con tus filtros. Prueba otra alcaldía o categoría.':
   'No encontramos titulares viales recientes verificables en nuestro índice. Esto NO significa que las calles estén libres; revisa las fuentes oficiales de arriba.';
  root.append(txt('p',message,'traffic-empty'));
 }
 more.hidden=filtered.length<=visible;
 total.textContent=String(articles.length);
 boroughCount.textContent=String(new Set(articles.map(a=>a.borough).filter(a=>a!=='No precisada')).size);
 lastChecked.textContent=consulted?hourFmt.format(consulted):'—';
 const source=provenance==='api'?'Titulares obtenidos de medios indexados por Google News.':
  provenance==='archive'?'Respaldo: archivo de noticias de CDMX AL MEMENTO.':
  'Fuentes de titulares no disponibles.';
 status.textContent=source+' '+filtered.length+' resultados en la selección · ventana de publicación: últimas 48 h. Una noticia no demuestra que siga existiendo un cierre.';
}
async function timedFetch(url,ms){
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),ms);
 try{
  const response=await fetch(url,{cache:'no-store',signal:ctrl.signal});
  if(!response.ok)throw Error('HTTP '+response.status);
  return await response.json();
 }finally{clearTimeout(timer)}
}
async function load(){
 if(loading)return;
 loading=true;reload.disabled=true;reload.textContent='Consultando…';
 status.textContent='Buscando información vial reciente…';
 let rows=[],selected='none';
 try{
  const data=await timedFetch('/api/trafico?t='+Date.now(),8500);
  rows=normalizeApi(data);if(rows.length)selected='api';
 }catch(e){console.warn('El índice vial externo no está disponible:',e.message||e)}
 if(!rows.length){
  try{
   const backup=await timedFetch('/news.json?t='+Date.now(),6000);
   rows=fromArchive(backup);
   if(rows.length)selected='archive';
  }catch(e){console.warn('No hay índice de respaldo vial:',e.message||e)}
 }
 articles=unique(rows);provenance=selected;consulted=new Date();lastLoad=Date.now();
 visible=9;refillBoroughs();render();
 loading=false;reload.disabled=false;reload.textContent='Actualizar titulares';
}
type.addEventListener('change',()=>{visible=9;render()});
borough.addEventListener('change',()=>{visible=9;render()});
search.addEventListener('input',()=>{visible=9;render()});
more.addEventListener('click',()=>{visible+=9;render()});
reload.addEventListener('click',load);
document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState==='visible'&&Date.now()-lastLoad>15*60*1000)void load();
});
// Mantener una pestaña abierta al día sin peticiones por segundo.
setInterval(()=>{
 if(document.visibilityState==='visible'&&Date.now()-lastLoad>=15*60*1000)void load();
},60*1000);
load();
})();