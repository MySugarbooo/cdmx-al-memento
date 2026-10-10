/* UMBRAL 9 • raycasting 2.5D, sprites originales y arma en primera persona */
(function(){
'use strict';
const TAU=Math.PI*2,clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const W=960,H=540,FOV=1.18,FOCAL=W/(2*Math.tan(FOV/2));
function col(v){return v}
function canvas(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c}
function rect(ctx,x,y,w,h,fill,r=0){ctx.fillStyle=fill;if(r){ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill()}else ctx.fillRect(x,y,w,h)}
function glow(ctx,x,y,r,color){const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,color);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2)}
function seedRand(s){return()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296}}
function makeWall(theme,kind){
 const c=canvas(128,128),x=c.getContext('2d'),rand=seedRand(kind*71+17);
 const g=x.createLinearGradient(0,0,128,128);g.addColorStop(0,theme.wall);g.addColorStop(1,'#111827');
 rect(x,0,0,128,128,g);
 if(kind===3){rect(x,0,0,128,128,'#232235');rect(x,4,5,120,118,theme.wall);for(let y=13;y<128;y+=21)rect(x,12,y,104,5,'#12222e')}
 if(kind===4){rect(x,0,0,128,128,'#0e1622');for(let i=0;i<6;i++)rect(x,15+i*17,0,7,128,theme.trim);rect(x,0,58,128,11,'#151c28');}
 for(let i=0;i<180;i++){const v=rand(),xx=rand()*128,yy=rand()*128;rect(x,xx,yy,1+v*12,1+v*9,v>.6?'#ffffff0a':'#00000015')}
 rect(x,0,0,128,7,'#d9eaff20');rect(x,0,120,128,8,'#070e1a70');
 rect(x,0,0,5,128,'#09101a77');rect(x,123,0,5,128,'#09101a77');
 x.strokeStyle='#ffffff1b';x.lineWidth=2;for(const y of [9,58,111]){x.beginPath();x.moveTo(8,y);x.lineTo(120,y);x.stroke()}
 for(const [xx,yy] of [[14,14],[112,14],[14,114],[112,114]]){
  x.fillStyle='#a5bac7';x.beginPath();x.arc(xx,yy,3.2,0,TAU);x.fill();x.fillStyle='#121b26';x.beginPath();x.arc(xx,yy,1.5,0,TAU);x.fill();
 }
 if(kind===2){
  rect(x,24,31,80,59,'#0b1724',7);rect(x,30,37,68,48,'#102c36',5);
  for(let i=0;i<5;i++){rect(x,40,45+i*8,20+rand()*38,3,theme.trim)}
  x.fillStyle=theme.trim;x.font='12px monospace';x.fillText('09',86,109);
 }else{
  rect(x,8,25,112,5,'#121b28a8');
  if(kind===1){rect(x,50,20,28,4,theme.trim);rect(x,50,99,28,4,theme.trim)}
 }
 return c;
}
function makeSprite(kind){
 const c=canvas(152,192),x=c.getContext('2d');
 if(['memory','medkit','ammo','exit'].includes(kind)){
  if(kind==='memory'){
   glow(x,76,91,76,'#6cf8ef40');x.save();x.translate(76,95);x.shadowColor='#9dfff7';x.shadowBlur=24;x.fillStyle='#59efff';x.beginPath();x.moveTo(0,-58);x.lineTo(40,-3);x.lineTo(0,55);x.lineTo(-40,-3);x.closePath();x.fill();x.shadowBlur=0;
   x.fillStyle='#b9ffff';x.beginPath();x.moveTo(0,-43);x.lineTo(26,-3);x.lineTo(0,38);x.closePath();x.fill();x.strokeStyle='#e7ffff';x.lineWidth=2;x.strokeRect(-10,-11,20,20);x.restore();
   x.fillStyle='#d5fffa';x.font='bold 13px monospace';x.textAlign='center';x.fillText('REGISTRO',76,164);
  }else if(kind==='medkit'){
   glow(x,76,99,70,'#8bffb43e');rect(x,36,42,80,96,'#d8fff1',13);rect(x,43,50,66,77,'#297a65',8);rect(x,66,61,21,54,'#d8fff1',4);rect(x,51,78,51,21,'#d8fff1',4);rect(x,46,134,61,8,'#182d31',3);
  }else if(kind==='ammo'){
   glow(x,76,99,68,'#ffce7844');rect(x,37,44,78,91,'#394654',13);rect(x,45,52,62,68,'#b6a876',8);rect(x,56,35,40,21,'#d9c99a',7);rect(x,47,81,58,13,'#262736');
   for(let i=0;i<4;i++)rect(x,56+i*11,99,7,13,'#fff1be',2);
  }else{
   glow(x,76,93,77,'#88fbf83d');x.strokeStyle='#88f8ea';x.lineWidth=12;x.shadowBlur=23;x.shadowColor='#6dfbea';x.beginPath();x.ellipse(76,90,39,72,0,0,TAU);x.stroke();
   x.shadowBlur=0;x.strokeStyle='#dff';x.lineWidth=3;x.beginPath();x.ellipse(76,90,31,64,0,0,TAU);x.stroke();
   const gr=x.createLinearGradient(38,25,111,148);gr.addColorStop(0,'#92fbf080');gr.addColorStop(1,'#c7a4ff85');x.fillStyle=gr;x.beginPath();x.ellipse(76,90,25,56,0,0,TAU);x.fill();
   x.fillStyle='#fff';x.font='bold 21px monospace';x.textAlign='center';x.fillText('↥',76,99);
  }
  return c;
 }
 const boss=(kind==='matriarch'||kind==='herald'),brute=kind==='brute',seer=kind==='seer';
 const glowcolor=kind==='herald'?'#f979bd':kind==='matriarch'?'#ff7d99':seer?'#67f5fe':'#b59bff';
 glow(x,76,112,85,glowcolor+'20');
 x.save();x.translate(76,98);
 if(boss){
  x.fillStyle=kind==='herald'?'#3b2647':'#453350';
  for(let i=0;i<9;i++){
   x.save();x.rotate(i*TAU/9);x.beginPath();x.moveTo(0,-24);x.quadraticCurveTo(55,-91,8,-102);x.quadraticCurveTo(-8,-52,0,-24);x.fill();x.restore();
  }
 }
 // Patas y apéndices orgánicos.
 const limb=brute?'#5a344d':seer?'#244c6d':boss?'#513450':'#423854';
 x.strokeStyle=limb;x.lineCap='round';x.lineWidth=boss?16:brute?14:9;
 for(const side of [-1,1]){
  for(let i=0;i<3;i++){
   x.beginPath();x.moveTo(side*(19+i*4),23+i*7);x.quadraticCurveTo(side*(38+i*12),54+i*4,side*(29+i*19),85+i*4);x.stroke();
   x.fillStyle=glowcolor;x.beginPath();x.arc(side*(29+i*19),85+i*4,boss?5:3,0,TAU);x.fill();
  }
 }
 const g=x.createRadialGradient(-21,-37,4,0,4,boss?91:71);
 g.addColorStop(0,kind==='herald'?'#91618b':seer?'#6891ae':brute?'#ad6d75':'#8c80b0');
 g.addColorStop(1,boss?'#281b38':'#261f38');
 x.fillStyle=g;x.beginPath();x.ellipse(0,boss?5:13,boss?57:brute?50:37,boss?75:brute?63:53,0,0,TAU);x.fill();
 // Articulaciones y hendiduras luminosas.
 x.strokeStyle=glowcolor;x.lineWidth=2;x.shadowColor=glowcolor;x.shadowBlur=15;
 for(const side of [-1,1]){x.beginPath();x.moveTo(side*14,1);x.quadraticCurveTo(side*27,29,side*25,52);x.stroke();}
 x.shadowBlur=0;
 x.fillStyle=boss?'#160f20':'#171a2b';x.beginPath();x.ellipse(0,-25,boss?40:29,boss?39:31,0,0,TAU);x.fill();
 // Ojos asimétricos, nada de sangre ni gore.
 for(let i=0;i<(seer?3:boss?5:2);i++){
  const count=seer?3:boss?5:2,xx=(i-(count-1)/2)*(boss?14:18),yy=-30+(i%2)*4;
  x.shadowColor=glowcolor;x.shadowBlur=15;x.fillStyle=glowcolor;
  x.beginPath();x.ellipse(xx,yy,boss?6:7,boss?8:9,0,0,TAU);x.fill();
  x.shadowBlur=0;x.fillStyle='#0c111c';x.beginPath();x.ellipse(xx+1,yy,2,4,0,0,TAU);x.fill();
 }
 x.strokeStyle='#211827';x.lineWidth=5;x.beginPath();x.arc(0,-1,boss?20:16,.1,Math.PI-.1);x.stroke();
 for(let i=-2;i<=2;i++){x.fillStyle='#d8c6ec';x.beginPath();x.moveTo(i*7-2,9);x.lineTo(i*7+3,9);x.lineTo(i*7,19);x.fill();}
 x.restore();
 return c;
}
class Renderer{
 constructor(canvasElement){this.canvas=canvasElement;this.ctx=canvasElement.getContext('2d',{alpha:false});this.ctx.imageSmoothingEnabled=true;this.world=null;this.wallTextures=[];this.sprites={};this.depth=new Float32Array(W/2);this.hitCache=[];this.lastWidth=W;this.lastHeight=H;
  for(const type of ['stalker','seer','brute','matriarch','herald','memory','medkit','ammo','exit'])this.sprites[type]=makeSprite(type);
 }
 load(level){this.world=level;this.wallTextures=[null,makeWall(level.palette,1),makeWall(level.palette,2),makeWall(level.palette,3),makeWall(level.palette,4)];}
 cast(x,y,dx,dy,max=28){
  const map=this.world.map,M=this.world.width,N=this.world.height;
  let mx=Math.floor(x),my=Math.floor(y),sdx=Math.abs(1/(dx||1e-9)),sdy=Math.abs(1/(dy||1e-9));
  const stepX=dx<0?-1:1,stepY=dy<0?-1:1;
  let sideX=(dx<0?x-mx:mx+1-x)*sdx,sideY=(dy<0?y-my:my+1-y)*sdy;
  let side=0,tile=1,dist=0;
  for(let i=0;i<65;i++){
   if(sideX<sideY){dist=sideX;sideX+=sdx;mx+=stepX;side=0}
   else{dist=sideY;sideY+=sdy;my+=stepY;side=1}
   if(mx<0||my<0||mx>=M||my>=N){tile=1;break}
   tile=map[my][mx];if(tile!==0)break;if(dist>max)break;
  }
  const wx=side===0?y+dist*dy:x+dist*dx;
  let tex=wx-Math.floor(wx);
  if((side===0&&dx>0)||(side===1&&dy<0))tex=1-tex;
  return {dist:Math.max(.04,dist),tile:tile||1,side,tex};
 }
 visible(x,y,z){
  const angle=Math.atan2(y-z.y,x-z.x),delta=Math.atan2(Math.sin(angle-z.a),Math.cos(angle-z.a));
  return Math.abs(delta)<FOV*.7;
 }
 draw(game,time){
  const ctx=this.ctx,level=this.world,player=game.player;if(!level||!player)return;
  const palette=level.palette;
  const horizon=clamp(H*.48+game.pitch,110,415),bob=game.stepBob||0;
  ctx.clearRect(0,0,W,H);
  const ceiling=ctx.createLinearGradient(0,0,0,horizon);
  ceiling.addColorStop(0,palette.top);ceiling.addColorStop(1,palette.bottom);
  rect(ctx,0,0,W,horizon,ceiling);
  const floor=ctx.createLinearGradient(0,horizon,0,H);floor.addColorStop(0,palette.floor);floor.addColorStop(1,'#030a13');
  rect(ctx,0,horizon,W,H-horizon,floor);
  // Luces del techo y líneas de perspectiva.
  const flicker=.75+Math.sin(time*8+level.stage)*.1;
  for(let i=0;i<8;i++){
   const x=((i*206+Math.sin(level.stage+i)*100-(player.x*17))%(W+220)+W+220)%(W+220)-110;
   rect(ctx,x,55+(i%3)*13,85,2,level.palette.trim+'25');
  }
  ctx.lineWidth=1;
  for(let i=1;i<=12;i++){
   const depth=i*i*1.14,py=horizon+(H-horizon)*(depth/(depth+6));
   ctx.globalAlpha=.08+((i%3===0)?0.04:0);ctx.strokeStyle=palette.trim;
   ctx.beginPath();ctx.moveTo(0,py);ctx.lineTo(W,py);ctx.stroke();
  }
  ctx.globalAlpha=1;
  // Rayos de pared en columnas de 2 píxeles (480 rayos para 960px horizontales).
  const rayW=2;
  for(let column=0;column<W/rayW;column++){
   const screen=column*rayW+rayW/2;
   const relative=(screen-W/2)/FOCAL;
   const a=player.a+Math.atan(relative),dx=Math.cos(a),dy=Math.sin(a);
   const hit=this.cast(player.x,player.y,dx,dy);
   const dist=Math.max(.12,hit.dist*Math.cos(a-player.a));this.depth[column]=dist;
   const height=FOCAL/dist,top=horizon-height*.52+bob;
   const idx=clamp(Math.floor(hit.tex*127),0,127);
   const tex=this.wallTextures[hit.tile]||this.wallTextures[1];
   ctx.drawImage(tex,idx,0,1,128,column*rayW,top,rayW+1,height);
   // Penumbra por distancia, paredes laterales y profundidad del escenario.
   const darkness=clamp(dist/28+(hit.side?.15:0),.07,.83);
   ctx.fillStyle=`rgba(1,5,14,${darkness})`;ctx.fillRect(column*rayW,top,rayW+1,height);
   if(hit.tile===4&&dist<9){ctx.fillStyle=palette.trim;ctx.globalAlpha=.07+.04*Math.sin(time*3+column*.06);ctx.fillRect(column*rayW,top,rayW+1,height);ctx.globalAlpha=1}
  }
  const sprites=[];
  for(const entity of game.enemies)if(entity.hp>0&&entity.alive!==false)sprites.push({type:entity.kind,x:entity.x,y:entity.y,scale:entity.kind==='matriarch'||entity.kind==='herald'?2.25:entity.kind==='brute'?1.37:1,entity,flash:entity.flash||0});
  for(const item of game.items)if(!item.taken)sprites.push({type:item.type,x:item.x,y:item.y,scale:item.type==='exit'?1.7:.73,entity:item});
  sprites.push({type:'exit',x:level.exit.x,y:level.exit.y,scale:1.6});
  sprites.sort((a,b)=>((b.x-player.x)**2+(b.y-player.y)**2)-((a.x-player.x)**2+(a.y-player.y)**2));
  for(const sprite of sprites){
   const dx=sprite.x-player.x,dy=sprite.y-player.y,distance=Math.hypot(dx,dy);
   let angle=Math.atan2(dy,dx)-player.a;angle=Math.atan2(Math.sin(angle),Math.cos(angle));
   const z=distance*Math.cos(angle);
   if(z<=.15||Math.abs(angle)>FOV*.8)continue;
   const sx=W/2+Math.tan(angle)*FOCAL;
   const actualHeight=FOCAL/z*sprite.scale;
   const actualWidth=actualHeight*(sprite.type==='exit'?.55:.73);
   const spriteCanvas=this.sprites[sprite.type]||this.sprites.stalker;
   const bottom=horizon+Math.min(H,FOCAL/z)*.50+bob;
   const visualY=bottom-actualHeight+(sprite.entity?.bob||0)*actualHeight*.13;
   const start=Math.max(0,Math.floor((sx-actualWidth/2)/rayW));
   const end=Math.min(W/rayW-1,Math.ceil((sx+actualWidth/2)/rayW));
   ctx.globalAlpha=clamp(1-(distance-12)/20,.15,1);
   for(let col=start;col<=end;col++){
    if(this.depth[col]<z-.13)continue;
    const pixelX=col*rayW,portion=(pixelX-(sx-actualWidth/2))/actualWidth;
    if(portion<0||portion>1)continue;
    ctx.drawImage(spriteCanvas,Math.min(151,Math.max(0,Math.floor(portion*152))),0,1,192,pixelX,visualY,rayW+1,actualHeight);
   }
   ctx.globalAlpha=1;
   if(sprite.entity?.flash>0){
    const g=ctx.createRadialGradient(sx,visualY+actualHeight*.40,0,sx,visualY+actualHeight*.4,actualHeight*.6);
    g.addColorStop(0,'#ffffff50');g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.fillRect(sx-actualWidth*.6,visualY,actualWidth*1.2,actualHeight);
   }
   if(sprite.entity?.isBoss&&distance<13){
    rect(ctx,sx-actualWidth*.34,visualY-15,actualWidth*.68,6,'#1e172b',3);
    rect(ctx,sx-actualWidth*.34,visualY-15,actualWidth*.68*clamp(sprite.entity.hp/sprite.entity.maxHp,0,1),6,'#ff748e',3);
   }
  }
  // Velo ligero y partículas de polvo suspendidas.
  ctx.save();ctx.globalAlpha=.38;for(let i=0;i<23;i++){
   let px=((i*193.5+Math.sin(i*4)*30+time*(i%2?5:-5))%W+W)%W,py=(i*83.6+Math.sin(time*.5+i)*20)%H;
   ctx.fillStyle=i%4?'#99c7d1':'#e2a6dc';ctx.fillRect(px,py,(i%3)+1,(i%3)+1);
  }ctx.restore();
  if(game.effects.damage>0){rect(ctx,0,0,W,H,`rgba(235,40,70,${game.effects.damage*.28})`)}
  if(game.effects.pulse>0){rect(ctx,0,0,W,H,`rgba(113,251,235,${game.effects.pulse*.12})`)}
  this.drawWeapon(game,time);
  this.drawCrosshair(game,time);
 }
 drawCrosshair(game,time){
  const c=this.ctx,cx=W/2,cy=H/2+game.pitch*.18,spread=(game.effects.recoil||0)*11+(game.moving?3:0),color=game.aimOnEnemy?'#ffb6b4':'#b6fff5';
  c.save();c.strokeStyle='#020e1799';c.lineWidth=5;c.beginPath();
  for(const s of [-1,1]){c.moveTo(cx+s*(13+spread),cy);c.lineTo(cx+s*(23+spread),cy);c.moveTo(cx,cy+s*(13+spread));c.lineTo(cx,cy+s*(23+spread))}c.stroke();
  c.strokeStyle=color;c.lineWidth=2.3;c.beginPath();for(const s of [-1,1]){c.moveTo(cx+s*(13+spread),cy);c.lineTo(cx+s*(23+spread),cy);c.moveTo(cx,cy+s*(13+spread));c.lineTo(cx,cy+s*(23+spread))}c.stroke();
  c.fillStyle='#e5fff8';c.beginPath();c.arc(cx,cy,2.6,0,TAU);c.fill();c.restore();
 }
 drawWeapon(game,time){
  const c=this.ctx,weapon=game.weapons[game.weaponIndex],rec=game.effects.recoil||0,walking=game.moving?Math.sin(time*10)*4:Math.sin(time*2)*1.8;
  const ox=W*.51+walking,oy=H+rec*24+Math.cos(time*10)*(game.moving?4:0);
  c.save();c.translate(ox,oy);
  // Guantes y brazo en primera persona.
  const arm=c.createLinearGradient(-80,-145,150,5);arm.addColorStop(0,'#263746');arm.addColorStop(.5,'#3c4d5e');arm.addColorStop(1,'#142330');
  c.fillStyle=arm;c.beginPath();c.moveTo(-118,32);c.lineTo(-60,-138);c.lineTo(2,-178);c.lineTo(45,20);c.closePath();c.fill();
  c.fillStyle='#182a39';c.beginPath();c.moveTo(81,35);c.lineTo(44,-136);c.lineTo(126,-161);c.lineTo(230,33);c.closePath();c.fill();
  const metal=c.createLinearGradient(-95,-245,110,-80);metal.addColorStop(0,'#647989');metal.addColorStop(.35,'#2d4256');metal.addColorStop(.73,'#131e2d');metal.addColorStop(1,'#748998');
  c.fillStyle=metal;c.beginPath();c.moveTo(-91,8);c.lineTo(-72,-146);c.lineTo(-38,-224);c.lineTo(32,-237);c.lineTo(77,-173);c.lineTo(99,12);c.closePath();c.fill();
  rect(c,-57,-225,75,21,'#0b1928',5);rect(c,-39,-240,38,17,'#6da49f',4);rect(c,-35,-230,28,5,'#c9fff3');
  // Cañón luminoso.
  rect(c,-22,-301,42,106,'#0a1725',7);rect(c,-14,-300,25,100,'#314858',7);rect(c,-8,-297,14,91,'#6dcfca',5);
  c.shadowBlur=11;c.shadowColor='#b5fcf2';rect(c,-3,-306,6,19,'#c7ffff',3);c.shadowBlur=0;
  rect(c,16,-210,46,16,'#3a5365',3);rect(c,49,-198,24,54,'#1b2a39',5);
  rect(c,-70,-176,42,16,'#4f6875',4);rect(c,-62,-164,25,38,'#0f202e',5);
  c.fillStyle='#c9efe7';c.font='bold 11px monospace';c.fillText(weapon.short||'P9',-41,-85);
  rect(c,-27,-145,52,8,'#79e0d4',3);
  c.globalAlpha=.28;glow(c,-2,-296,72,'#93ffee');c.globalAlpha=1;
  if(game.effects.muzzle>0){
   const fire=game.effects.muzzle;
   c.shadowBlur=35*fire;c.shadowColor='#d8fff5';
   c.fillStyle='#eaffef';c.beginPath();c.moveTo(-3,-296);c.lineTo(-45,-338-fire*30);c.lineTo(-4,-362-fire*40);c.lineTo(35,-330-fire*30);c.closePath();c.fill();
   c.fillStyle='#8affdf';c.beginPath();c.moveTo(-3,-298);c.lineTo(-14,-342-fire*12);c.lineTo(11,-337-fire*13);c.closePath();c.fill();
   c.shadowBlur=0;
  }
  c.restore();
 }
}
window.UMBRAL_RENDER=Renderer;
})();
