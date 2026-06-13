# ⚙️ ORACLE — Development Guide

> **Navigation:** [← Back to README](../README.md) | [Architecture](ARCHITECTURE.md) | [Deployment](DEPLOYMENT.md)

Local development setup, testing, debugging, codebase tour, and contribution workflow.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Setup](#2-local-setup)
3. [Which API Keys Do I Need?](#3-which-api-keys-do-i-need)
4. [Running the Services](#4-running-the-services)
5. [Testing](#5-testing)
6. [Debugging](#6-debugging)
7. [Codebase Tour](#7-codebase-tour)
8. [Adding a New Feature](#8-adding-a-new-feature)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | ≥ 20 | [nodejs.org](https://nodejs.org) |
| pnpm | ≥ 9 | `npm install -g pnpm` |
| Python | ≥ 3.12 | [python.org](https://python.org) |
| Docker Desktop | Latest | [docker.com](https://docker.com) |
| Supabase CLI | ≥ 1.x | `brew install supabase/tap/supabase` |

### Verify

```bash
node --version    # v20+
pnpm --version    # 9+
python --version  # 3.12+
docker --version  # works
supabase --version
```

---

## 2. Local Setup

```bash
# ── Clone ──
git clone https://github.com/knarayanareddy/Oracle.git
cd oracle

# ── Install JavaScript dependencies ──
pnpm install

# ── Install Python dependencies ──
pip install -r apps/api/requirements.txt

# ── Configure environment ──
cp .env.example .env.local
# Edit .env.local with your keys (see section 3 below)

# ── Start Supabase (requires Docker) ──
supabase start
# Note the output: API URL, anon key — copy to .env.local

# ── Apply migrations + seed demo data ──
supabase db reset

# ── Generate TypeScript types ──
pnpm gen:types

# ── Copy env vars for the API too ──
cp .env.local apps/api/.env
```

---

## 3. Which API Keys Do I Need?

### Tier 1: Required to Run

| Key | Why |
|-----|-----|
| `SUPABASE_URL` | Database connection |
| `SUPABASE_ANON_KEY` | Frontend data access |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend DB writes |

> **In demo mode,** local Supabase provides these automatically after `supabase start`.

### Tier 2: Recommended (enables real AI)

| Key | Why | Without It |
|-----|-----|-----------|
| `OPENAI_API_KEY` | GPT-4o reasoning, Whisper, embeddings | Falls back to deterministic logic (still works!) |
| `FASTAPI_SECRET_KEY` | Service-to-service auth | Uses insecure default (demo OK) |

### Tier 3: Optional (enhances specific layers)

| Key | Layer | Without It |
|-----|-------|------------|
| `POLYGON_API_KEY` | L1 enterprise data | Uses yfinance (free) |
| `ALPHA_VANTAGE_API_KEY` | L1 mid-tier data | Uses yfinance (free) |
| `NEWS_API_KEY` | L3 news feed | Uses keyword heuristic |
| `FRED_API_KEY` | L2 macro data | Uses static fallback values |
| `ELEVENLABS_API_KEY` | TTS voice | Uses Web Speech API (browser) |

> **The app runs fully without any Tier 3 keys.** They just enhance signal quality.

---

## 4. Running the Services

### Terminal 1: Supabase

```bash
supabase start              # start local Supabase stack
supabase functions serve    # serve Edge Functions on port 54321
```

### Terminal 2: FastAPI Backend

```bash
cd apps/api
uvicorn main:app --reload --port 8000

# → API at http://localhost:8000
# → Swagger docs at http://localhost:8000/docs
# → ReDoc at http://localhost:8000/redoc
```

### Terminal 3: React Frontend

```bash
cd apps/web
pnpm dev

# → http://localhost:5173
```

### Verify Everything Works

```bash
# 1. API health
curl http://localhost:8000/health
# → {"status": "healthy", ...}

# 2. Frontend loads
open http://localhost:5173
# → War Room dashboard with demo data

# 3. Supabase Studio (optional GUI)
open http://localhost:54323
```

---

## 5. Testing

### Python Tests (40 tests)

```bash
cd apps/api
pytest tests/ -v                    # all tests
pytest tests/test_resilience.py -v  # circuit breaker tests only
pytest tests/ -k "graphrag" -v      # filter by keyword
pytest tests/ --tb=long             # full tracebacks
```

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_api.py` | 11 | Core API + services |
| `test_resilience.py` | 9 | Circuit breaker states, retry, fallback |
| `test_graphrag.py` | 20 | Entity extraction, market data, security, JSON parsing |

### TypeScript

```bash
pnpm typecheck                    # type checking (tsc --noEmit)
pnpm --filter @oracle/web build   # production build
```

### Database (RLS)

```bash
supabase test db                  # pgTAP tests
```

### Security Scan

```bash
bash .github/scripts/check_no_service_key.sh
```

---

## 6. Debugging

### FastAPI

```bash
# Verbose logging
LOG_LEVEL=debug uvicorn main:app --reload --port 8000

# Test a specific endpoint
curl -X POST http://localhost:8000/api/v1/swarm/run \
  -H "Content-Type: application/json" \
  -H "X-Oracle-Secret: dev-insecure-change-me" \
  -d '{"simulation_id": "test", "seed_text": "test trigger for debugging"}' | jq

# Check circuit breaker state (in Python shell)
python -c "
from services.resilience import llm_breaker, market_data_breaker, polymarket_breaker
print(f'LLM: {llm_breaker.state}')
print(f'Market: {market_data_breaker.state}')
print(f'Polymarket: {polymarket_breaker.state}')
"
```

### Supabase

```bash
# View local database
supabase status                    # shows connection info
psql postgresql://postgres:postgres@localhost:54322/postgres

# Check RLS policies
SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname LIKE 'oracle_%';

# View scheduled jobs
SELECT jobid, schedule, command FROM cron.jobs;

# Reset everything
supabase db reset
```

### React

```bash
# The Zustand store is visible in React DevTools
# Install: https://chrome.google.com/webstore/detail/react-developer-tools

# Realtime events are logged in the console
# Filter: "New feed event"
```

### Common Issues

| Problem | Fix |
|---------|-----|
| `ImportError: No module named 'pydantic_settings'` | `pip install pydantic-settings` |
| Supabase won't start | Ensure Docker Desktop is running |
| `ECONNREFUSED 127.0.0.1:8000` | Start FastAPI: `uvicorn main:app --reload` |
| Frontend blank page | Check `.env.local` has `VITE_SUPABASE_URL` |
| `auth.uid() = null` in queries | You're in demo mode — this is expected |
| yfinance rate limited | Wait 15 min, or set `MARKET_DATA_PROVIDER=polygon` |

---

## 7. Codebase Tour

### Backend (`apps/api/`)

```
Entry Point
├── main.py                 FastAPI app, middleware, routers
├── config.py               Pydantic settings (reads .env)
├── logging_config.py       Structured JSON logging (structlog)
│
Routers (HTTP endpoints)
├── routers/
│   ├── health.py           GET /health
│   ├── swarm.py            POST /swarm/run, /swarm/debate
│   ├── voice.py            POST /voice/transcribe, /voice/process
│   ├── strategy.py         POST /strategy/parse, /strategy/backtest
│   ├── signals.py          GET /signals/latest, POST /signals/refresh
│   ├── recommendations.py  POST /recommendations/generate
│   └── accuracy.py         POST /accuracy/evaluate, GET /accuracy/stats
│
Services (Business Logic)
├── services/
│   ├── mirofish.py         Swarm simulation (L6) + mock fallback
│   ├── langchain_brain.py  Multi-agent debate (L7) + intent router (L10)
│   ├── backtest.py         Historical backtest engine
│   ├── graphrag.py         pgvector semantic memory (L9)
│   ├── memory.py           Memory service facade (L9)
│   ├── market_data_provider.py  Provider chain: Polygon → AV → yfinance
│   ├── resilience.py       Circuit breakers + retry logic
│   ├── security.py         Runtime leak guards
│   └── signals/            L1-L5 signal pipelines
│       ├── l1_market_data.py
│       ├── l2_macro.py
│       ├── l3_news.py
│       ├── l4_technical.py
│       ├── l5_polymarket.py    (includes WebSocket client)
│       └── pipeline.py         (orchestrator)
```

### Frontend (`apps/web/src/`)

```
├── main.tsx                React entry, BrowserRouter, QueryClient
├── App.tsx                 Routes + layout (TopBar, VoiceBar, Feed)
│
├── components/
│   ├── TopBar.tsx          Nav + autopilot toggle + layer status dots
│   ├── VoiceBar.tsx        Hold-to-speak + text fallback + suggestions
│   └── TransparencyFeed.tsx  Real-time feed panel (Supabase Realtime)
│
├── pages/
│   ├── WarRoom.tsx         Dashboard: equity curve, positions, signals
│   ├── SwarmPage.tsx       Swarm sim: seed input → live agents → verdict
│   ├── StrategyPage.tsx    NL → parse → backtest → metrics
│   └── MemoryPage.tsx      Investor DNA radar, accuracy, learning log
│
├── stores/
│   └── oracle.store.ts     Zustand global state + demo feed sequence
│
├── lib/
│   ├── supabase.ts         Supabase client (anon key only!)
│   └── api.ts              FastAPI client wrappers
│
└── types/
    └── index.ts            All TypeScript types (canonical)
```

---

## 8. Adding a New Feature

### Example: Adding a new signal layer (L6b)

1. **Create the signal provider:**
   ```
   apps/api/services/signals/l6b_new_signal.py
   ```
   ```python
   from .base import SignalProvider

   class L6bNewSignal(SignalProvider):
       layer = "L6b"

       async def fetch(self) -> list[dict]:
           # Your implementation
           return [...]
   ```

2. **Register in the pipeline:**
   ```python
   # apps/api/services/signals/pipeline.py
   from .l6b_new_signal import l6b_new_signal
   ALL_PROVIDERS = [..., l6b_new_signal]
   ```

3. **Add the layer to frontend types:**
   ```typescript
   // apps/web/src/types/index.ts
   export type Layer = 'L1' | ... | 'L6b' | ...
   ```

4. **Update RLS CHECK constraints** (if the layer appears in DB):
   ```sql
   ALTER TABLE oracle_signals.signal_events
     DROP CONSTRAINT signal_events_layer_check,
     ADD CONSTRAINT signal_events_layer_check
       CHECK (layer IN ('L1', ..., 'L6b', ...));
   ```

5. **Write tests:**
   ```python
   def test_l6b_signal_layer():
       from services.signals.l6b_new_signal import L6bNewSignal
       assert L6bNewSignal().layer == "L6b"
   ```

6. **Run all tests:**
   ```bash
   cd apps/api && pytest tests/ -v
   pnpm typecheck
   ```

### Commit Convention

```
feat(swarm): add volatility detection to swarm engine
fix(voice): use in-memory BytesIO instead of temp files
docs(api): add response examples to strategy endpoints
refactor(resilience): extract circuit breaker to shared module
test(graphrag): add entity extraction tests
chore(deps): pin langchain to 0.3.4
```

---

## 9. Troubleshooting

### "Supabase won't start"

```bash
# Ensure Docker is running
docker info

# Reset Supabase
supabase stop
supabase start

# If port conflicts (54321, 54322, 54323)
# Check what's using the port:
lsof -i :54321
```

### "Frontend shows 'Loading...' forever"

```bash
# Check if Supabase is reachable
curl http://localhost:54321/rest/v1/

# Check if .env.local exists and has values
cat .env.local | grep VITE_SUPABASE

# Regenerate types
pnpm gen:types

# Restart dev server
cd apps/web && pnpm dev
```

### "API returns 500 errors"

```bash
# Check the logs
cd apps/api && uvicorn main:app --reload --port 8000 --log-level debug

# Common cause: missing env vars
python -c "from config import settings; print(f'Supabase: {bool(settings.supabase_url)}')"

# Reset circuit breakers (if stuck open)
python -c "
from services.resilience import llm_breaker, market_data_breaker
llm_breaker.reset()
market_data_breaker.reset()
print('Breakers reset')
"
```

### "yfinance returns empty data"

yfinance rate-limits aggressively (~2000 requests/hour, shared). Solutions:
1. Wait 15 minutes
2. Set `ALPHA_VANTAGE_API_KEY` in `.env.local`
3. Set `POLYGON_API_KEY` for enterprise data
4. Set `MARKET_DATA_PROVIDER=auto` (uses chain failover)

---

> **← Back to README** | [Contributing →](../CONTRIBUTING.md)
