from __future__ import annotations

import os

from sqlalchemy.orm import Session

from backend.models import Server


def _default_phone() -> str:
    return os.getenv("ALERT_RECEIVER_PHONE_NUMBER", "").strip() or "+10000000000"


def seed_servers_if_empty(db: Session) -> None:
    if db.query(Server).first():
        return

    default_phone = _default_phone()
    seeds = [
        ("CNC_01", "CNC Line 01", os.getenv("NEUROGUARD_PHONE_CNC_01", default_phone)),
        ("CNC_02", "CNC Line 02", os.getenv("NEUROGUARD_PHONE_CNC_02", default_phone)),
        ("PUMP_03", "Pump 03", os.getenv("NEUROGUARD_PHONE_PUMP_03", default_phone)),
        ("CONVEYOR_04", "Conveyor 04", os.getenv("NEUROGUARD_PHONE_CONVEYOR_04", default_phone)),
    ]

    for slug, name, phone in seeds:
        db.add(
            Server(
                server_name=name,
                server_slug=slug,
                assigned_phone_number=phone.strip(),
                last_status=None,
                sms_enabled=True,
            )
        )
    db.commit()



