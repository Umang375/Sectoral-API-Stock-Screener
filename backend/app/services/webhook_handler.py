"""Webhook handler for intraday Chartlink alerts.

PATTERN: Event Handler
──────────────────────
Receives raw webhook payloads from Chartlink, filters for tracked stocks,
and persists alert events.

WHY filter for tracked stocks?
- Chartlink sends alerts for ALL stocks matching the scan — which may
  include stocks we don't track.  We only save alerts for stocks already
  in our `stocks` table.
- This keeps the webhook_alerts table focused and queryable.

WHY store the full payload as JSONB?
- Chartlink may add/change fields without notice.
- Storing the raw payload means we never lose data, even if our parser
  doesn't extract a new field yet.
"""

import logging
from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stock import Stock
from app.models.webhook import WebhookAlert

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Processes intraday alert payloads from Chartlink webhooks.

    Usage:
        handler = WebhookHandler()
        result = await handler.process_alert(payload, session)
        # result = {"tracked": 3, "ignored": 7, "alerts_saved": 3}
    """

    async def process_alert(
        self,
        payload: dict,
        session: AsyncSession,
    ) -> dict[str, int]:
        """Process a Chartlink webhook alert payload.

        Expected payload shape (from Chartlink):
        {
            "scan_name": "200 DMA Crossover",
            "alert_name": "My Alert",
            "triggered_at": "2026-07-04 10:15:00",
            "stocks": [
                {"nsecode": "RELIANCE", "close": "2850.50", "per_chg": "1.25", ...}
            ]
        }
        """
        scan_name = payload.get("scan_name", "unknown_scan")
        triggered_at_str = payload.get("triggered_at", "")
        stock_rows = payload.get("stocks", [])

        # Parse trigger time.
        try:
            triggered_at = datetime.fromisoformat(triggered_at_str)
        except (ValueError, TypeError):
            triggered_at = datetime.utcnow()

        # Derive alert_type from scan name.
        alert_type = self._derive_alert_type(scan_name)

        tracked = 0
        ignored = 0

        for row in stock_rows:
            symbol = str(row.get("nsecode", row.get("symbol", ""))).upper().strip()
            if not symbol:
                ignored += 1
                continue

            # Check if this stock exists in our database.
            stmt = select(Stock).where(Stock.symbol == symbol)
            result = await session.exec(stmt)
            stock = result.first()

            if not stock:
                logger.debug("Ignoring alert for untracked stock: %s", symbol)
                ignored += 1
                continue

            # Save the alert event.
            trigger_value = None
            try:
                trigger_value = float(row.get("close", 0))
            except (ValueError, TypeError):
                pass

            alert = WebhookAlert(
                stock_id=stock.id,
                alert_type=alert_type,
                metric=scan_name,
                trigger_value=trigger_value,
                payload=row,
                triggered_at=triggered_at,
            )
            session.add(alert)
            tracked += 1
            logger.info("Alert saved: %s — %s at %s", symbol, alert_type, triggered_at)

        await session.commit()

        return {
            "tracked": tracked,
            "ignored": ignored,
            "alerts_saved": tracked,
        }

    @staticmethod
    def _derive_alert_type(scan_name: str) -> str:
        """Convert a human-readable scan name into a machine-friendly alert type.

        "200 DMA Crossover" → "200_DMA_CROSSOVER"
        "RSI > 70 Overbought" → "RSI_>_70_OVERBOUGHT"
        """
        return scan_name.upper().replace(" ", "_").replace("-", "_")
