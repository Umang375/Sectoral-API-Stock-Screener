'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  createTextWatermark,
} from 'lightweight-charts';

/**
 * Format Indian currency string.
 */
function formatRupee(val) {
  if (val == null || isNaN(val)) return '—';
  return '₹' + Number(val).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatVolume(val) {
  if (val == null || isNaN(val)) return '—';
  const num = Number(val);
  if (num >= 10000000) return (num / 10000000).toFixed(2) + ' Cr';
  if (num >= 100000) return (num / 100000).toFixed(2) + ' L';
  if (num >= 1000) return (num / 1000).toFixed(1) + ' K';
  return num.toLocaleString('en-IN');
}

/**
 * TradingViewStockChart
 * High-performance TradingView Lightweight Chart (v5) component.
 */
export default function TradingViewStockChart({
  symbol = '',
  snapshots = [],
  height = 500,
}) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const mainSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);

  const [activeTimeframe, setActiveTimeframe] = useState('ALL');
  const [chartType, setChartType] = useState('candles'); // 'candles' | 'line'

  // Process snapshots into strictly ascending, deduplicated OHLCV points
  const { candleData, lineData, volumeData, latestBar } = useMemo(() => {
    if (!Array.isArray(snapshots) || snapshots.length === 0) {
      return { candleData: [], lineData: [], volumeData: [], latestBar: null };
    }

    // Sort chronologically ascending
    const sorted = [...snapshots]
      .filter((s) => s.date)
      .sort((a, b) => (a.date > b.date ? 1 : a.date < b.date ? -1 : 0));

    const seenDates = new Set();
    const candles = [];
    const lines = [];
    const volumes = [];

    for (const s of sorted) {
      const dateStr = typeof s.date === 'string' ? s.date.slice(0, 10) : s.date;
      if (seenDates.has(dateStr)) continue;
      seenDates.add(dateStr);

      const rawClose = Number(s.close ?? s.ltp);
      const rawOpen = Number(s.open ?? rawClose);
      const rawHigh = Number(s.high ?? Math.max(rawOpen, rawClose));
      const rawLow = Number(s.low ?? Math.min(rawOpen, rawClose));

      const high = Math.max(rawHigh, rawOpen, rawClose);
      const low = Math.min(rawLow, rawOpen, rawClose);
      const open = rawOpen;
      const close = rawClose;
      const vol = Number(s.volume ?? 0);

      const isUp = close >= open;

      candles.push({
        time: dateStr,
        open,
        high,
        low,
        close,
      });

      lines.push({
        time: dateStr,
        value: close,
      });

      volumes.push({
        time: dateStr,
        value: vol,
        color: isUp ? 'rgba(16, 185, 129, 0.45)' : 'rgba(239, 68, 68, 0.45)',
      });
    }

    const latest = candles.length > 0 ? candles[candles.length - 1] : null;
    return { candleData: candles, lineData: lines, volumeData: volumes, latestBar: latest };
  }, [snapshots]);

  // Active hover HUD state (defaults to latest bar)
  const [hudData, setHudData] = useState(null);

  useEffect(() => {
    if (latestBar) {
      const volItem = volumeData.find((v) => v.time === latestBar.time);
      const diff = latestBar.close - latestBar.open;
      const pct = latestBar.open > 0 ? (diff / latestBar.open) * 100 : 0;
      setHudData({
        time: latestBar.time,
        open: latestBar.open,
        high: latestBar.high,
        low: latestBar.low,
        close: latestBar.close,
        volume: volItem ? volItem.value : 0,
        change: diff,
        changePct: pct,
        isLatest: true,
      });
    }
  }, [latestBar, volumeData]);

  // Initialize and mount chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Clean up any existing instances in container
    chartContainerRef.current.innerHTML = '';

    // Create Chart instance
    const chart = createChart(chartContainerRef.current, {
      autoSize: true,
      layout: {
        background: { type: 'solid', color: '#111827' },
        textColor: '#9ca3af',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        fontSize: 12,
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
      },
      crosshair: {
        mode: 1, // Magnet mode
        vertLine: {
          color: '#6366f1',
          width: 1,
          style: 3,
          labelBackgroundColor: '#4f46e5',
        },
        horzLine: {
          color: '#6366f1',
          width: 1,
          style: 3,
          labelBackgroundColor: '#4f46e5',
        },
      },
      rightPriceScale: {
        borderColor: '#2a324b',
        scaleMargins: {
          top: 0.1,
          bottom: 0.25,
        },
      },
      timeScale: {
        borderColor: '#2a324b',
        timeVisible: false,
        secondsVisible: false,
      },
      localization: {
        priceFormatter: (price) =>
          '₹' + Number(price).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }),
      },
    });

    chartRef.current = chart;

    // Watermark
    if (symbol) {
      try {
        createTextWatermark(chart.panes()[0], {
          horzAlign: 'center',
          vertAlign: 'center',
          lines: [
            {
              text: symbol.toUpperCase(),
              color: 'rgba(255, 255, 255, 0.05)',
              fontSize: 56,
            },
          ],
        });
      } catch (err) {
        console.debug('Watermark init skipped:', err);
      }
    }

    // Add main price series (Candlestick or Line)
    let mainSeries;
    if (chartType === 'line') {
      mainSeries = chart.addSeries(LineSeries, {
        color: '#6366f1',
        lineWidth: 2,
      }, 0);
      if (lineData.length > 0) mainSeries.setData(lineData);
    } else {
      mainSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: true,
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      }, 0);
      if (candleData.length > 0) mainSeries.setData(candleData);
    }
    mainSeriesRef.current = mainSeries;

    // Volume Series (Pane 1)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    }, 1);
    volumeSeriesRef.current = volumeSeries;

    const panes = chart.panes();
    if (panes.length > 1) {
      panes[1].setHeight(84);
    }

    if (volumeData.length > 0) {
      volumeSeries.setData(volumeData);
    }

    if (candleData.length > 0) {
      chart.timeScale().fitContent();
    }

    // Crosshair move HUD updater
    chart.subscribeCrosshairMove((param) => {
      if (!param.point || !param.time) {
        if (latestBar) {
          const volItem = volumeData.find((v) => v.time === latestBar.time);
          const diff = latestBar.close - latestBar.open;
          const pct = latestBar.open > 0 ? (diff / latestBar.open) * 100 : 0;
          setHudData({
            time: latestBar.time,
            open: latestBar.open,
            high: latestBar.high,
            low: latestBar.low,
            close: latestBar.close,
            volume: volItem ? volItem.value : 0,
            change: diff,
            changePct: pct,
            isLatest: true,
          });
        }
        return;
      }

      const bar = param.seriesData.get(mainSeries);
      if (bar) {
        const volBar = param.seriesData.get(volumeSeries);
        const open = bar.open ?? bar.value;
        const close = bar.close ?? bar.value;
        const high = bar.high ?? bar.value;
        const low = bar.low ?? bar.value;
        const diff = close - open;
        const pct = open > 0 ? (diff / open) * 100 : 0;

        setHudData({
          time: param.time,
          open,
          high,
          low,
          close,
          volume: volBar ? volBar.value : 0,
          change: diff,
          changePct: pct,
          isLatest: false,
        });
      }
    });

    return () => {
      chart.remove();
      chartRef.current = null;
      mainSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [symbol, chartType, candleData.length]);

  // Handle timeframe changes
  const handleTimeframeChange = (tf) => {
    setActiveTimeframe(tf);
    const chart = chartRef.current;
    if (!chart || candleData.length === 0) return;

    if (tf === 'ALL') {
      chart.timeScale().fitContent();
      return;
    }

    const lastDate = new Date(candleData[candleData.length - 1].time);
    const fromDate = new Date(lastDate);

    if (tf === '1M') fromDate.setMonth(fromDate.getMonth() - 1);
    else if (tf === '3M') fromDate.setMonth(fromDate.getMonth() - 3);
    else if (tf === '6M') fromDate.setMonth(fromDate.getMonth() - 6);
    else if (tf === '1Y') fromDate.setFullYear(fromDate.getFullYear() - 1);

    const fromStr = fromDate.toISOString().slice(0, 10);
    const toStr = lastDate.toISOString().slice(0, 10);

    chart.timeScale().setVisibleRange({
      from: fromStr,
      to: toStr,
    });
  };

  return (
    <div className="tv-chart-wrapper">
      {/* ── Top Control & Inspection Bar ──────────────────── */}
      <div className="tv-chart-header">
        <div className="tv-controls-left">
          {/* Chart Type Toggle */}
          <div className="tv-type-pills">
            <button
              type="button"
              className={`tv-type-btn ${chartType === 'candles' ? 'active' : ''}`}
              onClick={() => setChartType('candles')}
            >
              Candles
            </button>
            <button
              type="button"
              className={`tv-type-btn ${chartType === 'line' ? 'active' : ''}`}
              onClick={() => setChartType('line')}
            >
              Line
            </button>
          </div>

          {/* Timeframe Selector */}
          <div className="tv-timeframe-pills">
            {['1M', '3M', '6M', '1Y', 'ALL'].map((tf) => (
              <button
                key={tf}
                type="button"
                className={`tv-tf-btn ${activeTimeframe === tf ? 'active' : ''}`}
                onClick={() => handleTimeframeChange(tf)}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* OHLCV Live HUD */}
        {hudData && (
          <div className="tv-hud-stats">
            <span className="tv-hud-item tv-hud-date">
              {hudData.time}
            </span>
            <span className="tv-hud-item">
              <span className="tv-hud-label">O</span>
              <span className="tv-hud-val">{formatRupee(hudData.open)}</span>
            </span>
            <span className="tv-hud-item">
              <span className="tv-hud-label">H</span>
              <span className="tv-hud-val text-green">{formatRupee(hudData.high)}</span>
            </span>
            <span className="tv-hud-item">
              <span className="tv-hud-label">L</span>
              <span className="tv-hud-val text-red">{formatRupee(hudData.low)}</span>
            </span>
            <span className="tv-hud-item">
              <span className="tv-hud-label">C</span>
              <span className="tv-hud-val font-semibold">{formatRupee(hudData.close)}</span>
            </span>
            <span className={`tv-hud-item ${hudData.change >= 0 ? 'text-green' : 'text-red'}`}>
              <span className="tv-hud-label">CHG</span>
              <span className="tv-hud-val">
                {hudData.change > 0 ? '+' : ''}
                {hudData.changePct.toFixed(2)}%
              </span>
            </span>
            <span className="tv-hud-item tv-hud-vol">
              <span className="tv-hud-label">VOL</span>
              <span className="tv-hud-val">{formatVolume(hudData.volume)}</span>
            </span>
          </div>
        )}
      </div>

      <div
        ref={chartContainerRef}
        className="tv-chart-canvas-container"
        style={{ width: '100%', height: typeof height === 'number' ? `${height}px` : height, minHeight: '400px' }}
      />
    </div>
  );
}
