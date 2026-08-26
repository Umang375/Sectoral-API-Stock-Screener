'use client';

/**
 * AdvanceDeclineBar component.
 * Renders a visual dual-color horizontal bar (Red = Declining, Green = Advancing)
 * and display counters for both counts underneath.
 */
export default function AdvanceDeclineBar({ advancing = 0, declining = 0, total = 0 }) {
  const adv = Number(advancing) || 0;
  const dec = Number(declining) || 0;
  const sum = adv + dec;

  let decWidth = 0;
  let advWidth = 0;

  if (sum > 0) {
    decWidth = (dec / sum) * 100;
    advWidth = (adv / sum) * 100;
  }

  return (
    <div className="ad-container" title={`Market Breadth: ${adv} Advancing / ${dec} Declining (Total: ${total || sum})`}>
      <div className="ad-bar-track">
        {decWidth > 0 && (
          <div
            className="ad-bar-dec"
            style={{ width: `${decWidth}%` }}
          />
        )}
        {advWidth > 0 && (
          <div
            className="ad-bar-adv"
            style={{ width: `${advWidth}%` }}
          />
        )}
        {sum === 0 && <div className="ad-bar-empty" />}
      </div>
      <div className="ad-counts-row">
        <span className="ad-count-dec">{dec}</span>
        <span className="ad-count-adv">{adv}</span>
      </div>
    </div>
  );
}
