/**
 * Stocks page — searchable, paginated table of all tracked stocks.
 * Server Component
 */

import { getStocks } from '@/lib/api';
import Link from 'next/link';

const PAGE_SIZE = 30;

export default async function StocksPage({ searchParams }) {
  const resolvedParams = await searchParams;
  const search = resolvedParams?.q || '';
  const page = parseInt(resolvedParams?.page || '0', 10);

  let stocks = [];
  let error = null;

  try {
    stocks = await getStocks(page * PAGE_SIZE, PAGE_SIZE);
  } catch (err) {
    error = err.message;
  }

  // Server-side filter
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
        <form method="GET" action="/stocks" style={{ display: 'flex', width: '100%' }}>
          <input
            type="text"
            name="q"
            className="search-input"
            placeholder="Search by symbol, name, or tag..."
            defaultValue={search}
          />
          {/* Keep page in sync if searching from page N */}
          <input type="hidden" name="page" value="0" /> 
        </form>
      </div>

      {/* ── Table ─────────────────────────────────────────── */}
      {error ? (
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
        {page > 0 ? (
          <Link href={`?q=${encodeURIComponent(search)}&page=${page - 1}`} className="pagination-btn">
            ← Previous
          </Link>
        ) : (
          <button className="pagination-btn" disabled>← Previous</button>
        )}
        <span className="pagination-info">
          Page {page + 1}
        </span>
        {stocks.length >= PAGE_SIZE ? (
          <Link href={`?q=${encodeURIComponent(search)}&page=${page + 1}`} className="pagination-btn">
            Next →
          </Link>
        ) : (
          <button className="pagination-btn" disabled>Next →</button>
        )}
      </div>
    </div>
  );
}
