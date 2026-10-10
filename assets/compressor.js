'use strict';
(() => {
const $=id=>document.getElementById(id);
const input=$('files'),zone=$('dropzone'),list=$('file-list'),run=$('run'),clear=$('clear'),notice=$('notice');
const quality=$('quality'),qualityText=$('quality-value'),width=$('max-width'),format=$('image-format'),pdfMode=$('pdf-mode'),smart=$('smart-retry'),target=$('target-kb'),zipButton=$('download-zip'),zipNote=$('zip-note'),zipLinks=$('zip-links'),presetButtons=[...document.querySelectorAll('[data-target]')];
let selected=[],busy=false,bundleBusy=false,downloads=[],bundle=[];
const LIMIT=40*1024*1024,MAX_FILES=12;
const bytes=n=>n<1024?n+' B':n<1048576?(n/1024).toFixed(1)+' KB':(n/1048576).toFixed(2)+' MB';
const ext=name=>(name.split('.').pop()||'').toLowerCase();
const valid=new Set(['jpg','jpeg','png','webp','pdf','docx','txt','md','csv','json','rtf']);
const safeName=s=>s.replace(/[<>:"/\\|?*\x00-\x1F]/g,'_').slice(0,140);
const nextName=(name,suffix,newExt)=>safeName(name.replace(/\.[^.]*$/,'')+suffix+'.'+newExt);
function status(t,type=''){notice.textContent=t;notice.className='notification '+type}
function saveLink(blob,name,label='⬇ Descargar archivo comprimido',extraClass=''){const url=URL.createObjectURL(blob);downloads.push(url);const a=document.createElement('a');a.href=url;a.download=name;a.className='download '+extraClass;a.textContent=label;return a}
function dispose(){downloads.forEach(URL.revokeObjectURL);downloads=[]}
function previewImage(before,after){
 const wrap=document.createElement('section');wrap.className='image-preview';wrap.setAttribute('aria-label','Comparar imagen original y procesada');
 const title=document.createElement('h4');title.textContent='Comparación visual: antes y después';wrap.append(title);
 const description=document.createElement('p');description.className='preview-help';description.textContent='Mueve la barra para ver los cambios. Compara detalles y letras antes de descargar: el límite de tamaño puede reducir mucho la calidad.';wrap.append(description);
 const stage=document.createElement('div');stage.className='compare-stage';stage.style.setProperty('--compare','50%');
 const left=document.createElement('img');left.alt='Imagen original';left.className='compare-before';
 const right=document.createElement('img');right.alt='Imagen después de comprimir';right.className='compare-after';
 for(const pair of [[before,left],[after,right]]){
  const uri=URL.createObjectURL(pair[0]);downloads.push(uri);pair[1].src=uri;pair[1].decoding='async';
 }
 const line=document.createElement('span');line.className='compare-line';line.setAttribute('aria-hidden','true');
 const beforeLabel=document.createElement('span');beforeLabel.className='compare-tag tag-before';beforeLabel.textContent='ANTES';
 const afterLabel=document.createElement('span');afterLabel.className='compare-tag tag-after';afterLabel.textContent='DESPUÉS';
 stage.append(left,right,line,beforeLabel,afterLabel);
 const label=document.createElement('label');label.className='compare-control';label.textContent='Mostrar la imagen comprimida: ';
 const current=document.createElement('output');current.textContent='50 %';label.append(current);
 const slider=document.createElement('input');slider.type='range';slider.min='0';slider.max='100';slider.value='50';slider.step='1';slider.setAttribute('aria-label','Porcentaje de imagen comprimida visible');
 slider.addEventListener('input',()=>{stage.style.setProperty('--compare',slider.value+'%');current.textContent=slider.value+' %'});
 wrap.append(stage,label,slider);
 return wrap;
}
function refreshPresets(){
 const choice=target.value;
 for(const btn of presetButtons){const active=btn.dataset.target===choice;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));btn.disabled=busy||bundleBusy}
}
function resetBundle(){bundle=[];if(zipButton)zipButton.disabled=true;if(zipNote)zipNote.textContent='Se activará cuando haya al menos 2 resultados válidos.';if(zipLinks)zipLinks.replaceChildren()}
function invalidateResults(){
 dispose();resetBundle();$('results').replaceChildren();
}
function uniqueZipName(name,used){
 const clean=safeName(name).replace(/^\.+/,'_')||'archivo';
 const dot=clean.lastIndexOf('.');
 const stem=dot>0?clean.slice(0,dot):clean;
 const suffix=dot>0?clean.slice(dot):'';
 let candidate=clean,number=2;
 while(used.has(candidate.toLocaleLowerCase('es'))){candidate=stem+'-'+(number++)+suffix}
 used.add(candidate.toLocaleLowerCase('es'));return candidate;
}
async function downloadBundle(){
 if(busy||bundleBusy||bundle.length<2)return;
 if(!window.JSZip){status('No se cargó el componente para descargar ZIP. Comprueba tu conexión.','warning');return}
 const total=bundle.reduce((n,item)=>n+item.blob.size,0);
 if(total>150*1024*1024){status('Para proteger la memoria, el ZIP admite hasta 150 MB combinados. Descarga los archivos por separado.','warning');return}
 bundleBusy=true;zipButton.disabled=true;refreshPresets();zipLinks.replaceChildren();
 try{
  const zip=new window.JSZip(),used=new Set();
  for(const file of bundle)zip.file(uniqueZipName(file.name,used),file.blob,{binary:true,compression:file.compression||'STORE'});
  const zipBlob=await zip.generateAsync({type:'blob',compression:'STORE',streamFiles:true},meta=>{if(zipNote)zipNote.textContent='Preparando ZIP… '+Math.round(meta.percent)+' %'});
  const result=saveLink(zipBlob,'comprimeme-archivos.zip','⬇ Guardar ZIP preparado');
  result.classList.add('zip-download');
  zipLinks.append(result);
  zipNote.textContent='ZIP listo: '+bundle.length+' archivos · '+bytes(zipBlob.size)+'. Si tu navegador no lo descarga automáticamente, usa el enlace.';
  // Mostrar siempre un enlace manual accesible, aunque se inicie la descarga automáticamente.
  result.click();
 }catch(err){status('No se pudo crear el ZIP: '+err.message,'warning');zipNote.textContent='Puedes descargar los archivos individualmente.'}
 finally{bundleBusy=false;zipButton.disabled=bundle.length<2;refreshPresets()}
}
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

// Buscar de forma adaptativa la combinación de formato, resolución y calidad
// que se acerque a un límite real de bytes. No crea archivos vacíos ni garantiza
// una calidad determinada: la interfaz indica claramente si no alcanza la meta.
async function compressImage(blob,originalExt,level,limit,requested='auto',targetBytes=0){
 const base=await raster(blob,limit);
 const original=originalExt==='jpeg'?'jpg':originalExt;
 const maxDim=Math.max(base.width,base.height);
 const types=requested==='jpg'?['image/jpeg']:requested==='webp'?['image/webp']:
   requested==='original'?[original==='png'?'image/png':original==='webp'?'image/webp':'image/jpeg']:
   original==='png'?['image/webp','image/png']:
   original==='webp'?['image/webp','image/jpeg']:['image/jpeg','image/webp'];
 const extFromType=t=>t==='image/jpeg'?'jpg':t==='image/webp'?'webp':'png';
 let bestFit=null,smallest=null;
 // El nivel mínimo admite tamaños muy pequeños; la calidad visual puede ser baja.
 // Usar seis iteraciones de búsqueda binaria como máximo por resolución.
 const steps=targetBytes>0?[1,.84,.68,.54,.42,.32,.24,.17,.12,.085,.055]:[1];
 for(const fraction of steps){
   let sized=base;
   const maxSide=Math.max(24,Math.round(maxDim*fraction));
   if(maxSide<maxDim){
     const scale=maxSide/maxDim;
     sized=document.createElement('canvas');
     sized.width=Math.max(1,Math.round(base.width*scale));
     sized.height=Math.max(1,Math.round(base.height*scale));
     const context=sized.getContext('2d');
     if(!context)throw Error('No fue posible preparar la imagen.');
     context.imageSmoothingEnabled=true;
     context.imageSmoothingQuality='high';
     context.drawImage(base,0,0,sized.width,sized.height);
   }
   for(const mime of types){
     let canvas=sized;
     if(mime==='image/jpeg'){
       canvas=document.createElement('canvas');
       canvas.width=sized.width;canvas.height=sized.height;
       const context=canvas.getContext('2d');
       if(!context)throw Error('No se pudo preparar el fondo de JPG.');
       context.fillStyle='#ffffff';
       context.fillRect(0,0,canvas.width,canvas.height);
       context.drawImage(sized,0,0);
     }
     const save=async q=>{
       const blob=await makeBlob(canvas,mime,q);
       if(blob.type&&blob.type!==mime)throw Error('Tu navegador no admite '+mime+'. Prueba otro formato.');
       return blob;
     };
     const remember=(blob,q)=>{
       const candidate={blob,extension:extFromType(mime),dimensions:canvas.width+'×'+canvas.height,qualityUsed:q,lossy:mime!=='image/png',targetMet:targetBytes>0&&blob.size<=targetBytes};
       if(!smallest||candidate.blob.size<smallest.blob.size)smallest=candidate;
       if(candidate.targetMet){
         // Un compromiso entre resolución y calidad visual.
         const score=Math.pow(Math.max(1,canvas.width*canvas.height)/(base.width*base.height),.22)*(mime==='image/png'?1.05:(.15+q*.85));
         if(!bestFit||score>bestFit.score)bestFit={...candidate,score};
       }
       return candidate;
     };
     if(!targetBytes){
       const b=await save(level);
       return remember(b,level);
     }
     if(mime==='image/png'){
       remember(await save(1),1);
     }else{
       // Primero probar una calidad razonable y la mínima; luego afinar por búsqueda.
       let high=Math.max(.1,Math.min(.95,level));
       let test=await save(high);
       let candidate=remember(test,high);
       if(!candidate.targetMet){
         let low=.06;
         test=await save(low);candidate=remember(test,low);
         if(candidate.targetMet){
           let lower=low,upper=high;
           for(let attempt=0;attempt<6;attempt++){
             const middle=(lower+upper)/2;
             const trial=remember(await save(middle),middle);
             if(trial.targetMet)lower=middle;
             else upper=middle;
           }
         }
       }
     }
   }
   // No procesar tamaños diminutos si ya se consiguió una solución razonable.
   if(bestFit&&bestFit.score>.40&&bestFit.qualityUsed>=.38)break;
 }
 const chosen=bestFit||smallest;
 if(!chosen)throw Error('No se pudo generar una versión compatible.');
 return chosen;
}
function settings(){return{q:Number(quality.value)/100,maxWidth:Number(width.value),fmt:format.value,pdf:pdfMode.value,smart:Boolean(smart?.checked),targetKB:Number(target.value||0),targetBytes:Number(target.value||0)*1000}}
async function imageFile(file,s){
 if(s.targetBytes&&file.size<=s.targetBytes)return{blob:file,name:file.name,note:'La imagen original ya cumple el límite elegido; no se alteró.',alreadyOk:true,targetMet:true};
 const limit=s.targetBytes?s.targetBytes:(s.smart?file.size:0);
 const result=await compressImage(file,ext(file.name),s.q,s.maxWidth,s.fmt,limit);
 const note='Resolución de salida: '+result.dimensions
   +(result.extension!==ext(file.name).replace('jpeg','jpg')?' · Convertida a '+result.extension.toUpperCase():'')
   +(result.lossy?' · Calidad aproximada: '+Math.round(result.qualityUsed*100)+' %':' · PNG sin pérdida por calidad')
   +(s.targetBytes?(result.targetMet?' · Objetivo de '+s.targetKB+' KB alcanzado':' · No se alcanzó el objetivo de '+s.targetKB+' KB'):'');
 return {blob:result.blob,name:nextName(file.name,'-comprimida',result.extension),note,targetMet:result.targetMet};
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
 let rejected=0,added=0;
 for(const file of append){
  const key=file.name+'|'+file.size+'|'+file.lastModified;
  if(selected.length>=MAX_FILES||!valid.has(ext(file.name))||file.size>LIMIT||file.size===0||seen.has(key)){rejected++;continue}
  selected.push(file);seen.add(key);added++
 }
 if(added)invalidateResults();renderFiles();if(rejected)status('Se omitieron '+rejected+' archivos (formato, tamaño máximo de 40 MB, duplicados o límite de 12).','warning');
 else status(selected.length+' archivo(s) seleccionados.');
}
function renderFiles(){
 list.replaceChildren();
 for(const file of selected){
  const row=document.createElement('div');row.className='file-row';
  const left=document.createElement('div');const title=document.createElement('strong');title.textContent=file.name;const sub=document.createElement('small');sub.textContent=bytes(file.size)+' · '+ext(file.name).toUpperCase();left.append(title,sub);
  const del=document.createElement('button');del.type='button';del.className='remove';del.textContent='Quitar';del.disabled=busy||bundleBusy;del.addEventListener('click',()=>{if(busy||bundleBusy)return;selected=selected.filter(f=>f!==file);invalidateResults();renderFiles();status('Archivo quitado. Vuelve a comprimir los seleccionados.');});
  row.append(left,del);list.append(row);
 }run.disabled=busy||!selected.length||bundleBusy;clear.disabled=busy||!selected.length||bundleBusy;
}
async function process(){
 if(busy||bundleBusy||!selected.length)return;busy=true;invalidateResults();renderFiles();refreshPresets();const s=settings();
 let savedCount=0;status('Trabajando. Mantén abierta esta pestaña…','working');
 for(let i=0;i<selected.length;i++){
  const file=selected[i],kind=ext(file.name),block=document.createElement('article');
  status('Procesando '+(i+1)+' de '+selected.length+': '+file.name+'…','working');block.className='result-card';
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
   if(['jpg','jpeg','png','webp'].includes(kind)){
    try{block.append(previewImage(file,out.blob))}
    catch(previewError){const info=document.createElement('p');info.className='preview-help';info.textContent='Vista previa no disponible para esta imagen.';block.append(info)}
   }
   const sizeTarget=s.targetBytes;
   const reachedTarget=sizeTarget>0&&out.blob.size<=sizeTarget;
   if(sizeTarget>0){
     const resultTarget=document.createElement('p');
     resultTarget.className=reachedTarget?'target-status target-ok':'target-status target-missed';
     resultTarget.textContent=reachedTarget
       ?'✓ Dentro del límite: '+bytes(out.blob.size)+' de '+s.targetKB+' KB'
       :'⚠ No se alcanzó el máximo de '+s.targetKB+' KB. Resultado: '+bytes(out.blob.size)+'.';
     block.append(resultTarget);
     if(!reachedTarget){
       const advice=document.createElement('p');advice.className='result-warning';
       advice.textContent=['jpg','jpeg','png','webp'].includes(kind)
         ?'Este archivo no pudo quedar por debajo de '+s.targetKB+' KB con los ajustes disponibles. Prueba una imagen más sencilla o acepta una pérdida de detalle mayor en otro editor.'
         :'En PDF, Word y archivos de texto no siempre es técnicamente posible llegar a '+s.targetKB+' KB sin perder contenido. El formato y su estructura imponen un tamaño mínimo.';
       block.append(advice);
     }
   }
   if(out.blob.size<file.size||out.alreadyOk){
    const p=document.createElement('p');p.className='result-success';
    p.textContent=out.alreadyOk?'Tu archivo original ya cumple el tamaño máximo.':reachedTarget?'¡Listo! Se alcanzó el tamaño solicitado.':'Se redujo el archivo, pero comprueba si cumple tu límite.';
    block.append(p,saveLink(out.blob,out.name,out.alreadyOk?'⬇ Descargar original (ya cumple)':'⬇ Descargar archivo comprimido'));bundle.push(['txt','md','csv','json','rtf'].includes(kind)
      ?{name:file.name,blob:file,compression:'DEFLATE'}
      :{name:out.name,blob:out.blob,compression:'STORE'});savedCount++;
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
 busy=false;renderFiles();refreshPresets();
 if(zipButton)zipButton.disabled=bundle.length<2;
 if(zipNote)zipNote.textContent=bundle.length>=2?'Tienes '+bundle.length+' archivos listos para guardar juntos en un ZIP.':bundle.length===1?'Hay 1 resultado descargable. Agrega más archivos para activar el ZIP.':'Ningún resultado elegible para ZIP. Prueba otros ajustes.';
 status('Proceso terminado. '+savedCount+' de '+selected.length+' archivo(s) disponibles para descargar.'+(savedCount<selected.length?' Consulta las alternativas en los resultados que no se redujeron.':''),savedCount===selected.length?'success':'warning');
}
input.addEventListener('change',()=>{addFiles(input.files);input.value=''});
zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('dragging')});
zone.addEventListener('dragleave',()=>zone.classList.remove('dragging'));
zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('dragging');addFiles(e.dataTransfer.files)});
quality.addEventListener('input',()=>qualityText.textContent=quality.value+' %');
clear.addEventListener('click',()=>{if(busy||bundleBusy)return;selected=[];invalidateResults();renderFiles();refreshPresets();status('Lista vacía.')});
for(const btn of presetButtons){btn.addEventListener('click',()=>{if(busy||bundleBusy)return;target.value=btn.dataset.target;refreshPresets();status('Objetivo: '+(target.value==='0'?'sin límite de tamaño':target.value+' KB')+'. Presiona Comprimir seleccionados para aplicarlo.');})}
target.addEventListener('change',()=>{refreshPresets();status('Nuevo objetivo: '+(target.value==='0'?'sin límite':target.value+' KB')+'. Vuelve a comprimir para usarlo.')});
if(zipButton)zipButton.addEventListener('click',downloadBundle);
run.addEventListener('click',process);
window.addEventListener('pagehide',dispose);
renderFiles();refreshPresets();resetBundle();
})();