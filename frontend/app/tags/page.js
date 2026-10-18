/**
 * Tags & Sectors Page — displays performance & breadth heatmaps for AI tags and industry sectors.
 * Server Component
 */

import { getStocks, getTags } from '@/lib/api';
import SectorHeatmapTable from '@/components/SectorHeatmap/SectorHeatmapTable';

export const dynamic = 'force-dynamic';

function aggregateSectorsFromStocks(stocks) {
  if (!Array.isArray(stocks)) return [];

  const sectorsMap = new Map();

  for (const stock of stocks) {
    const sectorName = stock.sector?.trim() || 'Diversified / Others';
    if (!sectorsMap.has(sectorName)) {
      sectorsMap.set(sectorName, {
        id: `sector-${sectorName}`,
        label: sectorName,
        stocks: [],
        drawdownList: [],
        ret1DList: [],
        ret1WList: [],
        ret1MList: [],
        ret3MList: [],
        ret6MList: [],
        ret1YList: [],
        ret2YList: [],
      });
    }

    const sec = sectorsMap.get(sectorName);
    sec.stocks.push({
      symbol: stock.symbol,
      name: stock.name,
      ltp: stock.ltp,
      change_pct: stock.change_pct,
      drawdown_52w_high: stock.drawdown_52w_high,
      volume: stock.volume,
    });

    if (stock.drawdown_52w_high != null) sec.drawdownList.push(stock.drawdown_52w_high);
    if (stock.return_1d != null) sec.ret1DList.push(stock.return_1d);
    if (stock.return_1w != null) sec.ret1WList.push(stock.return_1w);
    if (stock.return_1m != null) sec.ret1MList.push(stock.return_1m);
    if (stock.return_3m != null) sec.ret3MList.push(stock.return_3m);
    if (stock.return_6m != null) sec.ret6MList.push(stock.return_6m);
    if (stock.return_1y != null) sec.ret1YList.push(stock.return_1y);
    if (stock.return_2y != null) sec.ret2YList.push(stock.return_2y);
  }

  const calcAvg = (arr) => arr.length ? Number((arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1)) : null;

  const result = [];
  for (const sec of sectorsMap.values()) {
    const advancing_count = sec.stocks.filter((s) => s.change_pct != null && s.change_pct > 0).length;
    const declining_count = sec.stocks.filter((s) => s.change_pct != null && s.change_pct < 0).length;
    const unchanged_count = sec.stocks.length - advancing_count - declining_count;

    result.push({
      id: sec.id,
      label: sec.label,
      stock_count: sec.stocks.length,
      advancing_count,
      declining_count,
      unchanged_count,
      drawdown_52w_high: calcAvg(sec.drawdownList),
      return_1d: calcAvg(sec.ret1DList),
      return_1w: calcAvg(sec.ret1WList),
      return_1m: calcAvg(sec.ret1MList),
      return_3m: calcAvg(sec.ret3MList),
      return_6m: calcAvg(sec.ret6MList),
      return_1y: calcAvg(sec.ret1YList),
      return_2y: calcAvg(sec.ret2YList),
      stocks: sec.stocks,
    });
  }

  result.sort((a, b) => b.stock_count - a.stock_count);
  return result;
}

export default async function TagsPage() {
  let tags = [];
  let sectors = [];
  let error = null;

  try {
    const [tagsRes, stocksRes] = await Promise.allSettled([
      getTags(0, 200),
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

      {error && !hasData ? (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>Failed to load data: {error}</p>
        </div>
      ) : !hasData ? (
        <div className="empty-state">
          <div className="empty-icon">🏷️</div>
          <p>No tags or sectors generated yet. Run a screener to start classifying stocks.</p>
        </div>
      ) : (
        <SectorHeatmapTable
          tags={tags}
          sectors={sectors}
          defaultMode="tags"
          showControls={true}
          allowExpandAll={true}
        />
      )}
    </div>
  );
}
