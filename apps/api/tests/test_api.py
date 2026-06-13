# ════════════════════════════════════════════════════════════════
# ORACLE API — Unit Tests
# Run: pytest apps/api/tests/ -v
# ════════════════════════════════════════════════════════════════
import sys
import os
import pytest
import asyncio

# Ensure app dir on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Health router ──
def test_health_check():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "services" in data


# ── Swarm config validation ──
def test_swarm_config_defaults():
    from services.mirofish import SwarmConfig
    config = SwarmConfig(simulation_id="test-123", seed_text="Fed signals rate hike")
    assert config.agent_count == 500
    assert config.round_count == 40
    assert config.llm_model == "gpt-4o-mini"
    assert "twitter" in config.environments


# ── Mock swarm engine produces valid output ──
@pytest.mark.asyncio
async def test_mock_swarm_run():
    from services.mirofish import SwarmConfig, swarm_engine
    config = SwarmConfig(
        simulation_id="test-swarm",
        seed_text="Fed signals aggressive rate hikes in 2026",
        agent_count=100,
        round_count=5,
    )
    result = await swarm_engine.run(config)
    assert result.status == "complete"
    assert len(result.rounds) == 5
    assert result.report["verdict"] in ("BULLISH", "BEARISH", "NEUTRAL")
    assert 0 <= result.report["confidence"] <= 1
    assert result.tokens_used > 0


# ── Mock debate produces valid consensus ──
@pytest.mark.asyncio
async def test_mock_debate():
    from services.langchain_brain import oracle_brain
    result = await oracle_brain.run_debate(
        swarm_report={"verdict": "BEARISH", "confidence": 0.65},
        signals=[{"layer": "L5", "direction": "bearish"}],
    )
    assert result["consensus"] in ("BUY", "SELL", "HOLD", "REDUCE", "REBALANCE")
    assert "layers_activated" in result
    assert len(result["bull_argument"]) > 0


# ── Intent routing ──
@pytest.mark.asyncio
async def test_intent_routing():
    from services.langchain_brain import oracle_brain
    result = await oracle_brain.route_intent("Run a swarm simulation on CPI data")
    assert result["intent"] == "run_swarm_simulation"

    result = await oracle_brain.route_intent("What's my portfolio risk?")
    assert result["intent"] == "query_portfolio"


# ── Strategy parser fallback ──
def test_strategy_fallback_parse():
    from routers.strategy import _fallback_parse
    result = _fallback_parse("Buy NVDA when RSI below 30 and swarm bullish above 60%")
    assert len(result["entry"]) >= 1
    assert result["entry"][0]["layer"] in ("L4", "L5", "L6")


# ── Backtest engine technical indicators ──
def test_rsi_calculation():
    import pandas as pd
    from services.backtest import BacktestEngine
    prices = pd.Series([100 + i * 0.5 for i in range(50)])
    rsi = BacktestEngine._rsi(prices, 14)
    # All gains → RSI should be high
    assert rsi.iloc[-1] > 80


def test_sharpe_ratio_edge_cases():
    from services.backtest import BacktestEngine
    import pandas as pd
    assert BacktestEngine._sharpe(pd.Series([])) == 0.0
    assert BacktestEngine._sharpe(pd.Series([0.01, 0.01, 0.01])) == 0.0  # zero std


# ── Voice intent response ──
def test_voice_intent_response():
    from routers.voice import _intent_response
    resp = _intent_response("run_swarm_simulation", {}, "test")
    assert "swarm" in resp.lower()
    resp = _intent_response("set_autopilot", {}, "test")
    assert "autopilot" in resp.lower()


# ── Signal provider layer assignments ──
def test_signal_layers():
    from services.signals.l1_market_data import L1MarketData
    from services.signals.l2_macro import L2MacroSignals
    from services.signals.l3_news import L3NewsSentiment
    from services.signals.l4_technical import L4Technical
    from services.signals.l5_polymarket import L5Polymarket

    assert L1MarketData().layer == "L1"
    assert L2MacroSignals().layer == "L2"
    assert L3NewsSentiment().layer == "L3"
    assert L4Technical().layer == "L4"
    assert L5Polymarket().layer == "L5"


# ── Polymarket asset extraction ──
def test_polymarket_asset_extraction():
    from services.signals.l5_polymarket import L5Polymarket
    assert L5Polymarket._extract_asset("Will the Fed raise rates?") == "FED"
    assert L5Polymarket._extract_asset("Will there be a recession?") == "recession"
    assert L5Polymarket._extract_asset("Random question") is None
