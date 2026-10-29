/* Aire y clima de CDMX · fuentes explícitas, sin datos inventados.
 * Índice general: Aire CDMX; boletines: CAMe; pronósticos: MET Norway.
 * No se deduce el estado de contingencia ni un índice por alcaldía.
 */
(()=>{
'use strict';
const $=id=>document.getElementById(id);
const boroughs=[
 'Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos',
 'Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras',
 'Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'
];
const risk={
 BAJO:'Riesgo bajo informado. Consulta las recomendaciones del índice para las actividades al aire libre.',
 MODERADO:'Riesgo moderado informado. Las personas sensibles deben vigilar síntomas y consultar las recomendaciones oficiales.',
 ALTO:'Riesgo alto informado. Las personas sensibles deben limitar la actividad intensa al aire libre según las recomendaciones oficiales.',
 'MUY ALTO':'Riesgo muy alto informado. Considera reducir actividades al aire libre y sigue las medidas de protección de Aire CDMX.',
 'EXTREMADAMENTE ALTO':'Riesgo extremadamente alto informado. Evita la actividad física intensa al aire libre y consulta las indicaciones oficiales.'
};
const levels={'BUENA':'good','ACEPTABLE':'fair','MALA':'bad','MUY MALA':'very-bad','EXTREMADAMENTE MALA':'extreme'};
const timestamp=new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'});
const currentHour=new Intl.DateTimeFormat('es-MX',{hour:'2-digit',minute:'2-digit',timeZone:'America/Mexico_City'});
const get=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=String(text);if(cls)el.className=cls;return el};
const safeNumber=(value,min,max)=>typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max;
const $air=$('air-index-primary');
if(!$air||!$('air-weather-grid')||!$('air-contingency-list'))return;
let airData=null,airLastCheck=0,airBusy=false;
let camLastCheck=0,camBusy=false;
let weatherBusy=false,weatherLastCheck=0;
const forecast=new Map();
const weatherGrid=$('air-weather-grid'),boroughSelect=$('air-borough');
const preferredKey='cdmx.memento.alcaldia.v1';
let activeBorough='all';
function formatTime(value){
 const time=Date.parse(String(value||''));
 return Number.isFinite(time)?timestamp.format(new Date(time)):'No disponible';
}
function knownAir(data){
 const air=data?.air;
 const sourceTime=Date.parse(air?.reported_at||'');
 const checked=Date.parse(data?.checked_at||'');
 if(data?.schema!==1||data?.status!=='ok'||!air?.official||!levels[air.category]
   ||!risk[air.risk]||!Array.isArray(air.pollutants)||!air.pollutants.length
   ||!Number.isFinite(sourceTime)||!Number.isFinite(checked))return false;
 const now=Date.now();
 return now-sourceTime>=-15*60*1000&&now-sourceTime<=150*60*1000
   &&now-checked>=-15*60*1000&&now-checked<60*60*1000;
}
function showAir(){
 const value=$('air-index-value'),riskLabel=$('air-index-risk'),pollution=$('air-index-pollutant');
 const reported=$('air-index-reported'),checked=$('air-index-checked');
 const status=$('air-index-status'),advice=$('air-index-recommendation');
 const good=knownAir(airData);
 $air.dataset.level=good?levels[airData.air.category]:'unknown';
 value.textContent=good?airData.air.category[0]+airData.air.category.slice(1).toLocaleLowerCase('es-MX'):'Sin verificación reciente';
 riskLabel.textContent=good?'Riesgo a la salud: '+airData.air.risk:'Riesgo no confirmado';
 pollution.textContent=good?airData.air.pollutants.join(', '):'—';
 reported.textContent=good?formatTime(airData.air.reported_at):'—';
 checked.textContent=good?formatTime(airData.checked_at):'—';
 status.textContent=good?
  'Nivel general tomado del Índice AIRE Y SALUD oficial de CDMX. No es una medición por alcaldía.':
  'No fue posible confirmar un reporte oficial reciente. Consulta directamente Aire CDMX.';
 advice.textContent=good?risk[airData.air.risk]:
  'No asignamos un color a datos que no pudimos verificar. Consulta las recomendaciones del Índice AIRE Y SALUD en la fuente oficial.';
}
async function fetchJSON(url,ms=9000){
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),ms);
 try{
  const response=await fetch(url,{cache:'no-store',signal:ctrl.signal,headers:{Accept:'application/json'}});
  if(!response.ok)throw Error('HTTP '+response.status);
  return await response.json();
 }finally{clearTimeout(timer)}
}
async function loadAir(){
 if(airBusy)return;
 airBusy=true;
 const button=$('air-refresh');button.disabled=true;
 $('air-index-status').textContent='Consultando Índice AIRE Y SALUD…';
 try{
  const data=await fetchJSON('/api/aire?refresh='+Date.now(),14000);
  airData=knownAir(data)?data:null;
 }catch{airData=null}
 finally{airBusy=false;airLastCheck=Date.now();button.disabled=false;showAir()}
}
$('air-refresh').addEventListener('click',loadAir);
function validForecast(data,name){
 const time=Date.parse(data?.forecast_for||'');
 return data?.alcaldia===name&&data?.source==='MET Norway'&&data.estimated===true
  &&safeNumber(data.temperature_c,-40,55)&&Number.isFinite(time)
  &&Date.now()-time<3*60*60*1000&&time-Date.now()<7*60*60*1000;
}
function drawWeather(){
 const choice=boroughSelect.value;
 weatherGrid.replaceChildren();
 const show=choice==='all'?boroughs:boroughs.filter(name=>name===choice);
 let ready=0,errors=0;
 for(const name of show){
  const data=forecast.get(name);
  const valid=validForecast(data,name);
  const card=get('article',undefined,'air-weather-card');
  card.dataset.selected=String(choice===name);
  card.append(get('h3',name));
  if(valid){
   ready++;
   const temp=get('div',undefined,'air-weather-line');
   temp.append(get('span',typeof data.icon==='string'?data.icon:'🌤️','air-weather-icon'));
   temp.append(get('strong',Math.round(data.temperature_c)+' °C','air-weather-temp'));
   card.append(temp);
   card.append(get('p',String(data.description||'Pronóstico variable').slice(0,110),'air-weather-description'));
   const details=get('div',undefined,'air-weather-details');
   if(safeNumber(data.humidity_pct,0,100))details.append(get('span','Humedad estimada: '+Math.round(data.humidity_pct)+' %'));
   if(safeNumber(data.wind_kmh,0,360))details.append(get('span','Viento estimado: '+data.wind_kmh+' km/h'));
   if(safeNumber(data.precipitation_mm,0,1000)&&[1,6].includes(data.precipitation_window_hours)){
    details.append(get('span','Lluvia estimada · próximas '+data.precipitation_window_hours+' h: '+data.precipitation_mm.toFixed(1)+' mm'));
   }else details.append(get('span','Cantidad de lluvia: no disponible'));
   card.append(details);
   card.append(get('small','Hora del pronóstico: '+formatTime(data.forecast_for)+' · MET Norway'));
  }else{
   errors++;
   card.append(get('p','Pronóstico no disponible o desactualizado.','air-weather-description'));
   card.append(get('small','No se muestran temperaturas estimadas sin fecha y fuente.'));
  }
  const link=get('a','Noticias de '+name+' ↗','air-borough-link');
  link.href='/alcaldias/?alcaldia='+encodeURIComponent(name)+'#noticias-alcaldia';
  card.append(link);weatherGrid.append(card);
 }
 $('air-weather-update').textContent=weatherBusy?
  'Consultando pronósticos · '+ready+' disponible(s) de '+show.length+' visible(s)…':
  ready+' pronóstico(s) disponible(s) de '+show.length+' alcaldía(s) visible(s).'+
  (errors?' Hay datos no disponibles.':'');
}
function initWeather(){
 const all=boroughSelect.querySelector('option');
 for(const name of boroughs){
  const option=get('option',name);option.value=name;boroughSelect.append(option);
 }
 try{
  const choice=localStorage.getItem(preferredKey);
  if(boroughs.includes(choice))boroughSelect.value=choice;
 }catch{}
 activeBorough=boroughSelect.value;drawWeather();
}
boroughSelect.addEventListener('change',()=>{
 activeBorough=boroughSelect.value;
 if(boroughs.includes(activeBorough)){
  try{localStorage.setItem(preferredKey,activeBorough)}catch{}
  window.dispatchEvent(new CustomEvent('cdmx:borough-changed',{detail:{borough:activeBorough}}));
 }
 drawWeather();
});
window.addEventListener('cdmx:borough-changed',event=>{
 const name=event.detail?.borough;
 if(boroughs.includes(name)&&boroughSelect.value!==name){
  boroughSelect.value=name;activeBorough=name;drawWeather();
 }
});
async function loadWeather(){
 if(weatherBusy)return;
 weatherBusy=true;$('air-weather-refresh').disabled=true;
 $('air-weather-update').textContent='Consultando modelos meteorológicos…';
 const queue=boroughs.slice();
 async function worker(){
  while(queue.length){
   if(document.visibilityState==='hidden')return;
   const name=queue.shift();
   try{
    const data=await fetchJSON('/api/clima?alcaldia='+encodeURIComponent(name),10500);
    if(validForecast(data,name))forecast.set(name,data);
    else forecast.delete(name);
   }catch{forecast.delete(name)}
   drawWeather();
  }
 }
 try{await Promise.all([worker(),worker(),worker()])}
 finally{
  weatherBusy=false;weatherLastCheck=Date.now();
  $('air-weather-refresh').disabled=false;drawWeather();
 }
}
$('air-weather-refresh').addEventListener('click',loadWeather);
const actionNames={activacion:'Activación',suspension:'Suspensión',seguimiento:'Seguimiento'};
async function loadCAMe(){
 if(camBusy)return;
 camBusy=true;
 const list=$('air-contingency-list'),status=$('air-contingency-status');
 status.textContent='Consultando archivo de comunicados CAMe…';
 try{
  const data=await fetchJSON('/api/contingencias?refresh='+Date.now(),12000);
  if(data?.schema!==1||data?.status!=='ok'||!Array.isArray(data.advisories))throw Error('Sin archivo oficial');
  list.replaceChildren();
  for(const item of data.advisories.slice(0,5)){
   if(!actionNames[item.action]||!/^\d{4}-\d{2}-\d{2}$/.test(item.date)||typeof item.title!=='string')continue;
   const card=get('article',undefined,'air-advisory');
   card.append(get('span','Comunicado histórico · '+actionNames[item.action],'air-advisory-tag'));
   card.append(get('h3',item.title.slice(0,240)));
   card.append(get('p','Publicado: '+item.date+' · CAMe. Este comunicado no acredita por sí solo que la medida siga vigente.'));
   const link=get('a','Leer comunicado en CAMe ↗');
   link.href=item.url?.startsWith('https://www.gob.mx/comisionambiental/')?item.url:
    'https://www.gob.mx/comisionambiental/es/archivo/prensa';
   link.target='_blank';link.rel='noopener noreferrer';card.append(link);list.append(card);
  }
  if(!list.children.length)list.append(get('p','No hay avisos de contingencia en el archivo consultado. Confirma siempre con la CAMe.','air-empty'));
  status.textContent='Comunicados consultados: '+formatTime(data.checked_at)+' · Archivo histórico. Estado vigente: no verificado.';
 }catch{
  list.replaceChildren();
  list.append(get('p','No se pudo consultar el archivo de comunicados oficiales. La situación vigente no está confirmada; abre directamente la CAMe.','air-empty'));
  status.textContent='Avisos oficiales no disponibles en este momento.';
 }finally{camBusy=false;camLastCheck=Date.now()}
}
function refreshStale(){
 if(document.visibilityState!=='visible')return;
 if(Date.now()-airLastCheck>12*60*1000)void loadAir();
 else if(airData&&!knownAir(airData))showAir();
 if(Date.now()-weatherLastCheck>35*60*1000)void loadWeather();
 else drawWeather();
 if(Date.now()-camLastCheck>35*60*1000)void loadCAMe();
}
document.addEventListener('visibilitychange',refreshStale);
setInterval(refreshStale,5*60*1000);
initWeather();
showAir();
void Promise.all([loadAir(),loadWeather(),loadCAMe()]);
})();