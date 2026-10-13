'use strict';(()=>{
 const field=document.getElementById('explore-borough-search');
 const grid=document.getElementById('explore-borough-grid');
 const status=document.getElementById('explore-borough-count');
 if(!field||!grid||!status)return;
 const rows=[...grid.querySelectorAll('.explore-card')];
 const clean=s=>(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
 field.addEventListener('input',()=>{
  let count=0;const q=clean(field.value.trim());
  for(const row of rows){const show=clean(row.textContent).includes(q);row.hidden=!show;if(show)count++;}
  status.textContent=count?count+' guías de alcaldía encontradas.':'No encontramos esa alcaldía. Prueba con otro nombre.';
 });
})();