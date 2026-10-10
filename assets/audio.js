/* Cat: banda sonora AMBIENT original, lenta y relajante; Web Audio sin música externa */
(() => {
"use strict";
// Progresiones originales: intervalos suaves y arpegios despacio.
const worlds=[
 {chords:[[57,60,64,69],[53,57,60,64],[55,59,62,67],[52,55,59,64]],melody:[0,2,4,7,4,2,0,-3]},
 {chords:[[60,64,67,72],[57,60,64,69],[62,65,69,74],[55,59,62,67]],melody:[0,4,7,9,7,4,2,0]},
 {chords:[[52,55,59,64],[48,52,55,60],[50,53,57,62],[55,59,62,67]],melody:[0,3,7,5,3,0,-2,0]},
 {chords:[[57,60,64,69],[55,59,62,67],[53,57,60,65],[52,56,59,64]],melody:[0,4,7,12,9,7,4,2]}
];
class CatAudio{
 constructor(){this.context=null;this.enabled=true;this.master=null;this.step=0;this.timer=0;this.chapter=-1;this.unlocked=false;this.compressor=null;this.voices=0;}
 init(){
  if(this.context){
   if(this.context.state==='suspended')this.context.resume().catch(()=>{});
   return;
  }
  const Context=window.AudioContext||window.webkitAudioContext;
  if(!Context)return;
  try{
   const ctx=new Context();
   this.context=ctx;
   this.master=ctx.createGain();
   this.master.gain.value=this.enabled?.19:0;
   this.compressor=ctx.createDynamicsCompressor();
   this.compressor.threshold.value=-18;
   this.compressor.ratio.value=2;
   this.master.connect(this.compressor);
   this.compressor.connect(ctx.destination);
   this.unlocked=true;
   ctx.resume().catch(()=>{});
  }catch(e){this.enabled=false}
 }
 toggle(){
  this.enabled=!this.enabled;
  if(this.enabled)this.init();
  if(this.context&&this.master)this.master.gain.setTargetAtTime(this.enabled?.19:0,this.context.currentTime,.08);
  return this.enabled;
 }
 note(midi,length=.35,volume=.14,shape='sine',attack=.025){
  const ctx=this.context;
  if(!this.enabled||!ctx||!this.master||ctx.state!=='running')return;
  const now=ctx.currentTime;
  const osc=ctx.createOscillator(),gain=ctx.createGain();
  osc.type=shape;
  osc.frequency.value=440*Math.pow(2,(midi-69)/12);
  gain.gain.setValueAtTime(.0001,now);
  gain.gain.exponentialRampToValueAtTime(Math.max(.0003,volume),now+attack);
  gain.gain.exponentialRampToValueAtTime(.0001,now+length);
  osc.connect(gain);gain.connect(this.master);
  osc.start(now);osc.stop(now+length+.015);
 }
 // Capa cálida de acordes en vez de pitidos estridentes.
 pad(chord){
  for(let i=0;i<chord.length;i++)this.note(chord[i]-12,2.9,.027,'sine',.37);
 }
 sfx(type){
  if(!this.enabled)return;
  this.init();
  const patterns={
   jump:[72,79],shoot:[79,84],power:[76,81,88,93],
   coin:[84,91],star:[76,83,88,95],checkpoint:[72,76,79,84],
   hurt:[48,43],bounce:[67,76],enemy:[63,69],boss:[50,55,62],
   dash:[70,76],finish:[72,76,79,84,88],click:[72],over:[59,55,50]
  };
  const notes=patterns[type]||patterns.click;
  notes.forEach((m,i)=>this.note(m,.10+i*.027,type==='shoot'?.09:.12,type==='hurt'||type==='boss'?'triangle':'sine',.007));
 }
 update(dt,chapter,playing){
  if(!playing||!this.enabled||!this.context||this.context.state!=='running')return;
  if(this.chapter!==chapter){this.chapter=chapter;this.step=0;this.timer=.05}
  this.timer-=dt;
  if(this.timer>0)return;
  const theme=worlds[chapter%4],beat=.49,index=this.step++;
  this.timer=Math.max(.03,this.timer+beat);
  const chord=theme.chords[Math.floor(index/8)%4];
  // Un acorde largo cada cuatro segundos, un arpegio cálido cada medio segundo.
  if(index%8===0)this.pad(chord);
  const key=index%8, melody=theme.melody[key];
  const anchor=chapter===2?59:64;
  if(key!==5)this.note(anchor+melody,beat*.87,.085,'sine',.035);
  if(key%2===0)this.note(chord[key%4]+12,beat*.8,.035,'triangle',.02);
 }
}
window.CAT_AUDIO=CatAudio;
})();
