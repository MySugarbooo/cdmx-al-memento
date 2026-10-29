/* Estado público de Metro y Metrobús desde el tablero oficial de CDMX.
 * Endpoint incorporado en las páginas oficiales:
 * https://incidentesmovilidad.cdmx.gob.mx/public/bandejaEstadoServicio.xhtml
 * No es GTFS ni predicción de tiempos de arribo. No publicar datos parciales.
 * © 2026 CDMX AL MEMENTO; lectura sin almacenamiento de datos personales.
 */
const ORIGIN='https://incidentesmovilidad.cdmx.gob.mx/public/bandejaEstadoServicio.xhtml';
const SOURCES={
 stc:'https://www.metro.cdmx.gob.mx/la-red/estado-del-servicio',
 mb:'https://metrobus.cdmx.gob.mx/ServicioMB'
};
const EXPECTED={
 stc:new Set(['1','2','3','4','5','6','7','8','9','12','A','B']),
 mb:new Set(['1','2','3','4','5','6','7'])
};
const TABLE='frmEstadoServicio:tblEstadoServicio';
const TTL_SECONDS=300;
const TIMEOUT_MS=7500;
const HEADERS={'Content-Type':'application/json; charset=utf-8','X-Content-Type-Options':'nosniff'};
const NORMAL='servicio regular';

function plain(text,limit=400){
 return String(text||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'')
  .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,'')
  .replace(/<[^>]*>/g,' ')
  .replace(/&#(x[0-9a-f]+|\d+);/gi,(s,n)=>{
   const code=n.toLowerCase().startsWith('x')?parseInt(n.slice(1),16):parseInt(n,10);
   return Number.isInteger(code)&&code>0&&code<0x110000?String.fromCodePoint(code):' ';
  })
  .replace(/&(amp|nbsp|quot|apos|lt|gt|aacute|eacute|iacute|oacute|uacute|ntilde|Aacute|Eacute|Iacute|Oacute|Uacute|Ntilde);/g,(s,n)=>{
   const map={amp:'&',nbsp:' ',quot:'"',apos:"'",lt:'<',gt:'>',aacute:'á',eacute:'é',iacute:'í',oacute:'ó',uacute:'ú',ntilde:'ñ',Aacute:'Á',Eacute:'É',Iacute:'Í',Oacute:'Ó',Uacute:'Ú',Ntilde:'Ñ'};
   return map[n]||' ';
  })
  .replace(/\s+/g,' ').trim().slice(0,limit);
}
function rowCount(markup){
 const match=String(markup||'').match(/paginator\s*:\s*\{[^}]*?\browCount\s*:\s*(\d+)/i);
 const number=match?Number(match[1]):NaN;
 return Number.isInteger(number)&&number>0&&number<100?number:null;
}
function viewState(markup){
 for(const input of String(markup||'').match(/<input\b[^>]*>/gi)||[]){
  if(!/name\s*=\s*["']jakarta\.faces\.ViewState["']/i.test(input))continue;
  const match=input.match(/value\s*=\s*["']([^"']+)["']/i);
  if(match)return match[1].replace(/&amp;/g,'&');
 }
 return null;
}
function parseRows(html,system){
 const lines=EXPECTED[system];
 if(!lines)throw Error('Sistema no reconocido');
 const rows=[];
 const tr=/<tr\b([^>]*)>([\s\S]*?)<\/tr>/gi;
 let match;
 while((match=tr.exec(String(html||'')))){
  if(!/\bdata-ri\s*=\s*["']?\d+["']?/i.test(match[1]))continue;
  const cells=[...match[2].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)].map(x=>x[1]);
  if(cells.length<3)throw Error('Registro oficial incompleto');
  const image=cells[0].match(/<img\b[^>]*\bsrc\s*=\s*["']([^"']+)["']/i);
  if(!image)throw Error('Sin identificador de línea');
  const icon=image[1].match(/\/lineas\/(stc|mb)([a-z0-9]+)\.(?:svg|png)/i);
  const line=icon?.[2]?.toUpperCase()||'';
  if(!lines.has(line))throw Error('Línea no reconocida: '+line);
  const state=plain(cells[1],110);
  if(!state)throw Error('Sin información de estado');
  rows.push({
   linea:line,
   estado:state,
   estaciones_afectadas:plain(cells[2],180),
   informacion_adicional:plain(cells[3]||'',350),
   regular:state.toLowerCase().startsWith(NORMAL)
  });
 }
 return rows;
}
function rowsValid(rows,system,count){
 const expected=EXPECTED[system];
 if(!Number.isInteger(count)||count<expected.size||count>60||rows.length!==count)return false;
 const found=new Set(rows.map(row=>row.linea));
 return found.size===expected.size&&[...expected].every(line=>found.has(line));
}
function partialFragment(body){
 const update=String(body||'').match(/<update\b[^>]*\bid\s*=\s*["']frmEstadoServicio:tblEstadoServicio["'][^>]*>([\s\S]*?)<\/update>/i);
 if(!update)return null;
 const cdata=update[1].match(/<!\[CDATA\[([\s\S]*?)\]\]>/i);
 return cdata?cdata[1]:update[1].replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
}
function cookieForNextRequest(response){
 const value=response.headers.get('set-cookie')||'';
 const match=value.match(/\bJSESSIONID=([^;,\s]+)/i);
 return match?'JSESSIONID='+match[1]:'';
}
async function readSystem(system){
 const url=ORIGIN+'?idMedioTransporte='+system;
 const response=await fetch(url,{
  method:'GET',signal:AbortSignal.timeout(TIMEOUT_MS),
  headers:{'Accept':'text/html','User-Agent':'CDMXALMEMENTO/1.0 (https://cdmx-al-memento.pages.dev/contacto.html)'}
 });
 if(!response.ok)throw Error('Fuente oficial no disponible '+system);
 const html=await response.text();
 if(html.length>500000)throw Error('Respuesta excesivamente grande');
 const count=rowCount(html),state=viewState(html);
 if(!count)throw Error('Conteo oficial no encontrado');
 const rows=parseRows(html,system);
 if(count>rows.length){
  if(!state)throw Error('Falta sesión para paginar');
  const cookie=cookieForNextRequest(response);
  for(let first=10;first<count;first+=10){
   const params=new URLSearchParams();
   params.set('jakarta.faces.partial.ajax','true');
   params.set('jakarta.faces.source',TABLE);
   params.set('jakarta.faces.partial.execute',TABLE);
   params.set('jakarta.faces.partial.render',TABLE);
   params.set(TABLE,TABLE);
   params.set(TABLE+'_pagination','true');
   params.set(TABLE+'_first',String(first));
   params.set(TABLE+'_rows','10');
   params.set(TABLE+'_encodeFeature','true');
   params.set('frmEstadoServicio','frmEstadoServicio');
   params.set('jakarta.faces.ViewState',state);
   const paged=await fetch(url,{
    method:'POST',signal:AbortSignal.timeout(TIMEOUT_MS),
    headers:{
     'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
     'Faces-Request':'partial/ajax','X-Requested-With':'XMLHttpRequest',
     ...(cookie?{'Cookie':cookie}:{})
    },
    body:params.toString()
   });
   if(!paged.ok)throw Error('No fue posible completar la paginación');
   const body=await paged.text();
   if(body.length>500000)throw Error('Respuesta excesivamente grande');
   const fragment=partialFragment(body);
   if(!fragment)throw Error('La paginación no devolvió filas');
   rows.push(...parseRows(fragment,system));
  }
 }
 if(!rowsValid(rows,system,count))throw Error('La consulta no incluye todas las líneas');
 return {url:SOURCES[system],rows};
}
function json(body,maxAge=TTL_SECONDS){
 return new Response(JSON.stringify(body),{
  status:200,headers:{...HEADERS,'Cache-Control':'public, max-age='+maxAge+', s-maxage='+maxAge}
 });
}
export async function onRequestGet({request,context}){
 const cache=typeof caches!=='undefined'?caches.default:null;
 const key=new Request(new URL('/api/estado-transporte',request.url).toString());
 if(cache){
  try{const result=await cache.match(key);if(result)return result}catch{}
 }
 let output,cacheSeconds=TTL_SECONDS;
 try{
  const [metro,metrobus]=await Promise.race([
   Promise.all([readSystem('stc'),readSystem('mb')]),
   new Promise((_,reject)=>setTimeout(()=>reject(Error('Tiempo de espera agotado')),10000))
  ]);
  output={
   schema:1,status:'ok',checked_at:new Date().toISOString(),
   source:'Tablero público oficial de incidentes de movilidad CDMX',
   source_url:ORIGIN,operators:{stc:metro,mb:metrobus},
   note:'Hora de consulta, no de actualización de incidentes ni de operación del sistema.'
  };
 }catch{
  cacheSeconds=90;
  output={schema:1,status:'unavailable',checked_at:null,
   source:'Tablero público oficial de incidentes de movilidad CDMX',
   source_url:ORIGIN,operators:{
    stc:{url:SOURCES.stc,rows:[]},mb:{url:SOURCES.mb,rows:[]}
   },
   note:'No fue posible realizar una consulta completa. No se presentan estados inventados.'};
 }
 const result=json(output,cacheSeconds);
 if(cache&&context?.waitUntil){
  context.waitUntil(cache.put(key,result.clone()).catch(()=>{}));
 }
 return result;
}
export {parseRows,rowCount,viewState,rowsValid,partialFragment};
