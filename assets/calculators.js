'use strict';
const cur=n=>new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',minimumFractionDigits:2,maximumFractionDigits:2}).format(n);
const fmt=n=>new Intl.NumberFormat('es-MX',{maximumFractionDigits:4}).format(n);
const result=document.querySelector('#result');
const form=document.querySelector('#calculator');
if(form&&result){
  function numeric(key){const el=form.elements.namedItem(key);if(!el)throw Error('Campo no encontrado: '+key);const raw=String(el.value).trim().replace(',','.');if(raw==='')throw Error('Llena todos los campos.');const v=Number(raw);if(!Number.isFinite(v)||Math.abs(v)>1e12)throw Error('Introduce números válidos y razonables.');return v}
  function positive(key){const n=numeric(key);if(n<0)throw Error('Los valores no pueden ser negativos.');return n}
  function aboveZero(key){const n=positive(key);if(n===0)throw Error('Ese valor debe ser mayor que cero.');return n}
  function percent(key){const v=positive(key);if(v>100)throw Error('El porcentaje debe estar entre 0 y 100.');return v}
  function whole(key){const v=aboveZero(key);if(!Number.isInteger(v)||v>1000000)throw Error('Indica un número entero de personas.');return v}
  const formulas={
    descuentos(){const p=positive('precio'),d=percent('descuento'),saving=p*d/100;return [cur(p-saving),'Ahorras '+cur(saving)+' al aplicar un descuento de '+fmt(d)+' % sobre '+cur(p)+'.']},
    iva(){const amount=positive('monto'),rate=percent('tasa'),mode=form.elements.namedItem('modo').value;const factor=1+rate/100;if(mode==='agregar'){const tax=amount*rate/100;return [cur(amount+tax),'Monto base '+cur(amount)+' + IVA '+cur(tax)+' = '+cur(amount+tax)+'.']}const base=amount/factor;return [cur(base),'Base sin IVA '+cur(base)+' · impuesto incluido '+cur(amount-base)+'.']},
    porcentaje(){const base=numeric('base'),p=positive('porcentaje');return [fmt(base*p/100),'El '+fmt(p)+' % de '+fmt(base)+' es '+fmt(base*p/100)+'.']},
    propina(){const bill=positive('cuenta'),p=percent('propina'),people=whole('personas'),tip=bill*p/100;return [cur((bill+tip)/people)+' por persona','Total con propina: '+cur(bill+tip)+' · propina: '+cur(tip)+' · '+people+' persona(s).']},
    'dividir-cuenta'(){const total=positive('total'),people=whole('personas');return [cur(total/people)+' por persona','División igual de '+cur(total)+' entre '+people+' persona(s).']},
    'precio-unitario'(){const p1=positive('precio1'),q1=aboveZero('cantidad1'),p2=positive('precio2'),q2=aboveZero('cantidad2');const u1=p1/q1,u2=p2/q2;return [u1===u2?'Mismo precio unitario':u1<u2?'Conviene la opción A':'Conviene la opción B','Opción A: '+cur(u1)+' por unidad · Opción B: '+cur(u2)+' por unidad. Compara cantidades en la misma unidad.']},
    promedio(){const a=positive('nota1'),b=positive('nota2'),c=positive('nota3');if([a,b,c].some(n=>n>10))throw Error('Usa calificaciones entre 0 y 10.');const average=(a+b+c)/3;return [fmt(average)+' de 10','Promedio simple de tres materias con la misma importancia.']},
    'promedio-ponderado'(){const a=positive('n1'),b=positive('n2'),c=positive('n3'),w1=positive('p1'),w2=positive('p2'),w3=positive('p3');const sum=w1+w2+w3;if([a,b,c].some(n=>n>10)||sum===0)throw Error('Usa notas entre 0 y 10 y pesos mayores que cero.');return [fmt((a*w1+b*w2+c*w3)/sum)+' de 10','Ponderaciones ingresadas: '+fmt(sum)+' partes. Se normalizan automáticamente, aunque no sumen 100.']},
    'nota-necesaria'(){const current=positive('actual'),target=positive('objetivo'),weight=percent('peso');if(current>10||target>10||weight===0)throw Error('Las calificaciones deben ser de 0 a 10 y el examen tener peso mayor que 0 %.');const w=weight/100,need=(target-current*(1-w))/w;return [need<=0?'Meta ya alcanzable':need>10?'Meta imposible con esta ponderación':fmt(need)+' de 10','Nota necesaria en el examen: '+fmt(need)+'. Su peso en la calificación final es '+fmt(weight)+' %.']},
    ahorro(){const goal=positive('meta'),saved=positive('ahorrado'),weekly=aboveZero('semanal');const remaining=Math.max(0,goal-saved);const weeks=Math.ceil(remaining/weekly);return [weeks+' semana(s)','Faltan '+cur(remaining)+'. Este cálculo no contempla intereses, inflación ni imprevistos.']},
    'regla-de-tres'(){const a=numeric('a'),b=numeric('b'),c=numeric('c');if(a===0)throw Error('El primer valor (A) no puede ser cero.');return [fmt(b*c/a),'Relación directa: si '+fmt(a)+' corresponde a '+fmt(b)+', '+fmt(c)+' corresponde a '+fmt(b*c/a)+'.']}
  };
  function run(){try{const fn=formulas[form.dataset.tool];if(!fn)throw Error('Calculadora no disponible.');const [title,detail]=fn();const main=result.querySelector('.number'),desc=result.querySelector('.detail');main.textContent=title;desc.textContent=detail;result.classList.remove('error');}catch(e){result.querySelector('.number').textContent='Revisa los valores';result.querySelector('.detail').textContent=e.message;result.classList.add('error');}}
  form.addEventListener('submit',e=>{e.preventDefault();run()});form.addEventListener('input',run);form.addEventListener('change',run);run();
}
