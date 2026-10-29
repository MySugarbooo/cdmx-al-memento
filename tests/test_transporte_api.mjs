// Sin red: pruebas del parser de la página oficial de incidentes de CDMX.
// El import vía data: URL evita depender del tipo de módulo del repositorio.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../functions/api/estado-transporte.js',import.meta.url),'utf8');
const {parseRows,rowCount,viewState,rowsValid,partialFragment}=await import(
 'data:text/javascript;base64,'+Buffer.from(source).toString('base64')
);
function record(system,line,index,state='Servicio Regular',detail=''){
 const icon=(system==='stc'?'stc':'MB')+line;
 return `<tr data-ri="${index}" class="ui-widget-content"><td><img src="/jakarta.faces.resource/img/iconos/lineas/${icon}.${system==='stc'?'svg':'png'}.xhtml"/></td><td>${state}</td><td>Ninguna</td><td>${detail}</td></tr>`;
}
const stc=['1','2','3','4','5','6','7','8','9','12','A','B'];
const page1=stc.slice(0,10).map((line,i)=>record('stc',line,i)).join('');
const page2=stc.slice(10).map((line,i)=>record('stc',line,i+10)).join('');
const initial=`<html><form><input type="hidden" name="jakarta.faces.ViewState" value="xyzABC:123"/></form><table>${page1}</table><script>PrimeFaces.cw("DataTable","widget_frmEstadoServicio_tblEstadoServicio",{paginator:{rows:10,rowCount:12,page:0}});</script></html>`;
assert.equal(rowCount(initial),12);
assert.equal(viewState(initial),'xyzABC:123');
const metro1=parseRows(initial,'stc');
const ajax=`<partial-response><changes><update id="frmEstadoServicio:tblEstadoServicio"><![CDATA[${page2}]]></update></changes></partial-response>`;
const fragment=partialFragment(ajax);
assert.ok(fragment);
const metro=[...metro1,...parseRows(fragment,'stc')];
assert.equal(metro.length,12);
assert.ok(rowsValid(metro,'stc',12),'La paginación incluye A y B');
assert.ok(!rowsValid(metro1,'stc',12),'No publicar diez líneas como doce');
assert.equal(metro.at(-2).linea,'A');
assert.equal(metro.at(-1).linea,'B');
assert.equal(parseRows(record('mb','2',0,'Retraso en el servicio','Marcha lenta'), 'mb')[0].regular,false);
assert.equal(parseRows(record('mb','2',0,'Retraso en el servicio','Marcha lenta'), 'mb')[0].informacion_adicional,'Marcha lenta');
assert.equal(parseRows(record('mb','5',0), 'mb')[0].linea,'5');
assert.equal(parseRows(record('stc','1',0,'Servicio Regular','Sin novedades'), 'stc')[0].estado,'Servicio Regular');
assert.throws(()=>parseRows(record('stc','999',0),'stc'));
assert.equal(partialFragment('<error>No hay datos</error>'),null);
const duplicate=[...metro,parseRows(record('stc','1',12,'Retraso en el servicio'),'stc')[0]];
assert.ok(rowsValid(duplicate,'stc',13),'Conservar dos incidencias en la misma línea');
console.log('Estado de transporte API: parser y paginación pasaron 13 comprobaciones sin red.');
