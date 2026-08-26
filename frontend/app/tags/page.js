/**
 * Tags & Sectors Page — displays the full Sector Performance & Market Breadth Heatmap Table.
 * Server Component
 */

import { getTags } from '@/lib/api';
import SectorHeatmapTable from '@/components/SectorHeatmap/SectorHeatmapTable';

export const dynamic = 'force-dynamic';

export default async function TagsPage() {
  let tags = [];
  let error = null;

  try {
    tags = await getTags(0, 200);
  } catch (err) {
    error = err.message;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Top Sectors</h2>
        <p>AI-classified industry cohorts, advance-decline breadth, and multi-period return heatmaps</p>
      </div>

      {error ? (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>Failed to load sector data: {error}</p>
        </div>
      ) : tags.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🏷️</div>
          <p>No sector tags generated yet. Run a screener to start classifying stocks.</p>
        </div>
      ) : (
        <SectorHeatmapTable
          sectors={tags}
          title="Top Sectors"
          subtitle={`Tracking ${tags.length} sector cohorts and constituent equities`}
          showControls={true}
          allowExpandAll={true}
        />
      )}
    </div>
  );
}
