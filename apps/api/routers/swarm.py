# ════════════════════════════════════════════════════════════════
# Swarm Router (§10, §11)
# POST /api/v1/swarm/run — core simulation endpoint
# Called by the swarm-trigger Edge Function.
# ════════════════════════════════════════════════════════════════
import asyncio
import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Any

from config import settings
from logging_config import logger
from services.mirofish import swarm_engine, SwarmConfig
from services.langchain_brain import oracle_brain

router = APIRouter(prefix="/api/v1/swarm", tags=["swarm"])


class SwarmRunRequest(BaseModel):
    simulation_id: str
    seed_text: str = Field(..., min_length=10)
    seed_type: str = "user_thesis"
    agent_count: int = Field(500, ge=1, le=1000)
    round_count: int = Field(40, ge=1, le=40)
    agent_mix: dict = Field(default_factory=lambda: {"institutional": 35, "retail": 50, "media": 15})
    llm_model: str = "gpt-4o-mini"
    environments: list[str] = Field(default_factory=lambda: ["twitter", "reddit"])
    supabase_simulation_id: str | None = None


@router.post("/run")
async def run_swarm(req: SwarmRunRequest):
    """
    Execute a swarm simulation. Streams rounds back to Supabase via
    the callback URL, then returns the final report.
    """
    config = SwarmConfig(
        simulation_id=req.simulation_id,
        seed_text=req.seed_text,
        seed_type=req.seed_type,
        agent_count=min(req.agent_count, settings.oracle_max_agents),
        round_count=min(req.round_count, settings.oracle_max_rounds),
        agent_mix=req.agent_mix,
        llm_model=req.llm_model,
        environments=req.environments,
    )

    result = await swarm_engine.run(config)

    # ── Stream rounds to Supabase (fire-and-forget) ──
    sim_id = req.supabase_simulation_id or req.simulation_id
    asyncio.create_task(_write_rounds(sim_id, result.rounds))
    asyncio.create_task(_finalize_simulation(sim_id, result))

    return {
        "simulation_id": req.simulation_id,
        "status": result.status,
        "rounds": result.rounds,
        "report": result.report,
        "tokens_used": result.tokens_used,
        "cost_usd": result.cost_usd,
    }


@router.post("/debate")
async def run_debate_endpoint(req: Request):
    """
    Run the L7 multi-agent debate (Bull/Bear/Risk → Consensus).
    Called by autopilot-loop after a swarm completes.
    """
    body = await req.json()
    swarm_report = body.get("swarm_report", body.get("report", {}))
    signals = body.get("signals", [])
    portfolio_state = body.get("portfolio_state")

    result = await oracle_brain.run_debate(swarm_report, signals, portfolio_state)
    return result


async def _write_rounds(simulation_id: str, rounds: list[dict]) -> None:
    """Write round-by-round results to simulation_rounds table."""
    if not settings.supabase_url:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            for r in rounds:
                await client.post(
                    f"{settings.supabase_url}/rest/v1/simulation_rounds",
                    json={"simulation_id": simulation_id, **r},
                    headers={
                        "apikey": settings.supabase_service_role_key,
                        "Authorization": f"Bearer {settings.supabase_service_role_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                )
    except Exception as e:
        logger.warning("write_rounds_failed", error=str(e))


async def _finalize_simulation(simulation_id: str, result) -> None:
    """Update the simulation record with final verdict + metrics."""
    if not settings.supabase_url:
        return
    try:
        report = result.report
        async with httpx.AsyncClient(timeout=10) as client:
            await client.patch(
                f"{settings.supabase_url}/rest/v1/simulations?id=eq.{simulation_id}",
                json={
                    "status": "complete",
                    "current_round": len(result.rounds),
                    "final_bullish": report.get("final_bullish"),
                    "final_bearish": report.get("final_bearish"),
                    "final_neutral": report.get("final_neutral"),
                    "confidence": report.get("confidence"),
                    "verdict": report.get("verdict"),
                    "narrative": report.get("executive_summary"),
                    "predicted_impact": report.get("predicted_impacts"),
                    "tokens_used": result.tokens_used,
                    "cost_usd": result.cost_usd,
                    "completed_at": "now()",
                },
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Authorization": f"Bearer {settings.supabase_service_role_key}",
                    "Content-Type": "application/json",
                },
            )
            # Write report
            await client.post(
                f"{settings.supabase_url}/rest/v1/simulation_reports",
                json={
                    "simulation_id": simulation_id,
                    "verdict": report.get("verdict"),
                    "confidence": report.get("confidence"),
                    "executive_summary": report.get("executive_summary"),
                    "narrative_themes": report.get("narrative_themes"),
                    "institutional_consensus": report.get("institutional_consensus"),
                    "retail_consensus": report.get("retail_consensus"),
                    "media_framing": report.get("media_framing"),
                    "predicted_impacts": report.get("predicted_impacts"),
                    "recommended_actions": report.get("recommended_actions"),
                },
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Authorization": f"Bearer {settings.supabase_service_role_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
            )
    except Exception as e:
        logger.error("finalize_sim_failed", error=str(e))
