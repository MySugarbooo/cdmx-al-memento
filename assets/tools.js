'use strict';
(() => {
const root=document.getElementById('text-tool');if(!root)return;
const id=root.dataset.tool,input=document.getElementById('input-text'),input2=document.getElementById('input-text-2'),output=document.getElementById('output-text'),extra=document.getElementById('result-stats'),status=document.getElementById('tool-status'),opts=document.getElementById('options');
const textLimits=50000;
const graphemes=s=>{if(Intl.Segmenter){return [...new Intl.Segmenter('es',{granularity:'grapheme'}).segment(s)].length}return [...s].length};
const words=s=>s.match(/[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*/gu)||[];
const collapse=s=>s.replace(/\r\n?/g,'\n');
const locale=(a,b)=>a.localeCompare(b,'es',{sensitivity:'base',numeric:true});
const getOpt=name=>opts?opts.querySelector('[name="'+name+'"]'):null;
const opt=name=>getOpt(name)?.value||'';
const checked=name=>Boolean(getOpt(name)?.checked);
function work(s,t){
const lines=collapse(s).split('\n'),trim=s.trim(),w=words(s);
switch(id){
case 'contar-palabras': {
 const count=w.length, chars=graphemes(s), noSpace=graphemes(s.replace(/\s/gu,'')), paras=collapse(s).split(/\n\s*\n/).filter(x=>x.trim()).length;
 const sentences=(trim.match(/[.!?]+(?:["'»”)\]]*)?(?=\s|$)/g)||[]).length;
 return {result:s,stats:count+' palabras · '+chars+' caracteres · '+noSpace+' sin espacios · '+paras+' párrafos · '+sentences+' frases detectadas · ~'+Math.max(1,Math.ceil(count/210))+' min de lectura'};
}
case 'cambiar-mayusculas': {
 let out=s,mode=opt('modo');
 if(mode==='upper')out=s.toLocaleUpperCase('es-MX');
 else if(mode==='lower')out=s.toLocaleLowerCase('es-MX');
 else if(mode==='title')out=s.toLocaleLowerCase('es-MX').replace(/(^|[\s([{"'«¿¡])([\p{L}])/gu,(m,a,b)=>a+b.toLocaleUpperCase('es-MX'));
 else if(mode==='sentence')out=s.toLocaleLowerCase('es-MX').replace(/(^|[.!?]\s+|[¿¡])([\p{L}])/gu,(m,a,b)=>a+b.toLocaleUpperCase('es-MX'));
 return {result:out,stats:graphemes(out)+' caracteres · Conversión automática: revisa nombres propios y siglas'};
}
case 'limpiar-espacios': {
 const mode=opt('limpieza');let out=collapse(s);
 if(mode==='lines')out=out.split('\n').map(x=>x.trim().replace(/[ \t]+/g,' ')).join('\n').replace(/\n{3,}/g,'\n\n').trim();
 else if(mode==='blank')out=out.split('\n').filter(x=>x.trim()!=='').join('\n');
 else if(mode==='one')out=out.trim().replace(/\s+/g,' ');
 else out=out.split('\n').map(x=>x.replace(/[ \t]+$/g,'')).join('\n').trim();
 return {result:out,stats:(graphemes(s)-graphemes(out))+' caracteres de diferencia'};
}
case 'quitar-duplicados': {
 const seen=new Set();let removed=0;
 const out=lines.filter(line=>{const key=checked('ignorar')?line.trim().toLocaleLowerCase('es-MX'):line.trim();if(key===''&&checked('vacias'))return false;if(seen.has(key)){removed++;return false}seen.add(key);return true});
 return {result:out.join('\n'),stats:removed+' líneas repetidas eliminadas · '+out.length+' líneas conservadas'};
}
case 'ordenar-lineas': {
 const nonempty=lines.filter(x=>x.trim()!=='');
 nonempty.sort((a,b)=>locale(a.trim(),b.trim())*(opt('orden')==='desc'?-1:1));
 return {result:nonempty.join('\n'),stats:nonempty.length+' líneas ordenadas alfabéticamente en español'};
}
case 'comparar-textos': {
 const A=collapse(s).split('\n'),B=collapse(t).split('\n');
 const left=new Map(),right=new Map();for(const x of A)left.set(x,(left.get(x)||0)+1);for(const x of B)right.set(x,(right.get(x)||0)+1);
 const gone=[],added=[];for(const [line,n] of left){for(let k=0;k<Math.max(0,n-(right.get(line)||0));k++)gone.push('− '+line)}
 for(const [line,n] of right){for(let k=0;k<Math.max(0,n-(left.get(line)||0));k++)added.push('+ '+line)}
 const identical=s===t;const result=identical?'Los textos son idénticos.':[...gone,...added].join('\n')||'Los textos contienen las mismas líneas, pero su orden cambió.';
 return {result,stats:gone.length+' líneas eliminadas · '+added.length+' añadidas · '+(identical?'Textos idénticos':'Comparación por líneas, sin interpretar cambios internos')};
}
case 'extraer-correos': {
 const raw=s.match(/[A-Z0-9._%+-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+/gi)||[];
 const map=new Map();for(const mail of raw){const value=mail.replace(/[.,;:!?]+$/,'');const key=value.toLocaleLowerCase('en-US');if(!map.has(key))map.set(key,value)}
 const out=[...map.values()];
 return {result:out.join('\n'),stats:out.length+' direcciones con formato de correo detectadas · No se verifica si existen'};
}
case 'crear-enlace': {
 const out=s.normalize('NFD').replace(/\p{M}/gu,'').toLocaleLowerCase('es-MX').replace(/ñ/g,'n').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,120).replace(/-$/,'');
 return {result:out,stats:out.length+' caracteres · Identificador sugerido para una URL'};
}
case 'formatear-lista': {
 const arr=lines.map(x=>x.trim()).filter(Boolean),style=opt('estilo');
 const out=arr.map((x,i)=>style==='numbers'?(i+1)+'. '+x:style==='checks'?'- [ ] '+x:'• '+x);
 return {result:out.join('\n'),stats:out.length+' elementos formateados'};
}
case 'frecuencia-palabras': {
 const list=words(s.toLocaleLowerCase('es-MX'));
 const stop=new Set('de la el los las y o un una uno unas unos para por con en a al del se que lo su sus es son no si como más muy esta este estos estas mi tu yo me te hay ser fue han ha pero le les entre sobre sin desde hasta ya'.split(' '));
 const hist=new Map();for(const raw of list){const w=raw.replace(/^['’-]+|['’-]+$/g,'');if(w.length<=1||(checked('stopwords')&&stop.has(w)))continue;hist.set(w,(hist.get(w)||0)+1)}
 const ordered=[...hist.entries()].sort((a,b)=>b[1]-a[1]||locale(a[0],b[0])).slice(0,40);
 return {result:ordered.map(([w,n])=>w+': '+n).join('\n'),stats:list.length+' palabras totales · '+hist.size+' palabras distintas · Top 40 mostrado'};
}
default:return{result:s,stats:'Herramienta no disponible'};
}
}
function update(){
 try{
 const s=input?.value||'',t=input2?.value||'';
 if(s.length>textLimits||t.length>textLimits){output.value='';extra.textContent='Límite: 50,000 caracteres por campo.';return}
 const r=work(s,t);output.value=r.result;extra.textContent=r.stats;status.textContent='Resultado actualizado. Todo se procesa en tu navegador.';
 }catch(e){output.value='';extra.textContent='No se pudo procesar el texto';status.textContent='Revisa los datos e inténtalo nuevamente.'}
}
root.addEventListener('input',update);root.addEventListener('change',update);
document.getElementById('copy-result')?.addEventListener('click',async()=>{
 if(!output.value){status.textContent='No hay contenido para copiar.';return}
 try{await navigator.clipboard.writeText(output.value);status.textContent='Resultado copiado al portapapeles.'}catch{output.focus();output.select();status.textContent='Seleccioné el resultado. Presiona Ctrl+C para copiarlo.'}
});
document.getElementById('clear-input')?.addEventListener('click',()=>{
 if(input)input.value='';if(input2)input2.value='';update();input?.focus();
});
update();
})();
