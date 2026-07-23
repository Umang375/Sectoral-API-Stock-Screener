/**
 * API client — centralised fetch wrapper for the backend.
 *
 * WHY a wrapper instead of raw fetch()?
 * - Single place to set the API base URL (dev vs production).
 * - Consistent error handling across all pages.
 * - Easy to add auth headers later (one line change).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Make an API request and return parsed JSON.
 * Throws on non-2xx responses with the error detail.
 */
async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

/* ── Public API functions ────────────────────────────────── */

export async function getDashboard() {
  return apiFetch('/api/dashboard');
}

export async function getStocks(skip = 0, limit = 50) {
  return apiFetch(`/api/stocks?skip=${skip}&limit=${limit}`);
}

export async function getStock(symbol) {
  return apiFetch(`/api/stocks/${symbol}`);
}

export async function getTags(skip = 0, limit = 50) {
  return apiFetch(`/api/tags?skip=${skip}&limit=${limit}`);
}

export async function getTagReturns(label, limit = 12) {
  return apiFetch(`/api/tags/${encodeURIComponent(label)}/returns?limit=${limit}`);
}

export async function getStockReturns(symbol, limit = 12) {
  return apiFetch(`/api/stocks/${symbol}/returns?limit=${limit}`);
}
