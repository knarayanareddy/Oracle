# ════════════════════════════════════════════════════════════════
# ORACLE FastAPI — Centralized Configuration (Addendum D)
# Loads from environment variables. Never hardcode secrets.
# ════════════════════════════════════════════════════════════════
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──
    app_name: str = "ORACLE API"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    secret_key: str = "dev-insecure-change-me"

    # ── Supabase ──
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ── LLM ──
    openai_api_key: str = ""
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ── Market Data ──
    alpha_vantage_api_key: str = ""
    fred_api_key: str = ""
    polygon_api_key: str = ""  # Enterprise feed — institutional grade
    polygon_base_url: str = "https://api.polygon.io"
    market_data_provider: str = "auto"  # auto → polygon > alphavantage > yfinance
    market_data_cache_ttl: int = 60  # seconds

    # ── News & Prediction Markets ──
    news_api_key: str = ""
    polymarket_api_url: str = "https://gamma-api.polymarket.com"
    polymarket_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws"

    # ── Voice ──
    elevenlabs_api_key: str = ""

    # ── CORS ──
    cors_origins: str = "http://localhost:5173"

    # ── Rate Limiting ──
    rate_limit_per_minute: int = 100

    # ── Resilience ──
    llm_circuit_failure_threshold: int = 5
    llm_circuit_cooldown_seconds: float = 30.0
    llm_max_retries: int = 2

    # ── Feature Flags ──
    oracle_offline_mode: bool = False
    oracle_max_agents: int = 1000
    oracle_max_rounds: int = 40
    oracle_signal_refresh_minutes: int = 15

    # ── Demo ──
    demo_user_id: str = "00000000-0000-0000-0000-000000000001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
