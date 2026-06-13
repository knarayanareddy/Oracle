# ════════════════════════════════════════════════════════════════
# Strategy Router (§04 Module 3)
# POST /api/v1/strategy/parse   — NL → structured conditions
# POST /api/v1/strategy/backtest — run historical backtest
# ════════════════════════════════════════════════════════════════
import asyncio
import json
from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Any

import yfinance as yf
import pandas as pd

from config import settings
from logging_config import logger
from services.backtest import backtest_engine
from services.langchain_brain import PRIMARY_LLM
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])

PARSE_PROMPT = """You are ORACLE's strategy parser. Convert the user's natural language trading strategy description into a structured JSON object.

Output format:
{
  "name": "short name",
  "entry": [{"layer": "L4|L5|L6", "condition": "rsi|macd_cross_up|swarm_bullish|polymarket_prob|above_ema50|price_below_bb_lower", "operator": ">|<|=", "threshold": number, "asset": "optional"}],
  "exit": [{"layer": "...", "condition": "...", "operator": "...", "threshold": number}],
  "risk": {"max_position_pct": 0.1, "stop_loss_pct": 0.08, "max_daily_trades": 3}
}

Map common phrases:
- "RSI below 30" → entry L4 rsi < 30
- "swarm bullish above 60%" → entry L6 swarm_bullish > 0.60
- "Polymarket probability above 70%" → entry L5 polymarket_prob > 0.70
- "above EMA50" → entry L4 above_ema50 = 1
- "MACD crossover" → entry L4 macd_cross_up = 1
- "stop loss at X%" → risk stop_loss_pct

Output ONLY valid JSON, no explanation."""


class StrategyParseRequest(BaseModel):
    description: str = Field(..., min_length=5)


class BacktestRequest(BaseModel):
    conditions: dict
    symbol: str = "NVDA"
    start_date: str = "2022-01-03"
    end_date: str = "2026-06-01"
    initial_capital: float = 100_000
    layers_used: list[str] = Field(default_factory=lambda: ["L4"])


@router.post("/parse")
async def parse_strategy(req: StrategyParseRequest):
    """Parse natural language into structured strategy conditions."""
    if PRIMARY_LLM:
        try:
            resp = await PRIMARY_LLM.ainvoke([
                SystemMessage(content=PARSE_PROMPT),
                HumanMessage(content=req.description),
            ])
            parsed = json.loads(resp.content)
            parsed["natural_language_input"] = req.description
            return parsed
        except Exception as e:
            logger.warning("strategy_parse_llm_failed", error=str(e))

    return _fallback_parse(req.description)


@router.post("/backtest")
async def backtest_strategy(req: BacktestRequest):
    """Run a historical backtest on parsed strategy conditions."""
    from services.market_data_provider import market_data_manager

    # Fetch via provider chain (polygon → alphavantage → yfinance)
    ohlcv, spy_ohlcv = await asyncio.gather(
        market_data_manager.get_history(req.symbol, req.start_date, req.end_date),
        market_data_manager.get_history("SPY", req.start_date, req.end_date),
    )

    if ohlcv is None or ohlcv.empty:
        return {"error": f"No data for {req.symbol} from any provider"}

    result = backtest_engine.run(
        ohlcv=ohlcv,
        spy_ohlcv=spy_ohlcv if spy_ohlcv is not None else ohlcv,
        conditions=req.conditions,
        initial_capital=req.initial_capital,
        layers_used=req.layers_used,
    )

    return {
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_capital": result.final_capital,
        "total_return": result.total_return,
        "benchmark_return": result.benchmark_return,
        "alpha": result.alpha,
        "sharpe_ratio": result.sharpe_ratio,
        "sortino_ratio": result.sortino_ratio,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "profit_factor": result.profit_factor,
        "total_trades": result.total_trades,
        "equity_curve": result.equity_curve,
        "monthly_returns": result.monthly_returns,
        "layer_contribution": result.layer_contribution,
    }


def _fallback_parse(description: str) -> dict:
    """Keyword-based fallback parser."""
    d = description.lower()
    entry = []
    if "rsi" in d:
        thresh = 30 if "below" in d or "under" in d or "<" in d else 70
        op = "<" if thresh == 30 else ">"
        entry.append({"layer": "L4", "condition": "rsi", "operator": op, "threshold": thresh})
    if "swarm" in d:
        entry.append({"layer": "L6", "condition": "swarm_bullish", "operator": ">", "threshold": 0.60})
    if "polymarket" in d:
        entry.append({"layer": "L5", "condition": "polymarket_prob", "operator": ">", "threshold": 0.70})
    if "ema" in d or "trend" in d:
        entry.append({"layer": "L4", "condition": "above_ema50", "operator": "=", "threshold": 1})
    if "macd" in d:
        entry.append({"layer": "L4", "condition": "macd_cross_up", "operator": "=", "threshold": 1})
    if not entry:
        entry.append({"layer": "L4", "condition": "above_ema50", "operator": "=", "threshold": 1})

    return {
        "name": description[:40],
        "natural_language_input": description,
        "entry": entry,
        "exit": [{"layer": "L4", "condition": "rsi", "operator": ">", "threshold": 65}],
        "risk": {"max_position_pct": 0.15, "stop_loss_pct": 0.08, "max_daily_trades": 3},
    }
