# ════════════════════════════════════════════════════════════════
# Recommendations Router (§12)
# POST /api/v1/recommendations/generate — full L1-L10 recommendation
# Combines: memory context → signals → debate → explanation
# ════════════════════════════════════════════════════════════════
from fastapi import APIRouter, Request
from pydantic import BaseModel

from config import settings
from logging_config import logger
from services.langchain_brain import oracle_brain
from services.memory import memory_service
from services.signals.pipeline import signal_pipeline

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


class RecommendationRequest(BaseModel):
    user_id: str
    query: str = ""
    asset: str | None = None


@router.post("/generate")
async def generate_recommendation(req: RecommendationRequest):
    """
    Full recommendation pipeline:
    L9 memory → L1-L5 signals → L6/L7/L8 debate → L10 explanation
    """
    # L9: Fetch memory context
    memory_ctx = await memory_service.get_context(req.user_id, req.query)

    # L1-L5: Fetch latest signals
    signals = await signal_pipeline.get_latest(limit=20)

    # L6-L8: Run debate (using mock swarm report from signals)
    swarm_report = _build_swarm_summary(signals)
    debate_result = await oracle_brain.run_debate(
        swarm_report=swarm_report,
        signals=signals,
        portfolio_state=memory_ctx.get("investor_risk_profile"),
    )

    # L10: Generate explanation
    explanation = await oracle_brain.generate_explanation(debate_result, {
        "memory": memory_ctx,
        "signals": signals[:5],
        "swarm": swarm_report,
    })

    # Update memory after recommendation
    await memory_service.update_after_event(req.user_id, {
        "lesson_text": f"Recommended {debate_result.get('consensus')} with {debate_result.get('confidence')} confidence",
        "confidence": 3,
        "tags": ["recommendation"],
        "source_type": "behavior_pattern",
    })

    return {
        "consensus": debate_result.get("consensus"),
        "confidence": debate_result.get("confidence"),
        "explanation": explanation,
        "bull_argument": debate_result.get("bull_argument"),
        "bear_argument": debate_result.get("bear_argument"),
        "risk_assessment": debate_result.get("risk_assessment"),
        "recommended_action": debate_result.get("recommended_action", {}),
        "layers_activated": debate_result.get("layers_activated", []),
        "memory_context": {
            "investor_risk": memory_ctx.get("investor_risk_profile", {}).get("revealed_risk"),
            "best_signal_combo": memory_ctx.get("investor_risk_profile", {}).get("best_signal_combo"),
            "recent_lessons": len(memory_ctx.get("relevant_lessons", [])),
        },
    }


def _build_swarm_summary(signals: list[dict]) -> dict:
    """Build a quick swarm-like summary from current signals."""
    bull = sum(1 for s in signals if s.get("direction") == "bullish")
    bear = sum(1 for s in signals if s.get("direction") == "bearish")
    total = max(len(signals), 1)

    verdict = "BULLISH" if bull > bear else "BEARISH" if bear > bull else "NEUTRAL"
    confidence = round(max(bull, bear) / total, 4) if total else 0.5

    return {
        "verdict": verdict,
        "confidence": confidence,
        "final_bullish": round(bull / total, 4),
        "final_bearish": round(bear / total, 4),
    }
