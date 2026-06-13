# ════════════════════════════════════════════════════════════════
# LangChain Brain — Agent Orchestration (§12)
# Intent router, debate agents (Bull/Bear/Risk/Consensus), L10 explainer.
# Uses GPT-4o for primary reasoning (ADR-006).
#
# RESILIENCE: Every LLM call is wrapped in a circuit breaker + retry.
# If the circuit trips (sustained OpenAI outages/rate limits), calls
# fall back to deterministic logic rather than crashing — but the
# breaker's cooldown prevents oscillation. The `mode` field in the
# response tells the caller whether real LLM or fallback was used.
#
# Addresses expert feedback: "robust retry logic and circuit breakers
# for LLM calls" + "abrupt shifts in recommendation quality"
# ════════════════════════════════════════════════════════════════
import json
import asyncio
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config import settings
from logging_config import logger
from services.resilience import resilient_call, retry_with_backoff, llm_breaker


# ── LLM instances ──
def _get_llm(model: str = "gpt-4o") -> ChatOpenAI | None:
    if not settings.openai_api_key:
        return None
    return ChatOpenAI(model=model, temperature=0.7, api_key=settings.openai_api_key)


PRIMARY_LLM = _get_llm("gpt-4o")

# ── System prompts (§12) ──
BULL_PROMPT = """You are an optimistic equity analyst. Given the swarm results and market signals, construct the strongest possible bullish argument. Be specific, data-driven, and reference layer signals. Output JSON: {"argument": str, "supporting_signals": [str], "confidence": float}"""

BEAR_PROMPT = """You are a risk-focused portfolio manager. Given the swarm results and market signals, construct the strongest possible bearish/cautious argument. Be specific, data-driven, and reference layer signals. Output JSON: {"argument": str, "supporting_signals": [str], "confidence": float}"""

RISK_PROMPT = """You are a risk officer. Given the bull and bear arguments, assess portfolio-level risk implications. Output JSON: {"risk_score": int(1-10), "position_sizing": str, "max_exposure": float}"""

CONSENSUS_PROMPT = """You are ORACLE's consensus synthesizer. Given bull, bear, and risk agent outputs plus the swarm verdict, produce a final consensus. Output JSON: {"consensus": "BUY"|"SELL"|"HOLD"|"REDUCE"|"REBALANCE", "confidence": float, "reasoning": str, "recommended_action": {"asset": str, "action": str, "from_pct": float, "to_pct": float, "rationale": str}}"""

EXPLANATION_PROMPT = """You are ORACLE's explanation engine. Given a trading recommendation and the full reasoning chain that produced it, generate a clear, concise explanation for the user.

Requirements:
- Write in plain English, no jargon
- Explain WHICH layers activated and WHY they matter
- Quantify the key signals (e.g., "63% of simulated agents...")
- State what the recommendation is and why
- Acknowledge uncertainty honestly
- Never claim certainty about market outcomes
- End with what ORACLE will do if conditions change

Format: 2-3 sentences max for main explanation, then bullet points for key factors."""

INTENT_PROMPT = """Classify the user's command into one of these intents:
- run_swarm_simulation: user wants to run a swarm simulation on a topic
- query_portfolio: user asks about their portfolio, risk, or positions
- build_strategy: user wants to create or backtest a trading strategy
- generate_recommendation: user wants advice on what to do
- set_autopilot: user wants to activate/deactivate autopilot

Output JSON: {"intent": str, "parameters": {}}"""


# ════════════════════════════════════════════════════════════════
# Safe JSON parsing — LLMs sometimes wrap JSON in markdown or add prose
# ════════════════════════════════════════════════════════════════
def _safe_json_parse(text: str) -> dict | None:
    """Extract and parse JSON from an LLM response, tolerating markdown fences."""
    if not text:
        return None
    # Strip markdown code fences
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(l for l in lines if not l.strip().startswith("```"))
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Try extracting first {...} block
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


class OracleBrain:
    """LangChain-powered multi-agent reasoning engine with resilient LLM calls."""

    # ════════════════════════════════════════════════════════════════
    # Helper: invoke LLM through circuit breaker + retry
    # ════════════════════════════════════════════════════════════════
    async def _invoke_llm(
        self,
        messages: list,
        *,
        fallback_value: Any = None,
        max_retries: int | None = None,
    ) -> Any:
        """
        Invoke the primary LLM through the circuit breaker with retry.
        Returns the raw response object, or fallback_value on failure.
        """
        if PRIMARY_LLM is None:
            return fallback_value

        retries = max_retries if max_retries is not None else settings.llm_max_retries

        async def _call():
            return await PRIMARY_LLM.ainvoke(messages)

        return await resilient_call(
            _call,
            breaker=llm_breaker,
            fallback=lambda: fallback_value,
            max_retries=retries,
        )

    async def _invoke_llm_json(
        self,
        system_prompt: str,
        user_content: str,
        *,
        fallback: dict | None = None,
    ) -> tuple[dict | None, str]:
        """
        Invoke LLM expecting JSON output.
        Returns (parsed_dict_or_None, mode) where mode is "llm" or "fallback".
        """
        resp = await self._invoke_llm(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_content)],
            fallback_value=None,
        )
        if resp is None:
            return fallback, "fallback"
        parsed = _safe_json_parse(resp.content)
        if parsed is None:
            logger.warning("llm_json_parse_failed", content_preview=resp.content[:100])
            return fallback, "fallback"
        return parsed, "llm"

    # ════════════════════════════════════════════════════════════════
    # Intent Router
    # ════════════════════════════════════════════════════════════════
    async def route_intent(self, transcript: str) -> dict:
        """Intent router (§12). Falls back to keyword matching if no LLM."""
        parsed, mode = await self._invoke_llm_json(
            INTENT_PROMPT, transcript,
            fallback=self._keyword_intent(transcript),
        )
        if parsed and "intent" in parsed:
            if mode == "fallback":
                logger.info("intent_router_fallback", transcript=transcript[:50])
            return parsed
        return self._keyword_intent(transcript)

    @staticmethod
    def _keyword_intent(transcript: str) -> dict:
        t = transcript.lower()
        if any(k in t for k in ["simulate", "swarm", "agents on", "run a sim"]):
            return {"intent": "run_swarm_simulation", "parameters": {"seed_text": transcript}}
        if any(k in t for k in ["portfolio", "risk", "exposure", "positions", "holdings"]):
            return {"intent": "query_portfolio", "parameters": {"query": transcript}}
        if any(k in t for k in ["strategy", "backtest", "build a", "create a rule"]):
            return {"intent": "build_strategy", "parameters": {"description": transcript}}
        if any(k in t for k in ["autopilot", "autonomous", "turn on", "activate"]):
            return {"intent": "set_autopilot", "parameters": {"status": True}}
        return {"intent": "generate_recommendation", "parameters": {"query": transcript}}

    # ════════════════════════════════════════════════════════════════
    # Multi-Agent Debate (L7) — with circuit breaker on each call
    # ════════════════════════════════════════════════════════════════
    async def run_debate(
        self,
        swarm_report: dict,
        signals: list[dict],
        portfolio_state: dict | None = None,
    ) -> dict:
        """
        Bull Agent vs Bear Agent vs Risk Agent → Consensus Synthesizer.

        Each LLM call is independently wrapped in the circuit breaker.
        Bull + Bear run concurrently; if one fails it degrades to a
        partial argument rather than collapsing the entire debate.
        """
        context = json.dumps({
            "swarm_report": swarm_report,
            "market_signals": signals[-10:],
            "portfolio": portfolio_state,
        }, indent=2)

        # ── If circuit is already open, skip straight to deterministic ──
        if PRIMARY_LLM is None or llm_breaker.state == "open":
            logger.info("debate_skipped_circuit_open" if llm_breaker.state == "open" else "debate_no_llm")
            result = self._mock_debate(swarm_report)
            result["mode"] = "circuit_open" if llm_breaker.state == "open" else "no_llm"
            return result

        # ── Run bull + bear concurrently (each with its own resilience) ──
        bull_task = self._invoke_llm_json(BULL_PROMPT, context, fallback=None)
        bear_task = self._invoke_llm_json(BEAR_PROMPT, context, fallback=None)
        bull_result, bear_result = await asyncio.gather(bull_task, bear_task)

        bull, bull_mode = bull_result
        bear, bear_mode = bear_result

        # If both bull and bear failed (circuit likely tripped), use mock
        if bull is None and bear is None:
            logger.warning("debate_both_agents_failed")
            result = self._mock_debate(swarm_report)
            result["mode"] = "circuit_open"
            return result

        # Fill in missing arguments with deterministic fallbacks
        if bull is None:
            bull = {"argument": "Momentum and accumulation patterns suggest constructive outlook.", "supporting_signals": ["swarm_bullish"], "confidence": 0.5}
            bull_mode = "partial_fallback"
        if bear is None:
            bear = {"argument": "Macro risk and sentiment indicators warrant caution.", "supporting_signals": ["yield_curve"], "confidence": 0.5}
            bear_mode = "partial_fallback"

        # ── Risk agent (sequential — depends on bull + bear) ──
        risk, risk_mode = await self._invoke_llm_json(
            RISK_PROMPT,
            json.dumps({"bull": bull, "bear": bear}),
            fallback={"risk_score": 5, "position_sizing": "moderate", "max_exposure": 0.15},
        )

        # ── Consensus synthesizer ──
        consensus, consensus_mode = await self._invoke_llm_json(
            CONSENSUS_PROMPT,
            json.dumps({"bull": bull, "bear": bear, "risk": risk, "swarm_verdict": swarm_report.get("verdict")}),
            fallback=self._mock_consensus(swarm_report, bull, bear, risk),
        )

        mode = "llm" if all(m == "llm" for m in [bull_mode, bear_mode, risk_mode, consensus_mode]) else "partial_fallback"

        return {
            "bull_argument": bull.get("argument", ""),
            "bear_argument": bear.get("argument", ""),
            "risk_assessment": risk.get("risk_score", 5) if risk else 5,
            "consensus": consensus.get("consensus", "HOLD"),
            "confidence": consensus.get("confidence", 0.5),
            "reasoning_trail": {
                "bull_signals": bull.get("supporting_signals", []),
                "bear_signals": bear.get("supporting_signals", []),
                "risk_sizing": risk.get("position_sizing", "") if risk else "",
                "explanation": consensus.get("reasoning", ""),
            },
            "recommended_action": consensus.get("recommended_action", {}),
            "layers_activated": ["L6", "L7", "L8", "L10"],
            "mode": mode,
            "agent_modes": {"bull": bull_mode, "bear": bear_mode, "risk": risk_mode, "consensus": consensus_mode},
        }

    # ════════════════════════════════════════════════════════════════
    # L10 Explanation Generator
    # ════════════════════════════════════════════════════════════════
    async def generate_explanation(self, recommendation: dict, reasoning_chain: dict) -> str:
        """L10 Explanation Generator — plain English for the user."""
        resp = await self._invoke_llm(
            [
                SystemMessage(content=EXPLANATION_PROMPT),
                HumanMessage(content=json.dumps({"recommendation": recommendation, "reasoning": reasoning_chain})),
            ],
            fallback_value=None,
        )
        if resp is not None and resp.content:
            return resp.content

        return self._fallback_explanation(recommendation)

    @staticmethod
    def _fallback_explanation(recommendation: dict) -> str:
        consensus = recommendation.get("consensus", "HOLD")
        conf = recommendation.get("confidence", 0.5)
        return (
            f"ORACLE recommends {consensus} with {conf*100:.0f}% confidence. "
            f"This decision synthesizes swarm simulation, multi-agent debate, and risk assessment. "
            f"• Key factor: {'Bullish consensus emerging from agent simulation' if consensus == 'BUY' else 'Bearish signals dominating across layers' if consensus in ('SELL','REDUCE') else 'Mixed signals warrant caution'}\n"
            f"• If conditions change, ORACLE will re-evaluate automatically."
        )

    # ════════════════════════════════════════════════════════════════
    # Deterministic fallbacks
    # ════════════════════════════════════════════════════════════════
    def _mock_debate(self, swarm_report: dict) -> dict:
        """Fallback debate when LLM unavailable or circuit open."""
        verdict = swarm_report.get("verdict", "NEUTRAL")
        conf = swarm_report.get("confidence", 0.5)
        consensus = {"BULLISH": "BUY", "BEARISH": "REDUCE", "NEUTRAL": "HOLD"}.get(verdict, "HOLD")
        return {
            "bull_argument": "Momentum indicators and institutional accumulation patterns support a constructive outlook.",
            "bear_argument": "Elevated macro risk and yield curve signals suggest caution is warranted.",
            "risk_assessment": 5,
            "consensus": consensus,
            "confidence": conf,
            "reasoning_trail": {
                "bull_signals": ["swarm_bullish_pct", "technical_momentum"],
                "bear_signals": ["yield_curve", "macro_risk"],
                "explanation": f"Consensus {consensus} derived from {verdict.lower()} swarm verdict at {conf*100:.0f}% confidence.",
            },
            "recommended_action": {"asset": "NVDA", "action": consensus, "rationale": "Swarm-driven consensus"},
            "layers_activated": ["L6", "L7", "L8", "L10"],
            "mode": "no_llm",
        }

    def _mock_consensus(self, swarm_report: dict, bull: dict, bear: dict, risk: dict | None) -> dict:
        """Fallback consensus synthesizer when LLM unavailable."""
        verdict = swarm_report.get("verdict", "NEUTRAL")
        consensus = {"BULLISH": "BUY", "BEARISH": "REDUCE", "NEUTRAL": "HOLD"}.get(verdict, "HOLD")
        bull_conf = bull.get("confidence", 0.5)
        bear_conf = bear.get("confidence", 0.5)
        confidence = swarm_report.get("confidence", max(bull_conf, bear_conf))
        return {
            "consensus": consensus,
            "confidence": confidence,
            "reasoning": f"Consensus {consensus} from {verdict.lower()} swarm. Bull confidence {bull_conf:.0%}, Bear confidence {bear_conf:.0%}.",
            "recommended_action": {"asset": "NVDA", "action": consensus, "rationale": "Swarm-driven consensus (fallback synthesis)"},
        }


# Singleton
oracle_brain = OracleBrain()
