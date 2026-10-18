'use client';

import dynamic from 'next/dynamic';

const TradingViewStockChart = dynamic(
  () => import('./TradingViewStockChart'),
  {
    ssr: false,
    loading: () => (
      <div className="tv-chart-loading">
        <div className="spinner" />
        <p>Loading interactive candlestick chart...</p>
      </div>
    ),
  }
);

/**
 * StockChartWrapper
 * Client-boundary wrapper enabling ssr: false dynamic import of TradingView Lightweight Charts
 * within Next.js App Router Server Components.
 */
export default function StockChartWrapper({ symbol, snapshots, height = 500 }) {
  return (
    <TradingViewStockChart
      symbol={symbol}
      snapshots={snapshots}
      height={height}
    />
  );
}
