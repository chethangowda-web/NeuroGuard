from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("neuroguard.scheduler")

_scheduler: Optional[BackgroundScheduler] = None


def run_prediction() -> None:
    from backend.database import SessionLocal
    from backend.services.monitor_service import reconcile_all_servers

    db = SessionLocal()
    try:
        reconcile_all_servers(db)
    except Exception as exc:
        logger.exception("Scheduled prediction/reconcile failed: %s", exc)
    finally:
        db.close()


def start_alert_scheduler(interval_seconds: int = 30) -> BackgroundScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    sched = BackgroundScheduler()
    sched.add_job(run_prediction, "cron", minute="*/30", id="neuroguard_prediction", replace_existing=True)
    sched.start()
    logger.info("Prediction scheduler started (cron */30m)")
    _scheduler = sched
    return sched


def shutdown_alert_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
