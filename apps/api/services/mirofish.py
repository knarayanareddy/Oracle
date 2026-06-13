# ════════════════════════════════════════════════════════════════
# MiroFish Swarm Engine Wrapper (§11)
# Wraps the forked OASIS-based simulation. Provides a clean async API.
# Falls back to a deterministic mock simulation when MiroFish is not
# installed (hackathon safety net — ADR-009 offline path).
# ════════════════════════════════════════════════════════════════
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any

from config import settings
from logging_config import logger

# Try to import the real MiroFish fork (oracle-swarm submodule)
try:
    from oracle_swarm import run_simulation as _mirofish_run  # type: ignore
    MIROFISH_AVAILABLE = True
except ImportError:
    _mirofish_run = None
    MIROFISH_AVAILABLE = False


@dataclass
class SwarmConfig:
    simulation_id: str
    seed_text: str
    seed_type: str = "user_thesis"
    agent_count: int = 500
    round_count: int = 40
    agent_mix: dict = field(default_factory=lambda: {"institutional": 35, "retail": 50, "media": 15})
    llm_model: str = "gpt-4o-mini"
    environments: list = field(default_factory=lambda: ["twitter", "reddit"])


@dataclass
class SwarmResult:
    simulation_id: str
    status: str
    rounds: list[dict]
    report: dict
    tokens_used: int
    cost_usd: float


class SwarmEngine:
    """Facade for the MiroFish swarm simulation."""

    async def run(self, config: SwarmConfig) -> SwarmResult:
        logger.info(
            "swarm_run_start",
            simulation_id=config.simulation_id,
            agent_count=config.agent_count,
            round_count=config.round_count,
            llm_model=config.llm_model,
            engine="mirofish" if MIROFISH_AVAILABLE else "mock",
        )
        start = time.monotonic()

        if MIROFISH_AVAILABLE and not settings.oracle_offline_mode:
            result = await self._run_mirofish(config)
        else:
            result = await self._run_mock(config)

        elapsed = time.monotonic() - start
        logger.info(
            "swarm_run_complete",
            simulation_id=config.simulation_id,
            elapsed_s=round(elapsed, 2),
            verdict=result.report.get("verdict"),
            confidence=result.report.get("confidence"),
            tokens=result.tokens_used,
        )
        return result

    async def _run_mirofish(self, config: SwarmConfig) -> SwarmResult:
        """Call the real MiroFish fork."""
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: _mirofish_run(
                seed_text=config.seed_text,
                agent_count=config.agent_count,
                round_count=config.round_count,
                agent_mix=config.agent_mix,
                llm_model=config.llm_model,
                environments=config.environments,
            ),
        )
        return SwarmResult(
            simulation_id=config.simulation_id,
            status="complete",
            rounds=raw.get("rounds", []),
            report=raw.get("report", {}),
            tokens_used=raw.get("tokens_used", 0),
            cost_usd=raw.get("cost_usd", 0.0),
        )

    async def _run_mock(self, config: SwarmConfig) -> SwarmResult:
        """
        Deterministic mock simulation for hackathon demo when MiroFish
        is not installed. Produces realistic round-by-round consensus
        drift using a biased random walk influenced by seed sentiment.
        ════════════════════════════════════════════════════════════
        """
        rounds: list[dict] = []
        # Seed-determined initial bias (simple keyword heuristic)
        bearish_kw = ["rate hike", "recession", "crash", "bear", "sell", "fear", "inflation", "cut", "miss"]
        bullish_kw = ["beat", "buyback", "growth", "bull", "rally", "surge", "record", "upgrade", "strong"]
        text_lower = config.seed_text.lower()
        bias = sum(1 for k in bullish_kw if k in text_lower) - sum(1 for k in bearish_kw if k in text_lower)
        # Map bias to starting bullish probability
        bull = max(0.15, min(0.85, 0.5 + bias * 0.08))
        bear = (1 - bull) * 0.7
        neutral = 1 - bull - bear

        for r in range(1, config.round_count + 1):
            # Opinion dynamics: herding amplifies dominant view
            dominant = max(bull, bear, neutral)
            if dominant == bull:
                bull = min(0.85, bull + random.uniform(0.005, 0.02))
            elif dominant == bear:
                bear = min(0.80, bear + random.uniform(0.005, 0.02))
            total = bull + bear + neutral
            bull, bear, neutral = bull / total, bear / total, neutral / total

            interactions = int(config.agent_count * random.uniform(0.3, 0.6))
            shifts = int(interactions * random.uniform(0.1, 0.25))
            coalitions = int(config.agent_count * random.uniform(0.05, 0.15))

            rounds.append({
                "round_number": r,
                "bullish_pct": round(bull, 4),
                "bearish_pct": round(bear, 4),
                "neutral_pct": round(neutral, 4),
                "interactions": interactions,
                "opinion_shifts": shifts,
                "coalitions": coalitions,
                "dominant_narrative": self._narrative(bull, bear, config.seed_text),
                "agent_activity": {
                    "institutional": {"active": int(config.agent_count * 0.35 * random.uniform(0.6, 0.9))},
                    "retail": {"active": int(config.agent_count * 0.50 * random.uniform(0.5, 0.85))},
                    "media": {"active": int(config.agent_count * 0.15 * random.uniform(0.7, 1.0))},
                },
            })
            # Simulate async round execution (faster for demo: 150ms)
            await asyncio.sleep(0.15)

        # Final verdict
        if bull > bear and bull > neutral:
            verdict = "BULLISH"
        elif bear > bull and bear > neutral:
            verdict = "BEARISH"
        else:
            verdict = "NEUTRAL"

        confidence = round(max(bull, bear, neutral), 4)
        tokens = config.agent_count * config.round_count * random.randint(120, 180)
        cost = round(tokens * (0.0004 if "qwen" in config.llm_model else 0.01) / 1000, 4)

        report = {
            "verdict": verdict,
            "confidence": confidence,
            "final_bullish": round(bull, 4),
            "final_bearish": round(bear, 4),
            "final_neutral": round(neutral, 4),
            "executive_summary": self._summary(verdict, confidence, config.seed_text),
            "narrative_themes": self._themes(verdict),
            "institutional_consensus": "Accumulating on weakness, positioning for recovery" if verdict == "BULLISH" else "De-risking, raising cash buffers",
            "retail_consensus": "FOMO-driven buying detected" if verdict == "BULLISH" else "Panic selling and capitulation patterns emerging",
            "media_framing": "Optimistic coverage dominating headlines" if verdict == "BULLISH" else "Fear-based narratives amplifying downside",
            "predicted_impacts": self._impacts(verdict),
            "recommended_actions": self._actions(verdict, config.seed_text),
        }

        return SwarmResult(
            simulation_id=config.simulation_id,
            status="complete",
            rounds=rounds,
            report=report,
            tokens_used=tokens,
            cost_usd=cost,
        )

    def _narrative(self, bull: float, bear: float, seed: str) -> str:
        if bull > bear:
            return "Institutional accumulation driving retail FOMO"
        if bear > bull:
            return "Risk-off sentiment cascading through retail"
        return "Mixed signals — institutions cautious, retail divided"

    def _summary(self, verdict: str, conf: float, seed: str) -> str:
        return (
            f"Swarm of agents reached {verdict.lower()} consensus "
            f"({conf*100:.0f}% confidence) in response to: \"{seed[:80]}...\". "
            f"The simulation reveals {'optimistic' if verdict == 'BULLISH' else 'pessimistic' if verdict == 'BEARISH' else 'divided'} "
            f"market psychology with {'strong' if conf > 0.65 else 'moderate'} conviction."
        )

    def _themes(self, verdict: str) -> list[dict]:
        if verdict == "BULLISH":
            return [
                {"theme": "Momentum continuation", "prevalence": 0.42, "agents": 210},
                {"theme": "Earnings optimism", "prevalence": 0.28, "agents": 140},
                {"theme": "Dip-buying resolve", "prevalence": 0.18, "agents": 90},
            ]
        elif verdict == "BEARISH":
            return [
                {"theme": "Rate-hike anxiety", "prevalence": 0.38, "agents": 190},
                {"theme": "Recession hedging", "prevalence": 0.29, "agents": 145},
                {"theme": "Tech de-rating", "prevalence": 0.21, "agents": 105},
            ]
        return [
            {"theme": "Range-bound indecision", "prevalence": 0.35, "agents": 175},
            {"theme": "Conflicting macro signals", "prevalence": 0.30, "agents": 150},
        ]

    def _impacts(self, verdict: str) -> dict[str, float]:
        if verdict == "BULLISH":
            return {"tech": 0.028, "financials": 0.015, "bonds": -0.008, "crypto": 0.041}
        if verdict == "BEARISH":
            return {"tech": -0.032, "financials": -0.018, "bonds": 0.011, "crypto": -0.045}
        return {"tech": 0.004, "financials": 0.001, "bonds": 0.002, "crypto": -0.003}

    def _actions(self, verdict: str, seed: str) -> list[dict]:
        if verdict == "BULLISH":
            return [{"action": "BUY", "asset": "NVDA", "rationale": "Swarm bullish consensus + technical confirmation"}]
        if verdict == "BEARISH":
            return [{"action": "REDUCE", "asset": "NVDA", "rationale": "Bearish swarm + elevated macro risk"}]
        return [{"action": "HOLD", "asset": "SPY", "rationale": "Neutral consensus — no edge detected"}]


# Singleton
swarm_engine = SwarmEngine()
