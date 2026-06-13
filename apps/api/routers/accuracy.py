# ════════════════════════════════════════════════════════════════
# Accuracy Router (§10, §18)
# POST /api/v1/accuracy/evaluate — evaluate past simulation accuracy
# GET  /api/v1/accuracy/stats — get accuracy statistics
# ════════════════════════════════════════════════════════════════
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
import httpx
import yfinance as yf

from config import settings
from logging_config import logger

router = APIRouter(prefix="/api/v1/accuracy", tags=["accuracy"])


@router.post("/evaluate")
async def evaluate_accuracy():
    """
    Check simulations from 5+ days ago against actual price outcomes.
    Called by pg_cron daily at 4am UTC.
    """
    if not settings.supabase_url:
        return {"evaluated": 0, "note": "Supabase not configured"}

    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            # Fetch unverified simulations older than 5 days
            resp = await client.get(
                f"{settings.supabase_url}/rest/v1/simulations",
                params={
                    "select": "id,user_id,seed_text,verdict,confidence,predicted_impact,created_at",
                    "accuracy_verified": "eq.false",
                    "created_at": f"lt.{cutoff}",
                    "limit": "50",
                },
                headers=headers,
            )
            sims = resp.json()

            evaluated = 0
            for sim in sims:
                # Fetch actual price movement (simplified — checks SPY)
                actual_direction = await _get_actual_outcome(sim.get("created_at"))
                is_correct = actual_direction is not None and (
                    (sim["verdict"] == "BULLISH" and actual_direction == "bullish") or
                    (sim["verdict"] == "BEARISH" and actual_direction == "bearish")
                ) if sim.get("verdict") else None

                # Update accuracy record
                await client.post(
                    f"{settings.supabase_url}/rest/v1/simulation_accuracy",
                    json={
                        "user_id": sim["user_id"],
                        "simulation_id": sim["id"],
                        "predicted_direction": sim.get("verdict"),
                        "actual_direction": actual_direction,
                        "is_correct": is_correct,
                        "confidence_at_prediction": sim.get("confidence"),
                    },
                    headers={**headers, "Prefer": "resolution=merge-duplicates"},
                )

                # Mark simulation as verified
                await client.patch(
                    f"{settings.supabase_url}/rest/v1/simulations?id=eq.{sim['id']}",
                    json={"accuracy_verified": True, "actual_outcome": actual_direction},
                    headers=headers,
                )
                evaluated += 1

        logger.info("accuracy_evaluation_complete", evaluated=evaluated)
        return {"evaluated": evaluated}

    except Exception as e:
        logger.error("accuracy_eval_failed", error=str(e))
        return {"error": str(e), "evaluated": 0}


@router.get("/stats")
async def get_accuracy_stats(user_id: str = Query(...)):
    """Get accuracy statistics for a user."""
    from services.memory import memory_service
    stats = await memory_service.get_accuracy_stats(user_id)
    return stats


async def _get_actual_outcome(created_at: str) -> str | None:
    """Determine actual market direction since simulation date."""
    try:
        def _fetch():
            sim_date = created_at[:10]
            spy = yf.Ticker("SPY").history(start=sim_date, period="5d")
            if len(spy) < 2:
                return None
            ret = (spy["Close"].iloc[-1] / spy["Close"].iloc[0]) - 1
            return "bullish" if ret > 0.005 else "bearish" if ret < -0.005 else "neutral"

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
    except Exception as e:
        logger.debug("actual_outcome_failed", error=str(e))
        return None
