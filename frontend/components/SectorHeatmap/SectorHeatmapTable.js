'use client';

import { useState } from 'react';
import Link from 'next/link';
import AdvanceDeclineBar from './AdvanceDeclineBar';
import ConstituentStocksTable from './ConstituentStocksTable';
import { formatPercent, get52WHighStyle, getReturnStyle } from '@/lib/heatmapUtils';

function filterAndSortSectors(sectors, searchQuery, activeFilter, sortKey, sortDir) {
  if (!Array.isArray(sectors)) return [];

  let result = [...sectors];

  // Search query filter (sector label or constituent stock symbol/name)
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase().trim();
    result = result.filter((item) => {
      const matchesLabel = item.label?.toLowerCase().includes(q);
      const matchesStock = item.stocks?.some(
        (stk) =>
          stk.symbol?.toLowerCase().includes(q) ||
          stk.name?.toLowerCase().includes(q)
      );
      return matchesLabel || matchesStock;
    });
  }

  // Quick filter pills
  if (activeFilter === 'BULLISH') {
    result = result.filter((item) => (item.advancing_count || 0) > (item.declining_count || 0));
  } else if (activeFilter === 'BEARISH') {
    result = result.filter((item) => (item.declining_count || 0) > (item.advancing_count || 0));
  } else if (activeFilter === 'NEAR_HIGH') {
    result = result.filter((item) => item.drawdown_52w_high != null && item.drawdown_52w_high >= -5);
  } else if (activeFilter === 'TOP_GAINERS') {
    result = result.filter((item) => item.return_1d != null && item.return_1d > 0);
  }

  // Sort
  result.sort((a, b) => {
    let valA = a[sortKey];
    let valB = b[sortKey];

    // Handle custom/special keys
    if (sortKey === 'weight') {
      valA = a.stock_count || 0;
      valB = b.stock_count || 0;
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
 * SectorHeatmapTable Component.
 * High-density financial matrix table displaying sector-level market breadth,
 * 52-week high drawdown, and multi-period return heatmaps with expandable stock constituents.
 */
export default function SectorHeatmapTable({
  sectors = [],
  tags = null,
  title = null,
  subtitle = null,
  defaultLimit = null,
  showControls = true,
  allowExpandAll = true,
  defaultMode = 'tags',
}) {
  const hasBothModes = Boolean(tags !== null && sectors !== null);
  const [activeMode, setActiveMode] = useState(hasBothModes ? defaultMode : (tags ? 'tags' : 'sectors'));

  const isSectorMode = activeMode === 'sectors';
  const activeDataset = (isSectorMode ? sectors : (tags || sectors)) || [];
  const entityLabel = isSectorMode ? 'SECTOR' : 'TAG';
  const displayTitle = isSectorMode
    ? 'Top Sectors'
    : (title || (hasBothModes ? 'Top Tags' : 'Top Sectors'));
  const displaySubtitle = subtitle || (
    isSectorMode
      ? `Tracking ${sectors ? sectors.length : 0} sector cohorts and constituent equities`
      : `Market breadth, 52W high drawdown, and multi-period return heatmaps`
  );

  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [sortKey, setSortKey] = useState('return_1d');
  const [sortDir, setSortDir] = useState('desc'); // 'asc' | 'desc'
  const [expandedSectors, setExpandedSectors] = useState(new Set());
  const [isExpandedLimit, setIsExpandedLimit] = useState(false);

  // Toggle single sector row accordion
  const toggleRow = (tagId) => {
    setExpandedSectors((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) {
        next.delete(tagId);
      } else {
        next.add(tagId);
      }
      return next;
    });
  };

  // Filtering & Sorting pipeline
  const filteredSectors = filterAndSortSectors(
    activeDataset,
    searchQuery,
    activeFilter,
    sortKey,
    sortDir
  );

  // Determine pagination / row display count
  const displayedSectors = (!defaultLimit || isExpandedLimit)
    ? filteredSectors
    : filteredSectors.slice(0, defaultLimit);

  // Expand / Collapse all visible rows
  const toggleExpandAll = () => {
    if (expandedSectors.size > 0) {
      setExpandedSectors(new Set());
    } else {
      const allIds = new Set(filteredSectors.map((s) => s.id));
      setExpandedSectors(allIds);
    }
  };

  // Handle column header sort
  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const hasMoreRows = defaultLimit && filteredSectors.length > defaultLimit;

  return (
    <div className="heatmap-card">
      {/* ── Table Header & Controls ───────────────────────── */}
      <div className="heatmap-header">
        <div className="heatmap-title-wrap">
          <div className="heatmap-title-row">
            <h3 className="heatmap-title">{displayTitle}</h3>
            {hasBothModes && (
              <div className="heatmap-mode-toggle">
                <button
                  type="button"
                  className={`mode-toggle-btn ${activeMode === 'tags' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveMode('tags');
                    setExpandedSectors(new Set());
                  }}
                >
                  🏷️ Tags ({tags ? tags.length : 0})
                </button>
                <button
                  type="button"
                  className={`mode-toggle-btn ${activeMode === 'sectors' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveMode('sectors');
                    setExpandedSectors(new Set());
                  }}
                >
                  🏭 Sectors ({sectors ? sectors.length : 0})
                </button>
              </div>
            )}
          </div>
          {displaySubtitle && <p className="heatmap-subtitle">{displaySubtitle}</p>}
        </div>

        {showControls && (
          <div className="heatmap-controls">
            <div className="heatmap-search-wrap">
              <span className="heatmap-search-icon">🔍</span>
              <input
                type="text"
                placeholder="Filter sector or stock..."
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
                All ({activeDataset.length})
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'BULLISH' ? 'active' : ''}`}
                onClick={() => setActiveFilter('BULLISH')}
              >
                Bullish Breadth
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'BEARISH' ? 'active' : ''}`}
                onClick={() => setActiveFilter('BEARISH')}
              >
                Bearish Breadth
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'NEAR_HIGH' ? 'active' : ''}`}
                onClick={() => setActiveFilter('NEAR_HIGH')}
              >
                Near 52W High
              </button>
              <button
                type="button"
                className={`filter-pill ${activeFilter === 'TOP_GAINERS' ? 'active' : ''}`}
                onClick={() => setActiveFilter('TOP_GAINERS')}
              >
                1D Gainers
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Main Matrix Table ─────────────────────────────── */}
      {displayedSectors.length === 0 ? (
        <div className="heatmap-empty-state">
          <span className="empty-icon">📊</span>
          <p>{searchQuery ? 'No sectors matching your search query.' : 'No sectoral matrix data available yet.'}</p>
        </div>
      ) : (
        <div className="heatmap-table-container">
          <table className="heatmap-table">
            <thead>
              <tr>
                <th
                  className={`col-sector-name ${sortKey === 'label' ? 'sorted' : ''}`}
                  onClick={() => handleSort('label')}
                >
                  <div className="th-content">
                    <span>{entityLabel}</span>
                    {sortKey === 'label' && (
                      <span className="sort-indicator">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </div>
                </th>

                <th
                  className={`col-weight ${sortKey === 'weight' ? 'sorted' : ''}`}
                  onClick={() => handleSort('weight')}
                >
                  <div className="th-content center">
                    <span>WEIGHT</span>
                    {sortKey === 'weight' && (
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
              </tr>
            </thead>

            <tbody>
              {displayedSectors.map((sector) => {
                const isExpanded = expandedSectors.has(sector.id);
                const high52Style = get52WHighStyle(sector.drawdown_52w_high);
                const ret1DStyle = getReturnStyle(sector.return_1d);
                const ret1WStyle = getReturnStyle(sector.return_1w);
                const ret1MStyle = getReturnStyle(sector.return_1m);
                const ret3MStyle = getReturnStyle(sector.return_3m);
                const ret6MStyle = getReturnStyle(sector.return_6m);
                const ret1YStyle = getReturnStyle(sector.return_1y);
                const ret2YStyle = getReturnStyle(sector.return_2y);

                return (
                  <RowGroup
                    key={sector.id}
                    sector={sector}
                    isExpanded={isExpanded}
                    onToggle={() => toggleRow(sector.id)}
                    high52Style={high52Style}
                    ret1DStyle={ret1DStyle}
                    ret1WStyle={ret1WStyle}
                    ret1MStyle={ret1MStyle}
                    ret3MStyle={ret3MStyle}
                    ret6MStyle={ret6MStyle}
                    ret1YStyle={ret1YStyle}
                    ret2YStyle={ret2YStyle}
                    isSectorMode={isSectorMode}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Expand All Rows or Toggle Limit ───────────────── */}
      <div className="heatmap-footer">
        {hasMoreRows && (
          <button
            type="button"
            className="heatmap-expand-btn"
            onClick={() => setIsExpandedLimit((prev) => !prev)}
          >
            {isExpandedLimit
              ? `↑ Collapse to Top ${defaultLimit} ${entityLabel === 'TAG' ? 'Tags' : 'Sectors'}`
              : `↓ Show All ${filteredSectors.length} ${entityLabel === 'TAG' ? 'Tags' : 'Sectors'}`}
          </button>
        )}

        {allowExpandAll && displayedSectors.length > 0 && (
          <button
            type="button"
            className="heatmap-accordion-all-btn"
            onClick={toggleExpandAll}
          >
            {expandedSectors.size > 0 ? '− Collapse All Stocks' : '+ Expand All Stocks'}
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * RowGroup Sub-component: Renders the parent sector row and its nested accordion subtable.
 */
function RowGroup({
  sector,
  isExpanded,
  onToggle,
  high52Style,
  ret1DStyle,
  ret1WStyle,
  ret1MStyle,
  ret3MStyle,
  ret6MStyle,
  ret1YStyle,
  ret2YStyle,
  isSectorMode = false,
}) {
  return (
    <>
      <tr className={`heatmap-row ${isExpanded ? 'expanded' : ''}`}>
        {/* Sector Name Column */}
        <td className="cell-sector-name">
          <div className="sector-label-wrap">
            <button
              type="button"
              className="accordion-toggle-btn"
              onClick={onToggle}
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
              disabled={!sector.stocks || sector.stocks.length === 0}
              style={{
                opacity: (!sector.stocks || sector.stocks.length === 0) ? 0.35 : 1,
                cursor: (!sector.stocks || sector.stocks.length === 0) ? 'default' : 'pointer',
              }}
            >
              {isExpanded ? '−' : '+'}
            </button>
            <Link
              href={isSectorMode ? `/stocks?sector=${encodeURIComponent(sector.label)}` : `/tags/${encodeURIComponent(sector.label)}`}
              className="sector-name-link"
            >
              <span className="sector-title">{sector.label}</span>
            </Link>
          </div>
        </td>

        {/* Advance-Decline Weight Bar */}
        <td className="cell-weight">
          <AdvanceDeclineBar
            advancing={sector.advancing_count}
            declining={sector.declining_count}
            unchanged={sector.unchanged_count}
            total={sector.stock_count}
          />
        </td>

        {/* 52W High Cell */}
        <td className="cell-matrix">
          {sector.drawdown_52w_high != null ? (
            <div className={`matrix-cell-badge ${high52Style.className}`}>
              {formatPercent(sector.drawdown_52w_high, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 1D Return Cell */}
        <td className="cell-matrix">
          {sector.return_1d != null ? (
            <div className={`matrix-cell-badge ${ret1DStyle.className}`}>
              {formatPercent(sector.return_1d, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 1W Return Cell */}
        <td className="cell-matrix">
          {sector.return_1w != null ? (
            <div className={`matrix-cell-badge ${ret1WStyle.className}`}>
              {formatPercent(sector.return_1w, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 1M Return Cell */}
        <td className="cell-matrix">
          {sector.return_1m != null ? (
            <div className={`matrix-cell-badge ${ret1MStyle.className}`}>
              {formatPercent(sector.return_1m, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 3M Return Cell */}
        <td className="cell-matrix">
          {sector.return_3m != null ? (
            <div className={`matrix-cell-badge ${ret3MStyle.className}`}>
              {formatPercent(sector.return_3m, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 6M Return Cell */}
        <td className="cell-matrix">
          {sector.return_6m != null ? (
            <div className={`matrix-cell-badge ${ret6MStyle.className}`}>
              {formatPercent(sector.return_6m, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 1YR* Return Cell */}
        <td className="cell-matrix">
          {sector.return_1y != null ? (
            <div className={`matrix-cell-badge ${ret1YStyle.className}`}>
              {formatPercent(sector.return_1y, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>

        {/* 2YR* Return Cell */}
        <td className="cell-matrix">
          {sector.return_2y != null ? (
            <div className={`matrix-cell-badge ${ret2YStyle.className}`}>
              {formatPercent(sector.return_2y, false)}
            </div>
          ) : (
            <div className="matrix-cell-empty">—</div>
          )}
        </td>
      </tr>

      {/* Expanded Accordion Sub-row for Constituent Stocks */}
      {isExpanded && (
        <tr className="subtable-container-row">
          <td colSpan={10} className="subtable-container-cell">
            <ConstituentStocksTable
              stocks={sector.stocks}
              sectorName={sector.label}
            />
          </td>
        </tr>
      )}
    </>
  );
}
