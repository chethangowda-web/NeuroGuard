from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

load_dotenv()

logger = logging.getLogger("neuroguard.sms")

_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 1.5


def _mock_sms_enabled() -> bool:
    v = os.getenv("NEUROGUARD_MOCK_SMS", "").strip().lower()
    return v in ("1", "true", "yes")


def _mock_result(to: str, message: str, reason: str) -> Dict[str, Any]:
    sid = f"MOCK-{int(time.time() * 1000)}"
    logger.warning("MOCK SMS (%s) to=%s … %s", reason, to, (message or "")[:120])
    print(f"MOCK SMS ({reason}) SID: {sid} to={to}")
    return {"success": True, "sid": sid, "error": None, "mock": True}


def _is_valid_e164(phone_number: Optional[str]) -> bool:
    if not isinstance(phone_number, str) or len(phone_number) < 8:
        return False
    return phone_number.startswith("+")


def send_sms_alert(message: str) -> bool:
    """Backward-compatible single-receiver helper using ALERT_RECEIVER_PHONE_NUMBER."""
    to = os.getenv("ALERT_RECEIVER_PHONE_NUMBER", "").strip()
    if not to and _mock_sms_enabled():
        to = "+15555550100"
    result = send_sms(to, message)
    return bool(result.get("success"))


def send_sms(to_number: str, message: str) -> Dict[str, Any]:
    """
    Send SMS via Twilio with retries. Does not raise; returns a result dict.
    Keys: success (bool), sid (str|None), error (str|None)
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    to = (to_number or "").strip()

    if not _is_valid_e164(to):
        err = "Invalid destination number (must be E.164, start with +)"
        logger.error(err)
        return {"success": False, "sid": None, "error": err}

    if _mock_sms_enabled() or not account_sid or not auth_token:
        reason = "NEUROGUARD_MOCK_SMS=1" if _mock_sms_enabled() else "Twilio credentials not set (using mock)"
        return _mock_result(to, message, reason)

    if not _is_valid_e164(from_number):
        err = "Invalid TWILIO_PHONE_NUMBER (must be E.164, start with +)"
        logger.error(err)
        return {"success": False, "sid": None, "error": err}

    client = Client(account_sid, auth_token)
    last_error: Optional[str] = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.messages.create(body=message, from_=from_number, to=to)
            logger.info("SMS sent successfully, SID: %s (attempt %s)", response.sid, attempt)
            print(f"SMS sent successfully, SID: {response.sid}")
            return {"success": True, "sid": response.sid, "error": None}
        except TwilioRestException as exc:
            last_error = f"Twilio error {exc.code}: {exc.msg}"
            logger.warning("SMS attempt %s failed: %s", attempt, last_error)
        except Exception as exc:
            last_error = str(exc)
            logger.warning("SMS attempt %s failed: %s", attempt, last_error)

        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY_SEC * attempt)

    print(f"SMS failed: {last_error}")
    logger.error("SMS failed after %s attempts: %s", _MAX_RETRIES, last_error)
    return {"success": False, "sid": None, "error": last_error or "Unknown error"}
