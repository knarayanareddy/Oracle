# 🔐 ORACLE — Security Model

> **Navigation:** [← Back to README](../README.md) | [Architecture](ARCHITECTURE.md)

Comprehensive security documentation: RLS model, key isolation, circuit breakers,
GDPR/AVG compliance, and the threat model.

---

## Table of Contents

1. [Security Principles](#1-security-principles)
2. [Key Isolation Model](#2-key-isolation-model)
3. [Row Level Security (RLS)](#3-row-level-security-rls)
4. [Runtime Guards](#4-runtime-guards)
5. [Resilience (Circuit Breakers)](#5-resilience-circuit-breakers)
6. [GDPR / AVG Compliance](#6-gdpr--avg-compliance)
7. [Threat Model](#7-threat-model)
8. [Security CI Pipeline](#8-security-ci-pipeline)

---

## 1. Security Principles

```
DESIGN PRINCIPLE                     IMPLEMENTATION
────────────────────────────────────────────────────────────────
RLS on every table                  PostgreSQL enforces at DB layer
Service role key isolation          Backend + Edge Functions ONLY
No PII in logs                      UUIDs only, structured JSON
Signed URLs for storage             No public buckets
Secrets in env vars                 Never in code or client
HTTPS only                          TLS 1.2+ on all APIs
CORS restricted                     Whitelist = Vercel domain only
Rate limiting                       100 req/min per IP
Input sanitization                  Before LLM prompt injection
Paper trading only                  No real money (ADR-008)
```

---

## 2. Key Isolation Model

```
┌──────────────────────────────────────────────────────────────┐
│  KEY HIERARCHY                                                │
│                                                               │
│  Service Role Key (FULL ACCESS — bypasses RLS)               │
│  ├── Used by: Edge Functions, FastAPI backend                │
│  ├── NEVER in: frontend code, .env files exposed to browser  │
│  └── CI scan: check_no_service_key.sh blocks if found        │
│                                                               │
│  Anon Key (PUBLIC — RLS-enforced)                            │
│  ├── Used by: Frontend React app                             │
│  ├── Can only: read/write own data (auth.uid() = user_id)   │
│  └── Safe to expose in VITE_ env vars                        │
│                                                               │
│  FASTAPI_SECRET_KEY (service-to-service auth)                │
│  ├── Used by: Edge Functions → FastAPI calls                 │
│  └── Verified via X-Oracle-Secret header middleware          │
└──────────────────────────────────────────────────────────────┘
```

### Hard Rules

```
❌ NEVER store real financial account numbers
❌ NEVER store real brokerage credentials
❌ NEVER expose service role key to frontend
❌ NEVER log full LLM prompts (may contain financial PII)
❌ NEVER execute real trades (paper trading only)
❌ NEVER use public storage buckets

✅ ALWAYS validate input before LLM injection
✅ ALWAYS use signed URLs for file access
✅ ALWAYS log sensitive actions to audit_log
✅ ALWAYS use RLS with JWT, not service role, in frontend
```

---

## 3. Row Level Security (RLS)

**Every table in ORACLE has RLS enabled. No exceptions.**

### Access Matrix

| Table | User Read | User Write | Service Role |
|-------|-----------|------------|--------------|
| `profiles` | Own only | Own only | Full |
| `positions` | Own only | Own only | Full |
| `trades` | Own only | Own only | Full |
| `simulations` | Own only | Own only | Full |
| `signal_events` | All (read-only) | ❌ | Full |
| `strategies` | Own + public | Own only | Full |
| `memory_nodes` | Own only | Own only | Full |
| `investor_profiles` | Own only | Own only | Full |
| `transparency_feed_events` | Own only | Own only | Full |
| `audit_log` | Own only | INSERT only | Full (no UPDATE/DELETE) |

### Demo Mode Bypass

For the hackathon, a `demo_user_id()` function allows anonymous access:

```sql
USING (auth.uid() = user_id OR user_id = oracle_feed.demo_user_id())
```

> **Phase 2:** Remove the demo bypass and require authentication for all access.

---

## 4. Runtime Guards

### Startup Validation

[`services/security.py`](../apps/api/services/security.py) validates configuration at startup:

```python
from services.security import validate_security_config
warnings = validate_security_config()
```

Checks:
1. Service role key is set if Supabase URL is configured
2. `FASTAPI_SECRET_KEY` is not the insecure default (in production)
3. Anon key ≠ service role key (critical RLS bypass prevention)

### Response Leak Guard Middleware

Scans all JSON responses for accidental key leakage:

```python
@app.middleware("http")
async def leak_guard(request, call_next):
    response = await call_next(request)
    # Scan response body for JWT patterns, API keys
    if scan_for_key_leaks(response_body):
        logger.error("security_leak_detected", path=request.url.path)
        return JSONResponse({"error": "Response blocked"}, status_code=500)
    return response
```

Detected patterns:
- JWT tokens (`eyJ...`)
- OpenAI-style keys (`sk-...`)
- `SUPABASE_SERVICE_ROLE_KEY` / `service_role` strings

---

## 5. Resilience (Circuit Breakers)

See [Architecture → Resilience Model](ARCHITECTURE.md#6-resilience-model) for the full
circuit breaker documentation.

| Breaker | Protects | Failover Behavior |
|---------|----------|-------------------|
| `llm_breaker` | GPT-4o, Whisper, embeddings | Deterministic fallback (mode disclosed) |
| `market_data_breaker` | Polygon, AlphaVantage, yfinance | Provider chain failover |
| `polymarket_breaker` | Polymarket REST + WS | Cached values |
| `news_breaker` | NewsAPI | Keyword heuristic |

---

## 6. GDPR / AVG Compliance

| Obligation | Implementation |
|-----------|----------------|
| **Data minimization** | Only collect data needed for ORACLE function |
| **Purpose limitation** | Data used only for investment recommendations |
| **Storage limitation** | Retention cron jobs (voice 24h, feed 30d) |
| **Right to erasure** | `memory_service.reset_memory(user_id)` — deletes all memory |
| **Data portability** | Strategy export (JSON/PDF) |
| **Consent** | Demo mode = implicit; auth mode = explicit consent on registration |
| **Transparency** | Full reasoning trail visible for every decision |
| **EU residency** | Supabase Frankfurt (eu-central-1) |

### Right to Erasure API

```python
# Erase all user memory data (GDPR Article 17)
await memory_service.reset_memory(user_id)
# Deletes: memory_nodes, learning_log, simulation_accuracy, investor_profiles
```

### Data Classification

```
CLASS       EXAMPLES                        CONTROLS
──────────────────────────────────────────────────────────────
PUBLIC      Market prices, signals,         No special controls
            simulation verdicts

PRIVATE     Portfolio positions,            RLS user-scoped,
            trade history                   audit log

SENSITIVE   Investor profile,               RLS + audit log +
            behavioral data                 explicit consent UI

SYSTEM      Service role keys,              Env vars only,
            API credentials                 never in DB
```

---

## 7. Threat Model

### T1: Service Role Key Leakage

| | |
|---|---|
| **Risk** | If service role key reaches frontend, attacker can bypass all RLS |
| **Mitigation** | CI scan (`check_no_service_key.sh`), runtime leak guard middleware, key never in VITE_ vars |
| **Detection** | Middleware logs `security_leak_detected` if pattern found in response |

### T2: Prompt Injection

| | |
|---|---|
| **Risk** | Malicious input in seed_text or voice command could manipulate LLM |
| **Mitigation** | Input validation (min length), structured JSON output parsing, system prompts define behavior |
| **Detection** | Response monitoring via transparency feed |

### T3: LLM Rate Limit Exhaustion

| | |
|---|---|
| **Risk** | Attacker triggers many simulations to exhaust OpenAI quota |
| **Mitigation** | Rate limiting (100 req/min), circuit breaker opens after 5 LLM failures |
| **Detection** | Circuit breaker logs, cost tracking per simulation |

### T4: Data Exfiltration via RLS Bypass

| | |
|---|---|
| **Risk** | Malicious SQL or RPC call accessing another user's data |
| **Mitigation** | RLS on every table, `SECURITY DEFINER` functions with `SET search_path`, user_id parameter validation |
| **Detection** | Audit log records all sensitive access |

### T5: Storage Access Control

| | |
|---|---|
| **Risk** | Unauthorized file access via storage buckets |
| **Mitigation** | All buckets private, signed URLs (1h expiry), user-scoped path prefixes (`${user_id}/...`) |
| **Detection** | Storage access logs in Supabase dashboard |

---

## 8. Security CI Pipeline

The security scan runs as the **first CI job** — all other jobs depend on it passing:

```yaml
jobs:
  security-scan:          # ← Runs FIRST
    steps:
      - run: bash .github/scripts/check_no_service_key.sh

  typecheck:
    needs: [security-scan]  # ← Blocked if security fails
```

### What the Scan Checks

```
✅ Frontend code (apps/web/src, packages/) for service_role references
✅ .gitignore includes .env.local
✅ No .env files tracked in git
✅ Supabase client uses anon key only
```

### Running Locally

```bash
bash .github/scripts/check_no_service_key.sh
```

---

> **← Back to README** | [Development Guide →](DEVELOPMENT.md)
