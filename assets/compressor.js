'use strict';
(() => {
const $=id=>document.getElementById(id);
const input=$('files'),zone=$('dropzone'),list=$('file-list'),run=$('run'),clear=$('clear'),notice=$('notice');
const quality=$('quality'),qualityText=$('quality-value'),width=$('max-width'),format=$('image-format'),pdfMode=$('pdf-mode'),smart=$('smart-retry');
let selected=[],busy=false,downloads=[];
const LIMIT=40*1024*1024,MAX_FILES=12;
const bytes=n=>n<1024?n+' B':n<1048576?(n/1024).toFixed(1)+' KB':(n/1048576).toFixed(2)+' MB';
const ext=name=>(name.split('.').pop()||'').toLowerCase();
const valid=new Set(['jpg','jpeg','png','webp','pdf','docx','txt','md','csv','json','rtf']);
const safeName=s=>s.replace(/[<>:"/\\|?*\x00-\x1F]/g,'_').slice(0,140);
const nextName=(name,suffix,newExt)=>safeName(name.replace(/\.[^.]*$/,'')+suffix+'.'+newExt);
function status(t,type=''){notice.textContent=t;notice.className='notification '+type}
function saveLink(blob,name,label='⬇ Descargar archivo comprimido',extraClass=''){const url=URL.createObjectURL(blob);downloads.push(url);const a=document.createElement('a');a.href=url;a.download=name;a.className='download '+extraClass;a.textContent=label;return a}
function dispose(){downloads.forEach(URL.revokeObjectURL);downloads=[]}
const makeBlob=(canvas,mime,q)=>new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('El navegador no pudo generar la imagen.')),mime,q));
async function raster(blob,maxPixels){
 let bitmap;
 try{bitmap=await createImageBitmap(blob)}catch(e){throw Error('No se pudo abrir esta imagen o su formato no es compatible.')}
 const scale=Math.min(1,maxPixels/Math.max(bitmap.width,bitmap.height));
 const w=Math.max(1,Math.round(bitmap.width*scale)),h=Math.max(1,Math.round(bitmap.height*scale));
 if(w*h>18000000){bitmap.close();throw Error('La imagen es demasiado grande para procesarla en este dispositivo.')}
 const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
 const ctx=canvas.getContext('2d',{alpha:true});if(!ctx){bitmap.close();throw Error('No se pudo preparar el lienzo de imagen.')}
 ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(bitmap,0,0,w,h);bitmap.close();
 return canvas;
}
async function compressImage(blob,originalExt,level,limit,requested='auto',targetBytes=0){
 const canvas=await raster(blob,limit);
 const extType=originalExt==='jpeg'?'jpg':originalExt;
 let type,outputExt;
 if(requested==='jpg'){type='image/jpeg';outputExt='jpg'}
 else if(requested==='webp'){type='image/webp';outputExt='webp'}
 else if(requested==='original'||(requested==='auto'&&extType==='png')){type=extType==='png'?'image/png':extType==='webp'?'image/webp':'image/jpeg';outputExt=extType}
 else{type=extType==='webp'?'image/webp':'image/jpeg';outputExt=extType}
 let targetCanvas=canvas;
 if(type==='image/jpeg'){
  // JPEG no admite transparencia: reemplazar canal alfa por fondo blanco.
  const bg=document.createElement('canvas');bg.width=canvas.width;bg.height=canvas.height;
  const ctx=bg.getContext('2d');if(!ctx)throw Error('No se pudo preparar la imagen.');
  ctx.fillStyle='#ffffff';ctx.fillRect(0,0,bg.width,bg.height);ctx.drawImage(canvas,0,0);
  targetCanvas=bg;
 }
 let result=await makeBlob(targetCanvas,type,level),usedQuality=level;
 if(result.type && result.type!==type)throw Error('El navegador no admite este formato de salida. Prueba con JPG.');
 // Si el primer resultado es mayor, volver a codificar sin volver a decodificar la foto.
 // Solo se activa cuando el usuario acepta el modo de compresión adaptativa.
 if(targetBytes>0&&(type==='image/jpeg'||type==='image/webp')&&result.size>=targetBytes){
  let q=level-.08,tries=0;
  while(q>=.31&&tries<7&&result.size>=targetBytes){
   q=Math.round(q*100)/100;
   const candidate=await makeBlob(targetCanvas,type,q);
   if(candidate.size<result.size){result=candidate;usedQuality=q}
   q-=.08;tries++;
  }
 }
 return {blob:result,extension:outputExt,dimensions:canvas.width+'×'+canvas.height,qualityUsed:usedQuality,lossy:type!=='image/png'};
}
function settings(){return{q:Number(quality.value)/100,maxWidth:Number(width.value),fmt:format.value,pdf:pdfMode.value,smart:Boolean(smart?.checked)}}
async function imageFile(file,s){
 const result=await compressImage(file,ext(file.name),s.q,s.maxWidth,s.fmt,s.smart?file.size:0);
 const reduced=result.qualityUsed<s.q;
 const note='Resolución: '+result.dimensions
  +(result.extension!==ext(file.name).replace('jpeg','jpg')?' · Formato convertido':'')
  +(result.lossy?' · Calidad: '+Math.round(result.qualityUsed*100)+' %'+(reduced?' (ajustada para intentar reducir el tamaño)':''):' · PNG sin pérdida de calidad por ajuste');
 return {blob:result.blob,name:nextName(file.name,'-comprimida',result.extension),note};
}
async function pdfFile(file,s){
 if(!window.PDFLib)throw Error('La biblioteca PDF no pudo cargarse. Comprueba tu conexión a internet.');
 const data=await file.arrayBuffer();
 if(s.pdf==='preserve'){
  let document;
  try{document=await window.PDFLib.PDFDocument.load(data)}catch{throw Error('El PDF puede estar cifrado, dañado o no ser compatible con la optimización sin cambios.')}
  const saved=await document.save({useObjectStreams:true,updateFieldAppearances:false});
  return {blob:new Blob([saved],{type:'application/pdf'}),name:nextName(file.name,'-optimizado','pdf'),note:'Estructura reescrita sin rasterizar las páginas. Algunos archivos no se reducen.'};
 }
 if(!window.pdfjsLib||!window.jspdf?.jsPDF)throw Error('No se cargaron las bibliotecas para comprimir PDF por imágenes.');
 const pdfjs=window.pdfjsLib;
 pdfjs.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
 let pdf;try{pdf=await pdfjs.getDocument({data:new Uint8Array(data),useSystemFonts:true}).promise}catch{throw Error('No se pudo leer este PDF. Comprueba que no esté protegido por contraseña.')}
 if(pdf.numPages>65){await pdf.destroy();throw Error('Para proteger el navegador, procesa PDF de hasta 65 páginas en el modo de compresión fuerte.')}
 let result;
 try{
  for(let i=1;i<=pdf.numPages;i++){
   status('Procesando PDF: página '+i+' de '+pdf.numPages+'…','working');
   const page=await pdf.getPage(i);
   const base=page.getViewport({scale:1});
   const scale=Math.min(s.q>=.8?1.65:s.q>=.6?1.25:.95,2300/Math.max(base.width,base.height));
   const view=page.getViewport({scale:scale});
   const canvas=document.createElement('canvas');canvas.width=Math.ceil(view.width);canvas.height=Math.ceil(view.height);
   if(canvas.width*canvas.height>16000000)throw Error('La página PDF requiere demasiada memoria.');
   const ctx=canvas.getContext('2d',{alpha:false});
   ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
   await page.render({canvasContext:ctx,viewport:view,background:'white'}).promise;
   const img=canvas.toDataURL('image/jpeg',Math.min(.9,s.q));
   if(!result)result=new window.jspdf.jsPDF({orientation:base.width>base.height?'landscape':'portrait',unit:'pt',format:[base.width,base.height],compress:true});
   else result.addPage([base.width,base.height],base.width>base.height?'landscape':'portrait');
   result.addImage(img,'JPEG',0,0,base.width,base.height,undefined,'FAST');
   canvas.width=canvas.height=1;page.cleanup();
  }
  return {blob:result.output('blob'),name:nextName(file.name,'-ligero','pdf'),note:'PDF aplanado en imágenes. Ya no conserva texto seleccionable, formularios ni enlaces interactivos.'}
 }finally{await pdf.destroy()}
}
async function wordFile(file,s){
 if(!window.JSZip)throw Error('La biblioteca para documentos no se cargó. Revisa tu conexión.');
 let archive;try{archive=await window.JSZip.loadAsync(file)}catch{throw Error('Solo admitimos documentos .docx válidos, no archivos .doc antiguos.')}
 if(!archive.file('[Content_Types].xml')||!archive.file('word/document.xml'))throw Error('Este archivo no contiene la estructura DOCX esperada.');
 let changed=0,images=0;
 const entries=Object.keys(archive.files).filter(path=>/^word\/media\/[^/]+\.(png|jpe?g|webp)$/i.test(path));
 for(const path of entries){
  const f=archive.file(path);if(!f)continue;
  images++;const original=await f.async('uint8array');
  if(original.length>14*1024*1024)continue;
  try{const e=ext(path);const b=new Blob([original],{type:e==='png'?'image/png':e==='webp'?'image/webp':'image/jpeg'});
   const output=await compressImage(b,e,s.q,Math.min(s.maxWidth,1600),'original');
   if(output.blob.size<original.length*.93){archive.file(path,await output.blob.arrayBuffer(),{binary:true,compression:'DEFLATE'});changed++}
  }catch{/* Media no compatible: se conserva tal cual. */}
 }
 const blob=await archive.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:9},streamFiles:true});
 return {blob,name:nextName(file.name,'-optimizado','docx'),note:changed+' de '+images+' imágenes internas optimizadas; texto y estructura DOCX conservados. Puede no reducirse si ya estaba comprimido.'}
}
async function textFile(file){
 if(!window.JSZip)throw Error('No se pudo cargar la biblioteca ZIP.');
 const zip=new window.JSZip();zip.file(file.name,await file.arrayBuffer());
 const blob=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:9}});
 return {blob,name:nextName(file.name,'-comprimido','zip'),note:'Se creó un ZIP. El archivo de texto original se conserva dentro.'}
}
function addFiles(incoming){
 if(busy)return;
 const append=[...incoming],seen=new Set(selected.map(f=>f.name+'|'+f.size+'|'+f.lastModified));
 let rejected=0;
 for(const file of append){
  const key=file.name+'|'+file.size+'|'+file.lastModified;
  if(selected.length>=MAX_FILES||!valid.has(ext(file.name))||file.size>LIMIT||file.size===0||seen.has(key)){rejected++;continue}
  selected.push(file);seen.add(key)
 }
 renderFiles();if(rejected)status('Se omitieron '+rejected+' archivos (formato, tamaño máximo de 40 MB, duplicados o límite de 12).','warning');
 else status(selected.length+' archivo(s) seleccionados.');
}
function renderFiles(){
 list.replaceChildren();
 for(const file of selected){
  const row=document.createElement('div');row.className='file-row';
  const left=document.createElement('div');const title=document.createElement('strong');title.textContent=file.name;const sub=document.createElement('small');sub.textContent=bytes(file.size)+' · '+ext(file.name).toUpperCase();left.append(title,sub);
  const del=document.createElement('button');del.type='button';del.className='remove';del.textContent='Quitar';del.disabled=busy;del.addEventListener('click',()=>{selected=selected.filter(f=>f!==file);renderFiles()});
  row.append(left,del);list.append(row);
 }run.disabled=busy||!selected.length;clear.disabled=busy||!selected.length;
}
async function process(){
 if(busy||!selected.length)return;busy=true;dispose();$('results').replaceChildren();renderFiles();const s=settings();
 let savedCount=0;status('Trabajando. Mantén abierta esta pestaña…','working');
 for(let i=0;i<selected.length;i++){
  const file=selected[i],kind=ext(file.name),block=document.createElement('article');block.className='result-card';
  const h=document.createElement('h3');h.textContent=file.name;block.append(h);
  try{
   let out;
   if(['jpg','jpeg','png','webp'].includes(kind))out=await imageFile(file,s);
   else if(kind==='pdf')out=await pdfFile(file,s);
   else if(kind==='docx')out=await wordFile(file,s);
   else out=await textFile(file);
   const change=100*(file.size-out.blob.size)/file.size;
   const p=document.createElement('p');p.textContent='Original: '+bytes(file.size)+' · Resultado: '+bytes(out.blob.size)+' · '+(change>=0?'Reducción: '+change.toFixed(1)+' %':'Aumento: '+(-change).toFixed(1)+' %');
   block.append(p);
   const note=document.createElement('small');note.textContent=out.note;block.append(note);
   if(out.blob.size<file.size){
    const p=document.createElement('p');p.className='result-success';p.textContent='¡Listo! Tu archivo ocupa menos espacio.';
    block.append(p,saveLink(out.blob,out.name));savedCount++;
   }else{
    const warn=document.createElement('p');warn.className='result-warning';
    warn.textContent='Esta versión no es más ligera que el original. Puedes ajustar la calidad, convertir a WebP o descargarla igualmente si la necesitas.';
    block.append(warn);
    const actions=document.createElement('div');actions.className='result-actions';
    if(['jpg','jpeg','png','webp'].includes(kind)&&s.fmt!=='webp'){
      const retry=document.createElement('button');retry.type='button';retry.className='btn btn-outline';
      retry.textContent='Probar compresión WebP';
      retry.addEventListener('click',()=>{format.value='webp';if(Number(quality.value)>65){quality.value='65';qualityText.textContent='65 %'}process()});
      actions.append(retry);
    }
    actions.append(saveLink(out.blob,out.name,'⬇ Descargar de todos modos (más pesado)','download-warning'));
    block.append(actions);
   }
  }catch(err){const warn=document.createElement('p');warn.className='result-error';warn.textContent='No se procesó: '+err.message;block.append(warn)}
  $('results').append(block);
 }
 busy=false;renderFiles();status('Proceso terminado: '+savedCount+' de '+selected.length+' archivo(s) se redujeron.'+(savedCount<selected.length?' Revisa las opciones de los resultados que no se redujeron.':''),savedCount===selected.length?'success':'warning');
}
input.addEventListener('change',()=>{addFiles(input.files);input.value=''});
zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('dragging')});
zone.addEventListener('dragleave',()=>zone.classList.remove('dragging'));
zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('dragging');addFiles(e.dataTransfer.files)});
quality.addEventListener('input',()=>qualityText.textContent=quality.value+' %');
clear.addEventListener('click',()=>{selected=[];dispose();$('results').replaceChildren();renderFiles();status('Lista vacía.')});
run.addEventListener('click',process);
window.addEventListener('pagehide',dispose);
renderFiles();
})();