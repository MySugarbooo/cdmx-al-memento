/* UMBRAL 9 • composición ambiental sintetizada original mediante Web Audio */
(function(){
'use strict';
const scales=[
 [[43,50,55,58],[39,46,51,55],[41,48,53,57],[38,45,50,55]],
 [[45,52,57,60],[43,50,55,59],[41,48,53,57],[38,45,50,55]],
 [[40,47,52,55],[36,43,48,52],[38,45,50,53],[35,42,47,50]],
 [[43,49,53,58],[39,46,51,55],[36,43,48,53],[41,48,53,56]],
 [[41,48,53,57],[38,45,50,53],[36,43,48,52],[40,47,52,55]],
 [[38,45,50,53],[35,42,47,52],[41,48,53,57],[43,50,55,59]]
];
const clamp=(a,b,c)=>Math.max(b,Math.min(c,a));
class AudioEngine{
 constructor(){this.ctx=null;this.master=null;this.enabled=true;this.volume=.42;this.clock=0;this.step=0;this.scene=-1;this.currentIntensity=0;this.lowpass=null;this.echo=null;this.feedback=null;this.compressor=null;}
 unlock(){
  if(this.ctx){if(this.ctx.state==='suspended')this.ctx.resume().catch(()=>{});return}
  const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;
  try{
   this.ctx=new AC();const c=this.ctx;
   this.master=c.createGain();this.master.gain.value=this.enabled?this.volume*.25:0;
   this.lowpass=c.createBiquadFilter();this.lowpass.type='lowpass';this.lowpass.frequency.value=2050;
   this.echo=c.createDelay(1.5);this.echo.delayTime.value=.36;
   this.feedback=c.createGain();this.feedback.gain.value=.19;
   this.compressor=c.createDynamicsCompressor();this.compressor.threshold.value=-22;this.compressor.ratio.value=3;
   this.lowpass.connect(this.master);this.lowpass.connect(this.echo);this.echo.connect(this.feedback);this.feedback.connect(this.echo);this.echo.connect(this.master);
   this.master.connect(this.compressor);this.compressor.connect(c.destination);
   c.resume().catch(()=>{});
  }catch(e){this.enabled=false}
 }
 setEnabled(on){this.enabled=!!on;this.unlock();this.updateVolume();}
 setVolume(v){this.volume=clamp(Number(v)||0,0,1);this.updateVolume();}
 updateVolume(){if(this.ctx&&this.master)this.master.gain.setTargetAtTime(this.enabled?this.volume*.25:0,this.ctx.currentTime,.05)}
 tone(midi,seconds,peak=.13,wave='sine',attack=.04,delay=0,filter=false){
  if(!this.ctx||!this.enabled||this.ctx.state!=='running')return;
  const c=this.ctx,now=c.currentTime+delay,osc=c.createOscillator(),gain=c.createGain();
  osc.type=wave;osc.frequency.value=440*Math.pow(2,(midi-69)/12);
  gain.gain.setValueAtTime(.0001,now);gain.gain.exponentialRampToValueAtTime(Math.max(.0002,peak),now+attack);
  gain.gain.exponentialRampToValueAtTime(.0001,now+seconds);
  osc.connect(gain);gain.connect(filter?this.lowpass:this.master);
  osc.start(now);osc.stop(now+seconds+.05);
 }
 noise(duration=.2,peak=.12,lowpassFreq=1800){
  if(!this.ctx||!this.enabled||this.ctx.state!=='running')return;
  const c=this.ctx,n=Math.floor(c.sampleRate*duration),buffer=c.createBuffer(1,n,c.sampleRate),samples=buffer.getChannelData(0);
  for(let i=0;i<n;i++)samples[i]=(Math.random()*2-1)*Math.pow(1-i/n,1.4);
  const src=c.createBufferSource(),f=c.createBiquadFilter(),v=c.createGain();src.buffer=buffer;
  f.type='lowpass';f.frequency.value=lowpassFreq;
  v.gain.setValueAtTime(Math.max(.0001,peak),c.currentTime);v.gain.exponentialRampToValueAtTime(.0001,c.currentTime+duration);
  src.connect(f);f.connect(v);v.connect(this.master);src.start();src.stop(c.currentTime+duration+.01);
 }
 effect(type){
  if(!this.enabled)return;this.unlock();
  switch(type){
   case 'shoot':this.tone(77,.10,.12,'sawtooth',.008);this.tone(65,.15,.08,'triangle',.008,.035);break;
   case 'reload':this.tone(44,.065,.07,'square',.006);this.tone(51,.085,.06,'square',.006,.12);break;
   case 'hurt':this.noise(.19,.20,530);this.tone(42,.29,.13,'sawtooth');break;
   case 'enemy':this.tone(37,.21,.11,'triangle');break;
   case 'boss':this.noise(.28,.23,700);this.tone(32,.33,.16,'sawtooth');break;
   case 'pickup':this.tone(81,.13,.11,'sine');this.tone(88,.22,.13,'sine',.02,.09);break;
   case 'med':this.tone(72,.15,.1,'sine');this.tone(76,.18,.11,'sine',.02,.13);this.tone(79,.28,.12,'sine',.02,.25);break;
   case 'unlock':this.tone(64,.25,.12,'sine');this.tone(69,.28,.12,'sine',.02,.12);this.tone(76,.38,.14,'sine',.02,.24);break;
   case 'fail':this.tone(50,.3,.1,'triangle');this.tone(43,.35,.13,'triangle',.03,.25);break;
   case 'step':this.noise(.042,.013,350);break;
   case 'click':this.tone(69,.08,.055,'sine');break;
   case 'alarm':this.tone(61,.32,.08,'triangle');this.tone(54,.26,.08,'triangle',.02,.16);break;
  }
 }
 update(dt,scene,intensity=0){
  if(!this.ctx||!this.enabled||this.ctx.state!=='running')return;
  if(scene!==this.scene){this.scene=scene;this.clock=0;this.step=0;}
  this.currentIntensity+=(intensity-this.currentIntensity)*Math.min(1,dt*1.2);
  this.lowpass.frequency.setTargetAtTime(1250+this.currentIntensity*1100,this.ctx.currentTime,.3);
  this.clock-=dt;if(this.clock>0)return;
  const beat=.54;this.clock=Math.max(.04,this.clock+beat);
  const progression=scales[scene%6],beatIndex=this.step++,chord=progression[Math.floor(beatIndex/8)%4];
  if(beatIndex%8===0){
   for(let i=0;i<4;i++)this.tone(chord[i],3.8,.032,'sine',.5,i*.12,true);
   this.tone(chord[0]-12,3.3,.04,'triangle',.7,0,true);
  }
  const melodyIndex=[0,2,3,1,2,3,1,0][beatIndex%8];
  if(beatIndex%2===0)this.tone(chord[melodyIndex]+12,beat*1.55,.058,'sine',.08,0,true);
  else if(beatIndex%4===3)this.tone(chord[1]+7,beat*.95,.026,'triangle',.06,0,true);
  if(intensity>.5&&beatIndex%2===0)this.tone(chord[0]+12,beat*.42,.034,'triangle',.012);
 }
 suspend(){if(this.ctx&&this.ctx.state==='running')this.ctx.suspend().catch(()=>{})}
 resume(){if(this.enabled)this.unlock()}
}
window.UMBRAL_AUDIO=AudioEngine;
})();
