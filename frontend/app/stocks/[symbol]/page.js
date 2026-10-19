/**
 * Stock Detail Page — dedicated equity view with TradingView Candlestick Chart,
 * sector taxonomy, Gemini AI cohort tags, and multi-period return snapshots.
 * Server Component
 */

import Link from 'next/link';
import { getStock, getStockHistory, getStockReturns } from '@/lib/api';
import { formatPercent } from '@/lib/heatmapUtils';
import StockChartWrapper from '@/components/Charts/StockChartWrapper';

export const dynamicParams = true;

function formatCurrency(val) {
  if (val == null || isNaN(val)) return '—';
  return '₹' + Number(val).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatVolume(val) {
  if (val == null || isNaN(val)) return '—';
  const num = Number(val);
  if (num >= 10000000) return (num / 10000000).toFixed(2) + ' Cr';
  if (num >= 100000) return (num / 100000).toFixed(2) + ' L';
  if (num >= 1000) return (num / 1000).toFixed(1) + ' K';
  return num.toLocaleString('en-IN');
}

export default async function StockDetailPage({ params }) {
  const resolvedParams = await params;
  const symbol = decodeURIComponent(resolvedParams.symbol).toUpperCase();

  let stock = null;
  let history = [];
  let returns = [];
  let error = null;

  try {
    const [stockRes, historyRes, returnsRes] = await Promise.allSettled([
      getStock(symbol),
      getStockHistory(symbol, 0, 750),
      getStockReturns(symbol, 12),
    ]);

    if (stockRes.status === 'fulfilled') {
      stock = stockRes.value;
    } else {
      throw new Error(stockRes.reason?.message || `Stock '${symbol}' not found`);
    }

    if (historyRes.status === 'fulfilled') {
      history = historyRes.value;
    }

    if (returnsRes.status === 'fulfilled') {
      returns = returnsRes.value;
    }
  } catch (err) {
    error = err.message;
  }

  if (error || !stock) {
    return (
      <div className="stock-detail-page">
        <div className="stock-detail-back">
          <Link href="/stocks" className="back-btn">
            ← Back to Stocks
          </Link>
        </div>
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <h3>Stock Not Found</h3>
          <p>{error || `We could not locate data for symbol ${symbol}.`}</p>
        </div>
      </div>
    );
  }

  const latest = stock.latest_snapshot || {};
  const ltp = latest.ltp;
  const changePct = latest.change_pct;
  const isPositive = changePct != null && changePct >= 0;

  // Calculate 52-week high drawdown from stock or history within 365 calendar days
  let high52w = stock.high_52w ?? null;
  let drawdown52w = stock.drawdown_52w_high ?? null;

  if ((high52w == null || drawdown52w == null) && history.length > 0) {
    // 52 weeks corresponds to 365 calendar days (~250 trading days) from latest snapshot
    const refDate = history[0].date ? new Date(history[0].date) : new Date();
    const msInDay = 24 * 60 * 60 * 1000;
    const history52w = history.filter((h) => {
      if (!h.date) return false;
      const d = new Date(h.date);
      const diffDays = (refDate - d) / msInDay;
      return diffDays >= 0 && diffDays <= 365;
    });

    // Fallback to latest 252 trading sessions if date filtering yielded empty
    const targetHistory = history52w.length > 0 ? history52w : history.slice(0, 252);
    const prices = targetHistory
      .map((h) => Number(h.high ?? h.ltp))
      .filter((p) => !isNaN(p) && p > 0);

    if (prices.length > 0) {
      high52w = Math.max(...prices);
      if (ltp && high52w > 0) {
        drawdown52w = ((ltp - high52w) / high52w) * 100;
      }
    }
  }

  return (
    <div className="stock-detail-page">
      {/* ── Breadcrumb & Navigation ───────────────────────── */}
      <div className="stock-detail-back">
        <Link href="/stocks" className="back-btn">
          ← Back to Stocks
        </Link>
      </div>

      {/* ── Stock Master Header ───────────────────────────── */}
      <div className="stock-master-header card">
        <div className="stock-header-main">
          <div className="stock-title-group">
            <div className="stock-badge-row">
              <h1 className="stock-symbol-title">{stock.symbol}</h1>
              {!stock.is_active && (
                <span className="badge badge-dormant" title="Stock is inactive or soft-deleted">
                  Inactive
                </span>
              )}
              {stock.sector && (
                <span className="badge badge-sector">
                  {stock.sector}
                </span>
              )}
            </div>
            {stock.name && <p className="stock-company-name">{stock.name}</p>}

            {/* AI Cohort Tags */}
            {stock.tags && stock.tags.length > 0 && (
              <div className="stock-tags-row">
                <span className="stock-tags-label">AI Tags:</span>
                {stock.tags.map((tag) => (
                  <Link
                    key={tag}
                    href={`/tags/${encodeURIComponent(tag)}`}
                    className="badge badge-accent tag-hover-link"
                  >
                    #{tag}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Real-time Price Spotlight */}
          <div className="stock-spotlight-price">
            <div className="spotlight-ltp">{formatCurrency(ltp)}</div>
            {changePct != null && (
              <div
                className={`spotlight-change ${
                  isPositive ? 'change-positive' : 'change-negative'
                }`}
              >
                {isPositive ? '▲ +' : '▼ '}
                {changePct.toFixed(2)}%
                <span className="spotlight-date-sub"> (1D)</span>
              </div>
            )}
            {latest.date && (
              <div className="spotlight-as-of">As of {latest.date}</div>
            )}
          </div>
        </div>

        {/* ── Key Financial Stat Metrics Strip ─────────────── */}
        <div className="stock-metrics-strip">
          <div className="metric-cell">
            <span className="metric-label">DAY RANGE</span>
            <span className="metric-val">
              {latest.low != null && latest.high != null
                ? `${formatCurrency(latest.low)} – ${formatCurrency(latest.high)}`
                : '—'}
            </span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">52W HIGH</span>
            <span className="metric-val">{formatCurrency(high52w)}</span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">52W DRAWDOWN</span>
            <span
              className={`metric-val ${
                drawdown52w != null && drawdown52w >= -5 ? 'text-green' : 'text-muted'
              }`}
            >
              {drawdown52w != null ? formatPercent(drawdown52w, false) : '—'}
            </span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">VOLUME</span>
            <span className="metric-val">{formatVolume(latest.volume)}</span>
          </div>
        </div>
      </div>

      {/* ── Interactive TradingView Chart Section ─────────── */}
      <div className="card stock-chart-card">
        <div className="card-header-clean">
          <div>
            <h3 className="section-title">Interactive Technical Chart</h3>
            <p className="section-subtitle">
              TradingView Lightweight Candlestick with Volume histogram & interactive crosshair
            </p>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <p>No historical price snapshot data available for {stock.symbol}.</p>
          </div>
        ) : (
          <StockChartWrapper
            symbol={stock.symbol}
            snapshots={history}
            height={500}
          />
        )}
      </div>

      {/* ── Performance & Snapshot Data Section ────────────── */}
      <div className="stock-bottom-grid">
        {/* Weekly Returns History */}
        <div className="card">
          <h3 className="section-title">Weekly Return Intervals</h3>
          <p className="section-subtitle">Last 12 weekly trading windows</p>

          {returns.length === 0 ? (
            <div className="empty-state">
              <p>No weekly return intervals calculated yet.</p>
            </div>
          ) : (
            <div className="returns-table-wrapper">
              <table className="mini-data-table">
                <thead>
                  <tr>
                    <th>WEEK START</th>
                    <th>OPEN</th>
                    <th>CLOSE</th>
                    <th className="text-right">RETURN</th>
                  </tr>
                </thead>
                <tbody>
                  {returns.map((r, idx) => (
                    <tr key={idx}>
                      <td>{r.week_start}</td>
                      <td>{formatCurrency(r.open_ltp)}</td>
                      <td>{formatCurrency(r.close_ltp)}</td>
                      <td
                        className={`text-right font-medium ${
                          r.is_positive ? 'text-green' : 'text-red'
                        }`}
                      >
                        {r.return_pct != null
                          ? `${r.return_pct > 0 ? '+' : ''}${r.return_pct.toFixed(2)}%`
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Daily Snapshots */}
        <div className="card">
          <h3 className="section-title">Recent Daily Snapshots</h3>
          <p className="section-subtitle">End-of-day prices & volumes</p>

          {history.length === 0 ? (
            <div className="empty-state">
              <p>No daily snapshots available.</p>
            </div>
          ) : (
            <div className="returns-table-wrapper">
              <table className="mini-data-table">
                <thead>
                  <tr>
                    <th>DATE</th>
                    <th>LTP</th>
                    <th className="text-right">1D CHG</th>
                    <th className="text-right">VOLUME</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 10).map((h, idx) => (
                    <tr key={idx}>
                      <td>{h.date}</td>
                      <td className="font-semibold">{formatCurrency(h.close ?? h.ltp)}</td>
                      <td
                        className={`text-right ${
                          h.change_pct != null && h.change_pct >= 0 ? 'text-green' : 'text-red'
                        }`}
                      >
                        {h.change_pct != null
                          ? `${h.change_pct > 0 ? '+' : ''}${h.change_pct.toFixed(2)}%`
                          : '—'}
                      </td>
                      <td className="text-right">{formatVolume(h.volume)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
