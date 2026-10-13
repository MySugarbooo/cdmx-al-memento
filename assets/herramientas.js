'use strict';
/* Cálculos explicativos, no asesoría laboral ni finiquito oficial. */
(()=>{
 const fmt=n=>new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:2}).format(n);
 const out=(id,value)=>{const el=document.getElementById(id);if(el)el.textContent=value};
 const read=(form,name,min=0,max=1e9)=>{
  const n=Number(form.elements.namedItem(name)?.value);
  return Number.isFinite(n)&&n>=min&&n<=max?n:NaN;
 };
 const daysInYear=year=>((year%4===0&&year%100!==0)||year%400===0)?366:365;
 function vacations(years){
  if(years<=0)return 0;
  if(years<=5)return 10+2*years;
  return 20+2*Math.ceil((years-5)/5);
 }
 function formatResult(value,details){
  return fmt(value)+(details?' · '+details:'');
 }
 const aguinaldo=document.getElementById('tool-aguinaldo');
 if(aguinaldo)aguinaldo.addEventListener('submit',event=>{
  event.preventDefault();
  const salary=read(aguinaldo,'salario',0.01,1000000);
  const year=read(aguinaldo,'anio',2000,2100);
  const days=read(aguinaldo,'dias',0,366);
  const entitlement=read(aguinaldo,'derecho',15,100);
  const total=daysInYear(year);
  if([salary,year,days,entitlement].some(n=>!Number.isFinite(n))||days>total){
   out('tool-aguinaldo-out','Revisa salario, año y días; no pueden exceder los días del año.');return;
  }
  const result=salary*entitlement*days/total;
  out('tool-aguinaldo-out',formatResult(result,entitlement+' días anuales × '+days+'/'+total+' días trabajados, antes de impuestos.'));
 });
 const vac=document.getElementById('tool-vacaciones');
 if(vac)vac.addEventListener('submit',event=>{
  event.preventDefault();
  const salary=read(vac,'salario',0.01,1000000);
  const years=read(vac,'antiguedad',1,70);
  const percentage=read(vac,'porcentaje',25,100);
  if([salary,years,percentage].some(n=>!Number.isFinite(n))||!Number.isInteger(years)){
   out('tool-vacaciones-out','Introduce un salario válido y años completos de antigüedad.');return;
  }
  const days=vacations(years),bonus=salary*days*(percentage/100);
  out('tool-vacaciones-out',formatResult(bonus,days+' días de vacaciones al año × '+percentage+' % de prima; es solo el complemento, no el salario vacacional.'));
 });
 const fin=document.getElementById('tool-finiquito');
 if(fin)fin.addEventListener('submit',event=>{
  event.preventDefault();
  const salary=read(fin,'salario',0.01,1000000);
  const year=read(fin,'anio',2000,2100);
  const days=read(fin,'dias',0,366);
  const years=read(fin,'antiguedad',1,70);
  const vacationWorked=read(fin,'diasciclo',0,366);
  const taken=read(fin,'disfrutados',0,100);
  const pending=read(fin,'pendiente',0,100);
  const total=daysInYear(year);
  if([salary,year,days,years,vacationWorked,taken,pending].some(n=>!Number.isFinite(n))||
    !Number.isInteger(years)||days>total||vacationWorked>366){
   out('tool-finiquito-out','Revisa los números. Usa días no negativos y el año correcto.');return;
  }
  const aguinaldoPart=salary*15*days/total;
  const accrued=vacations(years)*vacationWorked/365;
  const owed=Math.max(0,accrued-taken);
  const vacationPay=salary*owed;
  const premium=vacationPay*.25;
  const salaryPending=salary*pending;
  const sum=aguinaldoPart+vacationPay+premium+salaryPending;
  out('tool-finiquito-out',fmt(sum)+' · Salario pendiente '+fmt(salaryPending)+
   ' + aguinaldo proporcional '+fmt(aguinaldoPart)+
   ' + vacaciones estimadas '+fmt(vacationPay)+
   ' + prima vacacional '+fmt(premium)+'. Estimación orientativa antes de deducciones; no incluye indemnización, bonos, horas extra ni condiciones del contrato.');
 });
 const budget=document.getElementById('tool-ahorro');
 if(budget)budget.addEventListener('submit',event=>{
  event.preventDefault();
  const income=read(budget,'ingreso',0,1e9);
  const fixed=read(budget,'fijos',0,1e9);
  const variable=read(budget,'variables',0,1e9);
  if([income,fixed,variable].some(n=>!Number.isFinite(n))){
   out('tool-ahorro-out','Usa montos válidos.');return;
  }
  const left=income-fixed-variable;
  out('tool-ahorro-out',fmt(left)+' al mes · '+(left>=0?'Puedes decidir cuánto reservar de este sobrante.':'Los gastos superan el ingreso; revisa tu presupuesto.'));
 });
 const converter=document.getElementById('tool-distancias');
 if(converter)converter.addEventListener('submit',event=>{
  event.preventDefault();
  const km=read(converter,'kilometros',0,10000);
  const speed=read(converter,'velocidad',1,150);
  if(!Number.isFinite(km)||!Number.isFinite(speed)){
   out('tool-distancias-out','Escribe una distancia y una velocidad válidas.');return;
  }
  const minutes=Math.round(km/speed*60);
  out('tool-distancias-out',minutes+' minutos aproximados · '+km+' km a '+speed+' km/h, sin considerar tráfico, semáforos ni pendientes.');
 });
 const thisYear=new Date().getFullYear();
 for(const el of document.querySelectorAll('[data-default-year]')){
  el.value=thisYear;
 }
})();