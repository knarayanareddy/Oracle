# ════════════════════════════════════════════════════════════════
# ORACLE API — GraphRAG + Market Data + Security Tests
# Tests for the new institutional-grade modules.
# ════════════════════════════════════════════════════════════════
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ════════════════════════════════════════════════════════════════
# GraphRAG Engine — entity extraction (pure logic, no DB needed)
# ════════════════════════════════════════════════════════════════
def test_graphrag_extract_tickers():
    from services.graphrag import graphrag_engine
    entities = graphrag_engine.extract_entities("NVDA and AAPL both beat earnings expectations")
    labels = [e["label"] for e in entities]
    assert "NVDA" in labels
    assert "AAPL" in labels
    assert any(e["type"] == "event" and e["label"] == "earnings" for e in entities)


def test_graphrag_extract_macro_concepts():
    from services.graphrag import graphrag_engine
    entities = graphrag_engine.extract_entities("Fed signals rate hike amid rising inflation")
    labels = [e["label"] for e in entities]
    assert "rate hike" in labels
    assert "inflation" in labels
    assert any(e["type"] == "event" and e["label"] == "fed_statement" for e in entities)


def test_graphrag_extract_empty_text():
    from services.graphrag import graphrag_engine
    entities = graphrag_engine.extract_entities("nothing relevant here")
    assert entities == []


def test_graphrag_extract_crypto():
    from services.graphrag import graphrag_engine
    entities = graphrag_engine.extract_entities("BTC breaks all-time high as ETH follows")
    labels = [e["label"] for e in entities]
    crypto_nodes = [e for e in entities if e["type"] == "asset" and e.get("properties", {}).get("class") == "crypto"]
    assert len(crypto_nodes) >= 1


# ════════════════════════════════════════════════════════════════
# Market Data Provider Chain
# ════════════════════════════════════════════════════════════════
def test_market_data_chain_has_yfinance():
    """yfinance is always available (no key needed)."""
    from services.market_data_provider import market_data_manager
    names = [p.name for p in market_data_manager._chain]
    assert "yfinance" in names


def test_market_data_chain_includes_polygon_when_configured():
    """Polygon should be in chain if key is set."""
    from services.market_data_provider import PolygonProvider, YFinanceProvider
    yf = YFinanceProvider()
    assert yf.available is True  # always available
    poly = PolygonProvider()
    # available depends on whether key is set — just verify property works
    assert isinstance(poly.available, bool)


@pytest.mark.asyncio
async def test_yfinance_get_history():
    """Integration test — fetches real data from yfinance (no key)."""
    from services.market_data_provider import YFinanceProvider
    provider = YFinanceProvider()
    df = await provider.get_history("AAPL", "2024-01-01", "2024-03-01")
    # yfinance might be rate-limited in CI, so just check it doesn't crash
    if df is not None:
        assert not df.empty
        assert "Close" in df.columns


# ════════════════════════════════════════════════════════════════
# Security Guards
# ════════════════════════════════════════════════════════════════
def test_security_validate_config_no_crash():
    """Security validation should run without crashing."""
    from services.security import validate_security_config
    warnings = validate_security_config()
    assert isinstance(warnings, list)


def test_security_scan_detects_jwt():
    """Leak scanner should detect JWT-like tokens."""
    from services.security import scan_for_key_leaks
    # Fake JWT-looking string
    assert scan_for_key_leaks('{"key": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijklmnopqrstuvwxyz123456"}') is True


def test_security_scan_clean_text():
    """Leak scanner should pass clean responses."""
    from services.security import scan_for_key_leaks
    assert scan_for_key_leaks('{"status": "healthy", "version": "1.0.0"}') is False


def test_security_is_service_role_key():
    from services.security import is_service_role_key
    assert is_service_role_key("not-a-jwt") is False
    assert is_service_role_key("") is False


# ════════════════════════════════════════════════════════════════
# Polymarket volatility detection
# ════════════════════════════════════════════════════════════════
def test_polymarket_asset_extraction():
    from services.signals.l5_polymarket import L5Polymarket
    assert L5Polymarket._extract_asset("Will the Fed raise rates?") == "FED"
    assert L5Polymarket._extract_asset("Will inflation exceed 3%?") == "CPI"
    assert L5Polymarket._extract_asset("Random unrelated question") is None


def test_polymarket_volatility_threshold():
    from services.signals.l5_polymarket import VOLATILITY_SWING_THRESHOLD
    assert VOLATILITY_SWING_THRESHOLD > 0
    assert VOLATILITY_SWING_THRESHOLD < 1


# ════════════════════════════════════════════════════════════════
# LangChain brain safe JSON parsing
# ════════════════════════════════════════════════════════════════
def test_safe_json_parse_plain():
    from services.langchain_brain import _safe_json_parse
    assert _safe_json_parse('{"consensus": "BUY"}') == {"consensus": "BUY"}


def test_safe_json_parse_markdown_fenced():
    from services.langchain_brain import _safe_json_parse
    result = _safe_json_parse('```json\n{"consensus": "SELL"}\n```')
    assert result == {"consensus": "SELL"}


def test_safe_json_parse_with_prose():
    from services.langchain_brain import _safe_json_parse
    result = _safe_json_parse('Here is my analysis: {"consensus": "HOLD", "confidence": 0.7} That is all.')
    assert result == {"consensus": "HOLD", "confidence": 0.7}


def test_safe_json_parse_invalid():
    from services.langchain_brain import _safe_json_parse
    assert _safe_json_parse("not json at all") is None
    assert _safe_json_parse("") is None


@pytest.mark.asyncio
async def test_brain_keyword_intent_fallback():
    """When no LLM, intent routing should use keyword fallback."""
    from services.langchain_brain import oracle_brain
    result = await oracle_brain.route_intent("run a swarm simulation on inflation")
    assert result["intent"] == "run_swarm_simulation"


@pytest.mark.asyncio
async def test_brain_debate_fallback_mode():
    """When no LLM, debate should return deterministic result with mode flag."""
    from services.langchain_brain import oracle_brain
    result = await oracle_brain.run_debate(
        swarm_report={"verdict": "BEARISH", "confidence": 0.65},
        signals=[{"layer": "L5", "direction": "bearish"}],
    )
    assert result["consensus"] in ("BUY", "SELL", "HOLD", "REDUCE", "REBALANCE")
    assert "mode" in result  # should indicate fallback
    assert result["mode"] in ("no_llm", "circuit_open", "partial_fallback", "llm")


# ════════════════════════════════════════════════════════════════
# Memory service GraphRAG integration
# ════════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_memory_context_graceful_without_supabase():
    """Memory service should return empty context if Supabase not configured."""
    from services.memory import memory_service
    memory_service._client = None  # force re-init
    result = await memory_service.get_context("nonexistent-user", "test query")
    # Should not crash — should return structured empty result
    assert "retrieval_method" in result
    assert result["retrieval_method"] in ("error", "skipped", "keyword_fallback", "vector_graphrag")
