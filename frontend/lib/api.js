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
  const { cache, revalidate = 300, ...restOptions } = options;

  const fetchConfig = {
    ...restOptions,
    headers: {
      'Content-Type': 'application/json',
      ...restOptions.headers,
    },
  };

  if (cache) {
    fetchConfig.cache = cache;
  } else {
    fetchConfig.next = { revalidate };
  }

  const res = await fetch(url, fetchConfig);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

/* ── Public API functions ────────────────────────────────── */

export async function getDashboard() {
  return apiFetch('/api/dashboard', { revalidate: 60 });
}

export async function getStocks(skip = 0, limit = 150) {
  return apiFetch(`/api/stocks?skip=${skip}&limit=${limit}`, { revalidate: 300 });
}

export async function getStock(symbol) {
  return apiFetch(`/api/stocks/${encodeURIComponent(symbol)}`, { revalidate: 60 });
}

export async function getStockHistory(symbol, skip = 0, limit = 500) {
  return apiFetch(`/api/stocks/${encodeURIComponent(symbol)}/history?skip=${skip}&limit=${limit}`, { revalidate: 300 });
}

export async function getTags(skip = 0, limit = 150) {
  return apiFetch(`/api/tags?skip=${skip}&limit=${limit}`, { revalidate: 300 });
}

export async function getTagReturns(label, limit = 12) {
  return apiFetch(`/api/tags/${encodeURIComponent(label)}/returns?limit=${limit}`, { revalidate: 300 });
}

export async function getTagDailyReturns(label, limit = 30) {
  return apiFetch(`/api/tags/${encodeURIComponent(label)}/daily-returns?limit=${limit}`, { revalidate: 300 });
}

export async function getTagStocks(label) {
  return apiFetch(`/api/tags/${encodeURIComponent(label)}/stocks`, { revalidate: 300 });
}

export async function getStockReturns(symbol, limit = 12) {
  return apiFetch(`/api/stocks/${encodeURIComponent(symbol)}/returns?limit=${limit}`, { revalidate: 300 });
}
