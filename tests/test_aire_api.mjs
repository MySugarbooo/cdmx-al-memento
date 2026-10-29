/* Pruebas sin internet: calidad del aire oficial y boletines CAMe.
 * Nunca se convierte un dato antiguo en un índice actual.
 */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const importSource=async relative=>{
 const source=await readFile(new URL(relative,import.meta.url),'utf8');
 return import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
};
const air=await importSource('../functions/api/aire.js');
const came=await importSource('../functions/api/contingencias.js');
const now=Date.parse('2026-10-29T14:32:00Z');
const official=`<body><p>08:00 h, jueves 29 de octubre de 2026</p>
<p>13 °C</p><p>Índice AIRE Y SALUD: <strong>ACEPTABLE</strong></p>
<p>Contaminante(s): PM<sub>2.5</sub></p>
<p>Riesgo: MODERADO</p>
<table><tr><td>Cuauhtémoc</td><td></td></tr></table></body>`;
const got=air.parseAirReport(official,now);
assert.equal(got.category,'ACEPTABLE');
assert.equal(got.risk,'MODERADO');
assert.deepEqual(got.pollutants,['PM2.5']);
assert.equal(got.reported_at,'2026-10-29T14:00:00.000Z');
assert.equal(got.scope.includes('no equivale'),true);

const tableLayout=`<body><table><tr><td>Menú</td></tr></table>
<div><span>08:00 h, jueves 29 de octubre de 2026</span></div>
<div>Índice AIRE Y SALUD: ACEPTABLE</div>
<div>Contaminante(s): PM<sub>2.5</sub></div>
<div>Riesgo: MODERADO</div></body>`;
assert.equal(air.parseAirReport(tableLayout,now).category,'ACEPTABLE',
 'Las tablas de diseño antes del índice no deben impedir leer el informe.');
const light=`<p>Ciudad de México, jueves 29 de octubre de 2026</p>
<p>08 horas</p><p><strong>Índice AIRE Y SALUD: BUENA</strong></p>
<p><strong>Nivel de riesgo:</strong> BAJO</p>
<p><strong>Contaminante(s):</strong> O<sub>3</sub>,PM<sub>10</sub></p>`;
const l=air.parseAirReport(light,now);
assert.equal(l.category,'BUENA');
assert.deepEqual(l.pollutants,['O3','PM10']);
assert.throws(()=>air.parseAirReport(official,Date.parse('2026-10-29T19:00:00Z')),'No permitir reporte antiguo');
assert.throws(()=>air.parseAirReport('<p>Índice AIRE Y SALUD: ACEPTABLE</p>',now));
assert.throws(()=>air.parseAirReport(official.replace('ACEPTABLE','TODO EXCELENTE'),now));
assert.equal(air.sourceStamp(2026,2,31,8,0),null);
assert.equal(air.sourceStamp(2026,10,29,8,0),'2026-10-29T14:00:00.000Z');

const press=`<html><main>
<article><time>29 de octubre de 2026 Fecha de publicación</time>
<h2><a href="/comisionambiental/prensa/aviso-nuevo">SE ACTIVA CONTINGENCIA AMBIENTAL ATMOSFÉRICA POR OZONO EN LA ZMVM</a></h2></article>
<article><time>13 de septiembre de 2026 Fecha de publicación</time>
<h2><a href="https://www.gob.mx/comisionambiental/prensa/aviso-viejo">SE SUSPENDE LA CONTINGENCIA AMBIENTAL ATMOSFÉRICA POR OZONO EN LA ZMVM</a></h2></article>
<article><time>09 de octubre de 2026 Fecha de publicación</time>
<h2>Seminario técnico ambiental en CDMX</h2></article>
</main></html>`;
const adv=came.parseAdvisories(press,now);
assert.equal(adv.length,2);
assert.equal(adv[0].action,'activacion');
assert.equal(adv[1].action,'suspension');
assert.equal(adv[0].recent,true);
assert.equal(adv[1].recent,false);
assert.equal(adv[0].archived,true);
assert.equal(adv[0].url,'https://www.gob.mx/comisionambiental/prensa/aviso-nuevo');
assert.equal(came.safeOfficial('https://evil.test/article'),null);
assert.equal(came.safeOfficial('javascript:alert(1)'),null);

console.log('Pruebas Aire/CDMX y CAMe: fuente, fecha, vigencia, contaminantes y enlaces correctos.');
