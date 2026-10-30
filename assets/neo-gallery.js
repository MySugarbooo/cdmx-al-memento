'use strict';
/* Galería de fotografías originales del archivo del sitio, con atribución. */
(()=>{
 const out=document.getElementById('neo-photo-grid');if(!out)return;
 const status=document.getElementById('neo-photo-status');
 const note=(tag,text,klass)=>{const x=document.createElement(tag);x.textContent=text;if(klass)x.className=klass;return x};
 fetch('/assets/fotos-manifest.json',{cache:'force-cache'})
 .then(r=>{if(!r.ok)throw Error('sin archivo');return r.json()})
 .then(j=>{
  const list=(Array.isArray(j.photos)?j.photos:[]).filter(p=>p&&/^[a-z0-9_]{2,40}$/.test(p.id||'')&&typeof p.file==='string'&&typeof p.author==='string').slice(0,100);
  if(!list.length)throw Error('no hay fotos');
  out.replaceChildren();
  for(const p of list){
   const card=document.createElement('figure');card.className='neo-photo-card';
   const image=document.createElement('img');image.src='/assets/fotos/'+p.id+'.jpg';image.alt='Foto de archivo: '+String(p.topic||'Ciudad de México');image.loading='lazy';image.decoding='async';
   const caption=document.createElement('figcaption');
   const title=note('strong',p.topic||'Ciudad de México');
   const author=note('small','Autor: '+p.author+' · '+(p.license||'Licencia indicada por la fuente'));
   const link=document.createElement('a');link.href='https://commons.wikimedia.org/wiki/File:'+encodeURIComponent(p.file.replace(/ /g,'_'));
   link.rel='noopener noreferrer';link.target='_blank';link.textContent='Fuente y licencia ↗';
   caption.append(title,author,link);card.append(image,caption);out.append(card)
  }
  status.textContent=list.length+' fotografías de archivo acreditadas · Consulta los autores y las licencias.';
 }).catch(()=>{
  status.textContent='No se pudo cargar la galería en este momento.';
  const link=document.createElement('a');link.href='/creditos-fotograficos.html';link.textContent='Abrir los créditos fotográficos ↗';out.replaceChildren(link)
 });
})();
