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
 const validPhoto=url=>typeof url==='string'&&(
    /^\/assets\/(?:fotos|alcaldias)\/[a-z0-9_-]+\.jpe?g$/i.test(url)||
    /^https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons\//.test(url));
 const safeCredits=url=>/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(String(url||''));
 const notice='Imagen de carácter ilustrativo y referencial; no constituye evidencia gráfica de los hechos descritos.';
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
   const photo=article.photo||{};
   const usable=validPhoto(photo.url);
   image.src=usable?photo.url:fallback[category]||'/assets/fotos/reforma.jpg';
   image.alt='Imagen ilustrativa y referencial sobre '+category+'. No constituye evidencia gráfica del hecho.';
   image.loading='lazy';image.decoding='async';
   image.onerror=()=>{
    image.onerror=null;
    image.src=fallback[category]||'/assets/fotos/reforma.jpg';
    const shownCredit=card.querySelector('.neo-photo-attribution');
    if(shownCredit)shownCredit.textContent=notice+' · Imagen de recurso editorial. Consulta los créditos de la fototeca.';
   };
   const h=node('h3');const link=node('a',article.title);link.href=article.local_url;h.append(link);
   const info=node('p',(article.source||'Medio externo')+' · '+escapeDate(article.published_at||article.date));
   const caption=node('p',notice,'neo-photo-attribution');
   if(usable&&photo.author&&photo.license&&safeCredits(photo.source)){
    caption.append(document.createTextNode(' · Autor: '+photo.author+' · '+photo.license+' · '));
    const credit=node('a','Fuente y licencia ↗');credit.href=photo.source;
    credit.target='_blank';credit.rel='noopener noreferrer';caption.append(credit);
   }else{
    caption.append(document.createTextNode(' · '));
    const link=node('a','Créditos fotográficos ↗');link.href='/creditos-fotograficos.html';caption.append(link);
   }
   card.append(image,h,info,caption);grid.append(card);
  }
  status.textContent=articles.length+' noticias de '+category.toLowerCase()+' · Titulares de medios identificados';
 }).catch(()=>{
  if(status)status.textContent='No se pudieron actualizar los titulares. Consulta el archivo de noticias.';
  grid.replaceChildren();const a=node('a','Abrir archivo mensual →');a.href='/archivo/';grid.append(a);
 });
})();
