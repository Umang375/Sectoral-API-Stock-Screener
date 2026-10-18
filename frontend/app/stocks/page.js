/**
 * Stocks page — full searchable performance heatmap matrix of all tracked equities.
 * Server Component
 */

import { getStocks } from '@/lib/api';
import StockHeatmapTable from '@/components/SectorHeatmap/StockHeatmapTable';

export const revalidate = 300;

export default async function StocksPage() {
  let stocks = [];
  let error = null;

  try {
    stocks = await getStocks(0, 200);
  } catch (err) {
    error = err.message;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Top Stocks</h2>
        <p>All tracked equities with 52W high drawdown, multi-period return heatmaps, and volume</p>
      </div>

      {error ? (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>Failed to load stock data: {error}</p>
        </div>
      ) : stocks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📈</div>
          <p>No stocks tracked yet. Run a screener to get started.</p>
        </div>
      ) : (
        <StockHeatmapTable
          stocks={stocks}
          title="Top Stocks"
          subtitle={`Tracking ${stocks.length} equities across Indian equity sectors`}
          showControls={true}
        />
      )}
    </div>
  );
}
