/* Pruebas offline del índice vial: fecha, CDMX, categorías, enlaces y seguridad. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const js=await readFile(new URL('../functions/api/trafico.js',import.meta.url),'utf8');
const {decodeXML,tagValue,identifyType,placeFromTitle,hasCDMXContext,linkSafe,parseRSS,mergeFeeds}=
 await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
assert.equal(decodeXML('Reforma &amp; Insurgentes'),'Reforma & Insurgentes');
assert.equal(tagValue('<title><![CDATA[Marcha en CDMX]]></title>','title'),'Marcha en CDMX');
assert.equal(identifyType('Marcha en Paseo de la Reforma CDMX'),'marchas');
assert.equal(identifyType('Cierre vial en Iztapalapa'),'cierres');
assert.equal(identifyType('Obras con cierre de carriles en CDMX'),'obras');
assert.equal(identifyType('Accidente vial en CDMX'),'incidentes');
assert.equal(identifyType('Precio del euro en México'),null);
assert.equal(placeFromTitle('Bloqueo vial en Xochimilco CDMX'),'Xochimilco');
assert.equal(hasCDMXContext('Marcha de Xalapa Veracruz llega a CDMX'),false);
assert.equal(hasCDMXContext('Marcha en CDMX hoy'),true);
assert.equal(linkSafe('javascript:alert(1)'),null);
assert.equal(linkSafe('https://example.com/article/abc'),null);
assert.ok(linkSafe('https://news.google.com/rss/articles/ABC?oc=5'));
const now=Date.now();
const item=(title,ageHours,link='https://news.google.com/rss/articles/ABC?oc=5',source='Medio MX')=>`<item>
<title><![CDATA[${title} - ${source}]]></title><link>${link.replaceAll('&','&amp;')}</link>
<pubDate>${new Date(now-ageHours*3600000).toUTCString()}</pubDate><source url="https://example.com">${source}</source></item>`;
const xml='<?xml version="1.0"?><rss><channel>'+
item('Cierre vial en CDMX por evento',1)+
item('Obras con reducción de carriles en Iztapalapa',3)+
item('Marcha en Xalapa Veracruz para mañana en CDMX',1)+
item('Precio del euro en México',1)+
item('Accidente vial en CDMX',49)+
item('Cierre vial en CDMX',1,'https://evil.example/rss/articles/ABC')+
'</channel></rss>';
const parsed=parseRSS(xml,now);
assert.equal(parsed.length,2);
assert.deepEqual(parsed.map(x=>x.type),['cierres','obras']);
assert.equal(parsed[0].title,'Cierre vial en CDMX por evento');
assert.equal(parsed[1].borough,'Iztapalapa');
const merged=mergeFeeds([parsed,[parsed[0]]]);
assert.equal(merged.length,2);
assert.throws(()=>parseRSS('<html>no es RSS</html>',now));
console.log('Pruebas de tráfico: categorías, ubicación, RSS, duplicados, fechas y seguridad correctas.');
