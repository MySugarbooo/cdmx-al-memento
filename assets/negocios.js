'use strict';
/* Directorio de exploración; no certifica datos comerciales ni muestra
   publicidad de negocios que no hayan contratado un patrocinio. */
(()=>{
 const boroughs=['Álvaro Obregón','Azcapotzalco','Benito Juárez','Coyoacán','Cuajimalpa de Morelos','Cuauhtémoc','Gustavo A. Madero','Iztacalco','Iztapalapa','La Magdalena Contreras','Miguel Hidalgo','Milpa Alta','Tláhuac','Tlalpan','Venustiano Carranza','Xochimilco'];
 const examples=[
  ['Mercado de San Ángel','Álvaro Obregón','Mercado'],
  ['Mercado Portales','Benito Juárez','Mercado'],
  ['Mercado de Coyoacán','Coyoacán','Mercado'],
  ['Mercado Medellín','Cuauhtémoc','Mercado'],
  ['Mercado de San Juan','Cuauhtémoc','Mercado'],
  ['Central de Abasto de la Ciudad de México','Iztapalapa','Central de abasto'],
  ['Mercado Escandón','Miguel Hidalgo','Mercado'],
  ['Mercado La Paz','Tlalpan','Mercado'],
  ['Mercado de Jamaica','Venustiano Carranza','Mercado de flores'],
  ['Mercado La Merced','Venustiano Carranza','Mercado'],
  ['Mercado de Xochimilco','Xochimilco','Mercado']
 ];
 const cards=document.getElementById('local-market-results'),select=document.getElementById('local-market-area'),search=document.getElementById('local-market-query'),status=document.getElementById('local-market-status');
 if(!cards||!select||!search||!status)return;
 for(const name of boroughs){
  const opt=document.createElement('option');opt.value=name;opt.textContent=name;select.append(opt);
 }
 const mapURL=(name,borough)=>'https://www.openstreetmap.org/search?query='+encodeURIComponent(name+' '+borough+' Ciudad de México');
 const el=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text)x.textContent=text;return x};
 function card(name,borough,type,isGuide=false){
  const wrapper=el('article','explore-feature');
  const tag=el('p','explore-tag',type+' · '+borough);
  const title=el('h3','',name);
  const detail=el('p','portal-info',isGuide?
   'Explora opciones aportadas por la comunidad de mapas; verifica la información en el sitio del comercio.':
   'Lugar de referencia histórica o comercial; la ficha no confirma horario, precio, servicio ni operación actual.');
  const anchor=el('a','explore-btn',isGuide?'Buscar comercios en mapa colaborativo ↗':'Consultar ubicación orientativa ↗');
  anchor.href=mapURL(name,borough);anchor.target='_blank';anchor.rel='noopener noreferrer nofollow';
  wrapper.append(tag,title,detail,anchor);return wrapper;
 }
 function render(){
  const name=select.value;
  const q=search.value.trim().normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  cards.replaceChildren();let count=0;
  const matches=(title,borough)=>{
   const test=(title+' '+borough).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
   return (!name||borough===name)&&test.includes(q);
  };
  for(const [title,borough,type] of examples){
   if(!matches(title,borough))continue;
   cards.append(card(title,borough,type));count++;
  }
  // Las 16 alcaldías participan igual, incluso sin lugares seleccionados:
  // el enlace evita inventar nombres u horarios de negocios.
  for(const borough of boroughs){
   const title='Mercados, cafeterías y comercios de '+borough;
   if(!matches(title,borough))continue;
   cards.append(card(title,borough,'Búsqueda comunitaria',true));count++;
  }
  status.textContent=count+' resultados de referencia/búsquedas comunitarias. No son fichas de operación verificadas.';
  if(!count){const n=el('p','explore-note','No hay coincidencias. Cambia la alcaldía o prueba otra palabra.');cards.append(n);}
 }
 select.addEventListener('change',render);search.addEventListener('input',render);
 render();
})();