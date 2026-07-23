'use client';

/**
 * Stocks page — searchable, paginated table of all tracked stocks.
 *
 * Styling from styles/stocks.css (imported in layout.js).
 */

import { useEffect, useState } from 'react';
import { getStocks } from '@/lib/api';

const PAGE_SIZE = 30;

export default function StocksPage() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  useEffect(() => {
    setLoading(true);
    getStocks(page * PAGE_SIZE, PAGE_SIZE)
      .then(setStocks)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page]);

  // Client-side search filter (on the current page of results).
  const filtered = stocks.filter(
    (s) =>
      s.symbol.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div>
      <div className="page-header">
        <h2>Stocks</h2>
        <p>All tracked equities with latest prices and AI-generated tags</p>
      </div>

      {/* ── Search Bar ────────────────────────────────────── */}
      <div className="search-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Search by symbol, name, or tag..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* ── Table ─────────────────────────────────────────── */}
      {loading ? (
        <StocksTableSkeleton />
      ) : error ? (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>{error}</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <p>{search ? 'No stocks match your search.' : 'No stocks tracked yet. Add a screener to get started.'}</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>LTP</th>
                  <th>Change</th>
                  <th>Tags</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((stock) => (
                  <tr key={stock.symbol}>
                    <td>
                      <div className="stock-symbol">{stock.symbol}</div>
                      <div className="stock-name">{stock.name}</div>
                    </td>
                    <td>
                      <span className="stock-ltp">
                        {stock.ltp != null ? `₹${stock.ltp.toLocaleString('en-IN')}` : '—'}
                      </span>
                    </td>
                    <td>
                      {stock.change_pct != null ? (
                        <span className={`stock-change ${stock.change_pct >= 0 ? 'positive' : 'negative'}`}>
                          {stock.change_pct > 0 ? '+' : ''}
                          {stock.change_pct.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td>
                      <div className="stock-tags">
                        {stock.tags.map((tag, j) => (
                          <span key={j} className="stock-tag">{tag}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Pagination ────────────────────────────────────── */}
      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
        >
          ← Previous
        </button>
        <span className="pagination-info">
          Page {page + 1}
        </span>
        <button
          className="pagination-btn"
          onClick={() => setPage((p) => p + 1)}
          disabled={stocks.length < PAGE_SIZE}
        >
          Next →
        </button>
      </div>
    </div>
  );
}

/* ── Loading Skeleton ──────────────────────────────────────── */
function StocksTableSkeleton() {
  return (
    <div className="card">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} style={{ display: 'flex', gap: 16, padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="skeleton" style={{ width: 80, height: 16 }} />
          <div className="skeleton" style={{ width: 60, height: 16 }} />
          <div className="skeleton" style={{ width: 50, height: 16 }} />
          <div className="skeleton" style={{ width: 120, height: 16 }} />
        </div>
      ))}
    </div>
  );
}
