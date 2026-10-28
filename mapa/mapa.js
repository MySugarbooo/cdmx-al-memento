'use strict';
/* Mapa CDMX: límites reales de las 16 alcaldías (Atlas SIGIRPC/INEGI). */
(() => {
 const $=id=>document.getElementById(id);
 const status=$('mapa-status'),capas=$('capas'),lugares=$('mapa-lugares'),buscar=$('mapa-buscar');
 const listaAlcaldias=$('mapa-alcaldias-lista'),infoAlcaldia=$('mapa-alcaldia-info');
 if(!status||!capas||!lugares)return;
 const dataUrl='/mapa/alcaldias.geojson?v=20261028';
 const shortNames={
  'Álvaro Obregón':'Álvaro O.','La Magdalena Contreras':'Magdalena C.',
  'Cuajimalpa de Morelos':'Cuajimalpa','Gustavo A. Madero':'G. A. Madero',
  'Venustiano Carranza':'Venustiano C.','Benito Juárez':'Benito Juárez'
 };
 const places=[
  {id:'los-dinamos',type:'natural',name:'Parque Los Dinamos',kind:'naturaleza',emoji:'🌲',lat:19.2959,lng:-99.2555,area:'La Magdalena Contreras · Río Magdalena',info:'Bosque de oyamel y encino junto al Río Magdalena, con senderos y cascadas. Marcador de referencia, no acceso único.'},
  {id:'desierto-leones',type:'natural',name:'Desierto de los Leones',kind:'naturaleza',emoji:'🌳',lat:19.295,lng:-99.312778,area:'Cuajimalpa y Álvaro Obregón',info:'Parque nacional de bosque templado y senderos. Punto aproximado del área protegida.'},
  {id:'bosque-tlalpan',type:'natural',name:'Bosque de Tlalpan',kind:'naturaleza',emoji:'🌿',lat:19.291111,lng:-99.199167,area:'Tlalpan',info:'Área natural protegida con senderos y vegetación del Pedregal. Marcador de referencia.'},
  {id:'cumbres-ajusco',type:'natural',name:'Cumbres del Ajusco',kind:'naturaleza',emoji:'⛰️',lat:19.21,lng:-99.259444,area:'Tlalpan · Sierra del Ajusco',info:'Parque nacional montañoso con bosques de altura y panorámicas de la capital. Marcador aproximado.'},
  {id:'fuentes-brotantes',type:'natural',name:'Fuentes Brotantes de Tlalpan',kind:'naturaleza',emoji:'💧',lat:19.285833,lng:-99.179444,area:'Tlalpan',info:'Parque nacional con manantiales y espacios arbolados. Marcador de referencia.'},
  {id:'cerro-estrella',type:'natural',name:'Cerro de la Estrella',kind:'naturaleza',emoji:'🌄',lat:19.338056,lng:-99.091389,area:'Iztapalapa',info:'Cerro con vegetación de matorral y valor ecológico y cultural. Punto de referencia.'},
  {id:'ejidos-xochimilco',type:'natural',name:'Zona de conservación de Xochimilco',kind:'naturaleza',emoji:'🪷',lat:19.278056,lng:-99.077778,area:'Xochimilco y San Gregorio Atlapulco',info:'Zona de conservación ecológica en el paisaje lacustre y chinampero. Pin orientativo, no entrada.'},
  {id:'sierra-guadalupe',type:'natural',name:'Sierra de Guadalupe',kind:'naturaleza',emoji:'🌵',lat:19.566111,lng:-99.119444,area:'Gustavo A. Madero',info:'Área natural protegida al norte de CDMX. Marcador aproximado del área.'},
  {id:'bosque-chapultepec',type:'natural',name:'Bosque de Chapultepec',kind:'naturaleza',emoji:'🌳',lat:19.4205,lng:-99.1930,area:'Miguel Hidalgo',info:'Parque urbano histórico con museos, lagos y zonas boscosas. Punto representativo, no acceso.'},
  {id:'museo-antropologia',type:'museo',name:'Museo Nacional de Antropología',kind:'museo',emoji:'🏺',lat:19.4260,lng:-99.1864,area:'Chapultepec · Miguel Hidalgo',info:'Museo dedicado a las culturas de México, con colecciones arqueológicas y etnográficas. Comprueba horario en la web oficial.'},
  {id:'museo-frida-kahlo',type:'museo',name:'Museo Frida Kahlo',kind:'museo',emoji:'🎨',lat:19.3550,lng:-99.1625,area:'Del Carmen · Coyoacán',info:'Museo instalado en la Casa Azul, relacionado con la vida y obra de Frida Kahlo. Consulta entradas y horarios oficiales.'},
  {id:'museo-memoria',type:'museo',name:'Museo Memoria y Tolerancia',kind:'museo',emoji:'🕊️',lat:19.4336,lng:-99.1455,area:'Centro · Cuauhtémoc',info:'Museo enfocado en derechos humanos, memoria histórica y cultura de paz.'},
  {id:'templo-mayor',type:'museo',name:'Zona Arqueológica del Templo Mayor',kind:'museo',emoji:'🏺',lat:19.4344,lng:-99.1323,area:'Centro Histórico · Cuauhtémoc',info:'Sitio arqueológico del antiguo recinto sagrado mexica. Consulta horarios y acceso con el INAH.'},
  {id:'cuicuilco',type:'museo',name:'Zona Arqueológica de Cuicuilco',kind:'museo',emoji:'🏛️',lat:19.3016,lng:-99.1837,area:'Tlalpan',info:'Zona arqueológica al sur de la ciudad, conocida por su basamento circular. Comprueba acceso oficial.'},
 ];
 function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function art(kind){
  const line='#50334a',peach='#ffc7a2',pink='#ec80a9',cream='#ffecc6',blue='#85bcd2';
  const pieces={
   palacio:'<path d="M9 37H55V56H9Z" fill="'+cream+'"/><path d="M13 34Q32 19 51 34V38H13Z" fill="'+pink+'"/><path d="M24 31Q32 5 40 31" fill="'+blue+'"/><path d="M21 45h22M19 55V39M45 55V39M30 55V42h6v13" stroke="'+line+'" stroke-width="3" fill="none"/>',
   arco:'<path d="M12 22L18 17H46L52 22V55H43V34H21V55H12Z" fill="'+peach+'"/><path d="M21 34v-9h22v9M14 21h36M28 17V12h8v5" fill="none" stroke="'+line+'" stroke-width="3"/><rect x="8" y="53" width="48" height="4" rx="1" fill="'+pink+'"/>',
   'palacio-nacional':'<path d="M5 32H59V55H5Z" fill="'+peach+'"/><path d="M5 32h54v5H5z" fill="'+pink+'"/><path d="M26 55V42q6-6 12 0v13" fill="'+cream+'"/><path d="M11 42h7v10h-7zm35 0h7v10h-7z" fill="'+blue+'"/><path d="M32 31V11m0 0 10 4-10 6" stroke="'+line+'" stroke-width="2" fill="none"/><path d="M32 11l4 2-4 2" stroke="#44a269" stroke-width="4"/>',
   angel:'<path d="M25 55h14l-3-29h-8Z" fill="'+cream+'"/><path d="M22 24Q8 5 10 28Q21 28 29 20Q43 4 52 22Q50 29 35 24" fill="'+blue+'"/><circle cx="32" cy="14" r="5" fill="'+peach+'"/><path d="M32 20l-5 8h11z" fill="'+pink+'"/><path d="M16 55h32v3H16Z" fill="'+pink+'"/>',
   castillo:'<path d="M9 31h46v25H9z" fill="'+cream+'"/><path d="M9 31V19h12v12m22 0V19h12v12" fill="'+pink+'"/><path d="M8 19h14M42 19h14M30 55V43q3-4 6 0v12" fill="none" stroke="'+line+'" stroke-width="3"/><path d="M16 38h7v7h-7zm25 0h7v7h-7z" fill="'+blue+'"/>',
   torre:'<path d="M22 10h20l5 46H17z" fill="'+blue+'"/><path d="M19 20h26M18 30h28M17 40h30M16 50h32M26 10V6h12v4" stroke="'+line+'" fill="none" stroke-width="2"/><path d="M26 12v40m12-40v40" stroke="#fff4cf" stroke-width="3"/>',
   basilica:'<path d="M9 36h46v19H9Z" fill="'+cream+'"/><path d="M17 36Q32 8 47 36" fill="'+blue+'"/><path d="M32 13v-7m-5 4h10" stroke="'+line+'" stroke-width="2"/><path d="M27 55V43q5-7 10 0v12" fill="'+pink+'"/><path d="M13 40v15m38-15v15" stroke="'+line+'" stroke-width="2"/>',
   trajineras:'<path d="M7 42H57L49 56H16Z" fill="'+pink+'"/><path d="M17 42V20Q32 6 47 20V42" stroke="'+line+'" stroke-width="3" fill="none"/><path d="M17 24h30M24 18v23m16-23v23" stroke="'+line+'" stroke-width="2"/><path d="M9 60q6-4 12 0t12 0t12 0t12 0" stroke="'+blue+'" stroke-width="3" fill="none"/><circle cx="32" cy="22" r="5" fill="'+peach+'"/>',
   biblioteca:'<rect x="12" y="12" width="40" height="44" rx="2" fill="'+cream+'"/><path d="M12 20h40M12 31h40M12 42h40M24 12v44m16-44v44" fill="none" stroke="'+pink+'" stroke-width="4"/><path d="M19 25l6 5m15-5-7 6m-14 7 6-5m15 4-7-7" stroke="'+line+'" stroke-width="2"/>',
   soumaya:'<path d="M26 8Q45 4 42 20Q39 32 47 52L50 56H17Q10 46 20 31Q29 19 26 8Z" fill="'+blue+'"/><path d="M24 16h16M19 25h22M15 36h30M16 46h31" stroke="'+cream+'" stroke-width="3"/><path d="M26 8Q45 4 42 20Q39 32 47 52L50 56H17Q10 46 20 31Q29 19 26 8Z" fill="none" stroke="'+line+'" stroke-width="2"/>',
   catedral:'<path d="M12 31h40v24H12Z" fill="'+cream+'"/><path d="M10 30V13h12v18M42 31V13h12v18" fill="'+pink+'"/><path d="M16 12V6m-5 4h10M48 12V6m-5 4h10" stroke="'+line+'" stroke-width="2"/><path d="M24 55V42q8-8 16 0v13" fill="'+blue+'"/>',
   naturaleza:'<path d="M31 55V37" stroke="#85563c" stroke-width="6"/><path d="M32 8 13 31h9L9 43h46L42 31h9Z" fill="#6bc9a0" stroke="#2b715c" stroke-width="3"/><path d="M25 24h14M20 35h24" stroke="#e9ffe9" stroke-width="2"/>',
   museo:'<path d="M8 26 32 12 56 26v4H8Z" fill="#dcb4f8"/><path d="M12 50h40v7H12z" fill="#ffdb8b"/><path d="M17 30v20m10-20v20m10-20v20m10-20v20" stroke="#8b699f" stroke-width="5"/>',
   salud:'<rect x="10" y="20" width="44" height="36" rx="4" fill="#c8edf5"/><path d="M27 25h10v8h8v10h-8v8H27v-8h-8V33h8Z" fill="#dd5076"/>'
  };
  const drawing=pieces[kind]||pieces.palacio;
  return '<div class="mapa-pin"><svg viewBox="0 0 64 64" width="64" height="64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M9 8Q32-2 55 8L61 38Q63 56 42 60H22Q2 57 3 38Z" fill="#fff7e9" stroke="'+line+'" stroke-width="3"/><g stroke="'+line+'" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">'+drawing+'</g></svg></div>';
 }
 function placePopup(place){
  return '<div class="mapa-popup"><div class="mapa-type">'+esc(place.area)+'</div><h3>'+esc(place.emoji+' '+place.name)+'</h3><p>'+esc(place.info)+'</p><p><strong>Ilustración representativa, no fotografía.</strong></p></div>';
 }
 function show(message,failed=false){
  status.textContent=message;
  status.toggleAttribute('data-error',failed);
 }
 function checked(type){return Boolean(capas.querySelector('input[value="'+type+'"]')?.checked)}
 function redrawList(filter=''){
  const term=filter.toLocaleLowerCase('es-MX').trim();
  lugares.replaceChildren();
  for(const place of places.filter(p=>(p.name+' '+p.area).toLocaleLowerCase('es-MX').includes(term))){
   const b=document.createElement('button');b.type='button';b.className='mapa-lugar';
   const em=document.createElement('span');em.textContent=place.emoji;
   const name=document.createElement('span');name.textContent=place.name;
   b.append(em,name);b.addEventListener('click',()=>focusPlace(place));lugares.append(b);
  }
  if(!lugares.children.length){const p=document.createElement('p');p.className='muted';p.textContent='No hay museos ni áreas verdes con ese nombre.';lugares.append(p)}
 }
 redrawList();
 buscar?.addEventListener('input',()=>redrawList(buscar.value));
 if(!window.L){
  $('mapa-interactivo').textContent='No fue posible cargar el mapa interactivo. Revisa tu conexión.';
  show('No se pudo cargar la biblioteca del mapa.',true);return;
 }
 const L=window.L;
 const map=L.map('mapa-interactivo',{zoomControl:false,preferCanvas:false,minZoom:9,maxZoom:18})
  .setView([19.33,-99.15],10);
 L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'
 }).addTo(map);
 L.control.zoom({position:'bottomright'}).addTo(map);
 const baseStyle={color:'#fff2fa',weight:1.8,opacity:1,fillColor:'#e879ad',fillOpacity:.17};
 const hoverStyle={color:'#ffffff',weight:4,opacity:1,fillColor:'#fb7fb6',fillOpacity:.4};
 const selectedStyle={color:'#ffffff',weight:4.4,opacity:1,fillColor:'#f44a9d',fillOpacity:.48};
 const regionMap=new Map();
 let active=null,selectedName='',fullBounds=null;
 function urlFor(name){return '/alcaldias/?alcaldia='+encodeURIComponent(name)+'#noticias-alcaldia'}
 function resetHighlight(layer){layer.setStyle(layer===active?selectedStyle:baseStyle)}
 function panel(name){
  if(!infoAlcaldia)return;
  infoAlcaldia.replaceChildren();
  const title=document.createElement('strong');title.textContent=name||'Selecciona una alcaldía';
  const help=document.createElement('span');help.textContent=name?' Consulta sus notas locales o elige otra zona del mapa.':' Pasa el cursor para ver el contorno blanco, o toca una región.';
  infoAlcaldia.append(title,help);
  if(name){
   const a=document.createElement('a');a.href=urlFor(name);a.textContent='Ver noticias de '+name+' ↗';
   infoAlcaldia.append(a);
  }
 }
 panel('');
 function selectRegion(layer,name,focus=false){
  if(active&&active!==layer)resetHighlight(active);
  active=layer;selectedName=name;
  layer.setStyle(selectedStyle);layer.bringToFront();
  panel(name);
  if(focus)map.fitBounds(layer.getBounds(),{padding:[35,35],maxZoom:12,animate:true});
  layer.openPopup();
  for(const button of (listaAlcaldias?.querySelectorAll('button')||[])){
   button.setAttribute('aria-pressed',String(button.dataset.region===name));
  }
 }
 const polygons=L.geoJSON(null,{
  style:()=>({...baseStyle}),
  onEachFeature:(feature,layer)=>{
   const name=String(feature.properties?.nomgeo||'');
   if(!name)return;
   regionMap.set(name,layer);
   const url=urlFor(name);
   layer.bindTooltip(shortNames[name]||name,{permanent:true,direction:'center',className:'alcaldia-tooltip',opacity:.96});
   layer.bindPopup('<div class="mapa-popup mapa-popup-alcaldia"><span class="mapa-type">ALCALDÍA · CDMX</span><h3>'+esc(name)+'</h3><a href="'+url+'">Consultar noticias de esta alcaldía ↗</a></div>',{maxWidth:280});
   layer.on('mouseover',()=>{layer.setStyle(hoverStyle);layer.bringToFront();panel(name)});
   layer.on('mouseout',()=>{resetHighlight(layer);panel(selectedName)});
   layer.on('click',()=>selectRegion(layer,name));
  }
 }).addTo(map);
 const layers={
  naturaleza:L.layerGroup().addTo(map),
  museos:L.layerGroup().addTo(map)
 };
 const markers=new Map();
 for(const place of places){
  const marker=L.marker([place.lat,place.lng],{
   icon:L.divIcon({className:'mapa-pin-wrap',html:art(place.kind),iconSize:[64,70],iconAnchor:[32,65],popupAnchor:[0,-55]}),
   keyboard:true,title:place.name,alt:place.name,riseOnHover:true
  });
  marker.bindPopup(placePopup(place),{maxWidth:270,autoPan:true});
  marker.addTo(place.type==='natural'?layers.naturaleza:layers.museos);
  markers.set(place.id,marker);
 }
 function toggleLayer(type){
  const group=layers[type];if(!group)return;
  if(checked(type))group.addTo(map);else map.removeLayer(group);
 }
 capas.addEventListener('change',event=>toggleLayer(event.target.value));
 function focusPlace(place){
  const type=place.type==='natural'?'naturaleza':'museos';
  if(!checked(type)){
   const el=capas.querySelector('input[value="'+type+'"]');
   if(el){el.checked=true;toggleLayer(type)}
  }
  map.flyTo([place.lat,place.lng],Math.max(13,map.getZoom()),{duration:.7});
  window.setTimeout(()=>markers.get(place.id)?.openPopup(),730);
  $('mapa-interactivo').scrollIntoView({block:'center',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
 }
 function fitCity(){
  if(fullBounds?.isValid())map.fitBounds(fullBounds,{padding:[22,22],maxZoom:11,animate:false});
  else map.setView([19.33,-99.15],10);
 }
 function clearSelection(){
  if(active)resetHighlight(active);
  active=null;selectedName='';panel('');
  for(const b of (listaAlcaldias?.querySelectorAll('button')||[]))b.setAttribute('aria-pressed','false');
 }
 function buildRegionButtons(){
  if(!listaAlcaldias)return;
  listaAlcaldias.replaceChildren();
  for(const name of [...regionMap.keys()].sort((a,b)=>a.localeCompare(b,'es-MX'))){
   const button=document.createElement('button');
   button.type='button';button.dataset.region=name;button.textContent=name;
   button.setAttribute('aria-pressed','false');
   button.addEventListener('click',()=>selectRegion(regionMap.get(name),name,true));
   listaAlcaldias.append(button);
  }
 }
 async function loadRegions(){
  show('Cargando límites de las 16 alcaldías…');
  try{
   const response=await fetch(dataUrl,{cache:'default'});
   if(!response.ok)throw Error('No se pudieron descargar las divisiones');
   const data=await response.json();
   if(data.type!=='FeatureCollection'||data.features?.length!==16)throw Error('Los límites no incluyen 16 alcaldías');
   if(new Set(data.features.map(f=>f.properties?.cvegeo)).size!==16)throw Error('Hay claves de alcaldía duplicadas');
   polygons.addData(data);
   if(regionMap.size!==16)throw Error('No se dibujaron todas las alcaldías');
   fullBounds=polygons.getBounds();
   buildRegionButtons();
   fitCity();
   show('16 alcaldías cargadas · Pasa el cursor para resaltar el contorno blanco.');
  }catch(error){
   console.error('Mapa de alcaldías:',error);
   show('No se pudieron cargar los límites territoriales. Actualiza la página para reintentar.',true);
  }
 }
 $('solo-monumentos')?.addEventListener('click',()=>{
  for(const el of capas.querySelectorAll('input[type="checkbox"]')){
   el.checked=el.value==='naturaleza';toggleLayer(el.value);
  }
 });
 $('todas-capitas')?.addEventListener('click',()=>{
  for(const el of capas.querySelectorAll('input[type="checkbox"]')){
   el.checked=true;toggleLayer(el.value);
  }
  clearSelection();fitCity();
 });
 $('mapa-centrar')?.addEventListener('click',()=>{clearSelection();fitCity()});
 const enlarge=$('mapa-ampliar'),frame=document.querySelector('.mapa-frame');
 function setExpanded(enabled){
  if(!frame||!enlarge)return;
  frame.classList.toggle('mapa-ampliado',enabled);
  document.body.classList.toggle('mapa-expandido',enabled);
  enlarge.textContent=enabled?'✕ Cerrar mapa grande':'⤢ Ver mapa grande';
  enlarge.setAttribute('aria-pressed',String(enabled));
  enlarge.setAttribute('aria-label',enabled?'Cerrar mapa grande':'Ampliar mapa de Ciudad de México');
  window.setTimeout(()=>map.invalidateSize({pan:false}),100);
 }
 enlarge?.addEventListener('click',()=>setExpanded(!frame.classList.contains('mapa-ampliado')));
 document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&frame?.classList.contains('mapa-ampliado'))setExpanded(false);
 });
 loadRegions();
 window.setTimeout(()=>map.invalidateSize({pan:false}),250);
 const named=new URLSearchParams(location.search).get('lugar');
 if(named){const place=places.find(p=>p.id===named);if(place)window.setTimeout(()=>focusPlace(place),800)}
})();
