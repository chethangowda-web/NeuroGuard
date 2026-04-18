"""ORM models — classic Column style for compatibility with Python 3.14 + SQLAlchemy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Server(Base):
    __tablename__ = "servers"

    server_id = Column(Integer, primary_key=True, autoincrement=True)
    server_name = Column(String(255), nullable=False)
    server_slug = Column(String(128), unique=True, nullable=False, index=True)
    assigned_phone_number = Column(String(32), nullable=False)
    last_status = Column(String(32), nullable=True)
    sms_enabled = Column(Boolean, default=True, nullable=False)
    last_sms_sent_at = Column(DateTime, nullable=True)
    last_delivery_status = Column(String(64), nullable=True)
    last_cpu = Column(Float, nullable=True)
    last_memory = Column(Float, nullable=True)
    last_disk = Column(Float, nullable=True)
    last_failure_probability = Column(Float, nullable=True)
    last_metrics_at = Column(DateTime, nullable=True)

    alert_logs = relationship("AlertLog", back_populates="server")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.server_id"), nullable=False, index=True)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    twilio_sid = Column(String(64), nullable=True)
    success = Column(Boolean, nullable=False)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    server = relationship("Server", back_populates="alert_logs")
