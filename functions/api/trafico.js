'use strict';
/* Titulares viales recientes, NO confirmaciones de cierres activos.
 * Google News RSS (enlaces y atribución, sin reproducir artículos).
 * El visitante siempre debe revisar @OVIALCDMX y agenda de SSC.
 * Ningún dato de esta API es un reporte oficial de tráfico en tiempo real.
 */
const SOURCES=[
 {key:'marchas',q:'("marcha" OR "manifestación" OR "movilización") ("CDMX" OR "Ciudad de México") when:2d'},
 {key:'cierres',q:'("cierre vial" OR "bloqueo vial" OR "calles cerradas") ("CDMX" OR "Ciudad de México") when:2d'},
 {key:'obras',q:'("cierre de carriles" OR "obras viales" OR "accidente vial") ("CDMX" OR "Ciudad de México") when:2d'}
];
const MAX_AGE_MS=48*60*60*1000;
const CACHE_SECONDS=15*60;
const MAX_FETCH_MS=7500;
const CORS={'Content-Type':'application/json; charset=utf-8','X-Content-Type-Options':'nosniff'};
const BOROUGHS=[
 'Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos',
 'Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras',
 'Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'
];
const ACCENTS={
 'álvaro obregón':'alvaro obregon','benito juárez':'benito juarez',
 'cuajimalpa de morelos':'cuajimalpa de morelos','cuauhtémoc':'cuauhtemoc',
 'gustavo a. madero':'gustavo a madero','tláhuac':'tlahuac',
 'venustiano carranza':'venustiano carranza','la magdalena contreras':'la magdalena contreras'
};
const normalize=t=>String(t||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es-MX');
function decodeXML(text){
 const entities={amp:'&',quot:'"',apos:"'",lt:'<',gt:'>',nbsp:' ',ntilde:'ñ',
 aacute:'á',eacute:'é',iacute:'í',oacute:'ó',uacute:'ú',
 Aacute:'Á',Eacute:'É',Iacute:'Í',Oacute:'Ó',Uacute:'Ú'};
 return String(text||'').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1')
 .replace(/&#(x[0-9a-f]+|\d+);/gi,(raw,n)=>{
  const value=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):parseInt(n,10);
  return Number.isInteger(value)&&value>0&&value<0x110000?String.fromCodePoint(value):' ';
 })
 .replace(/&([a-zA-Z]+);/g,(raw,n)=>entities[n]||raw)
 .replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
}
function tagValue(xml,tag){
 const m=String(xml||'').match(new RegExp('<'+tag+'(?:\\s[^>]*)?>([\\s\\S]*?)<\\/'+tag+'>','i'));
 return m?decodeXML(m[1]):'';
}
function identifyType(title){
 const t=normalize(title);
 // A headline is only categorized, never certified as an active road closure.
 if(/\b(marcha|marchas|manifestacion|manifestantes|movilizacion|protesta|concentracion)\b/.test(t))return 'marchas';
 if(/\b(choque|accidente|volcadura|percance|inundacion|socavon|vehiculo varado)\b/.test(t)
   && /\b(vial|avenida|calzada|carretera|autopista|calle|transito|circulacion|periferico|insurgentes)\b/.test(t))return 'incidentes';
 if(/\b(obra|obras|repavimentacion|mantenimiento|reparacion|carriles)\b/.test(t)
   && /\b(vial|cierre|calle|avenida|calzada|transito|circulacion|carriles|autopista|periferico|paseo de la reforma)\b/.test(t))return 'obras';
 if(/\b(cierre|cierres|cerrada|cerrado|bloqueo|bloqueos|corte|afectacion|afectaciones|colapso vial|trafico)\b/.test(t)
   && /\b(vial|calle|calles|avenida|av\.|calzada|carriles|circulacion|carretera|autopista|reforma|periferico|insurgentes|bloqueo|bloqueos|trafico)\b/.test(t))return 'cierres';
 return null;
}
function placeFromTitle(title){
 const t=normalize(title);
 const found=BOROUGHS.find(name=>t.includes(normalize(name)));
 return found||'No precisada';
}
function hasCDMXContext(title){
 const t=normalize(title);
 const city=/\b(cdmx|ciudad de mexico|capital mexicana|capital del pais)\b/.test(t);
 const borough=BOROUGHS.some(name=>t.includes(normalize(name)));
 const roads=/\b(paseo de la reforma|eje central|insurgentes|viaducto tlalpan|circuito interior|av\. tlahuac|calzada de tlalpan|periferico sur)\b/.test(t);
 const outside=/\b(xalapa|veracruz|guadalajara|monterrey|puebla|cancun|queretaro|morelia|tijuana|oaxaca|merida|zacatecas|hermosillo|chilpancingo|cuernavaca)\b/.test(t);
 // Reject another city's event even if a broad query included CDMX.
 return (city||borough||roads)&&(!outside||borough||roads);
}
function linkSafe(url){
 try{
  const u=new URL(String(url||''));
  return u.protocol==='https:'&&u.hostname==='news.google.com'&&u.pathname.startsWith('/rss/articles/')?u.href:null;
 }catch{return null}
}
function parseRSS(xml,now=Date.now()){
 const input=String(xml||'');
 if(!input.includes('<rss')&&!input.includes('<feed'))throw Error('RSS inválido');
 const matches=[...input.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)];
 const rows=[];
 for(const match of matches.slice(0,70)){
  const item=match[1],raw=tagValue(item,'title'),url=linkSafe(tagValue(item,'link'));
  const date=Date.parse(tagValue(item,'pubDate'));
  const source=tagValue(item,'source').slice(0,95)||'Medio de comunicación';
  const title=raw.endsWith(' - '+source)?raw.slice(0,-source.length-3):raw;
  const type=identifyType(title);
  if(!type||!url||!hasCDMXContext(title)||!Number.isFinite(date)
    ||date>now+5*60*1000||now-date>MAX_AGE_MS)continue;
  rows.push({
   title:title.slice(0,240),
   source,
   published_at:new Date(date).toISOString(),
   type,
   borough:placeFromTitle(title),
   url
  });
 }
 return rows;
}
function mergeFeeds(feeds){
 const seen=new Set(),all=[];
 for(const feed of feeds){
  for(const item of feed){
   const key=normalize(item.title).replace(/[^a-z0-9]+/g,'').slice(0,150);
   if(!key||seen.has(key))continue;
   seen.add(key);all.push(item);
  }
 }
 return all.sort((a,b)=>Date.parse(b.published_at)-Date.parse(a.published_at)).slice(0,35);
}
async function fetchOne(q){
 const url=new URL('https://news.google.com/rss/search');
 url.searchParams.set('q',q);
 url.searchParams.set('hl','es-419');
 url.searchParams.set('gl','MX');
 url.searchParams.set('ceid','MX:es-419');
 const abort=new AbortController();
 const timer=setTimeout(()=>abort.abort(),MAX_FETCH_MS);
 try{
  const response=await fetch(url,{method:'GET',signal:abort.signal,headers:{Accept:'application/rss+xml, application/xml, text/xml'}});
  if(!response.ok)throw Error('Fuente RSS indisponible');
  const raw=await response.text();
  if(raw.length>750000)throw Error('RSS demasiado grande');
  return parseRSS(raw);
 }finally{clearTimeout(timer)}
}
function resultJSON(object,ttl=CACHE_SECONDS){
 return new Response(JSON.stringify(object),{
  status:200,headers:{...CORS,'Cache-Control':'public, max-age='+ttl+', s-maxage='+ttl}
 });
}
export async function onRequestGet({request,context}){
 const key=new Request(new URL('/api/trafico',request.url).toString());
 const cache=typeof caches==='undefined'?null:caches.default;
 if(cache){try{const hit=await cache.match(key);if(hit)return hit}catch{}}
 const results=await Promise.allSettled(SOURCES.map(s=>fetchOne(s.q)));
 const good=results.filter(r=>r.status==='fulfilled').map(r=>r.value);
 const records=mergeFeeds(good);
 const output={
  schema:1,status:good.length?'ok':'unavailable',
  checked_at:new Date().toISOString(),
  advisory:'Titulares periodísticos, NO cierres confirmados ni estado vial en vivo. Verifica antes de salir.',
  origin:'Google News RSS: medios identificados y enlazados; no fuente oficial de tránsito.',
  streams_consulted:good.length,streams_expected:SOURCES.length,
  window_hours:48,articles:records
 };
 const response=resultJSON(output,good.length?CACHE_SECONDS:90);
 if(cache&&context?.waitUntil)context.waitUntil(cache.put(key,response.clone()).catch(()=>{}));
 return response;
}
export {decodeXML,tagValue,identifyType,placeFromTitle,hasCDMXContext,linkSafe,parseRSS,mergeFeeds};
