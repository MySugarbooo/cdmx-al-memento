/* Escribe Pro · HTML, CSS y JavaScript puro. Sin backend. */
'use strict';

const $ = id => document.getElementById(id);
const editor = $('editor');
const titleField = $('documentTitle');
const STORAGE_KEY = 'escribe-pro-backup-v2';
const SETTINGS_KEY = 'escribe-pro-preferences-v2';
const DB_NAME = 'EscribeProDocuments';
let db = null;
let documents = [];
let activeId = null;
let saveTimer = null;
let toastTimer = null;
let savedRange = null;
let ready = false;
let zoom = 100;
let findCursor = 0;
const defaultSettings = { paper: 'a4', margins: 'normal', spacing: '1.5', header: '', footer: '', numbering: true };
const templates = {
  blank: { title:'Documento sin título', html:'<p><br></p>' },
  letter: {title:'Carta profesional',html:'<p style="text-align:right">Ciudad de México, [fecha]</p><p><strong>[Nombre del destinatario]</strong><br>[Cargo o institución]</p><p><strong>Asunto: [Motivo de la carta]</strong></p><p>Estimado/a [nombre]:</p><p>Por medio de la presente, me permito dirigirme a usted para [escribir el propósito de la carta].</p><p>[Desarrolla aquí la información principal, antecedentes o solicitud.]</p><p>Agradezco su atención y quedo pendiente de su respuesta.</p><p>Atentamente,</p><p><strong>[Tu nombre]</strong><br>[Datos de contacto]</p>'},
  resume: {title:'Mi currículum',html:'<h1>[Tu nombre y apellido]</h1><p>[Profesión o especialidad] · [Ciudad] · [Correo] · [Teléfono]</p><hr><h2>Perfil profesional</h2><p>Profesional con experiencia en [área], especializado/a en [habilidades].</p><h2>Experiencia laboral</h2><p><strong>[Puesto] — [Empresa]</strong><br>[Mes/año] – [Mes/año]</p><ul><li>[Logro con resultado medible]</li><li>[Responsabilidad principal]</li></ul><h2>Educación</h2><p><strong>[Estudios]</strong> — [Institución], [año]</p><h2>Habilidades</h2><p>[Habilidad 1] · [Habilidad 2] · [Habilidad 3]</p><h2>Idiomas</h2><p>[Idioma] — [Nivel]</p>'},
  report: {title:'Informe de proyecto',html:'<h1>Informe de proyecto</h1><p><strong>Autor:</strong> [Nombre]<br><strong>Fecha:</strong> [Fecha]<br><strong>Proyecto:</strong> [Nombre del proyecto]</p><hr><h2>Resumen ejecutivo</h2><p>[Describe las conclusiones más importantes.]</p><h2>1. Objetivo</h2><p>[¿Qué se busca alcanzar?]</p><h2>2. Contexto</h2><p>[Antecedentes y datos relevantes.]</p><h2>3. Resultados</h2><table><tbody><tr><th>Indicador</th><th>Resultado</th></tr><tr><td>[Indicador]</td><td>[Dato]</td></tr></tbody></table><h2>4. Conclusiones</h2><p>[Resume los hallazgos.]</p><h2>5. Próximos pasos</h2><ul><li>[Acción 1]</li><li>[Acción 2]</li></ul>'},
  notes: {title:'Mis apuntes',html:'<h1>Apuntes de [tema]</h1><p><strong>Fecha:</strong> [Fecha] &nbsp; <strong>Clase:</strong> [Nombre]</p><h2>Ideas principales</h2><ul><li>[Concepto importante]</li><li>[Idea que quiero recordar]</li></ul><h2>Desarrollo</h2><p>[Escribe aquí tus apuntes.]</p><h2>Dudas</h2><ul><li>[Pregunta pendiente]</li></ul><h2>Resumen</h2><p>[Conclusión en tus propias palabras.]</p>'}
};

function safeId() { return globalThis.crypto?.randomUUID?.() || `doc-${Date.now()}-${Math.random().toString(36).slice(2)}`; }
function escapeHtml(v) { return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function dateLabel(timestamp) { const date=new Date(timestamp); return new Intl.DateTimeFormat('es-MX',{day:'2-digit',month:'short'}).format(date); }
function notify(message) { const el=$('toast');el.textContent=message;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3500); }
function setStatus(message, isError=false) { $('saveStatus').textContent=message;$('saveStatus').style.color=isError?'#da6767':''; }
function storageWarning() { $('storageStatus').textContent='Respaldo limitado';setStatus('Error de almacenamiento; exporta una copia',true);notify('No se pudo guardar. Descarga tu documento para protegerlo.'); }

function openDatabase() {
  return new Promise((resolve,reject)=>{
    if(!('indexedDB' in window)) return reject(Error('IndexedDB no disponible'));
    const request=indexedDB.open(DB_NAME,1);
    request.onupgradeneeded=()=>{const store=request.result.createObjectStore('docs',{keyPath:'id'});store.createIndex('updatedAt','updatedAt');};
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
}
function dbAction(type,docId=null,value=null){
  return new Promise((resolve,reject)=>{
    if(!db) return reject(Error('No hay base de datos'));
    const transaction=db.transaction('docs',type==='read'?'readonly':'readwrite');
    const store=transaction.objectStore('docs');
    const request=type==='all'?store.getAll():type==='read'?store.get(docId):type==='put'?store.put(value):store.delete(docId);
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
}
function readBackup(){try{const raw=localStorage.getItem(STORAGE_KEY);return raw?JSON.parse(raw):[]}catch{return[]}}
async function persistDocument(doc){
  if(db) { await dbAction('put',null,doc); return; }
  const items=readBackup().filter(item=>item.id!==doc.id);items.push(doc);
  localStorage.setItem(STORAGE_KEY,JSON.stringify(items));
}
async function deleteDocument(id){
  if(db) await dbAction('delete',id);
  else localStorage.setItem(STORAGE_KEY,JSON.stringify(readBackup().filter(d=>d.id!==id)));
}
async function initialize(){
  try { db=await openDatabase();documents=await dbAction('all');$('storageStatus').textContent='Guardado local'; }
  catch(error){console.warn('Almacenamiento alternativo',error);db=null;documents=readBackup();$('storageStatus').textContent='Respaldo local';}
  documents.sort((a,b)=>b.updatedAt-a.updatedAt);
  if(!documents.length){const first=createRecord('blank');documents=[first];try{await persistDocument(first)}catch{storageWarning()}}
  const prefs=readPreferences();document.body.classList.toggle('dark',!!prefs.dark);$('themeButton').textContent=prefs.dark?'☀':'☾';
  const chosen=documents.find(d=>d.id===prefs.lastId)||documents[0];
  activateDocument(chosen.id);ready=true;renderDocuments();
}
function createRecord(type='blank'){
  const tmpl=templates[type]||templates.blank;
  return {id:safeId(),title:tmpl.title,html:tmpl.html,settings:{...defaultSettings},createdAt:Date.now(),updatedAt:Date.now()};
}
function readPreferences(){try{return JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}catch{return{}}}
function setPreferences(next){try{localStorage.setItem(SETTINGS_KEY,JSON.stringify({...readPreferences(),...next}))}catch{/* Preferencias opcionales */}}
function current(){return documents.find(d=>d.id===activeId)}
function captureDoc(){const doc=current();if(!doc)return null;doc.title=titleField.value.trim()||'Documento sin título';doc.html=sanitize(editor.innerHTML);doc.settings={paper:$('paperSize').value,margins:$('pageMargins').value,spacing:$('lineSpacing').value,header:$('headerText').value,footer:$('footerText').value,numbering:$('pageNumbering').checked};doc.updatedAt=Date.now();return doc}
async function saveNow(){
  if(!activeId)return;
  clearTimeout(saveTimer);saveTimer=null;
  const doc=captureDoc();setStatus('Guardando…');
  try { await persistDocument(doc);setStatus('✓ Guardado en este dispositivo');renderDocuments(); }
  catch(error){console.warn('Error al guardar',error);storageWarning()}
}
function scheduleSave(){if(!ready)return;setStatus('Cambios sin guardar…');clearTimeout(saveTimer);saveTimer=setTimeout(saveNow,650);refreshStatistics()}
function activateDocument(id){
  const doc=documents.find(d=>d.id===id);if(!doc)return;
  clearTimeout(saveTimer);saveTimer=null;activeId=id;savedRange=null;
  titleField.value=doc.title||'Documento sin título';editor.innerHTML=sanitize(doc.html||'<p><br></p>');
  const settings={...defaultSettings,...doc.settings};
  $('paperSize').value=settings.paper;$('pageMargins').value=settings.margins;$('lineSpacing').value=settings.spacing;$('headerText').value=settings.header;$('footerText').value=settings.footer;$('pageNumbering').checked=settings.numbering!==false;
  applyLayout();refreshStatistics();setStatus('✓ Guardado en este dispositivo');setPreferences({lastId:id});renderDocuments();
}
async function switchDocument(id){if(id===activeId)return;await saveNow();activateDocument(id);closeSidebar();}
async function newDocument(type='blank'){
  await saveNow();const doc=createRecord(type);documents.unshift(doc);
  try{await persistDocument(doc)}catch{storageWarning()}
  activateDocument(doc.id);closeSidebar();notify('Documento creado');editor.focus();
}
async function duplicateDocument(id){await saveNow();const original=documents.find(d=>d.id===id);if(!original)return;const copy={...original,id:safeId(),title:`Copia de ${original.title}`,settings:{...defaultSettings,...original.settings},createdAt:Date.now(),updatedAt:Date.now()};documents.unshift(copy);try{await persistDocument(copy)}catch{storageWarning()}activateDocument(copy.id);notify('Documento duplicado')}
async function renameDocument(id){const doc=documents.find(d=>d.id===id);if(!doc)return;const values=await ask('Cambiar nombre','Elige un título para el documento.',[{id:'name',label:'Nombre',value:doc.title,required:true,maxlength:100}]);if(!values)return;await saveNow();doc.title=values.name.trim()||doc.title;doc.updatedAt=Date.now();try{await persistDocument(doc)}catch{storageWarning()}if(activeId===id)titleField.value=doc.title;renderDocuments()}
async function removeDocument(id){const doc=documents.find(d=>d.id===id);if(!doc)return;if(!confirm(`¿Eliminar “${doc.title}”? Esta acción no se puede deshacer.`))return;await saveNow();try{await deleteDocument(id)}catch(error){notify('No se pudo eliminar el documento');return}documents=documents.filter(d=>d.id!==id);if(!documents.length){const fresh=createRecord();documents=[fresh];try{await persistDocument(fresh)}catch{storageWarning()}}if(activeId===id)activateDocument(documents[0].id);renderDocuments();notify('Documento eliminado')}
function renderDocuments(){
  const term=$('documentSearch').value.toLocaleLowerCase('es');
  const entries=[...documents].sort((a,b)=>b.updatedAt-a.updatedAt).filter(doc=>doc.title.toLocaleLowerCase('es').includes(term));
  const list=$('documentsList');list.replaceChildren();
  if(!entries.length){list.innerHTML='<p class="no-documents">No hay documentos que coincidan.</p>';return;}
  for(const doc of entries){
    const item=document.createElement('div');item.className='document-item'+(doc.id===activeId?' active':'');
    item.tabIndex=0;item.setAttribute('role','button');item.setAttribute('aria-label',`Abrir ${doc.title}`);
    item.innerHTML=`<span class="document-glyph">W</span><span class="document-meta"><strong>${escapeHtml(doc.title)}</strong><small>Editado ${escapeHtml(dateLabel(doc.updatedAt))}</small></span>`;
    const more=document.createElement('button');more.className='doc-more';more.title='Opciones de documento';more.setAttribute('aria-label',`Opciones de ${doc.title}`);more.textContent='⋯';
    more.addEventListener('click',async event=>{
      event.stopPropagation();const choice=await ask('Opciones de documento',doc.title,[{id:'action',label:'Acción',type:'select',options:[['duplicate','Duplicar'],['rename','Cambiar nombre'],['delete','Eliminar']]}]);
      if(!choice)return;
      if(choice.action==='duplicate')await duplicateDocument(doc.id);
      if(choice.action==='rename')await renameDocument(doc.id);
      if(choice.action==='delete')await removeDocument(doc.id);
    });
    item.append(more);item.addEventListener('click',()=>switchDocument(doc.id));item.addEventListener('keydown',e=>{if(e.target===item&&(e.key==='Enter'||e.key===' ')){e.preventDefault();switchDocument(doc.id)}});list.append(item);
  }
}
function openSidebar(){$('sidebar').classList.add('open');$('scrim').hidden=false}
function closeSidebar(){$('sidebar').classList.remove('open');$('scrim').hidden=true}
function applyLayout(){
  const paper=$('pageContainer');paper.classList.toggle('paper-letter',$('paperSize').value==='letter');paper.classList.remove('margins-normal','margins-narrow','margins-wide');paper.classList.add('margins-'+$('pageMargins').value);
  paper.style.setProperty('--line-height',$('lineSpacing').value);
  $('pageHeader').textContent=$('headerText').value;$('pageFooter').textContent=$('footerText').value;
  document.querySelector('.workspace-view').textContent=($('paperSize').value==='letter'?'Carta':'A4')+' · Vista de edición';refreshStatistics();
}
function refreshStatistics(){
  const text=editor.innerText||'';const words=text.trim()?text.trim().split(/\s+/u).length:0;
  $('wordCount').textContent=`${words.toLocaleString('es-MX')} palabras`;
  $('characterCount').textContent=`${text.length.toLocaleString('es-MX')} caracteres`;
  $('readingTime').textContent=`${Math.max(1,Math.ceil(words/220))} min lectura`;
  const pageHeight=$('paperSize').value==='letter'?1056:1122;
  const pages=Math.max(1,Math.ceil((editor.scrollHeight+90)/pageHeight));
  $('pageCount').textContent=`${pages} ${pages===1?'página':'páginas'} aprox.`;
}
function storeSelection(){const s=window.getSelection();if(!s?.rangeCount)return;const range=s.getRangeAt(0);if(editor.contains(range.commonAncestorContainer))savedRange=range.cloneRange()}
function restoreSelection(){editor.focus();if(savedRange){try{const sel=window.getSelection();sel.removeAllRanges();sel.addRange(savedRange.cloneRange())}catch{/* selección antigua */}}}
function command(cmd,value=null){restoreSelection();try{document.execCommand(cmd,false,value)}catch(error){console.warn(cmd,error);notify('Esta función no está disponible en tu navegador')}storeSelection();scheduleSave()}
function insertHtml(html){restoreSelection();document.execCommand('insertHTML',false,sanitize(html));storeSelection();scheduleSave()}
function isSafeLink(url){try{const parsed=new URL(url,location.href);return ['https:','http:','mailto:'].includes(parsed.protocol)}catch{return false}}
function isSafeImage(url){return /^data:image\/(?:png|jpe?g|webp|gif);base64,[a-z0-9+/=\s]+$/i.test(url)||/^https?:\/\//i.test(url)}
function sanitize(raw){
  const parsed=new DOMParser().parseFromString(`<div id="safe-root">${raw}</div>`,'text/html');const root=parsed.getElementById('safe-root');if(!root)return '';
  const allowed=new Set(['P','BR','DIV','SPAN','H1','H2','H3','H4','STRONG','B','EM','I','U','S','STRIKE','SUB','SUP','UL','OL','LI','BLOCKQUOTE','A','HR','TABLE','THEAD','TBODY','TR','TH','TD','IMG','FONT']);
  const remove=new Set(['SCRIPT','STYLE','IFRAME','OBJECT','EMBED','FORM','INPUT','TEXTAREA','BUTTON','SELECT','META','LINK','SVG','MATH','VIDEO','AUDIO','NOSCRIPT']);
  function walk(parent){for(const node of [...parent.childNodes]){
    if(node.nodeType===8){node.remove();continue}
    if(node.nodeType!==1)continue;
    if(remove.has(node.tagName)){node.remove();continue}
    if(!allowed.has(node.tagName)){walk(node);node.replaceWith(...node.childNodes);continue}
    for(const attr of [...node.attributes]){
      const key=attr.name.toLowerCase();let ok=false;
      if(key==='href'&&node.tagName==='A')ok=isSafeLink(attr.value);
      if(key==='src'&&node.tagName==='IMG')ok=isSafeImage(attr.value);
      if(key==='alt'&&node.tagName==='IMG')ok=true;
      if(key==='width'&&node.tagName==='IMG')ok=/^\d{1,4}$/.test(attr.value);
      if(key==='colspan'&&['TD','TH'].includes(node.tagName))ok=/^[1-9]\d?$/.test(attr.value);
      if(key==='rowspan'&&['TD','TH'].includes(node.tagName))ok=/^[1-9]\d?$/.test(attr.value);
      if(key==='style'){
        const output=[];const permitted=new Set(['color','background-color','text-align','font-size','font-family','font-weight','font-style','text-decoration','width']);
        for(const pair of attr.value.split(';')){const position=pair.indexOf(':');if(position<0)continue;const property=pair.slice(0,position).trim().toLowerCase(),value=pair.slice(position+1).trim();if(!permitted.has(property)||!/^[#(),.%\w\s-]+$/.test(value)||/url|expression|var\s*\(/i.test(value))continue;output.push(`${property}:${value}`)}
        if(output.length)node.setAttribute('style',output.join(';'));else node.removeAttribute('style');ok=true;
      }
      if(key==='class'&&node.classList.contains('page-break')&&node.tagName==='DIV'){node.className='page-break';ok=true}
      if(key==='contenteditable'&&node.classList.contains('page-break')){node.setAttribute('contenteditable','false');ok=true}
      if(key==='size'&&node.tagName==='FONT')ok=/^[1-7]$/.test(attr.value);
      if(key==='face'&&node.tagName==='FONT')ok=/^[\w\s,-]+$/.test(attr.value);
      if(key==='color'&&node.tagName==='FONT')ok=/^#[0-9a-f]{3,8}$/i.test(attr.value);
      if(!ok)node.removeAttribute(attr.name);
    }
    if(node.tagName==='A'){node.setAttribute('rel','noopener noreferrer');node.setAttribute('target','_blank')}
    walk(node);
  }}
  walk(root);return root.innerHTML;
}
function ask(heading,description,fields){
  return new Promise(resolve=>{
    const dialog=$('promptDialog');$('promptHeading').textContent=heading;$('promptDescription').textContent=description||'';
    const place=$('promptFields');place.replaceChildren();
    for(const field of fields){const label=document.createElement('label');label.htmlFor=`dialog-${field.id}`;label.textContent=field.label;place.append(label);
      const control=document.createElement(field.type==='select'?'select':'input');control.id=`dialog-${field.id}`;control.name=field.id;if(field.type!=='select'){control.type=field.type||'text';control.value=field.value||'';control.required=field.required||false;if(field.maxlength)control.maxLength=field.maxlength;if(field.min)control.min=field.min;if(field.max)control.max=field.max;}
      else for(const [value,labelText] of field.options){const option=document.createElement('option');option.value=value;option.textContent=labelText;control.append(option)}
      place.append(control);
    }
    function onClose(){dialog.removeEventListener('close',onClose);if(dialog.returnValue!=='ok'){resolve(null);return}const data={};for(const field of fields)data[field.id]=place.querySelector(`[name="${field.id}"]`).value;resolve(data)}
    dialog.addEventListener('close',onClose);dialog.showModal();const first=place.querySelector('input,select');if(first)first.focus();
  });
}
function download(blob,filename){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000)}
function filename(ext){return `${(titleField.value.trim()||'documento').replace(/[\\/:*?"<>|\x00-\x1f]/g,'-').slice(0,85)}.${ext}`}
function makePageHtml(){const docHtml=sanitize(editor.innerHTML);return `<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(titleField.value)}</title><style>body{font:16px/1.5 Arial,sans-serif;max-width:820px;margin:40px auto;padding:0 24px;color:#263149}img{max-width:100%;height:auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:8px}h1,h2,h3{line-height:1.25}.page-break{break-after:page;page-break-after:always;border-top:1px dashed #aaa;margin:30px 0}@media print{@page{size:${$('paperSize').value==='a4'?'A4':'letter'};margin:18mm}body{margin:0;padding:0}.page-break{border:0}}</style></head><body>${$('headerText').value?`<header>${escapeHtml($('headerText').value)}</header>`:''}<main>${docHtml}</main>${$('footerText').value?`<footer>${escapeHtml($('footerText').value)}</footer>`:''}</body></html>`}
function exportSimple(type){
  if(type==='import'){$('fileInput').click();return}
  if(type==='pdf'){printDocument();return}
  if(type==='html')download(new Blob([makePageHtml()],{type:'text/html;charset=utf-8'}),filename('html'));
  if(type==='txt')download(new Blob([editor.innerText],{type:'text/plain;charset=utf-8'}),filename('txt'));
  if(type==='docx')exportWord();
}
function printDocument(){const tag=document.createElement('style');tag.id='dynamic-print-size';tag.textContent=`@media print{@page{size:${$('paperSize').value==='letter'?'letter':'A4'};margin:${$('pageMargins').value==='narrow'?'10mm':$('pageMargins').value==='wide'?'25mm':'16mm'}}}`;document.head.append(tag);if($('pageNumbering').checked){const numberingStyle=document.createElement('style');numberingStyle.id='print-page-numbers';numberingStyle.textContent='@media print{@page{@bottom-center{content:"Página " counter(page) " / " counter(pages);font:10px Arial,sans-serif;color:#777}}}';document.head.append(numberingStyle);setTimeout(()=>numberingStyle.remove(),4000)}window.print();setTimeout(()=>tag.remove(),4000)}

/* DOCX con la biblioteca docx.js: formato de párrafos, tablas, listas e imágenes de datos. */
function rgbHex(input){const match=(input||'').match(/^#([a-f0-9]{3,8})$/i);if(match){const val=match[1];return val.length===3?val.split('').map(c=>c+c).join('').toUpperCase():val.slice(0,6).toUpperCase()}const rgb=(input||'').match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);return rgb?rgb.slice(1).map(n=>Number(n).toString(16).padStart(2,'0')).join('').toUpperCase():null}
function decodeDataImage(uri){const match=uri.match(/^data:image\/(png|jpeg|jpg|gif|webp);base64,(.+)$/is);if(!match)return null;const raw=atob(match[2].replace(/\s/g,''));const data=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)data[i]=raw.charCodeAt(i);return{type:match[1].toLowerCase()==='jpg'?'jpeg':match[1].toLowerCase(),data}}
async function exportWord(){
  if(!window.docx){notify('Para exportar a Word necesitas internet para cargar la biblioteca DOCX.');return}
  const {Document,Packer,Paragraph,TextRun,ImageRun,Table,TableCell,TableRow,WidthType,HeadingLevel,AlignmentType,ExternalHyperlink,Header,Footer,PageNumber}=window.docx;
  const alignment={left:AlignmentType.LEFT,right:AlignmentType.RIGHT,center:AlignmentType.CENTER,justify:AlignmentType.JUSTIFIED};
  function textRuns(node,options={}){
    if(node.nodeType===3){return node.textContent?[new TextRun({...options,text:node.textContent})]:[]}
    if(node.nodeType!==1)return[];
    const tag=node.tagName.toLowerCase();if(tag==='br')return[new TextRun({text:'',break:1})];
    if(tag==='img'){
      const image=decodeDataImage(node.getAttribute('src')||'');if(!image)return[];
      const naturalWidth=Math.max(20,Number(node.getAttribute('width'))||260);const width=Math.min(500,naturalWidth);
      return[new ImageRun({data:image.data,type:image.type,transformation:{width,height:Math.round(width*0.75)},altText:{title:'Imagen',description:node.getAttribute('alt')||'Imagen del documento',name:'Imagen'}})];
    }
    const opts={...options};if(['b','strong'].includes(tag))opts.bold=true;if(['i','em'].includes(tag))opts.italics=true;if(tag==='u')opts.underline={};if(['s','strike'].includes(tag))opts.strike=true;
    const style=node.style||{};
    if(style.fontWeight==='bold'||Number(style.fontWeight)>=600)opts.bold=true;
    if(style.fontStyle==='italic')opts.italics=true;
    if(style.textDecoration.includes('underline'))opts.underline={};
    const color=rgbHex(style.color||node.getAttribute?.('color'));if(color)opts.color=color;
    const highlight=rgbHex(style.backgroundColor);if(highlight)opts.shading={fill:highlight};
    if(style.fontFamily||node.getAttribute?.('face'))opts.font=(style.fontFamily||node.getAttribute('face')).replace(/["']/g,'');
    const fontSize=parseFloat(style.fontSize);if(Number.isFinite(fontSize)&&fontSize>=8&&fontSize<=72)opts.size=Math.round(fontSize*1.5);
    const parts=[...node.childNodes].flatMap(c=>textRuns(c,opts));
    if(tag==='a'&&isSafeLink(node.getAttribute('href')||''))return[new ExternalHyperlink({link:node.getAttribute('href'),children:parts.filter(r=>r instanceof TextRun)})];
    return parts;
  }
  const headingLevel={h1:HeadingLevel.HEADING_1,h2:HeadingLevel.HEADING_2,h3:HeadingLevel.HEADING_3};
  function para(node,extras={}){const tag=node.tagName?.toLowerCase()||'p';const align=node.style?.textAlign;return new Paragraph({children:textRuns(node),heading:headingLevel[tag],alignment:alignment[align]||undefined,spacing:{after:120},...extras})}
  function blocks(container){const output=[];
    for(const child of container.childNodes){
      if(child.nodeType===3){if(child.textContent.trim())output.push(new Paragraph({children:[new TextRun(child.textContent)]}));continue}
      if(child.nodeType!==1)continue;
      const tag=child.tagName.toLowerCase();
      if(tag==='table'){
        const rows=[...child.querySelectorAll('tr')].map(tr=>new TableRow({children:[...tr.children].filter(c=>['TD','TH'].includes(c.tagName)).map(cell=>new TableCell({children:[para(cell)],columnSpan:Math.min(10,Number(cell.getAttribute('colspan'))||1)}))}));
        if(rows.length)output.push(new Table({rows,width:{size:100,type:WidthType.PERCENTAGE}}));
      }else if(tag==='ul'||tag==='ol'){
        for(const li of child.children){if(li.tagName!=='LI')continue;output.push(para(li,tag==='ul'?{bullet:{level:0}}:{numbering:{reference:'decimal-numbering',level:0}}))}
      }else if(tag==='div'&&child.classList.contains('page-break')){
        output.push(new Paragraph({pageBreakBefore:true,children:[]}));
      }else if(tag==='div'&&!child.className){output.push(...blocks(child));}
      else if(tag==='hr'){output.push(new Paragraph({children:[new TextRun('_____________________________________________________')]}));}
      else output.push(para(child));
    }
    return output;
  }
  try{
    setStatus('Generando archivo Word…');
    const header=$('headerText').value.trim(),footer=$('footerText').value.trim();
    const children=blocks(editor);if(!children.length)children.push(new Paragraph(''));
    const size=$('paperSize').value==='letter'?{width:12240,height:15840}:{width:11906,height:16838};
    const margins={normal:1050,narrow:570,wide:1500};const margin=margins[$('pageMargins').value]||1050;
    const footerRuns=footer?[new TextRun(footer)]:[];if($('pageNumbering').checked){if(footerRuns.length)footerRuns.push(new TextRun('  ·  '));footerRuns.push(new TextRun('Página '),new TextRun({children:[PageNumber.CURRENT]}))}
    const doc=new Document({numbering:{config:[{reference:'decimal-numbering',levels:[{level:0,format:'decimal',text:'%1.',alignment:'left'}]}]},sections:[{properties:{page:{size,margin:{top:margin,right:margin,bottom:margin,left:margin}}},headers:header?{default:new Header({children:[new Paragraph({children:[new TextRun(header)]})]})}:undefined,footers:footerRuns.length?{default:new Footer({children:[new Paragraph({children:footerRuns})]})}:undefined,children}]});
    const blob=await Packer.toBlob(doc);download(blob,filename('docx'));setStatus('✓ Documento exportado');notify('Tu archivo Word está listo');
  }catch(error){console.error(error);setStatus('No se pudo exportar Word',true);notify('Error de exportación Word: '+error.message)}
}
async function importFile(file){
  if(!file)return;
  try{
    if(file.size>16*1024*1024)throw Error('El archivo supera el límite de 16 MB');
    let html='';const name=file.name.toLowerCase();
    if(name.endsWith('.docx')){
      if(!window.mammoth)throw Error('Necesitas conexión para cargar el lector de Word');
      const result=await mammoth.convertToHtml({arrayBuffer:await file.arrayBuffer()},{convertImage:mammoth.images.imgElement(img=>img.read('base64').then(base64=>({src:`data:${img.contentType};base64,${base64}`})))});
      html=sanitize(result.value);if(result.messages?.length)notify('Word importado. Revisa los formatos especiales.');
    }else if(/\.html?$/i.test(name)){
      const page=new DOMParser().parseFromString(await file.text(),'text/html');page.querySelectorAll('script,style,iframe,object,embed,svg,form').forEach(el=>el.remove());html=sanitize(page.body.innerHTML);
    }else if(name.endsWith('.txt'))html=(await file.text()).split(/\r?\n/).map(line=>`<p>${escapeHtml(line)||'<br>'}</p>`).join('');
    else throw Error('Solo se admiten .docx, .html y .txt');
    await saveNow();const doc=createRecord();doc.title=file.name.replace(/\.[^.]+$/,'');doc.html=html||'<p><br></p>';documents.unshift(doc);
    try{await persistDocument(doc)}catch{storageWarning()}
    activateDocument(doc.id);notify('Archivo importado correctamente');
  }catch(error){console.error(error);notify('No se pudo importar: '+error.message)}
}
function selectionCell(){const range=savedRange;if(!range)return null;const base=range.commonAncestorContainer.nodeType===1?range.commonAncestorContainer:range.commonAncestorContainer.parentElement;const cell=base?.closest?.('td,th');return cell&&editor.contains(cell)?cell:null}
function insertTableRow(){const cell=selectionCell();if(!cell){notify('Coloca el cursor dentro de una tabla');return}const row=cell.closest('tr');const tr=document.createElement('tr');for(let i=0;i<row.children.length;i++){const td=document.createElement('td');td.innerHTML='<br>';tr.append(td)}row.after(tr);scheduleSave()}
function insertTableColumn(){const cell=selectionCell();if(!cell){notify('Coloca el cursor dentro de una tabla');return}const index=[...cell.parentElement.children].indexOf(cell);for(const row of cell.closest('table').rows){const td=document.createElement(row.parentElement.tagName==='THEAD'?'th':'td');td.innerHTML='<br>';row.children[index]?.after(td)||row.append(td)}scheduleSave()}
function removeTableRow(){const cell=selectionCell();if(!cell){notify('Coloca el cursor dentro de una tabla');return}const table=cell.closest('table');const row=cell.closest('tr');if(table.rows.length<=1)table.remove();else row.remove();scheduleSave()}
function textNodes(){const walker=document.createTreeWalker(editor,NodeFilter.SHOW_TEXT,{acceptNode(node){return node.parentElement?.closest('.page-break')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});const nodes=[];let node;while((node=walker.nextNode()))nodes.push(node);return nodes}
function findNext(){const term=$('findText').value;if(!term){$('findStatus').textContent='Escribe algo para buscar';return}const matches=[];for(const node of textNodes()){let at=0;const hay=node.textContent.toLocaleLowerCase('es'),needle=term.toLocaleLowerCase('es');while((at=hay.indexOf(needle,at))!==-1){matches.push({node,start:at,end:at+needle.length});at+=needle.length;}}
  if(!matches.length){$('findStatus').textContent='Sin coincidencias';return}
  const entry=matches[findCursor%matches.length];findCursor++;const range=document.createRange();range.setStart(entry.node,entry.start);range.setEnd(entry.node,entry.end);savedRange=range.cloneRange();const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);entry.node.parentElement.scrollIntoView({block:'center',behavior:'smooth'});$('findStatus').textContent=`${((findCursor-1)%matches.length)+1} de ${matches.length}`;
}
function replaceSelected(){const term=$('findText').value;if(!term){notify('Introduce el texto que deseas buscar');return}let range=savedRange;if(!range||range.collapsed||range.toString().toLocaleLowerCase('es')!==term.toLocaleLowerCase('es')){findNext();range=savedRange}if(range&&range.toString().toLocaleLowerCase('es')===term.toLocaleLowerCase('es')){range.deleteContents();const node=document.createTextNode($('replaceText').value);range.insertNode(node);range.setStartAfter(node);range.collapse(true);savedRange=range.cloneRange();scheduleSave();notify('Se reemplazó una coincidencia');}}
function replaceEvery(){const term=$('findText').value;if(!term){notify('Introduce el texto que deseas buscar');return}const replace=$('replaceText').value;let count=0;for(const node of textNodes()){const escaped=term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const exp=new RegExp(escaped,'gi');const matches=node.textContent.match(exp);if(matches){node.textContent=node.textContent.replace(exp,()=>replace);count+=matches.length}}scheduleSave();$('findStatus').textContent=`${count} reemplazos`;notify(`${count} coincidencia(s) reemplazadas`)}
function selectedText(){if(savedRange&&!savedRange.collapsed&&editor.contains(savedRange.commonAncestorContainer))return savedRange.toString();return ''}
function setSelectionText(transform){const text=selectedText();if(!text){notify('Selecciona un fragmento dentro del documento');return}const replacement=transform(text);restoreSelection();document.execCommand('insertText',false,replacement);scheduleSave();storeSelection()}
function cleanupSpaces(){setSelectionText(text=>text.replace(/[ \t]{2,}/g,' ').replace(/\s+([,.;:!?])/g,'$1').replace(/([,;:!?])([^\s\n])/g,'$1 $2').replace(/\n{3,}/g,'\n\n'));}
function extractSummary(text){const sentences=(text.match(/[^.!?\n]+[.!?]+|[^.!?\n]+$/gu)||[]).map(s=>s.trim()).filter(s=>s.length>15);if(sentences.length<=3)return sentences.join(' ');const stop=new Set('de la el los las y a en un una que por para con es se del al como su sus o lo le más no son fue sobre este esta estos estas entre también desde cuando donde cada todo todos muy pero sin'.split(' '));const words=(text.toLocaleLowerCase('es').match(/[\p{L}]{4,}/gu)||[]).filter(w=>!stop.has(w));const freq={};for(const w of words)freq[w]=(freq[w]||0)+1;const scored=sentences.map((sentence,index)=>{const tokens=(sentence.toLocaleLowerCase('es').match(/[\p{L}]{4,}/gu)||[]).filter(w=>!stop.has(w));return {index,score:tokens.reduce((sum,w)=>sum+(freq[w]||0),0)/Math.sqrt(tokens.length||1)}});const count=Math.min(5,Math.max(2,Math.ceil(sentences.length*.27)));return scored.sort((a,b)=>b.score-a.score).slice(0,count).sort((a,b)=>a.index-b.index).map(e=>sentences[e.index]).join(' ')}
function summarize(){const text=selectedText()||editor.innerText||'';if(text.trim().length<75){$('assistantOutput').textContent='Escribe o selecciona un texto más largo para obtener un resumen.';return}$('assistantOutput').textContent=extractSummary(text);notify('Resumen extractivo generado en este dispositivo')}
async function copyAll(){try{await navigator.clipboard.writeText(editor.innerText);notify('Texto copiado al portapapeles')}catch{notify('No se pudo copiar; selecciona el texto manualmente')}}

/* Eventos de la interfaz */
$('newDocument').addEventListener('click',()=>newDocument());
document.querySelectorAll('[data-template]').forEach(button=>button.addEventListener('click',()=>newDocument(button.dataset.template)));
$('openSidebar').addEventListener('click',openSidebar);$('closeSidebar').addEventListener('click',closeSidebar);$('scrim').addEventListener('click',closeSidebar);
$('documentSearch').addEventListener('input',renderDocuments);
titleField.addEventListener('input',scheduleSave);
editor.addEventListener('input',scheduleSave);
editor.addEventListener('keyup',storeSelection);
editor.addEventListener('mouseup',storeSelection);
document.addEventListener('selectionchange',storeSelection);
editor.addEventListener('paste',event=>{
  const html=event.clipboardData?.getData('text/html');if(!html)return;
  event.preventDefault();insertHtml(html);
});
document.querySelectorAll('.ribbon button[data-command]').forEach(button=>{
  button.addEventListener('mousedown',event=>event.preventDefault());
  button.addEventListener('click',()=>command(button.dataset.command));
});
$('fontFamily').addEventListener('change',e=>command('fontName',e.target.value));
$('fontSize').addEventListener('change',e=>command('fontSize',e.target.value));
$('fontColor').addEventListener('input',e=>command('foreColor',e.target.value));
$('highlightColor').addEventListener('input',e=>command('hiliteColor',e.target.value));
$('textStyle').addEventListener('change',e=>command('formatBlock',e.target.value));
const tabs={home:'homeRibbon',insert:'insertRibbon',layout:'layoutRibbon',tools:'toolsRibbon'};
for(const [tab,ribbon] of Object.entries(tabs)){
  $(`${tab}Tab`).addEventListener('click',()=>{
    Object.entries(tabs).forEach(([other,area])=>{$(`${other}Tab`).classList.toggle('active',other===tab);$(area).hidden=other!==tab;});
  });
}
for(const id of ['paperSize','pageMargins','lineSpacing','headerText','footerText','pageNumbering'])$(id).addEventListener('input',()=>{applyLayout();scheduleSave()});
$('exportButton').addEventListener('click',event=>{event.stopPropagation();const menu=$('exportMenu');menu.hidden=!menu.hidden;$('exportButton').setAttribute('aria-expanded',String(!menu.hidden))});
$('exportMenu').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{$('exportMenu').hidden=true;$('exportButton').setAttribute('aria-expanded','false');exportSimple(button.dataset.export)}));
document.addEventListener('click',event=>{if(!event.target.closest('.dropdown-wrap')){$('exportMenu').hidden=true;$('exportButton').setAttribute('aria-expanded','false')}});
$('importButton').addEventListener('click',()=>$('fileInput').click());
$('fileInput').addEventListener('change',async e=>{await importFile(e.target.files[0]);e.target.value=''});
$('printButton').addEventListener('click',printDocument);
$('themeButton').addEventListener('click',()=>{const dark=document.body.classList.toggle('dark');$('themeButton').textContent=dark?'☀':'☾';setPreferences({dark})});
$('assistantButton').addEventListener('click',()=>{const panel=$('assistantPanel');panel.hidden=!panel.hidden;$('assistantButton').setAttribute('aria-expanded',String(!panel.hidden))});
$('closeAssistant').addEventListener('click',()=>{$('assistantPanel').hidden=true;$('assistantButton').setAttribute('aria-expanded','false')});
$('insertImage').addEventListener('click',()=>$('imageInput').click());
$('imageInput').addEventListener('change',event=>{const file=event.target.files[0];if(!file)return;if(file.size>3*1024*1024){notify('La imagen debe pesar menos de 3 MB');event.target.value='';return}const reader=new FileReader();reader.onload=()=>insertHtml(`<img src="${reader.result}" alt="Imagen insertada" width="320">`);reader.readAsDataURL(file);event.target.value=''});
$('insertTable').addEventListener('click',async()=>{const data=await ask('Insertar tabla','Elige la cantidad de filas y columnas (máximo 12 × 8).',[{id:'rows',label:'Filas',type:'number',value:'3',min:1,max:12},{id:'cols',label:'Columnas',type:'number',value:'3',min:1,max:8}]);if(!data)return;const rows=Math.min(12,Math.max(1,Number(data.rows)||3)),cols=Math.min(8,Math.max(1,Number(data.cols)||3));const html='<table><tbody>'+Array.from({length:rows},()=>'<tr>'+Array.from({length:cols},()=>'<td><br></td>').join('')+'</tr>').join('')+'</tbody></table><p><br></p>';insertHtml(html)});
$('insertLink').addEventListener('click',async()=>{const data=await ask('Insertar enlace','Escribe la dirección de la página (https://) y su texto opcional.',[{id:'url',label:'Dirección web',value:'https://',required:true},{id:'label',label:'Texto del enlace (opcional)',value:selectedText()}]);if(!data)return;if(!isSafeLink(data.url)){notify('Solo se permiten enlaces http, https y mailto');return}if(selectedText()&&!data.label)command('createLink',data.url);else insertHtml(`<a href="${escapeHtml(data.url)}">${escapeHtml(data.label||data.url)}</a>`)});
let selectedImage=null;
editor.addEventListener('click',event=>{if(selectedImage)selectedImage.classList.remove('selected-image');selectedImage=event.target.closest('img');if(selectedImage&&editor.contains(selectedImage))selectedImage.classList.add('selected-image')});
function resizeSelectedImage(fraction){if(!selectedImage||!editor.contains(selectedImage)){notify('Primero toca una imagen del documento');return}const base=Math.max(100,editor.clientWidth-6);selectedImage.setAttribute('width',String(Math.round(base*fraction)));selectedImage.style.width=Math.round(base*fraction)+'px';scheduleSave();notify('Tamaño de imagen actualizado')}
$('imageSmall').addEventListener('click',()=>resizeSelectedImage(.25));$('imageMedium').addEventListener('click',()=>resizeSelectedImage(.5));$('imageLarge').addEventListener('click',()=>resizeSelectedImage(1));
$('insertRule').addEventListener('click',()=>insertHtml('<hr><p><br></p>'));
$('insertDate').addEventListener('click',()=>command('insertText',new Intl.DateTimeFormat('es-MX',{dateStyle:'long'}).format(new Date())));
$('insertBreak').addEventListener('click',()=>insertHtml('<div class="page-break" contenteditable="false"></div><p><br></p>'));
$('addTableRow').addEventListener('click',insertTableRow);$('addTableColumn').addEventListener('click',insertTableColumn);$('removeTableRow').addEventListener('click',removeTableRow);
$('findNext').addEventListener('click',findNext);$('replaceOne').addEventListener('click',replaceSelected);$('replaceAll').addEventListener('click',replaceEvery);$('findText').addEventListener('input',()=>{findCursor=0;$('findStatus').textContent=''})
$('cleanupText').addEventListener('click',cleanupSpaces);$('upperText').addEventListener('click',()=>setSelectionText(s=>s.toLocaleUpperCase('es')));$('lowerText').addEventListener('click',()=>setSelectionText(s=>s.toLocaleLowerCase('es')));$('summarizeText').addEventListener('click',summarize);$('copyText').addEventListener('click',copyAll);
$('zoomIn').addEventListener('click',()=>changeZoom(10));$('zoomOut').addEventListener('click',()=>changeZoom(-10));
function changeZoom(delta){zoom=Math.min(150,Math.max(70,zoom+delta));$('pageContainer').style.setProperty('--zoom',zoom/100);$('zoomLevel').textContent=`${zoom}%`}
document.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveNow();notify('Documento guardado')}
  if(e.key==='Escape'){$('exportMenu').hidden=true;closeSidebar()}
});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'&&saveTimer)saveNow()});
window.addEventListener('beforeunload',()=>{if(saveTimer){const doc=captureDoc();if(!db){try{const items=readBackup().filter(d=>d.id!==doc.id);items.push(doc);localStorage.setItem(STORAGE_KEY,JSON.stringify(items))}catch{}}}});
initialize();