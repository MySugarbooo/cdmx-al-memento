'use strict';
(()=>{
 if(document.querySelector('[data-site-like]'))return;
 const bar=document.createElement('section');bar.className='site-like-bar wrap';
 bar.setAttribute('aria-label','Apoya a CDMX AL MEMENTO');
 const button=document.createElement('button');button.type='button';button.className='site-like-button';
 button.dataset.siteLike='';button.setAttribute('aria-pressed','false');button.disabled=true;
 const heart=document.createElement('span');heart.className='site-like-heart';heart.setAttribute('aria-hidden','true');heart.textContent='♡';
 const label=document.createElement('span');label.textContent='Me gusta este sitio';
 const count=document.createElement('span');count.className='site-like-count';count.textContent='—';
 const status=document.createElement('p');status.className='site-like-status';status.setAttribute('role','status');status.textContent='Cargando…';
 button.append(heart,label,count);bar.append(button,status);
 const main=document.querySelector('main');if(!main)return;main.before(bar);
 let busy=false,liked=false,loaded=false;
 const format=new Intl.NumberFormat('es-MX');
 async function query(method='GET'){
  const options={method,credentials:'same-origin',cache:'no-store'};
  if(method==='POST'){options.headers={'Content-Type':'application/json'};options.body='{}';}
  const response=await fetch('/api/likes',options);
  if(!response.ok)throw new Error('Counter unavailable');
  const data=await response.json();
  if(!Number.isSafeInteger(data.count)||data.count<0||typeof data.liked!=='boolean')
   throw new Error('Invalid count');
  loaded=true;liked=data.liked;count.textContent=format.format(data.count);
  button.setAttribute('aria-pressed',String(liked));heart.textContent=liked?'♥':'♡';
  label.textContent=liked?'Te gusta este sitio':'Me gusta este sitio';
  status.textContent=liked?'¡Gracias por tu apoyo!':'¿Te gusta CDMX AL MEMENTO? Déjanos un corazón.';
 }
 async function refresh(){
  if(busy)return;busy=true;button.disabled=true;
  try{await query();}
  catch{status.textContent='No se pudo cargar el contador. Pulsa para reintentar.';}
  finally{busy=false;button.disabled=liked;}
 }
 button.addEventListener('click',async()=>{
  if(busy||liked)return;
  if(!loaded){await refresh();return;}
  busy=true;button.disabled=true;status.textContent='Guardando…';
  try{await query('POST');}
  catch{status.textContent='No se guardó tu Me gusta. Puedes intentarlo de nuevo.';}
  finally{busy=false;button.disabled=liked;}
 });
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
 window.addEventListener('pageshow',event=>{if(event.persisted)refresh();});
 refresh();
})();
