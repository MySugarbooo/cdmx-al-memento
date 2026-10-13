'use strict';
/* Mapa ilustrado: las rutas se leen del Atlas Público SIGIRPC; no se dibujan recorridos inventados. */
(() => {
 const $=id=>document.getElementById(id);
 const status=$('mapa-status'),capas=$('capas'),lugares=$('mapa-lugares'),buscar=$('mapa-buscar');
 if(!status||!capas||!lugares)return;
 const origin='https://serviciosatlas.sgirpc.cdmx.gob.mx/arcgis/rest/services/AtlasCapasPublicas/Movilidad_Integrada_CDMX/FeatureServer';
 const sources={metro:1,metrobus:3,rtp:5,trolebus:7,ligero:9,cablebus:11,camiones:16};
 const systems={
  metro:{name:'Metro',color:'#df5a99'},
  metrobus:{name:'Metrobús',color:'#9560c5'},
  ligero:{name:'Tren Ligero',color:'#dfa838'},
  cablebus:{name:'Cablebús',color:'#3a9fc6'},
  trolebus:{name:'Trolebús',color:'#168d85'},
  rtp:{name:'RTP',color:'#436add'},
  camiones:{name:'Camiones concesionados',color:'#cc7856'}
 };
 const metroColors={'1':'#e966a1','2':'#2369ba','3':'#afa415','4':'#66ac9d','5':'#e8c500','6':'#e95345','7':'#e67534','8':'#329c6d','9':'#78504a','A':'#a73e9b','B':'#9ba2ad','12':'#bb9a45'};
 const metrobusColors={'1':'#c52d54','2':'#884da8','3':'#478b74','4':'#e6a040','5':'#3874bd','6':'#b4508e','7':'#478b54'};
 const places=[
  {id:'bellas',name:'Palacio de Bellas Artes',kind:'palacio',emoji:'🎭',lat:19.4352,lng:-99.1412,area:'Centro Histórico · Cuauhtémoc',info:'Palacio de mármol y cúpula icónica donde conviven exposiciones, ópera, danza y muralismo.'},
  {id:'revolucion',name:'Monumento a la Revolución',kind:'arco',emoji:'🏛️',lat:19.4364,lng:-99.1546,area:'Tabacalera · Cuauhtémoc',info:'Arcos monumentales y mirador que recuerdan la Revolución mexicana.'},
  {id:'nacional',name:'Palacio Nacional',kind:'palacio-nacional',emoji:'🇲🇽',lat:19.4326,lng:-99.1317,area:'Zócalo · Cuauhtémoc',info:'Histórico edificio frente a la Plaza de la Constitución, sede del Poder Ejecutivo federal.'},
  {id:'angel',name:'Ángel de la Independencia',kind:'angel',emoji:'✨',lat:19.4270,lng:-99.1677,area:'Paseo de la Reforma · Cuauhtémoc',info:'Columna coronada por la Victoria Alada, uno de los símbolos de la ciudad.'},
  {id:'chapultepec',name:'Castillo de Chapultepec',kind:'castillo',emoji:'🏰',lat:19.4205,lng:-99.1819,area:'Bosque de Chapultepec · Miguel Hidalgo',info:'Castillo en lo alto del cerro, hoy sede del Museo Nacional de Historia.'},
  {id:'latino',name:'Torre Latinoamericana',kind:'torre',emoji:'🏙️',lat:19.4339,lng:-99.1408,area:'Centro Histórico · Cuauhtémoc',info:'Rascacielos histórico con mirador sobre el corazón de la capital.'},
  {id:'basilica',name:'Basílica de Guadalupe',kind:'basilica',emoji:'⛪',lat:19.4848,lng:-99.1170,area:'Villa de Guadalupe · Gustavo A. Madero',info:'Conjunto de templos y explanadas, lugar emblemático de peregrinación.'},
  {id:'xochimilco',name:'Embarcadero de Nativitas',kind:'trajineras',emoji:'🛶',lat:19.2546,lng:-99.0996,area:'Xochimilco',info:'Punto de partida de trajineras para recorrer los canales tradicionales.'},
  {id:'unam',name:'Biblioteca Central UNAM',kind:'biblioteca',emoji:'📚',lat:19.3319,lng:-99.1871,area:'Ciudad Universitaria · Coyoacán',info:'Biblioteca reconocida por sus mosaicos monumentales de Juan O’Gorman.'},
  {id:'soumaya',name:'Museo Soumaya',kind:'soumaya',emoji:'🖼️',lat:19.4406,lng:-99.2047,area:'Nuevo Polanco · Miguel Hidalgo',info:'Museo de arte distinguido por su fachada curvada de hexágonos brillantes.'},
  {id:'catedral',name:'Catedral Metropolitana',kind:'catedral',emoji:'⛪',lat:19.4352,lng:-99.1334,area:'Zócalo · Cuauhtémoc',info:'Catedral frente al Zócalo, con dos torres y siglos de historia arquitectónica.'},
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
  {id:'hospital-general',type:'salud',name:'Hospital General de México',kind:'salud',emoji:'🏥',lat:19.4125,lng:-99.1525,area:'Doctores · Cuauhtémoc',info:'Institución de atención médica. Marcador orientativo; no confirma admisión, servicios ni disponibilidad de urgencias.'},
  {id:'hospital-siglo-xxi',type:'salud',name:'Centro Médico Nacional Siglo XXI',kind:'salud',emoji:'🏥',lat:19.4069,lng:-99.1555,area:'Doctores · Cuauhtémoc',info:'Complejo hospitalario del IMSS. Marcador de referencia, no sustituye información de acceso o atención.'},
  {id:'hospital-la-raza',type:'salud',name:'Centro Médico Nacional La Raza',kind:'salud',emoji:'🏥',lat:19.4700,lng:-99.1440,area:'La Raza · Azcapotzalco',info:'Complejo médico del IMSS. Punto aproximado, sin información sobre camas, urgencias o disponibilidad.'}
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
 function routeName(feature,mode){
  const p=feature.properties||{};
  const line=String(p.linea||'').trim();
  const route=String(p.ruta||'').trim();
  return systems[mode].name+(line?' · Línea '+line:'')+(route?' · '+route:'');
 }
 function simpleLine(line){
  const text=String(line||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/\s+/g,' ').trim();
  const tokens=text.match(/(?:^| )L(?:INEA)?\s*([A-B]|12|[1-9])\b/);
  if(tokens)return tokens[1];
  if(/^([A-B]|12|[1-9])$/.test(text))return text;
  return '';
 }
 function colorFor(mode,feature){
  const raw=feature?.properties?.linea;
  const id=simpleLine(raw);
  return (mode==='metro'&&metroColors[id])||(mode==='metrobus'&&metrobusColors[id])||systems[mode].color;
 }
 function styleFor(mode,feature){
  return {color:colorFor(mode,feature),weight:mode==='metro'?5:mode==='metrobus'?4.6:3.5,opacity:.92,dashArray:mode==='cablebus'?'8 6':mode==='rtp'||mode==='camiones'?'7 5':undefined,lineCap:'round',lineJoin:'round',className:'ruta-'+mode};
 }
 const state=new Map();
 const checked=mode=>Boolean(capas.querySelector('input[value="'+mode+'"]')?.checked);
 function show(message,failed=false){status.textContent=message;failed?status.setAttribute('data-error',''):status.removeAttribute('data-error')}
 function redrawList(filter=''){
  const term=filter.toLocaleLowerCase('es-MX').trim();
  lugares.replaceChildren();
  for(const place of places.filter(x=>(x.name+' '+x.area).toLocaleLowerCase('es-MX').includes(term))){
   const b=document.createElement('button');b.type='button';b.className='mapa-lugar';
   const em=document.createElement('span');em.textContent=place.emoji;
   const txt=document.createElement('span');txt.textContent=place.name;
   b.append(em,txt);b.addEventListener('click',()=>focusPlace(place));
   lugares.append(b);
  }
  if(!lugares.children.length){const p=document.createElement('p');p.className='muted';p.textContent='No hay lugares con ese nombre.';lugares.append(p)}
 }
 redrawList();
 buscar?.addEventListener('input',()=>redrawList(buscar.value));
 if(typeof window.L==='undefined'){
  $('mapa-interactivo').textContent='El mapa necesita conectarse al servidor de cartografía. Comprueba tu conexión y recarga la página.';
  show('No se pudo iniciar la biblioteca del mapa.',true);
  return;
 }
 const L=window.L;
 const map=L.map('mapa-interactivo',{zoomControl:false,preferCanvas:true,worldCopyJump:false,minZoom:9,maxZoom:19}).setView([19.414,-99.145],11);
 // CARTO exige una API key desde 2026; OSM Standard no requiere clave.
 // Usar su URL oficial, caché normal del navegador y atribución visible.
 const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom:19,
  attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'
 });
 tiles.addTo(map);
 L.control.zoom({position:'bottomright'}).addTo(map);
 const layerMonuments=L.layerGroup().addTo(map),layerNature=L.layerGroup().addTo(map),
       layerMuseums=L.layerGroup().addTo(map),layerHealth=L.layerGroup(),markers=new Map();
 const pointLayer=type=>type==='natural'?layerNature:type==='museo'?layerMuseums:type==='salud'?layerHealth:layerMonuments;
 for(const place of places){
  const marker=L.marker([place.lat,place.lng],{
   icon:L.divIcon({className:'mapa-pin-wrap',html:art(place.kind),iconSize:[64,70],iconAnchor:[32,65],popupAnchor:[0,-55]}),
   keyboard:true,title:place.name,alt:place.name,riseOnHover:true
  });
  marker.bindPopup(placePopup(place),{maxWidth:270,autoPan:true});
  marker.addTo(pointLayer(place.type));markers.set(place.id,marker);
 }
 function focusPlace(place){
  const layer=place.type==='natural'?'naturaleza':place.type==='museo'?'museos':place.type==='salud'?'salud':'monumentos';
  if(!checked(layer)){const el=capas.querySelector('input[value="'+layer+'"]');el.checked=true;toggleLayer(layer)}
  map.flyTo([place.lat,place.lng],Math.max(14,map.getZoom()),{duration:.7});
  setTimeout(()=>markers.get(place.id)?.openPopup(),450);
  $('mapa-interactivo').scrollIntoView({block:'center',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
 }
 async function obtain(mode,offset){
  const proxied='/api/transporte?modo='+encodeURIComponent(mode)+'&offset='+offset;
  const official=origin+'/'+sources[mode]+'/query?'+new URLSearchParams({
   where:'1=1',outFields:'*',returnGeometry:'true',outSR:'4326',
   resultOffset:String(offset),resultRecordCount:'350',f:'geojson'
  });
  let reason=null;
  for(const path of [proxied,official]){
   try{
    const controller=new AbortController();
    const id=setTimeout(()=>controller.abort(),14000);
    let response;
    try{response=await fetch(path,{signal:controller.signal})}
    finally{clearTimeout(id)}
    if(!response.ok)throw Error('HTTP '+response.status);
    const json=await response.json();
    if(json.error||!Array.isArray(json.features))throw Error('Geometrías no disponibles');
    return {features:json.features,nextOffset:json.nextOffset===undefined?
      (json.features.length>=350?offset+350:null):json.nextOffset};
   }catch(error){reason=error}
  }
  throw reason||Error('No fue posible consultar las rutas');
 }
 async function loadMode(mode){
  const layer=L.geoJSON(null,{
   style:feature=>styleFor(mode,feature),
   onEachFeature:(feature,obj)=>{
    const title=routeName(feature,mode);
    obj.bindPopup('<div class="mapa-popup"><span class="mapa-type">'+esc(systems[mode].name)+'</span><h3>'+esc(title)+'</h3><p>Trazo geográfico de referencia publicado por el Atlas CDMX. No indica circulación o servicio actual.</p></div>',{maxWidth:280});
    obj.on('mouseover',()=>obj.setStyle({weight:7,opacity:1}));
    obj.on('mouseout',()=>layer.resetStyle(obj));
   }
  });
  const info={layer,loaded:false,loading:true,total:0};
  state.set(mode,info);
  if(checked(mode))layer.addTo(map);
  try{
   let offset=0;
   for(let page=0;page<16;page++){
    const result=await obtain(mode,offset);
    const features=result.features.filter(f=>f&&f.geometry&&['LineString','MultiLineString'].includes(f.geometry.type));
    layer.addData({type:'FeatureCollection',features});
    info.total+=features.length;
    if(checked(mode))show('Cargando '+systems[mode].name+' · '+info.total+' trazos…');
    if(result.nextOffset==null)break;
    offset=result.nextOffset;
    if(page===15){show('Se alcanzó el límite de rutas para '+systems[mode].name+'.',true)}
   }
   info.loaded=true;
   if(info.total===0)throw Error('El atlas no devolvió rutas para esta capa.');
  }catch(error){
   info.error=error;
   if(checked(mode)){show('No se pudieron descargar las rutas de '+systems[mode].name+'. Intenta desactivar y activar de nuevo. Los monumentos siguen disponibles.',true)}
  }finally{
   info.loading=false;
   if(!info.error&&checked(mode))show(systems[mode].name+' · '+info.total+' trazos del atlas cargados.');
  }
 }
 function toggleLayer(mode){
  if(['monumentos','naturaleza','museos','salud'].includes(mode)){
   const group=mode==='naturaleza'?layerNature:mode==='museos'?layerMuseums:mode==='salud'?layerHealth:layerMonuments;
   if(checked(mode))group.addTo(map);else map.removeLayer(group);
   return;
  }
  const info=state.get(mode);
  if(checked(mode)){
   if(!info){loadMode(mode);return}
   if(info.error){state.delete(mode);loadMode(mode);return}
   info.layer.addTo(map);
  }else if(info){map.removeLayer(info.layer)}
 }
 capas.addEventListener('change',event=>{
  const mode=event.target.value;
  if(Object.prototype.hasOwnProperty.call(systems,mode)||['monumentos','naturaleza','museos','salud'].includes(mode))toggleLayer(mode);
 });
 function setDefaults(onlyPlaces=false){
  capas.querySelectorAll('input[type="checkbox"]').forEach(el=>{
   const before=el.checked;
   el.checked=onlyPlaces?['monumentos','naturaleza','museos','salud'].includes(el.value):['metro','metrobus','monumentos','naturaleza','museos'].includes(el.value);
   if(before!==el.checked)toggleLayer(el.value);
  });
 }
 $('solo-monumentos')?.addEventListener('click',()=>setDefaults(true));
 $('todas-capitas')?.addEventListener('click',()=>{setDefaults(false);map.setView([19.414,-99.145],11)});
 $('mapa-centrar')?.addEventListener('click',()=>map.setView([19.414,-99.145],11));
 const enlarge=$('mapa-ampliar'), frame=document.querySelector('.mapa-frame');
 function setExpanded(enabled){
  if(!frame||!enlarge)return;
  frame.classList.toggle('mapa-ampliado',enabled);
  document.body.classList.toggle('mapa-expandido',enabled);
  enlarge.textContent=enabled?'✕ Cerrar mapa grande':'⤢ Ver mapa grande';
  enlarge.setAttribute('aria-pressed',String(enabled));
  enlarge.setAttribute('aria-label',enabled?'Cerrar mapa grande':'Ampliar mapa de Ciudad de México');
  window.setTimeout(()=>map.invalidateSize({pan:false}),80);
 }
 enlarge?.addEventListener('click',()=>setExpanded(!frame.classList.contains('mapa-ampliado')));
 document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&frame?.classList.contains('mapa-ampliado'))setExpanded(false);
 });
 for(const mode of ['metro','metrobus'])toggleLayer(mode);
 setTimeout(()=>map.invalidateSize(),250);
 const named=new URLSearchParams(location.search).get('lugar');
 if(named){const place=places.find(p=>p.id===named);if(place)setTimeout(()=>focusPlace(place),750)}
})();
