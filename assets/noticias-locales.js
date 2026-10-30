'use strict';
/* Cada lectura permanece dentro de CDMX AL MEMENTO.
 * La fuente externa es una referencia opcional, no el destino de la tarjeta.
 */
(()=>{
 const $=id=>document.getElementById(id);
 const params=new URLSearchParams(location.search);
 const id=params.get('id')||'';
 const month=params.get('mes')||'';
 const title=$('local-story-title'),meta=$('local-story-meta'),intro=$('local-story-intro');
 const body=$('local-story-body'),figure=$('local-photo-wrap'),picture=$('local-story-photo');
 const caption=$('local-story-credit'),more=$('local-more-grid'),breadcrumb=$('local-breadcrumb');
 const cardWrap=$('local-more');
 const elem=(tag,cls,text)=>{
  const el=document.createElement(tag);
  if(cls)el.className=cls;
  if(text!==undefined)el.textContent=text;
  return el;
 };
 const dateFormat=new Intl.DateTimeFormat('es-MX',{
  timeZone:'America/Mexico_City',dateStyle:'full',timeStyle:'short'
 });
 function validArticle(x){
  return x&&typeof x.title==='string'&&typeof x.local_url==='string'&&
   /^\/noticias\/\?id=[a-f0-9]{20}&mes=\d{4}-\d{2}$/.test(x.local_url);
 }
 function publication(x){
  const d=new Date(x.published_at||'');
  return Number.isFinite(d.getTime())?dateFormat.format(d):x.date||'Fecha sin confirmar';
 }
 function safeExternal(url){
  try{const u=new URL(url);return u.protocol==='https:'&&
   (u.hostname==='news.google.com'||u.hostname==='commons.wikimedia.org');}
  catch{return false;}
 }
 function representativePhoto(x){
  const api=window.CDMX_FOTOS;
  if(api?.ready&&typeof api.forArticle==='function'){
   const id=api.forArticle(x),item=api.images?.[id];
   if(item&&item.author&&item.license&&item.source&&item.url)return {...item,kind:'representativa'};
  }
  const stored=x?.photo;
  return stored&&stored.kind!=='hecho'&&stored.author&&stored.license&&stored.source?{...stored,kind:'representativa'}:null;
 }
 function selectedPhoto(x){
  const exact=x?.photo;
  // El registro editorial aprobado tiene prioridad sobre la fototeca de contexto.
  if(exact?.kind==='hecho'&&exact.verified===true&&exact.author&&exact.license&&exact.source&&exact.licenseUrl&&exact.evidence_url)return exact;
  return representativePhoto(x);
 }
 function photo(x,small=false){
  const info=selectedPhoto(x);
  if(!info||!info.url||!/^\/assets\/(?:fotos|alcaldias)\/[a-z0-9_-]+\.jpg$/.test(info.url)&&
    !/^https:\/\/(?:thumb|upload)\.wikimedia\.org\/wikipedia\/commons\//.test(info.url))return null;
  const img=elem('img');
  img.src=info.url;img.loading=small?'lazy':'eager';img.decoding='async';
  img.width=small?480:1200;img.height=small?300:750;
  img.alt=info.kind==='hecho'&&info.verified===true?'Fotografía verificada del acontecimiento: '+(info.topic||x.title):'Imagen representativa: '+(info.topic||'Ciudad de México')+'. No constituye evidencia del acontecimiento.';
  let retried=false;
  img.addEventListener('error',()=>{
   if(retried){img.hidden=true;return}
   retried=true;
   const alternate=info.kind==='hecho'?representativePhoto(x):null;
   if(alternate&&alternate.url&&alternate.url!==info.url){
    img.src=alternate.url;
    img.alt='Imagen representativa; no corresponde necesariamente al hecho descrito.';
   }else img.hidden=true;
  });
  return img;
 }
 function addText(container,heading,content){
  const h=elem('h2','',heading),p=elem('p','',content);
  container.append(h,p);
 }
 function storyCard(x){
  const card=elem('a','explore-card');
  const match=/^\/noticias\/\?id=([a-f0-9]{20})&mes=\d{4}-\d{2}$/.exec(x.local_url||'');
  card.href=match?'/articulos/'+match[1]+'/':x.local_url;
  const image=photo(x,true);if(image)card.append(image);
  const text=elem('span','explore-card-body');
  text.append(elem('span','explore-tag',x.category||'CDMX'),
    elem('strong','',x.title),
    elem('small','',x.brief?.lead||'Consulta nuestra nota con fuente y contexto.'));
  card.append(text);return card;
 }
 function renderList(items){
  title.textContent='Noticias de CDMX: elige una lectura';
  breadcrumb.textContent='Titulares locales';
  meta.textContent='Todos los resúmenes se pueden leer sin salir del sitio.';
  intro.textContent='Selecciona una noticia. Encontrarás una síntesis redactada para CDMX AL MEMENTO, su fuente, la firma editorial y una fotografía de contexto con créditos.';
  body.replaceChildren();
  if(figure)figure.hidden=true;
  if(cardWrap)cardWrap.hidden=false;
  if(more){more.replaceChildren();for(const x of items.filter(validArticle))more.append(storyCard(x));}
 }
 function addVerification(article,updated){
  const section=elem('section','local-verification');
  section.setAttribute('aria-label','Ficha de verificación y procedencia');
  section.append(elem('h2','','Ficha de verificación'));
  section.append(elem('p','local-verification-state','Referencia periodística identificada · Verificación independiente pendiente'));
  const data=elem('dl','local-verification-data');
  function field(label,value){
   const pair=elem('div','local-verification-field');
   pair.append(elem('dt','',label),elem('dd','',String(value||'No informado')));
   data.append(pair);
  }
  field('Información disponible','Titular y metadatos de un medio identificado; no equivale a confirmar los hechos relatados.');
  field('Medio de origen',article.source||'No indicado');
  field('Fecha del medio',publication(article));
  field('Archivo actualizado',updated||'Fecha de actualización no informada');
  field('Alcaldía',article.borough?article.borough+' (mencionada en el titular, no ubicación comprobada)':'Sin alcaldía confirmada');
  section.append(data);
  section.append(elem('p','local-verification-method',article.brief?.method||
   'Síntesis preparada a partir del título y metadatos disponibles.'));
  if(safeExternal(article.url)){
   const source=elem('a','local-verification-source','Consultar la fuente original');
   source.href=article.url;source.target='_blank';source.rel='noopener noreferrer nofollow';
   section.append(source);
  }
  body.append(section);
 }
 let activeArticle=null;
 function renderArticle(article,items,updated){
  activeArticle={article,items,updated};
  title.textContent=article.title;
  breadcrumb.textContent=article.category||'Noticia local';
  document.title=article.title.slice(0,65)+' | CDMX AL MEMENTO';
  // Metadatos específicos de cada noticia, sin modificar el diseño visible.
  const description=(article.brief?.lead||'Noticia de Ciudad de México con fuentes y contexto editorial.').slice(0,155);
  const descriptionTag=document.querySelector('meta[name="description"]');
  if(descriptionTag)descriptionTag.setAttribute('content',description);
  const canonicalTag=document.querySelector('link[rel="canonical"]');
  if(canonicalTag&&validArticle(article))canonicalTag.href=new URL('/articulos/'+id+'/',location.origin).href;
  const ogTitle=document.querySelector('meta[property="og:title"]');
  if(ogTitle)ogTitle.setAttribute('content',article.title);
  const ogDescription=document.querySelector('meta[property="og:description"]');
  if(ogDescription)ogDescription.setAttribute('content',description);
  meta.textContent=(article.category||'CDMX')+' · '+publication(article)+
   ' · Fuente identificada: '+(article.source||'Medio de origen')+
   (article.borough?' · Alcaldía mencionada: '+article.borough:'');
  intro.textContent=article.brief?.lead||'La publicación citada aborda el tema del encabezado; el índice disponible no permite confirmar más detalles.';
  body.replaceChildren();
  addVerification(article,updated);
  addText(body,'Por qué importa',article.brief?.context||'La noticia puede ser relevante para quienes viven y trabajan en la Ciudad de México.');
  addText(body,'Qué falta por confirmar',article.brief?.pending||'Los hechos y los cambios posteriores requieren fuentes actualizadas.');
  const editorial=elem('section','local-story-editorial');
  editorial.append(elem('h2','','Nota de Amau Kisumi'),
    elem('p','','Nuestro compromiso es informar con empatía y claridad: distinguimos lo que dice una fuente de lo que aún está pendiente de confirmar. No afirmamos haber hecho entrevistas ni haber visto imágenes del suceso.'));
  body.append(editorial);
  const source=elem('section','local-story-sources');
  source.append(elem('h2','','Fuentes y método'),
   elem('p','',article.brief?.method||'Esta nota se ha elaborado a partir del título y la fecha del medio citado.'));
  const pub=elem('p','', 'Medio de origen: '+(article.source||'Fuente periodística')+
   '. Fecha de publicación comunicada por el medio: '+publication(article)+'.');
  source.append(pub);
  if(safeExternal(article.url)){
   const ref=elem('a','local-source-link','Consultar la fuente original (opcional) ↗');
   ref.href=article.url;ref.target='_blank';ref.rel='noopener noreferrer nofollow';
   source.append(ref);
  }
  body.append(source);
  const img=photo(article);
  if(img&&figure){
   picture.src=img.src;picture.alt=img.alt;picture.hidden=false;figure.hidden=false;
   const rights=selectedPhoto(article)||{};
   picture.onerror=()=>{
    const alternate=rights.kind==='hecho'?representativePhoto(article):null;
    if(!alternate||!alternate.url||alternate.url===rights.url){figure.hidden=true;return}
    picture.onerror=()=>{figure.hidden=true};
    picture.src=alternate.url;
    picture.alt='Imagen representativa del tema; no documenta el acontecimiento.';
    caption.replaceChildren(document.createTextNode('Imagen representativa del tema, no corresponde necesariamente al hecho · Autor: '+
     alternate.author+' · '+alternate.license+' · '));
    if(safeExternal(alternate.source)){
     const link=elem('a','','Obra y autor ↗');link.href=alternate.source;link.target='_blank';link.rel='noopener noreferrer';caption.append(link);
    }
   };
   caption.replaceChildren();
   const label=rights.kind==='hecho'&&rights.verified===true?'Fotografía verificada del acontecimiento: ':'Imagen representativa; no corresponde necesariamente al hecho descrito: ';
   caption.append(document.createTextNode(label+(rights.topic||'CDMX')+
    ' · Autor: '+(rights.author||'Fuente original')+
    ' · '+(rights.license||'Licencia en la fuente')+' · '));
   if(safeExternal(rights.source)){
    const origin=elem('a','','Obra y autor ↗');
    origin.href=rights.source;origin.target='_blank';origin.rel='noopener noreferrer';
    caption.append(origin);
   }
   if(/^https?:\/\/creativecommons\.org\//.test(rights.licenseUrl||'')){
    const l=elem('a','',' · Licencia y condiciones ↗');l.href=rights.licenseUrl;
    l.target='_blank';l.rel='noopener noreferrer';caption.append(l);
   }
  }else if(figure)figure.hidden=true;
  more?.replaceChildren();
  if(cardWrap)cardWrap.hidden=false;
  for(const other of items.filter(x=>validArticle(x)&&x.local_url!==article.local_url).slice(0,4)){
   more?.append(storyCard(other));
  }
 }
 document.addEventListener('cdmx-fotos-ready',()=>{if(activeArticle)renderArticle(activeArticle.article,activeArticle.items,activeArticle.updated)});
 const requested=/^[a-f0-9]{20}$/.test(id)&&/^\d{4}-\d{2}$/.test(month);
 const monthURL=requested?'/archivo/'+month+'.json':null;
 async function readJSON(path){
  const r=await fetch(path,{cache:'no-store'});
  if(!r.ok)throw new Error('Catálogo no disponible');return r.json();
 }
 readJSON('/news.json?t='+Date.now()).then(async current=>{
  const recent=Array.isArray(current.articles)?current.articles.filter(validArticle):[];
  if(!requested){renderList(recent);return;}
  let found=recent.find(x=>x.local_url===('/noticias/?id='+id+'&mes='+month));
  if(found){renderArticle(found,recent,current.updated);return;}
  const archive=await readJSON(monthURL);
  const all=Array.isArray(archive.articles)?archive.articles.filter(validArticle):[];
  found=all.find(x=>x.local_url===('/noticias/?id='+id+'&mes='+month));
  if(found){renderArticle(found,all,archive.updated);return;}
  title.textContent='No encontramos esta noticia en el archivo';
  intro.textContent='Es posible que haya vencido el periodo de conservación del periódico. Explora los titulares que siguen disponibles.';
  renderList(recent);
 }).catch(()=>{
  title.textContent='No pudimos cargar la noticia';
  meta.textContent='Conexión no disponible';
  intro.textContent='Inténtalo de nuevo más tarde. No te enviaremos automáticamente a otro sitio.';
 });
})();
