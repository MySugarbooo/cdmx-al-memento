/* Etapa 6 · Estado de Metro y Metrobús.
   Datos del tablero oficial recogidos periódicamente por GitHub Actions.
   Nunca transforma ausencia de datos o información antigua en "servicio normal".
*/
(()=>{
'use strict';
const $=id=>document.getElementById(id);
const root=$('transport-live'),grid=$('transport-grid'),status=$('transport-status');
const meta=$('transport-updated'),button=$('transport-refresh');
const countMetro=$('transport-stat-metro'),countMb=$('transport-stat-mb');
const countIncidents=$('transport-stat-affected'),notes=$('transport-note');
if(!root||!grid||!status||!meta||!button||!countMetro||!countMb||!countIncidents)return;
const config={
 stc:{name:'Metro',url:'https://www.metro.cdmx.gob.mx/la-red/estado-del-servicio',
  lines:['1','2','3','4','5','6','7','8','9','12','A','B']},
 mb:{name:'Metrobús',url:'https://metrobus.cdmx.gob.mx/ServicioMB',
  lines:['1','2','3','4','5','6','7']}
};
const allSystems=['stc','mb'];
const maximumAge=90*60*1000;
const dateFormat=new Intl.DateTimeFormat('es-MX',{
 dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'
});
const allowedSystem=key=>Object.prototype.hasOwnProperty.call(config,key);
let choice='all',snapshot=null,fresh=false,activeRequest=0,previousCheck=0,loading=false;
const node=(tag,text,className)=>{
 const el=document.createElement(tag);
 if(text!==undefined)el.textContent=String(text);
 if(className)el.className=className;
 return el;
};
function sourceLink(system,label){
 const a=node('a',label||'Consultar operador oficial');
 a.href=config[system].url;a.target='_blank';a.rel='noopener noreferrer';
 return a;
}
function groupLines(rows,system){
 const grouped=new Map(config[system].lines.map(name=>[name,[]]));
 for(const row of rows){
  if(!row||!grouped.has(row.linea)||typeof row.estado!=='string')continue;
  grouped.get(row.linea).push(row);
 }
 return grouped;
}
function isComplete(data){
 if(!data||data.schema!==1||data.status!=='ok'||!data.operators)return false;
 for(const system of allSystems){
  const rows=data.operators[system]?.rows;
  if(!Array.isArray(rows)||rows.length<config[system].lines.length||rows.length>60)return false;
  const grouped=groupLines(rows,system);
  if([...grouped.values()].some(values=>values.length===0))return false;
  if(rows.some(row=>!row||!config[system].lines.includes(row.linea)
   ||typeof row.estado!=='string'||row.estado.trim().length===0))return false;
 }
 return true;
}
function isFresh(data){
 const date=Date.parse(data?.checked_at||'');
 const age=Date.now()-date;
 return isComplete(data)&&Number.isFinite(date)&&age>=-5*60*1000&&age<=maximumAge;
}
function formatCheckedAt(data){
 const time=Date.parse(data?.checked_at||'');
 return Number.isFinite(time)?dateFormat.format(new Date(time)):'Sin registro de consulta';
}
function countOperator(data,system){
 if(!isFresh(data))return {affected:null,regular:null};
 const rows=groupLines(data.operators[system].rows,system);
 let affected=0,regular=0;
 for(const lines of rows.values()){
  if(lines.some(row=>!String(row.estado).toLocaleLowerCase('es-MX').startsWith('servicio regular')))affected++;
  else regular++;
 }
 return {affected,regular};
}
function createLineCard(system,line,rows,upToDate){
 const article=node('article',undefined,'transport-line');
 article.dataset.system=system;article.dataset.line=line;
 const head=node('div',undefined,'transport-line-head');
 const badge=node('span',system==='stc'?'Metro · Línea '+line:'Metrobús · Línea '+line,'transport-line-label');
 badge.dataset.system=system;badge.dataset.line=line;
 const hasNotice=upToDate&&rows.some(row=>
  !String(row.estado).toLocaleLowerCase('es-MX').startsWith('servicio regular'));
 const state=node('strong',upToDate?(hasNotice?'Incidencia informada':'Servicio regular reportado'):'Sin verificación reciente',
  'transport-line-state');
 state.dataset.state=upToDate?(hasNotice?'incident':'regular'):'unknown';
 head.append(badge,state);article.append(head);
 if(upToDate){
  const incidentRows=rows.filter(row=>
   !String(row.estado).toLocaleLowerCase('es-MX').startsWith('servicio regular'));
  if(incidentRows.length){
   for(const item of incidentRows){
    const part=node('div',undefined,'transport-incident');
    part.append(node('strong',String(item.estado).slice(0,110)));
    const affected=String(item.estaciones_afectadas||'').trim();
    if(affected&&!/^ningun[ao]s?$/i.test(affected))part.append(node('p','Tramo/estaciones: '+affected.slice(0,180)));
    const info=String(item.informacion_adicional||'').trim();
    if(info)part.append(node('p',info.slice(0,350)));
    article.append(part);
   }
  }else{
   article.append(node('p','El tablero oficial registra «Servicio Regular». Esto no confirma circulación en este momento ni descarta afectaciones sin reportar.','transport-line-info'));
  }
 }else{
  article.append(node('p','No hay una consulta reciente y completa para confirmar la situación de esta línea.','transport-line-info'));
 }
 const more=node('div',undefined,'transport-line-links');
 more.append(sourceLink(system,'Ver estado en '+config[system].name+' ↗'));
 article.append(more);
 return article;
}
function render(){
 const usable=isFresh(snapshot);
 fresh=usable;grid.replaceChildren();
 const systems=choice==='all'?allSystems:[choice];
 for(const system of systems){
  const group=groupLines(usable?snapshot.operators[system].rows:[],system);
  for(const line of config[system].lines){
   grid.append(createLineCard(system,line,group.get(line)||[],usable));
  }
 }
 const metro=countOperator(snapshot,'stc'),mb=countOperator(snapshot,'mb');
 countMetro.textContent=metro.affected===null?'—':String(metro.affected);
 countMb.textContent=mb.affected===null?'—':String(mb.affected);
 countIncidents.textContent=metro.affected===null||mb.affected===null?
  '—':String(metro.affected+mb.affected);
 const checked=usable?formatCheckedAt(snapshot):null;
 meta.textContent=usable?
  'Consulta completa del tablero oficial: '+checked+' (hora de CDMX).':
  'Sin datos oficiales recientes verificables. Se muestran accesos a las fuentes originales.';
 status.textContent=usable?
  'Datos consultados del tablero público de incidentes. Una línea con «Servicio Regular» puede estar fuera de su horario de operación.':
  'Estado no confirmado: no interpretamos el silencio del servidor como servicio regular.';
 notes.textContent=usable?
  'Última consulta del archivo: '+checked+'. No es la hora de un incidente ni una confirmación de actividad en vivo.':
  'Esta sección necesita una consulta completa del tablero oficial de Metro y Metrobús dentro de los últimos 90 minutos.';
}
async function load(){
 if(loading)return;
 loading=true;button.disabled=true;button.textContent='Consultando…';
 const serial=++activeRequest;
 try{
  const resp=await fetch('/transporte/estado.json?v='+Date.now(),{cache:'no-store'});
  if(!resp.ok)throw Error('HTTP '+resp.status);
  const body=await resp.json();
  if(serial!==activeRequest)return;
  snapshot=body;previousCheck=Date.now();render();
 }catch(error){
  if(serial===activeRequest){
   snapshot=null;previousCheck=Date.now();render();
   status.textContent='No pudimos consultar el archivo de transporte. Comprueba los avisos directamente en las páginas oficiales.';
  }
 }finally{
  if(serial===activeRequest){loading=false;button.disabled=false;button.textContent='Revisar datos publicados';}
 }
}
root.querySelectorAll('[data-transport-filter]').forEach(tab=>{
 tab.addEventListener('click',()=>{
  choice=tab.dataset.transportFilter;
  if(choice!=='all'&&!allowedSystem(choice))choice='all';
  for(const other of root.querySelectorAll('[data-transport-filter]')){
   const active=other===tab;
   other.setAttribute('aria-pressed',String(active));
   other.classList.toggle('active',active);
  }
  render();
 });
});
button.addEventListener('click',load);
document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState==='visible'){
  if(Date.now()-previousCheck>10*60*1000)void load();
  else if(snapshot&&!isFresh(snapshot))render();
 }
});
render();void load();
})();