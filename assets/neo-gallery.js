'use strict';
/* Galería editorial: exactamente 100 imágenes con atribución individual y fuente. */
(()=>{
 const grid=document.getElementById('neo-photo-grid'),status=document.getElementById('neo-photo-status');
 if(!grid||!status)return;
 const safeImage=u=>/^\/assets\/fotos\/[a-z0-9_]+\.jpg$/i.test(u)||/^https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons\//.test(u);
 const safeCommons=u=>/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(u);
 const safeLicense=u=>/^https?:\/\/creativecommons\.org\//.test(u);
 const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
 fetch('/assets/fotos/seleccion-100.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
 .then(data=>{
  const photos=(Array.isArray(data.photos)?data.photos:[]).filter(p=>p&&safeImage(p.url)&&safeCommons(p.source)&&safeLicense(p.licenseUrl)&&p.author&&p.license).slice(0,100);
  if(!photos.length)throw Error('Galería sin archivos acreditados');
  const controls=el('div','neo-photo-filters');
  const categories=['Todas',...new Set(photos.map(p=>p.category))];
  const buttons=new Map();
  const show=category=>{
   for(const [name,button] of buttons){const active=name===category;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active))}
   grid.replaceChildren();
   for(const p of photos){
    if(category!=='Todas'&&p.category!==category)continue;
    const figure=el('figure','neo-photo-card'),img=el('img'),caption=el('figcaption');
    img.src=p.url;img.loading='lazy';img.decoding='async';img.alt='Fotografía de archivo: '+p.topic;
    img.onerror=()=>{img.onerror=null;img.hidden=true;figure.classList.add('neo-photo-unavailable');figure.prepend(el('p','neo-photo-error','Imagen temporalmente no disponible. Consulta la fuente original.'))};
    const categoryTag=el('span','neo-photo-category',p.category);
    const title=el('strong','',p.topic);
    const author=el('small','','Fotografía: '+p.author+' · '+p.license);
    const links=el('div','neo-photo-links');
    const origin=el('a','','Obra y autor ↗');origin.href=p.source;origin.rel='noopener noreferrer';origin.target='_blank';
    const license=el('a','','Licencia y condiciones ↗');license.href=p.licenseUrl;license.rel='noopener noreferrer';license.target='_blank';
    links.append(origin,license);
    const note=el('small','neo-photo-warning','Imagen de archivo; no documenta necesariamente una noticia.');
    caption.append(categoryTag,title,author,links,note);
    figure.append(img,caption);grid.append(figure);
   }
   status.textContent=grid.childElementCount+' de '+photos.length+' fotografías con autor, fuente y licencia individual.';
  };
  for(const name of categories){const n=photos.filter(p=>p.category===name).length;const button=el('button','',''+name+' ('+(name==='Todas'?photos.length:n)+')');button.type='button';button.setAttribute('aria-pressed','false');button.addEventListener('click',()=>show(name));buttons.set(name,button);controls.append(button)}
  grid.before(controls);show('Todas');
 }).catch(err=>{status.textContent='No se pudo cargar la fototeca: '+err.message;grid.replaceChildren();const a=el('a','','Consultar créditos existentes ↗');a.href='/creditos-fotograficos.html';grid.append(a)});
})();