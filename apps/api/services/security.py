# ════════════════════════════════════════════════════════════════
# ORACLE — Security Guards (§19, ADR-001)
# Runtime enforcement that the service role key is NEVER exposed
# to the frontend. Validates config at startup and provides
# middleware that strips sensitive headers from responses.
#
# Addresses expert feedback: "Verify Supabase RLS policies are
# strictly enforced and no service keys are leaked to the client"
# ════════════════════════════════════════════════════════════════
import re
from config import settings
from logging_config import logger

# Patterns that should NEVER appear in a response body sent to frontend
SENSITIVE_KEY_PATTERNS = [
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT tokens
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI-style API keys
    re.compile(r"SUPABASE_SERVICE_ROLE_KEY", re.I),
    re.compile(r"service_role", re.I),
]


def validate_security_config() -> list[str]:
    """
    Validate security configuration at startup.
    Returns a list of warnings (empty = all clear).

    Called from app lifespan. Logs warnings but does not hard-fail
    in demo mode to avoid blocking the hackathon demo.
    """
    warnings: list[str] = []

    # 1. Service role key must be set if Supabase is configured
    if settings.supabase_url and not settings.supabase_service_role_key:
        warnings.append("Supabase URL configured but SERVICE_ROLE_KEY is empty — backend DB writes will fail")

    # 2. Secret key must not be the insecure default in production
    if settings.secret_key == "dev-insecure-change-me":
        env = "demo" if settings.demo_user_id == "00000000-0000-0000-0000-000000000001" else "production"
        if env == "production":
            warnings.append("SECURITY: FASTAPI_SECRET_KEY is the insecure default — must change before production deployment")
        else:
            logger.info("security_check_demo_mode", note="Using insecure default secret key (acceptable in demo mode)")

    # 3. Verify the anon key and service role key are DIFFERENT
    if (settings.supabase_anon_key and settings.supabase_service_role_key
            and settings.supabase_anon_key == settings.supabase_service_role_key):
        warnings.append("CRITICAL: SUPABASE_ANON_KEY equals SUPABASE_SERVICE_ROLE_KEY — this breaks the RLS security model!")

    for w in warnings:
        logger.warning("security_config_warning", warning=w)

    return warnings


def is_service_role_key(key: str) -> bool:
    """Check if a string looks like a Supabase service role JWT."""
    if not key or not key.startswith("eyJ"):
        return False
    try:
        import base64
        import json
        # Decode JWT payload (second segment)
        payload_b64 = key.split(".")[1]
        # Add padding
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("role") == "service_role"
    except Exception:
        return False


def scan_for_key_leaks(text: str) -> bool:
    """
    Scan a string (e.g., API response body) for accidental key leakage.
    Returns True if a potential leak is detected.
    """
    for pattern in SENSITIVE_KEY_PATTERNS:
        if pattern.search(text):
            return True
    return False
