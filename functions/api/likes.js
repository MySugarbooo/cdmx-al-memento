const COOKIE = '__Host-cdmx_like';
const COOKIE_AGE = 31536000;
const READ = `SELECT (SELECT COUNT(*) FROM site_likes) AS total,
  EXISTS(SELECT 1 FROM site_likes WHERE visitor_hash = ?) AS liked`;
function reply(body, status = 200, cookie) {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'private, no-store',
    'X-Content-Type-Options': 'nosniff',
    'Vary': 'Cookie',
  };
  if (cookie) headers['Set-Cookie'] = `${COOKIE}=${cookie}; Path=/; Max-Age=${COOKIE_AGE}; Secure; HttpOnly; SameSite=Lax`;
  return new Response(JSON.stringify(body), { status, headers });
}
function visitor(request) {
  const value = request.headers.get('Cookie')?.split(';').map(x => x.trim()).find(x => x.startsWith(COOKIE + '='))?.slice(COOKIE.length + 1);
  return /^[a-f0-9]{64}$/.test(value || '') ? value : null;
}
async function hash(token) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return Array.from(new Uint8Array(bytes), x => x.toString(16).padStart(2, '0')).join('');
}
function randomToken() {
  return Array.from(crypto.getRandomValues(new Uint8Array(32)), x => x.toString(16).padStart(2, '0')).join('');
}
function state(row) {
  return { total: Number(row.total), liked: Boolean(row.liked) };
}
export async function onRequest({ request, env }) {
  if (!['GET', 'PUT'].includes(request.method)) return reply({ error: 'Método no permitido.' }, 405);
  if (request.method === 'PUT') {
    // Same-origin JSON requests only; no cross-site vote submissions.
    if (request.headers.get('Origin') !== new URL(request.url).origin || request.headers.get('Sec-Fetch-Site') === 'cross-site') {
      return reply({ error: 'Solicitud no permitida.' }, 403);
    }
    if (!request.headers.get('Content-Type')?.startsWith('application/json')) return reply({ error: 'Se requiere JSON.' }, 415);
  }
  if (!env.LIKES_DB) return reply({ error: 'Los Me gusta todavía no están disponibles.', code: 'NOT_CONFIGURED' }, 503);
  let token = visitor(request);
  if (request.method === 'PUT' && !token) return reply({ error: 'Permite las cookies del sitio y vuelve a intentarlo.' }, 428);
  token ||= randomToken();
  try {
    const key = await hash(token);
    if (request.method === 'GET') {
      const row = await env.LIKES_DB.prepare(READ).bind(key).first();
      return reply(state(row), 200, token);
    }
    // Bound the body even when Content-Length is absent or incorrect.
    const reader = request.body?.getReader();
    if (!reader) return reply({ error: 'Solicitud vacía.' }, 400);
    const chunks = []; let length = 0;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      length += value.length;
      if (length > 256) { await reader.cancel(); return reply({ error: 'Solicitud demasiado grande.' }, 413); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(length); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    let body;
    try { body = JSON.parse(new TextDecoder().decode(bytes)); } catch { return reply({ error: 'JSON inválido.' }, 400); }
    if (!body || typeof body.liked !== 'boolean') return reply({ error: 'Indica si deseas dar o quitar Me gusta.' }, 400);
    const write = body.liked
      ? env.LIKES_DB.prepare('INSERT OR IGNORE INTO site_likes (visitor_hash, created_at) VALUES (?, unixepoch())').bind(key)
      : env.LIKES_DB.prepare('DELETE FROM site_likes WHERE visitor_hash = ?').bind(key);
    // D1 batches execute atomically. Repeated requests cannot add extra likes.
    const results = await env.LIKES_DB.batch([write, env.LIKES_DB.prepare(READ).bind(key)]);
    return reply(state(results[1].results[0]), 200, token);
  } catch {
    return reply({ error: 'No se pudo consultar o guardar el Me gusta. Intenta de nuevo.' }, 503);
  }
}
