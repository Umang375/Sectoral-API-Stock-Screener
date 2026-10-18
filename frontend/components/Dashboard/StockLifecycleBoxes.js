import Link from 'next/link';

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const parts = String(dateStr).split('T')[0].split('-');
  if (parts.length === 3) {
    const [year, month, day] = parts;
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthIdx = parseInt(month, 10) - 1;
    if (monthIdx >= 0 && monthIdx < 12) {
      return `${parseInt(day, 10)} ${months[monthIdx]} ${year}`;
    }
  }
  return dateStr;
}

export default function StockLifecycleBoxes({ dumpedStocks = [], addedStocks = [] }) {
  return (
    <div className="lifecycle-grid">
      {/* ── Box 1: Dumped / Inactive Stocks ─────────────────────────── */}
      <div className="card lifecycle-card">
        <div className="card-header lifecycle-header">
          <div>
            <div className="lifecycle-title-wrap">
              <span className="card-title">🗑️ Dumped Stocks</span>
              <span className="badge badge-dumped-count">
                {dumpedStocks.length} Inactive
              </span>
            </div>
            <p className="card-subtitle">
              Dormant for 3+ weeks; preserved historically but excluded from active screeners
            </p>
          </div>
        </div>

        <div className="lifecycle-list">
          {dumpedStocks.length === 0 ? (
            <div className="empty-state-mini">
              <span>✨</span>
              <p>No stocks currently marked inactive</p>
            </div>
          ) : (
            dumpedStocks.map((stock) => (
              <div key={stock.symbol} className="lifecycle-item">
                <div className="lifecycle-item-left">
                  <div className="lifecycle-item-title-row">
                    <Link
                      href={`/stocks/${encodeURIComponent(stock.symbol)}`}
                      className="lifecycle-symbol"
                    >
                      {stock.symbol}
                    </Link>
                    <span className="lifecycle-company-name" title={stock.name}>
                      {stock.name}
                    </span>
                  </div>
                  <div className="lifecycle-meta-row">
                    {stock.sector && (
                      <span className="lifecycle-sector-tag">{stock.sector}</span>
                    )}
                    <span className="lifecycle-date-text">
                      Dormant since: {formatDate(stock.date)}
                    </span>
                  </div>
                </div>

                <div className="lifecycle-item-right">
                  {stock.days_inactive != null && (
                    <span className="badge badge-dormant">
                      {stock.days_inactive}d dormant
                    </span>
                  )}
                  {stock.ltp != null && (
                    <span className="lifecycle-price">₹{stock.ltp.toFixed(2)}</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Box 2: Recently Added & Reactivated Stocks ──────────────── */}
      <div className="card lifecycle-card">
        <div className="card-header lifecycle-header">
          <div>
            <div className="lifecycle-title-wrap">
              <span className="card-title">✨ Added & Reactivated</span>
              <span className="badge badge-added-count">
                {addedStocks.length} Recent
              </span>
            </div>
            <p className="card-subtitle">
              Brand-new equities or stocks resurrected from dormancy in the last 14 days
            </p>
          </div>
        </div>

        <div className="lifecycle-list">
          {addedStocks.length === 0 ? (
            <div className="empty-state-mini">
              <span>📈</span>
              <p>No new or reactivated stocks in the last 14 days</p>
            </div>
          ) : (
            addedStocks.map((stock) => (
              <div key={stock.symbol} className="lifecycle-item">
                <div className="lifecycle-item-left">
                  <div className="lifecycle-item-title-row">
                    <Link
                      href={`/stocks/${encodeURIComponent(stock.symbol)}`}
                      className="lifecycle-symbol"
                    >
                      {stock.symbol}
                    </Link>
                    <span className="lifecycle-company-name" title={stock.name}>
                      {stock.name}
                    </span>
                  </div>
                  <div className="lifecycle-meta-row">
                    {stock.sector && (
                      <span className="lifecycle-sector-tag">{stock.sector}</span>
                    )}
                    <span className="lifecycle-date-text">
                      {stock.status === 'reactivated' ? 'Reactivated on: ' : 'New added on: '}
                      {formatDate(stock.date)}
                    </span>
                  </div>
                </div>

                <div className="lifecycle-item-right">
                  {stock.status === 'reactivated' ? (
                    <span className="badge badge-reactivated">🔄 Reactivated</span>
                  ) : (
                    <span className="badge badge-new">✨ New</span>
                  )}
                  {stock.ltp != null && (
                    <span className="lifecycle-price">₹{stock.ltp.toFixed(2)}</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
