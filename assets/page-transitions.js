'use strict';
/* Cabecera compartida y navegación fluida de CDMX AL MEMENTO.
 * No se interceptan enlaces ni se oculta el contenido durante la salida.
 * CSS View Transitions realiza cambios progresivos cuando el navegador lo soporta.
 */
(()=>{
 const path=location.pathname;
 const standalone=path.startsWith('/kisumi-studio/')||path.startsWith('/escribe-pro/')||path==='/mapa/preview.html';
 if(standalone)return;
 // Páginas sin styles.css, como la portada de animales generada, reciben el tema.
 if(![...document.styleSheets].some(s=>s.href&&/\/styles\.css(?:\?|$)/.test(s.href))){
   const core=document.createElement('link');core.rel='stylesheet';core.href='/styles.css?v=20261027-unificado';document.head.append(core);
 }
 // Las páginas con styles.css ya importan el tema; el resto lo reciben por la hoja central.
 // Esta navegación no añade un segundo archivo CSS duplicado.
 if(path==='/'||path==='/index.html')return;
 function init(){
  const main=document.querySelector('main');if(!main||document.body.classList.contains('neo-site-inner')){document.documentElement.classList.add('neo-ready');return;}
  document.body.classList.add('neo-site-inner');
  const section=(function(){
   if(path.startsWith('/cdmx/'))return ['CDMX','Últimas noticias de la capital con fecha y fuente','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/seguridad/'))return ['Seguridad','Noticias y prevención','/assets/fotos/seguridad.jpg'];
   if(path.startsWith('/servicios/'))return ['Servicios','Guías y herramientas útiles para tu ciudad','/assets/fotos/gobierno.jpg'];
   if(path.startsWith('/alcaldias/'))return ['Alcaldías','Noticias e historia de las 16 demarcaciones','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/descubre/'))return ['Descubre CDMX','Cultura, historia y rutas de las alcaldías','/assets/fotos/zocalo.jpg'];
   if(path.startsWith('/avisos/'))return ['Alertas y avisos','Consulta fuentes oficiales y recomendaciones','/assets/fotos/seguridad.jpg'];
   if(path.startsWith('/movilidad/'))return ['Movilidad','Metro, Metrobús y transporte en la capital','/assets/fotos/movilidad.jpg'];
   if(path.startsWith('/guias/'))return ['Guías','Información para tomar mejores decisiones','/assets/fotos/metro.jpg'];
   if(path.startsWith('/animales/'))return ['Animales y naturaleza','Rescate, bienestar animal y biodiversidad','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/comunidad/'))return ['Mi comunidad','Pregunta, comparte y responde con tu cuenta','/assets/fotos/angel.jpg'];
   if(path.startsWith('/noticias/'))return ['Noticias','Información con fecha, fuente y contexto','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/archivo/'))return ['Hemeroteca','Noticias organizadas por mes','/assets/fotos/zocalo.jpg'];
   if(path.startsWith('/reportes/'))return ['Reportes','Seguimiento editorial con fuentes originales','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/mapa/'))return ['Mapa de CDMX','Explora lugares y rutas de la capital','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/cerca/'))return ['Cerca de ti','Noticias por alcaldía y servicios cercanos','/assets/fotos/reforma.jpg'];
   if(path.startsWith('/favoritos/'))return ['Guardados','Tus noticias favoritas en este dispositivo','/assets/fotos/angel.jpg'];
   if(path.startsWith('/agenda/'))return ['Agenda cultural','Eventos y actividades para explorar','/assets/fotos/cultura.jpg'];
   if(path.startsWith('/negocios/'))return ['Comercios','Negocios y servicios de la CDMX','/assets/fotos/gobierno.jpg'];
   if(path.startsWith('/herramientas/'))return ['Herramientas','Calculadoras y recursos prácticos','/assets/fotos/zocalo.jpg'];
   if(path.startsWith('/publicidad/'))return ['Publicidad','Información comercial y transparencia','/assets/fotos/reforma.jpg'];
   if(path.includes('fotograf'))return ['Fotografías','Créditos y fuentes de nuestras imágenes','/assets/fotos/angel.jpg'];
   if(path.includes('privacidad'))return ['Privacidad','Cómo protegemos tu información','/assets/fotos/angel.jpg'];
   if(path.includes('contacto'))return ['Contacto','Sugerencias y correcciones editoriales','/assets/fotos/reforma.jpg'];
   return ['CDMX AL MEMENTO','Noticias, información y recursos de la capital','/assets/fotos/angel.jpg'];
  })();
  const navItems=[
   ['Portada','/'],['Alcaldías','/alcaldias/'],['CDMX','/cdmx/'],
   ['Seguridad','/seguridad/'],['Movilidad','/movilidad/'],['Servicios','/servicios/'],
   ['Animales','/animales/'],['Fotografías','/fotografias/'],['Mi comunidad','/comunidad/']
  ];
  const icon='<svg viewBox="0 0 100 85" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="site-pink" x1="0" x2="1"><stop stop-color="#ff9dce"/><stop offset="1" stop-color="#ee3896"/></linearGradient></defs><g fill="url(#site-pink)"><path d="M4 79h92v4H4zM12 77V54l9-5 9 6v22zM34 77V25l8-5 7 9v48zM53 77V35l11-8 7 7v43zM76 77V47l8-4 5 8v26zM43 20l4-15 5 16-5 3zM45 4l3-4 2 4zM60 27l-2-15 7 7-1 11z"/></g><g fill="#ffe0ed"><rect x="40" y="38" width="3" height="8"/><rect x="60" y="42" width="3" height="6"/><rect x="80" y="55" width="3" height="7"/></g></svg>';
  let header=document.querySelector('body > header');
  if(!header){header=document.createElement('header');document.body.insertBefore(header,main)}
  header.className='neo-global-header';
  const top=document.createElement('div');top.className='neo-global-top';
  const status=document.createElement('div');status.className='neo-global-date';
  const time=document.createElement('time');let today=new Date();
  time.dateTime=today.toISOString().slice(0,10);
  time.textContent=new Intl.DateTimeFormat('es-MX',{timeZone:'America/Mexico_City',dateStyle:'full'}).format(today);
  const city=document.createElement('span');city.className='neo-site-local';city.textContent='Ciudad de México · Noticias con fuentes';
  status.append(time,city);
  const brand=document.createElement('a');brand.href='/';brand.className='neo-global-brand';
  brand.setAttribute('aria-label','CDMX AL MEMENTO · volver a portada');
  brand.innerHTML=icon+'<strong>CDMX<em>AL MEMENTO</em></strong>';
  const actions=document.createElement('div');actions.className='neo-global-actions';
  const search=document.createElement('form');search.className='neo-global-search';search.setAttribute('role','search');
  search.action='/';search.method='get';
  const input=document.createElement('input');input.type='search';input.name='buscar';input.placeholder='Buscar noticias…';input.setAttribute('aria-label','Buscar noticias en la portada');
  const searchButton=document.createElement('button');searchButton.type='submit';searchButton.setAttribute('aria-label','Buscar noticias');searchButton.textContent='⌕';
  search.append(input,searchButton);
  const mobileSearch=document.createElement('button');mobileSearch.type='button';mobileSearch.className='neo-mobile-search';
  mobileSearch.setAttribute('aria-label','Abrir buscador');mobileSearch.setAttribute('aria-expanded','false');mobileSearch.textContent='⌕';
  mobileSearch.addEventListener('click',()=>{
    const open=search.classList.toggle('neo-open');mobileSearch.setAttribute('aria-expanded',String(open));
    if(open)input.focus()
  });
  const toggle=document.createElement('button');toggle.type='button';toggle.textContent='☾';toggle.setAttribute('aria-label','Cambiar tono de la interfaz');
  toggle.addEventListener('click',()=>{
   document.body.classList.toggle('neo-site-soft');document.documentElement.classList.toggle('neo-soft');
   toggle.setAttribute('aria-pressed',String(document.body.classList.contains('neo-site-soft')));
  });
  const profile=document.createElement('a');profile.href='/comunidad/';profile.textContent='♙';profile.setAttribute('aria-label','Mi comunidad');
  actions.append(search,mobileSearch,toggle,profile);top.append(status,brand,actions);
  const nav=document.createElement('nav');nav.className='neo-global-nav';nav.setAttribute('aria-label','Secciones principales');
  let selected=false;
  const active=(href)=>{
    if(href==='/')return false;
    if(href==='/alcaldias/')return path.startsWith('/alcaldias/');
    if(href==='/cdmx/')return path.startsWith('/cdmx/');
    if(href==='/seguridad/')return path.startsWith('/seguridad/')||path.startsWith('/avisos/');
    if(href==='/servicios/')return path.startsWith('/servicios/')||path.startsWith('/guias/')||path.startsWith('/herramientas/');
    if(href==='/fotografias/')return path.includes('fotograf');
    return path.startsWith(href);
  };
  for(const [label,href] of navItems){
   const a=document.createElement('a');a.textContent=label;a.href=href;
   if(active(href)){a.setAttribute('aria-current','page');selected=true}
   nav.append(a)
  }
  for(const [label,href] of [['Archivo','/archivo/'],['Reportes','/reportes/'],['Mapa','/mapa/']]){
    const a=document.createElement('a');a.className='neo-nav-more';a.href=href;a.textContent=label;
    if(path.startsWith(href))a.setAttribute('aria-current','page');
    nav.append(a);
  }
  header.replaceChildren(top,nav);
  const banner=document.createElement('div');banner.className='neo-inner-banner';banner.style.setProperty('--neo-section-img','url("'+section[2]+'")');
  const intro=document.createElement('div');const kicker=document.createElement('span');kicker.className='neo-inner-label';kicker.textContent='CDMX AL MEMENTO · EXPLORA';
  const label=document.createElement('strong');label.textContent=section[0];const desc=document.createElement('p');desc.textContent=section[1];intro.append(kicker,label,desc);
  const back=document.createElement('a');back.href='/';back.className='neo-back';back.textContent='← Volver a portada';
  // La sección ya presenta un título editorial propio: no duplicarlo con otra banda.
  // Conservar la cabecera y navegación global, sin agregar un segundo encabezado.
  if(!main.querySelector('h1,[role="heading"][aria-level="1"]')){
    banner.append(intro,back);main.prepend(banner);
  }
  let dock=document.querySelector('body > nav.neo-inner-dock');
  if(!dock){dock=document.createElement('nav');dock.className='neo-inner-dock';dock.setAttribute('aria-label','Navegación móvil');
    const entries=[['⌂','Inicio','/'],['▤','Alcaldías','/alcaldias/'],['＋','Publicar','/comunidad/#cdmx-comments-editor'],['♧','Comunidad','/comunidad/'],['♡','Guardados','/favoritos/']];
    for(const [symbol,label,href] of entries){
      const a=document.createElement('a');a.href=href;a.setAttribute('aria-label',label);
      if(label==='Publicar')a.className='neo-publish';
      else if((label==='Alcaldías'&&path.startsWith('/alcaldias/'))||(label==='Comunidad'&&path.startsWith('/comunidad/'))||(label==='Guardados'&&path.startsWith('/favoritos/')))a.className='neo-current';
      const icon=document.createElement('span');icon.textContent=symbol;a.append(icon,document.createTextNode(label==='Publicar'?'':label));dock.append(a)
    }
    document.body.append(dock);
  }
  // Los anclajes internos se desplazan de forma suave; no bloquear formularios ni links de otras rutas.
  document.addEventListener('click',e=>{
    const link=e.target.closest?.('a[href^="#"]');if(!link||e.defaultPrevented)return;
    const id=decodeURIComponent(link.getAttribute('href').slice(1));if(!id)return;
    const target=document.getElementById(id);if(!target)return;
    if(!matchMedia('(prefers-reduced-motion: reduce)').matches){e.preventDefault();history.replaceState(null,'','#'+encodeURIComponent(id));
      target.scrollIntoView({behavior:'smooth',block:'start'})}
  });
 }
 const originalInit=init;
 function revealAfterInit(){try{originalInit()}finally{document.documentElement.classList.add('neo-ready')}}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',revealAfterInit,{once:true});
 else revealAfterInit();
})();
