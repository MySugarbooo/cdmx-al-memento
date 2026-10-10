'use strict';
const icons={Metro:'🚇',Movilidad:'🚦',Seguridad:'🛡️',Cultura:'🎭',Gobierno:'🏛️',CDMX:'🏙️'};
let articles=[],category='',updated='';
const grid=document.getElementById('grid'),search=document.getElementById('search'),status=document.getElementById('status'),reportList=document.getElementById('report-list');
function element(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function validLink(u){try{const p=new URL(u);return p.protocol==='https:'&&p.hostname==='news.google.com'}catch{return false}}
function render(){
 const q=(search?.value||'').toLocaleLowerCase('es-MX').trim();
 const filtered=articles.filter(a=>(!category||a.category===category)&&[a.title,a.source,a.category].some(v=>String(v||'').toLocaleLowerCase('es-MX').includes(q)));
 if(status)status.textContent=filtered.length?filtered.length+' noticias disponibles · Última sincronización: '+updated:'No hay noticias para esta búsqueda.';
 if(grid){grid.replaceChildren();for(const a of filtered){if(!validLink(a.url))continue;const c=element('article','card'),art=element('div','art',icons[a.category]||'📰'),inside=element('div','inside');art.setAttribute('aria-hidden','true');inside.append(element('span','badge',a.category||'CDMX'),element('h3','',a.title),element('p','','Este titular se recopiló automáticamente. Consulta la nota original para conocer detalles y contexto.'),element('div','meta',(a.source||'Fuente externa')+' · '+(a.date||'')));const link=element('a','read','Leer en la fuente ↗');link.href=a.url;link.target='_blank';link.rel='noopener noreferrer nofollow';inside.append(link);c.append(art,inside);grid.append(c);}}
 document.querySelectorAll('[data-filter]').forEach(el=>{el.classList.toggle('active',el.dataset.filter===category);el.setAttribute('aria-pressed',String(el.dataset.filter===category))});
}
search?.addEventListener('input',render);
document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',ev=>{ev.preventDefault();category=el.dataset.filter||'';render();document.getElementById('noticias')?.scrollIntoView({behavior:'smooth'})}));
Promise.allSettled([fetch('/news.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error();return r.json()}),fetch('/reports.json?t='+Date.now()).then(r=>{if(!r.ok)throw Error();return r.json()})]).then(([n,r])=>{
 if(n.status==='fulfilled'&&Array.isArray(n.value.articles)){articles=n.value.articles.filter(a=>a&&typeof a.title==='string'&&validLink(a.url));updated=n.value.updated||'sin fecha';render()}else if(status)status.textContent='No fue posible cargar las noticias.';
 if(reportList){reportList.replaceChildren();const data=r.status==='fulfilled'&&Array.isArray(r.value.reports)?r.value.reports:[];for(const x of data.slice(0,5)){if(!/^\/reportes\/\d{4}-\d{2}-\d{2}\.html$/.test(x.url))continue;const li=element('li'),a=element('a','','Reporte del '+x.date);a.href=x.url;li.append(a,document.createTextNode(' · '+Number(x.count||0)+' titulares'));reportList.append(li)}if(!reportList.children.length)reportList.append(element('li','','El primer reporte aparecerá cuando haya suficientes titulares y fuentes.'))}
});
