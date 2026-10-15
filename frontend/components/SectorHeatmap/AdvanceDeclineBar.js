'use client';

/**
 * AdvanceDeclineBar component.
 * Renders a visual dual-color horizontal bar (Red = Declining, Green = Advancing)
 * and display counters for both counts underneath.
 */
export default function AdvanceDeclineBar({
  advancing = 0,
  declining = 0,
  unchanged = 0,
  total = 0,
}) {
  const adv = Number(advancing) || 0;
  const dec = Number(declining) || 0;
  const unc = Number(unchanged) || 0;
  const sum = adv + dec + unc;
  const displayTotal = total || sum;

  let decWidth = 0;
  let uncWidth = 0;
  let advWidth = 0;

  if (sum > 0) {
    decWidth = (dec / sum) * 100;
    uncWidth = (unc / sum) * 100;
    advWidth = (adv / sum) * 100;
  }

  return (
    <div
      className="ad-container"
      title={`Market Breadth: ${adv} Advancing / ${unc} Unchanged / ${dec} Declining (Total: ${displayTotal})`}
    >
      <div className="ad-bar-track">
        {decWidth > 0 && (
          <div
            className="ad-bar-dec"
            style={{ width: `${decWidth}%` }}
            title={`${dec} Declining`}
          />
        )}
        {uncWidth > 0 && (
          <div
            className="ad-bar-unc"
            style={{ width: `${uncWidth}%` }}
            title={`${unc} Unchanged`}
          />
        )}
        {advWidth > 0 && (
          <div
            className="ad-bar-adv"
            style={{ width: `${advWidth}%` }}
            title={`${adv} Advancing`}
          />
        )}
        {sum === 0 && <div className="ad-bar-empty" />}
      </div>
      <div className="ad-counts-row">
        <span className="ad-count-dec" title={`${dec} Declining`}>{dec}</span>
        <span className="ad-count-unc" title={`${unc} Unchanged`}>{unc}</span>
        <span className="ad-count-adv" title={`${adv} Advancing`}>{adv}</span>
      </div>
    </div>
  );
}
