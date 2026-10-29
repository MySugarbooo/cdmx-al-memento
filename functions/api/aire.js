/* Datos oficiales de Aire y Salud para CDMX; no son mediciones de cada alcaldía.
 * Fuente: https://www.aire.cdmx.gob.mx/ultima-hora-reporte.php
 * Si la hora de la fuente está atrasada, o cambió el formato, devolver "unavailable".
 * No se calculan índices ni se declara el estado de contingencia aquí.
 */
const REPORT='https://www.aire.cdmx.gob.mx/ultima-hora-reporte.php';
const LIGHT='https://www.aire.cdmx.gob.mx/default.php';
const MONTHS={enero:1,febrero:2,marzo:3,abril:4,mayo:5,junio:6,julio:7,
 agosto:8,septiembre:9,setiembre:9,octubre:10,noviembre:11,diciembre:12};
const BANDS=['BUENA','ACEPTABLE','MALA','MUY MALA','EXTREMADAMENTE MALA'];
const RISKS=['BAJO','MODERADO','ALTO','MUY ALTO','EXTREMADAMENTE ALTO'];
const POLLUTANTS=['O3','PM2.5','PM10','NO2','SO2','CO'];
const MAX_AGE=150*60*1000;
const HEADERS={'Content-Type':'application/json; charset=utf-8','X-Content-Type-Options':'nosniff'};
function strip(html){
 return String(html||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'')
  .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,'')
  .replace(/<[^>]+>/g,' ').replace(/&nbsp;|&#160;/g,' ')
  .replace(/&aacute;/g,'á').replace(/&eacute;/g,'é').replace(/&iacute;/g,'í')
  .replace(/&oacute;/g,'ó').replace(/&uacute;/g,'ú').replace(/&ntilde;/g,'ñ')
  .replace(/\s+/g,' ').trim();
}
function sourceStamp(year,month,day,hour,minute){
 if(!Number.isInteger(year)||!Number.isInteger(month)||!Number.isInteger(day)
   ||!Number.isInteger(hour)||!Number.isInteger(minute)
   ||year<2024||year>2100||month<1||month>12||day<1||day>31||hour>23||hour<0
   ||minute<0||minute>59)return null;
 const date=new Date(Date.UTC(year,month-1,day,hour+6,minute));
 // Ciudad de México está en UTC-6 todo el año desde 2022.
 const local=new Intl.DateTimeFormat('en-US',{timeZone:'America/Mexico_City',
  year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23',minute:'2-digit'}).formatToParts(date);
 const v=part=>Number(local.find(t=>t.type===part)?.value);
 if(v('year')!==year||v('month')!==month||v('day')!==day||v('hour')!==hour||v('minute')!==minute)return null;
 return date.toISOString();
}
function parseAirReport(markup,now=Date.now()){
 // El portal puede responder con tablas de presentación antes del indicador;
 // no cortar el HTML en la primera tabla ni depender de párrafos específicos.
 const raw=String(markup||'');
 if(raw.length<130||raw.length>450000)throw Error('Respuesta oficial inesperada');
 const plain=strip(raw).normalize('NFC');
 const indexMatch=/Índice\s+AIRE\s+Y\s+SALUD:\s*(EXTREMADAMENTE MALA|MUY MALA|ACEPTABLE|BUENA|MALA)\b/i.exec(plain);
 if(!indexMatch)throw Error('Categoría, riesgo o contaminante ausente');
 const idx=indexMatch.index;
 // Sólo aceptamos datos alrededor del encabezado del reporte, no texto de
 // informes históricos o tablas de otros años en el resto del documento.
 const before=plain.slice(Math.max(0,idx-1700),idx);
 const after=plain.slice(idx,idx+550);
 const dates=[...before.matchAll(/(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(20\d\d)/gi)];
 const dateParts=dates.at(-1);
 if(!dateParts)throw Error('No hay fecha/hora oficial');
 const hours=[...before.matchAll(/(?:^|\s)([01]?\d|2[0-3]):([0-5]\d)\s*h\b/gi)];
 const hoursPlain=[...before.matchAll(/(?:^|\s)([01]?\d|2[0-3])\s*horas?\b/gi)];
 const timeCandidates=[
  ...hours.map(m=>({index:m.index,hour:Number(m[1]),minute:Number(m[2])})),
  ...hoursPlain.map(m=>({index:m.index,hour:Number(m[1]),minute:0}))
 ].sort((a,b)=>a.index-b.index);
 const time=timeCandidates.at(-1);
 if(!time)throw Error('No hay fecha/hora oficial');
 const publishedAt=sourceStamp(
  Number(dateParts[3]),MONTHS[dateParts[2].toLowerCase()],
  Number(dateParts[1]),time.hour,time.minute
 );
 if(!publishedAt)throw Error('Fecha oficial no válida');
 const age=now-Date.parse(publishedAt);
 if(age< -15*60*1000||age>MAX_AGE)throw Error('Índice oficial desactualizado');
 const category=indexMatch[1].toUpperCase();
 const riskMatch=/(?:Nivel de riesgo|Riesgo):\s*(EXTREMADAMENTE ALTO|MUY ALTO|MODERADO|BAJO|ALTO)\b/i.exec(
  plain.slice(Math.max(0,idx-250),idx+450)
 );
 const pollutantLabel=/Contaminante\(s\):/i.exec(after);
 const risk=riskMatch?.[1]?.toUpperCase();
 if(!BANDS.includes(category)||!RISKS.includes(risk)||!pollutantLabel)
  throw Error('Categoría, riesgo o contaminante ausente');
 // El portal inserta textos accesorios después del nombre del contaminante.
 // Identificar únicamente las fórmulas dentro del campo encabezado, sin
 // depender de una etiqueta HTML específica o de una coma final.
 const pollutantField=after.slice(pollutantLabel.index+pollutantLabel[0].length)
  .split(/\b(?:Nivel de riesgo|Riesgo|Recomendaci[oó]n|Hoy no circulan|Información|Reporte)\b/i)[0]
  .slice(0,95).toUpperCase().replace(/\s+/g,'');
 const detected=POLLUTANTS.filter(p=>
  new RegExp('(?:^|[^A-Z0-9.])'+p.replace('.','\\.')+'(?:$|[^A-Z0-9.])').test(pollutantField)
 );
 if(!detected.length)throw Error('Sin contaminantes identificables');
 return {
  category,risk,pollutants:detected,reported_at:publishedAt,
  source_url:REPORT,official:true,
  scope:'Reporte general de la Ciudad de México; no equivale al nivel de ninguna alcaldía o estación.'
 };
}
async function fromOfficial(url){
 const controller=new AbortController();
 const timeout=setTimeout(()=>controller.abort(),7800);
 try{
  const response=await fetch(url,{headers:{
   Accept:'text/html','User-Agent':'CDMXALMEMENTO/1.0 (https://cdmx-al-memento.pages.dev/contacto.html)'
  },signal:controller.signal});
  if(!response.ok)throw Error('HTTP '+response.status);
  const content=await response.text();
  if(content.length>450000)throw Error('Respuesta demasiado grande');
  try{return parseAirReport(content)}
  catch(error){
   error.publicPreview=strip(content).slice(0,430);
   error.publicSize=content.length;
   throw error;
  }
 }finally{clearTimeout(timeout)}
}
function json(body,ttl){
 return new Response(JSON.stringify(body),{
  status:200,headers:{...HEADERS,'Cache-Control':ttl>0?
   'public, max-age='+ttl+', s-maxage='+ttl:'no-store'}
 });
}
function safeFailure(error){
 const message=String(error?.message||'');
 const match=message.match(/HTTP (\d{3})/);
 if(match)return 'upstream-http-'+match[1];
 if(/No hay fecha\/hora oficial/.test(message))return 'source-time-missing';
 if(/Fecha oficial no válida/.test(message))return 'source-date-invalid';
 if(/desactualizado/.test(message))return 'source-report-stale';
 if(/Categoría, riesgo o contaminante|Sin contaminantes|Clasificación desconocida/.test(message))return 'source-format-changed';
 if(/excesivamente grande|inesperada/.test(message))return 'source-format-unexpected';
 if(error?.name==='AbortError'||error?.name==='TimeoutError')return 'upstream-timeout';
 return 'source-unreachable';
}
export async function onRequestGet({request,context}){
 const cache=typeof caches==='undefined'?null:caches.default;
 const key=new Request(new URL('/api/aire',request.url).toString());
 if(cache){try{const found=await cache.match(key);if(found)return found}catch{}}
 let result,ttl=0;
 const failures=[];
 const samples=[];
 const debug=new URL(request.url).searchParams.get('diagnostico')==='si';
 try{
  let air;
  try{air=await fromOfficial(REPORT)}
  catch(error){
   failures.push(safeFailure(error));
   if(debug)samples.push({source:'reporte',preview:error.publicPreview||'',size:error.publicSize||0});
   air=await fromOfficial(LIGHT);
  }
  result={schema:1,status:'ok',checked_at:new Date().toISOString(),air};
  ttl=600; // No convertir la hora de consulta en hora del reporte oficial.
 }catch(error){
  failures.push(safeFailure(error));
  if(debug)samples.push({source:'portada',preview:error.publicPreview||'',size:error.publicSize||0});
  result={schema:1,status:'unavailable',checked_at:new Date().toISOString(),
   air:null,diagnostic:failures,...(debug?{samples}:{}),
   note:'No hay un índice oficial reciente comprobable. Consulta Aire CDMX.'};
 }
 const response=json(result,ttl);
 if(cache&&context?.waitUntil&&ttl>0){
  context.waitUntil(cache.put(key,response.clone()).catch(()=>{}));
 }
 return response;
}
export {parseAirReport,sourceStamp,strip};
