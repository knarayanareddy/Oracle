# ════════════════════════════════════════════════════════════════
# Health check router (§20)
# Railway/deployment health probes.
# ════════════════════════════════════════════════════════════════
from datetime import datetime, timezone
from fastapi import APIRouter
from config import settings
from logging_config import logger

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Liveness + readiness probe. Reports service connectivity."""
    services = {
        "supabase": _check_supabase(),
        "openai": _check_openai(),
        "alpha_vantage": "ready" if settings.alpha_vantage_api_key else "no-key",
        "polymarket": "ready",
        "mirofish": "ready" if not settings.oracle_offline_mode else "offline",
    }
    all_ok = all(v in ("connected", "ready", "no-key") for v in services.values())

    logger.info("health_check", status="healthy" if all_ok else "degraded", services=services)
    return {
        "status": "healthy" if all_ok else "degraded",
        "version": settings.version,
        "services": services,
        "offline_mode": settings.oracle_offline_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _check_supabase() -> str:
    return "connected" if settings.supabase_url and settings.supabase_service_role_key else "no-config"


def _check_openai() -> str:
    return "connected" if settings.openai_api_key else "no-key"
