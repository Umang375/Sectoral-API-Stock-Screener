'use client';

import { useState } from 'react';
import Link from 'next/link';
import { formatPercent, get52WHighStyle, getReturnStyle } from '@/lib/heatmapUtils';

function filterAndSortStocks(stocks, searchQuery, activeFilter, sortKey, sortDir) {
  if (!Array.isArray(stocks)) return [];

  let result = [...stocks];

  // Search query filter (symbol, name, or tags)
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase().trim();
    result = result.filter((item) => {
      const matchesSymbol = item.symbol?.toLowerCase().includes(q);
      const matchesName = item.name?.toLowerCase().includes(q);
      const matchesTag = item.tags?.some((t) => t.toLowerCase().includes(q));
      return matchesSymbol || matchesName || matchesTag;
    });
  }

  // Quick filter pills
  if (activeFilter === 'TOP_GAINERS') {
    result = result.filter((item) => item.return_1d != null && item.return_1d > 0);
  } else if (activeFilter === 'TOP_LOSERS') {
    result = result.filter((item) => item.return_1d != null && item.return_1d < 0);
  } else if (activeFilter === 'NEAR_HIGH') {
    result = result.filter((item) => item.drawdown_52w_high != null && item.drawdown_52w_high >= -5);
  }

  // Sort
  result.sort((a, b) => {
    let valA = a[sortKey];
    let valB = b[sortKey];

    if (sortKey === 'symbol') {
      valA = a.symbol || '';
      valB = b.symbol || '';
    }

    if (valA == null && valB == null) return 0;
    if (valA == null) return 1;
    if (valB == null) return -1;

    if (typeof valA === 'string') {
      return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }

    return sortDir === 'asc' ? valA - valB : valB - valA;
  });

  return result;
}

/**
 * StockHeatmapTable Component.
 * Financial heatmap table for individual stocks with multi-period returns,
 * 52W high drawdown, tags, and contiguous heatmap cells.
 */
export default function StockHeatmapTable({
  stocks = [],
  title = 'Top Stocks',
  subtitle = 'Multi-period equity performance, 52-week high drawdown, and volume',
  defaultLimit = null,
  showControls = true,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [sortKey, setSortKey] = useState('return_1d');
  const [sortDir, setSortDir] = useState('desc'); // 'asc' | 'desc'
  const [isExpandedLimit, setIsExpandedLimit] = useState(false);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const filteredStocks = filterAndSortStocks(
    stocks,
    searchQuery,
    activeFilter,
    sortKey,
    sortDir
  );

  const displayedStocks = (!defaultLimit || isExpandedLimit)
    ? filteredStocks
    : filteredStocks.slice(0, defaultLimit);

  const hasMoreRows = defaultLimit && filteredStocks.length > defaultLimit;

  return (
    <div className="heatmap-card">
      {/* ── Table Header & Controls ───────────────────────── */}
      <div className="heatmap-header">
        <div className="heatmap-title-wrap">
          <h3 className="heatmap-title">{title}</h3>
          {subtitle && <p className="heatmap-subtitle">{subtitle}</p>}
        </div>

        {showControls && (
          <div className="heatmap-controls">
            <div className="heatmap-search-wrap">
              <span className="heatmap-search-icon">🔍</span>
              <input
                type="text"
                placeholder="Filter stock or tag..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="heatmap-search-input"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="heatmap-search-clear"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="heatmap-filter-pills">
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'ALL' ? 'active' : ''}`}
                onClick={() => setActiveFilter('ALL')}
              >
                All ({stocks.length})
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'TOP_GAINERS' ? 'active' : ''}`}
                onClick={() => setActiveFilter('TOP_GAINERS')}
              >
                1D Gainers
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'TOP_LOSERS' ? 'active' : ''}`}
                onClick={() => setActiveFilter('TOP_LOSERS')}
              >
                1D Losers
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'NEAR_HIGH' ? 'active' : ''}`}
                onClick={() => setActiveFilter('NEAR_HIGH')}
              >
                Near 52W High
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Main Stock Matrix Table ───────────────────────── */}
      {displayedStocks.length === 0 ? (
        <div className="heatmap-empty-state">
          <span className="empty-icon">📈</span>
          <p>{searchQuery ? 'No stocks matching your search query.' : 'No stock data available yet.'}</p>
        </div>
      ) : (
        <div className="heatmap-table-container">
          <table className="heatmap-table">
            <thead>
              <tr>
                <th
                  className={`col-stock-symbol ${sortKey === 'symbol' ? 'sorted' : ''}`}
                  onClick={() => handleSort('symbol')}
                >
                  <div className="th-content">
                    <span>STOCK</span>
                    {sortKey === 'symbol' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-stock-ltp ${sortKey === 'ltp' ? 'sorted' : ''}`}
                  onClick={() => handleSort('ltp')}
                >
                  <div className="th-content right">
                    <span>LTP (₹)</span>
                    {sortKey === 'ltp' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-52w ${sortKey === 'drawdown_52w_high' ? 'sorted' : ''}`}
                  onClick={() => handleSort('drawdown_52w_high')}
                >
                  <div className="th-content center">
                    <span className="th-multiline">52W<br />HIGH</span>
                    {sortKey === 'drawdown_52w_high' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_1d' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_1d')}
                >
                  <div className="th-content center">
                    <span>1D</span>
                    {sortKey === 'return_1d' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_1w' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_1w')}
                >
                  <div className="th-content center">
                    <span>1W</span>
                    {sortKey === 'return_1w' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_1m' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_1m')}
                >
                  <div className="th-content center">
                    <span>1M</span>
                    {sortKey === 'return_1m' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_3m' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_3m')}
                >
                  <div className="th-content center">
                    <span>3M</span>
                    {sortKey === 'return_3m' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_6m' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_6m')}
                >
                  <div className="th-content center">
                    <span>6M</span>
                    {sortKey === 'return_6m' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_1y' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_1y')}
                >
                  <div className="th-content center">
                    <span>1YR*</span>
                    {sortKey === 'return_1y' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-return ${sortKey === 'return_2y' ? 'sorted' : ''}`}
                  onClick={() => handleSort('return_2y')}
                >
                  <div className="th-content center">
                    <span>2YR*</span>
                    {sortKey === 'return_2y' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-stock-vol ${sortKey === 'volume' ? 'sorted' : ''}`}
                  onClick={() => handleSort('volume')}
                >
                  <div className="th-content right">
                    <span>VOLUME</span>
                    {sortKey === 'volume' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>
              </tr>
            </thead>

            <tbody>
              {displayedStocks.map((stock) => {
                const high52Style = get52WHighStyle(stock.drawdown_52w_high);
                const ret1DStyle = getReturnStyle(stock.return_1d);
                const ret1WStyle = getReturnStyle(stock.return_1w);
                const ret1MStyle = getReturnStyle(stock.return_1m);
                const ret3MStyle = getReturnStyle(stock.return_3m);
                const ret6MStyle = getReturnStyle(stock.return_6m);
                const ret1YStyle = getReturnStyle(stock.return_1y);
                const ret2YStyle = getReturnStyle(stock.return_2y);

                return (
                  <tr key={stock.symbol} className="heatmap-row">
                    {/* Stock Symbol & Name */}
                    <td className="cell-stock-symbol">
                      <div className="stock-cell-wrap">
                        <Link
                          href={`/stocks/${encodeURIComponent(stock.symbol)}`}
                          className="stock-symbol-link"
                        >
                          <span className="stock-title">{stock.symbol}</span>
                          {stock.name && <span className="stock-subtitle">{stock.name}</span>}
                        </Link>
                        {stock.tags && stock.tags.length > 0 && (
                          <div className="stock-mini-tags">
                            {stock.tags.slice(0, 2).map((t, idx) => (
                              <span key={idx} className="badge badge-accent">
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>

                    {/* LTP */}
                    <td className="cell-stock-ltp">
                      {stock.ltp != null ? `₹${Number(stock.ltp).toLocaleString('en-IN')}` : '—'}
                    </td>

                    {/* 52W High Cell */}
                    <td className="cell-matrix">
                      {stock.drawdown_52w_high != null ? (
                        <div className={`matrix-cell-badge ${high52Style.className}`}>
                          {formatPercent(stock.drawdown_52w_high, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 1D Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_1d != null ? (
                        <div className={`matrix-cell-badge ${ret1DStyle.className}`}>
                          {formatPercent(stock.return_1d, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 1W Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_1w != null ? (
                        <div className={`matrix-cell-badge ${ret1WStyle.className}`}>
                          {formatPercent(stock.return_1w, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 1M Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_1m != null ? (
                        <div className={`matrix-cell-badge ${ret1MStyle.className}`}>
                          {formatPercent(stock.return_1m, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 3M Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_3m != null ? (
                        <div className={`matrix-cell-badge ${ret3MStyle.className}`}>
                          {formatPercent(stock.return_3m, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 6M Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_6m != null ? (
                        <div className={`matrix-cell-badge ${ret6MStyle.className}`}>
                          {formatPercent(stock.return_6m, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 1YR* Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_1y != null ? (
                        <div className={`matrix-cell-badge ${ret1YStyle.className}`}>
                          {formatPercent(stock.return_1y, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* 2YR* Return Cell */}
                    <td className="cell-matrix">
                      {stock.return_2y != null ? (
                        <div className={`matrix-cell-badge ${ret2YStyle.className}`}>
                          {formatPercent(stock.return_2y, false)}
                        </div>
                      ) : (
                        <div className="matrix-cell-empty">—</div>
                      )}
                    </td>

                    {/* Volume */}
                    <td className="cell-stock-vol">
                      {stock.volume != null ? Number(stock.volume).toLocaleString('en-IN') : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Expand Toggle ─────────────────────────────────── */}
      {hasMoreRows && (
        <div className="heatmap-footer">
          <button
            type="button"
            className="heatmap-expand-btn"
            onClick={() => setIsExpandedLimit((prev) => !prev)}
          >
            {isExpandedLimit
              ? `↑ Collapse to Top ${defaultLimit} Stocks`
              : `↓ Show All ${filteredStocks.length} Stocks`}
          </button>
        </div>
      )}
    </div>
  );
}
