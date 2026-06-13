# ════════════════════════════════════════════════════════════════
# Signals Router (§13)
# GET  /api/v1/signals/latest — latest L1-L5 signals
# POST /api/v1/signals/refresh — trigger pipeline refresh (cron)
# ════════════════════════════════════════════════════════════════
from fastapi import APIRouter

from logging_config import logger
from services.signals.pipeline import signal_pipeline

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.get("/latest")
async def get_latest_signals(limit: int = 50):
    """Return latest signals from all L1-L5 providers."""
    signals = await signal_pipeline.get_latest(limit)
    return {"signals": signals, "count": len(signals)}


@router.post("/refresh")
async def refresh_signals():
    """
    Trigger a full signal pipeline refresh.
    Called by pg_cron every 15 minutes.
    """
    result = await signal_pipeline.refresh_all()
    return result
