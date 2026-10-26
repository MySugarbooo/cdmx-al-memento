/* Comentarios por noticia con Firebase Auth + Firestore.
   Sin configuración, la interfaz avisa claramente y NO simula envíos. */
(async()=>{
'use strict';
const root=document.getElementById('cdmx-comments');
if(!root)return;
const status=document.getElementById('cdmx-comments-status');
const login=document.getElementById('cdmx-comments-login');
const editor=document.getElementById('cdmx-comments-editor');
const list=document.getElementById('cdmx-comments-list');
const send=document.getElementById('cdmx-comments-send');
const textarea=document.getElementById('cdmx-comments-text');
const signout=document.getElementById('cdmx-comments-logout');
const google=document.getElementById('cdmx-comments-google');
const facebook=document.getElementById('cdmx-comments-facebook');
const isCommunity=root.dataset.commentsScope==='community';
const params=new URLSearchParams(location.search);
const id=params.get('id'),month=params.get('mes');
if(!isCommunity&&(!/^[a-f0-9]{20}$/.test(id||'')||!/^20\d\d-(0[1-9]|1[0-2])$/.test(month||''))){
 status.textContent='Abre una noticia concreta para consultar sus comentarios.';login.hidden=true;return;
}
const cfg=window.CDMX_COMMENTS_FIREBASE;
if(!cfg||!cfg.apiKey||!cfg.authDomain||!cfg.projectId||!cfg.appId){
 status.textContent='Los comentarios están preparados, pero falta conectar Google y Facebook en la configuración del sitio.';
 login.hidden=true;return;
}
let auth,db,mod,fs,user=null,unsubscribe=null;
try{
 [mod,fs]=await Promise.all([
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js'),
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js')
 ]);
 const appmod=await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js');
 const app=appmod.initializeApp(cfg,'cdmx-comments');
 auth=mod.getAuth(app);db=fs.getFirestore(app);
 await mod.getRedirectResult(auth);
}catch(e){status.textContent='No se pudo conectar el servicio de comentarios. Inténtalo más tarde.';login.hidden=true;return;}
const collection=isCommunity?fs.collection(db,'community','main','comments'):fs.collection(db,'articles',month+'_'+id,'comments');
function display(rows){
 list.replaceChildren();
 if(!rows.length){const li=document.createElement('li');li.textContent='Todavía no hay comentarios. Sé la primera persona en participar.';list.append(li);return;}
 for(const row of rows){
  const c=row.data(),li=document.createElement('li');
  const name=document.createElement('strong');name.textContent=String(c.name||'Lector').slice(0,80);
  const time=document.createElement('time');
  const stamp=c.createdAt?.toDate?.();
  time.textContent=stamp?new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'}).format(stamp):'Fecha pendiente';
  const p=document.createElement('p');p.textContent=String(c.text||'').slice(0,1000);
  li.append(name,time,p);
  if(user&&c.uid===user.uid){
   const remove=document.createElement('button');remove.className='secondary';remove.type='button';remove.textContent='Eliminar mi comentario';
   remove.onclick=async()=>{if(!confirm('¿Eliminar tu comentario?'))return;remove.disabled=true;try{await fs.deleteDoc(row.ref)}catch{status.textContent='No fue posible eliminar el comentario.'}finally{remove.disabled=false}};
   li.append(remove);
  }
  list.append(li);
 }
}
mod.onAuthStateChanged(auth,person=>{
 user=person;
 login.hidden=!!person;editor.hidden=!person;signout.hidden=!person;
 if(person){status.textContent='Participas como '+(person.displayName||'usuario autenticado')+'. Los comentarios son públicos.';}
 else status.textContent='Inicia sesión con Google o Facebook para comentar. Tu comentario y nombre serán públicos.';
 if(unsubscribe){unsubscribe();unsubscribe=null;}
 const q=fs.query(collection,fs.orderBy('createdAt','desc'),fs.limit(50));
 unsubscribe=fs.onSnapshot(q,snapshot=>display(snapshot.docs),error=>{status.textContent='No se pudieron cargar los comentarios ('+(error.code||'error')+'). Revisa las reglas de Firestore.';});
});
async function authenticate(provider){
 try{
  status.textContent='Conectando con tu cuenta…';
  await mod.signInWithPopup(auth,provider);
 }catch(error){
  if(error?.code==='auth/popup-blocked'||error?.code==='auth/cancelled-popup-request'){
   try{await mod.signInWithRedirect(auth,provider);return}catch{}
  }
  status.textContent='No se pudo iniciar sesión. Revisa que el proveedor esté habilitado y permite ventanas emergentes.';
 }
}
google.onclick=()=>authenticate(new mod.GoogleAuthProvider());
// Facebook requiere una aplicación Meta habilitada.
if(facebook)facebook.hidden=true;
signout.onclick=()=>mod.signOut(auth);
send.onclick=async()=>{
 const text=textarea.value.trim();
 if(!user||text.length<2||text.length>1000){status.textContent='Escribe un comentario de 2 a 1000 caracteres.';return;}
 send.disabled=true;
 try{
  await fs.addDoc(collection,{uid:user.uid,name:(user.displayName||'Lector').slice(0,80),text,createdAt:fs.serverTimestamp()});
  textarea.value='';status.textContent='Comentario publicado correctamente.';
 }catch(error){console.error('Error al publicar comentario:',error);status.textContent='No se pudo publicar ('+(error.code||'error desconocido')+'). '+(error.code==='permission-denied'?'La base de datos rechazó el permiso; vuelve a iniciar sesión e inténtalo.':'Comprueba tu conexión e inténtalo de nuevo.');}
 finally{send.disabled=false;}
};
})();
