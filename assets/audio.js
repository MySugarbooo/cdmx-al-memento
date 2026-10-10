/* Cat • música chiptune ORIGINAL generada en tiempo real con Web Audio */
(() => {
"use strict";
const tunes=[
 [0,4,7,12,7,4,2,7,0,4,9,7,5,4,2,-3],
 [0,2,4,7,11,7,4,2,0,4,7,12,11,7,4,2],
 [0,3,7,10,7,3,0,-2,0,5,7,10,12,10,7,3],
 [0,4,7,9,12,9,7,4,5,9,12,16,14,12,9,7]
];
class CatAudio{
 constructor(){this.context=null;this.enabled=true;this.step=0;this.timer=0;this.chapter=-1;this.master=null;this.unlocked=false;}
 init(){
  if(this.context){if(this.context.state==='suspended')this.context.resume().catch(()=>{});return}
  const AudioCtx=window.AudioContext||window.webkitAudioContext;
  if(!AudioCtx)return;
  try{
   const ctx=new AudioCtx;this.context=ctx;
   this.master=ctx.createGain();this.master.gain.value=.14;
   this.master.connect(ctx.destination);
   this.unlocked=true;
   ctx.resume().catch(()=>{});
  }catch(_){this.enabled=false;}
 }
 toggle(){
  this.enabled=!this.enabled;
  if(this.enabled)this.init();
  if(this.master&&this.context)this.master.gain.setTargetAtTime(this.enabled?.14:0,this.context.currentTime,.08);
  return this.enabled;
 }
 note(midi,duration=.13,volume=.22,kind='triangle'){
  if(!this.enabled||!this.context||!this.master||this.context.state!=='running')return;
  const ctx=this.context,t=ctx.currentTime;
  const oscillator=ctx.createOscillator(),envelope=ctx.createGain();
  oscillator.type=kind;oscillator.frequency.value=440*Math.pow(2,(midi-69)/12);
  envelope.gain.setValueAtTime(0.0001,t);
  envelope.gain.exponentialRampToValueAtTime(Math.max(.001,volume),t+.013);
  envelope.gain.exponentialRampToValueAtTime(.0001,t+duration);
  oscillator.connect(envelope);envelope.connect(this.master);
  oscillator.start(t);oscillator.stop(t+duration+.02);
 }
 sfx(type){
  if(!this.enabled)return;
  this.init();
  const notes={jump:[[76,.09],[83,.14]],coin:[[88,.07],[95,.17]],star:[[80,.09],[84,.13],[88,.18],[92,.31]],hurt:[[47,.14],[40,.25]],bounce:[[62,.1],[74,.2]],checkpoint:[[76,.11],[83,.15],[88,.27]],finish:[[72,.13],[76,.13],[79,.13],[84,.34]],click:[[76,.065]],over:[[57,.2],[53,.2],[48,.32]]}[type];
  if(!notes)return;
  notes.forEach(([pitch,duration],i)=>this.note(pitch,duration,.19,type==='hurt'||type==='over'?'sawtooth':'sine'));
 }
 update(dt,chapter,playing){
  if(!playing||!this.enabled||!this.context||this.context.state!=='running')return;
  if(this.chapter!==chapter){this.chapter=chapter;this.step=0;this.timer=0}
  this.timer-=dt;
  if(this.timer>0)return;
  const beat=.22;this.timer+=beat;this.timer=Math.max(this.timer,.02);
  const tune=tunes[chapter%tunes.length],i=this.step++%tune.length;
  this.note(67+tune[i],beat*.83,.16,'triangle');
  if(i%4===0)this.note(43+[0,5,0,7][chapter],beat*2.7,.105,'sine');
  if(i%2===0)this.note(55+[0,2,3,5][chapter],.06,.045,'square');
 }
}
window.CAT_AUDIO=CatAudio;
})();
