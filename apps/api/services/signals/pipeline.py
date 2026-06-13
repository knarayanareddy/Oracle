# ════════════════════════════════════════════════════════════════
# Signal Pipeline Orchestrator (§13)
# Aggregates all L1-L5 providers, runs them concurrently,
# and pushes results to Supabase via the signal-ingest Edge Function.
# ════════════════════════════════════════════════════════════════
import asyncio
import httpx

from config import settings
from logging_config import logger
from .l1_market_data import l1_market_data
from .l2_macro import l2_macro_signals
from .l3_news import l3_news_sentiment
from .l4_technical import l4_technical
from .l5_polymarket import l5_polymarket

ALL_PROVIDERS = [l1_market_data, l2_macro_signals, l3_news_sentiment, l4_technical, l5_polymarket]


class SignalPipeline:
    """Orchestrates concurrent L1-L5 signal collection."""

    async def refresh_all(self) -> dict:
        """Run all providers concurrently and return aggregated signals."""
        logger.info("signal_refresh_start")
        results = await asyncio.gather(
            *[p.fetch() for p in ALL_PROVIDERS],
            return_exceptions=True,
        )

        all_signals: list[dict] = []
        errors: list[str] = []
        for provider, result in zip(ALL_PROVIDERS, results):
            if isinstance(result, Exception):
                errors.append(f"{provider.layer}: {result}")
                logger.warning("signal_provider_error", layer=provider.layer, error=str(result))
            else:
                all_signals.extend(result)

        # Push to Supabase via Edge Function (best-effort)
        await self._ingest(all_signals)

        logger.info(
            "signal_refresh_complete",
            total=len(all_signals),
            errors=len(errors),
            layers={p.layer: len(r) if not isinstance(r, Exception) else 0 for p, r in zip(ALL_PROVIDERS, results)},
        )
        return {
            "signals_collected": len(all_signals),
            "errors": errors,
            "by_layer": {
                p.layer: len(r) if not isinstance(r, Exception) else 0
                for p, r in zip(ALL_PROVIDERS, results)
            },
        }

    async def get_latest(self, limit: int = 50) -> list[dict]:
        """Return latest signals from providers (for API response)."""
        results = await asyncio.gather(
            *[p.fetch() for p in ALL_PROVIDERS],
            return_exceptions=True,
        )
        signals = []
        for result in results:
            if isinstance(result, list):
                signals.extend(result)
        return signals[:limit]

    async def _ingest(self, signals: list[dict]) -> None:
        """Push signals to Supabase signal_events via Edge Function."""
        if not signals or not settings.supabase_url:
            return
        supabase_fn_url = f"{settings.supabase_url}/functions/v1/signal-ingest"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    supabase_fn_url,
                    json=signals,
                    headers={
                        "Authorization": f"Bearer {settings.supabase_service_role_key}",
                        "Content-Type": "application/json",
                    },
                )
        except Exception as e:
            logger.warning("signal_ingest_push_failed", error=str(e))


# Singleton
signal_pipeline = SignalPipeline()
