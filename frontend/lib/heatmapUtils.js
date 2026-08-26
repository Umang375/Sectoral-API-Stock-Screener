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
