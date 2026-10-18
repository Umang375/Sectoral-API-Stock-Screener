/**
 * Heatmap utility functions for financial matrix color scales and formatting.
 *
 * Implements color harmonies matching professional trading terminals:
 * - High Gains: Deep emerald green with white text
 * - Moderate Gains: Vivid leaf green with dark text
 * - Mild Gains: Soft mint with dark text
 * - Neutral: Ivory / cream with dark text
 * - Mild Losses: Soft blush pink with dark text
 * - Moderate Losses: Salmon / coral red with dark text
 * - Deep Losses / Drawdowns: Crimson / dark burgundy with white text
 */

/**
 * Returns background and text color styling for a return percentage value.
 * @param {number|null|undefined} val - Return percentage (e.g. 10.6, -1.2, null)
 * @returns {{ bg: string, color: string, className: string }}
 */
export function getReturnStyle(val) {
  if (val == null || isNaN(val)) {
    return {
      bg: 'transparent',
      color: 'var(--text-muted)',
      className: 'heatmap-empty',
    };
  }

  // Large positive return >= +10%
  if (val >= 10) {
    return {
      bg: '#15803d',
      color: '#ffffff',
      className: 'heatmap-pos-high',
    };
  }

  // Moderate positive return >= +2%
  if (val >= 2) {
    return {
      bg: '#4ade80',
      color: '#052e16',
      className: 'heatmap-pos-mid',
    };
  }

  // Mild positive return > 0%
  if (val > 0) {
    return {
      bg: '#bbf7d0',
      color: '#064e3b',
      className: 'heatmap-pos-low',
    };
  }

  // Flat / Neutral return = 0%
  if (val === 0) {
    return {
      bg: '#fef3c7',
      color: '#78350f',
      className: 'heatmap-neutral',
    };
  }

  // Mild negative return >= -3%
  if (val >= -3) {
    return {
      bg: '#fee2e2',
      color: '#7f1d1d',
      className: 'heatmap-neg-low',
    };
  }

  // Moderate negative return >= -10%
  if (val >= -10) {
    return {
      bg: '#fca5a5',
      color: '#7f1d1d',
      className: 'heatmap-neg-mid',
    };
  }

  // Deep negative return < -10%
  return {
    bg: '#991b1b',
    color: '#ffffff',
    className: 'heatmap-neg-high',
  };
}

/**
 * Returns background and text color styling for 52-Week High drawdown percentage.
 * (Drawdown is <= 0%, where 0% is at 52-week high, -30% is a deep drawdown).
 * @param {number|null|undefined} val - Drawdown percentage (e.g. 0, -1.9, -15.0)
 * @returns {{ bg: string, color: string, className: string }}
 */
export function get52WHighStyle(val) {
  if (val == null || isNaN(val)) {
    return {
      bg: 'transparent',
      color: 'var(--text-muted)',
      className: 'heatmap-empty',
    };
  }

  // At or near 52W High (0% or > -1%)
  if (val >= -0.5) {
    return {
      bg: '#fef3c7',
      color: '#78350f',
      className: 'drawdown-high',
    };
  }

  // Mild drawdown (-0.5% to -5%)
  if (val >= -5) {
    return {
      bg: '#fca5a5',
      color: '#7f1d1d',
      className: 'drawdown-mild',
    };
  }

  // Moderate drawdown (-5% to -15%)
  if (val >= -15) {
    return {
      bg: '#8e2525',
      color: '#ffffff',
      className: 'drawdown-moderate',
    };
  }

  // Deep drawdown (< -15%)
  return {
    bg: '#581c1c',
    color: '#ffffff',
    className: 'drawdown-deep',
  };
}

/**
 * Formats percentage numbers cleanly.
 * @param {number|null|undefined} val
 * @param {boolean} showPlus - If true, prefixes positive numbers with '+'
 * @returns {string} Formatted string like "+10.6%", "-1.2%", "0%", or "—"
 */
export function formatPercent(val, showPlus = false) {
  if (val == null || isNaN(val)) {
    return '—';
  }
  const formatted = Math.abs(val % 1) < 0.01 ? val.toFixed(0) : val.toFixed(1);
  if (val > 0) {
    return `${showPlus ? '+' : ''}${formatted}%`;
  }
  return `${formatted}%`;
}

/**
 * Aggregates a flat list of stock records into sector cohort matrix objects.
 * @param {Array} stocks
 * @returns {Array} Array of sector objects compatible with SectorHeatmapTable
 */
export function aggregateSectorsFromStocks(stocks) {
  if (!Array.isArray(stocks) || stocks.length === 0) return [];

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
      return_1d: stock.return_1d,
      return_1w: stock.return_1w,
      return_1m: stock.return_1m,
      return_3m: stock.return_3m,
      return_6m: stock.return_6m,
      return_1y: stock.return_1y,
      return_2y: stock.return_2y,
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
