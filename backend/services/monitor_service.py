from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from backend.models import AlertLog, Server
from backend.services.sms_service import send_sms

logger = logging.getLogger("neuroguard.monitor")

STATUS_NORMAL = "NORMAL"
STATUS_AT_RISK = "AT_RISK"
STATUS_CRITICAL = "CRITICAL"


def derive_operational_status(
    failure_probability_percent: float,
    cpu_percent: float,
    memory_percent: float,
    disk_percent: float,
) -> str:
    """Map live metrics to a coarse health state (UI / alerting)."""
    fp = float(failure_probability_percent)
    if fp >= 70 or cpu_percent > 90 or memory_percent > 92 or disk_percent > 95:
        return STATUS_CRITICAL
    if fp >= 30 or cpu_percent > 80 or memory_percent > 85 or disk_percent > 90:
        return STATUS_AT_RISK
    return STATUS_NORMAL


def _build_sms_message(server_name: str, previous: Optional[str], new_status: str) -> str:
    name = server_name or "Server"
    if new_status == STATUS_NORMAL:
        if previous in (STATUS_AT_RISK, STATUS_CRITICAL):
            return f"Update: {name} has recovered and is back to normal."
        return f"Update: {name} is operating normally."
    if new_status == STATUS_AT_RISK:
        return f"Warning: {name} is at risk. Maintenance may be required soon."
    if new_status == STATUS_CRITICAL:
        return f"Critical Alert: {name} may fail soon. Immediate action required."
    return f"Update: {name} status is now {new_status}."


def process_metrics_for_slug(
    db: Session,
    server_slug: str,
    server_display_name: Optional[str],
    cpu_percent: float,
    memory_percent: float,
    disk_percent: float,
    failure_probability_percent: float,
) -> Tuple[Optional[Server], bool]:
    """
    Persist metrics, detect status change, send SMS to server's assigned number if needed.
    Returns (server, sms_attempted).
    """
    server = db.query(Server).filter(Server.server_slug == server_slug).first()
    if not server:
        logger.warning("Unknown server_slug=%s — register in DB first", server_slug)
        return None, False

    new_status = derive_operational_status(
        failure_probability_percent, cpu_percent, memory_percent, disk_percent
    )
    previous = server.last_status

    server.last_cpu = cpu_percent
    server.last_memory = memory_percent
    server.last_disk = disk_percent
    server.last_failure_probability = failure_probability_percent
    server.last_metrics_at = datetime.utcnow()
    if server_display_name:
        server.server_name = server_display_name

    if previous == new_status:
        db.commit()
        db.refresh(server)
        logger.debug("No status change for %s (%s)", server_slug, new_status)
        return server, False

    # Bootstrap: first observation while healthy — persist state, no SMS noise.
    if previous is None and new_status == STATUS_NORMAL:
        server.last_status = new_status
        db.commit()
        db.refresh(server)
        return server, False

    message = _build_sms_message(server.server_name, previous, new_status)
    sms_attempted = False
    twilio_sid = None
    success = False
    error_detail = None

    if server.sms_enabled:
        sms_attempted = True
        result = send_sms(server.assigned_phone_number, message)
        success = bool(result.get("success"))
        twilio_sid = result.get("sid")
        error_detail = result.get("error")
        server.last_sms_sent_at = datetime.utcnow() if success else server.last_sms_sent_at
        _mock = bool(result.get("mock"))
        server.last_delivery_status = (
            ("delivered (mock)" if _mock else "delivered")
            if success
            else f"failed: {error_detail or 'unknown'}"
        )
    else:
        server.last_delivery_status = "skipped_sms_disabled"
        success = True
        error_detail = None

    server.last_status = new_status

    log = AlertLog(
        server_id=server.server_id,
        from_status=previous,
        to_status=new_status,
        message=message,
        twilio_sid=twilio_sid,
        success=success,
        error_detail=error_detail,
    )
    db.add(log)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("DB commit failed after alert for %s: %s", server_slug, exc)
        raise

    db.refresh(server)
    logger.info(
        "Status change %s -> %s for %s (sms=%s)",
        previous,
        new_status,
        server_slug,
        sms_attempted,
    )
    return server, sms_attempted


def reconcile_all_servers(db: Session) -> None:
    """Re-evaluate last known metrics (scheduler safety net)."""
    for server in db.query(Server).all():
        if (
            server.last_cpu is None
            or server.last_memory is None
            or server.last_disk is None
            or server.last_failure_probability is None
        ):
            continue
        new_status = derive_operational_status(
            server.last_failure_probability,
            server.last_cpu,
            server.last_memory,
            server.last_disk,
        )
        if server.last_status != new_status:
            process_metrics_for_slug(
                db,
                server.server_slug,
                None,
                server.last_cpu,
                server.last_memory,
                server.last_disk,
                server.last_failure_probability,
            )
