/**
 * Tags & Sectors Page — displays performance & breadth heatmaps for AI tags and industry sectors.
 * Server Component
 */

import { getStocks, getTags } from '@/lib/api';
import SectorHeatmapTable from '@/components/SectorHeatmap/SectorHeatmapTable';
import { aggregateSectorsFromStocks } from '@/lib/heatmapUtils';

export const dynamic = 'force-dynamic';

export default async function TagsPage() {
  let tags = [];
  let sectors = [];
  let error = null;

  try {
    const [tagsRes, stocksRes] = await Promise.allSettled([
      getTags(0, 500),
      getStocks(0, 500),
    ]);

    if (tagsRes.status === 'fulfilled') {
      tags = tagsRes.value || [];
    } else {
      error = tagsRes.reason?.message;
    }

    if (stocksRes.status === 'fulfilled') {
      sectors = aggregateSectorsFromStocks(stocksRes.value || []);
    }
  } catch (err) {
    error = err.message;
  }

  const hasData = tags.length > 0 || sectors.length > 0;

  return (
    <div>
      <div className="page-header">
        <h2>Tags & Sectors</h2>
        <p>Market breadth, 52W high drawdown, and multi-period return heatmaps</p>
      </div>

      {error && (
        <div className="empty-state" style={{ marginBottom: '24px' }}>
          <div className="empty-icon">⚠️</div>
          <p>Failed to load data: {error}</p>
        </div>
      )}

      <SectorHeatmapTable
        tags={tags}
        sectors={sectors}
        defaultMode="tags"
        pageSize={150}
        showControls={true}
        allowExpandAll={true}
      />
    </div>
  );
}
