# ════════════════════════════════════════════════════════════════
# ORACLE — Market Data Provider Abstraction (§13, L1)
#
# Provider chain: Polygon.io (enterprise) → Alpha Vantage → yfinance (free)
# All providers implement the same interface. The active provider is
# chosen by config (market_data_provider: auto|polygon|alphavantage|yfinance).
#
# Addresses expert feedback: "Replace yfinance with an institutional
# data provider" — Polygon.io is the enterprise-grade swap, with
# yfinance kept as a free fallback so the API contracts never break.
# ════════════════════════════════════════════════════════════════
import time
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
import pandas as pd
import yfinance as yf

from config import settings
from logging_config import logger
from services.resilience import resilient_call, market_data_breaker


@dataclass
class OHLCV:
    """Normalized OHLCV data frame across providers."""
    df: pd.DataFrame  # columns: Open, High, Low, Close, Volume (index: Date)


class MarketDataProvider(ABC):
    """Interface for all market data providers."""

    name: str = "base"

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Fetch latest quotes for a list of symbols."""
        ...

    @abstractmethod
    async def get_history(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        """Fetch historical OHLCV. Returns DataFrame or None on failure."""
        ...

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider has credentials configured."""
        ...


# ════════════════════════════════════════════════════════════════
# Polygon.io — Enterprise grade (paid, reliable, no rate limits)
# ════════════════════════════════════════════════════════════════
class PolygonProvider(MarketDataProvider):
    name = "polygon"

    def __init__(self):
        self.base_url = settings.polygon_base_url
        self._cache: dict[str, tuple[float, dict]] = {}  # symbol → (timestamp, quote)

    @property
    def available(self) -> bool:
        return bool(settings.polygon_api_key)

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        quotes = []
        headers = {"Authorization": f"Bearer {settings.polygon_api_key}"}

        async def _fetch():
            results = []
            async with httpx.AsyncClient(timeout=10) as client:
                for symbol in symbols:
                    # Check cache
                    cached = self._cache.get(symbol)
                    if cached and time.time() - cached[0] < settings.market_data_cache_ttl:
                        results.append(cached[1])
                        continue
                    resp = await client.get(
                        f"{self.base_url}/v2/aggs/ticker/{self._fmt_symbol(symbol)}/prev",
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json().get("results", [{}])
                    if data:
                        q = data[0]
                        quote = {
                            "layer": "L1", "signal_type": "price_update", "asset": symbol,
                            "direction": "neutral",  # Polygon prev doesn't give change %
                            "strength": 2, "confidence": 0.98,
                            "raw_value": q.get("c", 0),
                            "context": f"{symbol} close: {q.get('c', 0)}",
                            "provider": "polygon",
                        }
                        self._cache[symbol] = (time.time(), quote)
                        results.append(quote)
            return results

        return await resilient_call(
            _fetch, breaker=market_data_breaker, fallback=lambda: [], max_retries=2,
        )

    async def get_history(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        headers = {"Authorization": f"Bearer {settings.polygon_api_key}"}

        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.base_url}/v2/aggs/ticker/{self._fmt_symbol(symbol)}/range/1/day/{start}/{end}",
                    headers=headers,
                    params={"adjusted": "true", "sort": "asc", "limit": 50000},
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
                if not results:
                    return None
                df = pd.DataFrame(results)
                df["Date"] = pd.to_datetime(df["t"], unit="ms")
                df = df.set_index("Date")
                df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
                return df[["Open", "High", "Low", "Close", "Volume"]]

        try:
            return await resilient_call(_fetch, breaker=market_data_breaker, fallback=lambda: None)
        except Exception:
            return None

    @staticmethod
    def _fmt_symbol(symbol: str) -> str:
        """Convert common symbols to Polygon format."""
        if symbol == "BTC-USD":
            return "X:BTCUSD"
        if symbol == "ETH-USD":
            return "X:ETHUSD"
        return symbol


# ════════════════════════════════════════════════════════════════
# Alpha Vantage — mid-tier (free key, 25 req/day)
# ════════════════════════════════════════════════════════════════
class AlphaVantageProvider(MarketDataProvider):
    name = "alphavantage"

    @property
    def available(self) -> bool:
        return bool(settings.alpha_vantage_api_key)

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        async def _fetch():
            quotes = []
            async with httpx.AsyncClient(timeout=10) as client:
                for symbol in symbols[:10]:  # rate limit
                    resp = await client.get(
                        "https://www.alphavantage.co/query",
                        params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": settings.alpha_vantage_api_key},
                    )
                    resp.raise_for_status()
                    data = resp.json().get("Global Quote", {})
                    if not data:
                        continue
                    price = float(data.get("05. price", 0))
                    change_pct = float(data.get("10. change percent", "0%").strip("%"))
                    quotes.append({
                        "layer": "L1", "signal_type": "price_update", "asset": symbol,
                        "direction": "bullish" if change_pct > 0.5 else "bearish" if change_pct < -0.5 else "neutral",
                        "strength": min(5, max(1, int(abs(change_pct)))),
                        "confidence": 0.92, "raw_value": price,
                        "context": f"{symbol} {'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                        "provider": "alphavantage",
                    })
            return quotes

        return await resilient_call(_fetch, breaker=market_data_breaker, fallback=lambda: [], max_retries=1)

    async def get_history(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        # Alpha Vantage daily history — limited but available
        async def _fetch():
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://www.alphavantage.co/query",
                    params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "full", "apikey": settings.alpha_vantage_api_key},
                )
                resp.raise_for_status()
                ts = resp.json().get("Time Series (Daily)", {})
                if not ts:
                    return None
                rows = []
                for date, vals in ts.items():
                    rows.append({
                        "Date": date,
                        "Open": float(vals["1. open"]), "High": float(vals["2. high"]),
                        "Low": float(vals["3. low"]), "Close": float(vals["4. close"]),
                        "Volume": int(vals["5. volume"]),
                    })
                df = pd.DataFrame(rows)
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.set_index("Date").sort_index()
                return df.loc[start:end]

        try:
            return await resilient_call(_fetch, breaker=market_data_breaker, fallback=lambda: None)
        except Exception:
            return None


# ════════════════════════════════════════════════════════════════
# yfinance — free fallback (rate-limited, no key, unreliable but always available)
# ════════════════════════════════════════════════════════════════
class YFinanceProvider(MarketDataProvider):
    name = "yfinance"

    @property
    def available(self) -> bool:
        return True  # always available (no key needed)

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        def _download():
            quotes = []
            try:
                tickers = yf.Tickers(" ".join(symbols))
                for symbol in symbols:
                    try:
                        hist = tickers.tickers[symbol].history(period="2d")
                        if hist.empty:
                            continue
                        price = float(hist["Close"].iloc[-1])
                        prev = float(hist["Close"].iloc[0]) if len(hist) > 1 else price
                        change_pct = ((price - prev) / prev * 100) if prev else 0
                        quotes.append({
                            "layer": "L1", "signal_type": "price_update", "asset": symbol,
                            "direction": "bullish" if change_pct > 0.5 else "bearish" if change_pct < -0.5 else "neutral",
                            "strength": min(5, max(1, int(abs(change_pct)))),
                            "confidence": 0.85, "raw_value": round(price, 4),
                            "context": f"{symbol} {'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                            "provider": "yfinance",
                        })
                    except Exception:
                        continue
            except Exception as e:
                logger.error("yfinance_quote_failed", error=str(e))
            return quotes

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)

    async def get_history(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        def _download():
            try:
                hist = yf.Ticker(symbol).history(start=start, end=end)
                if hist.empty:
                    return None
                return hist[["Open", "High", "Low", "Close", "Volume"]]
            except Exception as e:
                logger.warning("yfinance_history_failed", symbol=symbol, error=str(e))
                return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)


# ════════════════════════════════════════════════════════════════
# Provider Manager — selects active provider + automatic failover
# ════════════════════════════════════════════════════════════════
class MarketDataManager:
    """
    Manages the provider chain and automatic failover.

    Order (configurable via market_data_provider):
      auto → polygon > alphavantage > yfinance
      polygon → polygon only
      etc.

    If the active provider fails (circuit open), automatically falls
    through to the next available provider in the chain.
    """

    def __init__(self):
        self._polygon = PolygonProvider()
        self._alphavantage = AlphaVantageProvider()
        self._yfinance = YFinanceProvider()
        self._chain: list[MarketDataProvider] = []
        self._configure_chain()

    def _configure_chain(self) -> None:
        pref = settings.market_data_provider.lower()
        all_providers = {
            "polygon": self._polygon,
            "alphavantage": self._alphavantage,
            "yfinance": self._yfinance,
        }
        if pref == "auto":
            self._chain = [p for p in all_providers.values() if p.available]
        elif pref in all_providers:
            self._chain = [all_providers[pref]] + [p for k, p in all_providers.items() if k != pref and p.available]
        else:
            self._chain = [p for p in all_providers.values() if p.available]
        logger.info(
            "market_data_chain_configured",
            chain=[p.name for p in self._chain],
            preference=pref,
        )

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Try each provider in chain order until one succeeds."""
        for provider in self._chain:
            if not provider.available:
                continue
            try:
                quotes = await provider.get_quotes(symbols)
                if quotes:
                    return quotes
            except Exception as e:
                logger.warning("provider_failed", provider=provider.name, error=str(e))
                continue
        return []

    async def get_history(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        """Try each provider in chain order for historical data."""
        for provider in self._chain:
            if not provider.available:
                continue
            try:
                df = await provider.get_history(symbol, start, end)
                if df is not None and not df.empty:
                    logger.debug("history_fetched", provider=provider.name, symbol=symbol, rows=len(df))
                    return df
            except Exception as e:
                logger.warning("history_provider_failed", provider=provider.name, error=str(e))
                continue
        logger.error("all_providers_failed_history", symbol=symbol)
        return None

    @property
    def active_provider_name(self) -> str:
        return self._chain[0].name if self._chain else "none"


# Singleton
market_data_manager = MarketDataManager()
