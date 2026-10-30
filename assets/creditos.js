'use strict';
(function(){
 const holder=document.getElementById('extra-photo-credits');
 if(!holder)return;
 function el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n}
 function link(text,url){const a=el('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a}
 fetch('/assets/fotos/seleccion-100.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('not yet');return r.json()}).then(data=>{
  holder.replaceChildren();
  if(!Array.isArray(data.photos)||!data.photos.length){
   holder.append(el('p','La colección se está preparando. Las fotografías iniciales y sus créditos están arriba.'));return;
  }
  for(const p of data.photos){
   const card=el('section');card.className='credit-row';
   const title=el('h3',p.topic||p.file||'Fotografía de archivo');
   const info=el('p',(p.author||'Autor no verificado')+' · '+(p.license||'Licencia en origen'));
   const refs=el('p');
   if(/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(p.source||''))refs.append(link('Ver foto y autor ↗',p.source));
   if(/^https:\/\/creativecommons\.org\//.test(p.licenseUrl||'')){
    refs.append(document.createTextNode(' · '),link('Ver licencia ↗',p.licenseUrl));
   }
   card.append(title,info,refs);holder.append(card);
  }
 }).catch(()=>{
  holder.replaceChildren(el('p','Las fotografías adicionales se están incorporando. Vuelve a consultar esta sección cuando termine la actualización.'));
 });
})();
