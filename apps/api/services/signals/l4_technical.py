# ════════════════════════════════════════════════════════════════
# L4 — Technical Indicators (§13)
# Computed from L1 OHLCV data. RSI, MACD, Bollinger, EMA, ATR.
# ════════════════════════════════════════════════════════════════
import asyncio
import numpy as np
import pandas as pd
import yfinance as yf

from logging_config import logger
from .base import SignalProvider

TRACKED = ["NVDA", "AAPL", "MSFT", "SPY", "QQQ", "BTC-USD"]


class L4Technical(SignalProvider):
    layer = "L4"

    async def fetch(self) -> list[dict]:
        def _compute():
            signals: list[dict] = []
            for symbol in TRACKED:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="3mo")
                    if hist.empty or len(hist) < 50:
                        continue
                    close = hist["Close"]

                    rsi = self._rsi(close).iloc[-1]
                    macd_line, macd_signal = self._macd(close)
                    macd_val = macd_line.iloc[-1] - macd_signal.iloc[-1]
                    upper, lower = self._bollinger(close)
                    ema20 = close.ewm(span=20).mean().iloc[-1]
                    ema50 = close.ewm(span=50).mean().iloc[-1]
                    price = close.iloc[-1]

                    # Generate signal
                    parts = []
                    direction = "neutral"
                    strength = 2

                    if rsi < 30:
                        direction, strength = "bullish", 4
                        parts.append(f"RSI oversold ({rsi:.0f})")
                    elif rsi > 70:
                        direction, strength = "bearish", 4
                        parts.append(f"RSI overbought ({rsi:.0f})")
                    if macd_val > 0:
                        parts.append("MACD bullish")
                        if direction == "neutral":
                            direction = "bullish"
                    elif macd_val < 0:
                        parts.append("MACD bearish")
                        if direction == "neutral":
                            direction = "bearish"
                    if price > ema50:
                        parts.append("Above EMA50 (uptrend)")
                    else:
                        parts.append("Below EMA50 (downtrend)")

                    signals.append({
                        "layer": "L4",
                        "signal_type": "technical_indicator",
                        "asset": symbol,
                        "direction": direction,
                        "strength": strength,
                        "confidence": 0.74,
                        "raw_value": round(price, 2),
                        "context": f"{symbol}: {', '.join(parts)}",
                        "metadata": {
                            "rsi": round(float(rsi), 2),
                            "macd": round(float(macd_val), 4),
                            "ema20": round(float(ema20), 2),
                            "ema50": round(float(ema50), 2),
                        },
                    })
                except Exception as e:
                    logger.debug("technical_fetch_failed", symbol=symbol, error=str(e))
                    continue
            return signals

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _compute)

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _macd(close: pd.Series, fast=12, slow=26, signal_p=9):
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_p).mean()
        return macd, signal

    @staticmethod
    def _bollinger(close: pd.Series, period=20, std=2):
        sma = close.rolling(period).mean()
        rolling_std = close.rolling(period).std()
        return sma + std * rolling_std, sma - std * rolling_std


l4_technical = L4Technical()
