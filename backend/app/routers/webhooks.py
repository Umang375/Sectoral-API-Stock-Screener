"""Webhook receiver — accepts intraday alert payloads from Chartlink.

WHY a separate router (not just a function in screeners.py)?
- Webhooks are a fundamentally different concern: they're INBOUND events
  from an external system, not OUTBOUND requests from our users.
- Separation makes it easy to add webhook-specific middleware later
  (authentication, request signing, replay protection).

SECURITY CONSIDERATION:
- In production, verify webhook authenticity via a shared secret or
  HMAC signature in the request headers.
- For MVP, we accept all POSTs (Chartlink doesn't sign webhooks).
"""

from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.services.webhook_handler import WebhookHandler

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/chartlink")
async def receive_chartlink_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Receive and process an intraday alert from Chartlink.

    Accepts raw JSON, parses it through the WebhookHandler service,
    and returns a summary of tracked vs ignored stocks.
    """
    payload = await request.json()

    handler = WebhookHandler()
    result = await handler.process_alert(payload=payload, session=session)

    return {
        "status": "ok",
        "tracked": result["tracked"],
        "ignored": result["ignored"],
        "alerts_saved": result["alerts_saved"],
    }
