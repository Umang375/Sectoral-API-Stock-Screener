/**
 * Tag Detail page — shows weekly returns history for a specific tag.
 * Server Component
 */

import { getTagReturns } from '@/lib/api';
import Link from 'next/link';

export default async function TagDetailPage({ params }) {
  const resolvedParams = await params;
  const tagLabel = decodeURIComponent(resolvedParams.tag);

  let returnsData = null;
  let error = null;

  try {
    returnsData = await getTagReturns(tagLabel, 12);
  } catch (err) {
    error = err.message;
  }

  return (
    <div>
      <div className="page-header">
        <h2>{tagLabel}</h2>
        <p>Cohort performance analysis</p>
      </div>

      <div className="card">
        <div className="returns-title">
          <Link href="/tags" className="back-btn" style={{ textDecoration: 'none' }}>
            ← Back to Tags
          </Link>
          <span style={{ marginLeft: '12px' }}>Weekly Returns History</span>
        </div>

        {error ? (
          <div className="empty-state">
            <div className="empty-icon">⚠️</div>
            <p>{error}</p>
          </div>
        ) : returnsData?.returns?.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <p>No historical returns data for this cohort yet.</p>
            <p className="text-muted" style={{ marginTop: 8, fontSize: '0.8rem' }}>
              Returns are calculated every Monday at 7:00 AM.
            </p>
          </div>
        ) : (
          <div className="returns-section">
            {/* Stats overview of the latest week */}
            <div className="return-stats">
              <div className="return-stat-item">
                <div className="label">Current Stocks</div>
                <div className="value">{returnsData?.returns[0]?.stock_count || 0}</div>
              </div>
              <div className="return-stat-item">
                <div className="label">Latest Avg Return</div>
                <div className={`value ${returnsData?.returns[0]?.avg_return_pct >= 0 ? 'text-green' : 'text-red'}`}>
                  {returnsData?.returns[0]?.avg_return_pct > 0 ? '+' : ''}
                  {(returnsData?.returns[0]?.avg_return_pct || 0).toFixed(2)}%
                </div>
              </div>
              <div className="return-stat-item">
                <div className="label">Latest Median Return</div>
                <div className={`value ${returnsData?.returns[0]?.median_return_pct >= 0 ? 'text-green' : 'text-red'}`}>
                  {returnsData?.returns[0]?.median_return_pct > 0 ? '+' : ''}
                  {(returnsData?.returns[0]?.median_return_pct || 0).toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="returns-chart">
              {returnsData?.returns.map((ret, idx) => {
                // Server-side date formatting
                const start = new Date(ret.week_start).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
                const end = new Date(ret.week_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
                
                // Calculate bar width (max 20% for scale)
                const absVal = Math.abs(ret.avg_return_pct);
                const widthPct = Math.min(100, (absVal / 20) * 100);
                const isPositive = ret.avg_return_pct >= 0;

                return (
                  <div key={idx} className="return-bar-row">
                    <div className="return-bar-label">{start} - {end}</div>
                    <div className="return-bar-track">
                      <div className="return-bar-center" />
                      <div 
                        className={`return-bar-fill ${isPositive ? 'positive' : 'negative'}`}
                        style={{ width: `calc(${widthPct / 2}% + 10px)` }}
                      >
                      </div>
                    </div>
                    <div className={`return-bar-value ${isPositive ? 'text-green' : 'text-red'}`}>
                      {isPositive ? '+' : ''}{ret.avg_return_pct.toFixed(2)}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
