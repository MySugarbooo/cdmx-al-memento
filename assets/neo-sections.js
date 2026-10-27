'use strict';
/* Historias reales para páginas de Seguridad y Servicios.
   No inserta HTML no fiable ni genera métricas de ejemplo.
*/
(()=>{
 const grid=document.getElementById('neo-section-stories');
 if(!grid)return;
 const category=grid.dataset.newsCategory;
 const status=document.getElementById('neo-section-status');
 const fallback={'Seguridad':'/assets/fotos/seguridad.jpg','Gobierno':'/assets/fotos/gobierno.jpg'};
 const date=new Intl.DateTimeFormat('es-MX',{dateStyle:'medium',timeZone:'America/Mexico_City'});
 const escapeDate=value=>{const d=new Date(value);return Number.isFinite(d.getTime())?date.format(d):'Fecha no confirmada'};
 function node(tag,text,klass){const el=document.createElement(tag);if(klass)el.className=klass;if(text!==undefined)el.textContent=text;return el}
 const validPhoto=url=>typeof url==='string'&&/^\/assets\/fotos\/[a-z0-9_-]+\.jpe?g$/i.test(url);
 fetch('/news.json?site=sections-'+Date.now(),{cache:'no-store'})
 .then(r=>{if(!r.ok)throw Error('Sin conexión');return r.json()})
 .then(feed=>{
  const articles=(Array.isArray(feed.articles)?feed.articles:[])
    .filter(a=>a&&a.category===category&&typeof a.title==='string'
      &&/^https:\/\/news\.google\.com\//.test(a.url||'')
      &&/^\/noticias\/\?/.test(a.local_url||''))
    .slice(0,8);
  grid.replaceChildren();
  if(!articles.length){
    status.textContent='No hay titulares de esta categoría disponibles por ahora.';
    const a=node('a','Explorar todas las noticias →');a.href='/archivo/';grid.append(a);return;
  }
  for(const article of articles){
   const card=node('article',undefined,'neo-section-story');
   const image=node('img');
   image.src=validPhoto(article.photo?.url)?article.photo.url:fallback[category]||'/assets/fotos/reforma.jpg';
   image.alt='Fotografía de archivo relacionada con '+category;
   image.loading='lazy';image.decoding='async';
   image.onerror=()=>{image.onerror=null;image.src=fallback[category]||'/assets/fotos/reforma.jpg'};
   const h=node('h3');const link=node('a',article.title);link.href=article.local_url;h.append(link);
   const info=node('p',(article.source||'Medio externo')+' · '+escapeDate(article.published_at||article.date));
   const caption=node('p','Fotografía de archivo, no necesariamente del suceso.');
   card.append(image,h,info,caption);grid.append(card);
  }
  status.textContent=articles.length+' noticias de '+category.toLowerCase()+' · Titulares de medios identificados';
 }).catch(()=>{
  if(status)status.textContent='No se pudieron actualizar los titulares. Consulta el archivo de noticias.';
  grid.replaceChildren();const a=node('a','Abrir archivo mensual →');a.href='/archivo/';grid.append(a);
 });
})();
