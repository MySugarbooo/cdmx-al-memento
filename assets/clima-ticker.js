'use strict';
/* Franja meteorológica para las 16 alcaldías.
   Siempre inicia con Cuauhtémoc y recorre las demás en orden aleatorio.
   Pronósticos de MET Norway: nunca se inventa la temperatura.
   La alcaldía se elige en la sección «Mi alcaldía», no en la tira.
   La cinta siempre comienza en el centro de CDMX. */
(()=>{
 const track=document.getElementById('weather-ribbon-track');
 const reader=document.getElementById('weather-screen-reader');
 if(!track)return;
 // Fecha local fija a la derecha: no depende de la conexión meteorológica.
 const dateBadge=document.createElement('time');
 dateBadge.className='weather-ribbon__date';
 dateBadge.id='weather-current-date';
 const weekday=document.createElement('span');
 weekday.className='weather-date__weekday';
 const fullDate=document.createElement('span');
 fullDate.className='weather-date__long';
 const shortDate=document.createElement('span');
 shortDate.className='weather-date__short';
 dateBadge.append(weekday,fullDate,shortDate);
 const bar=document.getElementById('weather-ribbon');
 if(bar)bar.append(dateBadge);
 function refreshDate(){
  const now=new Date();
  const zone='America/Mexico_City';
  const format=options=>new Intl.DateTimeFormat('es-MX',{timeZone:zone,...options}).format(now);
  const day=format({weekday:'long'});
  weekday.textContent='📅 '+day[0].toUpperCase()+day.slice(1);
  fullDate.textContent=format({day:'numeric',month:'long',year:'numeric'});
  shortDate.textContent=format({day:'numeric',month:'short',year:'numeric'});
  const parts=new Intl.DateTimeFormat('en-US',{timeZone:zone,day:'2-digit',month:'2-digit',year:'numeric'}).formatToParts(now);
  const get=t=>parts.find(x=>x.type===t)?.value||'';
  dateBadge.dateTime=get('year')+'-'+get('month')+'-'+get('day');
  dateBadge.setAttribute('aria-label','Fecha de hoy en CDMX: '+day+', '+fullDate.textContent);
 }
 refreshDate();
 setInterval(refreshDate,60000);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshDate()});
 const KEY='cdmx.memento.alcaldia.v1';
 const CACHE_KEY='cdmx.memento.clima.cache.v2';
 const CENTER='Cuauhtémoc';
 const CACHE_AGE=40*60*1000; // Reducir peticiones en teléfonos que cambian de página.
 const MAX_STALE=120*60*1000; // Nunca enseñar como reciente un dato viejo.
 const NAMES=[
  'Cuauhtémoc','La Magdalena Contreras','Álvaro Obregón','Azcapotzalco',
  'Benito Juárez','Coyoacán','Cuajimalpa de Morelos','Gustavo A. Madero',
  'Iztacalco','Iztapalapa','Miguel Hidalgo','Milpa Alta','Tláhuac',
  'Tlalpan','Venustiano Carranza','Xochimilco'
 ];
 const safeName=name=>NAMES.includes(name)?name:CENTER;
 const getStored=()=>{
  try{return safeName(localStorage.getItem(KEY))}catch{return CENTER}
 };
 const randomOrder=()=>{
  const rest=NAMES.filter(name=>name!==CENTER);
  // Fisher-Yates, orden nuevo en cada carga; Cuauhtémoc siempre primero.
  for(let i=rest.length-1;i>0;i--){
   const j=Math.floor(Math.random()*(i+1));
   [rest[i],rest[j]]=[rest[j],rest[i]];
  }
  return [CENTER,...rest];
 };
 const order=randomOrder();
 const cache=new Map();
 function validData(data,name){
  const temp=data?.temperature_c;
  return data&&data.alcaldia===name&&data.source==='MET Norway'&&
   typeof temp==='number'&&Number.isFinite(temp)&&temp>=-40&&temp<=55;
 }
 function loadCache(){
  try{
   const entries=JSON.parse(localStorage.getItem(CACHE_KEY)||'{}');
   if(!entries||typeof entries!=='object')return;
   for(const name of NAMES){
    const item=entries[name];
    if(item&&Number.isFinite(item.at)&&Date.now()-item.at<MAX_STALE&&validData(item.data,name)){
     cache.set(name,item);
    }
   }
  }catch{/* El widget funciona incluso con almacenamiento bloqueado. */}
 }
 function saveCache(){
  try{
   const entries={};
   for(const [name,value] of cache)entries[name]=value;
   localStorage.setItem(CACHE_KEY,JSON.stringify(entries));
  }catch{/* Bloqueos de almacenamiento no impiden mostrar los datos. */}
 }
 function pick(name){
  const item=cache.get(name);
  return item&&Date.now()-item.at<MAX_STALE?item:null;
 }
 const original=document.createElement('div');
 original.className='weather-ribbon__set';
 original.dataset.weatherGroup='1';
 const textNodes=new Map();
 function chip(name){
  const chip=document.createElement('span');
  chip.className='weather-chip weather-chip--borough';
  chip.dataset.weatherBorough=name;
  chip.textContent='📍 '+name+' · consultando…';
  return chip;
 }
 for(const name of order){
  const node=chip(name);
  textNodes.set(name,node);
  original.append(node);
 }
 const source=document.createElement('a');
 source.className='weather-chip weather-chip--credit';
 source.href='https://api.met.no/';
 source.target='_blank';
 source.rel='noopener noreferrer';
 source.textContent='✦ Pronósticos: MET Norway ↗';
 original.append(source);
 const duplicate=original.cloneNode(true);
 duplicate.dataset.weatherGroup='2';
 duplicate.setAttribute('aria-hidden','true');
 duplicate.querySelectorAll('a').forEach(a=>a.tabIndex=-1);
 track.replaceChildren(original,duplicate);
 const copies=new Map();
 for(const node of duplicate.querySelectorAll('[data-weather-borough]')){
  copies.set(node.dataset.weatherBorough,node);
 }
 let selected=getStored();
 function highlightSelected(){
  for(const [name,node] of textNodes){
   node.classList.toggle('weather-chip--selected',name===selected);
   copies.get(name)?.classList.toggle('weather-chip--selected',name===selected);
  }
 }
 function renderOne(name){
  const item=pick(name);
  let txt='📍 '+name+' · consultando…';
  if(item){
   const data=item.data;
   const temp=Math.round(data.temperature_c)+'°C';
   const symbol=typeof data.icon==='string'?data.icon:'🌤️';
   const cond=typeof data.description==='string'?data.description:'Pronóstico variable';
   txt=symbol+' '+name+' · '+temp+' · '+cond;
   if(Date.now()-item.at>CACHE_AGE)txt+=' (dato anterior)';
  }
  textNodes.get(name).textContent=txt;
  copies.get(name).textContent=txt;
 }
 let geometryJob=0;
 function alignSpeed(){
  if(geometryJob)return;
  geometryJob=requestAnimationFrame(()=>{
   geometryJob=0;
   // Velocidad constante en píxeles/segundo: el texto sigue siendo legible,
   // aunque el carrusel contenga muchas alcaldías, también en móvil.
   const width=original.scrollWidth;
   if(width>0){
    const speed=window.innerWidth<600?78:88;
    track.style.setProperty('--weather-duration',Math.max(18,Math.min(110,width/speed)).toFixed(1)+'s');
   }
  });
 }
 function render(name){
  renderOne(name);highlightSelected();alignSpeed();
 }
 function updateReader(){
  const c=pick(CENTER);
  if(reader){
   reader.textContent=c?
    'Clima estimado en Cuauhtémoc: '+Math.round(c.data.temperature_c)+
      ' grados. La franja recorre las dieciséis alcaldías en orden aleatorio; fuente MET Norway.':
    'Clima estimado de las dieciséis alcaldías: consultando Cuauhtémoc primero.';
  }
 }
 function setSelected(name){
  selected=safeName(name);
  highlightSelected();
 }
 // La barra es únicamente informativa. El selector de alcaldía continúa
 // disponible en "CDMX cerca de ti", no dentro del carrusel estrecho.
 window.addEventListener('cdmx:borough-changed',event=>{
  if(event.detail?.borough)setSelected(event.detail.borough);
 });
 window.addEventListener('storage',event=>{
  if(event.key===KEY)setSelected(getStored());
 });
 loadCache();
 for(const name of order)renderOne(name);
 highlightSelected();
 updateReader();
 alignSpeed();
 // Evitar perder todos los datos en conexiones móviles intermitentes.
 const inFlight=new Map();
 async function loadOne(name,force=false){
  const old=pick(name);
  if(old&&Date.now()-old.at<CACHE_AGE&&!force)return;
  if(inFlight.has(name))return inFlight.get(name);
  const promise=(async()=>{
   const controller=new AbortController();
   const timer=setTimeout(()=>controller.abort(),9000);
   try{
    const response=await fetch('/api/clima?alcaldia='+encodeURIComponent(name),{
     headers:{Accept:'application/json'},signal:controller.signal
    });
    if(!response.ok)throw Error('Servicio no disponible');
    const data=await response.json();
    if(!validData(data,name))throw Error('Datos incompletos');
    cache.set(name,{at:Date.now(),data});
    saveCache();
    render(name);
    if(name===CENTER)updateReader();
   }catch{
    // No sustituir cifras válidas de caché por valores inventados.
    const item=pick(name);
    if(!item){
     const text='☁️ '+name+' · sin datos por ahora';
     textNodes.get(name).textContent=text;
     copies.get(name).textContent=text;
     alignSpeed();
    }
    if(name===CENTER){
     if(reader)reader.textContent='Pronóstico no disponible en este momento. No se muestran datos sin verificar.';
    }
   }finally{
    clearTimeout(timer);
    inFlight.delete(name);
   }
  })();
  inFlight.set(name,promise);
  return promise;
 }
 let refreshing=false;
 async function refreshAll(){
  if(refreshing)return;
  refreshing=true;
  try{
   // En móvil primero el centro, después solo tres consultas paralelas.
   await loadOne(CENTER);
   const queue=order.slice(1);
   async function worker(){
    while(queue.length){
     if(document.visibilityState==='hidden')return;
     const name=queue.shift();
     await loadOne(name);
    }
   }
   await Promise.all([worker(),worker(),worker()]);
  }finally{refreshing=false;}
 }
 refreshAll();
 window.addEventListener('resize',alignSpeed,{passive:true});
 document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState==='visible'){for(const name of order)renderOne(name);refreshAll();}
 });
 window.setInterval(()=>{if(document.visibilityState==='visible')refreshAll()},30*60*1000);
})();
