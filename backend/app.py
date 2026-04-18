from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.alert_scheduler import start_alert_scheduler
from backend.alerts_api import router as alerts_router
from backend.database import Base, SessionLocal, engine
from backend.seed import seed_servers_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neuroguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_servers_if_empty(db)
    finally:
        db.close()

    sched = start_alert_scheduler(interval_seconds=30)
    logger.info("NeuroGuard API started")
    yield
    sched.shutdown(wait=False)


app = FastAPI(title="NeuroGuard Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts_router)


@app.get("/health")
def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="d:/NG", html=True), name="static")
