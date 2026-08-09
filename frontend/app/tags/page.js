/**
 * Tags page — lists all active tags sorted by popularity.
 * Server Component
 */

import { getTags } from '@/lib/api';
import Link from 'next/link';

export default async function TagsPage() {
  let tags = [];
  let error = null;

  try {
    tags = await getTags(0, 100);
  } catch (err) {
    error = err.message;
  }

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
            <Link 
              href={`/tags/${encodeURIComponent(tag.label)}`} 
              key={tag.id}
              style={{ textDecoration: 'none' }}
            >
              <div className="tag-card">
                <div className="tag-label">{tag.label}</div>
                <div className="tag-meta">
                  <span className="tag-stock-count">
                    <strong>{tag.stock_count}</strong> tracked stocks
                  </span>
                  <span className="text-muted" style={{ fontSize: '0.8rem' }}>View returns →</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
