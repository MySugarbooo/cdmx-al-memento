/* Etapa 9: recepción privada y publicaciones públicas moderadas.
 * Los autores solo ven su buzón; proyección pública sin uid, nombre o email.
 * Las reglas de Firestore exigen que la aprobación y proyección sean atómicas.
 */
(async()=>{
'use strict';
const $=id=>document.getElementById(id);
const panel=$('citizen-form'),publicList=$('citizen-public-list'),modSection=$('citizen-moderator');
if(!panel||!publicList||!modSection)return;
const B=['Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras','Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'];
const C={baches:'Baches y pavimento',fugas:'Fugas y agua',alumbrado:'Alumbrado público',basura:'Basura y limpieza',banquetas:'Banquetas y accesibilidad',transporte:'Transporte público',otro:'Otros servicios urbanos'};
const ST={pending:'Pendiente de revisión',published:'Publicación revisada',closed:'Seguimiento cerrado',rejected:'Descartado'};
const nowFormat=new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Mexico_City'});
const label=(tag,value,cls)=>{const e=document.createElement(tag);if(value!==undefined)e.textContent=String(value);if(cls)e.className=cls;return e};
const norm=t=>String(t||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const dateOf=x=>x?.toDate?.()||new Date(0);
const formatted=x=>{const d=dateOf(x);return d.getTime()>0?nowFormat.format(d):'Fecha no disponible'};
const safeRow=x=>x&&B.includes(x.borough)&&Object.hasOwn(C,x.category)&&
 typeof x.title==='string'&&typeof x.description==='string'&&
 typeof x.colonia==='string'&&Object.hasOwn(ST,x.status);
const setStatus=(id,value)=>{const el=$(id);if(el)el.textContent=value};
let firebase=null,fs=null,auth=null,person=null,moderator=false,ready=false;
let published=[],mine=[],queue=[];
let lastSubmit=0,publicBusy=false,mineBusy=false,modBusy=false,submitBusy=false;
const submitBtn=$('citizen-send');
const selectedKey='cdmx.memento.alcaldia.v1';
function addBoroughOptions(element){
 for(const name of B){const option=label('option',name);option.value=name;element.append(option)}
}
addBoroughOptions($('citizen-borough'));addBoroughOptions($('citizen-filter-borough'));
try{const saved=localStorage.getItem(selectedKey);if(B.includes(saved))$('citizen-borough').value=saved}catch{}
function reportCard(row,privateView=false){
 const data=row.data();
 const card=label('article',undefined,'citizen-card');
 const top=label('div',undefined,'citizen-card-head');
 top.append(label('span',C[data.category]||'Reporte urbano','citizen-card-tag'));
 const when=label('time',formatted(data.createdAt),'citizen-card-time');
 if(data.createdAt?.toDate)when.dateTime=data.createdAt.toDate().toISOString();
 top.append(when);card.append(top);
 card.append(label('h3',data.title));
 card.append(label('p',data.borough+(data.colonia?' · Colonia '+data.colonia:' · Colonia no indicada'),'citizen-card-location'));
 card.append(label('p',data.description));
 const state=label('div',ST[data.status]||'Estado no disponible','citizen-card-state');
 state.dataset.state=data.status;card.append(state);
 const footer=label('div',undefined,'citizen-card-footer');
 footer.textContent=privateView?'Estado editorial del envío. No es un folio SUAC.':
  'Testimonio vecinal · no comprobado por las autoridades ni por esta página. No es un reporte SUAC.';
 card.append(footer);
 if(privateView&&['pending','rejected'].includes(data.status)){
  const withdraw=label('button','Retirar este envío','citizen-button citizen-button-outline');
  withdraw.type='button';
  withdraw.addEventListener('click',async()=>{
   if(!person||!ready||!window.confirm('¿Retirar este envío? Esta acción no puede deshacerse.'))return;
   withdraw.disabled=true;
   try{await fs.deleteDoc(fs.doc(firebase.db,'citizenReports',row.id));await loadMine()}
   catch{withdraw.disabled=false;setStatus('citizen-my-status','No fue posible retirar el reporte. Comprueba las reglas activas.')}
  });
  card.append(withdraw);
 }
 return card;
}
async function loadPublic(){
 if(!ready||publicBusy)return;
 publicBusy=true;
 setStatus('citizen-public-status','Consultando reportes aprobados…');
 try{
  const q=fs.query(fs.collection(firebase.db,'citizenReportsPublic'),fs.orderBy('createdAt','desc'),fs.limit(70));
  const snap=await fs.getDocs(q);
  published=snap.docs.filter(row=>{
   const d=row.data();
   return safeRow(d)&&['published','closed'].includes(d.status)&&
    !Object.hasOwn(d,'uid')&&!Object.hasOwn(d,'name')&&!Object.hasOwn(d,'email');
  });
  renderPublic();
 }catch(e){
  published=[];publicList.replaceChildren(label('p',
   'No se pudieron leer los reportes revisados. Puede faltar publicar las reglas de Firebase de la etapa 9.','citizen-empty'));
  setStatus('citizen-public-status','Consulta no disponible ('+(e.code||'error')+').');
 }finally{publicBusy=false}
}
function renderPublic(){
 const borough=$('citizen-filter-borough').value,cat=$('citizen-filter-category').value;
 const q=norm($('citizen-filter-text').value.trim());
 const visible=published.filter(row=>{
  const d=row.data();return (!borough||d.borough===borough)&&(!cat||d.category===cat)&&
   (!q||norm([d.borough,d.colonia,d.title,d.description].join(' ')).includes(q));
 });
 publicList.replaceChildren();
 for(const row of visible)publicList.append(reportCard(row));
 if(!visible.length)publicList.append(label('p',published.length?
  'No hay reportes aprobados que coincidan con los filtros.':
  'Todavía no hay reportes ciudadanos aprobados. Los envíos pendientes se mantienen privados.','citizen-empty'));
 setStatus('citizen-public-status',visible.length+' reporte(s) visible(s) · solo publicaciones revisadas. Última consulta: '+
  new Intl.DateTimeFormat('es-MX',{hour:'2-digit',minute:'2-digit',timeZone:'America/Mexico_City'}).format(new Date())+'.');
}
$('citizen-filter-borough').addEventListener('change',renderPublic);
$('citizen-filter-category').addEventListener('change',renderPublic);
$('citizen-filter-text').addEventListener('input',renderPublic);
$('citizen-public-refresh').addEventListener('click',loadPublic);
async function loadMine(){
 if(!ready||!person||mineBusy)return;
 mineBusy=true;setStatus('citizen-my-status','Consultando tus reportes…');
 try{
  const q=fs.query(fs.collection(firebase.db,'citizenReports'),
   fs.where('uid','==',person.uid),fs.limit(50));
  const snap=await fs.getDocs(q);
  mine=snap.docs.filter(x=>safeRow(x.data())&&x.data().uid===person.uid)
   .sort((a,b)=>dateOf(b.data().createdAt)-dateOf(a.data().createdAt));
  const list=$('citizen-my-list');list.replaceChildren();
  for(const item of mine)list.append(reportCard(item,true));
  if(!mine.length)list.append(label('p','No has enviado reportes todavía.','citizen-empty'));
  setStatus('citizen-my-status',mine.length+' envío(s) asociados a tu cuenta.');
 }catch(e){
  setStatus('citizen-my-status','No se pudieron consultar tus envíos ('+(e.code||'error')+'). Revisa las reglas de Firestore.');
 }finally{mineBusy=false}
}
$('citizen-my-refresh').addEventListener('click',loadMine);
function moderationItem(row){
 const d=row.data(),card=label('article',undefined,'citizen-review-card');
 const top=label('div',undefined,'citizen-card-head');
 top.append(label('span',ST[d.status]||'Reporte','citizen-card-tag'));
 top.append(label('time',formatted(d.createdAt),'citizen-card-time'));
 card.append(top);
 card.append(label('h3',d.title));
 card.append(label('p',d.borough+(d.colonia?' · '+d.colonia:'')+' · '+(C[d.category]||'Otro')));
 card.append(label('p',d.description));
 card.append(label('p','Cuenta autora (solo moderación): '+String(d.uid||'').slice(0,12)+'…'));
 const actions=label('div',undefined,'citizen-review-actions');
 const buttons=d.status==='pending'?[['published','Aprobar y publicar'],['rejected','Descartar']]:
  d.status==='published'?[['closed','Cerrar seguimiento'],['rejected','Retirar de la web']]:
  d.status==='closed'?[['rejected','Retirar de la web']]:[];
 for(const [status,title]of buttons){
  const button=label('button',title,'citizen-button'+(status==='rejected'?' citizen-button-outline':''));
  button.type='button';
  button.addEventListener('click',()=>setReportStatus(row,status,button));
  actions.append(button);
 }
 card.append(actions);return card;
}
async function loadModerator(){
 if(!ready||!person||!moderator||modBusy)return;
 modBusy=true;setStatus('citizen-mod-status','Consultando cola de moderación…');
 try{
  const collection=fs.collection(firebase.db,'citizenReports');
  const groups=await Promise.all(['pending','published','closed'].map(status=>
   fs.getDocs(fs.query(collection,fs.where('status','==',status),fs.limit(60)))));
  queue=groups.flatMap(g=>g.docs).filter(x=>safeRow(x.data()))
   .sort((a,b)=>dateOf(b.data().createdAt)-dateOf(a.data().createdAt));
  const list=$('citizen-mod-list');list.replaceChildren();
  for(const row of queue)list.append(moderationItem(row));
  if(!queue.length)list.append(label('p','No hay reportes pendientes ni publicaciones abiertas.','citizen-empty'));
  setStatus('citizen-mod-status',queue.filter(x=>x.data().status==='pending').length+
   ' pendiente(s) · '+queue.filter(x=>x.data().status==='published').length+' publicado(s) · '+
   queue.filter(x=>x.data().status==='closed').length+' cerrado(s).');
 }catch(e){
  setStatus('citizen-mod-status','No se pudo consultar la cola ('+(e.code||'error')+'). Comprueba rol moderador y reglas.');
 }finally{modBusy=false}
}
async function setReportStatus(row,next,button){
 if(!ready||!person||!moderator||button.disabled)return;
 const old=row.data();
 const allowed=(old.status==='pending'&&['published','rejected'].includes(next))||
  (old.status==='published'&&['closed','rejected'].includes(next))||
  (old.status==='closed'&&next==='rejected');
 if(!allowed)return;
 if(!window.confirm(next==='published'?
  '¿Revisaste que no contenga información personal y autorizas publicarlo?':
  next==='closed'?'¿Cerrar seguimiento editorial? No implica que el problema se reparó.':
  '¿Descartar o retirar este reporte?'))return;
 button.disabled=true;
 const privateRef=fs.doc(firebase.db,'citizenReports',row.id);
 const publicRef=fs.doc(firebase.db,'citizenReportsPublic',row.id);
 const updated=fs.serverTimestamp();
 const batch=fs.writeBatch(firebase.db);
 batch.update(privateRef,{status:next,moderatedBy:person.uid,updatedAt:updated});
 if(next==='published'){
  batch.set(publicRef,{
   borough:old.borough,colonia:old.colonia,category:old.category,
   title:old.title,description:old.description,status:'published',
   createdAt:old.createdAt,updatedAt:updated
  });
 }else if(next==='closed'){
  batch.update(publicRef,{status:'closed',updatedAt:updated});
 }else if(old.status==='published'||old.status==='closed'){
  batch.delete(publicRef);
 }
 try{
  await batch.commit();
  setStatus('citizen-mod-status','Decisión registrada. Actualizando listados…');
  await Promise.all([loadPublic(),loadModerator(),loadMine()]);
 }catch(e){
  button.disabled=false;
  setStatus('citizen-mod-status','No se guardó el cambio ('+(e.code||'error')+
   '). Comprueba las reglas nuevas de Firestore y tu rol moderador.');
 }
}
$('citizen-mod-refresh').addEventListener('click',loadModerator);
$('citizen-login').addEventListener('click',async()=>{
 if(!auth)return;
 try{await firebase.authMod.signInWithPopup(auth,new firebase.authMod.GoogleAuthProvider())}
 catch(e){
  if(['auth/popup-blocked','auth/cancelled-popup-request'].includes(e.code)){
   try{await firebase.authMod.signInWithRedirect(auth,new firebase.authMod.GoogleAuthProvider());return}catch{}
  }
  setStatus('citizen-auth-status','No se pudo iniciar sesión. Habilita ventanas emergentes o prueba otra vez.');
 }
});
$('citizen-logout').addEventListener('click',()=>auth&&firebase.authMod.signOut(auth));
panel.addEventListener('submit',async event=>{
 event.preventDefault();
 if(!ready||!person||submitBusy)return;
 const borough=$('citizen-borough').value,colonia=$('citizen-colonia').value.trim();
 const category=$('citizen-category').value,title=$('citizen-title').value.trim();
 const description=$('citizen-description').value.trim();
 if(!B.includes(borough)||!Object.hasOwn(C,category)||colonia.length>70||
  (colonia.length>0&&colonia.length<3)||title.length<8||title.length>110||
  description.length<20||description.length>900||!$('citizen-consent').checked){
  setStatus('citizen-send-status','Completa los campos y acepta las condiciones de publicación.');
  return;
 }
 if(Date.now()-lastSubmit<60000){
  setStatus('citizen-send-status','Evita envíos seguidos. Intenta de nuevo después de un minuto.');
  return;
 }
 // Barrera de usabilidad, no seguridad: la revisión humana sigue siendo obligatoria.
 if(/https?:\/\/|www\.|[\w.+-]+@[\w.-]+\.\w+|\b(?:\+?52\s?)?\d{10}\b/i.test(title+' '+description+' '+colonia)){
  setStatus('citizen-send-status','No agregues enlaces, teléfonos ni correos personales. Retíralos antes de enviar.');
  return;
 }
 submitBusy=true;submitBtn.disabled=true;
 setStatus('citizen-send-status','Enviando reporte privado para revisión…');
 try{
  const ref=fs.doc(fs.collection(firebase.db,'citizenReports'));
  await fs.setDoc(ref,{
   uid:person.uid,borough,colonia,category,title,description,
   status:'pending',createdAt:fs.serverTimestamp(),updatedAt:fs.serverTimestamp(),moderatedBy:''
  });
  lastSubmit=Date.now();panel.reset();
  setStatus('citizen-send-status','Reporte recibido para revisión. Aún NO aparece públicamente ni se envió al SUAC.');
  await loadMine();
 }catch(e){
  setStatus('citizen-send-status','No se pudo guardar el reporte ('+(e.code||'error')+
   '). Puede ser necesario publicar las reglas de seguridad de la etapa 9 en Firebase.');
 }finally{submitBusy=false;submitBtn.disabled=false}
});
try{
 const config=window.CDMX_COMMENTS_FIREBASE;
 if(!config?.apiKey||!config?.authDomain||!config?.projectId||!config?.appId)
  throw Error('firebase-config-missing');
 const [appMod,authMod,store]=await Promise.all([
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js'),
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js'),
  import('https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js')
 ]);
 const app=appMod.initializeApp(config,'cdmx-citizen');
 auth=authMod.getAuth(app);fs=store;
 firebase={db:store.getFirestore(app),authMod};ready=true;
 try{await authMod.getRedirectResult(auth)}catch{}
 await loadPublic();
 authMod.onAuthStateChanged(auth,async current=>{
  person=current;moderator=false;
  $('citizen-login').hidden=!!person;$('citizen-logout').hidden=!person;
  panel.hidden=!person;$('mis-reportes').hidden=!person;
  modSection.hidden=true;
  setStatus('citizen-auth-status',person?
   'Sesión Google activa. Tus envíos están privados hasta su revisión.':
   'Inicia sesión con Google para enviar y consultar tus reportes.');
  if(!person)return;
  await loadMine();
  try{
   const token=await authMod.getIdTokenResult(person,true);
   if(auth.currentUser!==person)return;
   moderator=token.claims.moderator===true;
   modSection.hidden=!moderator;
   if(moderator)await loadModerator();
  }catch{modSection.hidden=true}
 });
}catch(e){
 ready=false;
 setStatus('citizen-auth-status','No pudimos conectar Firebase. No se aceptan envíos sin confirmación.');
 setStatus('citizen-public-status','Los reportes públicos no están disponibles por ahora.');
 $('citizen-login').disabled=true;
}
})();
