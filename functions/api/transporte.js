/* Proxy del Atlas Público CDMX. Datos cartográficos orientativos, no operación en vivo. */
const SERVICE='https://serviciosatlas.sgirpc.cdmx.gob.mx/arcgis/rest/services/AtlasCapasPublicas/Movilidad_Integrada_CDMX/FeatureServer';
const LAYERS=Object.freeze({metro:1,metrobus:3,rtp:5,trolebus:7,ligero:9,cablebus:11,camiones:16});
const LIMIT=350;
function respond(payload,status=200,headers={}){
 return new Response(JSON.stringify(payload),{status,headers:{
  'content-type':'application/json; charset=utf-8',
  'cache-control':status===200?'public, max-age=180, s-maxage=3600':'no-store',
  'access-control-allow-origin':'*',
  ...headers
 }});
}
export async function onRequestGet({request}){
 const url=new URL(request.url);
 const mode=url.searchParams.get('modo');
 const offset=Number(url.searchParams.get('offset')||'0');
 if(!Object.prototype.hasOwnProperty.call(LAYERS,mode)||!Number.isInteger(offset)||offset<0||offset>7000){
  return respond({error:'Modo de transporte u offset inválido.'},400);
 }
 const query=new URL(SERVICE+'/'+LAYERS[mode]+'/query');
 query.search=new URLSearchParams({
  where:'1=1',outFields:'*',returnGeometry:'true',outSR:'4326',
  resultOffset:String(offset),resultRecordCount:String(LIMIT),f:'geojson'
 }).toString();
 try{
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),12000);
  let response;
  try{response=await fetch(query.toString(),{signal:controller.signal,headers:{accept:'application/geo+json,application/json'}})}
  finally{clearTimeout(timeout)}
  if(!response.ok)return respond({error:'El atlas oficial no respondió.'},502);
  const raw=await response.text();
  if(raw.length>6000000)return respond({error:'La consulta excede el tamaño permitido.'},502);
  const data=JSON.parse(raw);
  if(data.error||!Array.isArray(data.features))return respond({error:'El atlas no devolvió geometrías válidas.'},502);
  const features=data.features.filter(item=>
   item&&item.geometry&&['LineString','MultiLineString'].includes(item.geometry.type)
  ).map(item=>({
   type:'Feature',
   geometry:item.geometry,
   properties:{
    linea:String(item.properties?.linea??item.properties?.LINEA??'').slice(0,80),
    ruta:String(item.properties?.ruta??item.properties?.RUTA??item.properties?.nombre??item.properties?.NOMBRE??'').slice(0,180),
    sistema:String(item.properties?.sistema??item.properties?.SISTEMA??'').slice(0,80)
   }
  }));
  return respond({type:'FeatureCollection',modo:mode,features,nextOffset:data.features.length===LIMIT?offset+LIMIT:null});
 }catch(error){
  return respond({error:'No fue posible consultar el atlas oficial en este momento.'},502);
 }
}
