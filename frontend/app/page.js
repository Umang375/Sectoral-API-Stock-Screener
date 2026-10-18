/**
 * Dashboard page — homepage displaying stats overview, Top Sectors matrix,
 * Top Stocks matrix, and real-time webhook alerts.
 * Server Component
 */

import Link from 'next/link';
import { getDashboard, getStocks, getTags } from '@/lib/api';
import SectorHeatmapTable from '@/components/SectorHeatmap/SectorHeatmapTable';
import StockHeatmapTable from '@/components/SectorHeatmap/StockHeatmapTable';
import StockLifecycleBoxes from '@/components/Dashboard/StockLifecycleBoxes';
import { aggregateSectorsFromStocks } from '@/lib/heatmapUtils';

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  let data = null;
  let tags = [];
  let stocks = [];
  let error = null;

  try {
    const [dashboardRes, tagsRes, stocksRes] = await Promise.allSettled([
      getDashboard(),
      getTags(0, 200).catch(() => getTags(0, 100)),
      getStocks(0, 500).catch(() => getStocks(0, 100)),
    ]);

    if (dashboardRes.status === 'fulfilled') {
      data = dashboardRes.value;
    } else {
      error = dashboardRes.reason?.message || 'Failed to load dashboard data';
    }

    if (tagsRes.status === 'fulfilled') {
      tags = tagsRes.value || [];
    }

    if (stocksRes.status === 'fulfilled') {
      stocks = stocksRes.value || [];
    }
  } catch (err) {
    error = err.message;
  }

  if (error && !data) return <ErrorState message={error} />;
  if (!data) return null;

  const sectors = aggregateSectorsFromStocks(stocks);

  const topStock = data.top_stocks_this_week?.[0];
  const hasValidReturn = Boolean(topStock?.is_complete && typeof topStock?.return_pct === 'number');
  const returnClass = hasValidReturn
    ? (topStock.return_pct >= 0 ? 'green' : 'red')
    : '';

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>End-of-day performance overview for tracked equities and sector cohorts</p>
      </div>

      {/* ── Stats Grid ────────────────────────────────────── */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Stocks Tracked</div>
          <div className="stat-value">{data.total_stocks_tracked}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active Tags</div>
          <div className="stat-value">{data.total_tags}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Top Return</div>
          <div className={`stat-value ${returnClass}`.trim()}>
            {hasValidReturn
              ? `${topStock.return_pct > 0 ? '+' : ''}${topStock.return_pct.toFixed(2)}%`
              : '—'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Alerts Today</div>
          <div className="stat-value">{data.recent_alerts?.length || 0}</div>
        </div>
      </div>

      {/* ── Stock Lifecycle: Dumped & Added Boxes ─────────── */}
      <StockLifecycleBoxes
        dumpedStocks={data.dumped_stocks || []}
        addedStocks={data.recently_added_stocks || []}
      />

      {/* ── Top Tags & Sectors Heatmap Matrix ──────────────── */}
      <div className="dashboard-heatmap-wrap">
        <SectorHeatmapTable
          tags={tags}
          sectors={sectors}
          defaultMode="tags"
          defaultLimit={8}
          showControls={true}
          allowExpandAll={true}
        />
      </div>

      {/* ── Top Stocks Heatmap Matrix ───────────────────────── */}
      {stocks.length > 0 && (
        <div className="dashboard-heatmap-wrap">
          <StockHeatmapTable
            stocks={stocks}
            title="Top Stocks"
            subtitle="Multi-period equity returns, 52W high distance, sector tags, and volume"
            defaultLimit={10}
            showControls={true}
          />
        </div>
      )}

      {/* ── Recent Alerts Feed ──────────────────────────────── */}
      <div className="card card-mb">
        <div className="card-header">
          <span className="card-title">⚡ Recent Alerts</span>
        </div>
        {(data.recent_alerts?.length ?? 0) === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⚡</div>
            <p>No webhook alerts received yet.</p>
          </div>
        ) : (
          data.recent_alerts.map((alert, i) => (
            <div key={i} className="alert-item">
              <div className="alert-dot" />
              <div className="alert-content">
                <div className="alert-title">
                  <Link
                    href={`/stocks/${encodeURIComponent(alert.stock)}`}
                    className="alert-stock-link"
                  >
                    <strong>{alert.stock}</strong>
                  </Link>{' '}
                  — {alert.alert_type.replace(/_/g, ' ')}
                </div>
                <div className="alert-time">{alert.time}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/* ── Error State ───────────────────────────────────────────── */
function ErrorState({ message }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">⚠️</div>
      <p>Failed to load dashboard: {message}</p>
      <p className="text-muted error-muted-note">
        Make sure the backend is running at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
      </p>
    </div>
  );
}
