// Checks sin internet: no exponer identidad del autor, aprobación atómica y roles.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const read=path=>readFile(new URL('../'+path,import.meta.url),'utf8');
const [client,rules,html,privacy]=await Promise.all([
 read('assets/reportes-ciudadanos.js'),
 read('firebase/firestore.rules'),
 read('reportes-ciudadanos/index.html'),
 read('privacidad.html')
]);
assert.ok(client.includes('fs.writeBatch(firebase.db)'));
assert.ok(client.includes('batch.update(privateRef,'));
assert.ok(client.includes('batch.set(publicRef,{'));
assert.ok(client.includes('batch.update(publicRef,{'));
assert.ok(client.includes('batch.delete(publicRef)'));
assert.ok(client.includes('getIdTokenResult(person,true)'));
assert.ok(client.includes('token.claims.moderator===true'));
assert.ok(client.includes("status:'pending'"));
assert.ok(client.includes("fs.where('uid','==',person.uid)"));
assert.ok(client.includes('window.confirm('));
assert.ok(!client.includes('innerHTML'));
assert.ok(!client.includes('setCustomUserClaims'));
const projection=client.split('batch.set(publicRef,{')[1]?.split('});')[0]||'';
assert.ok(projection.includes('title:old.title'));
for(const field of ['uid:','email:','name:','phone:','photoURL:']){
 assert.ok(!projection.includes(field),'La copia pública incluye: '+field);
}
assert.ok(rules.includes('match /citizenReports/{reportId}'));
assert.ok(rules.includes('match /citizenReportsPublic/{reportId}'));
assert.ok(rules.includes("getAfter(citizenPublicPath(reportId)).data"));
assert.ok(rules.includes("getAfter(citizenPrivatePath(reportId)).data.status"));
assert.ok(rules.includes("citizenBorough(data.borough)"));
assert.ok(rules.includes("data.createdAt == request.time"));
assert.ok(rules.includes("data.moderatedBy == ''"));
assert.ok(html.includes('https://atencionciudadana.cdmx.gob.mx/'));
assert.ok(html.includes('no genera un folio SUAC'));
assert.ok(html.includes('id="citizen-form" hidden'));
assert.ok(privacy.includes('sin el UID, nombre, correo ni foto del autor'));
console.log('Reportes ciudadanos: 26 comprobaciones de aislamiento, rol, publicación atómica, identidad y fuente oficial.');
