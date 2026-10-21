(() => {
  const root=document.querySelector('[data-site-likes]');
  const strip=document.createElement('section');
  strip.className='engagement-visitors';
  const label=document.createElement('span'); label.textContent='Visitantes de CDMX AL MEMENTO';
  const value=document.createElement('strong'); value.textContent='—';
  const note=document.createElement('small'); note.textContent='Visitantes aproximados por navegador desde la activación del contador.';
  strip.append(label,value,note);
  if(root)root.after(strip);else document.querySelector('main')?.prepend(strip);
  async function request(article,body) {
    const url='/api/engagement'+(article?'?article='+encodeURIComponent(article):'');
    const response=await fetch(url,{method:body?'POST':'GET',credentials:'same-origin',cache:'no-store',
      headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});
    if(!response.ok)throw Error('Sin conexión');
    return response.json();
  }
  request('',{action:'visit'}).then(d=>value.textContent=d.visitors.toLocaleString('es-MX'))
    .catch(()=>value.textContent='No disponible');
  window.CDMX_addArticleLike=(card,article)=>{
    const id=article.local_url||article.url;
    if(!id||id.length>220)return;
    const button=document.createElement('button');
    button.className='article-like';button.type='button';button.disabled=true;
    button.textContent='♡ Me gusta · —';
    (card.querySelector('.inside')||card).append(button);
    let liked=false,working=false;
    function show(data) {
      liked=data.liked;button.disabled=false;
      button.setAttribute('aria-pressed',String(liked));
      button.textContent=(liked?'♥ Te gusta':'♡ Me gusta')+' · '+data.likes.toLocaleString('es-MX');
    }
    request(id).then(show).catch(()=>button.textContent='Me gusta no disponible');
    button.addEventListener('click',async()=>{
      if(working)return;working=true;button.disabled=true;
      try{show(await request(id,{action:'like',liked:!liked}));}
      catch{button.textContent='Error; recarga para intentar otra vez';}
      finally{working=false;}
    });
  };
})();