/* Cat y las Estrellas Perdidas • mundos y aventuras originales */
(() => {
"use strict";
const chapters=[
 {
  "title": "El Bosque de los Circuitos Dormidos",
  "short": "Bosque",
  "subtitle": "Despierta la primera señal",
  "sky": [
   "#151c41",
   "#40537b",
   "#80a48e"
  ],
  "ground": "#27476a",
  "top": "#59d7b1",
  "accent": "#a1ffe5",
  "flora": "#8eeac0",
  "story": "Lunaria pierde sus estrellas y hasta los relojes se detienen. Cat, una joven inventora de sombrero negro y cabello castaño, descubre que alguien instaló cuatro máquinas para robar la energía de los recuerdos. Su madre dejó un dispositivo llamado Pulso Aurora: dispara luz y rompe los sellos de sombra. Cat sale al bosque a buscar la primera señal, sabiendo que la noche no se arregla sola.",
  "end": "Cat apaga el Centinela de Raíces y recupera el primer fragmento del mapa. Dentro de la máquina encuentra una voz grabada: «No es un robo. Es una señal de auxilio». Ahora sabe que alguien la espera en las alturas."
 },
 {
  "title": "Las Torres del Viento Quieto",
  "short": "Torres",
  "subtitle": "La ciudad suspendida no puede respirar",
  "sky": [
   "#283b79",
   "#7d8dc0",
   "#f3c7c8"
  ],
  "ground": "#5a588c",
  "top": "#b9b1ff",
  "accent": "#fff0b4",
  "flora": "#ead7ff",
  "story": "En las torres que flotan sobre Lunaria, el viento se congeló y cientos de molinos dejaron de girar. Cat conoce a Nimbo, una nube que protegía a los viajeros hasta que un autómata llamado Vigía Nacarado cerró sus rutas. Para avanzar tendrá que combinar saltos, disparos y una carrera contra la corriente.",
  "end": "El Vigía Nacarado cae y las hélices vuelven a girar. Nimbo cuenta que todas las máquinas reciben órdenes desde un lugar sellado bajo la montaña. Cat escucha un nombre: Lira, la guardiana que desapareció hace años."
 },
 {
  "title": "Las Minas de Cristal Silencioso",
  "short": "Minas",
  "subtitle": "Incluso el eco necesita ser escuchado",
  "sky": [
   "#101633",
   "#393b79",
   "#88609c"
  ],
  "ground": "#282951",
  "top": "#85a1fc",
  "accent": "#a6fff5",
  "flora": "#91cde8",
  "story": "Cat entra en las minas donde los cristales almacenan voces antiguas. Los guardianes mecánicos le disparan desde las pasarelas y el suelo se quiebra bajo sus botas. Allí descubre que Lira intentó salvar a Lunaria de una tormenta estelar, pero sus máquinas aprendieron a obedecer sus órdenes demasiado literalmente.",
  "end": "La Reina del Eco desactiva su última barrera. Cat escucha a Lira: «Si estás oyendo esto, significa que el Núcleo me atrapó. No destruyas la luz, libérala». El camino hacia la fortaleza por fin queda abierto."
 },
 {
  "title": "La Fortaleza del Último Amanecer",
  "short": "Fortaleza",
  "subtitle": "Un último pulso para encender el cielo",
  "sky": [
   "#261934",
   "#864259",
   "#ffc49a"
  ],
  "ground": "#503452",
  "top": "#ffbe77",
  "accent": "#ffe2a9",
  "flora": "#ffb7c0",
  "story": "La fortaleza se eleva sobre una ciudad sin amaneceres. El Núcleo de Medianoche controla a los robots y ha encerrado a Lira dentro de un reloj gigantesco. Cat comprende que la energía robada no puede recuperarse a golpes solamente: debe destruir los escudos, apagar los cuatro guardianes y llegar al corazón para liberar a Lira.",
  "end": "Cat dispara un último Pulso Aurora y rompe los anillos del Núcleo. Lira queda libre, las máquinas dejan de atacar y miles de estrellas regresan al cielo. Cat no salva Lunaria por ser invencible: la salva porque aprendió a avanzar incluso con miedo. Al amanecer, su madre le deja una nota: «Ahora escribe tú la próxima aventura»."
 }
];
const names=["La señal en la niebla","Engranajes entre árboles","El puente del centinela","Guardián del Bosque","El ascensor de nubes","Baterías en el aire","La estación del viento","Vigía Nacarado","Pasadizos de cuarzo","La galería de las sombras","El corazón de la mina","Reina del Eco","Las murallas del ocaso","El corredor sin tiempo","Asalto al Núcleo","El Último Amanecer"];
const tips=["Muévete con A/D. Espacio salta. J o K dispara el Pulso Aurora.","Dispara a los centinelas antes de cruzar los puentes.","Los drones también lanzan proyectiles: esquívalos con doble salto.","Derrota al jefe para abrir el portal.","Busca plataformas altas y usa dos saltos.","Destruye las torretas mientras avanzas.","Los enemigos resisten varios golpes en niveles avanzados.","Ataca y esquiva: el jefe tiene un patrón de disparo.","Los cristales azules guardan tu avance.","Usa el doble salto para pasar sobre los rayos.","Recoge corazones y busca tu estrella secreta.","Derrota a la Reina del Eco, incluso si cambia de dirección.","Tu pulso puede destruir obstáculos enemigos.","Calcula el disparo antes de entrar a las plataformas.","Usa los puntos de control antes del combate final.","El Núcleo necesita varios golpes. ¡No te rindas!"];
const WIDTH=960,HEIGHT=540,GROUND=474;
function makeLevel(index){
 const chapter=Math.floor(index/4),stage=index%4;
 const length=3000+index*60;
 const grounds=[{x:0,w:940},{x:1110,w:760},{x:2050,w:length-2050}];
 const base=[
  [280,382,148],[512,315,125],[740,372,138],[925,395,135],
  [1083,360,125],[1303,320,144],[1528,356,155],[1744,316,152],
  [1870,393,140],[2040,361,135],[2285,316,154],[2515,375,142]
 ];
 const platforms=base.map(([x,y,w],i)=>({
  x:x+Math.round(Math.sin(index*1.43+i*1.21)*16)+((i>5&&i<9)?stage*8:0),
  y:y+Math.round(Math.cos(index*1.67+i*.8)*13)-((stage===3&&i%4===1)?18:0),w,h:22
 }));
 // Un puente visible adicional sobre cada hueco del suelo.
 platforms.push({x:936,y:410,w:92,h:18},{x:1025,y:363,w:83,h:18},{x:1866,y:414,w:95,h:18},{x:1961,y:362,w:92,h:18});
 for(let x=2720;x<length-225;x+=210)platforms.push({x,y:325+Math.round(Math.sin(x/150+index)*25),w:122,h:22});
 const orbs=[];
 for(let x=160;x<length-180;x+=130)orbs.push({x,y:GROUND-56-((Math.floor(x/130)+index)%3)*15});
 for(const p of platforms)orbs.push({x:p.x+p.w/2,y:p.y-35});
 // Estrella especial que se puede conseguir saltando desde una plataforma.
 const starPlatform=platforms[6];
 const star={x:starPlatform.x+starPlatform.w/2,y:starPlatform.y-56};
 const checkpoint={x:1680,y:GROUND-66};
 const enemies=[
  {x:640+(stage*16),y:GROUND-29,range:58+stage*4,speed:1.0+index*.03,type:'crawler',hp:1+Math.floor(index/6)},
  {x:1280+chapter*20,y:GROUND-30,range:56+chapter*5,speed:1.2+index*.025,type:'turret',hp:2+chapter},
  {x:2270+stage*12,y:GROUND-29,range:67+stage*4,speed:1.0+index*.03,type:'crawler',hp:2+chapter}
 ];
 if(stage>0)enemies.push({x:2590,y:GROUND-30,range:40,speed:1.4+index*.02,type:'turret',hp:2+chapter});
 if(stage>1)enemies.push({x:1500,y:320,range:56,speed:1.65+index*.03,type:'drone',hp:2+chapter});
 const spikes=[
  {x:795+stage*10,y:GROUND-18,w:45,h:18},
  {x:1420+chapter*11,y:GROUND-18,w:48,h:18},
  {x:2380+stage*10,y:GROUND-18,w:45,h:18}
 ];
 if(stage>=2)spikes.push({x:2680,y:GROUND-18,w:45,h:18});
 const boss=stage===3?{x:length-435,y:GROUND-116,w:91,h:116,hp:12+chapter*5,kind:['Arbóreo','Nacarado','Eco','Núcleo'][chapter]}:null;
 const moving=stage===0?[]:[{x:1600,y:275,w:115,h:19,originY:275,amplitude:45+stage*8,speed:1.3+chapter*.16,phase:index},{x:2380,y:260,w:117,h:19,originY:260,amplitude:35+stage*8,speed:1.45,phase:index+2}];
 platforms.push(...moving);
 return {boss,moving,index,chapter,stage,name:names[index],tip:tips[index],theme:chapters[chapter],length,ground:grounds,platforms,orbs,star,checkpoint,enemies,spikes,hearts:stage%2===1?[{x:platforms[4].x+platforms[4].w/2,y:platforms[4].y-52}]:[],portal:{x:length-150,y:GROUND-92},skyObjects:8+index%4};
}
const levels=names.map((_,i)=>makeLevel(i));
window.CAT_DATA={chapters,names,levels,WIDTH,HEIGHT,GROUND,total:16};
})();
