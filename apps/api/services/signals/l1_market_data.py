# ════════════════════════════════════════════════════════════════
# L1 — Market Data (§13)
# Now delegates to MarketDataManager (polygon → alphavantage → yfinance)
# with automatic failover. Provider chain configurable via env.
# ════════════════════════════════════════════════════════════════
from logging_config import logger
from services.market_data_provider import market_data_manager
from .base import SignalProvider

SUPPORTED_ASSETS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM",
    "SPY", "QQQ", "BTC-USD", "ETH-USD", "TLT", "IEF", "SHY", "VIX",
]


class L1MarketData(SignalProvider):
    layer = "L1"

    async def fetch(self) -> list[dict]:
        """Fetch latest prices via the provider chain with automatic failover."""
        signals = await market_data_manager.get_quotes(SUPPORTED_ASSETS[:12])
        if signals:
            logger.info("l1_fetched", provider=signals[0].get("provider", "?"), count=len(signals))
        else:
            logger.warning("l1_all_providers_failed")
        return signals


# Singleton — imported by pipeline.py
l1_market_data = L1MarketData()
