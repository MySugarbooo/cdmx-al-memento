'use strict';
/* Clima estimado por alcaldía, con atribución MET Norway.
   No usa geolocalización ni datos meteorológicos inventados. */
(()=>{
 const ribbon=document.getElementById('weather-ribbon');
 const track=document.getElementById('weather-ribbon-track');
 const select=document.getElementById('weather-borough');
 const reader=document.getElementById('weather-screen-reader');
 if(!ribbon||!track||!select)return;
 const KEY='cdmx.memento.alcaldia.v1';
 const NAMES=[
  'La Magdalena Contreras','Álvaro Obregón','Azcapotzalco','Benito Juárez',
  'Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero',
  'Iztacalco','Iztapalapa','Miguel Hidalgo','Milpa Alta','Tláhuac',
  'Tlalpan','Venustiano Carranza','Xochimilco'
 ];
 const DEFAULT='Cuauhtémoc';
 const safeName=name=>NAMES.includes(name)?name:DEFAULT;
 const savedName=()=>{
  try{return safeName(localStorage.getItem(KEY))}catch{return DEFAULT}
 };
 const writeName=name=>{
  try{localStorage.setItem(KEY,name)}catch{/* preferencias opcionales */}
 };
 function chip(text,extraClass=''){
  const node=document.createElement('span');
  node.className='weather-chip'+(extraClass?' '+extraClass:'');
  node.textContent=text;
  return node;
 }
 // Dos grupos idénticos producen un bucle perfecto sin vacíos al terminar.
 // El segundo se oculta a tecnologías de asistencia y no contiene controles.
 function show(parts,screenText){
  const originals=document.createElement('div');
  originals.className='weather-ribbon__set';
  originals.dataset.weatherGroup='1';
  for(const [text,extraClass] of parts)originals.append(chip(text,extraClass||''));
  const copy=originals.cloneNode(true);
  copy.dataset.weatherGroup='2';
  copy.setAttribute('aria-hidden','true');
  track.replaceChildren(originals,copy);
  if(reader)reader.textContent=screenText;
 }
 let currentName=savedName();
 for(const name of NAMES){
  const option=document.createElement('option');
  option.value=name;option.textContent=name;select.append(option);
 }
 select.value=currentName;
 let currentRequest=null,requestId=0,lastFetched=0;
 function hourMX(iso){
  const date=new Date(iso);
  if(!Number.isFinite(date.getTime()))return '';
  return new Intl.DateTimeFormat('es-MX',{
   timeZone:'America/Mexico_City',hour:'2-digit',minute:'2-digit',hour12:false
  }).format(date);
 }
 function renderPending(name){
  show([
   ['🌸 CLIMA · CDMX','weather-chip--title'],
   ['📍 '+name,'weather-chip--place'],
   ['☁️ Consultando el pronóstico…','']
  ],'Consultando el pronóstico para '+name+'.');
 }
 function renderUnavailable(name){
  show([
   ['🌸 CLIMA · CDMX','weather-chip--title'],
   ['📍 '+name,'weather-chip--place'],
   ['☁️ Clima no disponible por ahora',''],
   ['♡ Visita de nuevo en unos minutos','']
  ],'Pronóstico no disponible para '+name+'. No se muestran datos sin verificar.');
 }
 function renderWeather(data){
  const name=currentName;
  const temperature=Number(data.temperature_c);
  if(!Number.isFinite(temperature))throw Error('Pronóstico sin temperatura');
  const temperatureText=Math.round(temperature)+' °C';
  const parts=[
   ['🌸 CLIMA ESTIMADO · CDMX','weather-chip--title'],
   ['📍 '+name,'weather-chip--place'],
   [(typeof data.icon==='string'?data.icon:'🌤️')+' '+temperatureText,'weather-chip--temp'],
   ['💗 '+String(data.description||'Pronóstico variable'),''],
  ];
  if(data.humidity_pct!==null&&Number.isFinite(Number(data.humidity_pct))){
   parts.push(['💧 Humedad '+Math.round(Number(data.humidity_pct))+' %','']);
  }
  if(data.wind_kmh!==null&&Number.isFinite(Number(data.wind_kmh))){
   parts.push(['🍃 Viento '+Math.round(Number(data.wind_kmh))+' km/h','']);
  }
  const hour=hourMX(data.forecast_for);
  if(hour)parts.push(['🕒 Pronóstico para las '+hour+' h','']);
  parts.push(['✦ Fuente: MET Norway','weather-chip--credit']);
  show(parts,'Pronóstico estimado para '+name+': '+temperatureText+', '+String(data.description||'')+
   '. Datos de MET Norway; no es una medición de una estación en tiempo real.');
 }
 async function loadWeather(force=false){
  const name=currentName;
  if(!force&&Date.now()-lastFetched<14*60*1000)return;
  const id=++requestId;
  currentRequest?.abort();
  const controller=new AbortController();
  currentRequest=controller;
  renderPending(name);
  try{
   const response=await fetch('/api/clima?alcaldia='+encodeURIComponent(name),{
    signal:controller.signal,headers:{Accept:'application/json'}
   });
   if(!response.ok)throw Error('Error de consulta');
   const data=await response.json();
   if(id!==requestId)return;
   if(data.alcaldia!==name||!Number.isFinite(Number(data.temperature_c)))throw Error('Información incompleta');
   renderWeather(data);
   lastFetched=Date.now();
  }catch(error){
   if(id===requestId&&error.name!=='AbortError')renderUnavailable(name);
  }
 }
 function changeBorough(name,emit=false){
  const next=safeName(name);
  if(next===currentName){select.value=next;return;}
  currentName=next;
  select.value=next;
  lastFetched=0;
  if(emit){
   writeName(next);
   window.dispatchEvent(new CustomEvent('cdmx:borough-changed',{detail:{borough:next}}));
  }
  loadWeather(true);
 }
 select.addEventListener('change',()=>changeBorough(select.value,true));
 window.addEventListener('cdmx:borough-changed',event=>{
  if(event.detail?.borough)changeBorough(event.detail.borough);
 });
 window.addEventListener('storage',event=>{
  if(event.key===KEY)changeBorough(savedName());
 });
 document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState==='visible'&&Date.now()-lastFetched>14*60*1000)loadWeather(true);
 });
 window.setInterval(()=>{if(document.visibilityState==='visible')loadWeather(true)},15*60*1000);
 renderPending(currentName);
 loadWeather(true);
})();
