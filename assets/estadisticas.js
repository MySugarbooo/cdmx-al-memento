/* Panel de datos reales: lecturas GET únicamente, nunca genera visitas ni votos. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const number=n=>Number.isSafeInteger(n)&&n>=0?n.toLocaleString('es-MX'):'No disponible';
const formatDate=value=>{const normalized=typeof value==='string'?value.replace(/^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC$/,'$1T$2:00Z'):value;const d=new Date(normalized);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'}).format(d):'No disponible'};
async function get(url){const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),9000);try{const r=await fetch(url,{method:'GET',credentials:'same-origin',cache:'no-store',signal:ctrl.signal});if(!r.ok)throw Error('Respuesta '+r.status);return await r.json()}finally{clearTimeout(timer)}}
const categories=new Set(['CDMX','Seguridad','Movilidad','Gobierno','Cultura','Economía','Deportes','Salud','Medio ambiente','Servicios']);
function renderBreakdown(news){
 const container=$('stats-breakdown');if(!container)return;
 container.replaceChildren();
 if(!news||!Array.isArray(news.articles)){container.textContent='No disponible: no se pudo consultar el índice de noticias.';return}
 const counts=new Map();for(const article of news.articles){const raw=typeof article.category==='string'?article.category.trim():'';const category=raw&&raw.length<=48?raw:'Sin categoría';counts.set(category,(counts.get(category)||0)+1)}
 const ranked=[...counts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'es')).slice(0,8);const max=ranked[0]?.[1]||1;
 if(!ranked.length){container.textContent='No hay noticias en el índice actual.';return}
 for(const [name,count] of ranked){const item=document.createElement('div');item.className='stats-breakdown-item';const line=document.createElement('div');line.className='stats-breakdown-label';const label=document.createElement('span');label.textContent=name;const amount=document.createElement('strong');amount.textContent=number(count);line.append(label,amount);const track=document.createElement('div');track.className='stats-breakdown-track';track.setAttribute('role','img');track.setAttribute('aria-label',name+': '+count+' noticias');const bar=document.createElement('div');bar.className='stats-breakdown-bar';bar.style.width=(100*count/max).toFixed(2)+'%';track.append(bar);item.append(line,track);container.append(item)}
 const note=$('stats-breakdown-note');if(note)note.textContent='Distribución de '+news.articles.length+' artículos del índice actual, no del histórico completo.';
}
let loading=false;
async function load(){if(loading)return;loading=true;const btn=$('stats-refresh');btn.disabled=true;const status=$('stats-status');status.textContent='Consultando fuentes…';
const sources=await Promise.allSettled([get('/api/engagement'),get('/api/likes'),get('/news.json')]);
const visits=sources[0].status==='fulfilled'?sources[0].value:null;
const likes=sources[1].status==='fulfilled'?sources[1].value:null;
const news=sources[2].status==='fulfilled'?sources[2].value:null;
renderBreakdown(news);
$('stats-visitors').textContent=visits?number(visits.visitors):'No disponible';
$('stats-likes').textContent=likes?number(likes.total):'No disponible';
$('stats-news').textContent=news&&Array.isArray(news.articles)?number(news.articles.length):'No disponible';
$('stats-updated').textContent=news&&typeof news.updated==='string'?formatDate(news.updated):'No disponible';
const failures=sources.map((s,i)=>s.status==='rejected'?['visitantes','Me gusta','noticias'][i]:null).filter(Boolean);
status.textContent=failures.length?'Fuentes no disponibles: '+failures.join(', ')+'. Las demás cifras sí se consultaron.':'Datos consultados correctamente en las tres fuentes.';
$('stats-consulted').textContent='Consulta realizada: '+formatDate(new Date().toISOString())+'.';
loading=false;btn.disabled=false}
$('stats-refresh')?.addEventListener('click',load);load();
})();
