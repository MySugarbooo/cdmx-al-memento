/* Cat y las Estrellas Perdidas • mundos y aventuras originales */
(() => {
"use strict";
const chapters=[
 {title:"Bosque de los Farolitos",short:"Bosque",subtitle:"Donde la noche guarda secretos",sky:["#171d52","#624892","#fdaf83"],ground:"#27476a",top:"#52ceab",accent:"#85fbe4",flora:"#80cfb3",story:"Cat vivía en Lunaria, un pueblo donde cada noche las estrellas bajaban a jugar. Una mañana, el cielo amaneció vacío. Su abuela le entregó una bufanda luminosa y le susurró: «La primera chispa duerme en el bosque».",end:"La primera constelación vuelve a brillar. Una luciérnaga habla de una torre sobre las nubes, donde el viento colecciona canciones."},
 {title:"Islas sobre las Nubes",short:"Nubes",subtitle:"Saltos altos, sueños gigantes",sky:["#265aa0","#8c83df","#f6bddf"],ground:"#6660a8",top:"#b4a2ff",accent:"#fff3ae",flora:"#f4d8ff",story:"Siguiendo el brillo del bosque, Cat llegó a unas islas flotantes. Allí conoció a Nimbo, una nube diminuta que había olvidado cómo llover. «Si recuerdas mi canción, te mostraré el camino», dijo.",end:"Nimbo vuelve a cantar y las islas dejan de temblar. En la distancia, un eco responde desde el interior de la montaña."},
 {title:"Cuevas del Eco Azul",short:"Cuevas",subtitle:"El valor también puede iluminar",sky:["#0e143d","#2a2d75","#7a4f9d"],ground:"#252757",top:"#7b87ed",accent:"#8af7f7",flora:"#85bfea",story:"El eco de la montaña repetía el mayor miedo de Cat: «Eres demasiado pequeña». Ella apretó su bufanda y respondió: «Soy lo bastante valiente para dar el siguiente paso».",end:"Los cristales recuperan su voz. Queda una última chispa, encerrada tras las puertas del castillo del amanecer."},
 {title:"Castillo del Amanecer",short:"Castillo",subtitle:"Toda heroína empieza con un paso",sky:["#301644","#803657","#fbb878"],ground:"#4c345d",top:"#f9b26c",accent:"#ffe3a0",flora:"#ffbabb",story:"En el castillo esperaba Sombra, un guardián que había escondido las estrellas para que nunca se apagaran. Cat entendió entonces que guardar la luz para siempre también significa dejar al mundo a oscuras.",end:"Cat abrió las manos. Sombra devolvió la última chispa y descubrió que compartir luz no la hace desaparecer. Lunaria volvió a encenderse. Y sobre su ventana, una nueva estrella llevaba su nombre."}
];
const names=[
 "La bufanda brillante","El puente de musgo","Luciérnagas traviesas","El árbol que susurraba",
 "Saltos de algodón","El viento juguetón","La canción de Nimbo","Por encima del cielo",
 "Brillos en la roca","Los pasos del eco","El río subterráneo","La promesa de Cat",
 "Jardines del ocaso","Escaleras de luna","La última chispa","El regreso de las estrellas"
];
const tips=[
 "Camina con A/D o las flechas. Salta con Espacio, W o ↑.",
 "Hay plataformas sobre el suelo: ¡explóralas!",
 "Salta sobre los enemigos para ahuyentarlos.",
 "Recoge la estrella grande para el álbum de Cat.",
 "Tienes un salto extra mientras estás en el aire.",
 "Los corazones son tu energía. Evita los pinchos.",
 "Los cristales azules guardan un punto de control.",
 "¡El portal dorado está al final del camino!",
 "Las monedas mejoran tu puntuación de nivel.",
 "El sonido puede desactivarse cuando quieras.",
 "Puedes volver a jugar niveles completados.",
 "Respira: el juego guarda tu avance automáticamente.",
 "Intenta recoger todas las estrellas grandes.",
 "Una sombra nunca puede apagar tu valentía.",
 "El portal final abrirá una nueva página de la historia.",
 "Al regresar a Lunaria, todas las luces te esperan."
];
const WIDTH=960,HEIGHT=540,GROUND=474;
function makeLevel(index){
 const chapter=Math.floor(index/4),stage=index%4;
 const length=2840+index*48;
 const grounds=[{x:0,w:960},{x:1070,w:830},{x:2010,w:length-2010}];
 const base=[
  [280,382,148],[512,315,125],[740,372,138],[925,395,135],
  [1083,360,125],[1303,320,144],[1528,356,155],[1744,316,152],
  [1870,393,140],[2040,361,135],[2285,316,154],[2515,375,142]
 ];
 const platforms=base.map(([x,y,w],i)=>({
  x:x+((i>5&&i<9)?stage*8:0),y:y-((stage===3&&i%4===1)?18:0),w,h:22
 }));
 // Un puente visible adicional sobre cada hueco del suelo.
 platforms.push({x:960,y:425,w:110,h:18},{x:1900,y:423,w:115,h:18});
 for(let x=2750;x<length-225;x+=225)platforms.push({x,y:340+Math.round(Math.sin(x)*35),w:135,h:22});
 const orbs=[];
 for(let x=160;x<length-180;x+=130)orbs.push({x,y:GROUND-56-((Math.floor(x/130)+index)%3)*15});
 for(const p of platforms)orbs.push({x:p.x+p.w/2,y:p.y-35});
 // Estrella especial que se puede conseguir saltando desde una plataforma.
 const starPlatform=platforms[6];
 const star={x:starPlatform.x+starPlatform.w/2,y:starPlatform.y-56};
 const checkpoint={x:1680,y:GROUND-66};
 const enemies=[
  {x:630,y:GROUND-27,range:64,speed:1.0+index*.03},
  {x:1210,y:GROUND-27,range:72,speed:1.3+index*.025},
  {x:2190,y:GROUND-27,range:77,speed:1.05+index*.03}
 ];
 if(stage>0)enemies.push({x:2540,y:GROUND-27,range:42,speed:1.4+index*.02});
 const spikes=[
  {x:820,y:GROUND-18,w:46,h:18},
  {x:1395,y:GROUND-18,w:48,h:18},
  {x:2260,y:GROUND-18,w:45,h:18}
 ];
 if(stage>=2)spikes.push({x:2605,y:GROUND-18,w:42,h:18});
 return {index,chapter,stage,name:names[index],tip:tips[index],theme:chapters[chapter],length,ground:grounds,platforms,orbs,star,checkpoint,enemies,spikes,portal:{x:length-150,y:GROUND-92},skyObjects:8+index%4};
}
const levels=names.map((_,i)=>makeLevel(i));
window.CAT_DATA={chapters,names,levels,WIDTH,HEIGHT,GROUND,total:16};
})();
