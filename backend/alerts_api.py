from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AlertLog, Server
from backend.services.monitor_service import process_metrics_for_slug
from backend.services.sms_service import send_sms_alert

router = APIRouter(prefix="/api/v1", tags=["alerts"])


class MetricsIngest(BaseModel):
    server_slug: str = Field(..., min_length=1, max_length=128)
    server_name: Optional[str] = Field(None, max_length=255)
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    failure_probability_percent: float = Field(ge=0, le=100)


class ServerDashboardRow(BaseModel):
    server_id: int
    server_name: str
    server_slug: str
    current_status: Optional[str]
    assigned_phone_number: str
    sms_enabled: bool
    last_sms_sent_at: Optional[str]
    last_delivery_status: Optional[str]
    last_metrics_at: Optional[str]


class AlertLogOut(BaseModel):
    id: int
    server_slug: str
    from_status: Optional[str]
    to_status: str
    message: str
    success: bool
    twilio_sid: Optional[str]
    error_detail: Optional[str]
    created_at: str


@router.post("/metrics/ingest")
def ingest_metrics(payload: MetricsIngest, db: Session = Depends(get_db)):
    try:
        server, sms_evaluated = process_metrics_for_slug(
            db,
            payload.server_slug.strip(),
            payload.server_name,
            payload.cpu_percent,
            payload.memory_percent,
            payload.disk_percent,
            payload.failure_probability_percent,
        )
        if not server:
            raise HTTPException(status_code=404, detail=f"Unknown server_slug: {payload.server_slug}")

        return {
            "ok": True,
            "server_slug": server.server_slug,
            "last_status": server.last_status,
            "last_delivery_status": server.last_delivery_status,
            "last_sms_sent_at": server.last_sms_sent_at.isoformat() if server.last_sms_sent_at else None,
            "sms_evaluated": sms_evaluated,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest error: {str(e)}")


@router.get("/servers/alert-dashboard", response_model=List[ServerDashboardRow])
def alert_dashboard(db: Session = Depends(get_db)):
    try:
        rows: List[ServerDashboardRow] = []
        for s in db.query(Server).order_by(Server.server_slug).limit(20).all():
            rows.append(
                ServerDashboardRow(
                    server_id=s.server_id,
                    server_name=s.server_name,
                    server_slug=s.server_slug,
                    current_status=s.last_status,
                    assigned_phone_number=s.assigned_phone_number,
                    sms_enabled=s.sms_enabled,
                    last_sms_sent_at=s.last_sms_sent_at.isoformat() if s.last_sms_sent_at else None,
                    last_delivery_status=s.last_delivery_status,
                    last_metrics_at=s.last_metrics_at.isoformat() if s.last_metrics_at else None,
                )
            )
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@router.get("/alert-logs", response_model=List[AlertLogOut])
def alert_logs(limit: int = 30, db: Session = Depends(get_db)):
    try:
        limit = max(1, min(limit, 30))
        q = (
            db.query(AlertLog, Server.server_slug)
            .join(Server, AlertLog.server_id == Server.server_id)
            .order_by(AlertLog.created_at.desc())
            .limit(limit)
        )
        out: List[AlertLogOut] = []
        for log, slug in q.all():
            out.append(
                AlertLogOut(
                    id=log.id,
                    server_slug=slug,
                    from_status=log.from_status,
                    to_status=log.to_status,
                    message=log.message,
                    success=log.success,
                    twilio_sid=log.twilio_sid,
                    error_detail=log.error_detail,
                    created_at=log.created_at.isoformat(),
                )
            )
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logs error: {str(e)}")


@router.get("/test-sms")
def test_sms():
    """Send a one-off test SMS to ALERT_RECEIVER_PHONE_NUMBER (Twilio env)."""
    message = "NeuroGuard Test SMS Alert: Twilio working successfully!"
    ok = send_sms_alert(message)
    if not ok:
        raise HTTPException(status_code=500, detail="SMS send failed — check logs and Twilio credentials")
    return {"success": True, "message": message}
