# ════════════════════════════════════════════════════════════════
# L2 — Macro Signals (§13)
# Source: FRED API (Federal Reserve Economic Data)
# ════════════════════════════════════════════════════════════════
import asyncio
import httpx

from config import settings
from logging_config import logger
from .base import SignalProvider

MACRO_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "10y_treasury": "DGS10",
    "2y_treasury": "DGS2",
    "yield_curve_spread": "T10Y2Y",
    "cpi_yoy": "CPIAUCSL",
    "unemployment": "UNRATE",
}


class L2MacroSignals(SignalProvider):
    layer = "L2"

    async def fetch(self) -> list[dict]:
        if not settings.fred_api_key:
            logger.warning("fred_no_api_key", layer="L2")
            return self._fallback()
        try:
            return await self._fetch_fred()
        except Exception as e:
            logger.warning("fred_failed", error=str(e))
            return self._fallback()

    async def _fetch_fred(self) -> list[dict]:
        signals: list[dict] = []
        async with httpx.AsyncClient(timeout=10) as client:
            for label, series_id in MACRO_SERIES.items():
                resp = await client.get(
                    f"https://api.stlouisfed.org/fred/series/observations",
                    params={
                        "series_id": series_id,
                        "api_key": settings.fred_api_key,
                        "file_type": "json",
                        "limit": 2,
                        "sort_order": "desc",
                    },
                )
                obs = resp.json().get("observations", [])
                if len(obs) < 2:
                    continue
                current = float(obs[0]["value"])
                prev = float(obs[1]["value"])
                change_pct = ((current - prev) / prev) if prev else 0

                direction = "neutral"
                if "yield_curve" in label:
                    direction = "contrarian" if current < 0 else "neutral"
                elif current > prev:
                    direction = "bearish" if "rate" in label or "cpi" in label else "neutral"

                signals.append({
                    "layer": "L2",
                    "signal_type": "macro_update",
                    "asset": label,
                    "direction": direction,
                    "strength": min(5, max(1, int(abs(change_pct * 10)))),
                    "confidence": 0.85,
                    "raw_value": current,
                    "context": f"{label}: {current} (prev: {prev})",
                })
        return signals

    def _fallback(self) -> list[dict]:
        return [
            {"layer": "L2", "signal_type": "macro_update", "asset": "fed_funds_rate",
             "direction": "neutral", "strength": 3, "confidence": 0.8,
             "raw_value": 5.50, "context": "Fed Funds Rate: 5.50% (held)"},
            {"layer": "L2", "signal_type": "macro_update", "asset": "10y_treasury",
             "direction": "bearish", "strength": 3, "confidence": 0.81,
             "raw_value": 4.32, "context": "10Y yield rising — pressure on growth"},
            {"layer": "L2", "signal_type": "macro_update", "asset": "yield_curve_spread",
             "direction": "contrarian", "strength": 3, "confidence": 0.76,
             "raw_value": -0.18, "context": "Yield curve inverted — recession signal"},
        ]


l2_macro_signals = L2MacroSignals()
