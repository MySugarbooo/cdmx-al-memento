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
  this.player=null;this.held={left:false,right:false};this.jumpBuffer=0;
  this.camera=0;this.time=0;this.framePrev=0;this.score=0;this.coins=0;
  this.particles=[];this.orbs=[];this.enemies=[];this.hearts=[];this.starFound=false;this.checkpointHit=false;
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
    if(['arrowleft','arrowright','arrowup',' ','w','a','d'].includes(key)&&this.phase==='playing')event.preventDefault();
    if(key==='arrowleft'||key==='a')this.held.left=true;
    if(key==='arrowright'||key==='d')this.held.right=true;
    if((key===' '||key==='arrowup'||key==='w')&&!event.repeat){this.jumpBuffer=.16;if(this.phase==='playing')this.audio.init()}
    if(key==='p'||key==='escape'){event.preventDefault();if(!event.repeat)this.togglePause()}
    if(key==='m'&&!event.repeat)this.toggleMusic();
    if(key==='r'&&!event.repeat&&this.phase==='playing')this.chooseLevel(this.levelIndex,true);
  });
  window.addEventListener('keyup',event=>{
    const key=event.key.toLowerCase();
    if(key==='arrowleft'||key==='a')this.held.left=false;
    if(key==='arrowright'||key==='d')this.held.right=false;
  });
  window.addEventListener('blur',()=>{this.held.left=false;this.held.right=false;if(this.phase==='playing')this.pause()});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&this.phase==='playing')this.pause()});
  for(const control of document.querySelectorAll('[data-control]')){
    const kind=control.dataset.control;
    control.addEventListener('pointerdown',ev=>{
      ev.preventDefault();control.setPointerCapture?.(ev.pointerId);
      this.audio.init();
      if(kind==='jump')this.jumpBuffer=.19;else this.held[kind]=true;
      control.classList.add('is-held')
    });
    const release=()=>{if(kind!=='jump')this.held[kind]=false;control.classList.remove('is-held')};
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
    'Las estrellas de Lunaria han desaparecido. Cat, una chica valiente con una bufanda mágica, recorrerá cuatro mundos para devolver la luz al cielo.',
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
  this.coins=0;this.score=0;this.starFound=false;this.checkpointHit=false;this.jumpBuffer=0;
  this.health=3;this.flash=0;this.particles=[];
  this.orbs=this.level.orbs.map((orb,i)=>({...orb,hit:false,phase:i*.71}));
  this.enemies=this.level.enemies.map((enemy,i)=>({...enemy,alive:true,phase:i*.8}));
  this.hearts=this.level.hearts.map(item=>({...item,hit:false}));
  const resume=restore&&this.save.checkpoint?.level===index;
  this.checkpointHit=Boolean(resume);
  this.health=resume?Math.max(2,this.save.checkpoint.hearts):3;
  this.player={x:resume?this.level.checkpoint.x+30:72,y:GROUND-52,w:34,h:52,vx:0,vy:0,grounded:false,coyote:0,canDouble:true,facing:1,invuln:0,walk:0};
  $('level-name').textContent=(index+1)+' · '+this.level.name;
  $('game-message').textContent=this.level.tip;
  this.updateHud();
 }
 startLevel(index,forceFresh=false){
  this.setLevelScene(index,!forceFresh);
  if(forceFresh&&this.save.checkpoint?.level===index){this.save.checkpoint=null;persist(this.save)}
  this.phase='playing';this.hideOverlay();this.held.left=false;this.held.right=false;
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
    const detail=document.createElement('span');detail.className='level-detail';detail.textContent=locked?'Bloqueado':this.save.stars[index]?'★ Estrella conseguida':index<this.save.unlocked-1?'✓ Completado':'Disponible';
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
  this.phase='paused';this.held.left=false;this.held.right=false;
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
  $('pause-btn').disabled=true;this.held.left=false;this.held.right=false;
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
  p.y=GROUND-54;p.vx=0;p.vy=0;p.invuln=1.4;
 }
 step(dt){
  if(this.phase!=='playing')return;
  const p=this.player,l=this.level;
  this.time+=dt;this.audio.update(dt,l.chapter,true);
  p.invuln=Math.max(0,p.invuln-dt);this.flash=Math.max(0,this.flash-dt);
  this.jumpBuffer=Math.max(0,this.jumpBuffer-dt);
  const dir=Number(this.held.right)-Number(this.held.left);
  p.vx=dir*265;if(dir!==0)p.facing=dir;
  if(Math.abs(p.vx)>0)p.walk+=dt*11;
  p.coyote=p.grounded?.095:Math.max(0,p.coyote-dt);
  if(this.jumpBuffer>0&&(p.grounded||p.coyote>0||p.canDouble)){
   if(!p.grounded&&p.coyote<=0)p.canDouble=false;
   p.vy=p.grounded||p.coyote>0?-615:-565;
   p.grounded=false;p.coyote=0;this.jumpBuffer=0;
   this.audio.sfx('jump');this.burst(p.x+p.w/2,p.y+p.h-2,'#c7f6e3',5);
  }
  const previousBottom=p.y+p.h;
  p.x=clamp(p.x+p.vx*dt,1,l.length-p.w-2);
  p.vy=Math.min(1100,p.vy+1650*dt);
  p.y+=p.vy*dt;
  p.grounded=false;
  if(p.vy>=0){
   const candidates=l.ground.map(g=>({x:g.x,y:GROUND,w:g.w,h:70})).concat(l.platforms);
   let landing=null;
   for(const plat of candidates){
    if(p.x+p.w>plat.x+5&&p.x<plat.x+plat.w-5&&previousBottom<=plat.y+7&&p.y+p.h>=plat.y){
     if(!landing||plat.y<landing.y)landing=plat;
    }
   }
   if(landing){p.y=landing.y-p.h;p.vy=0;p.grounded=true;p.canDouble=true;}
  }
  if(p.y>H+140){this.respawn();return}
  const touch={x:p.x+4,y:p.y+5,w:p.w-8,h:p.h-6};
  for(const orb of this.orbs){
   if(orb.hit)continue;
   if(Math.abs(touch.x-orb.x)<26&&Math.abs(touch.y-orb.y)<41){
    orb.hit=true;this.coins++;this.score+=10;this.audio.sfx('coin');
    this.burst(orb.x,orb.y,'#ffec98',7);
   }
  }
  const st=l.star;
  if(!this.starFound&&Math.abs(p.x+p.w/2-st.x)<27&&Math.abs(p.y+p.h/2-st.y)<38){
   this.starFound=true;this.score+=100;this.audio.sfx('star');
   $('game-message').textContent='¡Encontraste la estrella especial! Llega al portal para guardarla.';
   this.burst(st.x,st.y,'#fff6a0',30);
  }
  for(const heart of this.hearts){
   if(heart.hit||this.health>=3)continue;
   if(Math.abs(p.x+p.w/2-heart.x)<26&&Math.abs(p.y+p.h/2-heart.y)<32){
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
   enemy.x=l.enemies[this.enemies.indexOf(enemy)].x+Math.sin(this.time*enemy.speed+enemy.phase)*enemy.range;
   const area={x:enemy.x-19,y:enemy.y-9,w:38,h:35};
   if(!overlap(touch,area))continue;
   if(p.vy>50&&previousBottom<=area.y+13){
    enemy.alive=false;p.vy=-390;p.canDouble=true;
    this.score+=30;this.audio.sfx('bounce');this.burst(enemy.x,enemy.y,'#a5b0ff',13);
   }else this.hurt(enemy.x);
  }
  if(p.x>l.portal.x-17&&p.x<l.portal.x+62&&p.y+p.h>l.portal.y+20)this.finishLevel();
  this.camera+=(clamp(p.x-320,0,l.length-W)-this.camera)*Math.min(1,dt*5.8);
  this.updateHud();
  for(const particle of this.particles){
   particle.life-=dt;particle.x+=particle.vx*dt;particle.y+=particle.vy*dt;particle.vy+=180*dt;
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
   if(!e.alive||Math.abs(e.x-this.camera)>W+75)continue;
   const bob=Math.sin(time*6+e.phase)*2;
   ctx.save();ctx.translate(e.x,e.y+bob);
   ctx.fillStyle='rgba(11,12,48,.35)';ctx.beginPath();ctx.ellipse(0,22,25,5,0,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#403b84';ctx.beginPath();ctx.ellipse(0,3,22,19,0,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#5654a7';ctx.beginPath();ctx.arc(-9,-11,10,0,Math.PI*2);ctx.arc(9,-11,10,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#fff1f2';ctx.beginPath();ctx.arc(-7,2,5,0,Math.PI*2);ctx.arc(7,2,5,0,Math.PI*2);ctx.fill();
   ctx.fillStyle='#2a204f';ctx.beginPath();ctx.arc(-5,2,2,0,Math.PI*2);ctx.arc(9,2,2,0,Math.PI*2);ctx.fill();
   ctx.restore();
  }
 }
 drawPortal(ctx,time){
  const {x,y}=this.level.portal;
  ctx.save();ctx.translate(x+26,y+45);
  ctx.shadowBlur=26;ctx.shadowColor='#ffdc84';
  ctx.strokeStyle='#ffe3a0';ctx.lineWidth=9;
  ctx.beginPath();ctx.ellipse(0,0,25,43,0,0,Math.PI*2);ctx.stroke();
  ctx.shadowBlur=0;
  const grad=ctx.createLinearGradient(-18,-30,20,34);
  grad.addColorStop(0,'#a5f7ea');grad.addColorStop(.5,'#fff0ae');grad.addColorStop(1,'#f6aee8');
  ctx.fillStyle=grad;ctx.globalAlpha=.68+.15*Math.sin(time*3);
  ctx.beginPath();ctx.ellipse(0,0,20,38,0,0,Math.PI*2);ctx.fill();
  ctx.globalAlpha=1;ctx.fillStyle='#fff';
  starPath(ctx,0,0,10,5,time*.7);ctx.fill();
  ctx.restore();
 }
 drawCat(ctx,p,time){
  if(!p)return;
  if(p.invuln>0&&Math.floor(p.invuln*11)%2===0)return;
  const bob=p.grounded?Math.sin(p.walk)*2:0;
  ctx.save();ctx.translate(Math.round(p.x+p.w/2),Math.round(p.y+bob));ctx.scale(p.facing,1);
  ctx.fillStyle='rgba(16,13,39,.3)';ctx.beginPath();ctx.ellipse(0,p.h+1,17,4,0,0,Math.PI*2);ctx.fill();
  // Botas y leggings
  ctx.fillStyle='#292450';roundedRect(ctx,-12,36,10,13,3,'#292450');roundedRect(ctx,3,36,10,13,3,'#292450');
  ctx.fillStyle='#ffa6ad';roundedRect(ctx,-14,45,15,7,3,'#ffa6ad');roundedRect(ctx,3,45,16,7,3,'#ffa6ad');
  // Mochila y chaqueta
  roundedRect(ctx,-17,18,33,25,10,'#eaa36c');
  roundedRect(ctx,-16,17,30,25,9,'#fecb7a');
  ctx.fillStyle='#ff7a91';ctx.fillRect(-17,22,35,7);
  // Pañuelo mágico flota
  ctx.fillStyle='#fa669e';ctx.beginPath();ctx.moveTo(7,15);ctx.quadraticCurveTo(22,14+Math.sin(time*7)*4,30,22);ctx.lineTo(16,24);ctx.closePath();ctx.fill();
  // Cabello
  ctx.fillStyle='#342955';ctx.beginPath();ctx.ellipse(0,12,18,20,0,0,Math.PI*2);ctx.fill();
  // Orejas del gorrito violeta: su nombre es Cat
  ctx.fillStyle='#8c61d1';ctx.beginPath();ctx.moveTo(-14,7);ctx.lineTo(-16,-12);ctx.lineTo(-4,0);ctx.moveTo(7,0);ctx.lineTo(16,-12);ctx.lineTo(15,8);ctx.fill();
  ctx.fillStyle='#d3a0ea';ctx.beginPath();ctx.moveTo(-13,-2);ctx.lineTo(-13,-8);ctx.lineTo(-8,1);ctx.moveTo(11,0);ctx.lineTo(14,-7);ctx.lineTo(13,4);ctx.fill();
  // Rostro
  ctx.fillStyle='#ffe0bf';ctx.beginPath();ctx.ellipse(0,10,13.5,15,0,0,Math.PI*2);ctx.fill();
  // Flequillo y ojos
  ctx.fillStyle='#3d2958';ctx.beginPath();ctx.moveTo(-13,7);ctx.quadraticCurveTo(-3,-9,12,3);ctx.lineTo(13,9);ctx.quadraticCurveTo(5,0,-2,4);ctx.closePath();ctx.fill();
  ctx.fillStyle='#332653';ctx.beginPath();ctx.ellipse(-5,12,1.5,2.1,0,0,Math.PI*2);ctx.ellipse(6,12,1.5,2.1,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#ee8b95';ctx.beginPath();ctx.arc(-10,17,3.2,0,Math.PI*2);ctx.arc(11,17,3.2,0,Math.PI*2);ctx.fill();
  ctx.strokeStyle='#9e5372';ctx.lineWidth=1.1;ctx.beginPath();ctx.arc(1,17,2,0,Math.PI);ctx.stroke();
  ctx.fillStyle='#fff6bb';starPath(ctx,10,-2,5,2.5);ctx.fill();
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
