'use client';

import Link from 'next/link';
import { formatPercent, get52WHighStyle, getReturnStyle } from '@/lib/heatmapUtils';

/**
 * ConstituentStocksTable component.
 * Displays the list of individual stocks inside an expanded sector accordion row.
 */
export default function ConstituentStocksTable({ stocks = [], sectorName = '' }) {
  if (!stocks || stocks.length === 0) {
    return (
      <div className="subtable-empty">
        <p>No constituent stock details available for {sectorName}.</p>
      </div>
    );
  }

  return (
    <div className="subtable-wrapper">
      <table className="subtable">
        <thead>
          <tr>
            <th className="subtable-th-symbol">Stock</th>
            <th className="subtable-th-ltp">LTP (₹)</th>
            <th className="subtable-th-drawdown">52W High</th>
            <th className="subtable-th-change">1D Change</th>
            <th className="subtable-th-vol">Volume</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock) => {
            const retStyle = getReturnStyle(stock.change_pct);
            const highStyle = get52WHighStyle(stock.drawdown_52w_high);

            return (
              <tr key={stock.symbol} className="subtable-row">
                <td className="subtable-td-symbol">
                  <Link
                    href={`/stocks?q=${encodeURIComponent(stock.symbol)}`}
                    className="subtable-stock-link"
                  >
                    <span className="subtable-symbol">{stock.symbol}</span>
                    {stock.name && <span className="subtable-name">{stock.name}</span>}
                  </Link>
                </td>
                <td className="subtable-td-ltp">
                  {stock.ltp != null ? `₹${Number(stock.ltp).toLocaleString('en-IN')}` : '—'}
                </td>
                <td className="subtable-td-drawdown">
                  {stock.drawdown_52w_high != null ? (
                    <span className={`subtable-badge ${highStyle.className}`}>
                      {formatPercent(stock.drawdown_52w_high, false)}
                    </span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
                <td className="subtable-td-change">
                  {stock.change_pct != null ? (
                    <span className={`subtable-badge ${retStyle.className}`}>
                      {formatPercent(stock.change_pct, true)}
                    </span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
                <td className="subtable-td-vol">
                  {stock.volume != null ? Number(stock.volume).toLocaleString('en-IN') : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
