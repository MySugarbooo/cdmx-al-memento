import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
const source = readFileSync(new URL('../functions/api/likes.js', import.meta.url), 'utf8');
const { onRequest } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const origin = 'https://cdmx-al-memento.pages.dev';
function setup() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(new URL('../deploy/likes.sql', import.meta.url), 'utf8'));
  const prepare = (sql) => ({ bind: (...args) => ({ first: async () => db.prepare(sql).get(...args), sql, args }) });
  return { db, env: { LIKES_DB: { prepare, async batch(statements) {
    db.exec('BEGIN');
    try {
      const result = statements.map(({sql, args}) => /^SELECT/.test(sql) ? { results: db.prepare(sql).all(...args) } : { results: [], meta: db.prepare(sql).run(...args) });
      db.exec('COMMIT'); return result;
    } catch (error) { db.exec('ROLLBACK'); throw error; }
  } } } };
}
async function visit(env, cookie) {
  const response = await onRequest({env, request: new Request(origin + '/api/likes', {headers: cookie ? {Cookie:cookie} : {}})});
  return {response, data:await response.json(), cookie:response.headers.get('set-cookie')?.split(';')[0]};
}
function vote(env, cookie, liked, extra={}) {
  return onRequest({env, request: new Request(origin + '/api/likes', {method:'PUT', headers:{Origin:origin,'Content-Type':'application/json',Cookie:cookie,...extra}, body:JSON.stringify({liked})})});
}
test('shared persistent total, reload, idempotency, independent visitors, unlike', async () => {
  const {env,db} = setup();
  const first = await visit(env); const second = await visit(env);
  assert.deepEqual(first.data, {total:0,liked:false});
  assert.match(first.response.headers.get('set-cookie'), /Secure; HttpOnly; SameSite=Lax/);
  assert.match(first.response.headers.get('Cache-Control'), /no-store/);
  assert.deepEqual(await (await vote(env,first.cookie,true)).json(),{total:1,liked:true});
  assert.deepEqual(await (await vote(env,first.cookie,true)).json(),{total:1,liked:true});
  assert.deepEqual((await visit(env,first.cookie)).data,{total:1,liked:true});
  assert.deepEqual((await visit(env,second.cookie)).data,{total:1,liked:false});
  assert.deepEqual(await (await vote(env,second.cookie,true)).json(),{total:2,liked:true});
  assert.deepEqual(await (await vote(env,first.cookie,false)).json(),{total:1,liked:false});
  assert.deepEqual(await (await vote(env,first.cookie,false)).json(),{total:1,liked:false});
  assert.deepEqual(await (await vote(env,second.cookie,false)).json(),{total:0,liked:false});
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM site_likes').get().n,0);
  db.close();
});
test('validation and origin checks prevent invalid writes', async () => {
  const {env,db}=setup(); const {cookie}=await visit(env);
  assert.equal((await vote(env,cookie,true,{Origin:'https://other.example'})).status,403);
  assert.equal((await vote(env,cookie,true,{'Sec-Fetch-Site':'cross-site'})).status,403);
  assert.equal((await vote(env,'',true)).status,428);
  assert.equal((await vote(env,cookie,'yes')).status,400);
  assert.equal((await vote(env,cookie,true,{'Content-Type':'text/plain'})).status,415);
  const response=await onRequest({env,request:new Request(origin+'/api/likes',{method:'PUT',headers:{Origin:origin,'Content-Type':'application/json',Cookie:cookie},body:'x'.repeat(257)})});
  assert.equal(response.status,413);
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM site_likes').get().n,0);
  db.close();
});
test('missing or failing database reports unavailability, never a fake zero', async () => {
  const missing=await visit({}); assert.equal(missing.response.status,503); assert.equal(missing.data.total,undefined);
  const failing=await visit({LIKES_DB:{prepare(){throw new Error('db offline');}}}); assert.equal(failing.response.status,503);
});
