/* Cat y las Estrellas Perdidas · motor original de plataformas, sin dependencias */
(() => {
"use strict";
const DATA=window.CAT_DATA;
if(!DATA)return;
const {levels,chapters,WIDTH:W,HEIGHT:H,GROUND}=DATA;
const $=id=>document.getElementById(id);
const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
const overlap=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
const number=(value,def=0)=>Number.isFinite(value)?value:def;
const SAVE_KEY='cat-lunaria-save-v1';
const imageFriendly=n=>String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g,',');
const starsFor=save=>(save.stars||[]).filter(Boolean).length;
function loadSave(){
 const initial={version:1,unlocked:1,lastLevel:0,bestCoins:Array(16).fill(0),stars:Array(16).fill(false),checkpoint:null,music:true,finished:false};
 try{
  const loaded=JSON.parse(localStorage.getItem(SAVE_KEY)||'null');
  if(!loaded||loaded.version!==1)return initial;
  initial.unlocked=clamp(Math.floor(number(loaded.unlocked,1)),1,16);
  initial.lastLevel=clamp(Math.floor(number(loaded.lastLevel)),0,initial.unlocked-1);
  initial.bestCoins=Array.from({length:16},(_,i)=>clamp(Math.floor(number(loaded.bestCoins?.[i])),0,999));
  initial.stars=Array.from({length:16},(_,i)=>loaded.stars?.[i]===true);
  initial.music=loaded.music!==false;initial.finished=loaded.finished===true;
  if(loaded.checkpoint&&Number.isInteger(loaded.checkpoint.level)&&loaded.checkpoint.level>=0&&loaded.checkpoint.level<initial.unlocked)
    initial.checkpoint={level:loaded.checkpoint.level,hearts:clamp(number(loaded.checkpoint.hearts,3),1,3)};
 }catch(_){/* Safari private mode and corrupted saves fall back to a safe clean state. */}
 return initial;
}
function persist(save){
 try{localStorage.setItem(SAVE_KEY,JSON.stringify(save));return true}
 catch(_){return false}
}
function roundedRect(ctx,x,y,w,h,r,fill,stroke){
 const radius=Math.min(r,w/2,h/2);
 ctx.beginPath();ctx.moveTo(x+radius,y);ctx.arcTo(x+w,y,x+w,y+h,radius);
 ctx.arcTo(x+w,y+h,x,y+h,radius);ctx.arcTo(x,y+h,x,y,radius);
 ctx.arcTo(x,y,x+w,y,radius);ctx.closePath();
 if(fill){ctx.fillStyle=fill;ctx.fill()}
 if(stroke){ctx.strokeStyle=stroke;ctx.stroke()}
}
function starPath(ctx,cx,cy,outer,inner,rotation=-Math.PI/2){
 ctx.beginPath();
 for(let i=0;i<10;i++){
  const a=rotation+i*Math.PI/5,rad=i%2?inner:outer;
  const x=cx+Math.cos(a)*rad,y=cy+Math.sin(a)*rad;
  if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)
 }
 ctx.closePath()
}
const pick=(array,i)=>array[((i%array.length)+array.length)%array.length];
class CatGame{
 constructor(){
  this.canvas=$('game-canvas');this.ctx=this.canvas.getContext('2d');
  this.audio=new window.CAT_AUDIO();
  this.save=loadSave();this.audio.enabled=this.save.music;
  this.phase='menu';this.level=levels[0];this.levelIndex=0;
  this.player=null;this.held={left:false,right:false,shoot:false};this.jumpBuffer=0;this.dashRequest=false;this.shootHeld=0;this.shotCooldown=0;this.dashCooldown=0;
  this.camera=0;this.time=0;this.framePrev=0;this.score=0;this.coins=0;
  this.particles=[];this.orbs=[];this.enemies=[];this.hearts=[];this.shots=[];this.enemyShots=[];this.boss=null;this.starFound=false;this.checkpointHit=false;
  this.health=3;this.flash=0;this.soundEnabled=this.save.music;this.effects=0;
  this.overlay=$('screen-overlay');this.actions=$('overlay-actions');
  this.bind();
  this.fillLevels();
  this.refreshStats();
  this.setLevelScene(0,false);
  this.welcome();
  requestAnimationFrame(time=>this.loop(time));
 }
 bind(){
  $('play-btn').addEventListener('click',()=>this.chooseLevel(this.save.lastLevel));
  $('continue-btn').addEventListener('click',()=>this.chooseLevel(this.save.lastLevel));
  $('pause-btn').addEventListener('click',()=>this.togglePause());
  $('restart-btn').addEventListener('click',()=>this.chooseLevel(this.levelIndex,true));
  $('music-btn').addEventListener('click',()=>this.toggleMusic());
  $('fullscreen-btn').addEventListener('click',()=>{
    const shell=$('game-shell');
    if(!document.fullscreenElement){shell.requestFullscreen?.().catch(()=>{})}
    else document.exitFullscreen?.().catch(()=>{});
  });
  $('reset-btn').addEventListener('click',()=>{
    if(!window.confirm('¿Borrar de este navegador el avance de Cat? Esta acción no se puede deshacer.'))return;
    this.save={version:1,unlocked:1,lastLevel:0,bestCoins:Array(16).fill(0),stars:Array(16).fill(false),checkpoint:null,music:this.audio.enabled,finished:false};
    persist(this.save);this.fillLevels();this.refreshStats();this.setLevelScene(0,false);this.welcome();
  });
  window.addEventListener('keydown',event=>{
    const target=event.target;
    if(target&&(['INPUT','TEXTAREA','SELECT'].includes(target.tagName)||target.isContentEditable))return;
    const key=event.key.toLowerCase();
    if(['arrowleft','arrowright','arrowup',' ','w','a','d','j','k','f','shift','l'].includes(key)&&this.phase==='playing')event.preventDefault();
    if(key==='arrowleft'||key==='a')this.held.left=true;
    if(key==='arrowright'||key==='d')this.held.right=true;
    if((key===' '||key==='arrowup'||key==='w')&&!event.repeat){this.jumpBuffer=.16;if(this.phase==='playing')this.audio.init()}
    if((key==='j'||key==='k'||key==='f')&&this.phase==='playing'){if(!this.held.shoot)this.shoot(false);this.held.shoot=true}
    if((key==='shift'||key==='l')&&this.phase==='playing'&&!event.repeat){this.dashRequest=true}
    if(key==='p'||key==='escape'){event.preventDefault();if(!event.repeat)this.togglePause()}
    if(key==='m'&&!event.repeat)this.toggleMusic();
    if(key==='r'&&!event.repeat&&this.phase==='playing')this.chooseLevel(this.levelIndex,true);
  });
  window.addEventListener('keyup',event=>{
    const key=event.key.toLowerCase();
    if(key==='arrowleft'||key==='a')this.held.left=false;
    if(key==='arrowright'||key==='d')this.held.right=false;
    if(key==='j'||key==='k'||key==='f'){if(this.held.shoot&&this.shootHeld>=.68)this.shoot(true);this.held.shoot=false;this.shootHeld=0}
  });
  window.addEventListener('blur',()=>{this.held.left=false;this.held.right=false;this.held.shoot=false;this.shootHeld=0;if(this.phase==='playing')this.pause()});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&this.phase==='playing')this.pause()});
  for(const control of document.querySelectorAll('[data-control]')){
    const kind=control.dataset.control;
    control.addEventListener('pointerdown',ev=>{
      ev.preventDefault();control.setPointerCapture?.(ev.pointerId);
      this.audio.init();
      if(kind==='jump')this.jumpBuffer=.19;
      else if(kind==='dash')this.dashRequest=true;
      else if(kind==='shoot'){if(!this.held.shoot)this.shoot(false);this.held.shoot=true}
      else this.held[kind]=true;
      control.classList.add('is-held')
    });
    const release=()=>{if(kind==='shoot'&&this.held.shoot&&this.shootHeld>=.68)this.shoot(true);
      if(kind==='shoot')this.shootHeld=0;
      if(kind!=='jump'&&kind!=='dash')this.held[kind]=false;
      control.classList.remove('is-held')};
    control.addEventListener('pointerup',release);
    control.addEventListener('pointercancel',release);
    control.addEventListener('lostpointercapture',release);
  }
 }
 showOverlay(kicker,title,body,actions){
  this.overlay.hidden=false;
  $('overlay-kicker').textContent=kicker;
  $('overlay-title').textContent=title;
  $('overlay-copy').textContent=body;
  this.actions.replaceChildren();
  actions.forEach((action,i)=>{
    const btn=document.createElement('button');
    btn.type='button';btn.className=i===0?'button button-bright':'button button-glass';
    btn.textContent=action.label;
    btn.addEventListener('click',()=>{this.audio.init();this.audio.sfx('click');action.onClick()});
    this.actions.append(btn);
  });
 }
 hideOverlay(){this.overlay.hidden=true}
 welcome(){
  this.phase='menu';
  $('pause-btn').disabled=true;
  $('level-name').textContent='Cat te espera en Lunaria';
  $('game-message').textContent='Selecciona «Jugar» para comenzar la aventura.';
  this.showOverlay('UNA AVENTURA DE ESTRELLAS','El viaje de Cat',
    'Las máquinas del Núcleo de Medianoche han apagado Lunaria. Cat, una joven inventora de sombrero negro, usará el Pulso Aurora de su madre para rescatar a Lira. Dispara con J/K, mantén para cargar y esquiva con Mayús.',
    [{label:this.save.unlocked>1?'▶ Continuar aventura':'▶ Empezar aventura',onClick:()=>this.chooseLevel(this.save.lastLevel)},
     {label:'Explorar niveles',onClick:()=>{$('level-map').scrollIntoView({behavior:'smooth',block:'start'})}}]);
 }
 chooseLevel(index,forceFresh=false){
  if(index>=this.save.unlocked)return;
  $('jugar').scrollIntoView?.({behavior:'smooth',block:'start'});
  this.audio.init();
  if(index%4===0&&!forceFresh&&(!this.save.checkpoint||this.save.checkpoint.level!==index)){
    const chapter=chapters[Math.floor(index/4)];
    this.phase='story';this.setLevelScene(index,false);
    this.showOverlay('CAPÍTULO '+(Math.floor(index/4)+1)+' DE 4',chapter.title,chapter.story,
      [{label:'✦ Comenzar nivel '+(index+1),onClick:()=>this.startLevel(index,forceFresh)},
       {label:'Volver al mapa',onClick:()=>this.welcome()}]);
  }else this.startLevel(index,forceFresh);
 }
 setLevelScene(index,restore){
  this.levelIndex=index;this.level=levels[index];
  this.time=0;this.camera=0;
  this.coins=0;this.score=0;this.starFound=false;this.checkpointHit=false;this.jumpBuffer=0;this.dashRequest=false;this.shootHeld=0;this.shotCooldown=0;this.dashCooldown=0;this.shots=[];this.enemyShots=[];
  this.health=3;this.flash=0;this.particles=[];
  this.orbs=this.level.orbs.map((orb,i)=>({...orb,hit:false,phase:i*.71}));
  this.enemies=this.level.enemies.map((enemy,i)=>({...enemy,alive:true,phase:i*.8,homeX:enemy.x,hp:enemy.hp||2,shootTimer:1.3+i*.57,hitFlash:0}));
  this.boss=this.level.boss?{...this.level.boss,maxHp:this.level.boss.hp,active:false,dead:false,shootTimer:1.7,hitFlash:0,phase:0}:null;
  this.hearts=this.level.hearts.map(item=>({...item,hit:false}));
  const resume=restore&&this.save.checkpoint?.level===index;
  this.checkpointHit=Boolean(resume);
  this.health=resume?Math.max(2,this.save.checkpoint.hearts):3;
  this.player={x:resume?this.level.checkpoint.x+30:72,y:GROUND-62,w:39,h:62,vx:0,vy:0,grounded:true,coyote:.095,canDouble:true,facing:1,invuln:0,walk:0,dash:0,charge:0,recoil:0,land:0};
  this.camera=clamp(this.player.x-320,0,this.level.length-W);
  $('level-name').textContent=(index+1)+' · '+this.level.name;
  $('game-message').textContent=this.level.tip;
  this.updateHud();
 }
 startLevel(index,forceFresh=false){
  this.setLevelScene(index,!forceFresh);
  if(forceFresh&&this.save.checkpoint?.level===index){this.save.checkpoint=null;persist(this.save)}
  this.phase='playing';this.hideOverlay();this.held.left=false;this.held.right=false;this.held.shoot=false;
  $('pause-btn').disabled=false;
  this.audio.init();this.refreshStats();
  this.canvas.focus?.({preventScroll:true});
 }
 updateHud(){
  $('hud-hearts').textContent='❤ '.repeat(this.health).trim()||'—';
  $('hud-coins').textContent=imageFriendly(this.coins);
  $('hud-star').textContent=this.starFound?'★ Encontrada':'☆ Pendiente';
  $('hud-checkpoint').textContent=this.checkpointHit?'✓ Guardado':'◇ Sin activar';
  $('hud-progress').textContent=Math.round((this.player?.x||0)/this.level.length*100)+' %';
  const power=$('hud-power');if(power)power.textContent=this.shootHeld>=.68?'✦ ¡CARGADO!':this.shootHeld>0?'Cargando '+Math.round(this.shootHeld/.68*100)+' %':'PULSO AURORA';
  const dash=$('hud-dash');if(dash)dash.textContent=this.dashCooldown>0?'Recarga '+this.dashCooldown.toFixed(1)+' s':'LISTO';
  const boss=$('boss-status');if(boss){boss.hidden=!this.boss||this.boss.dead||!this.boss.active;
     if(!boss.hidden){$('boss-name').textContent='JEFE · '+this.boss.kind;$('boss-health').style.width=clamp(100*this.boss.hp/this.boss.maxHp,0,100)+'%';}}
  $('progress-fill').style.width=clamp((this.player?.x||0)/this.level.length*100,0,100)+'%';
 }
 refreshStats(){
  $('total-stars').textContent=starsFor(this.save)+'/16';
  $('total-levels').textContent=(this.save.finished?16:this.save.unlocked-1)+'/16';
  $('total-coins').textContent=imageFriendly(this.save.bestCoins.reduce((a,b)=>a+b,0));
  $('music-btn').textContent=this.audio.enabled?'♫ Música: sí':'♪ Música: no';
  $('music-btn').setAttribute('aria-pressed',String(this.audio.enabled));
  $('continue-btn').textContent=this.save.unlocked>1?'Continuar desde el nivel '+(this.save.lastLevel+1):'Comenzar desde el nivel 1';
  this.fillLevels();
 }
 fillLevels(){
  const list=$('level-list');list.replaceChildren();
  levels.forEach((lvl,index)=>{
    const locked=index>=this.save.unlocked;
    const btn=document.createElement('button');
    btn.type='button';btn.disabled=locked;
    btn.className='level-tile'+(locked?' is-locked':'')+(this.save.stars[index]?' has-star':'');
    const head=document.createElement('span');head.className='level-number';head.textContent=locked?'🔒':String(index+1).padStart(2,'0');
    const text=document.createElement('span');text.className='level-label';text.textContent=lvl.name;
    const detail=document.createElement('span');detail.className='level-detail';detail.textContent=locked?'Bloqueado':this.save.stars[index]?'★ Estrella conseguida':(index<this.save.unlocked-1||(this.save.finished&&index===15))?'✓ Completado':'Disponible';
    btn.append(head,text,detail);
    btn.addEventListener('click',()=>{if(!locked)this.chooseLevel(index)});
    list.append(btn);
  });
 }
 toggleMusic(){
  this.audio.toggle();this.save.music=this.audio.enabled;
  persist(this.save);this.refreshStats();
 }
 pause(){
  if(this.phase!=='playing')return;
  this.phase='paused';this.held.left=false;this.held.right=false;this.held.shoot=false;this.shootHeld=0;
  this.showOverlay('UN DESCANSITO','Pausa de aventura','Cat espera a que estés lista. Tu progreso se conserva cuando completas niveles o tocas un cristal de control.',
    [{label:'▶ Seguir jugando',onClick:()=>{this.phase='playing';this.hideOverlay()}},
     {label:'↺ Reiniciar nivel',onClick:()=>this.startLevel(this.levelIndex,true)},
     {label:'Mapa de niveles',onClick:()=>this.welcome()}]);
 }
 togglePause(){
  if(this.phase==='playing')this.pause();
  else if(this.phase==='paused'){this.phase='playing';this.hideOverlay();this.audio.init()}
 }
 burst(x,y,color,count=11){
  for(let i=0;i<count;i++){
   const a=i*2.399+Math.random()*.3;
   this.particles.push({x,y,vx:Math.cos(a)*(55+Math.random()*120),vy:Math.sin(a)*(70+Math.random()*100)-45,life:.5+Math.random()*.35,max:.85,color,r:2+Math.random()*4});
  }
  if(this.particles.length>155)this.particles.splice(0,this.particles.length-155);
 }
 hurt(sourceX=0){
  const p=this.player;
  if(this.phase!=='playing'||p.invuln>0)return;
  this.health--;p.invuln=1.2;this.flash=.16;this.audio.sfx('hurt');
  this.burst(p.x+p.w/2,p.y+p.h/2,'#ffa2c7',13);
  this.updateHud();
  if(this.health<=0){this.die();return}
  p.vy=-370;p.vx=sourceX<p.x?200:-200;
 }
 die(){
  this.phase='dead';this.audio.sfx('over');
  $('pause-btn').disabled=true;this.held.left=false;this.held.right=false;this.held.shoot=false;this.shootHeld=0;
  this.showOverlay('SIGUE BRILLANDO','¡Cat necesita un descanso!','Perdiste tus tres corazones, pero tu avance guardado sigue a salvo. Puedes intentarlo otra vez.',
   [{label:'↺ Reintentar nivel',onClick:()=>this.startLevel(this.levelIndex,false)},
    {label:'Ir al mapa',onClick:()=>this.welcome()}]);
 }
 nextLevel(){
  if(this.levelIndex===15){this.completeAdventure();return}
  this.chooseLevel(this.levelIndex+1);
 }
 finishLevel(){
  if(this.phase!=='playing')return;
  this.phase='levelDone';this.audio.sfx('finish');$('pause-btn').disabled=true;
  const i=this.levelIndex;
  this.save.bestCoins[i]=Math.max(this.save.bestCoins[i],this.coins);
  if(this.starFound)this.save.stars[i]=true;
  this.save.unlocked=Math.max(this.save.unlocked,Math.min(16,i+2));
  this.save.lastLevel=Math.min(15,i+1);
  this.save.checkpoint=null;
  if(i===15)this.save.finished=true;
  const written=persist(this.save);
  this.refreshStats();
  this.burst(this.level.portal.x+28,this.level.portal.y+33,'#ffe69d',38);
  const details='Monedas: '+this.coins+' · '+(this.starFound?'★ Estrella conseguida':'☆ Aún puedes volver por la estrella')+(written?' · Progreso guardado':' · Advertencia: el navegador no permitió guardar');
  if(i===15){this.completeAdventure();return}
  const chapterDone=i%4===3,chapter=chapters[Math.floor(i/4)];
  this.showOverlay(chapterDone?'CAPÍTULO COMPLETADO':'NIVEL SUPERADO',
    chapterDone?'✦ '+chapter.title+' ✦':'¡Lo lograste, Cat!',
    (chapterDone?chapter.end+' ':'')+details,
    [{label:chapterDone?'✦ Siguiente capítulo':'▶ Siguiente nivel',onClick:()=>this.nextLevel()},
     {label:'Ver mapa de niveles',onClick:()=>this.welcome()}]);
 }
 completeAdventure(){
  this.phase='ending';$('pause-btn').disabled=true;
  this.showOverlay('FIN · UNA NUEVA CONSTELACIÓN','¡Las estrellas regresaron!',
   chapters[3].end+' Has recuperado '+starsFor(this.save)+' de 16 estrellas especiales. Puedes volver al mapa para completar las que te falten.',
   [{label:'★ Volver a jugar',onClick:()=>this.chooseLevel(0,true)},
    {label:'Ver niveles y estrellas',onClick:()=>this.welcome()}]);
 }
 respawn(){
  this.hurt();
  if(this.phase!=='playing')return;
  const p=this.player;
  p.x=this.checkpointHit?this.level.checkpoint.x+22:72;
  p.y=GROUND-p.h;p.vx=0;p.vy=0;p.grounded=true;p.coyote=.095;p.canDouble=true;p.invuln=1.4;p.dash=0;this.enemyShots=[];
  this.camera=clamp(p.x-320,0,this.level.length-W);
 }

 // Pulso Aurora: J/K/F o botón táctil. Una pulsación dispara; mantener y soltar carga un pulso amplio.
 shoot(charged){
  if(this.phase!=='playing'||!this.player)return;
  if(!charged&&this.shotCooldown>0)return;
  const p=this.player,dir=p.facing,boost=charged?3:1;
  this.shots.push({x:p.x+p.w/2+dir*25,y:p.y+29,vx:dir*(charged?750:840),vy:0,r:charged?15:7,damage:boost,ttl:1.2,charged});
  if(this.shots.length>18)this.shots.shift();
  this.shotCooldown=charged?.22:.24;p.recoil=.15;
  this.audio.sfx(charged?'power':'shoot');
  this.burst(p.x+p.w/2+dir*23,p.y+29,charged?'#fff3a3':'#94fff4',charged?14:5);
 }
 enemyFire(x,y,targetX,targetY,speed=255,spread=0){
  const a=Math.atan2(targetY-y,targetX-x)+spread;
  this.enemyShots.push({x,y,vx:Math.cos(a)*speed,vy:Math.sin(a)*speed,r:7,ttl:3.5});
  if(this.enemyShots.length>65)this.enemyShots.splice(0,this.enemyShots.length-65);
 }
 defeatEnemy(enemy){
  enemy.alive=false;
  this.burst(enemy.x,enemy.y,'#b8b2ff',19);
  this.audio.sfx('enemy');this.coins+=2;this.score+=45;
 }
 hitBoss(amount){
  const b=this.boss;if(!b||b.dead)return;
  b.active=true;b.hp=Math.max(0,b.hp-amount);b.hitFlash=.18;
  this.burst(b.x+b.w*.55,b.y+45,'#fff0a6',7+amount*2);
  this.audio.sfx('boss');
  if(b.hp<=0){
   b.dead=true;this.enemyShots=[];this.burst(b.x+b.w/2,b.y+b.h/2,'#fff2b0',55);
   this.audio.sfx('finish');
   $('game-message').textContent='¡El guardián cayó! El portal está desbloqueado.';
  }
 }
 step(dt){
  if(this.phase!=='playing')return;
  const p=this.player,l=this.level;
  this.time+=dt;
  this.audio.update(dt,l.chapter,true);
  p.invuln=Math.max(0,p.invuln-dt);p.recoil=Math.max(0,p.recoil-dt);p.land=Math.max(0,p.land-dt);
  this.flash=Math.max(0,this.flash-dt);
  this.jumpBuffer=Math.max(0,this.jumpBuffer-dt);
  this.shotCooldown=Math.max(0,this.shotCooldown-dt);
  this.dashCooldown=Math.max(0,this.dashCooldown-dt);
  this.shootHeld=this.held.shoot?Math.min(1.3,this.shootHeld+dt):0;
  const dir=Number(this.held.right)-Number(this.held.left);
  if(dir!==0)p.facing=dir;
  if(this.dashRequest&&this.dashCooldown<=0){
   p.dash=.17;this.dashCooldown=1.65;p.invuln=Math.max(p.invuln,.24);p.vy=0;
   this.audio.sfx('dash');this.burst(p.x+p.w/2,p.y+35,'#b6fff9',14);
  }
  this.dashRequest=false;
  p.vx=p.dash>0?p.facing*675:dir*290;
  p.dash=Math.max(0,p.dash-dt);
  if(Math.abs(p.vx)>0)p.walk+=dt*(p.dash>0?24:13);
  p.coyote=p.grounded?.10:Math.max(0,p.coyote-dt);
  if(this.jumpBuffer>0&&(p.grounded||p.coyote>0||p.canDouble)){
   if(!p.grounded&&p.coyote<=0)p.canDouble=false;
   p.vy=p.grounded||p.coyote>0?-660:-590;
   p.grounded=false;p.coyote=0;this.jumpBuffer=0;
   this.audio.sfx('jump');this.burst(p.x+p.w/2,p.y+p.h-3,'#c7f6e3',7);
  }
  for(const plat of l.moving){
   const previous=plat.y;
   plat.y=plat.originY+Math.sin(this.time*plat.speed+plat.phase)*plat.amplitude;
   plat.dy=plat.y-previous;
  }
  const priorBottom=p.y+p.h;
  p.x=clamp(p.x+p.vx*dt,1,l.length-p.w-2);
  if(p.dash<=0)p.vy=Math.min(1140,p.vy+1750*dt);
  p.y+=p.vy*dt;
  p.grounded=false;
  if(p.vy>=0){
   const candidates=l.ground.map(g=>({x:g.x,y:GROUND,w:g.w,h:70})).concat(l.platforms);
   let platform=null;
   for(const plat of candidates){
    if(p.x+p.w>plat.x+7&&p.x<plat.x+plat.w-7&&priorBottom<=plat.y+14&&p.y+p.h>=plat.y){
     if(!platform||plat.y<platform.y)platform=plat;
    }
   }
   if(platform){
    p.y=platform.y-p.h;
    if(platform.dy)p.y+=Math.min(0,platform.dy);
    p.vy=0;p.grounded=true;p.canDouble=true;
    if(priorBottom<platform.y-12&&Math.abs(p.vx)>60){p.land=.12;this.burst(p.x+20,p.y+p.h,'#d2edff',3)}
   }
  }
  if(p.y>H+130){this.respawn();return}
  const touch={x:p.x+5,y:p.y+5,w:p.w-10,h:p.h-7};
  for(const orb of this.orbs){
   if(orb.hit)continue;
   if(Math.abs(touch.x-orb.x)<26&&Math.abs(touch.y-orb.y)<42){
    orb.hit=true;this.coins++;this.score+=10;this.audio.sfx('coin');
    this.burst(orb.x,orb.y,'#ffe89e',8);
   }
  }
  const st=l.star;
  if(!this.starFound&&Math.abs(p.x+p.w/2-st.x)<30&&Math.abs(p.y+p.h/2-st.y)<42){
   this.starFound=true;this.score+=100;this.audio.sfx('star');
   $('game-message').textContent='¡Encontraste la estrella secreta! Llega al portal para guardarla.';
   this.burst(st.x,st.y,'#fff6a0',26);
  }
  for(const heart of this.hearts){
   if(heart.hit||this.health>=3)continue;
   if(Math.abs(p.x+p.w/2-heart.x)<31&&Math.abs(p.y+p.h/2-heart.y)<40){
    heart.hit=true;this.health=Math.min(3,this.health+1);this.audio.sfx('checkpoint');
    this.burst(heart.x,heart.y,'#ffadce',14);
   }
  }
  if(!this.checkpointHit&&Math.abs(p.x+p.w/2-l.checkpoint.x)<35&&p.y+p.h>l.checkpoint.y){
   this.checkpointHit=true;
   this.save.checkpoint={level:l.index,hearts:this.health};
   persist(this.save);this.audio.sfx('checkpoint');
   this.burst(l.checkpoint.x,l.checkpoint.y,'#8df6ff',18);
   $('game-message').textContent='¡Cristal activado! Tu punto de control está guardado.';
  }
  for(const spike of l.spikes)if(overlap(touch,spike))this.hurt(spike.x);
  for(const enemy of this.enemies){
   if(!enemy.alive)continue;
   enemy.hitFlash=Math.max(0,enemy.hitFlash-dt);
   enemy.x=enemy.homeX+Math.sin(this.time*enemy.speed+enemy.phase)*enemy.range;
   if(enemy.type==='drone')enemy.y=320+Math.sin(this.time*2.2+enemy.phase)*30;
   const box={x:enemy.x-19,y:enemy.y-15,w:38,h:38};
   if(overlap(touch,box)){
    if(p.vy>85&&priorBottom<=box.y+12){
     enemy.hp-=1;p.vy=-400;p.canDouble=true;this.audio.sfx('bounce');
     if(enemy.hp<=0)this.defeatEnemy(enemy);
     else enemy.hitFlash=.22;
    }else this.hurt(enemy.x);
   }
   const distance=Math.abs(p.x-enemy.x);
   if(enemy.type!=='crawler'&&distance<650){
    enemy.shootTimer-=dt;
    if(enemy.shootTimer<=0){
     this.enemyFire(enemy.x,enemy.y+9,p.x+p.w/2,p.y+24,enemy.type==='drone'?230:265);
     enemy.shootTimer=Math.max(.9,2.35-l.index*.04);
    }
   }
  }
  const boss=this.boss;
  if(boss&&!boss.dead){
   if(p.x>boss.x-770)boss.active=true;
   if(boss.active){
    boss.phase+=dt;boss.hitFlash=Math.max(0,boss.hitFlash-dt);
    boss.y=GROUND-boss.h+Math.sin(boss.phase*1.45)*12;
    boss.shootTimer-=dt;
    if(boss.shootTimer<=0){
     for(let i=-1;i<=1;i++)this.enemyFire(boss.x+25,boss.y+38,p.x+p.w/2,p.y+27,250+l.chapter*20,i*.22);
     boss.shootTimer=Math.max(.72,1.55-l.chapter*.11);
    }
   }
   if(overlap(touch,{x:boss.x,y:boss.y,w:boss.w,h:boss.h}))this.hurt(boss.x);
  }
  for(const shot of this.shots){
   shot.x+=shot.vx*dt;shot.y+=shot.vy*dt;shot.ttl-=dt;
   if(shot.ttl<=0)continue;
   for(const enemy of this.enemies){
    if(!enemy.alive)continue;
    if(overlap({x:shot.x-shot.r,y:shot.y-shot.r,w:shot.r*2,h:shot.r*2},{x:enemy.x-21,y:enemy.y-19,w:42,h:42})){
     enemy.hp-=shot.damage;enemy.hitFlash=.19;shot.ttl=0;
     this.burst(shot.x,shot.y,'#9fffee',7);
     if(enemy.hp<=0)this.defeatEnemy(enemy);
     break;
    }
   }
   if(shot.ttl>0&&boss&&!boss.dead&&overlap({x:shot.x-shot.r,y:shot.y-shot.r,w:shot.r*2,h:shot.r*2},boss)){
    shot.ttl=0;this.hitBoss(shot.damage);
   }
  }
  this.shots=this.shots.filter(shot=>shot.ttl>0&&shot.x>this.camera-130&&shot.x<this.camera+W+250);
  for(const bolt of this.enemyShots){
   bolt.x+=bolt.vx*dt;bolt.y+=bolt.vy*dt;bolt.ttl-=dt;
   if(bolt.ttl>0&&overlap({x:bolt.x-bolt.r,y:bolt.y-bolt.r,w:bolt.r*2,h:bolt.r*2},touch)){
    this.hurt(bolt.x);bolt.ttl=0;
   }
  }
  this.enemyShots=this.enemyShots.filter(b=>b.ttl>0&&b.y<H+80&&b.y>-100&&b.x>this.camera-130&&b.x<this.camera+W+150);
  if(p.x>l.portal.x-17&&p.x<l.portal.x+62&&p.y+p.h>l.portal.y+20){
   if(!boss||boss.dead)this.finishLevel();
   else if(boss.active)$('game-message').textContent='Derrota al guardián primero. ¡Dispara con J/K!';
  }
  this.camera+=(clamp(p.x-320,0,l.length-W)-this.camera)*Math.min(1,dt*5.5);
  this.updateHud();
  for(const particle of this.particles){
   particle.life-=dt;particle.x+=particle.vx*dt;particle.y+=particle.vy*dt;particle.vy+=170*dt;
  }
  this.particles=this.particles.filter(x=>x.life>0);
 }
 loop(t){
  if(!this.framePrev)this.framePrev=t;
  const dt=Math.min(.033,(t-this.framePrev)/1000);
  this.framePrev=t;
  this.step(dt);
  this.draw(t/1000);
  requestAnimationFrame(time=>this.loop(time));
 }
 draw(time){
  const ctx=this.ctx,l=this.level;
  if(!ctx)return;
  ctx.clearRect(0,0,W,H);
  this.drawSky(ctx,l,time);
  ctx.save();ctx.translate(-this.camera,0);
  this.drawTerrain(ctx,l,time);
  this.drawOrbs(ctx,time);
  this.drawHearts(ctx,time);
  this.drawStar(ctx,time);
  this.drawCheckpoint(ctx,time);
  this.drawEnemies(ctx,time);
  this.drawBoss(ctx,time);
  this.drawProjectiles(ctx,time);
  this.drawPortal(ctx,time);
  this.drawCat(ctx,this.player,time);
  for(const particle of this.particles){
   ctx.globalAlpha=clamp(particle.life/particle.max,0,1);
   ctx.fillStyle=particle.color;ctx.beginPath();ctx.arc(particle.x,particle.y,particle.r,0,Math.PI*2);ctx.fill();
  }
  ctx.restore();ctx.globalAlpha=1;
  if(this.flash>0){ctx.fillStyle='rgba(255,120,140,.16)';ctx.fillRect(0,0,W,H)}
  if(this.phase==='menu'||this.phase==='story'){
   ctx.fillStyle='rgba(15,15,45,.12)';ctx.fillRect(0,0,W,H);
  }
 }
 drawSky(ctx,l,time){
  const sky=l.theme.sky;
  const gradient=ctx.createLinearGradient(0,0,0,H);
  gradient.addColorStop(0,sky[0]);gradient.addColorStop(.62,sky[1]);gradient.addColorStop(1,sky[2]);
  ctx.fillStyle=gradient;ctx.fillRect(0,0,W,H);
  ctx.fillStyle='rgba(255,255,255,.65)';
  for(let i=0;i<65;i++){
   const x=((i*173+Math.sin(i*17)*53-this.camera*.08)%(W+100)+(W+100))%(W+100);
   const y=25+((i*71+l.chapter*27)%290);
   const twinkle=.5+.5*Math.sin(time*2+i);
   ctx.globalAlpha=(.24+twinkle*.55)*(l.chapter===1?.7:1);
   ctx.beginPath();ctx.arc(x,y,1+i%3*.42,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
  const moonX=770-this.camera*.045,moonY=104+Math.sin(time*.5)*6;
  ctx.shadowColor=l.theme.accent;ctx.shadowBlur=35;
  ctx.fillStyle=l.chapter===1?'#fff2cb':'#fbe2c6';
  ctx.beginPath();ctx.arc(moonX,moonY,37,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
  for(let layer=0;layer<3;layer++){
   const offset=this.camera*(.12+layer*.16);
   const level=370+layer*34;
   ctx.beginPath();ctx.moveTo(0,H);
   for(let x=-100;x<W+150;x+=10){
    const xx=x+offset,yy=level+Math.sin(xx/126+layer)*24+Math.cos(xx/67+layer*2)*11;
    ctx.lineTo(x,yy)
   }
   ctx.lineTo(W,H);ctx.closePath();
   ctx.fillStyle=['rgba(26,27,78,.24)','rgba(27,28,75,.32)','rgba(34,29,75,.48)'][layer];
   ctx.fill();
  }
  if(l.chapter===1){
   for(let i=0;i<9;i++){
    const x=(((i*250-this.camera*.25)%(W+290))+(W+290))%(W+290)-90;
    const y=145+(i%3)*86+Math.sin(time*.5+i)*8;
    ctx.fillStyle='rgba(255,255,255,.19)';
    for(let j=0;j<3;j++){ctx.beginPath();ctx.ellipse(x+j*26,y+(j%2)*5,38,17,0,0,Math.PI*2);ctx.fill()}
   }
  }
  if(l.chapter===2){
   for(let i=0;i<14;i++){
    const x=(((i*183-this.camera*.22)%(W+150))+(W+150))%(W+150);
    const y=260+(i%3)*68;
    ctx.fillStyle='rgba(138,247,247,.13)';starPath(ctx,x,y,13,5,time*.13);ctx.fill();
   }
  }
 }
 drawTerrain(ctx,l,time){
  // Los elementos de decoración se colocan antes de los suelos.
  for(let i=0;i<26;i++){
   const x=100+i*139;
   if(x<this.camera-80||x>this.camera+W+80)continue;
   const g=l.ground.some(seg=>x>seg.x&&x<seg.x+seg.w);
   if(!g)continue;
   if(l.chapter===0){
    ctx.strokeStyle='#2f796e';ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(x,GROUND);ctx.lineTo(x,GROUND-39-(i%3)*13);ctx.stroke();
    ctx.fillStyle='#52ba96';ctx.beginPath();ctx.ellipse(x,GROUND-53-(i%3)*10,19,27,0,0,Math.PI*2);ctx.fill();
   }else if(l.chapter===1){
    ctx.fillStyle='#e9ddff';ctx.beginPath();ctx.arc(x,GROUND-15,22,Math.PI,Math.PI*2);ctx.fill();
   }else if(l.chapter===2){
    ctx.fillStyle='#7e91de';starPath(ctx,x,GROUND-24,20,9,-Math.PI/2);ctx.fill();
   }else{
    ctx.fillStyle='#9d6078';ctx.fillRect(x-6,GROUND-31,12,31);
    ctx.fillStyle='#fbc97a';ctx.beginPath();ctx.arc(x,GROUND-34,9,0,Math.PI*2);ctx.fill();
   }
  }
  for(const ground of l.ground){
   ctx.fillStyle=l.theme.ground;ctx.fillRect(ground.x,GROUND,ground.w,H-GROUND+180);
   ctx.fillStyle=l.theme.top;ctx.fillRect(ground.x,GROUND,ground.w,11);
   ctx.fillStyle='rgba(255,255,255,.17)';
   for(let x=ground.x+29;x<ground.x+ground.w;x+=58)ctx.fillRect(x,GROUND+30+(x%3)*8,19,4);
  }
  for(const p of l.platforms){
   if(p.x+p.w<this.camera-75||p.x>this.camera+W+75)continue;
   ctx.shadowColor='rgba(0,0,0,.17)';ctx.shadowBlur=10;ctx.shadowOffsetY=6;
   roundedRect(ctx,p.x,p.y,p.w,p.h,9,l.theme.ground);ctx.shadowBlur=0;ctx.shadowOffsetY=0;
   roundedRect(ctx,p.x,p.y-2,p.w,9,6,l.theme.top);
   ctx.fillStyle='rgba(255,255,255,.13)';
   for(let x=p.x+16;x<p.x+p.w-10;x+=34)ctx.fillRect(x,p.y+13,11,3);
  }
  ctx.fillStyle='#fa9caa';
  for(const s of l.spikes){
   const count=Math.max(1,Math.floor(s.w/12));
   for(let i=0;i<count;i++){
    const xx=s.x+i*s.w/count;
    ctx.beginPath();ctx.moveTo(xx,s.y+s.h);ctx.lineTo(xx+s.w/count/2,s.y);ctx.lineTo(xx+s.w/count,s.y+s.h);ctx.closePath();ctx.fill();
   }
  }
 }
 drawOrbs(ctx,time){
  for(const orb of this.orbs){
   if(orb.hit||Math.abs(orb.x-this.camera)>W+90)continue;
   const y=orb.y+Math.sin(time*3+orb.phase)*5;
   ctx.shadowColor='#fff1a5';ctx.shadowBlur=15;ctx.fillStyle='#fff1b0';
   ctx.beginPath();ctx.arc(orb.x,y,7,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
   ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(orb.x-2,y-2,2,0,Math.PI*2);ctx.fill();
  }
 }
 drawHearts(ctx,time){
  for(const heart of this.hearts){
   if(heart.hit||Math.abs(heart.x-this.camera)>W+80)continue;
   const y=heart.y+Math.sin(time*3)*4;
   ctx.save();ctx.translate(heart.x,y);
   ctx.fillStyle='#ff95be';ctx.shadowColor='#ffafd4';ctx.shadowBlur=18;
   ctx.beginPath();ctx.moveTo(0,11);
   ctx.bezierCurveTo(-18,0,-16,-13,-4,-12);
   ctx.bezierCurveTo(0,-12,0,-7,0,-6);
   ctx.bezierCurveTo(3,-17,15,-16,16,-5);
   ctx.bezierCurveTo(17,2,7,8,0,11);ctx.fill();
   ctx.restore();
  }
 }
 drawStar(ctx,time){
  if(this.starFound)return;
  const s=this.level.star;if(s.x<this.camera-70||s.x>this.camera+W+70)return;
  ctx.save();ctx.translate(s.x,s.y+Math.sin(time*3)*7);ctx.rotate(Math.sin(time)*.2);
  ctx.shadowBlur=34;ctx.shadowColor='#fff6ac';
  ctx.fillStyle='#fff6ad';starPath(ctx,0,0,19,9);ctx.fill();
  ctx.shadowBlur=0;ctx.fillStyle='#fff';starPath(ctx,0,0,8,4);ctx.fill();
  ctx.restore();
 }
 drawCheckpoint(ctx,time){
  const c=this.level.checkpoint,x=c.x,y=c.y;
  if(x<this.camera-80||x>this.camera+W+80)return;
  ctx.fillStyle='#535c8b';roundedRect(ctx,x-4,GROUND-32,8,32,3,'#596a91');
  ctx.save();ctx.translate(x,y);
  ctx.shadowColor=this.checkpointHit?'#bdfdcf':'#9cf8ff';ctx.shadowBlur=20;
  ctx.fillStyle=this.checkpointHit?'#bdffd5':'#86e9ff';
  ctx.beginPath();ctx.moveTo(0,-20);ctx.lineTo(15,0);ctx.lineTo(0,20);ctx.lineTo(-15,0);ctx.closePath();ctx.fill();
  ctx.shadowBlur=0;ctx.fillStyle='#fff';ctx.globalAlpha=.5+.35*Math.sin(time*4);
  ctx.beginPath();ctx.moveTo(0,-13);ctx.lineTo(8,0);ctx.lineTo(0,13);ctx.closePath();ctx.fill();
  ctx.restore();ctx.globalAlpha=1;
 }

 drawEnemies(ctx,time){
  for(const e of this.enemies){
   if(!e.alive||Math.abs(e.x-this.camera)>W+80)continue;
   const flying=e.type==='drone';
   const bounce=Math.sin(time*6+e.phase)*2;
   ctx.save();ctx.translate(e.x,e.y+bounce);
   if(e.hitFlash>0){ctx.shadowColor='#fff';ctx.shadowBlur=22;}
   ctx.fillStyle='rgba(9,10,32,.22)';
   ctx.beginPath();ctx.ellipse(0,flying?57:25,22,4,0,0,Math.PI*2);ctx.fill();
   ctx.rotate(flying?Math.sin(time*2+e.phase)*.12:0);
   ctx.fillStyle=e.hitFlash>0?'#fff4e4':e.type==='turret'?'#615376':flying?'#677cbd':'#4c437c';
   roundedRect(ctx,-22,-18,44,39,11,ctx.fillStyle);
   ctx.fillStyle='#aaa0d9';roundedRect(ctx,-16,-12,32,20,6,'#827eb5');
   ctx.fillStyle='#ffc0cd';
   ctx.beginPath();ctx.ellipse(-9,-3,4,5,0,0,Math.PI*2);ctx.ellipse(9,-3,4,5,0,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#29213e';
   ctx.beginPath();ctx.arc(-8,-2,1.8,0,Math.PI*2);ctx.arc(10,-2,1.8,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#e6d0ff';
   if(flying){
    ctx.save();ctx.translate(-24,-3);ctx.rotate(time*10);ctx.fillRect(-11,-3,22,6);ctx.restore();
    ctx.save();ctx.translate(24,-3);ctx.rotate(-time*10);ctx.fillRect(-11,-3,22,6);ctx.restore();
   }else{
    ctx.fillRect(-19,15,12,10);ctx.fillRect(7,15,12,10);
   }
   if(e.type==='turret'){ctx.fillStyle='#faacb8';roundedRect(ctx,-6,-33,13,18,5,'#faacb8')}
   ctx.shadowBlur=0;ctx.restore();
  }
 }
 drawBoss(ctx,time){
  const b=this.boss;
  if(!b||b.dead||b.x+b.w<this.camera-100||b.x>this.camera+W+100)return;
  ctx.save();ctx.translate(b.x+b.w/2,b.y+b.h/2);
  const bounce=Math.sin(time*1.6)*5;
  ctx.translate(0,bounce);
  const grad=ctx.createLinearGradient(-45,-60,45,60);
  grad.addColorStop(0,b.hitFlash>0?'#fff6c3':'#7d77b7');
  grad.addColorStop(.55,b.hitFlash>0?'#ffe3d7':'#574f98');
  grad.addColorStop(1,'#382a6c');
  ctx.shadowColor=b.active?'#a78df9':'#665598';ctx.shadowBlur=b.active?30:9;
  roundedRect(ctx,-45,-55,90,110,20,grad);
  ctx.shadowBlur=0;
  ctx.fillStyle='#2a214a';roundedRect(ctx,-33,-38,66,49,16,'#292145');
  ctx.fillStyle=b.hitFlash>0?'#ffffff':'#ff99bd';
  ctx.beginPath();ctx.ellipse(-15,-13,9,7,0,0,Math.PI*2);ctx.ellipse(15,-13,9,7,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#261b3c';ctx.beginPath();ctx.arc(-14,-12,3,0,Math.PI*2);ctx.arc(16,-12,3,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#dbbeff';ctx.fillRect(-37,-69,13,22);ctx.fillRect(24,-69,13,22);
  ctx.strokeStyle='#c9aaff';ctx.lineWidth=4;ctx.beginPath();ctx.arc(0,28,16,0,Math.PI*2);ctx.stroke();
  ctx.fillStyle='#ffe2a3';starPath(ctx,0,28,9,4,time*.9);ctx.fill();
  ctx.fillStyle='#a5a0d2';
  roundedRect(ctx,-39,47,30,18,6,'#a5a0d2');roundedRect(ctx,9,47,30,18,6,'#a5a0d2');
  ctx.restore();
  if(b.active){
   const x=b.x-22,y=b.y-93;
   roundedRect(ctx,x,y,134,13,6,'#281d48');
   roundedRect(ctx,x+3,y+3,Math.max(0,(b.hp/b.maxHp)*128),7,4,'#ff91bd');
   ctx.fillStyle='#f8e2fe';ctx.textAlign='center';ctx.font='700 13px sans-serif';ctx.fillText(b.kind,b.x+b.w/2,y-7);
  }
 }
 drawProjectiles(ctx,time){
  for(const shot of this.shots){
   ctx.save();
   ctx.shadowBlur=shot.charged?23:16;ctx.shadowColor=shot.charged?'#ffe9a6':'#b0fff3';
   const gradient=ctx.createRadialGradient(shot.x,shot.y,0,shot.x,shot.y,shot.r*1.5);
   gradient.addColorStop(0,'#ffffff');gradient.addColorStop(.55,shot.charged?'#ffe58b':'#a2fff1');gradient.addColorStop(1,'#54d7eb55');
   ctx.fillStyle=gradient;ctx.beginPath();ctx.arc(shot.x,shot.y,shot.r,0,Math.PI*2);ctx.fill();
   ctx.strokeStyle=shot.charged?'#fff1bd8a':'#a4fff08a';ctx.lineWidth=shot.charged?5:3;
   ctx.beginPath();ctx.moveTo(shot.x,shot.y);ctx.lineTo(shot.x-(shot.vx>0?1:-1)*(shot.charged?44:25),shot.y);ctx.stroke();
   ctx.restore();
  }
  for(const shot of this.enemyShots){
   ctx.save();ctx.shadowBlur=12;ctx.shadowColor='#ff769d';
   ctx.fillStyle='#ff9ab6';ctx.beginPath();ctx.arc(shot.x,shot.y,shot.r,0,Math.PI*2);ctx.fill();ctx.restore();
  }
 }
 drawPortal(ctx,time){
  const {x,y}=this.level.portal;
  const locked=this.boss&&!this.boss.dead;
  ctx.save();ctx.translate(x+26,y+45);
  ctx.shadowBlur=26;ctx.shadowColor=locked?'#fb618c':'#ffdc84';
  ctx.strokeStyle=locked?'#fa769f':'#ffe3a0';ctx.lineWidth=9;
  ctx.beginPath();ctx.ellipse(0,0,25,43,0,0,Math.PI*2);ctx.stroke();
  ctx.shadowBlur=0;
  const grad=ctx.createLinearGradient(-18,-30,20,34);
  grad.addColorStop(0,'#a5f7ea');grad.addColorStop(.5,'#fff0ae');grad.addColorStop(1,'#f6aee8');
  ctx.fillStyle=locked?'#572346':grad;ctx.globalAlpha=locked?.78:(.68+.15*Math.sin(time*3));
  ctx.beginPath();ctx.ellipse(0,0,20,38,0,0,Math.PI*2);ctx.fill();
  ctx.globalAlpha=1;ctx.fillStyle='#fff';
  if(locked){ctx.font='bold 25px sans-serif';ctx.textAlign='center';ctx.fillText('✕',0,8)}
  else{starPath(ctx,0,0,10,5,time*.7);ctx.fill();}
  ctx.restore();
 }

 drawCat(ctx,p,time){
  if(!p)return;
  if(p.invuln>0&&Math.floor(p.invuln*14)%2===0)return;
  const motion=Math.sin(p.walk),running=Math.abs(p.vx)>5&&p.grounded;
  const bob=running?Math.sin(p.walk*2)*2:p.grounded?Math.sin(time*2)*.9:0;
  ctx.save();ctx.translate(Math.round(p.x+p.w/2),Math.round(p.y+bob));ctx.scale(p.facing,1);
  if(p.dash>0){
   ctx.globalAlpha=.32;ctx.fillStyle='#b6fff6';
   roundedRect(ctx,-47,5,30,38,15,'#b6fff6');
   ctx.globalAlpha=1;
  }
  // Sombras y botas de la protagonista; paso dinámico de carrera.
  ctx.fillStyle='rgba(12,8,30,.25)';ctx.beginPath();ctx.ellipse(0,p.h+1,24,5,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#19161f';
  const legA=running?motion*5:0,legB=running?-motion*5:0;
  roundedRect(ctx,-13+legA,40,11,18,3,'#25212c');
  roundedRect(ctx,3+legB,40,11,18,3,'#25212c');
  roundedRect(ctx,-16+legA,55,16,7,3,'#111015');
  roundedRect(ctx,2+legB,55,16,7,3,'#111015');
  // Cabello castaño largo y ondulado de la referencia.
  const hairMotion=Math.sin(time*7+(running?p.walk:0))*2;
  ctx.fillStyle='#543421';
  ctx.beginPath();ctx.moveTo(-20,17);ctx.bezierCurveTo(-29,24,-22,51,-25,56);
  ctx.bezierCurveTo(-15,59,-17,41,-11,42);
  ctx.lineTo(17,42);ctx.bezierCurveTo(21,55,28,58,28+hairMotion,52);
  ctx.bezierCurveTo(24,33,31,18,18,12);ctx.closePath();ctx.fill();
  ctx.strokeStyle='#946444';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(-20,19);ctx.quadraticCurveTo(-26,41,-19,52);
  ctx.moveTo(20,21);ctx.quadraticCurveTo(25,39,21+hairMotion,54);ctx.stroke();
  // Chaqueta negra, pequeño reflejo y guantes.
  const jacket=ctx.createLinearGradient(-17,25,20,45);
  jacket.addColorStop(0,'#14121e');jacket.addColorStop(1,'#36303e');
  roundedRect(ctx,-17,27,34,22,6,jacket);
  ctx.fillStyle='#514451';ctx.fillRect(-3,29,5,19);
  ctx.strokeStyle='#997c8c';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(-12,28);ctx.lineTo(-6,39);ctx.stroke();
  // Brazo y bláster Pulso Aurora.
  ctx.fillStyle='#2a202c';
  roundedRect(ctx,6,30,18,9,5,'#2a202c');
  roundedRect(ctx,18-p.recoil*20,28,23,11,5,'#7971a5');
  roundedRect(ctx,30-p.recoil*20,30,13,7,3,'#aaf7e6');
  ctx.fillStyle='#403458';ctx.fillRect(24,39,6,7);
  if(p.recoil>0){ctx.shadowBlur=14;ctx.shadowColor='#bffff5';ctx.fillStyle='#f8fff6';ctx.beginPath();ctx.arc(45,34,4,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0}
  // Rostro de tono miel inspirado en el personaje de referencia.
  ctx.fillStyle='#e0a96e';ctx.beginPath();ctx.ellipse(0,17,17,19,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#efbc81';ctx.beginPath();ctx.ellipse(-1,14,15,18,0,0,Math.PI*2);ctx.fill();
  // Mechones largos a ambos lados del rostro.
  ctx.fillStyle='#6d442c';ctx.beginPath();ctx.moveTo(-17,3);ctx.quadraticCurveTo(-23,22,-17,41);ctx.lineTo(-12,39);ctx.quadraticCurveTo(-16,26,-11,19);ctx.closePath();ctx.fill();
  ctx.beginPath();ctx.moveTo(16,5);ctx.quadraticCurveTo(24,22,21,42);ctx.lineTo(16,41);ctx.quadraticCurveTo(19,29,12,23);ctx.closePath();ctx.fill();
  // Ojos grandes, cejas y pestañas.
  ctx.strokeStyle='#3e291f';ctx.lineWidth=2.6;ctx.beginPath();ctx.moveTo(-12,10);ctx.lineTo(-5,8);ctx.moveTo(3,8);ctx.lineTo(12,10);ctx.stroke();
  ctx.fillStyle='#fcf4e9';ctx.beginPath();ctx.ellipse(-8,17,4.8,4.2,0,0,Math.PI*2);ctx.ellipse(8,17,4.8,4.2,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#281f24';ctx.beginPath();ctx.ellipse(-7,17,2.8,3.8,0,0,Math.PI*2);ctx.ellipse(9,17,2.8,3.8,0,0,Math.PI*2);ctx.fill();
  ctx.strokeStyle='#2c2324';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(-12,15);ctx.lineTo(-14,12);ctx.moveTo(12,15);ctx.lineTo(15,12);ctx.stroke();
  ctx.fillStyle='#a85b59';ctx.beginPath();ctx.ellipse(1,28,5.2,1.4,0,0,Math.PI*2);ctx.fill();
  // Sombrero negro de ala ancha como el de la imagen.
  const hat=ctx.createLinearGradient(0,-15,0,5);hat.addColorStop(0,'#1c1b1d');hat.addColorStop(1,'#303034');
  roundedRect(ctx,-20,-17,40,22,9,hat);
  ctx.fillStyle='#121214';ctx.beginPath();ctx.ellipse(0,2,31,7,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#4f4547';ctx.fillRect(-17,-1,34,3);
  ctx.strokeStyle='#645c61';ctx.lineWidth=1;ctx.beginPath();ctx.ellipse(0,2,30,6,0,Math.PI,Math.PI*2);ctx.stroke();
  // Anillo de energía al cargar el disparo.
  if(this.shootHeld>.13){
   ctx.globalAlpha=Math.min(.9,this.shootHeld/.68)*.75;
   ctx.strokeStyle=this.shootHeld>.68?'#ffe49b':'#abfff4';
   ctx.shadowColor=ctx.strokeStyle;ctx.shadowBlur=14;ctx.lineWidth=2.2;
   ctx.beginPath();ctx.arc(35,34,14+Math.sin(time*10)*2,0,Math.PI*2);ctx.stroke();
   ctx.globalAlpha=1;ctx.shadowBlur=0;
  }
  ctx.restore();
 }

}
document.addEventListener('DOMContentLoaded',()=>{
 try{window.catGame=new CatGame()}
 catch(error){
  console.error('No se pudo iniciar el juego',error);
  const errorBox=$('game-error');
  if(errorBox){errorBox.hidden=false;errorBox.textContent='El juego no pudo iniciar. Actualiza tu navegador y vuelve a intentarlo.'}
 }
});
})();
