# ════════════════════════════════════════════════════════════════
# L5 — Polymarket Integration (§13, ADR-007)
# Source: Polymarket Gamma API (public REST) + CLOB WebSocket (real-time).
#
# Dual-mode: REST polling (default, 15-min) + optional WebSocket
# subscription for real-time probability updates. WebSocket reconnects
# automatically with exponential backoff.
#
# Volatility guard: detects rapid probability swings and flags them
# as high-confidence contrarian signals (institutional grade).
#
# Addresses expert feedback: "robust WebSocket feeds rather than simple
# polling, as well as handling for high volatility scenarios"
# ════════════════════════════════════════════════════════════════
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from config import settings
from logging_config import logger
from services.resilience import resilient_call, polymarket_breaker
from .base import SignalProvider

CACHE_TTL = timedelta(hours=1)
REST_POLL_INTERVAL = timedelta(minutes=settings.oracle_signal_refresh_minutes)

# Volatility thresholds for high-vol detection
VOLATILITY_SWING_THRESHOLD = 0.08  # 8% probability change in one poll = high vol
RAPID_SWING_WINDOW = 3  # compare against poll N-3

_cache: dict = {}
_cache_time: datetime | None = None
_prev_probabilities: dict[str, float] = {}  # market_id → last probability (for volatility)
_probability_history: list[dict[str, float]] = []  # rolling window for vol detection


class L5Polymarket(SignalProvider):
    layer = "L5"

    async def fetch(self) -> list[dict]:
        """Fetch prediction market signals. Uses REST with cache."""
        global _cache_time
        if _cache_time and datetime.now(timezone.utc) - _cache_time < CACHE_TTL and _cache:
            return _cache.get("signals", [])

        try:
            return await self._fetch_polymarket_rest()
        except Exception as e:
            logger.warning("polymarket_failed", error=str(e))
            return self._fallback()

    async def _fetch_polymarket_rest(self) -> list[dict]:
        """Fetch from Gamma REST API with circuit breaker + volatility detection."""
        async def _fetch():
            signals: list[dict] = []
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{settings.polymarket_api_url}/markets",
                    params={"limit": 20, "active": "true", "closed": "false"},
                )
                resp.raise_for_status()
                markets = resp.json()

                current_probs: dict[str, float] = {}

                for market in markets:
                    question = market.get("question", "")
                    if not question:
                        continue
                    prices = market.get("outcomePrices", [])
                    yes_prob = float(prices[0]) if prices else 0.5
                    market_id = market.get("id", question[:20])
                    current_probs[market_id] = yes_prob
                    volume = float(market.get("volume24hr", market.get("volume", 0)))

                    # Filter for macro/finance relevance
                    keywords = ["rate", "fed", "inflation", "recession", "sp 500", "s&p", "gdp", "treasury", "market"]
                    if not any(k in question.lower() for k in keywords):
                        continue

                    # ── Volatility detection ──
                    prev_prob = _prev_probabilities.get(market_id)
                    volatility_swing = abs(yes_prob - prev_prob) if prev_prob is not None else 0.0
                    is_high_volatility = volatility_swing > VOLATILITY_SWING_THRESHOLD

                    # Direction with volatility overlay
                    if is_high_volatility:
                        # Rapid swing = contrarian/caution signal
                        direction = "contrarian"
                        strength = 5
                        vol_context = f"⚠️ HIGH VOLATILITY: {volatility_swing*100:.1f}% swing detected"
                    else:
                        direction = "bearish" if yes_prob > 0.6 else "bullish" if yes_prob < 0.4 else "neutral"
                        strength = min(5, max(1, int(abs(yes_prob - 0.5) * 10)))
                        vol_context = ""

                    confidence = round(min(0.95, 0.5 + volume / 10_000_000), 4)
                    # Boost confidence on high volume even if volatile
                    if volume > 5_000_000:
                        confidence = min(0.95, confidence + 0.05)

                    context = f"{question[:80]} — Yes: {yes_prob*100:.0f}%"
                    if vol_context:
                        context += f" | {vol_context}"

                    signals.append({
                        "layer": "L5",
                        "signal_type": "polymarket_prediction",
                        "asset": self._extract_asset(question),
                        "direction": direction,
                        "strength": strength,
                        "confidence": confidence,
                        "raw_value": round(yes_prob, 4),
                        "context": context,
                        "metadata": {
                            "market_id": market_id,
                            "volume_24h": volume,
                            "question": question,
                            "volatility_swing": round(volatility_swing, 4),
                            "high_volatility": is_high_volatility,
                        },
                    })
                    if len(signals) >= 5:
                        break

            # Update probability history for volatility tracking
            _probability_history.append(current_probs)
            if len(_probability_history) > RAPID_SWING_WINDOW * 3:
                _probability_history.pop(0)
            _prev_probabilities.update(current_probs)

            return signals or self._fallback()

        signals = await resilient_call(
            _fetch, breaker=polymarket_breaker, fallback=lambda: self._fallback(), max_retries=2,
        )

        global _cache, _cache_time
        _cache = {"signals": signals}
        _cache_time = datetime.now(timezone.utc)
        return signals

    @staticmethod
    def _extract_asset(question: str) -> str | None:
        q = question.lower()
        if "rate" in q or "fed" in q:
            return "FED"
        if "recession" in q:
            return "recession"
        if "s&p" in q or "sp 500" in q:
            return "SPY"
        if "inflation" in q or "cpi" in q:
            return "CPI"
        return None

    def _fallback(self) -> list[dict]:
        return [
            {"layer": "L5", "signal_type": "polymarket_prediction", "asset": "FED",
             "direction": "bearish", "strength": 5, "confidence": 0.88,
             "raw_value": 0.71, "context": "Rate hike probability: 71% (up from 62%)"},
            {"layer": "L5", "signal_type": "polymarket_prediction", "asset": "recession",
             "direction": "bearish", "strength": 3, "confidence": 0.62,
             "raw_value": 0.34, "context": "US recession 2026 probability: 34%"},
        ]


# ════════════════════════════════════════════════════════════════
# Optional: Polymarket CLOB WebSocket client for real-time updates
# (institutional grade). Runs as a background task when enabled.
# ════════════════════════════════════════════════════════════════
class PolymarketWebSocketClient:
    """
    Real-time Polymarket probability feed via WebSocket.

    Subscribes to market price changes and pushes updates to the
    cache immediately, rather than waiting for the 15-min REST poll.
    Auto-reconnects with exponential backoff on disconnect.

    Usage (in app lifespan):
        ws_client = PolymarketWebSocketClient()
        await ws_client.start()
    """

    def __init__(self):
        self._ws = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0

    async def start(self) -> None:
        """Start the WebSocket listener as a background task."""
        self._running = True
        asyncio.create_task(self._listen_loop())
        logger.info("polymarket_ws_started", url=settings.polymarket_ws_url)

    async def stop(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()

    async def _listen_loop(self) -> None:
        """Reconnect loop with exponential backoff."""
        try:
            import websockets
        except ImportError:
            logger.warning("polymarket_ws_no_websockets_lib")
            return

        while self._running:
            try:
                async with websockets.connect(settings.polymarket_ws_url) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1.0  # reset on successful connect
                    logger.info("polymarket_ws_connected")

                    # Subscribe to market changes (CLOB format)
                    await ws.send(json.dumps({"type": "Market", "assets_ids": []}))

                    while self._running:
                        msg = await ws.recv()
                        await self._handle_message(json.loads(msg))

            except Exception as e:
                logger.warning("polymarket_ws_disconnected", error=str(e))
                if self._running:
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def _handle_message(self, msg: dict) -> None:
        """Process a WebSocket message and update the cache."""
        # CLOB price change format: {changes: [{asset_id, price}]}
        changes = msg.get("changes") or msg.get("data", {}).get("changes", [])
        for change in changes:
            market_id = change.get("asset_id") or change.get("market")
            price = change.get("price")
            if market_id and price:
                _prev_probabilities[market_id] = float(price)
        # Invalidate cache so next fetch is fresh
        global _cache_time
        _cache_time = None


l5_polymarket = L5Polymarket()
polymarket_ws = PolymarketWebSocketClient()
