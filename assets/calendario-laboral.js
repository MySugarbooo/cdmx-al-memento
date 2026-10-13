'use strict';
/* Referencia de descansos obligatorios generales: art. 74 LFT.
 No sustituye el contrato, convenios especiales ni avisos electorales. */
(()=>{
 const yearPicker=document.getElementById('calendar-year');
 const results=document.getElementById('calendar-results');
 if(!yearPicker||!results)return;
 const nthMonday=(year,month,n)=>{
  const first=new Date(Date.UTC(year,month-1,1)).getUTCDay();
  return 1+(8-first)%7+7*(n-1);
 };
 const iso=(y,m,d)=>y+'-'+String(m).padStart(2,'0')+'-'+String(d).padStart(2,'0');
 const pretty=date=>{
  const [y,m,d]=date.split('-').map(Number);
  return new Intl.DateTimeFormat('es-MX',{weekday:'long',day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(Date.UTC(y,m-1,d)));
 };
 const items=y=>{
  const a=[
   {date:iso(y,1,1),label:'Año Nuevo'},
   {date:iso(y,2,nthMonday(y,2,1)),label:'Primer lunes de febrero, conmemoración del 5 de febrero'},
   {date:iso(y,3,nthMonday(y,3,3)),label:'Tercer lunes de marzo, conmemoración del 21 de marzo'},
   {date:iso(y,5,1),label:'Día del Trabajo'},
   {date:iso(y,9,16),label:'Aniversario de la Independencia'},
   {date:iso(y,11,nthMonday(y,11,3)),label:'Tercer lunes de noviembre, conmemoración del 20 de noviembre'},
   {date:iso(y,12,25),label:'Navidad'},
  ];
  if((y-2024)%6===0)a.push({date:iso(y,10,1),label:'Transmisión del Poder Ejecutivo Federal (cada seis años)'});
  return a.sort((a,b)=>a.date.localeCompare(b.date));
 };
 function render(){
  const year=Number(yearPicker.value);
  if(!Number.isInteger(year)||year<2026||year>2035)return;
  results.replaceChildren();
  for(const d of items(year)){
   const li=document.createElement('li'),title=document.createElement('strong'),when=document.createElement('small');
   title.textContent=d.label;
   when.textContent=pretty(d.date);
   li.append(title,when);results.append(li);
  }
  const note=document.getElementById('calendar-note');
  if(note)note.textContent='Listado general de descansos obligatorios de '+year+' según el artículo 74 de la Ley Federal del Trabajo. Los días que determinen las leyes electorales deben consultarse por separado; las condiciones especiales pueden cambiar el resultado.';
 }
 yearPicker.value='2026';
 yearPicker.addEventListener('change',render);render();
})();