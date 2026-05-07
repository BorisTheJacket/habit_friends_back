import os
import logging
from typing import Iterable, Optional

import httpx

logger = logging.getLogger(__name__)

ONESIGNAL_API_URL = "https://api.onesignal.com/notifications"
ONESIGNAL_APP_ID = os.environ.get("ONESIGNAL_APP_ID", "")
ONESIGNAL_REST_API_KEY = os.environ.get("ONESIGNAL_REST_API_KEY", "")


async def send_invite_notification(
    external_ids: Iterable[str],
    type_: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> None:
    """Fire a OneSignal push to one or more recipients addressed by their
    Firebase UID (registered as `external_id` from the iOS client).

    Failures are swallowed and logged — invite rows are already persisted in
    the DB so the recipient still sees them on next manual open.
    """
    ids = [uid for uid in external_ids if uid]
    if not ids:
        return
    if not ONESIGNAL_APP_ID or not ONESIGNAL_REST_API_KEY:
        logger.warning("OneSignal env not configured; skipping push for type=%s", type_)
        return

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "include_aliases": {"external_id": list(ids)},
        "target_channel": "push",
        "headings": {"en": title},
        "contents": {"en": body},
        "data": {"type": type_, **(data or {})},
    }
    headers = {
        "Authorization": f"Key {ONESIGNAL_REST_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(ONESIGNAL_API_URL, json=payload, headers=headers)
        if resp.status_code >= 300:
            logger.warning(
                "OneSignal returned %s for type=%s body=%s",
                resp.status_code,
                type_,
                resp.text,
            )
    except Exception as exc:
        logger.warning("OneSignal push failed type=%s err=%s", type_, exc)