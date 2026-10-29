/* CDMX AL MEMENTO · moderación avanzada
   El token firmado decide permisos, no los estilos de la página.
   La auditoría registra acciones en una transacción si las reglas ya están activas.
   Conserva las acciones anteriores en un modo de compatibilidad explícito.
*/
import {initializeApp} from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
import {
 getAuth,onAuthStateChanged,GoogleAuthProvider,signInWithPopup,signInWithRedirect,
 getRedirectResult,signOut,getIdTokenResult
} from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';
import {
 getFirestore,collection,doc,getDoc,getDocs,query,orderBy,limit,
 runTransaction,serverTimestamp,deleteDoc
} from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js';

const $=id=>document.getElementById(id);
const status=$('status'),login=$('login'),logout=$('logout'),refresh=$('refresh');
const privateArea=$('private'),reports=$('reports'),history=$('history'),historyStatus=$('history-status');
const identity=$('identity'),identityPhoto=$('identity-photo'),identityName=$('identity-name'),identityRole=$('identity-role');
const reportReason=$('reports-reason'),reportQuery=$('reports-search'),reportSort=$('reports-sort');
const histAction=$('history-action'),histQuery=$('history-search'),historyRefresh=$('history-refresh');
const pendingStat=$('stat-pending'),uniqueStat=$('stat-unique'),repeatedStat=$('stat-repeated');
const cfg=window.CDMX_COMMENTS_FIREBASE;
if(!cfg?.apiKey||!cfg?.authDomain||!cfg?.projectId||!cfg?.appId){
 status.textContent='Falta la configuración pública de Firebase.';
 throw Error('Firebase no configurado');
}
const app=initializeApp(cfg,'cdmx-moderation'),auth=getAuth(app),db=getFirestore(app);
const reportCollection=collection(db,'community','main','reports');
const auditCollection=collection(db,'community','main','moderationActions');
const allowedReasons={spam:'Publicidad o spam',abuso:'Acoso o insultos',privacidad:'Información privada',desinformacion:'Información engañosa',otro:'Otro motivo'};
const validComment=id=>/^[a-zA-Z0-9]{20}$/.test(id);
let isModerator=false,generation=0,activeReportDocs=[],activeHistoryDocs=[];
let auditMode='checking',reportRefreshBusy=false,historyRefreshBusy=false;
const timeFormat=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'medium',timeStyle:'short'});
function printableTime(value){
 try{const date=value?.toDate?.();return date&&!Number.isNaN(date.getTime())?timeFormat.format(date):'Fecha pendiente';}
 catch{return 'Fecha pendiente';}
}
function el(tag,text,cls){
 const node=document.createElement(tag);
 if(text!==undefined&&text!==null)node.textContent=String(text);
 if(cls)node.className=cls;
 return node;
}
function canAct(viewer){
 return isModerator&&viewer&&auth.currentUser===viewer;
}
function resetPrivate(){
 activeReportDocs=[];activeHistoryDocs=[];reports.replaceChildren();history.replaceChildren();
 pendingStat.textContent='—';uniqueStat.textContent='—';repeatedStat.textContent='—';
 auditMode='checking';refresh.hidden=true;historyRefresh.hidden=true;
 privateArea.hidden=true;isModerator=false;
}
function reportMatch(row){
 const data=row.data(),needle=reportQuery.value.trim().toLocaleLowerCase('es-MX');
 if(reportReason.value&&data.reason!==reportReason.value)return false;
 if(!needle)return true;
 return [row.id,data.reason,data.commentId,data.uid,...(row._display||[])].join(' ').toLocaleLowerCase('es-MX').includes(needle);
}
function recordCounts(){
 const counts=new Map();
 for(const row of activeReportDocs){
  const id=String(row.data().commentId||'');
  counts.set(id,(counts.get(id)||0)+1);
 }
 pendingStat.textContent=String(activeReportDocs.length);
 uniqueStat.textContent=String(counts.size);
 repeatedStat.textContent=String([...counts.values()].filter(x=>x>1).length);
 return counts;
}
function currentReportView(){
 const counts=recordCounts();
 const rows=activeReportDocs.filter(reportMatch);
 if(reportSort.value==='most'){
  rows.sort((a,b)=>(counts.get(b.data().commentId)||0)-(counts.get(a.data().commentId)||0)
   ||(b.data().createdAt?.toMillis?.()||0)-(a.data().createdAt?.toMillis?.()||0));
 }
 return {rows,counts};
}
function setAuditStatus(){
 const state=$('audit-state');
 if(!state)return;
 if(auditMode==='enabled'){
  state.textContent='Historial privado activo: las decisiones tomadas en este panel se guardarán con fecha y cuenta moderadora.';
 }else if(auditMode==='checking'){
  state.textContent='Comprobando si las reglas del historial ya están activadas…';
 }else{
  state.textContent='Historial no habilitado en Firebase. El panel conservará la moderación anterior, pero cada decisión sin historial requerirá una advertencia adicional.';
 }
}
async function loadReports(){
 const viewer=auth.currentUser,serial=generation;
 if(!canAct(viewer)||reportRefreshBusy)return;
 reportRefreshBusy=true;refresh.disabled=true;
 status.textContent='Actualizando reportes…';
 try{
  const snap=await getDocs(query(reportCollection,orderBy('createdAt','desc'),limit(50)));
  if(serial!==generation||!canAct(viewer))return;
  // Envoltorios propios: no modificamos objetos internos del SDK de Firestore.
  const data=snap.docs.map(row=>({
   id:row.id,ref:row.ref,data:()=>row.data(),_post:null,_display:[]
  }));
  // Consulta progresiva: máximo ocho lecturas de publicaciones a la vez.
  for(let i=0;i<data.length;i+=8){
   const batch=data.slice(i,i+8);
   await Promise.all(batch.map(async report=>{
    const id=String(report.data().commentId||'');
    if(!validComment(id)){report._display=['Identificador inválido'];report._post=null;return;}
    try{
     const result=await getDoc(doc(db,'community','main','comments',id));
     report._post=result.exists()?result.data():null;
     report._display=report._post?[String(report._post.name||''),String(report._post.text||'')]:['Publicación ya eliminada'];
    }catch(error){
     report._post=null;
     report._display=['No se pudo consultar el mensaje'];
    }
   }));
   if(serial!==generation||!canAct(viewer))return;
  }
  activeReportDocs=data;
  renderReports();
  status.textContent=snap.size+' reportes recientes consultados. Se muestran como máximo 50.';
 }catch(error){
  if(serial===generation)status.textContent='No fue posible cargar reportes ('+(error.code||'error')+').';
 }finally{
  reportRefreshBusy=false;if(serial===generation)refresh.disabled=false;
 }
}
function renderReports(){
 reports.replaceChildren();
 const {rows,counts}=currentReportView();
 if(!rows.length){
  reports.append(el('p',activeReportDocs.length?'No hay reportes que coincidan con los filtros.':'No hay reportes pendientes.','mod-empty'));
  return;
 }
 for(const report of rows){
  const data=report.data(),id=String(data.commentId||''),viewer=auth.currentUser;
  const card=el('article',undefined,'mod-card');
  card.append(el('h3',allowedReasons[data.reason]||'Motivo no especificado'));
  card.append(el('small','Reportado: '+printableTime(data.createdAt)+' · Publicación '+id));
  const repeat=counts.get(id)||0;
  if(repeat>1)card.append(el('span',repeat+' reportes recientes para esta publicación (no confirma una infracción)','mod-repeat'));
  if(report._post){
   const author=el('p','Autor: '+String(report._post.name||'Sin nombre').slice(0,80),'mod-author');
   const text=el('p',String(report._post.text||'').slice(0,1000));
   card.append(author,text,el('small','Publicado: '+printableTime(report._post.createdAt)));
  }else card.append(el('p',validComment(id)?'Publicación eliminada o no disponible.':'Identificador inválido.'));
  const noteLabel=el('label','Nota interna de la decisión (opcional, máximo 240 caracteres)','mod-note-label');
  const note=el('textarea');note.maxLength=240;note.rows=2;
  note.placeholder='Ej.: no constituye spam; publicación revisada conforme a las normas.';
  note.id='mod-note-'+report.id;noteLabel.htmlFor=note.id;
  card.append(noteLabel,note);
  const error=el('p','', 'mod-error');error.setAttribute('role','status');card.append(error);
  const buttons=el('div',undefined,'mod-actions-row');
  const open=el('a','Abrir en el foro');open.href='/comunidad/#post-'+encodeURIComponent(id);
  if(!validComment(id))open.hidden=true;
  const dismiss=el('button','Descartar reporte','secondary');
  const remove=el('button','Eliminar publicación');
  remove.disabled=!validComment(id)||!report._post;
  dismiss.disabled=auditMode==='checking';
  if(auditMode==='checking')remove.disabled=true;
  dismiss.type='button';remove.type='button';
  dismiss.addEventListener('click',()=>decide(report,'dismiss',note.value,card,error,dismiss,remove,viewer));
  remove.addEventListener('click',()=>decide(report,'remove',note.value,card,error,dismiss,remove,viewer));
  buttons.append(open,dismiss,remove);card.append(buttons);reports.append(card);
 }
}
async function decide(report,action,rawNote,card,error,dismiss,remove,viewer){
 if(!canAct(viewer)||auditMode==='checking')return;
 const commentId=String(report.data().commentId||'');
 if(action==='remove'&&!validComment(commentId))return;
 const label=action==='dismiss'?'descartar el reporte SIN retirar la publicación':'eliminar definitivamente la publicación y cerrar este reporte';
 const compat=auditMode!=='enabled';
 const warning='¿Confirmas que deseas '+label+'?'+
  (compat?'\n\nATENCIÓN: aún no está activo el historial; esta decisión no quedará registrada.':'\n\nLa decisión quedará registrada en el historial privado.');
 if(!window.confirm(warning))return;
 const note=String(rawNote||'').trim().slice(0,240);
 dismiss.disabled=true;remove.disabled=true;error.textContent='';
 try{
  if(compat){
   // Las reglas antiguas conservan el funcionamiento existente.
   if(action==='remove')await deleteDoc(doc(db,'community','main','comments',commentId));
   await deleteDoc(report.ref);
  }else{
   const auditRef=doc(auditCollection);
   const postRef=doc(db,'community','main','comments',commentId);
   await runTransaction(db,async tx=>{
    const reportSnap=await tx.get(report.ref);
    if(!reportSnap.exists())throw Error('Este reporte ya fue cerrado por otra persona.');
    if(action==='remove'){
     const postSnap=await tx.get(postRef);
     if(!postSnap.exists())throw Error('La publicación ya no existe. Descarta el reporte.');
    }
    tx.set(auditRef,{
     actorUid:viewer.uid,reportId:report.id,commentId,
     action,reason:String(reportSnap.data().reason||'otro'),
     note,createdAt:serverTimestamp()
    });
    if(action==='remove')tx.delete(postRef);
    tx.delete(report.ref);
   });
  }
  if(!canAct(viewer))return;
  activeReportDocs=activeReportDocs.filter(item=>item.id!==report.id);
  renderReports();
  status.textContent=(action==='remove'?'Publicación retirada y reporte cerrado.':'Reporte descartado.')+
   (compat?' Esta acción no tiene registro histórico.':' Decisión registrada en el historial privado.');
  if(!compat)void loadHistory();
 }catch(e){
  if(!canAct(viewer))return;
  error.textContent='No se realizó la acción ('+(e.code||e.message||'error')+').'+
   (e.code==='permission-denied'?' Comprueba que las reglas nuevas de Firebase estén publicadas.':'');
  dismiss.disabled=false;remove.disabled=!validComment(commentId)||!report._post;
 }
}
async function loadHistory(){
 const viewer=auth.currentUser,serial=generation;
 if(!canAct(viewer)||historyRefreshBusy)return;
 historyRefreshBusy=true;historyRefresh.disabled=true;
 historyStatus.textContent='Consultando historial privado…';
 try{
  const snap=await getDocs(query(auditCollection,orderBy('createdAt','desc'),limit(60)));
  if(serial!==generation||!canAct(viewer))return;
  activeHistoryDocs=snap.docs;
  auditMode='enabled';
  setAuditStatus();renderHistory();renderReports();
  historyStatus.textContent=snap.size+' decisiones consultadas (máximo 60).';
 }catch(error){
  if(serial!==generation)return;
  activeHistoryDocs=[];auditMode='unavailable';
  setAuditStatus();history.replaceChildren();renderReports();
  historyStatus.textContent=error.code==='permission-denied'?
   'La colección del historial está protegida. Publica las nuevas reglas completas de Firebase para activarlo.':
   'No se pudo consultar el historial ('+(error.code||'error')+'). Puedes reintentar.';
 }finally{
  historyRefreshBusy=false;if(serial===generation)historyRefresh.disabled=false;
 }
}
function renderHistory(){
 history.replaceChildren();
 const term=histQuery.value.trim().toLocaleLowerCase('es-MX');
 const show=activeHistoryDocs.filter(row=>{
  const item=row.data();
  if(histAction.value&&item.action!==histAction.value)return false;
  if(!term)return true;
  return [item.commentId,item.reportId,item.actorUid,item.reason,item.note,item.action].join(' ').toLocaleLowerCase('es-MX').includes(term);
 });
 if(!show.length){
  history.append(el('p',activeHistoryDocs.length?'Sin decisiones que coincidan con el filtro.':'Todavía no hay decisiones registradas en este historial.','mod-empty'));
  return;
 }
 for(const item of show){
  const data=item.data(),card=el('article',undefined,'mod-hist-card');
  const action=data.action==='remove'?'Publicación retirada':'Reporte descartado';
  card.append(el('h3',action));
  card.append(el('small',printableTime(data.createdAt)+' · Motivo denunciado: '+(allowedReasons[data.reason]||'Otro')));
  card.append(el('p','Publicación: '+String(data.commentId||'').slice(0,40)));
  const actor=String(data.actorUid||'');
  const identity=auth.currentUser?.uid===actor?'Tu cuenta moderadora':'UID moderador: '+actor.slice(0,14)+'…';
  card.append(el('small','Decisión tomada por: '+identity));
  if(data.note)card.append(el('p','Nota interna: '+String(data.note).slice(0,240)));
  history.append(card);
 }
}
reportReason.addEventListener('change',renderReports);
reportSort.addEventListener('change',renderReports);
reportQuery.addEventListener('input',renderReports);
histAction.addEventListener('change',renderHistory);
histQuery.addEventListener('input',renderHistory);
refresh.addEventListener('click',loadReports);
historyRefresh.addEventListener('click',loadHistory);
login.addEventListener('click',async()=>{
 try{await signInWithPopup(auth,new GoogleAuthProvider());}
 catch(error){
  if(error.code==='auth/popup-blocked'){
   try{await signInWithRedirect(auth,new GoogleAuthProvider());return}
   catch(e){status.textContent='No fue posible abrir la autenticación ('+(e.code||'error')+').';return}
  }
  status.textContent='No se pudo iniciar sesión ('+(error.code||'error')+').';
 }
});
logout.addEventListener('click',()=>signOut(auth));
getRedirectResult(auth).catch(error=>{console.warn('Autenticación por redirección:',error.code||error)});
onAuthStateChanged(auth,async viewer=>{
 const serial=++generation;
 resetPrivate();
 login.hidden=!!viewer;logout.hidden=!viewer;identity.hidden=!viewer;
 if(viewer){
  identityName.textContent=viewer.displayName||viewer.email||'Cuenta de Google';
  identityRole.textContent='Comprobando permisos…';
  identityPhoto.hidden=!viewer.photoURL;
  if(viewer.photoURL){
   identityPhoto.src=viewer.photoURL;identityPhoto.referrerPolicy='no-referrer';
  }else identityPhoto.removeAttribute('src');
 }else{
  identityName.textContent='';identityRole.textContent='';status.textContent='Inicia sesión con Google para verificar tu acceso.';
  return;
 }
 status.textContent='Comprobando permisos de moderación…';
 try{
  const token=await getIdTokenResult(viewer,true);
  if(serial!==generation||auth.currentUser!==viewer)return;
  isModerator=token.claims.moderator===true;
  if(!isModerator){
   identityRole.textContent='Sin permisos de moderación';
   status.textContent='Acceso denegado: esta cuenta no tiene permisos de moderación.';
   return;
  }
  identityRole.textContent='Moderador autorizado';
  privateArea.hidden=false;refresh.hidden=false;historyRefresh.hidden=false;
  setAuditStatus();status.textContent='Acceso autorizado.';
  // Conocer el estado del historial antes de habilitar decisiones.
  await loadHistory();
  if(serial!==generation||!canAct(viewer))return;
  await loadReports();
 }catch(error){
  if(serial===generation)status.textContent='No fue posible validar los permisos ('+(error.code||'error')+').';
 }
});