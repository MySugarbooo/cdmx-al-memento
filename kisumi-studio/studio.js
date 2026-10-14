'use strict';
(()=>{
 const $=id=>document.getElementById(id);
 const canvas=$('visualizer'),g=canvas.getContext('2d',{alpha:false});
 const audio=$('audio'),fileInput=$('audio-file'),drop=$('audio-drop');
 const CW=canvas.width,CH=canvas.height,TAU=Math.PI*2;
 const state={style:'aurora',file:null,url:null,ctx:null,src:null,analyser:null,recDest:null,record:null,blobURL:null,lyrics:[],sync:false,syncIndex:0,exporting:false,intensity:.72,sensitivity:.65,
  bass:0,mid:0,treble:0,overall:0,freq:new Uint8Array(1024),timeData:new Uint8Array(2048)};
 const particles=Array.from({length:160},(_,i)=>({seed:i,x:((i*9176+13)%1009)/1009,y:((i*3079+23)%997)/997,
  z:.28+((i*73)%100)/100,s:.5+((i*31)%79)/28}));
 const palettes={
  aurora:['#f671df','#9975ff','#67eeec'],laser:['#ff4aa3','#a683ff','#68fff3'],
  galaxy:['#ef9afa','#6278ff','#85e8fa'],spectrum:['#fb6bc5','#927bfc','#75fbe0']
 };
 const fix=n=>Number.isFinite(n)?Math.max(0,n):0;
 const clock=n=>{n=Math.floor(fix(n));return String(Math.floor(n/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');};
 const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
 const reduced=window.matchMedia?.('(prefers-reduced-motion:reduce)').matches===true;
 const status=(id,text)=>{const el=$(id);if(el)el.textContent=text;};
 const displayLyrics=()=>state.lyrics.filter(x=>x.text.trim().length).length;
 function setPlayState(){const playing=!audio.paused; $('play-btn').textContent=playing?'Ⅱ':'▶';$('play-btn').setAttribute('aria-label',playing?'Pausar':'Reproducir');}
 function updateTransport(){
  $('time-now').textContent=clock(audio.currentTime);$('time-total').textContent=clock(audio.duration);
  if(Number.isFinite(audio.duration)&&audio.duration>0){$('seek').value=String(Math.round((audio.currentTime/audio.duration)*1000));}
  updateHighlight();
 }
 async function initSound(){
  if(state.ctx){if(state.ctx.state==='suspended')await state.ctx.resume();return;}
  const Audio=window.AudioContext||window.webkitAudioContext;
  if(!Audio)throw Error('Tu navegador no permite analizar el audio.');
  const ac=new Audio();const analyser=ac.createAnalyser();
  analyser.fftSize=2048;analyser.smoothingTimeConstant=.82;
  const source=ac.createMediaElementSource(audio);
  const dest=ac.createMediaStreamDestination();
  source.connect(analyser);analyser.connect(ac.destination);analyser.connect(dest);
  state.ctx=ac;state.src=source;state.analyser=analyser;state.recDest=dest;
  state.freq=new Uint8Array(analyser.frequencyBinCount);
 }
 async function play(){
  if(!state.file)return;
  try{
   await initSound();
   if(audio.paused)await audio.play();else audio.pause();
   setPlayState();
  }catch(err){status('audio-status','No fue posible reproducir: '+String(err.message||err));}
 }
 function loadFile(file){
  if(!file)return;
  if(!file.type.startsWith('audio/')&&!/\.(?:mp3|m4a|wav|ogg|aac|flac|opus|aiff|mp4)$/i.test(file.name)){
   status('audio-status','Selecciona un archivo de audio compatible.');return;
  }
  if(state.exporting){status('audio-status','Detén la grabación antes de cambiar de audio.');return;}
  audio.pause();if(state.url)URL.revokeObjectURL(state.url);
  state.file=file;state.url=URL.createObjectURL(file);
  audio.src=state.url;audio.volume=Number($('volume').value);
  audio.load();setPlayState();
  $('track-title').textContent=file.name.replace(/\.[^.]+$/,'').slice(0,85);
  $('track-meta').textContent=(file.size/1024/1024).toFixed(1)+' MB · Archivo local';
  status('audio-status','✓ '+file.name+' · Listo para reproducir');
  $('empty-overlay').hidden=true;$('play-btn').disabled=false;
  $('export-btn').disabled=false;$('seek').disabled=false;
  if(state.lyrics.length)readLyrics(false);
 }
 fileInput.addEventListener('change',()=>loadFile(fileInput.files?.[0]));
 ['dragenter','dragover'].forEach(name=>drop.addEventListener(name,event=>{event.preventDefault();drop.classList.add('is-over');}));
 ['dragleave','drop'].forEach(name=>drop.addEventListener(name,event=>{event.preventDefault();drop.classList.remove('is-over');}));
 drop.addEventListener('drop',event=>{const f=event.dataTransfer?.files?.[0];if(f)loadFile(f)});
 drop.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();fileInput.click();}});
 $('play-btn').addEventListener('click',play);
 $('mute-btn').addEventListener('click',()=>{audio.muted=!audio.muted;$('mute-btn').textContent=audio.muted?'♩':'♫';});
 $('volume').addEventListener('input',event=>{audio.volume=Number(event.target.value);audio.muted=false;$('mute-btn').textContent='♫';});
 $('seek').addEventListener('input',event=>{
  if(Number.isFinite(audio.duration)&&audio.duration>0)audio.currentTime=Number(event.target.value)/1000*audio.duration;
  updateTransport();
 });
 audio.addEventListener('loadedmetadata',()=>{updateTransport();status('audio-status','✓ Duración: '+clock(audio.duration)+' · Reproduce y edita tu video');if(state.lyrics.length&&!state.lyrics.some(x=>x.sourceTimed))readLyrics(false);});
 audio.addEventListener('timeupdate',updateTransport);
 audio.addEventListener('pause',setPlayState);audio.addEventListener('play',setPlayState);
 audio.addEventListener('error',()=>status('audio-status','El navegador no puede reproducir este formato. Prueba MP3 o WAV.'));
 audio.addEventListener('ended',()=>{setPlayState();if(state.exporting)finishRecording();});
 $('fullscreen-btn').addEventListener('click',async()=>{
  const box=$('canvas-shell');
  try{if(document.fullscreenElement)await document.exitFullscreen();else await (box.requestFullscreen?box.requestFullscreen():Promise.reject(Error('Pantalla completa no disponible')));}
  catch{status('audio-status','La pantalla completa no está disponible en este navegador.');}
 });
 for(const b of document.querySelectorAll('[data-style]')){
  b.addEventListener('click',()=>{
   state.style=b.dataset.style;
   document.querySelectorAll('[data-style]').forEach(button=>{
    const on=button===b;button.classList.toggle('active',on);button.setAttribute('aria-pressed',String(on));
   });
  });
 }
 for(const key of ['intensity','sensitivity']){
  const node=$(key);
  node.addEventListener('input',()=>{state[key]=Number(node.value)/100;$(key+'-value').textContent=node.value+'%';});
 }
 // LRC [mm:ss.xx], [hh:mm:ss.xxx], SRT and WebVTT.
 function parseTimestamp(raw){
  const str=String(raw||'').trim().replace(',','.');
  const parts=str.split(':').map(Number);
  if(parts.some(x=>!Number.isFinite(x))||(parts.length!==2&&parts.length!==3))return NaN;
  const s=parts.length===2?parts[0]*60+parts[1]:parts[0]*3600+parts[1]*60+parts[2];
  return s>=0?s:NaN;
 }
 function parseLyrics(raw){
  const text=String(raw||'').replace(/\r/g,'').trim();if(!text)return[];
  const lines=text.split('\n');let rows=[];
  // SRT + VTT often contain blocks with ids and time arrow.
  if(lines.some(x=>x.includes('-->'))){
   const blocks=text.replace(/^WEBVTT[^\n]*\n/,'').split(/\n\s*\n/);
   for(const block of blocks){
    const all=block.split('\n').map(x=>x.trim()).filter(Boolean);
    const n=all.findIndex(x=>x.includes('-->'));if(n<0)continue;
    const [a,b]=all[n].split('-->').map(v=>parseTimestamp(v.trim().split(/\s+/)[0]));
    const t=all.slice(n+1).filter(x=>!/^\d+$/.test(x)).join(' ').trim();
    if(Number.isFinite(a)&&t)rows.push({start:a,end:Number.isFinite(b)?b:a+4,text:t,sourceTimed:true});
   }
  }else{
   let plain=[];
   for(const line of lines){
    const stamps=[...line.matchAll(/\[(\d{1,2}:\d{2}(?:[:.]\d{1,3})?(?:\.\d{1,3})?)\]/g)];
    let phrase=line.replace(/\[\d{1,2}:\d{2}(?:[:.]\d{1,3})?(?:\.\d{1,3})?\]/g,'').trim();
    if(/^\[(?:ar|ti|al|by|offset):/i.test(line)||!phrase)continue;
    if(stamps.length){
     for(const m of stamps){const t=parseTimestamp(m[1]);if(Number.isFinite(t))rows.push({start:t,end:t+4,text:phrase,sourceTimed:true});}
    }else plain.push(phrase);
   }
   if(!rows.length&&plain.length){
    const duration=Number.isFinite(audio.duration)&&audio.duration>0?audio.duration:Math.max(plain.length*4,40);
    const usable=Math.max(0,duration-2),step=usable/plain.length;
    rows=plain.map((phrase,i)=>({start:i*step,end:(i+1)*step,text:phrase,sourceTimed:false}));
   }
  }
  rows=rows.filter(x=>x.text.trim()).sort((a,b)=>a.start-b.start);
  for(let i=0;i<rows.length;i++){
   const next=rows[i+1];rows[i].end=clamp(next?Math.min(rows[i].end||next.start,next.start):rows[i].end||rows[i].start+4,rows[i].start+.2,
    Math.max(rows[i].start+.2,Number.isFinite(audio.duration)?audio.duration+2:36000));
  }
  return rows.slice(0,2000);
 }
 function readLyrics(fromText=true){
  if(fromText)state.lyrics=parseLyrics($('lyrics-text').value);
  else if(state.lyrics.length&&!state.lyrics.some(x=>x.sourceTimed))state.lyrics=parseLyrics($('lyrics-text').value);
  state.sync=false;state.syncIndex=0;showRows();updateHighlight();
  status('audio-status',state.lyrics.length?'✓ '+state.lyrics.length+' líneas de letra cargadas.':'Sin letras; puedes crear solo el visualizador.');
 }
 function showRows(){
  const list=$('lyric-lines');list.replaceChildren();
  const total=state.lyrics.length;
  $('lyric-count').textContent=total+' '+(total===1?'línea':'líneas');
  $('sync-start').disabled=total===0||!state.file;
  $('sync-next').disabled=!state.sync;
  $('export-lrc').disabled=total===0;$('clear-lyrics').disabled=total===0;
  if(!total){list.append(makeElement('p','empty-lines','Tus versos aparecerán aquí para ajustar el tiempo.'));return;}
  state.lyrics.forEach((line,i)=>{
   const row=makeElement('div','lyric-row');row.dataset.line=String(i);
   const input=document.createElement('input');input.type='text';input.inputMode='decimal';
   input.value=clock(line.start)+'.'+String(Math.round((line.start%1)*100)).padStart(2,'0');
   input.setAttribute('aria-label','Inicio de la línea '+(i+1));
   input.addEventListener('change',()=>{const n=parseTimestamp(input.value);if(Number.isFinite(n)){line.start=n;line.sourceTimed=true;state.lyrics.sort((a,b)=>a.start-b.start);updateHighlight();}
    else input.value=clock(line.start)+'.'+String(Math.round((line.start%1)*100)).padStart(2,'0');});
   const text=makeElement('span','lyric-text',line.text);
   const btn=makeElement('button','','×');btn.type='button';btn.title='Eliminar línea';
   btn.addEventListener('click',()=>{state.lyrics.splice(i,1);showRows();});
   row.append(input,text,btn);list.append(row);
  });
 }
 function makeElement(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
 function currentLine(time){
  if(!state.lyrics.length)return-1;
  let idx=-1;
  for(let i=0;i<state.lyrics.length;i++)if(time>=state.lyrics[i].start)idx=i;else break;
  return idx;
 }
 let highlighted=-2;
 function updateHighlight(){
  const n=currentLine(audio.currentTime);
  if(n===highlighted)return;
  highlighted=n;
  for(const el of $('lyric-lines').querySelectorAll('.lyric-row')){
   el.classList.toggle('active',Number(el.dataset.line)===n);
  }
 }
 $('apply-lyrics').addEventListener('click',()=>readLyrics(true));
 $('lyrics-file').addEventListener('change',async event=>{
  const file=event.target.files?.[0];if(!file)return;
  try{$('lyrics-text').value=await file.text();readLyrics(true);}catch{status('audio-status','No se pudo abrir el archivo de texto.');}
 });
 $('clear-lyrics').addEventListener('click',()=>{state.lyrics=[];$('lyrics-text').value='';showRows();});
 for(const button of document.querySelectorAll('[data-pane]')){
  button.addEventListener('click',()=>{
   const selected=button.dataset.pane;
   for(const tab of document.querySelectorAll('[data-pane]')){const match=tab.dataset.pane===selected;tab.classList.toggle('selected',match);tab.setAttribute('aria-selected',String(match));}
   $('pane-write').hidden=selected!=='write';$('pane-auto').hidden=selected!=='auto';
  });
 }
 $('sync-start').addEventListener('click',async()=>{
  if(!state.file||!state.lyrics.length)return;
  if(state.sync){state.sync=false;$('sync-start').textContent='◉ Marcar tiempos mientras suena';$('sync-next').disabled=true;return;}
  state.sync=true;state.syncIndex=0;
  $('sync-start').textContent='■ Finalizar marcado';
  $('sync-next').disabled=false;
  audio.currentTime=0;await initSound();try{await audio.play()}catch{}
  status('audio-status','Durante la reproducción, pulsa «Marcar siguiente línea» justo al empezar cada verso.');
 });
 function markNext(){
  if(!state.sync||state.syncIndex>=state.lyrics.length)return;
  const i=state.syncIndex++,time=audio.currentTime;
  state.lyrics[i].start=time;state.lyrics[i].sourceTimed=true;
  if(i>0)state.lyrics[i-1].end=time;
  if(state.syncIndex>=state.lyrics.length){
   state.sync=false;$('sync-start').textContent='◉ Marcar tiempos mientras suena';
   $('sync-next').disabled=true;status('audio-status','✓ Sincronización manual completada.');
  }
  showRows();
 }
 $('sync-next').addEventListener('click',markNext);
 document.addEventListener('keydown',event=>{
  if(event.code!=='Space'||!state.sync||event.repeat)return;
  const tag=event.target?.tagName;if(['INPUT','TEXTAREA','SELECT','BUTTON'].includes(tag)||event.target?.isContentEditable)return;
  event.preventDefault();markNext();
 });
 function lrcStamp(n){const mm=Math.floor(fix(n)/60),ss=fix(n)%60;return '['+String(mm).padStart(2,'0')+':'+ss.toFixed(2).padStart(5,'0')+']';}
 function textDownload(content,name,type){
  const url=URL.createObjectURL(new Blob([content],{type}));
  const link=makeElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
 }
 $('export-lrc').addEventListener('click',()=>{
  const text=state.lyrics.map(x=>lrcStamp(x.start)+x.text).join('\n')+'\n';
  textDownload(text,'kisumi-letras.lrc','text/plain;charset=utf-8');
 });
 // Whisper Tiny multilingual via Transformers.js. La inferencia es local
 // (el navegador descarga el modelo en la primera ejecución).
 let recognizer=null,transcribing=false;
 async function speechSamples(file){
  const C=window.AudioContext||window.webkitAudioContext;
  if(!C)throw Error('Este navegador no dispone de audio compatible.');
  const context=new C();
  try{
   const data=await file.arrayBuffer();
   const buffer=await context.decodeAudioData(data);
   if(buffer.duration>8*60)throw Error('Para evitar agotar la memoria, usa un audio de 8 minutos o menos en transcripción automática.');
   const size=Math.round(buffer.duration*16000);
   const mono=new Float32Array(size),channels=Array.from({length:buffer.numberOfChannels},(_,i)=>buffer.getChannelData(i)),ratio=buffer.sampleRate/16000;
   for(let i=0;i<size;i++){
    const pos=i*ratio,idx=Math.floor(pos),t=pos-idx;let sum=0;
    for(const ch of channels)sum+=(ch[idx]||0)*(1-t)+(ch[Math.min(idx+1,ch.length-1)]||0)*t;
    mono[i]=sum/channels.length;
   }
   return mono;
  }finally{context.close().catch(()=>{});}
 }
 $('transcribe-btn').addEventListener('click',async()=>{
  if(!state.file){status('ai-status','Primero sube un audio para analizarlo.');return;}
  if(transcribing)return;
  transcribing=true;$('transcribe-btn').disabled=true;
  const progress=$('ai-progress'),bar=$('ai-progress-bar');progress.hidden=false;bar.style.width='6%';
  try{
   status('ai-status','Preparando el audio localmente…');
   const samples=await speechSamples(state.file);bar.style.width='12%';
   if(!recognizer){
    status('ai-status','Descargando Whisper Tiny multilingüe. Puede tardar varios minutos la primera vez…');
    const module=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1');
    const {pipeline,env}=module;
    env.allowLocalModels=false;
    recognizer=await pipeline('automatic-speech-recognition','onnx-community/whisper-tiny',{
     device:'wasm',progress_callback:info=>{
      if(info?.status==='progress'&&Number.isFinite(info.progress)){
       bar.style.width=(12+Math.min(1,info.progress/100)*48)+'%';
       status('ai-status','Descargando modelo: '+Math.round(info.progress)+'% · Puede tardar…');
      }else if(info?.status==='ready'){bar.style.width='60%';}
     }
    });
   }
   bar.style.width='64%';
   status('ai-status','Reconociendo voz y tiempos; no cierres esta pestaña…');
   const opts={chunk_length_s:30,stride_length_s:5,return_timestamps:true,task:'transcribe'};
   if($('speech-language').value)opts.language=$('speech-language').value;
   const result=await recognizer(samples,opts);
   let chunks=Array.isArray(result?.chunks)?result.chunks.filter(x=>x&&typeof x.text==='string'):[];
   if(!chunks.length&&result?.text)chunks=[{text:result.text,timestamp:[0,Math.min(audio.duration||30,30)]}];
   const lines=chunks.map((x,i)=>{
    const ts=Array.isArray(x.timestamp)?x.timestamp:[i*4,(i+1)*4];
    const start=Number.isFinite(ts[0])?Math.max(0,ts[0]):i*4;
    return {start,end:Number.isFinite(ts[1])?ts[1]:start+4,text:x.text.trim(),sourceTimed:true};
   }).filter(x=>x.text.length).sort((a,b)=>a.start-b.start);
   if(!lines.length)throw Error('No se identificaron palabras en este audio. Prueba importar la letra como texto.');
   state.lyrics=lines;$('lyrics-text').value=lines.map(x=>lrcStamp(x.start)+x.text).join('\n');
   state.sync=false;showRows();bar.style.width='100%';
   status('ai-status','✓ Reconocidas '+lines.length+' frases con tiempos aproximados. Revisa la letra, especialmente si hay canto o instrumentos.');
   document.querySelector('[data-pane="write"]')?.click();
  }catch(e){
   status('ai-status','No se pudo transcribir aquí: '+String(e.message||e).slice(0,240)+'. Puedes importar TXT, SRT o LRC y sincronizar manualmente.');
   console.warn('Reconocimiento local no disponible:',e);
  }finally{transcribing=false;$('transcribe-btn').disabled=false;setTimeout(()=>{progress.hidden=true;bar.style.width='0%';},2200);}
 });
 function energy(){
  if(!state.analyser||audio.paused){state.bass*=.95;state.mid*=.95;state.treble*=.95;state.overall*=.95;return;}
  state.analyser.getByteFrequencyData(state.freq);
  const mean=(a,b)=>{let n=0;for(let i=a;i<Math.min(state.freq.length,b);i++)n+=state.freq[i];return n/Math.max(1,b-a)/255;};
  const multiplier=.7+state.sensitivity*1.6;
  state.bass=state.bass*.68+Math.min(1,mean(1,14)*multiplier)*.32;
  state.mid=state.mid*.68+Math.min(1,mean(14,120)*multiplier)*.32;
  state.treble=state.treble*.7+Math.min(1,mean(120,470)*multiplier)*.3;
  state.overall=state.bass*.52+state.mid*.3+state.treble*.18;
 }
 function light(x,y,r,color,opacity){
  const grad=g.createRadialGradient(x,y,0,x,y,r);
  grad.addColorStop(0,color);grad.addColorStop(1,'#090b2200');
  g.save();g.globalAlpha=opacity;g.fillStyle=grad;g.fillRect(x-r,y-r,2*r,2*r);g.restore();
 }
 function softBackground(t){
  const grad=g.createLinearGradient(0,0,CW,CH);
  grad.addColorStop(0,'#0b0821');grad.addColorStop(.48,state.style==='galaxy'?'#09082a':'#101329');grad.addColorStop(1,'#09091b');
  g.fillStyle=grad;g.fillRect(0,0,CW,CH);
  const n=state.intensity;
  light(CW*.22+Math.sin(t*.00035)*110,CH*.3,450,'#dc44cc',.2+n*.17+state.bass*.2);
  light(CW*.81,CH*.73+Math.cos(t*.0003)*75,430,'#4b7edc',.18+n*.12+state.mid*.2);
 }
 function starfield(t,color){
  g.save();
  for(const p of particles){
   const x=(p.x*CW+Math.sin(t*.0001*p.z+p.seed)*30+CW)%CW,y=(p.y*CH+Math.cos(t*.00013*p.z+p.seed)*18+CH)%CH;
   const r=p.s*(.7+state.treble*1.4),a=(.18+.65*p.z)*(1+state.overall*.35);
   g.fillStyle='rgba(214,228,255,'+clamp(a,0,1)+')';g.beginPath();g.arc(x,y,r,0,TAU);g.fill();
  }
  g.restore();
 }
 function drawAurora(t){
  const colors=palettes.aurora;
  starfield(t);
  g.save();g.globalCompositeOperation='lighter';
  const amp=(75+state.mid*165)*(.3+state.intensity);
  for(let j=0;j<6;j++){
   g.beginPath();g.lineWidth=22+j*5;g.strokeStyle=colors[j%3];g.globalAlpha=.05+state.intensity*.034;
   for(let x=-30;x<=CW+30;x+=18){
    const y=CH*.4+(j-2.5)*32+
     Math.sin(x*.0047+t*.00046+j*.8)*(amp*.7)+
     Math.sin(x*.009-t*.0007+j*.55)*(amp*.4);
    if(x===-30)g.moveTo(x,y);else g.lineTo(x,y);
   }
   g.stroke();
   g.lineWidth=2.4;g.globalAlpha=.45+state.intensity*.3;g.stroke();
  }
  g.restore();
 }
 function drawLaser(t){
  starfield(t);
  const n=48,gain=1+state.bass*1.6;
  g.save();g.globalCompositeOperation='lighter';
  for(let i=0;i<n;i++){
   const angle=i*TAU/n+t*.000065*(i%3===0?-1:1);
   const inner=105+state.bass*54,out=475+Math.sin(t*.001+i*.7)*75*gain;
   g.beginPath();g.moveTo(CW/2+Math.cos(angle)*inner,CH/2+Math.sin(angle)*inner);
   g.lineTo(CW/2+Math.cos(angle)*out,CH/2+Math.sin(angle)*out);
   g.strokeStyle=palettes.laser[i%3];g.lineWidth=i%7===0?2.5:1;
   g.globalAlpha=.12+state.intensity*.34+state.bass*.26;g.stroke();
  }
  g.globalAlpha=.7;g.strokeStyle='#efa3ff';g.lineWidth=3;
  g.beginPath();g.arc(CW/2,CH/2,115+state.bass*54,0,TAU);g.stroke();g.restore();
 }
 function drawGalaxy(t){
  starfield(t);
  const cx=CW/2,cy=CH/2,n=particles.length;
  g.save();g.globalCompositeOperation='screen';
  for(let i=0;i<n;i++){
   const p=particles[i];const angle=i*2.399+t*.000065*(.4+p.z);
   const radius=Math.sqrt(i/n)*340*(.85+state.bass*.35);
   const x=cx+Math.cos(angle)*radius*1.4,y=cy+Math.sin(angle)*radius*.67;
   const color=palettes.galaxy[i%3],size=(.7+p.s)*(.5+state.intensity+state.treble);
   g.globalAlpha=.25+state.intensity*.5;g.fillStyle=color;g.beginPath();g.arc(x,y,size,0,TAU);g.fill();
  }
  g.restore();light(cx,cy,200,'#aa5ffd',.2+state.bass*.26);
 }
 function drawSpectrum(t){
  const n=90,width=CW/n,peak=state.overall;
  g.save();g.globalCompositeOperation='lighter';
  for(let i=0;i<n;i++){
   const band=state.freq[Math.min(state.freq.length-1,2+Math.floor(i*state.freq.length/n*.8))]||0;
   const rest=audio.paused?(.1+.08*Math.sin(t*.0008+i*.2)):(band/255);
   const height=13+rest*(215+state.intensity*190);
   const gradient=g.createLinearGradient(0,CH*.5-height,0,CH*.5+height);
   gradient.addColorStop(0,'#8bf4ee');gradient.addColorStop(.5,'#b466fc');gradient.addColorStop(1,'#ff68c9');
   g.globalAlpha=.55+state.intensity*.4;g.fillStyle=gradient;
   g.fillRect(i*width+2,CH*.5-height,width-4,height*.96);
   g.fillRect(i*width+2,CH*.5+6,width-4,height*.25);
  }
  g.restore();starfield(t);
 }
 function centre(t){
  const bass=state.bass,s=75+bass*44;
  light(CW/2,CH/2,145+bass*105,'#c75be7',.12+state.intensity*.3);
  g.save();g.translate(CW/2,CH/2);
  g.rotate(t*.000075);g.strokeStyle=palettes[state.style][0];g.lineWidth=2;g.globalAlpha=.3+state.intensity*.4;
  g.beginPath();g.arc(0,0,s+20,0,TAU);g.stroke();
  g.rotate(-t*.0002);g.strokeStyle=palettes[state.style][2];g.globalAlpha=.27+state.intensity*.32;
  g.beginPath();g.arc(0,0,s+32,-Math.PI*.7,Math.PI*.22);g.stroke();
  g.restore();
 }
 function wrapLine(text,maxWidth,maxLines=3){
  const words=String(text).split(/\s+/).filter(Boolean);
  if(!words.length)return[];
  const lines=[];let line='';
  // CJK sin espacios: dividir por caracteres al exceder ancho.
  const units=words.length===1?[...text]:words;
  for(const word of units){
   const glue=words.length===1?'':' ';
   const candidate=line?line+glue+word:word;
   if(g.measureText(candidate).width>maxWidth&&line){lines.push(line);line=word;}
   else line=candidate;
  }
  if(line)lines.push(line);return lines.slice(0,maxLines);
 }
 function drawKaraoke(){
  if(!$('show-lyrics').checked)return;
  const idx=currentLine(audio.currentTime);if(idx<0)return;
  const item=state.lyrics[idx];if(!item)return;
  const text=item.text.trim();if(!text)return;
  g.save();
  const fontSize=text.length>95?35:text.length>60?41:51;
  g.font='800 '+fontSize+'px system-ui, Arial, sans-serif';g.textAlign='center';g.textBaseline='middle';
  const lines=wrapLine(text,CW*.81,3);
  const rowGap=fontSize*1.28;const baseY=CH*.79-(lines.length-1)*rowGap/2;
  const bgY=baseY-fontSize*.85,block=lines.length*rowGap+fontSize*.75;
  const grad=g.createLinearGradient(0,bgY,0,bgY+block);
  grad.addColorStop(0,'#07071400');grad.addColorStop(.45,'#080618bb');grad.addColorStop(1,'#070714c9');
  g.fillStyle=grad;g.fillRect(0,bgY,CW,block);
  for(let i=0;i<lines.length;i++){
   const y=baseY+i*rowGap;g.shadowColor='#ef66d3';g.shadowBlur=16;
   g.lineWidth=4;g.strokeStyle='#130e28';g.strokeText(lines[i],CW/2,y);
   g.fillStyle='#fff5ff';g.fillText(lines[i],CW/2,y);
  }
  if(Number.isFinite(item.end)&&item.end>item.start){
   const progress=clamp((audio.currentTime-item.start)/(item.end-item.start),0,1);
   const w=CW*.52;g.fillStyle='#ffffff30';g.fillRect((CW-w)/2,CH-37,w,4);
   g.fillStyle='#f57bdb';g.fillRect((CW-w)/2,CH-37,w*progress,4);
  }
  g.restore();
 }
 let last=0;
 function frame(t){
  requestAnimationFrame(frame);
  if(t-last<16&&!state.exporting)return;last=t;
  energy();softBackground(t);
  if(state.style==='aurora')drawAurora(t);
  if(state.style==='laser')drawLaser(t);
  if(state.style==='galaxy')drawGalaxy(t);
  if(state.style==='spectrum')drawSpectrum(t);
  if(state.style!=='spectrum')centre(t);
  if(state.file)drawKaraoke();
 }
 requestAnimationFrame(frame);
 // La captura usa Canvas+WebAudio y no depende de servidores.
 const mimeCandidates=['video/mp4;codecs=avc1.42E01E,mp4a.40.2','video/mp4','video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'];
 const chosen=window.MediaRecorder?mimeCandidates.find(x=>MediaRecorder.isTypeSupported(x)):null;
 $('format-label').textContent=chosen?.startsWith('video/mp4')?'MP4':chosen?'WEBM':'NO DISP.';
 if(!chosen)status('export-status','Este navegador no permite exportar video directamente. Puedes grabar la pantalla desde tu dispositivo.');
 function finishRecording(){
  if(state.record&&state.record.state!=='inactive')state.record.stop();
 }
 $('stop-record').addEventListener('click',()=>{audio.pause();finishRecording();});
 $('export-btn').addEventListener('click',async()=>{
  if(!state.file)return;
  if(!chosen||typeof canvas.captureStream!=='function'){status('export-status','No es posible capturar el lienzo en este navegador. Prueba Chrome/Edge en PC o la grabación de pantalla.');return;}
  if(state.exporting)return;
  let visualStream,all,rec;
  try{
   await initSound();
   if(!state.recDest?.stream.getAudioTracks().length)throw Error('No se pudo crear una pista de audio.');
   audio.pause();audio.currentTime=0;updateTransport();
   visualStream=canvas.captureStream(30);
   all=new MediaStream([...visualStream.getVideoTracks(),...state.recDest.stream.getAudioTracks()]);
   rec=new MediaRecorder(all,{mimeType:chosen,videoBitsPerSecond:6000000,audioBitsPerSecond:160000});
   const chunks=[];
   rec.ondataavailable=e=>{if(e.data?.size)chunks.push(e.data)};
   rec.onerror=e=>status('export-status','Falló la grabación: '+(e.error?.message||'error de codificador'));
   rec.onstop=()=>{
    state.exporting=false;$('export-btn').disabled=false;$('stop-record').hidden=true;
    visualStream?.getTracks().forEach(tr=>tr.stop());
    if(state.blobURL)URL.revokeObjectURL(state.blobURL);
    const result=new Blob(chunks,{type:rec.mimeType||chosen});
    if(result.size){
     state.blobURL=URL.createObjectURL(result);
     const link=$('download-video');link.href=state.blobURL;
     const ext=chosen.startsWith('video/mp4')?'mp4':'webm';
     link.download='kisumi-neon-studio-'+Date.now()+'.'+ext;link.hidden=false;
     status('export-status','✓ Video listo ('+(result.size/1024/1024).toFixed(1)+' MB). Pulsa descargar.');
    }else status('export-status','No se generó un archivo válido. Prueba otro navegador.');
   };
   $('download-video').hidden=true;state.exporting=true;state.record=rec;
   $('export-btn').disabled=true;$('stop-record').hidden=false;
   rec.start(1000);
   await audio.play();
   status('export-status','● Grabando con sonido a velocidad real · '+clock(audio.duration)+'. Mantén la pestaña abierta.');
  }catch(e){
   state.exporting=false;$('export-btn').disabled=false;$('stop-record').hidden=true;
   if(rec?.state==='recording')rec.stop();
   visualStream?.getTracks().forEach(x=>x.stop());
   status('export-status','No se pudo iniciar la exportación: '+String(e.message||e)+'.');
  }
 });
 audio.addEventListener('timeupdate',()=>{
  if(state.exporting)status('export-status','● Grabando video… '+clock(audio.currentTime)+' / '+clock(audio.duration)+'. No cierres la pestaña.');
 });
 window.addEventListener('beforeunload',()=>{
  if(state.url)URL.revokeObjectURL(state.url);
  if(state.blobURL)URL.revokeObjectURL(state.blobURL);
 });
 showRows();
})();
