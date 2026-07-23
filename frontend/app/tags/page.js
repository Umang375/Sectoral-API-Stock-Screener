'use client';

/**
 * Tags page — lists all active tags sorted by popularity.
 * When a tag is clicked, it fetches and shows its weekly returns history
 * using CSS-based horizontal bar charts.
 */

import { useEffect, useState } from 'react';
import { getTags, getTagReturns } from '@/lib/api';

export default function TagsPage() {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Detail view state
  const [selectedTag, setSelectedTag] = useState(null);
  const [returnsData, setReturnsData] = useState(null);
  const [returnsLoading, setReturnsLoading] = useState(false);
  const [returnsError, setReturnsError] = useState(null);

  useEffect(() => {
    getTags(0, 100)
      .then(setTags)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectTag = async (tagLabel) => {
    setSelectedTag(tagLabel);
    setReturnsLoading(true);
    setReturnsError(null);
    setReturnsData(null);
    
    try {
      const data = await getTagReturns(tagLabel, 12);
      setReturnsData(data);
    } catch (err) {
      setReturnsError(err.message);
    } finally {
      setReturnsLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedTag(null);
    setReturnsData(null);
  };

  if (loading && !selectedTag) {
    return (
      <div>
        <div className="page-header">
          <h2>Tags & Returns</h2>
          <p>AI-generated sector cohorts and their historical performance</p>
        </div>
        <div className="tags-grid">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card">
              <div className="skeleton" style={{ width: 120, height: 20, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: 80, height: 16 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Detail View: Returns Chart ───────────────────────────
  if (selectedTag) {
    return (
      <div>
        <div className="page-header">
          <h2>{selectedTag}</h2>
          <p>Cohort performance analysis</p>
        </div>

        <div className="card">
          <div className="returns-title">
            <button className="back-btn" onClick={handleBack}>
              ← Back to Tags
            </button>
            <span style={{ marginLeft: '12px' }}>Weekly Returns History</span>
          </div>

          {returnsLoading ? (
            <div style={{ padding: '40px 0', textAlign: 'center' }}>
              <div className="skeleton" style={{ width: '100%', height: 200 }} />
            </div>
          ) : returnsError ? (
            <div className="empty-state">
              <div className="empty-icon">⚠️</div>
              <p>{returnsError}</p>
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
                  // Format dates
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
                          {/* Value is shown outside for better legibility if bar is small */}
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

  // ── List View: Tag Grid ──────────────────────────────────
  return (
    <div>
      <div className="page-header">
        <h2>Tags</h2>
        <p>AI-generated sector cohorts sorted by popularity</p>
      </div>

      {error ? (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>{error}</p>
        </div>
      ) : tags.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🏷️</div>
          <p>No tags generated yet. Run a screener to start classifying stocks.</p>
        </div>
      ) : (
        <div className="tags-grid">
          {tags.map((tag) => (
            <div 
              key={tag.id} 
              className="tag-card"
              onClick={() => handleSelectTag(tag.label)}
            >
              <div className="tag-label">{tag.label}</div>
              <div className="tag-meta">
                <span className="tag-stock-count">
                  <strong>{tag.stock_count}</strong> tracked stocks
                </span>
                <span className="text-muted" style={{ fontSize: '0.8rem' }}>View returns →</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
