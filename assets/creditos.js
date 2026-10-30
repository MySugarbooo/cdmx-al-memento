'use strict';
/* Consulta escalonada de atribuciones: 1,100 fichas sin crear 1,100 nodos iniciales. */
(()=>{
 const holder=document.getElementById('extra-photo-credits');
 if(!holder)return;
 const el=(tag,text,cls)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node};
 const link=(txt,url)=>{const a=el('a',txt);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a};
 const fold=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const validSource=u=>/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(String(u||''));
 const validLicense=u=>/^https:\/\/creativecommons\.org\//.test(String(u||''));
 const notice='Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.';
 fetch('/assets/fotos/catalogo-editorial-1100.json',{cache:'no-cache'})
 .then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
 .then(data=>{
  const photos=(data.photos||[]).filter(p=>p&&p.author&&p.license&&validSource(p.source)&&validLicense(p.licenseUrl));
  if(photos.length<901||photos.length!==data.count)throw Error('Catálogo incompleto');
  const controls=el('div',undefined,'credits-controls');
  const search=el('input');search.type='search';search.placeholder='Filtrar por autor, tema o alcaldía';
  search.setAttribute('aria-label','Buscar los derechos y créditos fotográficos');
  const total=el('p','Catálogo de '+photos.length+' imágenes con autor y licencia individual.');
  controls.append(search,total);holder.before(controls);
  const more=el('button','Ver 50 créditos más','credits-more');
  more.type='button';holder.after(more);
  const limit=50;let filtered=photos.slice(),offset=0;
  const showMore=()=>{
    const fragment=document.createDocumentFragment();
    for(const p of filtered.slice(offset,offset+limit)){
      const card=el('section',undefined,'credit-row');
      const title=el('h3',p.topic||p.file||'Imagen de archivo');
      const info=el('p','Autor: '+p.author+' · '+p.license);
      const refs=el('p');
      refs.append(link('Archivo original y autor ↗',p.source),document.createTextNode(' · '),link('Condiciones de la licencia ↗',p.licenseUrl));
      const desc=el('p',notice);
      if(p.adaptation)desc.append(document.createTextNode(' '+p.adaptation));
      card.append(title,info,refs,desc);fragment.append(card);
    }
    holder.append(fragment);offset=Math.min(filtered.length,offset+limit);
    more.hidden=offset>=filtered.length;
    total.textContent='Mostrando '+offset+' de '+filtered.length+' resultados · Biblioteca completa: '+photos.length+' imágenes.';
  };
  function searchAgain(){
   const q=fold(search.value.trim());filtered=q?photos.filter(p=>fold([p.topic,p.file,p.author,p.category,...(p.keywords||[])].join(' ')).includes(q)):photos;
   holder.replaceChildren();offset=0;
   if(!filtered.length){more.hidden=true;total.textContent='No se encontraron imágenes con ese término.'}else showMore();
  }
  more.addEventListener('click',showMore);search.addEventListener('input',searchAgain);searchAgain();
 }).catch(error=>{
  holder.replaceChildren(el('p','No se pudo consultar la biblioteca ampliada: '+error.message));
 });
})();