import logging
import os

import httpx
from fastapi import APIRouter

from schemas import PasswordResetRequest, PasswordResetResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Web (browser) API key for the Firebase project. This is a public client key
# (it already ships inside the iOS app's GoogleService-Info.plist), so a fallback
# is provided to keep the endpoint working if the env var is not set. Prefer
# configuring FIREBASE_WEB_API_KEY in the environment.
FIREBASE_WEB_API_KEY = os.getenv(
    "FIREBASE_WEB_API_KEY",
    "AIzaSyAYafuNs5qJaAbi0JJLXMA6wDyKJyCF2Fo",
)

IDENTITY_TOOLKIT_OOB_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"
)


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(payload: PasswordResetRequest) -> PasswordResetResponse:
    """Trigger a Firebase password reset email for the given address.

    Uses the Identity Toolkit `sendOobCode` REST endpoint so the email is sent by
    Firebase itself (no SMTP server required). The response is intentionally
    generic regardless of whether the account exists, to prevent account
    enumeration.
    """
    email = (payload.email or "").strip()
    if not email:
        return PasswordResetResponse()

    body = {"requestType": "PASSWORD_RESET", "email": email}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                IDENTITY_TOOLKIT_OOB_URL,
                params={"key": FIREBASE_WEB_API_KEY},
                json=body,
            )
        if resp.status_code != 200:
            # EMAIL_NOT_FOUND / INVALID_EMAIL etc. are expected and must not be
            # surfaced to the caller. Log for diagnostics only.
            detail = resp.json().get("error", {}).get("message", resp.text)
            logger.info("Password reset not sent for %s: %s", email, detail)
    except Exception as exc:  # network/transport errors
        logger.warning("Password reset request failed for %s: %s", email, exc)

    return PasswordResetResponse()
