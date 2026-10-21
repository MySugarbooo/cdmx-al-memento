const json=(data,status=200,cookie)=>new Response(JSON.stringify(data),{status,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","X-Content-Type-Options":"nosniff",...(cookie?{"Set-Cookie":`__Host-cdmx_reader=${cookie}; Path=/; Max-Age=31536000; Secure; HttpOnly; SameSite=Lax`}:{})}});
const getCookie=(req)=>req.headers.get("Cookie")?.split(";").map(x=>x.trim()).find(x=>x.startsWith("__Host-cdmx_reader="))?.split("=")[1];
const digest=async s=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s))),x=>x.toString(16).padStart(2,"0")).join("");
export async function onRequest({request,env}){
 if(!["GET","POST"].includes(request.method))return json({error:"Método no permitido"},405);
 if(!env.LIKES_DB)return json({error:"La base de datos aún no está configurada."},503);
 const u=new URL(request.url);
 const slug=u.searchParams.get("article")||"";
 if(slug.length>220||slug&&!/^https:\/\/news\.google\.com\//.test(slug)&&!/^\/[a-z0-9/_-]+\.html$/.test(slug))return json({error:"Artículo inválido"},400);
 let token=getCookie(request);
 if(!/^[a-f0-9]{64}$/.test(token||""))token=Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,"0")).join("");
 const hash=await digest(token);
 const cookies=token;
 try{
  if(request.method==="POST"){
   if(request.headers.get("Origin")!==u.origin||!request.headers.get("Content-Type")?.startsWith("application/json"))return json({error:"Solicitud no permitida"},403,cookies);
   const body=await request.text();
   if(body.length>256)return json({error:"Solicitud demasiado grande"},413,cookies);
   const data=JSON.parse(body);
   if(data.action==="visit"){
    await env.LIKES_DB.prepare("INSERT OR IGNORE INTO unique_visitors(visitor_hash,first_seen) VALUES (?,unixepoch())").bind(hash).run();
   }else if(data.action==="like"&&slug&&typeof data.liked==="boolean"){
    if(data.liked)await env.LIKES_DB.prepare("INSERT OR IGNORE INTO article_likes(article_id,visitor_hash,created_at) VALUES (?,?,unixepoch())").bind(slug,hash).run();
    else await env.LIKES_DB.prepare("DELETE FROM article_likes WHERE article_id=? AND visitor_hash=?").bind(slug,hash).run();
   }else return json({error:"Acción inválida"},400,cookies);
  }
  const visits=await env.LIKES_DB.prepare("SELECT COUNT(*) AS n FROM unique_visitors").first();
  if(!slug)return json({visitors:Number(visits.n)},200,cookies);
  const row=await env.LIKES_DB.prepare("SELECT COUNT(*) AS n, COALESCE(MAX(CASE WHEN visitor_hash=? THEN 1 ELSE 0 END),0) AS liked FROM article_likes WHERE article_id=?").bind(hash,slug).first();
  return json({visitors:Number(visits.n),likes:Number(row.n),liked:Boolean(row.liked)},200,cookies);
 }catch(e){return json({error:"No se pudo consultar el contador. Revisa las tablas de D1."},503,cookies)}
}