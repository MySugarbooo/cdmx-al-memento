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
// Foro compatible con las reglas actuales: preguntas y respuestas usan el campo text.
// Formato: [FORO:PREGUNTA] título\\ncontenido o [FORO:RESPUESTA:ID] contenido.
const questionPrefix='[FORO:PREGUNTA] ',replyPrefix='[FORO:RESPUESTA:';
let currentRows=[],activeQuestion=null,forumFilter='all',forumQuery='';
let liveRows=[],olderRows=new Map(),pageCursor=null,hasMore=false,loadingOlder=false;
const PAGE_SIZE=isCommunity?100:50;
const moreButton=document.getElementById('forum-load-more');
const forumNotice=document.getElementById('forum-search-note');
const editorLabel=document.querySelector('label[for="forum-question-title"]');
let previousSend=0;
const questionInput=document.getElementById('forum-question-title');
const forumFeed=document.getElementById('forum-topics');
const forumSearch=document.getElementById('forum-search');
const forumSort=document.getElementById('forum-sort');
const forumHeading=document.getElementById('forum-editor-heading');
const forumCancel=document.getElementById('forum-cancel-reply');
function decode(row){const c=row.data();const raw=String(c.text||'');const isQuestion=raw.startsWith(questionPrefix);const reply=raw.match(/^\[FORO:RESPUESTA:([a-zA-Z0-9]{8,40})\] /);const body=isQuestion?raw.slice(questionPrefix.length):reply?raw.slice(reply[0].length):raw;const newline=body.indexOf('\n');return {row,id:row.id,c,kind:isQuestion?'question':reply?'reply':'legacy',parent:reply?reply[1]:null,title:isQuestion?(newline<0?body:body.slice(0,newline)).trim().slice(0,110):'',body:isQuestion?(newline<0?'':body.slice(newline+1)):body};}
function updateLimit(){
 if(!isCommunity||!textarea)return;
 const prefix=activeQuestion?replyPrefix+activeQuestion.id+'] ':questionPrefix+(questionInput?.value.trim()||'')+'\n';
 const available=Math.max(2,1000-prefix.length);
 textarea.maxLength=available;
 const counter=document.getElementById('forum-length');
 if(counter)counter.textContent=textarea.value.length+' / '+available+' caracteres para este mensaje';
}
function clearReply(){
 activeQuestion=null;
 if(questionInput)questionInput.hidden=false;
 if(editorLabel)editorLabel.hidden=false;
 if(forumHeading)forumHeading.textContent='Haz una pregunta a la comunidad';
 if(forumCancel)forumCancel.hidden=true;
 if(textarea)textarea.placeholder='Explica tu pregunta o comparte un detalle que ayude a otros a responder…';
 updateLimit();
}
function promptSignIn(){
 status.textContent='Inicia sesión con Google para publicar o responder.';
 document.getElementById('cdmx-comments-login')?.scrollIntoView({block:'center',behavior:'smooth'});
 google?.focus();
}

function setReply(topic){
 activeQuestion=topic;
 if(questionInput)questionInput.hidden=true;
 if(editorLabel)editorLabel.hidden=true;
 if(forumHeading)forumHeading.textContent='Responder a: '+topic.title;
 if(forumCancel)forumCancel.hidden=false;
 if(textarea){textarea.value='';textarea.placeholder='Escribe una respuesta útil y respetuosa…';}
 updateLimit();
 editor.hidden=!user;
 if(!user){promptSignIn();return;}
 editor.scrollIntoView({block:'center',behavior:'smooth'});
 textarea?.focus();
}
forumCancel?.addEventListener('click',clearReply);
questionInput?.addEventListener('input',updateLimit);
textarea?.addEventListener('input',updateLimit);
root.querySelectorAll('[data-forum-topic]').forEach(button=>button.addEventListener('click',()=>{
 forumQuery=button.dataset.forumTopic.toLocaleLowerCase('es-MX');
 if(forumSearch)forumSearch.value=button.dataset.forumTopic;
 display(currentRows);
 document.getElementById('forum-search')?.scrollIntoView({block:'center',behavior:'smooth'});
}));
document.querySelectorAll('[data-open-forum-editor]').forEach(link=>link.addEventListener('click',event=>{
 event.preventDefault();
 if(!user){promptSignIn();return;}
 editor.hidden=false;editor.scrollIntoView({block:'center',behavior:'smooth'});questionInput?.focus();
}));
forumSearch?.addEventListener('input',()=>{forumQuery=forumSearch.value.trim().toLocaleLowerCase('es-MX');display(currentRows)});
forumSort?.addEventListener('change',()=>display(currentRows));
root.querySelectorAll('[data-forum-filter]').forEach(b=>b.addEventListener('click',()=>{forumFilter=b.dataset.forumFilter;root.querySelectorAll('[data-forum-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});display(currentRows)}));
function profileFor(topic){const c=topic.c;const profile=document.createElement('div');profile.className='community-profile';const avatar=document.createElement('span');avatar.className='community-avatar';const photo=String(c.photoURL||(user&&c.uid===user.uid?user.photoURL:'')||'');if(/^https:\/\//i.test(photo)&&photo.length<1500){const img=document.createElement('img');img.src=photo;img.alt='Foto de perfil';img.loading='lazy';img.referrerPolicy='no-referrer';img.onerror=()=>{img.remove();avatar.textContent=String(c.name||'L').charAt(0).toUpperCase()};avatar.append(img)}else avatar.textContent=String(c.name||'L').charAt(0).toUpperCase();const details=document.createElement('div');details.className='community-profile-details';const name=document.createElement('strong');name.textContent=String(c.name||'Lector').slice(0,80);const time=document.createElement('time');const stamp=c.createdAt?.toDate?.();time.textContent=stamp?new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'}).format(stamp):'Fecha pendiente';details.append(name,time);profile.append(avatar,details);return profile;}
let isModerator=false;
function ownDelete(topic){
 if(!user||(!isModerator&&topic.c.uid!==user.uid))return null;
 const button=document.createElement('button');
 button.type='button';button.className='secondary forum-delete';button.textContent='Eliminar';
 button.addEventListener('click',async()=>{
  const warning=topic.kind==='question'?'¿Eliminar tu pregunta? Las respuestas de otras personas seguirán disponibles.':'¿Eliminar esta publicación?';
  if(!window.confirm(warning))return;
  button.disabled=true;
  try{
   await fs.deleteDoc(topic.row.ref);
   olderRows.delete(topic.id);
   if(isCommunity)renderMerged();
   status.textContent='Publicación eliminada.';
  }catch(error){
   status.textContent='No fue posible eliminar: '+(error.code||'error de permisos')+'.';
  }finally{button.disabled=false}
 });
 return button;
}
function reportButton(topic){
 if(!isCommunity||!topic.row)return null;
 const box=document.createElement('span');box.className='forum-report-wrap';
 const button=document.createElement('button');button.type='button';button.className='secondary forum-report';button.textContent='Reportar';
 const editor=document.createElement('span');editor.className='forum-report-editor';editor.hidden=true;
 const select=document.createElement('select');select.setAttribute('aria-label','Motivo del reporte');
 for(const [value,label] of [['spam','Publicidad o spam'],['abuso','Acoso o insultos'],['privacidad','Información privada'],['desinformacion','Información engañosa'],['otro','Otro motivo']]){
  const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);
 }
 const submit=document.createElement('button');submit.type='button';submit.textContent='Enviar reporte';
 const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Cancelar';cancel.className='secondary';
 button.addEventListener('click',()=>{
  if(!user){promptSignIn();return}
  editor.hidden=!editor.hidden;if(!editor.hidden)select.focus();
 });
 cancel.addEventListener('click',()=>editor.hidden=true);
 submit.addEventListener('click',async()=>{
  if(!user){promptSignIn();return}
  submit.disabled=true;
  try{
   const reportId=user.uid+'_'+topic.id;
   await fs.setDoc(fs.doc(db,'community','main','reports',reportId),{
    uid:user.uid,commentId:topic.id,reason:select.value,createdAt:fs.serverTimestamp()
   });
   editor.hidden=true;button.disabled=true;button.textContent='Reportado';
   status.textContent='Reporte recibido para revisión. Gracias por avisar.';
  }catch(error){
   status.textContent=error.code==='permission-denied'?
    'No se pudo enviar el reporte. Es necesario activar las nuevas reglas de seguridad de Firebase, o ya reportaste este mensaje.':
    'No se pudo enviar el reporte ('+(error.code||'error')+').';
  }finally{submit.disabled=false}
 });
 editor.append(select,submit,cancel);box.append(button,editor);return box;
}
function renderMerged(){
 const all=new Map();
 for(const row of liveRows)all.set(row.id,row);
 for(const [id,row] of olderRows)if(!all.has(id))all.set(id,row);
 const rows=[...all.values()].sort((a,b)=>{
  const aa=a.data().createdAt?.toMillis?.()||0,bb=b.data().createdAt?.toMillis?.()||0;
  return bb-aa;
 });
 display(rows);
 if(moreButton){moreButton.hidden=!isCommunity||!hasMore;moreButton.disabled=loadingOlder;moreButton.textContent=loadingOlder?'Cargando…':'Cargar conversaciones anteriores'}
 if(forumNotice)forumNotice.textContent='Búsqueda y contadores sobre '+rows.length+' mensajes cargados. Puedes cargar conversaciones anteriores.';
}
async function loadOlder(){
 if(!isCommunity||loadingOlder||!hasMore||!pageCursor)return;
 loadingOlder=true;renderMerged();
 try{
  const q=fs.query(collection,fs.orderBy('createdAt','desc'),fs.startAfter(pageCursor),fs.limit(PAGE_SIZE));
  const snap=await fs.getDocs(q);
  for(const row of snap.docs)olderRows.set(row.id,row);
  if(snap.docs.length)pageCursor=snap.docs[snap.docs.length-1];
  hasMore=snap.docs.length===PAGE_SIZE;
  status.textContent=snap.docs.length?'Se agregaron '+snap.docs.length+' mensajes anteriores.':'No hay más conversaciones para cargar.';
 }catch(error){status.textContent='No se pudieron cargar mensajes anteriores ('+(error.code||'error')+').'}
 finally{loadingOlder=false;renderMerged()}
}
moreButton?.addEventListener('click',loadOlder);
function display(rows){
 currentRows=rows;list.replaceChildren();
 if(!isCommunity){
  for(const row of rows){const topic=decode(row);const li=document.createElement('li');li.append(profileFor(topic));
   const p=document.createElement('p');p.textContent=topic.body;li.append(p);
   const remove=ownDelete(topic);if(remove)li.append(remove);list.append(li)
  }
  if(!rows.length){const li=document.createElement('li');li.textContent='Todavía no hay comentarios.';list.append(li)}
  return;
 }
 if(forumFeed)forumFeed.replaceChildren();
 const items=rows.map(decode),topics=items.filter(x=>x.kind==='question'),
  replies=items.filter(x=>x.kind==='reply'),legacy=items.filter(x=>x.kind==='legacy');
 const topicMap=new Map(topics.concat(legacy).map(t=>[t.id,t]));
 const replyMap=new Map();
 for(const reply of replies){
  if(!replyMap.has(reply.parent))replyMap.set(reply.parent,[]);
  replyMap.get(reply.parent).push(reply);
 }
 const count=document.getElementById('forum-count');
 if(count)count.textContent=topics.length+' preguntas · '+replies.length+' respuestas · '+legacy.length+' conversaciones anteriores (cargadas)';
 const allTopics=topics.concat(legacy.map(x=>({...x,kind:'legacy',title:x.body.slice(0,90)})));
 const orphanGroups=[...replyMap.entries()]
  .filter(([id])=>!topicMap.has(id))
  .map(([parent,answers])=>({id:'orphan-'+parent,kind:'orphan',parent,
   title:'Pregunta eliminada o pendiente de cargar',body:'Las respuestas se conservan para no perder la conversación.',
   c:{name:'Comunidad',uid:''},answers}));
 const counts=new Map(allTopics.map(t=>[t.id,(replyMap.get(t.id)||[]).length]));
 const shown=allTopics.concat(orphanGroups).filter(t=>{
  const responses=t.kind==='orphan'?t.answers.length:counts.get(t.id)||0;
  const text=(t.title+' '+t.body+' '+String(t.c.name||'')+' '+
   (replyMap.get(t.id)||t.answers||[]).map(r=>r.body).join(' ')).toLocaleLowerCase('es-MX');
  return (!forumQuery||text.includes(forumQuery)) &&
   (forumFilter==='all'||forumFilter==='unanswered'&&responses===0||forumFilter==='answered'&&responses>0);
 });
 if(forumSort?.value==='popular')shown.sort((a,b)=>
  (b.kind==='orphan'?b.answers.length:counts.get(b.id)||0)-
  (a.kind==='orphan'?a.answers.length:counts.get(a.id)||0));
 if(!shown.length){
  const li=document.createElement('li');li.className='forum-empty';
  li.textContent=allTopics.length||orphanGroups.length?'No hay conversaciones que coincidan con el filtro.':'Todavía no hay preguntas. ¡Inicia la conversación!';
  list.append(li);return;
 }
 for(const topic of shown){
  const li=document.createElement('li');li.className='forum-topic';li.id='post-'+topic.id;
  const related=topic.kind==='orphan'?topic.answers:replyMap.get(topic.id)||[];
  const head=document.createElement('div');head.className='forum-topic-head';
  const badge=document.createElement('span');badge.className='forum-topic-badge';
  badge.textContent=topic.kind==='legacy'?'Conversación':topic.kind==='orphan'?'Respuestas conservadas':'Pregunta';
  const countBadge=document.createElement('span');countBadge.className='forum-reply-count';
  countBadge.textContent=related.length+' '+(related.length===1?'respuesta':'respuestas');
  head.append(badge,countBadge);
  const title=document.createElement('h3');title.className='forum-topic-title';
  title.textContent=topic.title||'Conversación de la comunidad';
  const body=document.createElement('p');body.className='forum-topic-body';body.textContent=topic.body;
  li.append(head,title);
  if(topic.kind!=='orphan')li.append(profileFor(topic));
  li.append(body);
  if(topic.kind!=='orphan'){
   const actions=document.createElement('div');actions.className='forum-actions';
   const respond=document.createElement('button');respond.type='button';
   respond.className='community-mention';respond.textContent='↩ Responder';respond.onclick=()=>setReply(topic);actions.append(respond);
   const del=ownDelete(topic);if(del)actions.append(del);
   const report=reportButton(topic);if(report)actions.append(report);
   li.append(actions);
  }
  if(related.length){
   const thread=document.createElement('div');thread.className='forum-thread';
   thread.setAttribute('aria-label','Respuestas a '+topic.title);
   for(const answer of related.slice().reverse()){
    const answerBox=document.createElement('div');answerBox.className='forum-answer';answerBox.id='post-'+answer.id;
    answerBox.append(profileFor(answer));
    const p=document.createElement('p');p.textContent=answer.body;answerBox.append(p);
    const acts=document.createElement('div');acts.className='forum-actions';
    const remove=ownDelete(answer);if(remove)acts.append(remove);
    const report=reportButton(answer);if(report)acts.append(report);
    answerBox.append(acts);thread.append(answerBox);
   }
   li.append(thread);
  }
  list.append(li);
 }
}
mod.onAuthStateChanged(auth,person=>{
 user=person;
 login.hidden=!!person;editor.hidden=!person;signout.hidden=!person;
 if(person){status.textContent='Participas como '+(person.displayName||'usuario autenticado')+'. Tu nombre, foto de perfil y comentarios son públicos.';}
 else status.textContent='Inicia sesión con Google o Facebook para comentar. Tu comentario, nombre y foto de perfil de Google serán públicos.';
 if(unsubscribe){unsubscribe();unsubscribe=null;}
 const q=fs.query(collection,fs.orderBy('createdAt','desc'),fs.limit(isCommunity?200:50));
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
 const message=textarea.value.trim();
 const title=questionInput?.value.trim()||'';
 const text=isCommunity?(activeQuestion?replyPrefix+activeQuestion.id+'] '+message:questionPrefix+title+'\n'+message):message;
 if(!user||message.length<2||text.length>1000||(isCommunity&&!activeQuestion&&(title.length<8||title.length>110))){status.textContent=isCommunity?'Escribe un título de 8 a 110 caracteres y un mensaje válido (máximo 1000 caracteres en total).':'Escribe un comentario de 2 a 1000 caracteres.';return;}
 send.disabled=true;
 try{
  const payload={uid:user.uid,name:(user.displayName||'Lector').slice(0,80),text,createdAt:fs.serverTimestamp()};
  // Compatibilidad con reglas antiguas de Firestore: permiten solo cuatro campos.
  // Guardar photoURL sin actualizar reglas produce permission-denied.
  await fs.addDoc(collection,payload);
  textarea.value='';if(questionInput)questionInput.value='';clearReply();status.textContent=isCommunity?'Publicación enviada correctamente.':'Comentario publicado correctamente.';
 }catch(error){console.error('Error al publicar comentario:',error);status.textContent='No se pudo publicar ('+(error.code||'error desconocido')+'). '+(error.code==='permission-denied'?'La base de datos rechazó el permiso. Comprueba las reglas publicadas de Firestore.':'Comprueba tu conexión e inténtalo de nuevo.');}
 finally{send.disabled=false;}
};
})();
