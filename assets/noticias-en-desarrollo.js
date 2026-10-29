/* Cronología de titulares existentes; no afirma correspondencia entre sucesos. */
(()=>{
'use strict';
const $=id=>document.getElementById(id);
const category=$('dev-category'),search=$('dev-search'),timeline=$('dev-timeline'),more=$('dev-more'),status=$('dev-status'),refresh=$('dev-refresh');
if(!category||!search||!timeline||!more||!status||!refresh)return;
let items=[],visible=12,updated='',lastRequest=0;
const local=/^\/noticias\/\?id=[a-f0-9]{20}&mes=20\d{2}-(0[1-9]|1[0-2])$/;
const norm=text=>String(text||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es-MX');
const safeTitle=value=>String(value||'Sin titular').slice(0,320);
const getDate=a=>{
 const stamp=Date.parse(a.published_at||'');
 if(Number.isFinite(stamp))return stamp;
 const date=Date.parse(String(a.date||'')+'T12:00:00Z');
 return Number.isFinite(date)?date:0;
};
const shortDate=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',day:'numeric',month:'short',year:'numeric'});
const fullDate=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'medium',timeStyle:'short'});
function node(tag,content){const el=document.createElement(tag);if(content!==undefined)el.textContent=content;return el}
function dateLabel(a){
 const published=Date.parse(a.published_at||'');
 if(Number.isFinite(published))return fullDate.format(published)+' (publicación)';
 const fallback=getDate(a);
 return fallback?shortDate.format(fallback)+' · hora no indicada':'Fecha por confirmar';
}
function valid(a){return a&&typeof a.title==='string'&&a.title.trim().length>0&&typeof a.source==='string';}
function safeLink(url){try{const value=new URL(String(url));return value.protocol==='https:'&&value.hostname==='news.google.com'?value.toString():null}catch{return null}}
function render(){
 const query=norm(search.value.trim()),selected=category.value;
 const shown=items.filter(a=>(!selected||a.category===selected)&&(!query||norm([a.title,a.category,a.borough,a.source].join(' ')).includes(query)));
 timeline.replaceChildren();
 const active=shown.slice(0,visible);
 if(!active.length){timeline.append(node('p',query?'No hay noticias que coincidan con la búsqueda.':'No hay titulares disponibles en esta categoría.'));}
 for(const article of active){
  const card=node('article');card.className='dev-story';
  const time=node('time',dateLabel(article));if(article.published_at)time.dateTime=article.published_at;card.append(time);
  const theme=node('span',' · '+String(article.category||'CDMX'));theme.className='dev-category';card.append(theme);
  card.append(node('h3',safeTitle(article.title)));
  const meta=node('p','Fuente: '+String(article.source||'Medio externo').slice(0,100)+(article.borough?' · Alcaldía mencionada: '+String(article.borough).slice(0,55):''));meta.className='dev-source';card.append(meta);
  const desc=String(article.description||'').trim();
  if(desc)card.append(node('p',desc.slice(0,260)));
  const links=node('div');links.className='dev-links';
  if(local.test(String(article.local_url||''))){
   const link=node('a','Leer ficha y contexto');link.href=article.local_url;links.append(link);
  }
  const external=safeLink(article.url);
  if(external){const link=node('a','Consultar medio original');link.href=external;link.target='_blank';link.rel='noopener noreferrer nofollow';links.append(link);}
  card.append(links);timeline.append(card);
 }
 more.hidden=shown.length<=visible;
 status.textContent=shown.length+' titular(es) · Archivo actualizado: '+(updated||'sin fecha informada')+'.';
}
function refillCategory(){
 const old=category.value;
 category.replaceChildren();
 const all=node('option','Todas las categorías');all.value='';category.append(all);
 const labels=[...new Set(items.map(x=>String(x.category||'CDMX')))].sort((a,b)=>a.localeCompare(b,'es-MX'));
 for(const label of labels){const option=node('option',label);option.value=label;category.append(option);}
 category.value=labels.includes(old)?old:'';
}
async function load(){
 const current=++lastRequest;
 refresh.disabled=true;status.textContent='Consultando el archivo de noticias…';
 try{
  const response=await fetch('/news.json?t='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();
  if(!Array.isArray(data.articles))throw Error('Formato de noticias inválido');
  const seen=new Set(),fresh=[];
  for(const a of data.articles){
   if(!valid(a))continue;
   const key=String(a.local_url||'')||norm(a.title)+'|'+String(a.date||'');
   if(seen.has(key))continue;
   seen.add(key);fresh.push(a);
  }
  if(current!==lastRequest)return;
  items=fresh.sort((a,b)=>getDate(b)-getDate(a));updated=String(data.updated||'');
  visible=12;refillCategory();render();
 }catch(error){
  if(current===lastRequest)status.textContent='No fue posible cargar las noticias. Verifica tu conexión y vuelve a intentarlo.';
 }finally{if(current===lastRequest)refresh.disabled=false}
}
category.addEventListener('change',()=>{visible=12;render()});
search.addEventListener('input',()=>{visible=12;render()});
more.addEventListener('click',()=>{visible+=12;render()});
refresh.addEventListener('click',load);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&!refresh.disabled)load()});
load();
})();
