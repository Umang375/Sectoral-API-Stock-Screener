'use client';

/**
 * Dashboard page — homepage showing top stocks, top tags, and recent alerts.
 *
 * Uses the BFF endpoint (GET /api/dashboard) for a single fetch.
 * All styling comes from styles/dashboard.css (imported in layout.js).
 */

import { useEffect, useState } from 'react';
import { getDashboard } from '@/lib/api';

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Weekly performance overview for tracked stocks and sectors</p>
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
          <div className={`stat-value ${data.top_stocks_this_week[0]?.return_pct >= 0 ? 'green' : 'red'}`}>
            {data.top_stocks_this_week[0]
              ? `${data.top_stocks_this_week[0].return_pct > 0 ? '+' : ''}${data.top_stocks_this_week[0].return_pct.toFixed(2)}%`
              : '—'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Alerts Today</div>
          <div className="stat-value">{data.recent_alerts.length}</div>
        </div>
      </div>

      {/* ── Option B: Left col = Today + Weekly stocks, Right col = Sectors */}
      <div className="dashboard-grid">
        {/* ── Left Column: Stocks ──────────────────────────── */}
        <div>
          {/* Top Stocks Today */}
          <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
            <div className="card-header">
              <span className="card-title">🔥 Top Stocks Today</span>
            </div>
            {(data.top_stocks_today?.length ?? 0) === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📈</div>
                <p>No daily data yet. Run a screener to get started.</p>
              </div>
            ) : (
              data.top_stocks_today?.map((stock, i) => (
                <div key={i} className="performer-item">
                  <div className="performer-info">
                    <span className="performer-symbol">{stock.symbol}</span>
                    <div className="performer-tags">
                      {stock.tags.slice(0, 3).map((tag, j) => (
                        <span key={j} className="badge badge-accent">{tag}</span>
                      ))}
                    </div>
                  </div>
                  <span className={`performer-return ${stock.return_pct >= 0 ? 'text-green' : 'text-red'}`}>
                    {stock.return_pct > 0 ? '+' : ''}{stock.return_pct.toFixed(2)}%
                  </span>
                </div>
              ))
            )}
          </div>

          {/* Top Stocks This Week */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">🏆 Top Stocks This Week</span>
            </div>
            {data.top_stocks_this_week.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📈</div>
                <p>No weekly returns data yet. Data appears after the first week.</p>
              </div>
            ) : (
              data.top_stocks_this_week.map((stock, i) => (
                <div key={i} className="performer-item">
                  <div className="performer-info">
                    <span className="performer-symbol">{stock.symbol}</span>
                    <div className="performer-tags">
                      {stock.tags.slice(0, 3).map((tag, j) => (
                        <span key={j} className="badge badge-accent">{tag}</span>
                      ))}
                    </div>
                  </div>
                  <span className={`performer-return ${stock.return_pct >= 0 ? 'text-green' : 'text-red'}`}>
                    {stock.return_pct > 0 ? '+' : ''}{stock.return_pct.toFixed(2)}%
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── Right Column: Sectors ────────────────────────── */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">🏷️ Top Sectors This Week</span>
          </div>
          {data.top_tags_this_week.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🏷️</div>
              <p>No tag returns yet. Data will appear after the first week.</p>
            </div>
          ) : (
            data.top_tags_this_week.map((tag, i) => (
              <div key={i} className="performer-item">
                <div className="performer-info">
                  <span className="performer-symbol">{tag.tag}</span>
                  <span className="text-muted" style={{ fontSize: '0.75rem' }}>
                    {tag.stock_count} stocks
                  </span>
                </div>
                <span className={`performer-return ${tag.avg_return_pct >= 0 ? 'text-green' : 'text-red'}`}>
                  {tag.avg_return_pct > 0 ? '+' : ''}{tag.avg_return_pct.toFixed(2)}%
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Recent Alerts ─────────────────────────────────── */}
      <div className="card" style={{ marginTop: 'var(--space-6)' }}>
        <div className="card-header">
          <span className="card-title">⚡ Recent Alerts</span>
        </div>
        {data.recent_alerts.length === 0 ? (
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
                  <strong>{alert.stock}</strong> — {alert.alert_type.replace(/_/g, ' ')}
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

/* ── Loading Skeleton ──────────────────────────────────────── */
function DashboardSkeleton() {
  return (
    <div>
      <div className="page-header">
        <div className="skeleton" style={{ width: 200, height: 28, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 350, height: 16 }} />
      </div>
      <div className="stats-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-card">
            <div className="skeleton" style={{ width: 80, height: 12, marginBottom: 12 }} />
            <div className="skeleton" style={{ width: 60, height: 32 }} />
          </div>
        ))}
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
      <p className="text-muted" style={{ marginTop: 8, fontSize: '0.8rem' }}>
        Make sure the backend is running at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
      </p>
    </div>
  );
}
