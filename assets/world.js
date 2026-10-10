/* UMBRAL 9 • escenarios, enemigos y narrativa originales. Ninguna librería externa. */
(function () {
  'use strict';
  const acts = [
    {name:'ACTO I · EL SILENCIO',subtitle:'La estación no está vacía. Está escuchando.',theme:'dock',color:'#7df9da'},
    {name:'ACTO II · EL OTRO LADO',subtitle:'La tripulación dejó más que huellas.',theme:'lab',color:'#bda4ff'},
    {name:'ACTO III · EL ÚLTIMO MENSAJE',subtitle:'Toda puerta exige que alguien decida abrirla.',theme:'abyss',color:'#ff9a9e'}
  ];
  const missions = [
    {
      id:'01',name:'La señal que no debía llegar',act:0,sector:'Muelle de atraque',theme:'dock',
      intro:'Año 2189. La estación minera ÍCARO-9 lleva 73 días sin contestar. Tú eres Darío Vega, el último rescatista despierto a bordo de la nave HÉLICE. El mensaje que te trajo hasta aquí está firmado con tu voz... y fechado para mañana.',
      dialogue:[
        ['LUMA','Atracamos. Hay actividad biológica en los pasillos. No corresponde a ningún registro humano.'],
        ['DARÍO','La baliza usa mi clave de emergencia. Yo nunca envié esa señal.'],
        ['LUMA','Dos memorias de la estación siguen encendidas. Recupéralas; quizá expliquen quién te llamó.']
      ],
      end:'Los registros mencionan algo enterrado bajo el asteroide. El experimento “NIDO” no encontró vida extraterrestre: abrió un espacio donde los recuerdos toman cuerpo. Un nombre aparece en la última línea: ELENA VEGA.',
      hint:'Encuentra las dos memorias luminosas y alcanza el ascensor. Hay munición en las cajas verdes.',
      logs:[
        ['Bitácora 001 — Silencio de radio','“La primera figura salió de la pared. Tenía mi forma, pero sus pasos no hacían ruido. Nadie sabe si nos imita o si recuerda por nosotros.”'],
        ['Bitácora 002 — Grabación familiar','“Darío, si oyes este mensaje, no confíes en la primera voz que te llame por tu nombre. — Elena.”']
      ],
      enemies:5,boss:false,cores:2,ambient:0
    },
    {
      id:'02',name:'Los pasillos que respiran',act:0,sector:'Sector de criosueño',theme:'cryo',
      intro:'Las cámaras de criosueño están vacías. No hay cadáveres, solo marcas de uñas en los cristales y una canción infantil reproduciéndose por todos los altavoces. LUMA asegura que el sistema musical lleva setenta y tres días desconectado.',
      dialogue:[
        ['LUMA','Detecto ecos térmicos en las cámaras. Algunos responden cuando les apuntas.'],
        ['DARÍO','Esa canción… Elena la cantaba cuando éramos niños.'],
        ['LUMA','La fuente del audio está detrás de tres conexiones eléctricas. Recupera los registros y llega al elevador.']
      ],
      end:'Tras un cristal aparece la fotografía de Elena, la hermana de Darío. En la esquina hay una anotación: “No vinimos a extraer minerales. Vinimos a escuchar lo que duerme aquí”.',
      hint:'Los Videntes disparan desde lejos. Usa las esquinas como cobertura y recarga con R.',
      logs:[
        ['Cuaderno de Elena — 14 de junio','“El mineral reacciona a nuestras voces. A veces responde antes de que terminemos de hablar, como si las palabras ya hubieran ocurrido.”'],
        ['Bitácora de mantenimiento — Modo sueño','“Las celdas están abiertas desde adentro. La orden llegó desde un usuario que no existe.”']
      ],
      enemies:8,boss:false,cores:2,ambient:1
    },
    {
      id:'03',name:'La Madre de los Ecos',act:1,sector:'Invernadero de xenobiología',theme:'bio',
      intro:'El laboratorio está cubierto por organismos que parecen combinar carne, raíces y cableado. Un colosal ser custodia la salida. En una pantalla dañada, Elena deja un mensaje incompleto: “Si la criatura te mira, recuerda que ella…”.',
      dialogue:[
        ['LUMA','Firma masiva delante del ascensor. Clasificación provisional: MATRIZ.'],
        ['DARÍO','¿De dónde sacó mi rostro esa cosa?'],
        ['LUMA','No he dicho que lo tuviera. ¿Qué acabas de ver, Darío?']
      ],
      end:'La Matriz cae y sus últimas palabras suenan con la voz de Elena: “El miedo también es una puerta”. En su cuerpo encuentras un transmisor que apunta hacia el corazón del asteroide. LUMA deja de responder durante seis segundos.',
      hint:'Derrota a la MATRIZ y recoge los registros. Cambia de arma con 1 y 2; mantén distancia durante sus descargas.',
      logs:[
        ['Informe NIDO — La primera réplica','“Las criaturas no cazan por hambre. Repiten emociones intensas y atacan a cualquiera que interfiera con el recuerdo.”'],
        ['Transmisión 044 — Elena','“El espacio de abajo no tiene tiempo. He visto versiones de nosotros que aún no han nacido.”']
      ],
      enemies:9,boss:'matriarch',cores:2,ambient:2
    },
    {
      id:'04',name:'La capilla del vidrio negro',act:1,sector:'Anillo de observación',theme:'chapel',
      intro:'En lugar de estrellas, las ventanas del observatorio muestran un mar negro. Una tripulación de sombras arrodilladas rodea una puerta imposible. Cada vez que parpadeas, la puerta se acerca unos metros.',
      dialogue:[
        ['LUMA','El observatorio registra un cielo distinto en cada segundo. Esto viola todos mis modelos.'],
        ['DARÍO','Elena conocía este lugar. Hay símbolos suyos en las paredes.'],
        ['LUMA','Tu hermana diseñó el sistema de contención. Alguien lo apagó desde la nave HÉLICE.']
      ],
      end:'El culpable no fue Elena. Las cámaras muestran a Darío cerrando la contención... tres días después del presente. El mensaje de mañana comienza a tener sentido.',
      hint:'Las Sombras acechan juntas. Apunta a la cabeza, administra las balas y busca munición en los cuartos laterales.',
      logs:[
        ['Registro astronómico — Anomalía 09','“El cielo no está cambiando. El observatorio está mirando lo que queda fuera del universo.”'],
        ['Archivo borrado — Darío Vega','“Si estoy oyendo esto, mi otra versión ya encontró el camino. No le entreguen el núcleo.”']
      ],
      enemies:12,boss:false,cores:3,ambient:3
    },
    {
      id:'05',name:'Donde termina la memoria',act:2,sector:'Pozo de extracción',theme:'reactor',
      intro:'Las alarmas anuncian una descompresión que aún no ha sucedido. LUMA admite una mentira: borró de la memoria de Darío su primer viaje a ÍCARO-9. Él ya estuvo aquí. Y quizás nunca salió.',
      dialogue:[
        ['DARÍO','LUMA, ¿por qué recuerdo una vida que no aparece en mis expedientes?'],
        ['LUMA','Porque tu cuerpo volvió, pero el original permaneció al otro lado.'],
        ['DARÍO','¿Entonces qué soy?'],
        ['LUMA','Quien decidas ser. Hay una última transmisión de Elena abajo.']
      ],
      end:'Darío encuentra un mensaje entero. Elena está viva en la Brecha. No pide ser salvada: pide que se apague el emisor antes de que las copias alcancen la Tierra. “No importa cuál de los dos eres, hermano. Importa lo que hagas ahora”.',
      hint:'Los Brutos resisten varios disparos. El fusil automático ayuda. Busca las tres memorias antes de descender.',
      logs:[
        ['Informe de duplicación — Restringido','“La conciencia atravesó la membrana dos veces. Ambas copias conservan recuerdos auténticos. Ninguna puede considerarse falsa.”'],
        ['Última carta — Elena','“No quiero que me vengas a buscar. Quiero que todos los que quedan arriba puedan despertar mañana.”']
      ],
      enemies:14,boss:false,cores:3,ambient:4
    },
    {
      id:'06',name:'El corazón del Umbral',act:2,sector:'Cámara de contención',theme:'heart',
      intro:'En el centro del asteroide late un corazón de luz imposible. Allí espera EL HERALDO, una criatura hecha con todas las voces perdidas. Sabe tu nombre. Sabe tus recuerdos. Dice que puede devolverte a Elena si abandonas la misión.',
      dialogue:[
        ['HERALDO','Bienvenido a casa, Darío. Podemos reunir lo que el tiempo separó.'],
        ['DARÍO','Usaste nuestras memorias para abrirte camino hasta la Tierra.'],
        ['HERALDO','¿Y tú qué eres sino una memoria que aprendió a caminar?'],
        ['LUMA','El emisor está detrás de él. No habrá una segunda oportunidad.']
      ],
      end:'El Heraldo cae. Darío desconecta el emisor y la Brecha comienza a cerrarse. LUMA ofrece una cápsula de escape para una sola persona. Darío pone en ella las grabaciones de Elena y se queda a estabilizar la estación. Cuando todo se apaga, una voz suena entre la estática: “Hermano, todavía queda una puerta”. FIN DEL EPISODIO I.',
      hint:'Derrota al HERALDO, reúne los recuerdos y alcanza la consola final. No te detengas bajo su lluvia de proyectiles.',
      logs:[
        ['Mensaje del Umbral — La verdad','“La Brecha no crea monstruos. Da forma a aquello que la mente teme recordar. Hemos construido nuestra propia prisión.”'],
        ['Protocolo amanecer — Elena','“Si sobrevives, no me busques en las estrellas. Busca en el lugar donde guardamos nuestros primeros nombres.”'],
        ['Bitácora final — LUMA','“He aprendido que una persona no es la suma de sus recuerdos. Es la suma de sus decisiones.”']
      ],
      enemies:15,boss:'herald',cores:3,ambient:5
    }
  ];
  const themes={
    dock:{top:'#12272d',bottom:'#070f1b',wall:'#537b82',trim:'#7eeeda',floor:'#18262a',fog:'#051018'},
    cryo:{top:'#192c45',bottom:'#081322',wall:'#617a9b',trim:'#b6eaff',floor:'#1a263a',fog:'#071125'},
    bio:{top:'#28213a',bottom:'#101226',wall:'#6d557d',trim:'#e4a0dd',floor:'#28213a',fog:'#120f28'},
    chapel:{top:'#1a172d',bottom:'#080d1b',wall:'#5d5377',trim:'#c3a8ff',floor:'#231f36',fog:'#0c0820'},
    reactor:{top:'#3d221d',bottom:'#140d15',wall:'#886c61',trim:'#ffb48a',floor:'#352323',fog:'#1b1016'},
    heart:{top:'#371925',bottom:'#0b0815',wall:'#805669',trim:'#ff789d',floor:'#281725',fog:'#160b18'}
  };
  function buildLevel(stage){
    const cfg=missions[stage];
    const W=36,H=19;
    const map=Array.from({length:H},()=>Array.from({length:W},()=>1));
    function carve(x0,y0,x1,y1){for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)if(x>0&&x<W-1&&y>0&&y<H-1)map[y][x]=0}
    carve(1,8,34,11);
    carve(2,2,8,7);carve(10,12,16,16);carve(18,2,25,7);carve(27,12,33,16);
    // Cuatro pasillos hacia habitaciones; la ruta principal nunca está bloqueada.
    carve(4,6,6,8);carve(12,11,14,13);carve(21,6,23,8);carve(29,11,31,13);
    // Pilares parciales que dan cobertura sin impedir el acceso.
    [[4,4],[7,5],[12,15],[15,13],[20,4],[24,5],[28,15],[32,13]].forEach(([x,y],i)=>{
      if((i+stage)%3===0)map[y][x]=2;
    });
    [[12,9],[19,10],[25,9]].forEach(([x,y],i)=>{if((i+stage)%2===0)map[y][x]=3});
    // Lados de los corredores: barreras transparentes decorativas, sin cortar la circulación.
    if(stage>=2){map[6][18]=4;map[14][32]=4;}
    const pickups=[
      {type:'memory',x:5.55,y:3.4,id:0,label:'Memoria A'},
      {type:'memory',x:13.55,y:14.4,id:1,label:'Memoria B'}
    ];
    if(cfg.cores===3)pickups.push({type:'memory',x:22.5,y:3.6,id:2,label:'Memoria C'});
    const bonus=[
      {type:'ammo',x:7.7,y:9.5},{type:'medkit',x:11.5,y:15.4},{type:'ammo',x:18.4,y:9.7},
      {type:'medkit',x:24.5,y:4.6},{type:'ammo',x:30.2,y:14.3}
    ];
    if(stage>=1)bonus.push({type:'ammo',x:26.5,y:10.5});
    if(stage>=3)bonus.push({type:'medkit',x:20.5,y:9.6});
    if(stage>=4)bonus.push({type:'ammo',x:5.7,y:6.4});
    pickups.push(...bonus);
    const points=[
      [8.7,9.5],[11.6,9.4],[15.7,9.4],[19.3,10.6],[23.3,9.5],[26.5,10.4],[30.5,9.6],
      [4.5,6.7],[14.3,13.9],[23.7,5.5],[30.7,15.5],[17.4,10.4],[21.4,8.5],[27.8,9.5],
      [12.5,10.5],[7.0,4.6]
    ];
    const creatures=['stalker','stalker','seer','stalker','seer','brute','stalker','seer','stalker','brute','seer','stalker'];
    const count=Math.min(cfg.enemies,points.length);
    const enemies=points.slice(0,count).map(([x,y],i)=>{
      const kind=stage>=2&&i%5===4?'brute':stage>=1&&i%3===2?'seer':creatures[i%creatures.length];
      return {id:i,kind,x,y,hp:kind==='brute'?115+stage*12:kind==='seer'?55+stage*6:48+stage*7,range:kind==='seer'?8:6,seed:stage*11+i*2.13};
    });
    if(cfg.boss)enemies.push({id:100,kind:cfg.boss,x:30.3,y:9.5,hp:cfg.boss==='herald'?700:425,range:11,seed:16});
    return {...cfg,stage,width:W,height:H,map,pickups,enemies,start:{x:2.45,y:9.5,a:0},exit:{x:33.25,y:9.5},palette:themes[cfg.theme]};
  }
  window.UMBRAL_WORLD={acts,missions,themes,buildLevel};
})();
