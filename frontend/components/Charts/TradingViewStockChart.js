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
 * Normalizes Lightweight Charts Time objects or strings to 'YYYY-MM-DD'.
 */
function normalizeTime(time) {
  if (!time) return '';
  if (typeof time === 'string') return time.slice(0, 10);
  if (typeof time === 'object' && time.year) {
    const y = time.year;
    const m = String(time.month).padStart(2, '0');
    const d = String(time.day).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  return String(time);
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
  const candleSeriesRef = useRef(null);
  const lineSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);

  const [activeTimeframe, setActiveTimeframe] = useState('ALL');
  const [chartType, setChartType] = useState('candles'); // 'candles' | 'line'
  const [hudData, setHudData] = useState(null);

  // Process snapshots into strictly ascending, deduplicated OHLCV points
  const { candleData, lineData, volumeData, dataMap, latestBar } = useMemo(() => {
    if (!Array.isArray(snapshots) || snapshots.length === 0) {
      return { candleData: [], lineData: [], volumeData: [], dataMap: new Map(), latestBar: null };
    }

    // Sort chronologically ascending
    const sorted = [...snapshots]
      .filter((s) => s.date)
      .sort((a, b) => (a.date > b.date ? 1 : a.date < b.date ? -1 : 0));

    const seenDates = new Set();
    const candles = [];
    const lines = [];
    const volumes = [];
    const map = new Map();

    let prevClose = null;

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

      // Calculate daily change percentage accurately
      const refBase = prevClose ?? open;
      const change = close - refBase;
      const changePct = refBase > 0 ? (change / refBase) * 100 : 0;
      prevClose = close;

      const barItem = {
        time: dateStr,
        open,
        high,
        low,
        close,
        volume: vol,
        change,
        changePct,
      };

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

      map.set(dateStr, barItem);
    }

    const latest = candles.length > 0 ? map.get(candles[candles.length - 1].time) : null;
    return {
      candleData: candles,
      lineData: lines,
      volumeData: volumes,
      dataMap: map,
      latestBar: latest,
    };
  }, [snapshots]);

  // Keep live references for crosshair handlers so no stale closures exist
  const dataMapRef = useRef(dataMap);
  dataMapRef.current = dataMap;

  const latestBarRef = useRef(latestBar);
  latestBarRef.current = latestBar;

  // Set initial HUD state to latest bar
  useEffect(() => {
    if (latestBar) {
      setHudData({
        ...latestBar,
        isLatest: true,
      });
    }
  }, [latestBar]);

  // Initialize and mount chart (Runs only when container mounts or symbol changes)
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Clean up any existing instances in container
    chartContainerRef.current.innerHTML = '';

    // Create Chart instance with professional financial scale styling
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
        mode: 0, // Normal mode: smooth, non-snapping 60fps tracking
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
          top: 0.08,
          bottom: 0.08, // Balanced margins: full canvas utilization with zero dead gap
        },
      },
      timeScale: {
        borderColor: '#2a324b',
        timeVisible: false,
        secondsVisible: false,
        rightOffset: 5,
        barSpacing: 6,
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

    // Watermark in Pane 0 background
    if (symbol) {
      try {
        createTextWatermark(chart.panes()[0], {
          horzAlign: 'center',
          vertAlign: 'center',
          lines: [
            {
              text: symbol.toUpperCase(),
              color: 'rgba(255, 255, 255, 0.04)',
              fontSize: 56,
            },
          ],
        });
      } catch (err) {
        console.debug('Watermark init skipped:', err);
      }
    }

    // ── Pane 0: Candlestick Series ────────────────────────────
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: true,
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
      visible: chartType === 'candles',
    }, 0);
    if (candleData.length > 0) candleSeries.setData(candleData);
    candleSeriesRef.current = candleSeries;

    // ── Pane 0: Line Series (co-exists for instant, zero-flicker toggling) ─
    const lineSeries = chart.addSeries(LineSeries, {
      color: '#6366f1',
      lineWidth: 2,
      priceLineVisible: true,
      visible: chartType === 'line',
    }, 0);
    if (lineData.length > 0) lineSeries.setData(lineData);
    lineSeriesRef.current = lineSeries;

    // ── Pane 1: Volume Histogram Series ───────────────────────
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'right', // Visible scale so volume numbers appear on the right
    }, 1);
    if (volumeData.length > 0) volumeSeries.setData(volumeData);
    volumeSeriesRef.current = volumeSeries;

    // Configure Volume Pane scale margins so spikes don't clip the ceiling
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.2, // 20% breathing room above highest volume bar
        bottom: 0,
      },
    });

    // Set dedicated height for Volume Pane
    const panes = chart.panes();
    if (panes.length > 1) {
      panes[1].setHeight(84);
    }

    if (candleData.length > 0) {
      chart.timeScale().fitContent();
    }

    // ── Crosshair Hover HUD Updater ───────────────────────────
    chart.subscribeCrosshairMove((param) => {
      if (!param.point || !param.time) {
        const latest = latestBarRef.current;
        if (latest) {
          setHudData({
            ...latest,
            isLatest: true,
          });
        }
        return;
      }

      const timeKey = normalizeTime(param.time);
      const bar = dataMapRef.current.get(timeKey);

      if (bar) {
        setHudData({
          time: bar.time,
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
          volume: bar.volume,
          change: bar.change,
          changePct: bar.changePct,
          isLatest: false,
        });
      }
    });

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      lineSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [symbol]);

  // Update series data dynamically if snapshots change without tearing down the chart
  useEffect(() => {
    if (candleSeriesRef.current && lineSeriesRef.current && volumeSeriesRef.current) {
      candleSeriesRef.current.setData(candleData);
      lineSeriesRef.current.setData(lineData);
      volumeSeriesRef.current.setData(volumeData);
    }
  }, [candleData, lineData, volumeData]);

  // Handle Chart Type Toggle (Candles vs Line) instantly with zero canvas flicker
  useEffect(() => {
    if (candleSeriesRef.current && lineSeriesRef.current) {
      candleSeriesRef.current.applyOptions({ visible: chartType === 'candles' });
      lineSeriesRef.current.applyOptions({ visible: chartType === 'line' });
    }
  }, [chartType]);

  // Handle timeframe changes using exact trading sessions (Logical Range)
  const handleTimeframeChange = (tf) => {
    setActiveTimeframe(tf);
    const chart = chartRef.current;
    if (!chart || candleData.length === 0) return;

    if (tf === 'ALL') {
      chart.timeScale().fitContent();
      return;
    }

    // Trading-day session counts: avoids weekend gaps & invalid date jumps
    const tradingDayCounts = {
      '1M': 21,
      '3M': 63,
      '6M': 126,
      '1Y': 252,
    };

    const count = tradingDayCounts[tf] || candleData.length;
    const to = candleData.length - 1;
    const from = Math.max(0, to - count + 1);

    chart.timeScale().setVisibleLogicalRange({ from, to });
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
