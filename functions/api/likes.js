const COOKIE = 'cdmx_site_like';
const YEAR = 31536000;
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const SCHEMA = 'CREATE TABLE IF NOT EXISTS site_likes (visitor_id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)';
function json(body, status=200, extra={}) {
 return new Response(JSON.stringify(body), {status,headers:{
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...extra
 }});
}
function visitor(request) {
 const raw=request.headers.get('Cookie')||'';
 const match=raw.split(';').map(x=>x.trim()).find(x=>x.startsWith(COOKIE+'='));
 const value=match?match.slice(COOKIE.length+1):'';
 return UUID.test(value)?value:null;
}
async function database(env) {
 if(!env.LIKES_DB?.prepare)throw new Error('Storage unavailable');
 await env.LIKES_DB.prepare(SCHEMA).run();
 return env.LIKES_DB;
}
function countOf(row) {
 const n=Number(row?.count);
 if(!Number.isSafeInteger(n)||n<0)throw new Error('Invalid count');
 return n;
}
export async function onRequestGet({request,env}) {
 try {
  const db=await database(env);
  const id=visitor(request);
  const [count,liked]=await Promise.all([
   db.prepare('SELECT COUNT(*) AS count FROM site_likes').first(),
   id?db.prepare('SELECT 1 AS liked FROM site_likes WHERE visitor_id = ?').bind(id).first():null
  ]);
  return json({count:countOf(count),liked:Boolean(liked)});
 } catch {return json({error:'El contador no está disponible. Intenta más tarde.'},503);}
}
export async function onRequestPost({request,env}) {
 const origin=request.headers.get('Origin');
 if(origin!==new URL(request.url).origin ||
    request.headers.get('Sec-Fetch-Site')==='cross-site')
  return json({error:'Solicitud no permitida.'},403);
 if(!request.headers.get('Content-Type')?.startsWith('application/json'))
  return json({error:'Formato no permitido.'},415);
 try {
  const db=await database(env);
  const id=visitor(request)||crypto.randomUUID();
  // El índice único y el lote atómico evitan duplicados y pérdidas concurrentes.
  const result=await db.batch([
   db.prepare('INSERT OR IGNORE INTO site_likes (visitor_id) VALUES (?)').bind(id),
   db.prepare('SELECT COUNT(*) AS count FROM site_likes')
  ]);
  const count=countOf(result[1]?.results?.[0]);
  return json({count,liked:true},200,{
   'Set-Cookie':COOKIE+'='+id+'; Path=/; Max-Age='+YEAR+'; Secure; HttpOnly; SameSite=Lax'
  });
 } catch {return json({error:'No se pudo guardar tu Me gusta. Inténtalo de nuevo.'},503);}
}
export function onRequestOptions(){return json({error:'Método no permitido.'},405,{'Allow':'GET, POST'});}
