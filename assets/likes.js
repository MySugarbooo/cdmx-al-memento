(() => {
  const box = document.querySelector('[data-site-likes]');
  if (!box) return;
  const button = box.querySelector('button');
  const label = box.querySelector('[data-like-label]');
  const total = box.querySelector('[data-like-total]');
  const status = box.querySelector('[data-like-status]');
  const retry = box.querySelector('[data-like-retry]');
  let liked = false, ready = false, busy = false;
  async function request(options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/api/likes', { ...options, credentials: 'same-origin', cache: 'no-store', signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'No se pudieron consultar los Me gusta.');
      if (!Number.isSafeInteger(data.total) || data.total < 0 || typeof data.liked !== 'boolean') throw new Error('No se pudieron consultar los Me gusta.');
      return data;
    } finally { clearTimeout(timeout); }
  }
  function render(data) {
    liked = data.liked; ready = true;
    button.setAttribute('aria-pressed', String(liked));
    label.textContent = liked ? 'Te gusta' : 'Me gusta';
    total.textContent = `${data.total.toLocaleString('es-MX')} Me gusta`;
    status.textContent = liked ? '¡Gracias por apoyar CDMX AL MEMENTO! Puedes quitar tu Me gusta.' : 'Dale Me gusta a CDMX AL MEMENTO.';
    retry.hidden = true;
  }
  async function load() {
    if (busy) return;
    busy = true;
    try { render(await request()); }
    catch (error) {
      if (!ready) total.textContent = 'Contador no disponible';
      status.textContent = error.name === 'AbortError' ? 'La conexión tardó demasiado. Vuelve a intentarlo.' : error.message;
      retry.hidden = false;
    } finally { busy = false; button.disabled = !ready; }
  }
  button.addEventListener('click', async () => {
    if (busy || !ready) return;
    busy = true; button.disabled = true;
    status.textContent = 'Guardando…';
    try {
      render(await request({ method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ liked: !liked }) }));
    } catch (error) {
      status.textContent = error.name === 'AbortError' ? 'No se confirmó el cambio. Pulsa Actualizar contador para comprobarlo.' : error.message;
      // Re-read before allowing another toggle: the write may have succeeded.
      ready = false; retry.hidden = false;
    } finally { busy = false; button.disabled = !ready; }
  });
  retry.addEventListener('click', load);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
  setInterval(() => { if (!document.hidden && ready) load(); }, 60000);
  load();
})();
