'use strict';
/* Transiciones entre páginas: desplazamiento perceptible sin bloquear enlaces.
 * Respeta reduce motion, navegación con teclado, enlaces externos y volver atrás.
 */
(()=>{
 const KEY='cdmx.memento.page-slide.v1';
 const reduced=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches===true;
 const routeOrder=['/','/alcaldias/','/mapa/','/archivo/','/reportes/','/guias/','/cerca/','/movilidad/','/avisos/','/favoritos/','/descubre/','/agenda/','/negocios/','/herramientas/'];
 const rank=path=>{
  const i=routeOrder.findIndex(base=>base==='/'?path==='/':path.startsWith(base));
  return i<0?routeOrder.length:i;
 };
 let leaving=false,exitAnimation=null,entryAnimation=null;
 const root=document.querySelector('main');
 function resetExit(){
  leaving=false;
  if(exitAnimation){exitAnimation.cancel();exitAnimation=null;}
 }
 window.addEventListener('pageshow',resetExit);
 if(!root)return;
 // Al llegar a una página interna, recuperar la dirección de la visita anterior.
 try{
  const record=JSON.parse(sessionStorage.getItem(KEY)||'null');
  sessionStorage.removeItem(KEY);
  if(record&&record.to===location.pathname&&Date.now()-record.at<8000&&!reduced()&&typeof root.animate==='function'){
   const dir=record.dir===-1?-1:1;
   entryAnimation=root.animate([
    {opacity:.12,transform:'translate3d('+(dir*48)+'px,0,0)'},
    {opacity:1,transform:'translate3d(0,0,0)'}
   ],{duration:380,easing:'cubic-bezier(.18,.75,.25,1)',fill:'both'});
   entryAnimation.onfinish=()=>{entryAnimation.cancel();entryAnimation=null;};
  }
 }catch{/* La animación es opcional; la navegación no debe fallar. */}
 document.addEventListener('click',event=>{
  if(leaving||event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  const a=event.target.closest?.('a[href]');
  if(!a||a.hasAttribute('download')||(a.target&&a.target!=='_self')||a.hasAttribute('data-filter'))return;
  let target;
  try{target=new URL(a.href,location.href)}catch{return;}
  if(target.origin!==location.origin||!/^https?:$/.test(target.protocol)||target.pathname===location.pathname)return;
  if(/\.(?:json|xml|txt|jpg|png|webp|svg|pdf|mp4|css|js)$/i.test(target.pathname)||target.pathname.startsWith('/api/'))return;
  if(reduced()||typeof root.animate!=='function')return;
  event.preventDefault();
  leaving=true;
  entryAnimation?.cancel();
  const dir=rank(target.pathname)<rank(location.pathname)?-1:1;
  try{sessionStorage.setItem(KEY,JSON.stringify({from:location.pathname,to:target.pathname,dir,at:Date.now()}))}catch{}
  let done=false;
  const navigate=()=>{
   if(done)return;
   done=true;
   window.location.assign(target.href);
  };
  exitAnimation=root.animate([
   {opacity:1,transform:'translate3d(0,0,0)'},
   {opacity:.12,transform:'translate3d('+(-dir*48)+'px,0,0)'}
  ],{duration:190,easing:'cubic-bezier(.45,0,.85,.4)',fill:'both'});
  exitAnimation.onfinish=navigate;
  window.setTimeout(navigate,280); // Nunca retener la navegación si el navegador pausa la animación.
 },true);
})();
