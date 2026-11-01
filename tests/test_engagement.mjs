import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import vm from 'node:vm';

const origin = 'https://cdmx-al-memento.pages.dev';
const apiSource = readFileSync(new URL('../functions/api/engagement.js', import.meta.url), 'utf8');
const { onRequest } = await import('data:text/javascript;base64,' + Buffer.from(apiSource).toString('base64'));
const localKey = '/noticias/?id=d3fd9dd6a6a8b94ee26c&mes=2026-11';

function setup() {
  const db = new DatabaseSync(':memory:');
  db.exec('CREATE TABLE unique_visitors (visitor_hash TEXT PRIMARY KEY, first_seen INTEGER); ' +
    'CREATE TABLE article_likes (article_id TEXT NOT NULL, visitor_hash TEXT NOT NULL, ' +
    'created_at INTEGER, PRIMARY KEY(article_id, visitor_hash));');
  const env = { LIKES_DB: { prepare(sql) { return { first: async () => db.prepare(sql).get(), bind(...args) { return {
    first: async () => db.prepare(sql).get(...args),
    run: async () => db.prepare(sql).run(...args),
  }; } }; } } };
  return { db, env };
}
function get(env, key, cookie) {
  const url = origin + '/api/engagement' + (key ? '?article=' + encodeURIComponent(key) : '');
  return onRequest({ env, request: new Request(url, { headers: cookie ? { Cookie: cookie } : {} }) });
}

test('article likes accept a stable local article key and persist votes', async () => {
  const { db, env } = setup();
  const first = await get(env, localKey);
  assert.equal(first.status, 200);
  assert.deepEqual(await first.json(), { visitors: 0, likes: 0, liked: false });
  const cookie = first.headers.get('set-cookie').split(';')[0];
  const response = await onRequest({ env, request: new Request(origin + '/api/engagement?article=' + encodeURIComponent(localKey), {
    method: 'POST', headers: { Cookie: cookie, Origin: origin, 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'like', liked: true }),
  }) });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { visitors: 0, likes: 1, liked: true });
  assert.deepEqual(await (await get(env, localKey, cookie)).json(), { visitors: 0, likes: 1, liked: true });
  db.close();
});

test('legacy Google News article keys remain valid; malformed local keys are rejected', async () => {
  const { db, env } = setup();
  assert.equal((await get(env, 'https://news.google.com/rss/articles/legacy')).status, 200);
  assert.equal((await get(env, '/noticias/?id=invalid&mes=2026-11')).status, 400);
  assert.equal((await get(env, '/noticias/?id=d3fd9dd6a6a8b94ee26c&mes=2026-99')).status, 400);
  assert.equal((await get(env, 'https://other.example/article')).status, 400);
  db.close();
});

test('frontend uses local key for long RSS URLs and preserves short legacy keys', async () => {
  const source = readFileSync(new URL('../assets/engagement.js', import.meta.url), 'utf8');
  const calls = [], buttons = [], window = {};
  const document = {
    querySelector: () => null,
    getElementById: () => null,
    createElement: () => ({ append() {}, addEventListener() {}, setAttribute() {}, textContent: '', disabled: false }),
  };
  const fetch = async (url) => { calls.push(url); return { ok: true, json: async () => ({ visitors: 0, likes: 0, liked: false }) }; };
  vm.runInNewContext(source, { window, document, fetch, encodeURIComponent });
  const card = { querySelector: () => null, append: (button) => buttons.push(button) };
  window.CDMX_addArticleLike(card, { url: 'https://news.google.com/rss/articles/' + 'a'.repeat(300), local_url: localKey });
  await new Promise(setImmediate);
  assert.equal(buttons.length, 1);
  assert.ok(calls.some((url) => url.includes('article=' + encodeURIComponent(localKey))));
  const legacy = 'https://news.google.com/rss/articles/legacy';
  window.CDMX_addArticleLike(card, { url: legacy, local_url: localKey });
  await new Promise(setImmediate);
  assert.equal(buttons.length, 2);
  assert.ok(calls.some((url) => url.includes('article=' + encodeURIComponent(legacy))));
});
