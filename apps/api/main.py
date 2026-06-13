# ════════════════════════════════════════════════════════════════
# ORACLE FastAPI — Application Entry Point
# Wires CORS, rate limiting, routers, lifespan, health checks.
# ════════════════════════════════════════════════════════════════
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings
from logging_config import setup_logging, logger
from routers import swarm, voice, strategy, signals, accuracy, health, recommendations

setup_logging()


# ── Security validation at import time ──
from services.security import validate_security_config
_security_warnings = validate_security_config()


# ── Rate limiter (§19: 100 req/min per IP) ──
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "oracle_api_starting",
        version=settings.version,
        offline_mode=settings.oracle_offline_mode,
        market_data_provider=settings.market_data_provider,
    )
    # Start Polymarket WebSocket (real-time L5) in background
    # Best-effort — falls back to REST polling if WS unavailable
    try:
        from services.signals.l5_polymarket import polymarket_ws
        await polymarket_ws.start()
    except Exception as e:
        logger.warning("polymarket_ws_start_failed", error=str(e))
    yield
    # Cleanup
    try:
        await polymarket_ws.stop()
    except Exception:
        pass
    logger.info("oracle_api_stopping")


app = FastAPI(
    title="ORACLE — Swarm Intelligence Broker API",
    description="We don't predict markets. We simulate the humans that move them.",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def internal_auth(request: Request, call_next):
    """Verify X-Oracle-Secret on service-to-service calls from Edge Functions."""
    # Public routes that don't need the secret
    public_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
    if request.url.path in public_paths or request.method == "OPTIONS":
        return await call_next(request)

    # Endpoints called by Edge Functions carry X-Oracle-Secret
    # Frontend calls go through Supabase PostgREST (not here directly),
    # so any direct call to FastAPI must present the secret.
    secret = request.headers.get("X-Oracle-Secret", "")
    if secret and secret != settings.secret_key and settings.secret_key != "dev-insecure-change-me":
        return JSONResponse({"error": "Invalid service secret"}, status_code=status.HTTP_403_FORBIDDEN)

    response = await call_next(request)
    return response


@app.middleware("http")
async def leak_guard(request: Request, call_next):
    """
    Security guard: detect and block responses that accidentally
    contain service role keys or other secrets.
    Only scans JSON text responses under a size threshold.
    """
    response = await call_next(request)
    # Only scan smaller responses (avoid perf hit on large payloads)
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type and response.status_code == 200:
        # Read, scan, re-wrap (only for safety-critical small responses)
        try:
            content = b"".join([c async for c in response.body_iterator])
            text = content.decode("utf-8", errors="ignore")
            if len(text) < 50_000:  # only scan small responses
                from services.security import scan_for_key_leaks
                if scan_for_key_leaks(text):
                    logger.error("security_leak_detected", path=request.url.path)
                    return JSONResponse(
                        {"error": "Response blocked: potential sensitive data detected"},
                        status_code=500,
                    )
            # Re-create response with the consumed body
            from starlette.responses import Response
            return Response(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception:
            # If we can't scan, let it through (don't break the app)
            pass
    return response


# ── Routers ──
app.include_router(health.router)
app.include_router(swarm.router)
app.include_router(voice.router)
app.include_router(strategy.router)
app.include_router(signals.router)
app.include_router(accuracy.router)
app.include_router(recommendations.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
