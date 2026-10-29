/* Índice editorial de comunicados CAMe publicados en el portal oficial.
 * Una suspensión/activación antigua jamás se presenta como estado vigente.
 * Falla de forma cerrada; fuente oficial: gob.mx/comisionambiental/es/archivo/prensa
 */
const BASE='https://www.gob.mx';
const ARCHIVE=BASE+'/comisionambiental/es/archivo/prensa';
const MONTHS={enero:1,febrero:2,marzo:3,abril:4,mayo:5,junio:6,
 julio:7,agosto:8,septiembre:9,octubre:10,noviembre:11,diciembre:12};
const TTL=1800;
const HEADERS={'Content-Type':'application/json; charset=utf-8','X-Content-Type-Options':'nosniff'};
const text=markup=>String(markup||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'')
 .replace(/<[^>]*>/g,' ').replace(/&nbsp;|&#160;/g,' ')
 .replace(/&amp;/g,'&').replace(/&aacute;/g,'á').replace(/&oacute;/g,'ó')
 .replace(/&eacute;/g,'é').replace(/&iacute;/g,'í').replace(/&uacute;/g,'ú')
 .replace(/\s+/g,' ').trim();
function safeOfficial(href){
 try{
  const url=new URL(href,BASE);
  if(url.protocol!=='https:'||url.hostname!=='www.gob.mx'
    ||!url.pathname.startsWith('/comisionambiental/'))return null;
  return url.href;
 }catch{return null}
}
function parseAdvisories(html,now=Date.now()){
 const entries=[];
 for(const match of String(html||'').matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/gi)){
  const block=match[1];
  const heading=block.match(/<h2\b[^>]*>([\s\S]*?)<\/h2>/i);
  const time=block.match(/<time\b[^>]*>([\s\S]*?)<\/time>/i);
  if(!heading||!time)continue;
  const title=text(heading[1]).slice(0,240);
  const upper=title.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();
  if(!upper.includes('CONTINGENCIA AMBIENTAL'))continue;
  let action='informacion';
  if(/\b(SE SUSPENDE|SE LEVANTA|SE DESACTIVA)\b/.test(upper))action='suspension';
  else if(/\b(SE ACTIVA|SE DECLARA|SE ESTABLECE)\b/.test(upper))action='activacion';
  else if(/\b(CONTINUA|SE MANTIENE|SE PROLONGA)\b/.test(upper))action='seguimiento';
  else continue;
  const d=text(time[1]).match(/(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(20\d{2})/i);
  if(!d)continue;
  const month=MONTHS[d[2].toLowerCase()],day=Number(d[1]),year=Number(d[3]);
  if(!month||day<1||day>31)continue;
  const stamp=new Date(Date.UTC(year,month-1,day,12));
  if(stamp.getUTCDate()!==day||stamp.getUTCMonth()!==month-1
    ||stamp.getUTCFullYear()!==year||stamp.getTime()>now+24*60*60*1000)continue;
  const anchor=block.match(/<a\b[^>]*href\s*=\s*["']([^"']+)["']/i);
  const link=anchor?safeOfficial(anchor[1]):null;
  entries.push({
   title,action,date:stamp.toISOString().slice(0,10),
   url:link||ARCHIVE,
   archived:true,
   recent:now-stamp.getTime()<=48*60*60*1000,
   scope:'Comunicado oficial histórico: no confirma que la contingencia esté activa ahora.'
  });
 }
 return entries.sort((a,b)=>b.date.localeCompare(a.date)).slice(0,6);
}
function outputJSON(data,ttl){
 return new Response(JSON.stringify(data),{
  status:200,headers:{...HEADERS,'Cache-Control':ttl?
   'public, max-age='+ttl+', s-maxage='+ttl:'no-store'}
 });
}
export async function onRequestGet({request,context}){
 const cache=typeof caches==='undefined'?null:caches.default;
 const key=new Request(new URL('/api/contingencias',request.url).toString());
 if(cache){try{const found=await cache.match(key);if(found)return found}catch{}}
 let body,ttl=0;
 try{
  const ctrl=new AbortController();
  const timer=setTimeout(()=>ctrl.abort(),8200);
  let html;
  try{
   const response=await fetch(ARCHIVE,{
    headers:{Accept:'text/html','User-Agent':'CDMXALMEMENTO/1.0 (https://cdmx-al-memento.pages.dev/contacto.html)'},
    signal:ctrl.signal
   });
   if(!response.ok)throw Error('CAMe no disponible');
   html=await response.text();
   if(html.length>900000)throw Error('Respuesta excesivamente grande');
  }finally{clearTimeout(timer)}
  if(!/<article\b/i.test(html))throw Error('Archivo sin estructura verificable');
  body={schema:1,status:'ok',checked_at:new Date().toISOString(),
   source:'Comisión Ambiental de la Megalópolis',
   source_url:ARCHIVE,
   advisories:parseAdvisories(html),
   note:'Archivo de comunicados; no determina si existe una contingencia vigente.'};
  ttl=TTL;
 }catch{
  body={schema:1,status:'unavailable',checked_at:new Date().toISOString(),
   source_url:ARCHIVE,advisories:[],
   note:'No fue posible revisar los comunicados oficiales. Confirma en CAMe.'};
 }
 const response=outputJSON(body,ttl);
 if(cache&&context?.waitUntil&&ttl>0){
  context.waitUntil(cache.put(key,response.clone()).catch(()=>{}));
 }
 return response;
}
export {parseAdvisories,safeOfficial,text};
