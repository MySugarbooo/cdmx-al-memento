'use strict';
/* Fototeca editorial: catálogo de 1,100 imágenes con filtros, búsqueda y carga por lotes. */
(() => {
 const grid=document.getElementById('neo-photo-grid');
 const status=document.getElementById('neo-photo-status');
 if(!grid||!status)return;
 const DATA='/assets/fotos/catalogo-editorial-1100.json';
 const NOTICE='Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.';
 const safeImage=u=>/^\/assets\/fotos\/[a-z0-9_]+\.jpg$/i.test(String(u||''))||/^https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons\//.test(String(u||''));
 const safeCommons=u=>/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(String(u||''));
 const safeLicense=u=>/^https:\/\/creativecommons\.org\//.test(String(u||''));
 const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
 const fold=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const SIZE=24;
 fetch(DATA,{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
 .then(data=>{
  const photos=(Array.isArray(data.photos)?data.photos:[]).filter(p=>
   p&&safeImage(p.url)&&safeCommons(p.source)&&safeLicense(p.licenseUrl)&&p.author&&p.license&&p.topic);
  if(photos.length<901||photos.length!==data.count)throw Error('El catálogo no ha pasado la validación');
  const controls=el('div','neo-photo-toolbar');
  const filterBar=el('div','neo-photo-filters');
  const search=el('input','neo-photo-search');
  search.type='search';search.placeholder='Buscar alcaldía, transporte, museo o lugar…';
  search.setAttribute('aria-label','Buscar fotografías por tema o lugar');
  search.autocomplete='off';
  controls.append(search,filterBar);
  grid.before(controls);
  const more=el('button','neo-photo-more','Mostrar 24 imágenes más');
  more.type='button';more.setAttribute('aria-label','Cargar más fotografías de la galería');
  grid.after(more);
  const categories=['Todas',...new Set(photos.map(p=>p.category))];
  const buttons=new Map();
  let current='Todas',matches=[],rendered=0;
  const buildPhoto=p=>{
   const figure=el('figure','neo-photo-card');
   const img=el('img');
   img.src=p.url;img.loading='lazy';img.decoding='async';
   img.alt='Fotografía de carácter ilustrativo: '+p.topic;
   img.addEventListener('error',()=>{
     img.remove();figure.classList.add('neo-photo-unavailable');
     figure.prepend(el('p','neo-photo-error','Vista previa no disponible. Consulta el archivo original en Wikimedia Commons.'));
   },{once:true});
   const caption=el('figcaption');
   const categoryTag=el('span','neo-photo-category',p.category);
   const title=el('strong','',p.topic);
   const author=el('small','','Autor: '+p.author+' · Licencia: '+p.license);
   const links=el('div','neo-photo-links');
   const origin=el('a','','Ver fotografía y autor ↗');
   origin.href=p.source;origin.rel='noopener noreferrer';origin.target='_blank';
   const license=el('a','','Condiciones de licencia ↗');
   license.href=p.licenseUrl;license.rel='noopener noreferrer';license.target='_blank';
   links.append(origin,license);
   const notice=el('small','neo-photo-warning',NOTICE);
   const adaptation=el('small','neo-photo-warning',p.adaptation||'Fotografía conservada como archivo.');
   caption.append(categoryTag,title,author,links,notice,adaptation);
   figure.append(img,caption);return figure;
  };
  const displayMore=()=>{
   const fragment=document.createDocumentFragment();
   const end=Math.min(matches.length,rendered+SIZE);
   for(let i=rendered;i<end;i++)fragment.append(buildPhoto(matches[i]));
   grid.append(fragment);rendered=end;
   more.hidden=rendered>=matches.length;
   status.textContent='Mostrando '+rendered+' de '+matches.length+' resultados · Fototeca: '+photos.length+' imágenes con autor, fuente y licencia.';
  };
  const filter=()=>{
   const term=fold(search.value.trim());
   matches=photos.filter(p=>(current==='Todas'||p.category===current)&&
    (!term||fold([p.topic,p.file,p.category,...(p.keywords||[])].join(' ')).includes(term)));
   rendered=0;grid.replaceChildren();
   if(!matches.length){more.hidden=true;status.textContent='No hay fotografías con ese tema. Cambia los filtros o la búsqueda.'}
   else displayMore();
   for(const [name,button] of buttons){const active=current===name;
    button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active))}
  };
  for(const name of categories){
   const count=name==='Todas'?photos.length:photos.filter(p=>p.category===name).length;
   const b=el('button','',name+' ('+count+')');b.type='button';
   b.addEventListener('click',()=>{current=name;filter()});
   buttons.set(name,b);filterBar.append(b);
  }
  more.addEventListener('click',displayMore);
  search.addEventListener('input',filter);
  filter();
 }).catch(error=>{
   status.textContent='La fototeca no está disponible en este momento. '+error.message;
   grid.replaceChildren();
   const a=el('a','','Consultar los créditos publicados ↗');a.href='/creditos-fotograficos.html';grid.append(a);
 });
})();