// Tiny fetch wrapper. The Vite dev server proxies /api to the FastAPI backend.

const BASE = ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} ${text}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  positions: () => request('/api/positions'),
  summary: () => request('/api/portfolio/summary'),
  history: (symbol) => request(`/api/history/${encodeURIComponent(symbol)}`),
  forceSync: () => request('/api/sync', { method: 'POST' }),
  updateMetadata: (symbol, payload) =>
    request(`/api/metadata/${encodeURIComponent(symbol)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
}
