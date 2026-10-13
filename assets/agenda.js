'use strict';
/* Agenda editorial: solo eventos con fuente y fechas explícitas.
   Los eventos vencidos se ocultan en el navegador. No se inventan actividades. */
(()=>{
 const BOROUGHS=['Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras','Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'];
 const el=document.getElementById('agenda-list'),area=document.getElementById('agenda-borough'),free=document.getElementById('agenda-free'),status=document.getElementById('agenda-status'),next=document.getElementById('agenda-sources');
 if(!el||!area||!free||!status)return;
 for(const name of BOROUGHS){const opt=document.createElement('option');opt.value=name;opt.textContent=name;area.append(opt);}
 let rows=[];
 function todayMX(){
  const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Mexico_City',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const val=k=>parts.find(x=>x.type===k)?.value||'';
  return val('year')+'-'+val('month')+'-'+val('day');
 }
 function create(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e;}
 function render(){
  const wanted=area.value,now=todayMX();
  const displayed=rows.filter(x=>(!wanted||x.borough===wanted)&&(!free.checked||x.free===true)&&x.ends>=now);
  el.replaceChildren();
  for(const event of displayed){
   const card=create('article','explore-feature');
   const tag=create('p','explore-tag',event.category+' · '+event.borough);
   const heading=create('h3','',event.title);
   const meta=create('p','portal-info',event.venue+' · '+event.starts+(event.ends!==event.starts?' al '+event.ends:'')+' · '+event.price);
   const intro=create('p','',event.description||'');
   const link=create('a','explore-btn','Confirmar fecha, lugar y costo en la fuente oficial ↗');
   link.href=event.official;link.target='_blank';link.rel='noopener noreferrer nofollow';
   card.append(tag,heading,meta,intro,link);el.append(card);
  }
  if(!displayed.length){
   const msg=create('div','explore-note','No tenemos eventos con fecha y fuente revisadas para este filtro. Eso NO significa que no haya actividades: consulta la cartelera cultural oficial.');
   el.append(msg);
  }
  status.textContent=displayed.length+' actividad(es) con fecha y fuente, vigentes según la información publicada. Última revisión editorial: 13 octubre 2026. Verifica cambios en el enlace oficial.';
  if(next)next.textContent=wanted?'Ver más actividades oficiales de '+wanted+' ↗':'Explorar cartelera oficial de las 16 alcaldías ↗';
 }
 area.addEventListener('change',render);free.addEventListener('change',render);
 fetch('/agenda/eventos.json?t='+Date.now(),{cache:'no-store'}).then(r=>{
  if(!r.ok)throw Error('Catálogo no disponible');return r.json();
 }).then(data=>{
  rows=(Array.isArray(data.events)?data.events:[]).filter(e=>e&&/^https:\/\//.test(e.official||'')&&/^\d{4}-\d{2}-\d{2}$/.test(e.starts||'')&&/^\d{4}-\d{2}-\d{2}$/.test(e.ends||'')&&BOROUGHS.includes(e.borough));
  render();
 }).catch(()=>{status.textContent='No pudimos cargar eventos revisados. Consulta la cartelera oficial.';render()});
})();