/* Transcripción aislada de la interfaz. El Worker puede cancelarse inmediatamente. */
'use strict';
let transcriber=null;
const send=(type,extra={})=>self.postMessage({type,...extra});
self.onmessage=async event=>{
 const job=event.data;
 if(!job||job.type!=='transcribe')return;
 try{
  const {pipeline,env}=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1');
  env.allowLocalModels=false;
  if(env.backends?.onnx?.wasm){
   env.backends.onnx.wasm.numThreads=1;
   env.backends.onnx.wasm.proxy=false;
  }
  send('status',{text:'Cargando modelo compacto de voz (8 bits)…'});
  if(!transcriber){
   transcriber=await pipeline('automatic-speech-recognition','onnx-community/whisper-tiny',{
    device:'wasm',dtype:'q8',
    progress_callback:info=>{
     if(info?.status==='progress'&&Number.isFinite(info.progress)){
      send('download',{percent:Math.round(info.progress)});
     }
    }
   });
  }
  send('ready');
  const samples=new Float32Array(job.audio);
  const rate=16000,chunkSeconds=15,overlap=1.2;
  const chunkSize=Math.floor(chunkSeconds*rate),back=Math.floor(overlap*rate);
  const count=Math.ceil(samples.length/(chunkSize-back));
  const all=[];
  for(let i=0,start=0;start<samples.length;i++,start+=chunkSize-back){
   const end=Math.min(samples.length,start+chunkSize);
   const chunk=samples.subarray(start,end);
   // No chunk_length_s on small slices: avoids the built-in pipeline copying
   // 30s windows with stride, and caps per-inference allocations.
   const options={return_timestamps:true,task:'transcribe'};
   if(job.language)options.language=job.language;
   const result=await transcriber(chunk,options);
   let sections=(Array.isArray(result?.chunks)?result.chunks:[]).filter(x=>x?.text?.trim());
   if(!sections.length&&result?.text?.trim()){
    sections=[{text:result.text,timestamp:[0,(end-start)/rate]}];
   }
   for(const x of sections){
    const stamp=Array.isArray(x.timestamp)?x.timestamp:[0,null];
    const begin=Math.max(0,Number.isFinite(stamp[0])?stamp[0]:0)+start/rate;
    const until=(Number.isFinite(stamp[1])?stamp[1]:(end-start)/rate)+start/rate;
    // Avoid duplicate phrases in the overlapping 1.2s window.
    if(i&&begin<start/rate+.55)continue;
    const line={start:begin,end:Math.max(begin+.3,until),text:x.text.trim(),sourceTimed:true};
    if(line.text&&all.length<1000)all.push(line);
   }
   send('segment',{lines:all.slice(),done:Math.min(samples.length,end)/samples.length,
    index:i+1,count});
  }
  send('done',{lines:all});
 }catch(err){
  send('error',{message:String(err?.message||err||'Error al reconocer voz').slice(0,280)});
 }
};