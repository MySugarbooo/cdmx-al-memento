/* CDMX AL MEMENTO · perfiles públicos basados solo en publicaciones visibles.
   Sin documentos de perfiles ni permisos nuevos de Firebase.
   Contadores sobre actividad consultada, con paginación manual. */
(async()=>{
'use strict';
const $=id=>document.getElementById(id);
const status=$('profile-status'),name=$('profile-name'),subtitle=$('profile-subtitle');
const avatar=$('profile-avatar'),filter=$('profile-filter'),list=$('profile-list'),more=$('profile-more');
if(!status||!name||!subtitle||!avatar||!filter||!list||!more)return;
const params=new URLSearchParams(location.search);
const requested=String(params.get('uid')||'');
const uidPattern=/^[A-Za-z0-9_-]{8,128}$/;
if(requested&&!uidPattern.test(requested)){
 name.textContent='Perfil no disponible';status.textContent='El enlace del perfil no es válido.';
 list.replaceChildren();more.hidden=true;return;
}
const config=window.CDMX_COMMENTS_FIREBASE;
if(!config||!config.apiKey||!config.projectId||!config.appId||!config.authDomain){
 name.textContent='Perfil temporalmente no disponible';
 status.textContent='Falta la configuración de la comunidad.';
 list.replaceChildren();return;
}
let fs,db,auth,authApi;
try{
 const [appApi,firestore,authentication]=await Promise.all([
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js'),
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js'),
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js')
 ]);
 fs=firestore;authApi=authentication;
 const app=appApi.getApps().find(x=>x.name==='cdmx-public-profiles')||
  appApi.initializeApp(config,'cdmx-public-profiles');
 db=fs.getFirestore(app);auth=authApi.getAuth(app);
}catch(error){
 name.textContent='No se pudo cargar el perfil';
 status.textContent='No fue posible conectar con la comunidad. Inténtalo de nuevo.';
 list.replaceChildren();return;
}
const posts=fs.collection(db,'community','main','comments');
const PAGE_SIZE=40;
const rows=new Map();
const fmt=new Intl.DateTimeFormat('es-MX',{
 timeZone:'America/Mexico_City',dateStyle:'medium',timeStyle:'short'
});
const questionPrefix='[FORO:PREGUNTA] ';
const replyExpression=/^\[FORO:RESPUESTA:([a-zA-Z0-9]{8,40})\] /;
let targetUid='',cursor=null,hasMore=false,loading=false,ownUser=null,run=0;
function make(tag,cls,content){
 const el=document.createElement(tag);
 if(cls)el.className=cls;
 if(content!==undefined)el.textContent=content;
 return el;
}
function decode(doc){
 const data=doc.data();
 const raw=String(data.text||'');
 const question=raw.startsWith(questionPrefix),reply=raw.match(replyExpression);
 const body=question?raw.slice(questionPrefix.length):reply?raw.slice(reply[0].length):raw;
 const newline=body.indexOf('\n');
 const type=question?'question':reply?'reply':'legacy';
 const title=question?(newline>=0?body.slice(0,newline):body).trim().slice(0,110)
  :type==='reply'?'Respuesta en Mi comunidad':body.trim().slice(0,90);
 const text=question?(newline>=0?body.slice(newline+1):''):body;
 return {id:doc.id,type,title,text,data,parent:reply?reply[1]:null,
  timestamp:typeof data.createdAt?.toMillis==='function'?data.createdAt.toMillis():0};
}
function safePhoto(url){
 if(typeof url!=='string'||url.length>1500)return '';
 try{
  const u=new URL(url);
  return u.protocol==='https:'?u.href:'';
 }catch{return ''}
}
function setAvatar(photo,display){
 avatar.replaceChildren();
 const safe=safePhoto(photo);
 if(!safe){avatar.textContent=String(display||'L').trim().slice(0,1).toUpperCase()||'L';return;}
 const img=make('img');img.alt='';img.loading='lazy';img.referrerPolicy='no-referrer';img.src=safe;
 img.addEventListener('error',()=>{avatar.textContent=String(display||'L').slice(0,1).toUpperCase()||'L';img.remove()});
 avatar.append(img);
}
function render(){
 const entries=[...rows.values()].sort((a,b)=>b.timestamp-a.timestamp||b.id.localeCompare(a.id));
 const questions=entries.filter(x=>x.type==='question').length;
 const replies=entries.filter(x=>x.type==='reply').length;
 const legacy=entries.filter(x=>x.type==='legacy').length;
 $('profile-question-count').textContent=String(questions);
 $('profile-reply-count').textContent=String(replies);
 $('profile-legacy-count').textContent=String(legacy);
 $('profile-total-count').textContent=String(entries.length);
 const recent=entries.find(x=>String(x.data.name||'').trim()||safePhoto(x.data.photoURL));
 const display=String(recent?.data.name|| (ownUser?.uid===targetUid?ownUser.displayName:'')||'Lector').slice(0,80);
 name.textContent=display;
 document.title=display+' · Perfil público | CDMX AL MEMENTO';
 setAvatar(recent?.data.photoURL||(ownUser?.uid===targetUid?ownUser.photoURL:''),display);
 subtitle.textContent=entries.length?
  'Preguntas y respuestas compartidas públicamente en Mi comunidad.':
  'Esta cuenta todavía no tiene mensajes públicos disponibles en el foro.';
 const show=entries.filter(x=>filter.value==='all'||x.type===filter.value);
 list.replaceChildren();
 if(!show.length){
  list.append(make('li','profiles-empty',entries.length?
   'No hay publicaciones de este tipo entre los mensajes consultados.':
   'No se encontraron publicaciones públicas de esta cuenta.'));
 }
 for(const item of show){
  const card=make('li','profiles-post');
  const label={question:'Pregunta',reply:'Respuesta',legacy:'Conversación'}[item.type]||'Mensaje';
  card.append(make('span','profiles-post-type',label));
  const time=make('time','',item.timestamp?fmt.format(new Date(item.timestamp)):'Fecha pendiente');
  if(item.timestamp)time.dateTime=new Date(item.timestamp).toISOString();
  card.append(time);
  card.append(make('h3','',item.title||label));
  if(item.text)card.append(make('p','',item.text.slice(0,1000)));
  if(/^[a-zA-Z0-9]{20}$/.test(item.id)){
   const a=make('a','','Abrir en Mi comunidad');
   a.href='/comunidad/#post-'+item.id;
   a.title='En mensajes antiguos puede ser necesario pulsar Cargar conversaciones anteriores en el foro';
   card.append(a);
  }
  list.append(card);
 }
 more.hidden=!hasMore;
 more.disabled=loading;
 more.textContent=loading?'Consultando publicaciones…':'Cargar más publicaciones';
 status.textContent=entries.length?
  entries.length+' mensajes consultados de este perfil'+(hasMore?' · Hay más publicaciones disponibles.':'.'):
  'Sin mensajes públicos registrados en la consulta.';
}
async function loadPage(){
 if(loading||!targetUid||!uidPattern.test(targetUid))return;
 loading=true;more.disabled=true;
 status.textContent='Consultando las publicaciones públicas…';
 const version=run;
 try{
  const constraints=[fs.where('uid','==',targetUid),fs.limit(PAGE_SIZE)];
  if(cursor)constraints.push(fs.startAfter(cursor));
  const snap=await fs.getDocs(fs.query(posts,...constraints));
  if(version!==run)return;
  for(const doc of snap.docs)rows.set(doc.id,decode(doc));
  cursor=snap.docs[snap.docs.length-1]||null;
  hasMore=snap.docs.length===PAGE_SIZE;
  render();
 }catch(error){
  if(version!==run)return;
  status.textContent=error.code==='failed-precondition'?
   'La búsqueda requiere habilitar un índice de Firestore. El foro sigue disponible.':
   'No pudimos consultar este perfil ('+(error.code||'conexión')+'). Inténtalo de nuevo.';
  if(!rows.size){list.replaceChildren();list.append(make('li','','No se pudieron cargar los mensajes.'));}
  more.hidden=false;more.textContent='Reintentar consulta';
 }finally{if(version===run){loading=false;more.disabled=false}}
}
function openProfile(uid){
 if(!uidPattern.test(uid))return;
 run++;targetUid=uid;rows.clear();cursor=null;hasMore=false;loading=false;
 name.textContent='Consultando perfil…';subtitle.textContent='Publicaciones públicas del foro';
 avatar.textContent='?';list.replaceChildren();
 $('profile-question-count').textContent='—';$('profile-reply-count').textContent='—';
 $('profile-legacy-count').textContent='—';$('profile-total-count').textContent='—';
 more.hidden=true;loadPage();
}
filter.addEventListener('change',()=>{if(targetUid)render()});
more.addEventListener('click',loadPage);
if(requested){
 openProfile(requested);
}else{
 name.textContent='Mi perfil';
 subtitle.textContent='Inicia sesión en Mi comunidad para ver tus publicaciones públicas.';
 list.replaceChildren();
 more.hidden=true;
 authApi.onAuthStateChanged(auth,person=>{
  ownUser=person;
  if(person)openProfile(person.uid);
  else{
   run++;targetUid='';rows.clear();
   name.textContent='Mi perfil';setAvatar('','?');
   status.textContent='No has iniciado sesión. Entra a Mi comunidad para acceder a tu perfil.';
   list.replaceChildren();
   const li=make('li','','Puedes iniciar sesión con Google desde Mi comunidad.');
   const a=make('a','','Ir al foro');a.href='/comunidad/';
   li.append(make('p'),a);list.append(li);
  }
 });
}
})();
