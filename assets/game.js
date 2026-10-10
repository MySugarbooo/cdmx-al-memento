/* UMBRAL 9 • FPS jugable en navegador: combate, IA, misiones y guardado local */
(function(){
'use strict';
const $=id=>document.getElementById(id),clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const PI2=Math.PI*2;
const WORLD=window.UMBRAL_WORLD;
const SAVE_KEY='umbral9-progress-v1';
const WEAPON_DATA=[
 {id:'pistol',name:'P9 · Pulso',short:'P9',mag:18,rate:.25,damage:37,spread:.012,reload:1.15,range:18},
 {id:'rifle',name:'AR-6 · Carabina',short:'AR6',mag:32,rate:.105,damage:25,spread:.026,reload:1.7,range:20},
 {id:'shotgun',name:'TH-12 · Dispersor',short:'TH12',mag:8,rate:.79,damage:17,pellets:7,spread:.15,reload:1.95,range:11}
];
function newSave(){return {version:1,unlocked:1,lastStage:0,completed:Array(6).fill(false),bestKills:Array(6).fill(0),bestTime:Array(6).fill(null),logs:[],finished:false,music:true,volume:.42}};
function safeStorageRead(){try{const o=JSON.parse(localStorage.getItem(SAVE_KEY)||'null');if(!o||o.version!==1)return newSave();const def=newSave();
 def.unlocked=clamp(Math.floor(Number(o.unlocked)||1),1,6);def.lastStage=clamp(Math.floor(Number(o.lastStage)||0),0,def.unlocked-1);
 def.completed=Array.from({length:6},(_,i)=>o.completed?.[i]===true);
 def.bestKills=Array.from({length:6},(_,i)=>clamp(Math.floor(Number(o.bestKills?.[i])||0),0,1000));
 def.bestTime=Array.from({length:6},(_,i)=>Number.isFinite(o.bestTime?.[i])&&o.bestTime[i]>0?o.bestTime[i]:null);
 def.logs=Array.isArray(o.logs)?o.logs.filter(x=>typeof x==='string').slice(0,30):[];
 def.finished=o.finished===true;def.music=o.music!==false;def.volume=clamp(Number(o.volume)||.42,.02,1);return def;
 }catch(e){return newSave();}}
function formatTime(s){if(!Number.isFinite(s))return '--:--';return String(Math.floor(s/60)).padStart(2,'0')+':'+String(Math.floor(s%60)).padStart(2,'0')}
function normalize(v){return Math.atan2(Math.sin(v),Math.cos(v))}
function distance(a,b){return Math.hypot(a.x-b.x,a.y-b.y)}
function storageWrite(save){try{localStorage.setItem(SAVE_KEY,JSON.stringify(save));return true}catch(e){return false}}
class Game{
 constructor(){
  this.canvas=$('screen');this.ctx=this.canvas?.getContext('2d');if(!this.ctx)throw Error('El navegador no admite Canvas 2D');
  this.world=WORLD;this.renderer=new window.UMBRAL_RENDER(this.canvas);this.audio=new window.UMBRAL_AUDIO();
  this.save=safeStorageRead();this.audio.enabled=this.save.music;this.audio.volume=this.save.volume;
  this.stage=0;this.level=null;this.player=null;this.enemies=[];this.items=[];
  this.phase='menu';this.keys=new Set();this.pointerLocked=false;this.firing=false;
  this.pitch=0;this.stepBob=0;this.moving=false;this.aimOnEnemy=false;this.elapsed=0;this.kills=0;
  this.weapons=WEAPON_DATA;this.weaponIndex=0;this.ammo=[];this.projectiles=[];
  this.shotClock=0;this.reloadTime=0;this.dodgeClock=0;this.dodgePower=0;
  this.effects={recoil:0,muzzle:0,damage:0,pulse:0};this.eventTimer=0;this.lastFrame=0;this.timerHUD=0;
  this.savedMemories=new Set();this.touch={strafe:0,forward:0,lookId:null,lastX:0,lastY:0,moveId:null,originX:0,originY:0};
  this.bind();this.loadStage(0,false);this.refreshMenu();this.showHome();
  requestAnimationFrame(t=>this.loop(t));
 }
 loadStage(index,restore=false){
  this.stage=index;this.level=WORLD.buildLevel(index);this.renderer.load(this.level);this.pitch=0;
  const spawn=this.level.start;
  this.player={x:spawn.x,y:spawn.y,a:spawn.a,hp:100,shield:35,walk:0,alive:true,invuln:0};
  this.enemies=this.level.enemies.map(e=>({...e,maxHp:e.hp,alive:true,flash:0,alert:0,attack:Math.random()*1.4+.8,anim:0,bob:0,isBoss:e.kind==='matriarch'||e.kind==='herald',speed:e.kind==='brute'?.68:e.kind==='herald'?.56:e.kind==='matriarch'?.65:e.kind==='seer'?.66:1.05}));
  this.items=this.level.pickups.map(p=>({...p,taken:false}));
  this.weapons=WEAPON_DATA;this.weaponIndex=0;
  this.ammo=[{mag:18,reserve:148},{mag:32,reserve:196},{mag:8,reserve:44}];
  this.projectiles=[];this.elapsed=0;this.kills=0;this.shotClock=0;this.reloadTime=0;this.dodgeClock=0;this.dodgePower=0;
  this.savedMemories.clear();this.keys.clear();this.firing=false;this.pitch=0;this.stepBob=0;
  this.effects={recoil:0,muzzle:0,damage:0,pulse:0};this.moving=false;
  this.applyUI();
 }
 bind(){
  $('start-btn').addEventListener('click',()=>this.chooseMission(this.save.lastStage));
  $('hero-play').addEventListener('click',()=>this.chooseMission(this.save.lastStage));
  $('resume-btn').addEventListener('click',()=>this.resume());
  $('pause-btn').addEventListener('click',()=>this.togglePause());
  $('music-btn').addEventListener('click',()=>this.toggleSound());
  $('volume').value=String(this.save.volume*100);
  $('volume').addEventListener('input',e=>{this.save.volume=Number(e.target.value)/100;this.audio.setVolume(this.save.volume);storageWrite(this.save)});
  $('reset-progress').addEventListener('click',()=>{if(!window.confirm('¿Eliminar el progreso de UMBRAL 9 guardado en este navegador?'))return;this.save=newSave();storageWrite(this.save);this.audio.enabled=this.save.music;this.audio.setVolume(this.save.volume);this.loadStage(0);this.refreshMenu();this.showHome()});
  $('fullscreen-btn').addEventListener('click',()=>{const el=$('game-container');if(!document.fullscreenElement)el.requestFullscreen?.().catch(()=>{});else document.exitFullscreen?.().catch(()=>{})});
  $('screen').addEventListener('click',()=>{if(this.phase==='playing'&&!this.pointerLocked&&this.canvas.requestPointerLock){try{this.canvas.requestPointerLock()}catch(e){}}});
  document.addEventListener('pointerlockchange',()=>{this.pointerLocked=document.pointerLockElement===this.canvas;$('pointer-state').textContent=this.pointerLocked?'MOUSE ACTIVO · ESC PARA SOLTAR':'CLIC EN EL JUEGO PARA APUNTAR'});
  document.addEventListener('mousemove',e=>{if(this.phase==='playing'&&this.pointerLocked){this.player.a=normalize(this.player.a+e.movementX*.0024);this.pitch=clamp(this.pitch+e.movementY*.55,-110,120)}});
  this.canvas.addEventListener('mousedown',e=>{if(e.button===0&&this.phase==='playing'){this.audio.unlock();this.firing=true;if(this.pointerLocked)this.fire()}});
  document.addEventListener('mouseup',e=>{if(e.button===0)this.firing=false});
  this.canvas.addEventListener('contextmenu',e=>e.preventDefault());
  window.addEventListener('keydown',e=>{
   const tag=e.target?.tagName||'';if(['INPUT','TEXTAREA','SELECT'].includes(tag))return;
   const key=e.key.toLowerCase();
   if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright',' ','shift','r','1','2','3','e'].includes(key)&&this.phase==='playing')e.preventDefault();
   this.keys.add(key);
   if(this.phase==='playing'){
    if(key==='r'&&!e.repeat)this.reload();
    if(['1','2','3'].includes(key)&&!e.repeat)this.switchWeapon(Number(key)-1);
    if((key===' '||key==='control')&&!e.repeat)this.dodge();
    if(key==='e'&&!e.repeat)this.interact();
   }
   if((key==='p'||key==='escape')&&!e.repeat){if(this.phase==='playing')this.pause();else if(this.phase==='paused')this.resume();}
   if(key==='m'&&!e.repeat)this.toggleSound();
  });
  window.addEventListener('keyup',e=>this.keys.delete(e.key.toLowerCase()));
  window.addEventListener('blur',()=>{this.keys.clear();this.firing=false;if(this.phase==='playing')this.pause()});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&this.phase==='playing')this.pause()});
  for(const b of document.querySelectorAll('[data-action]')){
   const act=b.dataset.action;
   b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture?.(e.pointerId);this.audio.unlock();
    if(act==='shoot'){this.firing=true;this.fire()}
    if(act==='reload')this.reload();if(act==='dodge')this.dodge();if(act==='weapon')this.switchWeapon((this.weaponIndex+1)%Math.min(3,1+Math.floor(this.stage/2)));
    b.classList.add('pressed');
   });
   for(const name of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(name,()=>{if(act==='shoot')this.firing=false;b.classList.remove('pressed')});
  }
  const movement=$('touch-move');
  movement.addEventListener('pointerdown',e=>{e.preventDefault();movement.setPointerCapture?.(e.pointerId);this.touch.moveId=e.pointerId;const rect=movement.getBoundingClientRect();this.touch.originX=rect.left+rect.width/2;this.touch.originY=rect.top+rect.height/2;this.updateStick(e)});
  movement.addEventListener('pointermove',e=>{if(this.touch.moveId===e.pointerId)this.updateStick(e)});
  for(const type of ['pointerup','pointercancel','lostpointercapture'])movement.addEventListener(type,()=>{this.touch.moveId=null;this.touch.forward=0;this.touch.strafe=0;$('stick-knob').style.transform='translate(-50%,-50%)'});
  this.canvas.addEventListener('pointerdown',e=>{if(e.pointerType==='touch'&&this.phase==='playing'){this.touch.lookId=e.pointerId;this.touch.lastX=e.clientX;this.touch.lastY=e.clientY;this.canvas.setPointerCapture?.(e.pointerId)}});
  this.canvas.addEventListener('pointermove',e=>{if(e.pointerType==='touch'&&this.touch.lookId===e.pointerId&&this.phase==='playing'){
   this.player.a=normalize(this.player.a+(e.clientX-this.touch.lastX)*.007);this.pitch=clamp(this.pitch+(e.clientY-this.touch.lastY)*1.5,-110,120);
   this.touch.lastX=e.clientX;this.touch.lastY=e.clientY;
  }});
  for(const type of ['pointerup','pointercancel','lostpointercapture'])this.canvas.addEventListener(type,e=>{if(e.pointerId===this.touch.lookId)this.touch.lookId=null});
 }
 updateStick(event){const dx=clamp((event.clientX-this.touch.originX)/43,-1,1),dy=clamp((event.clientY-this.touch.originY)/43,-1,1);this.touch.strafe=dx;this.touch.forward=-dy;$('stick-knob').style.transform=`translate(calc(-50% + ${dx*35}px),calc(-50% + ${dy*35}px))`}
 showOverlay({tag,title,body,buttons,dialogue,story}){
  $('stage-overlay').hidden=false;
  $('overlay-tag').textContent=tag||'UMBRAL 9';$('overlay-title').textContent=title||'';$('overlay-body').textContent=body||'';
  $('overlay-buttons').replaceChildren();
  const chat=$('overlay-transcript');chat.replaceChildren();chat.hidden=!dialogue?.length;
  if(dialogue){for(const [name,line] of dialogue){const div=document.createElement('div');div.className='dialogue-line';const label=document.createElement('strong');label.textContent=name;const p=document.createElement('p');p.textContent=line;div.append(label,p);chat.append(div)}}
  for(const option of buttons){const button=document.createElement('button');button.type='button';button.className=option.primary?'button button-primary':'button button-outline';button.textContent=option.label;button.addEventListener('click',()=>{this.audio.unlock();this.audio.effect('click');option.fn()});$('overlay-buttons').append(button)}
 }
 hideOverlay(){$('stage-overlay').hidden=true}
 showHome(){this.phase='menu';this.firing=false;this.releasePointer();$('pause-btn').disabled=true;
  this.showOverlay({tag:'INCIDENTE ÍCARO-9 · AÑO 2189',title:'LA SEÑAL VIENE DE MAÑANA',
   body:'Una estación ha dejado de responder. Las criaturas que viven dentro imitan recuerdos humanos. Eres Darío Vega, rescatista orbital. Alguien envió un mensaje de auxilio con tu propia voz, pero fue grabado en el futuro. Descubre qué ocurrió antes de que el Umbral alcance la Tierra.',
   buttons:[{label:this.save.unlocked>1?'▶ CONTINUAR HISTORIA':'▶ INICIAR OPERACIÓN',primary:true,fn:()=>this.chooseMission(this.save.lastStage)},
    {label:'VER MISIONES',fn:()=>$('missions').scrollIntoView({behavior:'smooth'})}]});
  this.updateMenu();
 }
 chooseMission(i){if(i>=this.save.unlocked)return;this.audio.unlock();this.loadStage(i);this.phase='briefing';
  const cfg=this.level;
  this.showOverlay({tag:`MISIÓN ${cfg.id} / 06 · ${WORLD.acts[cfg.act].name}`,title:cfg.name.toUpperCase(),body:cfg.intro,
   dialogue:cfg.dialogue,buttons:[{label:'ENTRAR A LA ESTACIÓN',primary:true,fn:()=>this.start()}, {label:'VOLVER AL MENÚ',fn:()=>this.showHome()}]});
  $('game-section').scrollIntoView({behavior:'smooth',block:'start'});
 }
 start(){this.phase='playing';this.hideOverlay();$('pause-btn').disabled=false;this.keys.clear();this.audio.resume();this.audio.effect('alarm');this.message(this.level.hint,7);this.applyUI()}
 pause(){if(this.phase!=='playing')return;this.phase='paused';this.firing=false;this.keys.clear();this.releasePointer();
  this.showOverlay({tag:'OPERACIÓN EN PAUSA',title:'RESPIRA. LA BRECHA ESPERA.',body:'Puedes volver cuando quieras. La historia se guarda al completar misiones; los registros recuperados también se conservan.',buttons:[{label:'▶ SEGUIR JUGANDO',primary:true,fn:()=>this.resume()},{label:'REINICIAR MISIÓN',fn:()=>this.chooseMission(this.stage)},{label:'MENÚ PRINCIPAL',fn:()=>this.showHome()}]});
 }
 togglePause(){if(this.phase==='playing')this.pause();else if(this.phase==='paused')this.resume()}
 resume(){if(this.phase!=='paused')return;this.phase='playing';this.hideOverlay();this.keys.clear();this.audio.resume();}
 releasePointer(){if(document.pointerLockElement===this.canvas)document.exitPointerLock?.()}
 toggleSound(){this.audio.setEnabled(!this.audio.enabled);this.save.music=this.audio.enabled;storageWrite(this.save);this.applyUI()}
 switchWeapon(index){
  if(this.phase!=='playing'||this.reloadTime>0||index<0||index>=WEAPON_DATA.length)return;
  if(index===1&&this.stage<1||index===2&&this.stage<3){this.message('Esta arma se desbloquea en otra misión.',3);return;}
  this.weaponIndex=index;this.shotClock=.13;this.audio.effect('click');this.applyUI();
 }
 reload(){if(this.phase!=='playing'||this.reloadTime>0)return;const w=this.weapons[this.weaponIndex],ammo=this.ammo[this.weaponIndex];if(ammo.mag>=w.mag||ammo.reserve<=0)return;
  this.reloadTime=w.reload;this.firing=false;this.audio.effect('reload');this.message('RECARGANDO · '+w.name,1.5);
 }
 finishReload(){const w=this.weapons[this.weaponIndex],a=this.ammo[this.weaponIndex],needed=w.mag-a.mag,got=Math.min(needed,a.reserve);a.mag+=got;a.reserve-=got;this.audio.effect('reload');this.applyUI()}
 dodge(){if(this.phase!=='playing'||this.dodgeClock>0)return;this.dodgePower=.18;this.dodgeClock=2.8;this.player.invuln=.22;this.effects.pulse=.5;}
 canWalk(x,y,r=.22){const map=this.level.map;for(const sx of [-r,r])for(const sy of [-r,r]){
  const gx=Math.floor(x+sx),gy=Math.floor(y+sy);if(gy<0||gx<0||gy>=this.level.height||gx>=this.level.width||map[gy][gx])return false;
 }return true;}
 moveEntity(object,dx,dy,r=.23){if(this.canWalk(object.x+dx,object.y,r))object.x+=dx;if(this.canWalk(object.x,object.y+dy,r))object.y+=dy}
 sight(x1,y1,x2,y2){const dx=x2-x1,dy=y2-y1,len=Math.hypot(dx,dy);if(!len)return true;const hit=this.renderer.cast(x1,y1,dx/len,dy/len,len);return hit.dist>=len-.16;}
 fire(){
  if(this.phase!=='playing'||this.reloadTime>0||this.shotClock>0)return false;
  const w=this.weapons[this.weaponIndex],a=this.ammo[this.weaponIndex];
  if(a.mag<=0){this.audio.effect('click');this.shotClock=.24;if(a.reserve>0)this.reload();else this.message('SIN MUNICIÓN · Busca cajas doradas.',2.5);return false}
  a.mag--;this.shotClock=w.rate;this.effects.muzzle=.75;this.effects.recoil=.95;this.audio.effect('shoot');
  // Golpe instantáneo, con penetración de profundidad y un ángulo proporcional al tamaño.
  const count=w.pellets||1,base=this.player.a;
  for(let pellet=0;pellet<count;pellet++){
   const jitter=(Math.random()-.5)*2*w.spread,angle=base+jitter;
   const direction={x:Math.cos(angle),y:Math.sin(angle)};
   const wall=this.renderer.cast(this.player.x,this.player.y,direction.x,direction.y,w.range).dist;
   let chosen=null,hitDist=Infinity;
   for(const enemy of this.enemies){
    if(!enemy.alive)continue;
    const dx=enemy.x-this.player.x,dy=enemy.y-this.player.y,proj=dx*direction.x+dy*direction.y;
    if(proj<=0||proj>=Math.min(w.range,wall+.05)||proj>=hitDist)continue;
    const off=Math.abs(-dx*direction.y+dy*direction.x);
    const radius=enemy.isBoss?.54:enemy.kind==='brute'?.42:.31;
    if(off<radius){chosen=enemy;hitDist=proj}
   }
   if(chosen){
    const dist=Math.hypot(chosen.x-this.player.x,chosen.y-this.player.y);
    let damage=w.damage*(w.id==='shotgun'?clamp(1-dist/14,.28,1):1);
    // Golpes en el borde de la silueta generan menor daño.
    chosen.hp-=damage;chosen.flash=.15;chosen.alert=4;
    if(chosen.hp<=0)this.enemyDown(chosen);
   }
  }
  if(a.mag===0&&a.reserve>0)this.message('CARGADOR VACÍO · Pulsa R para recargar.',2);
  this.applyUI();return true;
 }
 enemyDown(enemy){if(!enemy.alive)return;enemy.alive=false;enemy.hp=0;enemy.flash=.45;this.kills++;
  this.audio.effect(enemy.isBoss?'boss':'enemy');this.effects.pulse=enemy.isBoss?1.4:.35;
  if(enemy.isBoss){this.message('OBJETIVO NEUTRALIZADO · Puerta de salida disponible.',5);this.audio.effect('unlock');}
  else if(this.kills%4===0)this.message('AMENAZAS NEUTRALIZADAS · '+this.kills,2);
 }
 get remaining(){return this.items.filter(x=>x.type==='memory'&&!x.taken).length}
 get bossAlive(){return this.enemies.some(e=>e.isBoss&&e.alive)}
 get exitOpen(){return this.remaining===0&&!this.bossAlive}
 interact(){
  if(this.phase!=='playing')return;
  const p=this.player,mem=this.items.find(x=>x.type==='memory'&&!x.taken&&distance(p,x)<1.4);
  if(mem){this.collect(mem);return}
  if(distance(p,this.level.exit)<1.5)this.tryExit();
  else this.message('Acércate a una memoria azul o a la puerta de salida.',2.5);
 }
 collect(item){if(item.taken)return;
  item.taken=true;
  if(item.type==='memory'){
   const log=this.level.logs[item.id];const key=this.stage+':'+item.id;
   if(log&&!this.save.logs.includes(key))this.save.logs.push(key);
   storageWrite(this.save);this.audio.effect('pickup');this.effects.pulse=.65;
   if(log){$('log-title').textContent=log[0];$('log-text').textContent=log[1];$('log-card').hidden=false;setTimeout(()=>{$('log-card').hidden=true},6500)}
   this.message('MEMORIA RECUPERADA · '+(this.level.cores-this.remaining)+'/'+this.level.cores,3.8);
   if(this.remaining===0){this.audio.effect('unlock');this.message(this.bossAlive?'TODAS LAS MEMORIAS · Derrota al guardián.':'TODAS LAS MEMORIAS · Ve a la puerta del sector.',5)}
  }else if(item.type==='medkit'){
   this.player.hp=clamp(this.player.hp+38,0,100);this.player.shield=clamp(this.player.shield+15,0,65);
   this.audio.effect('med');this.message('KIT MÉDICO · SALUD RESTABLECIDA',2.5);
  }else if(item.type==='ammo'){
   this.ammo[0].reserve=Math.min(220,this.ammo[0].reserve+36);
   this.ammo[1].reserve=Math.min(310,this.ammo[1].reserve+45);
   this.ammo[2].reserve=Math.min(80,this.ammo[2].reserve+12);
   this.audio.effect('pickup');this.message('SUMINISTROS · MUNICIÓN RECUPERADA',2.5);
  }
  this.applyUI();
 }
 tryExit(){
  if(!this.exitOpen){this.message(this.bossAlive?'PUERTA BLOQUEADA · Neutraliza al guardián.':'PUERTA BLOQUEADA · Recupera las memorias que faltan.',2.6);this.audio.effect('click');return}
  this.completeStage();
 }
 completeStage(){if(this.phase!=='playing')return;
  this.phase='complete';this.firing=false;this.keys.clear();this.releasePointer();
  this.save.completed[this.stage]=true;this.save.unlocked=Math.max(this.save.unlocked,Math.min(6,this.stage+2));
  this.save.lastStage=Math.min(5,this.stage+1);this.save.bestKills[this.stage]=Math.max(this.save.bestKills[this.stage],this.kills);
  if(this.save.bestTime[this.stage]===null||this.elapsed<this.save.bestTime[this.stage])this.save.bestTime[this.stage]=this.elapsed;
  if(this.stage===5)this.save.finished=true;
  const stored=storageWrite(this.save);this.audio.effect('unlock');this.refreshMenu();
  const ending=this.stage===5;
  this.showOverlay({tag:ending?'FIN DEL EPISODIO I':'MISIÓN '+this.level.id+' COMPLETADA',title:ending?'LA PUERTA NO ESTÁ CERRADA': 'TRANSMISIÓN RECUPERADA',
   body:this.level.end+' · '+this.kills+' criaturas neutralizadas · '+formatTime(this.elapsed)+(stored?' · Progreso guardado':' · Aviso: el navegador bloqueó el guardado'),
   buttons:ending?[{label:'VER EPÍLOGO',primary:true,fn:()=>this.showEpilogue()},{label:'VOLVER AL MENÚ',fn:()=>this.showHome()}]:[
    {label:'▶ SIGUIENTE MISIÓN',primary:true,fn:()=>this.chooseMission(this.stage+1)},{label:'REPETIR MISIÓN',fn:()=>this.chooseMission(this.stage)},{label:'MENÚ',fn:()=>this.showHome()}]});
 }
 showEpilogue(){this.phase='epilogue';this.showOverlay({tag:'FIN DEL EPISODIO I · CONTINUARÁ',title:'¿QUÉ QUEDA DEL OTRO LADO?',body:'LUMA recibe una última transmisión. No procede de ÍCARO-9: llega desde la Tierra, fechada doce años después. La voz de Darío susurra: «Si me recuerdas, todavía tenemos tiempo». La pantalla se oscurece. ¿Se cerró realmente el Umbral?',
 buttons:[{label:'VOLVER AL MAPA DE MISIONES',primary:true,fn:()=>this.showHome()},{label:'REPETIR EL ÚLTIMO SECTOR',fn:()=>this.chooseMission(5)}]});}
 damage(amount){if(this.phase!=='playing'||this.player.invuln>0)return;
  this.player.invuln=.35;
  const absorbed=Math.min(this.player.shield,amount*.65);this.player.shield=Math.max(0,this.player.shield-absorbed);
  this.player.hp=Math.max(0,this.player.hp-(amount-absorbed));
  this.effects.damage=1.7;this.audio.effect('hurt');this.applyUI();
  if(this.player.hp<=0)this.die();
 }
 die(){this.phase='dead';this.firing=false;this.keys.clear();this.releasePointer();this.audio.effect('fail');
  this.showOverlay({tag:'SIGNOS VITALES PERDIDOS',title:'NO ERES LO QUE TE PERSIGUE',body:'Las criaturas han detenido a Darío, pero el expediente de la misión permanece intacto. Puedes intentarlo de nuevo. Tus misiones completadas siguen guardadas.',
  buttons:[{label:'↻ REINTENTAR MISIÓN',primary:true,fn:()=>this.chooseMission(this.stage)},{label:'VOLVER AL MENÚ',fn:()=>this.showHome()}]});
 }
 message(text,seconds=3){$('toast').textContent=text;$('toast').classList.add('active');this.eventTimer=seconds;}
 applyUI(){
  $('hud-health').textContent=String(Math.round(this.player?.hp??100));
  $('hud-shield').textContent=String(Math.round(this.player?.shield??35));
  $('health-fill').style.width=(this.player?.hp??100)+'%';$('shield-fill').style.width=((this.player?.shield??35)/65*100)+'%';
  const weapon=this.weapons[this.weaponIndex],ammo=this.ammo[this.weaponIndex]||{mag:18,reserve:148};
  $('hud-weapon').textContent=weapon.name;
  $('hud-ammo').textContent=String(ammo.mag).padStart(2,'0');$('hud-reserve').textContent='/ '+String(ammo.reserve);
  $('hud-memories').textContent=(this.level?.cores-this.remaining||0)+' / '+(this.level?.cores||2);
  $('hud-sector').textContent=this.level?.sector.toUpperCase()||'ÍCARO-9';
  $('hud-time').textContent=formatTime(this.elapsed);
  $('hud-kills').textContent=String(this.kills);
  $('hud-exit').textContent=this.exitOpen?'SALIDA DISPONIBLE':'SALIDA BLOQUEADA';
  $('hud-exit').classList.toggle('ready',this.exitOpen);
  $('music-btn').textContent=this.audio.enabled?'♫ MÚSICA ON':'♫ MÚSICA OFF';
  $('music-btn').setAttribute('aria-pressed',String(this.audio.enabled));
  $('weapon-rifle').querySelector('strong').textContent=this.stage>=1?'2 · AR-6 CARABINA':'2 · BLOQUEADA';
  $('weapon-shotgun').querySelector('strong').textContent=this.stage>=3?'3 · TH-12 DISPERSOR':'3 · BLOQUEADA';
  $('weapon-pistol').classList.toggle('selected',this.weaponIndex===0);
  $('weapon-rifle').classList.toggle('selected',this.weaponIndex===1);
  $('weapon-shotgun').classList.toggle('selected',this.weaponIndex===2);
 }
 refreshMenu(){
  $('save-level').textContent=this.save.unlocked+'/6';
  $('save-records').textContent=this.save.logs.length+'/13';
  $('save-operations').textContent=this.save.completed.filter(Boolean).length+'/6';
  $('continue-label').textContent=this.save.unlocked>1?'CONTINUAR · MISIÓN '+String(this.save.lastStage+1).padStart(2,'0'):'EMPEZAR MISIÓN 01';
  const missions=$('mission-list');missions.replaceChildren();
  WORLD.missions.forEach((mission,i)=>{
   const locked=i>=this.save.unlocked;
   const button=document.createElement('button');button.type='button';button.disabled=locked;
   button.className='mission-tile'+(locked?' locked':'')+(this.save.completed[i]?' done':'');
   const no=document.createElement('span');no.className='mission-index';no.textContent=locked?'▣':'0'+(i+1);
   const info=document.createElement('div');info.className='mission-info';const nm=document.createElement('strong');nm.textContent=mission.name;const caption=document.createElement('small');caption.textContent=mission.sector;info.append(nm,caption);
   const tag=document.createElement('span');tag.className='mission-tag';tag.textContent=locked?'BLOQUEADA':this.save.completed[i]?'COMPLETADA':'DISPONIBLE';
   button.append(no,info,tag);button.addEventListener('click',()=>{if(!locked)this.chooseMission(i)});missions.append(button);
  });
 }
 updateMenu(){this.refreshMenu()}
 update(dt){
  if(this.phase!=='playing')return;
  this.elapsed+=dt;this.eventTimer=Math.max(0,this.eventTimer-dt);
  if(this.eventTimer===0)$('toast').classList.remove('active');
  for(const key of Object.keys(this.effects))this.effects[key]=Math.max(0,this.effects[key]-dt*(key==='damage'?1.8:key==='muzzle'?5:key==='recoil'?5:1.8));
  this.shotClock=Math.max(0,this.shotClock-dt);this.dodgeClock=Math.max(0,this.dodgeClock-dt);
  if(this.reloadTime>0){this.reloadTime-=dt;if(this.reloadTime<=0){this.reloadTime=0;this.finishReload()}}
  const p=this.player;
  p.invuln=Math.max(0,p.invuln-dt);
  let forward=(this.keys.has('w')||this.keys.has('arrowup')?1:0)-(this.keys.has('s')||this.keys.has('arrowdown')?1:0)+this.touch.forward;
  let sideways=(this.keys.has('d')?1:0)-(this.keys.has('a')?1:0)+this.touch.strafe;
  if(!this.pointerLocked){if(this.keys.has('arrowleft'))p.a=normalize(p.a-dt*1.9);if(this.keys.has('arrowright'))p.a=normalize(p.a+dt*1.9)}
  const len=Math.hypot(forward,sideways);if(len>1){forward/=len;sideways/=len}
  const speed=this.dodgePower>0?9.5:(this.keys.has('shift')?4.5:3.15);
  if(this.dodgePower>0){forward=1;sideways=0;this.dodgePower=Math.max(0,this.dodgePower-dt)}
  const angle=p.a;
  const dx=(Math.cos(angle)*forward-Math.sin(angle)*sideways)*speed*dt;
  const dy=(Math.sin(angle)*forward+Math.cos(angle)*sideways)*speed*dt;
  this.moveEntity(p,dx,dy,.24);
  this.moving=Math.abs(dx)+Math.abs(dy)>.0005;
  if(this.moving){p.walk+=dt*(speed>4?12:8);this.stepBob=Math.sin(p.walk)*Math.min(6,speed*1.1)}else this.stepBob*=Math.max(0,1-dt*8);
  if(this.firing&&this.shotClock<=0)this.fire();
  // Recoger objetos automáticamente; el contacto con la salida intenta completar misión.
  for(const item of this.items){if(item.taken)continue;if(distance(p,item)<.72)this.collect(item)}
  if(distance(p,this.level.exit)<.68)this.tryExit();
  const enemyCount=this.enemies.filter(e=>e.alive&&distance(e,p)<7).length;
  this.audio.update(dt,this.level.ambient,clamp(enemyCount/4,0,1));
  for(const enemy of this.enemies){
   if(!enemy.alive)continue;
   enemy.flash=Math.max(0,enemy.flash-dt);enemy.anim+=dt*2.5;enemy.bob=Math.sin(enemy.anim*2)*.02;
   const dist=distance(enemy,p);if(dist>14)continue;
   const los=this.sight(enemy.x,enemy.y,p.x,p.y);
   if(los)enemy.alert=3.3;else enemy.alert=Math.max(0,enemy.alert-dt);
   enemy.attack-=dt;
   if(enemy.alert>0&&dist>(enemy.isBoss?2.5:enemy.kind==='seer'?3.2:1.25)){
    const a=Math.atan2(p.y-enemy.y,p.x-enemy.x),speedEnemy=enemy.speed*(enemy.isBoss?1:.92);
    this.moveEntity(enemy,Math.cos(a)*speedEnemy*dt,Math.sin(a)*speedEnemy*dt,enemy.isBoss?.49:.23);
   }
   if(dist<1.28&&enemy.attack<=0){this.damage(enemy.isBoss?28:enemy.kind==='brute'?22:14);enemy.attack=enemy.isBoss?.9:1.1;}
   else if(los&&dist<(enemy.kind==='seer'?9:enemy.isBoss?10:5.2)&&enemy.attack<=0&&((enemy.isBoss)||(enemy.kind==='seer'))){
    const angle=Math.atan2(p.y-enemy.y,p.x-enemy.x),speedShot=enemy.isBoss?4.3:3.15;
    this.projectiles.push({x:enemy.x,y:enemy.y,dx:Math.cos(angle)*speedShot,dy:Math.sin(angle)*speedShot,life:2.5,damage:enemy.isBoss?22:12,kind:enemy.kind});
    if(enemy.isBoss){for(const add of [-.2,.2])this.projectiles.push({x:enemy.x,y:enemy.y,dx:Math.cos(angle+add)*speedShot,dy:Math.sin(angle+add)*speedShot,life:2.5,damage:17,kind:enemy.kind})}
    enemy.attack=enemy.isBoss?1.45:2.1;
   }
  }
  for(const bolt of this.projectiles){
   bolt.life-=dt;
   if(bolt.life<=0)continue;
   const tx=bolt.x+bolt.dx*dt,ty=bolt.y+bolt.dy*dt;
   if(!this.canWalk(tx,ty,.09)){bolt.life=0;continue}
   bolt.x=tx;bolt.y=ty;if(Math.hypot(bolt.x-p.x,bolt.y-p.y)<.36){this.damage(bolt.damage);bolt.life=0}
  }
  this.projectiles=this.projectiles.filter(b=>b.life>0);
  // Retroalimentación de mira (la criatura está visible en la línea central).
  this.aimOnEnemy=this.enemies.some(e=>{
    if(!e.alive)return false;const dx=e.x-p.x,dy=e.y-p.y,z=Math.hypot(dx,dy);if(z>14)return false;
    const delta=normalize(Math.atan2(dy,dx)-p.a);return Math.abs(delta)<.25/z&&this.sight(p.x,p.y,e.x,e.y);
  });
  this.timerHUD+=dt;
  if(this.timerHUD>.14){this.timerHUD=0;this.applyUI();}
  this.drawMiniMap();
 }
 drawMiniMap(){
  const c=$('minimap'),ctx=c.getContext('2d');if(!ctx)return;
  const w=c.width,h=c.height,step=6,view=11,px=this.player.x,py=this.player.y;
  ctx.clearRect(0,0,w,h);ctx.fillStyle='#051721';ctx.fillRect(0,0,w,h);
  const sx=(w-1)/view,sy=(h-1)/view;
  for(let iy=-5;iy<=5;iy++)for(let ix=-5;ix<=5;ix++){
   const mx=Math.floor(px)+ix,my=Math.floor(py)+iy;
   if(mx<0||my<0||mx>=this.level.width||my>=this.level.height)continue;
   ctx.fillStyle=this.level.map[my][mx]?'#466273':'#102430';
   ctx.fillRect((ix+5)*sx,(iy+5)*sy,sx-1,sy-1);
  }
  for(const item of this.items){if(item.taken)continue;const dx=item.x-Math.floor(px)+5,dy=item.y-Math.floor(py)+5;if(dx<0||dx>11||dy<0||dy>11)continue;
   ctx.fillStyle=item.type==='memory'?'#a8fff6':item.type==='medkit'?'#91ffbd':'#ffe1a9';ctx.fillRect(dx*sx-2,dy*sy-2,4,4);
  }
  for(const e of this.enemies){if(!e.alive)continue;const dx=e.x-Math.floor(px)+5,dy=e.y-Math.floor(py)+5;if(dx<0||dx>11||dy<0||dy>11)continue;
   ctx.fillStyle=e.isBoss?'#ffa2c7':'#ff789b';ctx.beginPath();ctx.arc(dx*sx,dy*sy,e.isBoss?4:2,0,PI2);ctx.fill();
  }
  const ex=this.level.exit.x-Math.floor(px)+5,ey=this.level.exit.y-Math.floor(py)+5;
  if(ex>=0&&ex<=11&&ey>=0&&ey<=11){ctx.strokeStyle=this.exitOpen?'#8ef9d4':'#dc8fa2';ctx.lineWidth=2;ctx.strokeRect(ex*sx-4,ey*sy-4,8,8)}
  const centerX=(px-Math.floor(px)+5)*sx,centerY=(py-Math.floor(py)+5)*sy;
  ctx.fillStyle='#fff6d1';ctx.beginPath();ctx.arc(centerX,centerY,4,0,PI2);ctx.fill();
  ctx.strokeStyle='#fff6d1';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(centerX,centerY);ctx.lineTo(centerX+Math.cos(this.player.a)*15,centerY+Math.sin(this.player.a)*15);ctx.stroke();
 }
 loop(t){
  const dt=this.lastFrame?Math.min(.04,(t-this.lastFrame)/1000):.016;this.lastFrame=t;
  try{this.update(dt);this.renderer.draw(this,t/1000)}catch(err){if(!this.reported){this.reported=true;console.error('UMBRAL 9:',err);$('runtime-error').textContent='Se produjo un error. Intenta recargar la página.';$('runtime-error').hidden=false;}}
  requestAnimationFrame(time=>this.loop(time));
 }
}
window.addEventListener('DOMContentLoaded',()=>{try{window.umbral=new Game()}catch(e){console.error(e);const t=$('runtime-error');if(t){t.textContent='No fue posible iniciar UMBRAL 9. Usa un navegador moderno y vuelve a cargar la página.';t.hidden=false}}});
})();
