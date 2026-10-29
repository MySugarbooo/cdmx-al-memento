/* Panel de datos reales: lecturas GET únicamente, nunca genera visitas ni votos. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const number=n=>Number.isSafeInteger(n)&&n>=0?n.toLocaleString('es-MX'):'No disponible';
const formatDate=value=>{const normalized=typeof value==='string'?value.replace(/^(\\d{4}-\\d{2}-\\d{2}) (\\d{2}:\\d{2}) UTC$/,'$1T$2:00Z'):value;const d=new Date(normalized);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'}).format(d):'No disponible'};
async function get(url){const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),9000);try{const r=await fetch(url,{method:'GET',credentials:'same-origin',cache:'no-store',signal:ctrl.signal});if(!r.ok)throw Error('Respuesta '+r.status);return await r.json()}finally{clearTimeout(timer)}}
let loading=false;
async function load(){if(loading)return;loading=true;const btn=$('stats-refresh');btn.disabled=true;const status=$('stats-status');status.textContent='Consultando fuentes…';
const sources=await Promise.allSettled([get('/api/engagement'),get('/api/likes'),get('/news.json')]);
const visits=sources[0].status==='fulfilled'?sources[0].value:null;
const likes=sources[1].status==='fulfilled'?sources[1].value:null;
const news=sources[2].status==='fulfilled'?sources[2].value:null;
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
