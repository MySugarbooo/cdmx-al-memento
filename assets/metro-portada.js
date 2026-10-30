/* CDMX AL MEMENTO · Resumen del Metro para la portada.
   Reutiliza el origen de /movilidad/ y nunca inventa afluencia o incidentes. */
(()=>{'use strict';
const card=document.getElementById('neo-metro-card');
if(!card)return;
const lines=['1','2','3','4','5','6','7','8','9','12','A','B'];
const allMetro=new Set(lines);
const mbLines=['1','2','3','4','5','6','7'];
const ageLimit=90*60*1000;
const elems={
 summary:document.getElementById('neo-metro-overview-title'),
 stamp:document.getElementById('neo-metro-checked'),
 crowd:document.getElementById('neo-metro-crowd'),
 incidents:document.getElementById('neo-metro-incidents'),
 regular:document.getElementById('neo-metro-regular'),
 unknown:document.getElementById('neo-metro-unverified')
};
const node=(tag,content,cls)=>{
 const el=document.createElement(tag);
 if(content!=null)el.textContent=String(content);
 if(cls)el.className=cls;
 return el;
};
function displayRows(parent,items,kind){
 parent.replaceChildren();
 if(!items.length){
  parent.append(node('p',kind==='crowd'?'No hay medición reciente y verificable de saturación por línea.':
   kind==='incident'?'No hay incidencias confirmadas en la última consulta.':
   'No hay líneas con estado regular verificado recientemente.','neo-metro-empty'));
  return;
 }
 for(const item of items.slice(0,4)){
  const a=node('a',null,'neo-metro-row');
  a.href='/movilidad/#transport-live';
  const badge=node('b','L'+item.line,'neo-metro-badge');
  badge.dataset.line=item.line;
  const detail=node('span',null,'neo-metro-row-text');
  detail.append(node('strong','Línea '+item.line));
  detail.append(node('small',item.detail));
  a.append(badge,detail);
  parent.append(a);
 }
 if(items.length>4)parent.append(node('p','+'+(items.length-4)+' líneas más · Ver detalles en Movilidad','neo-metro-more'));
}
function group(rows,valid){
 const map=new Map(lines.map(line=>[line,[]]));
 if(!valid)return map;
 for(const entry of rows){
  if(map.has(String(entry.linea)))map.get(String(entry.linea)).push(entry);
 }
 return map;
}
function fresh(data){
 if(!data||data.schema!==1||data.status!=='ok'||!data.operators)return false;
 for(const [system,expected] of [['stc',lines],['mb',mbLines]]){
  const rows=data.operators[system]?.rows;
  if(!Array.isArray(rows)||rows.length<expected.length||rows.length>60)return false;
  if(rows.some(x=>!x||!expected.includes(String(x.linea))||
   typeof x.estado!=='string'||!x.estado.trim()))return false;
  const ids=new Set(rows.map(x=>String(x.linea)));
  if(expected.some(x=>!ids.has(x)))return false;
 }
 const checked=Date.parse(data.checked_at||'');
 const age=Date.now()-checked;
 return Number.isFinite(checked)&&age>=-300000&&age<=ageLimit;
}
function paintUnknown(message){
 elems.summary.textContent='Estado de las líneas: sin verificación reciente';
 elems.stamp.textContent='Consulta no disponible · verifica antes de viajar';
 elems.crowd.replaceChildren(node('p','Afluencia por línea: sin información oficial verificable.','neo-metro-empty'));
 elems.incidents.replaceChildren(node('p','No es posible confirmar afectaciones actuales.','neo-metro-empty'));
 elems.regular.replaceChildren(node('p','No se confirma servicio regular sin datos recientes.','neo-metro-empty'));
 elems.unknown.replaceChildren();
 const head=node('strong','Consulta individual de las 12 líneas','neo-metro-unverified-title');
 const chips=node('div',null,'neo-metro-chips');
 for(const line of lines){
  const badge=node('a','L'+line,'neo-metro-chip');
  badge.href='/movilidad/#transport-live';
  badge.dataset.line=line;badge.title='Consultar Línea '+line;
  chips.append(badge);
 }
 elems.unknown.append(head,chips);
 elems.unknown.hidden=false;
 if(message)console.info('Resumen Metro:',message);
}
function paint(data){
 if(!fresh(data)){paintUnknown('Datos ausentes, incompletos o de más de 90 minutos.');return false}
 const grouped=group(data.operators.stc.rows,true);
 const incidents=[],regular=[],crowd=[];
 for(const line of lines){
  const records=grouped.get(line)||[];
  const issues=records.filter(item=>!item.estado.toLocaleLowerCase('es-MX').startsWith('servicio regular'));
  if(issues.length){
   const detail=issues.map(item=>String(item.estado).trim()).filter(Boolean).join(' · ').slice(0,98);
   incidents.push({line,detail:detail||'Aviso de operación'});
  }else{
   regular.push({line,detail:'Regular según último reporte'});
  }
  const loaded=records.filter(item=>/saturaci[oó]n|alta afluencia|aglomeraci[oó]n|alta demanda/i.test(
   [item.estado,item.informacion_adicional].filter(Boolean).join(' ')));
  if(loaded.length)crowd.push({line,detail:String(loaded[0].estado).slice(0,85)});
 }
 elems.summary.textContent=incidents.length?incidents.length+' líneas con avisos publicados':'Sin incidencias en el último tablero consultado';
 elems.stamp.textContent='Consulta del '+new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'short',timeStyle:'short'}).format(new Date(data.checked_at))+' (CDMX)';
 if(crowd.length)displayRows(elems.crowd,crowd,'crowd');
 else elems.crowd.replaceChildren(node('p','Sin reporte oficial de saturación por línea. No equivale a baja afluencia.','neo-metro-empty'));
 displayRows(elems.incidents,incidents,'incident');
 displayRows(elems.regular,regular,'regular');
 elems.unknown.hidden=true;
 return true;
}
async function getJSON(url,signal){
 const resp=await fetch(url,{cache:'no-store',signal});
 if(!resp.ok)throw new Error('HTTP '+resp.status);
 return resp.json();
}
let lastCheck=0,busy=false;
async function refresh(){
 if(busy)return;
 busy=true;
 const ctrl=new AbortController();
 const timer=setTimeout(()=>ctrl.abort(),8000);
 try{
  let data=null;
  try{
   const fromAPI=await getJSON('/api/estado-transporte?t='+Date.now(),ctrl.signal);
   if(fresh(fromAPI))data=fromAPI;
  }catch(e){/* Pages Functions puede no estar disponible. */}
  if(!data){
   try{data=await getJSON('/transporte/estado.json?t='+Date.now(),ctrl.signal)}
   catch(e){paintUnknown('No se pudo consultar el estado del Metro.');return}
  }
  paint(data);
 }finally{clearTimeout(timer);busy=false;lastCheck=Date.now()}
}
paintUnknown();
void refresh().catch(()=>paintUnknown('Error de consulta.'));
document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState==='visible'){
  if(Date.now()-lastCheck>10*60*1000)void refresh().catch(()=>paintUnknown());
  else if(elems.stamp.textContent.startsWith('Consulta del')){
   // Revalidar la antigüedad tras regresar a la pestaña.
   void refresh().catch(()=>paintUnknown());
  }
 }
});
setInterval(()=>{if(document.visibilityState==='visible')void refresh().catch(()=>paintUnknown())},10*60*1000);
})();