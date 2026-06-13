<div align="center">

# 🔮 ORACLE

### Swarm Intelligence Broker

**_We don't predict markets. We simulate the humans that move them._**

[![Status](https://img.shields.io/badge/status-active-success)]()
[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![Tests](https://img.shields.io/badge/tests-40%20passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-UNLICENSED-red)]()
[![GDPR](https://img.shields.io/badge/compliance-GDPR%2FAVG-orange)]()

**Amsterdam AI Broker Hackathon 2026** · Amsterdam Investment Club × Amsterdam Quant Society

</div>

---

ORACLE is an **AI-native brokerage intelligence platform** that simulates human market
psychology before making any investment recommendation. Instead of modeling assets, ORACLE
models the _people_ who move them — deploying swarms of 100–1,000 AI agents with independent
personas, behavioral logic, and persistent memory to predict how markets will react to
real-world triggers.

Every recommendation is **fully transparent** — you see exactly which of the 10 intelligence
layers activated, what each contributed, and why the decision was made. No black boxes.

---

## 📖 Documentation Hub

| Document | What's Inside | For Whom |
|----------|--------------|----------|
| **[🏗️ Architecture](docs/ARCHITECTURE.md)** | System design, data flow, the 10-layer intelligence stack, ADRs | Engineers, judges |
| **[🔌 API Reference](docs/API_REFERENCE.md)** | All 12 FastAPI endpoints + 5 Edge Functions with examples | Integrators |
| **[🗄️ Database Guide](docs/DATABASE.md)** | 30+ tables, 8 schemas, RLS policies, pgvector GraphRAG | Backend devs |
| **[🚀 Deployment Guide](docs/DEPLOYMENT.md)** | Supabase + Railway + Vercel production setup | DevOps |
| **[🎥 Demo Guide](docs/DEMO_GUIDE.md)** | 5-minute hackathon script + pre-demo checklist | Presenters |
| **[🔐 Security Model](docs/SECURITY.md)** | RLS, circuit breakers, GDPR compliance, threat model | Security review |
| **[⚙️ Development](docs/DEVELOPMENT.md)** | Local setup, testing, debugging, codebase tour | Contributors |
| **[📋 Changelog](CHANGELOG.md)** | Version history + roadmap | Everyone |

> **Just want to run it?** Jump to **[Quick Start](#-quick-start)** below.
> **First time here?** Read **[Architecture](docs/ARCHITECTURE.md)** first.

---

## ✨ What ORACLE Does

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT                                    │
│   Any financial trigger:                                        │
│   earnings report · Fed speech · news article · your thesis     │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       10-LAYER INTELLIGENCE STACK                │
│                                                                  │
│  L1 Market Data ─► L2 Macro ─► L3 News+Sentiment ─► L4 Technical│
│       ─► L5 Polymarket ─► L6 Swarm (500 agents) ─► L7 Debate     │
│            ─► L8 Risk ─► L9 GraphRAG Memory ─► L10 Explanation   │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                   │
│   Transparent recommendation + reasoning trail                   │
│   + backtest + autopilot paper trade                             │
└─────────────────────────────────────────────────────────────────┘
```

### The 7 Modules

| Module | What It Does | Screen |
|--------|-------------|--------|
| 🌊 **Swarm** | Deploy 100–1,000 AI agents to simulate market reaction | `/swarm` |
| 🎙️ **Voice** | Speak commands in natural language, get spoken responses | Global |
| ✨ **Strategy** | Describe a strategy in English → get a backtested result | `/strategy` |
| 🤖 **Autopilot** | Autonomous monitoring + paper trading with full transparency | Top bar toggle |
| 🧠 **Memory** | Persistent GraphRAG learning + Investor DNA profiling | `/memory` |
| 🧩 **Layers** | The 10-layer intelligence stack powering every decision | All screens |
| 📊 **War Room** | Real-time command center — portfolio, signals, live feed | `/` |

### What ORACLE Is NOT

- ❌ Not a live trading platform (paper trading only for MVP)
- ❌ Not a regulated financial advisor
- ❌ Not a black-box AI ("every decision is explained")
- ❌ Not a static dashboard ("it acts, not just displays")

---

## 🏗️ System Architecture (Summary)

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER INTERFACES                                                     │
│  ┌─────────────────────────┐  ┌────────────────────────────┐        │
│  │ ORACLE Web App          │  │ ORACLE Mobile (Phase 2)   │        │
│  │ React 18 + TypeScript   │  │ React Native (future)     │        │
│  │ Vite · Zustand · Recharts│  │                           │        │
│  │ Vercel deployment       │  │                           │        │
│  └───────────┬─────────────┘  └────────────────────────────┘        │
└──────────────┼──────────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌─────────────────┐  ┌──────────────────────┐
│ Supabase (EU)   │  │ FastAPI (Python)     │
│ Postgres + RLS  │  │ AI/ML engine         │
│ Edge Functions  │◄─┤ LangChain · Swarm    │
│ Realtime        │  │ Backtest · GraphRAG  │
│ pgvector        │  │ Railway deploy       │
└────────┬────────┘  └──────────┬───────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │ External Services     │
         │ OpenAI · Polygon.io  │
         │ Polymarket · FRED    │
         │ NewsAPI · Whisper    │
         └──────────────────────┘
```

> **Full architecture deep dive:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 📁 Project Structure

```
oracle/
├── apps/
│   ├── web/                      # React + TypeScript frontend
│   │   ├── src/
│   │   │   ├── components/       # TopBar, VoiceBar, TransparencyFeed
│   │   │   ├── pages/            # WarRoom, Swarm, Strategy, Memory
│   │   │   ├── stores/           # Zustand global state
│   │   │   ├── lib/              # Supabase client, API client
│   │   │   └── types/            # Canonical TypeScript types
│   │   └── package.json
│   │
│   └── api/                      # FastAPI Python backend
│       ├── routers/              # swarm, voice, strategy, signals, etc.
│       ├── services/             # AI engine, signals, resilience, security
│       │   ├── graphrag.py       # pgvector semantic memory (L9)
│       │   ├── langchain_brain.py# Multi-agent debate (L7)
│       │   ├── resilience.py     # Circuit breakers + retry
│       │   ├── market_data_provider.py # Polygon → AV → yfinance chain
│       │   ├── mirofish.py       # Swarm simulation engine (L6)
│       │   ├── backtest.py       # Historical backtest engine
│       │   ├── memory.py         # Memory service facade
│       │   ├── security.py       # Runtime leak guards
│       │   └── signals/          # L1-L5 signal pipelines
│       ├── tests/                # 40 pytest tests
│       ├── config.py             # Pydantic settings (Addendum D)
│       ├── main.py               # FastAPI app entry point
│       └── Dockerfile
│
├── packages/
│   ├── shared-types/             # Shared TypeScript types
│   └── mock-data/                # Demo seed data
│
├── supabase/
│   ├── migrations/               # SQL: schema + RLS + GraphRAG + cron
│   ├── tests/                    # pgTAP RLS policy tests
│   ├── seed.sql                  # Demo data (47 sims, portfolio, signals)
│   ├── config.toml               # Supabase local config
│   └── functions/                # 5 Edge Functions (Deno)
│       ├── swarm-trigger/
│       ├── autopilot-loop/
│       ├── signal-ingest/
│       ├── memory-update/
│       └── trade-execute/
│
├── oracle-swarm/                 # MiroFish fork (swarm engine)
│   ├── personas/financial/       # 8 financial agent personas (YAML)
│   ├── seed/                     # Financial entity parser
│   ├── callbacks/                # Supabase real-time writer
│   ├── utils/                    # Cost tracker
│   └── config/                   # Offline mode settings
│
├── .github/
│   ├── workflows/ci.yml          # CI/CD pipeline
│   └── scripts/                  # Security scan, etc.
│
├── docs/                         # ← You are here
├── docker-compose.yml            # Local dev environment
├── .env.example                  # Environment variable registry
└── pnpm-workspace.yaml
```

---

## 🚀 Quick Start

### Option A: Full Local Setup (recommended)

**Prerequisites:** Node.js ≥ 20 · Python ≥ 3.12 · Docker Desktop · Supabase CLI

```bash
# ── 1. Clone ──
git clone https://github.com/knarayanareddy/Oracle.git
cd oracle

# ── 2. Install dependencies ──
pnpm install
pip install -r apps/api/requirements.txt

# ── 3. Configure environment ──
cp .env.example .env.local
# → Open .env.local and fill in your API keys
#   (see docs/DEVELOPMENT.md for which keys are required vs optional)

# ── 4. Start Supabase ──
supabase start
supabase db reset          # applies migrations + seeds demo data
supabase functions serve   # serve Edge Functions

# ── 5. Generate TypeScript types ──
pnpm gen:types

# ── 6. Start backend (terminal 1) ──
cd apps/api && uvicorn main:app --reload --port 8000

# ── 7. Start frontend (terminal 2) ──
cd apps/web && pnpm dev
# → http://localhost:5173
```

### Option B: Demo Mode (no API keys needed)

ORACLE runs in demo mode by default with mocked data and deterministic simulations.
You only need API keys for real LLM reasoning, live market data, and voice transcription.

```bash
# Minimal setup — works with zero API keys
supabase start && supabase db reset
cd apps/api && uvicorn main:app --reload --port 8000  # terminal 1
cd apps/web && pnpm dev                                # terminal 2
```

### Verify Your Setup

```bash
curl http://localhost:8000/health    # → {"status": "healthy", ...}
open http://localhost:5173           # → War Room dashboard loads
```

> **Trouble?** See **[Troubleshooting](docs/DEVELOPMENT.md#troubleshooting)** in the Development guide.

---

## 🔑 Environment Variables

All configuration is centralized in `.env.example` (Addendum D of the design doc).
Copy to `.env.local` and fill in what you need:

| Variable | Required | Purpose |
|----------|----------|---------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Public key (frontend-safe) |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Privileged key (backend + Edge Functions only) |
| `OPENAI_API_KEY` | Recommended | GPT-4o, Whisper, embeddings |
| `POLYGON_API_KEY` | Optional | Enterprise market data (L1) |
| `ALPHA_VANTAGE_API_KEY` | Optional | Mid-tier market data (L1) |
| `NEWS_API_KEY` | Optional | News feed (L3) |
| `FRED_API_KEY` | Optional | Macro signals (L2) |
| `FASTAPI_SECRET_KEY` | ✅ Prod | Internal service auth |

> **Full variable reference:** [.env.example](.env.example) | **[Security model](docs/SECURITY.md)**

---

## 🧪 Testing

```bash
# Python tests (40 tests — resilience, GraphRAG, market data, security, API)
cd apps/api && pytest tests/ -v

# TypeScript type checking
pnpm typecheck

# RLS policy tests (requires Supabase running)
supabase test db

# Security scan (blocks merges if service key found in frontend)
bash .github/scripts/check_no_service_key.sh

# Build frontend
pnpm --filter @oracle/web build
```

---

## 🔒 Security & Compliance

ORACLE is designed with **privacy by architecture**:

- **RLS on every table** — PostgreSQL enforces row-level access at the DB layer
- **Service role key isolation** — never in frontend code; runtime leak guard middleware
- **CI security gate** — automated scan blocks service key leakage before deploy
- **Paper trading only** — no real money execution (ADR-008, regulatory safe)
- **GDPR/AVG compliant** — EU data residency (Frankfurt), right-to-erasure API
- **No PII in logs** — UUIDs only, structured JSON logging
- **Signed URLs** — no public storage buckets
- **Circuit breakers** — every external call degrades gracefully, never crashes

> **Full security model + threat analysis:** [docs/SECURITY.md](docs/SECURITY.md)

---

## 🛡️ Resilience

Every external dependency is protected by a circuit breaker + retry layer:

| Component | Failure Threshold | Cooldown | Fallback Behavior |
|-----------|------------------|----------|-------------------|
| LLM (GPT-4o) | 5 failures | 30s | Deterministic debate (mode flag disclosed) |
| Market data | 4 failures | 20s | Provider chain: Polygon → AlphaVantage → yfinance |
| Polymarket | 3 failures | 45s | Cached values (up to 1h) |
| News API | 3 failures | 60s | Keyword heuristic sentiment |
| Voice (Whisper) | 5 failures | 30s | Honest error status (not fake transcript) |

Circuit states: `CLOSED` → `OPEN` (fail-fast) → `HALF_OPEN` (probe) → `CLOSED` (recovered)

---

## 🎥 5-Minute Demo

```
[0:00] Hook        "We simulate the humans that move markets"
[0:30] Swarm       Paste Fed statement → watch 500 agents react live
[1:30] Voice       "What should I do with my tech exposure?"
[2:30] Strategy    Type a strategy → see backtest with full metrics
[3:30] Autopilot   Flip the toggle → watch transparency feed fire live
[4:30] Close       "This is what Robinhood looks like in 3 years"
```

> **Full demo guide with pre-demo checklist:** [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)

---

## 🗺️ Roadmap

| Phase | Status | Scope |
|-------|--------|-------|
| **Phase 0** Foundation | ✅ Done | UI shell, Supabase, FastAPI, mock data, MiroFish fork |
| **Phase 1** Hackathon MVP | ✅ Done | All 7 modules, voice, swarm, strategy, autopilot, transparency |
| **Phase 2** Post-hackathon Depth | 🔜 Month 1–3 | Real auth, live broker API, Neo4j, Zep memory, offline OASIS |
| **Phase 3** Scale | 📋 Month 3–12 | Multi-user, strategy marketplace, agent reputation, MiFID II |

> **Full roadmap:** [CHANGELOG.md](CHANGELOG.md)

---

## 🤝 Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the development workflow, code standards,
and commit conventions.

```bash
# Quick PR flow
git checkout -b feature/your-feature
# ... make changes ...
pnpm typecheck && cd apps/api && pytest tests/ -v
git commit -m "feat(swarm): add volatility detection to swarm engine"
git push origin feature/your-feature
# Open PR → CI runs: security scan → typecheck → tests → review
```

---

## 📄 License

UNLICENSED — proprietary. See the design doc §00 for details.

---

## 📬 Links

| Resource | URL |
|----------|-----|
| Design Doc (SSOT) | [Oracledesigndoc.md](https://github.com/knarayanareddy/Oracle/blob/main/Oracledesigndoc.md) |
| Frontend (Vercel) | _deployed at hackathon_ |
| API (Railway) | _deployed at hackathon_ |
| Supabase Dashboard | _Frankfurt (eu-central-1)_ |

---

<div align="center">

**ORACLE Engineering Design Suite v1.0.0**

_Last updated: 2026-06-13_

_This document and all code artifacts adhere to the Single Source of Truth (SSOT)_
_principle. If any artifact conflicts with the design doc, the design doc wins._

</div>
