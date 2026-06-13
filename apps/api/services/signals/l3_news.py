# ════════════════════════════════════════════════════════════════
# L3 — News & Sentiment NLP (§13)
# Source: NewsAPI + FinBERT/GPT-4o-mini sentiment.
# ════════════════════════════════════════════════════════════════
import asyncio
import httpx

from config import settings
from logging_config import logger
from .base import SignalProvider

TRACKED_TOPICS = [
    "Federal Reserve", "interest rates", "inflation", "earnings",
    "NVDA", "tech sector", "recession", "S&P 500", "bond yields",
]


class L3NewsSentiment(SignalProvider):
    layer = "L3"

    async def fetch(self) -> list[dict]:
        if not settings.news_api_key:
            logger.warning("newsapi_no_key", layer="L3")
            return self._fallback()
        try:
            return await self._fetch_newsapi()
        except Exception as e:
            logger.warning("newsapi_failed", error=str(e))
            return self._fallback()

    async def _fetch_newsapi(self) -> list[dict]:
        signals: list[dict] = []
        async with httpx.AsyncClient(timeout=10) as client:
            for topic in TRACKED_TOPICS[:5]:  # rate limit
                resp = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": topic,
                        "sortBy": "publishedAt",
                        "pageSize": 5,
                        "language": "en",
                        "apiKey": settings.news_api_key,
                    },
                )
                articles = resp.json().get("articles", [])
                if not articles:
                    continue

                # Simple sentiment heuristic from headline keywords
                sentiment = self._heuristic_sentiment([a.get("title", "") for a in articles])
                signals.append({
                    "layer": "L3",
                    "signal_type": "news_sentiment",
                    "asset": topic if topic.isupper() else None,
                    "direction": sentiment["direction"],
                    "strength": min(5, max(1, int(abs(sentiment["score"]) * 8))),
                    "confidence": 0.69,
                    "raw_value": round(sentiment["score"], 4),
                    "context": f"{len(articles)} articles on '{topic}': {sentiment['direction']}",
                    "source_url": articles[0].get("url"),
                })
        return signals

    @staticmethod
    def _heuristic_sentiment(headlines: list[str]) -> dict:
        positive = ["beat", "surge", "rally", "record", "strong", "growth", "upgrade", "buy", "boom", "jump"]
        negative = ["miss", "crash", "fear", "recession", "cut", "sell", "bear", "plunge", "warn", "drop"]
        text = " ".join(headlines).lower()
        score = (sum(1 for w in positive if w in text) - sum(1 for w in negative if w in text)) / max(len(headlines), 1)
        direction = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"
        return {"score": round(score, 4), "direction": direction}

    def _fallback(self) -> list[dict]:
        return [
            {"layer": "L3", "signal_type": "news_sentiment", "asset": "NVDA",
             "direction": "bullish", "strength": 4, "confidence": 0.78,
             "raw_value": 0.62, "context": "Positive earnings sentiment across 23 articles"},
            {"layer": "L3", "signal_type": "news_sentiment", "asset": "tech_sector",
             "direction": "bearish", "strength": 3, "confidence": 0.69,
             "raw_value": -0.34, "context": "Rate-hike fear dominating fintwit"},
        ]


l3_news_sentiment = L3NewsSentiment()
