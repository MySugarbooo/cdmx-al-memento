import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Script} from 'node:vm';

const read=(path)=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
const code=read('assets/comments.js');
const html=read('comunidad/index.html');
const news=read('noticias/index.html');
const css=read('assets/comments-seguridad-20261028.css');
const rules=read('firebase/firestore.rules');

test('los scripts del foro tienen sintaxis valida',()=>{
 assert.doesNotThrow(()=>new Script(code));
});
test('el titulo indica limites y muestra contador accesible',()=>{
 assert.match(html,/id="forum-question-title"[^>]*minlength="8"[^>]*maxlength="110"/);
 assert.match(html,/id="forum-title-help"[^>]*aria-live="polite"/);
 assert.match(html,/Faltan /);
 assert.match(html,/ caracteres para el mínimo/);
 assert.match(code,/title\.length<8\|\|title\.length>110/);
 assert.match(code,/if\(titleHelp\)titleHelp\.hidden=true/);
});
test('errores y resultados aparecen junto al botón de publicar',()=>{
 assert.match(html,/id="forum-editor-feedback"[^>]*role="status"/);
 assert.match(code,/showComposerFeedback\(status\.textContent,'error'\)/);
 assert.match(code,/showComposerFeedback\(status\.textContent,'success'\)/);
 assert.match(css,/\.forum-editor-feedback\[data-type=error\]/);
});
test('el editor oculto no aparece para visitantes anonimos',()=>{
 assert.match(css,/\.forum-editor\[hidden\].*display:none!important/);
 assert.match(code,/editor\.hidden=!person/);
});
test('replies antiguos y preguntas eliminadas permanecen visibles',()=>{
 assert.match(code,/Pregunta eliminada o pendiente de cargar/);
 assert.match(code,/orphanGroups/);
 assert.match(code,/replyMap/);
});
test('la búsqueda es explícitamente local y se puede paginar',()=>{
 assert.match(code,/fs\.startAfter\(pageCursor\)/);
 assert.match(code,/fs\.limit\(PAGE_SIZE\)/);
 assert.match(html,/id="forum-load-more"/);
 assert.match(html,/Búsquedas rápidas/);
 assert.match(html,/forum-search-note/);
});
test('identidad del remitente y fotos se basan en token verificado',()=>{
 assert.match(code,/mod\.getIdTokenResult\(person\)/);
 assert.match(code,/uid:user\.uid,name:identity\.name/);
 assert.match(rules,/request\.resource\.data\.name == verifiedName\(\)/);
 assert.match(rules,/photo == verified/);
 assert.match(rules,/request\.auth\.token\.firebase\.sign_in_provider == 'google\.com'/);
});
test('reportes y moderación no son públicos',()=>{
 assert.match(rules,/match \/community\/main\/reports\/\{reportId\}/);
 assert.match(rules,/allow read, delete: if moderator\(\)/);
 assert.match(rules,/allow create: if validReport\(reportId\)/);
 assert.match(code,/reportButton\(topic\)/);
 assert.match(code,/reportId=user\.uid\+'_'\+topic\.id/);
 assert.match(code,/result\.claims\.moderator===true/);
});
test('se prohíben escrituras no autorizadas y se respetan autores',()=>{
 assert.match(rules,/allow create: if validComment\(\)/);
 assert.match(rules,/allow update: if false/);
 assert.match(rules,/resource\.data\.uid == request\.auth\.uid/);
 assert.match(rules,/match \/communityBans\/\{uid\}/);
 assert.match(rules,/allow read, write: if false/);
});
test('páginas cargan el script de comentarios y la hoja de estilo vigentes',()=>{
 const communityScript=html.match(/\/assets\/comments\.js\?v=([\\w-]+)/);
 const newsScript=news.match(/\/assets\/comments\.js\?v=([\\w-]+)/);
 assert.ok(communityScript,'La comunidad debe cargar comments.js');
 assert.ok(newsScript,'Noticias debe cargar comments.js');
 assert.match(html,/\/assets\/comments-seguridad-20261028\.css\?v=[\\w-]+/);
});
