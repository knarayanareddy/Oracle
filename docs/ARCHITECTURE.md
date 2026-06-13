# 🏗️ ORACLE — Architecture Deep Dive

> **Navigation:** [← Back to README](../README.md) | [API Reference](API_REFERENCE.md) | [Database](DATABASE.md)

This document covers the complete system architecture, the 10-layer intelligence stack,
data flows, architecture decision records (ADRs), and the resilience model.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [The 10-Layer Intelligence Stack](#2-the-10-layer-intelligence-stack)
3. [Request Flow: From Trigger to Recommendation](#3-request-flow-from-trigger-to-recommendation)
4. [Container Diagram](#4-container-diagram)
5. [Architecture Decision Records](#5-architecture-decision-records)
6. [Resilience Model](#6-resilience-model)
7. [Realtime Subscriptions](#7-realtime-subscriptions)

---

## 1. High-Level Architecture

ORACLE uses a **three-tier separation of concerns**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 1: USER INTERFACE (React)                                      │
│                                                                      │
│  War Room dashboard, Swarm chamber, Strategy builder, Memory view    │
│  Voice command bar, Transparency feed                                │
│  Deployed on Vercel · Zustand state · TanStack Query                 │
│                                                                      │
│  ── Uses SUPABASE_ANON_KEY only (never service role) ──              │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS + Supabase Realtime (WebSocket)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 2: DATA + AUTH (Supabase, Frankfurt EU)                        │
│                                                                      │
│  PostgreSQL + pgvector    RLS on every table                         │
│  Edge Functions (Deno)    Auth (JWT)        Storage (signed URLs)    │
│  Realtime channels        pg_cron jobs                              │
│                                                                      │
│  ── Service role key used HERE (Edge Functions only) ──             │
└───────────┬─────────────────────────────┬───────────────────────────┘
            │                             │
            ▼                             ▼
┌──────────────────────────┐  ┌─────────────────────────────────────────┐
│  TIER 3: AI ENGINE        │  │  EXTERNAL SERVICES                       │
│  (FastAPI, Railway)       │  │                                          │
│                           │  │  OpenAI (GPT-4o, Whisper, embeddings)   │
│  LangChain orchestrator   │  │  Polygon.io (enterprise market data)    │
│  MiroFish swarm engine    │  │  Alpha Vantage (market data fallback)   │
│  Backtest engine          │  │  yfinance (market data free fallback)   │
│  GraphRAG (pgvector)      │  │  Polymarket (prediction markets)        │
│  Signal pipeline (L1-L5)  │  │  NewsAPI (news feed)                    │
│                           │  │  FRED (macro data)                      │
│  ── Protected by circuit  │  │  ElevenLabs (TTS, Phase 2)             │
│     breakers on all calls │  │                                          │
└──────────────────────────┘  └─────────────────────────────────────────┘
```

### Why This Separation?

| Concern | Handled By | Why |
|---------|-----------|-----|
| Auth-sensitive DB writes | Supabase Edge Functions | Close to auth context, JWT-aware, RLS-enforced |
| Heavy AI/ML compute | FastAPI (Python) | LangChain, yfinance, pandas, numpy ecosystem |
| UI rendering | React (Vite) | Best financial charting (Recharts), fast HMR |
| Data access control | PostgreSQL RLS | Enforced at DB layer, not bypassable |

---

## 2. The 10-Layer Intelligence Stack

Every ORACLE recommendation flows through up to 10 intelligence layers. Each layer
is independently testable, has its own data source, and contributes a weighted signal
to the final recommendation.

### Layer Definitions

```
LAYER  NAME                    SOURCE                    FREQUENCY      TYPE
────────────────────────────────────────────────────────────────────────────
 L1    Market Data             Polygon/AlphaV/yfinance   Real-time      Passive
 L2    Macro Signals           FRED API                  Daily          Passive
 L3    News + Sentiment        NewsAPI + FinBERT         15 minutes     Passive
 L4    Technical Indicators    Computed from L1          Real-time      Passive
 L5    Polymarket Signals      Polymarket REST + WS      15 minutes     Passive
────────────────────────────────────────────────────────────────────────────
 L6    Swarm Engine            MiroFish / OASIS          On-demand      Active *
 L7    Multi-Agent Debate      LangChain (GPT-4o)        Per L6 run     Active
 L8    Risk Scoring            Custom engine             Per recommendation Active
 L9    GraphRAG Memory         pgvector + OpenAI embed   Per interaction Active
 L10   Explanation Generator   GPT-4o                    Per recommendation Active
```

\* L6 triggers when: material signal detected in L1–L5, user requests swarm, or autopilot threshold hit.

### Activation Rules

```
                    ┌─────────────────────────────────┐
                    │  L1-L5: ALWAYS ACTIVE            │
                    │  (passive monitoring loop)       │
                    └────────────┬────────────────────┘
                                 │
                    Material signal detected?
                    (strength ≥ 4, or user request, or autopilot)
                                 │
                                 ▼
                    ┌─────────────────────────────────┐
                    │  L6: SWARM ENGINE fires          │
                    │  (100-1000 agents, 10-40 rounds) │
                    └────────────┬────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────────┐
                    │  L7: DEBATE fires                │
                    │  Bull vs Bear vs Risk → Consensus│
                    └────────────┬────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────────┐
                    │  L8: RISK SCORING                │
                    │  Position sizing, exposure limits│
                    └────────────┬────────────────────┘
                                 │
                    L9 (Memory) queried at start,
                    updated after. L10 fires last.
                                 │
                                 ▼
                    ┌─────────────────────────────────┐
                    │  L10: EXPLANATION GENERATOR      │
                    │  Plain English summary for user  │
                    └─────────────────────────────────┘
```

### Layer Contribution to Recommendations

Each layer reports which layers activated and with what weight:

```json
{
  "layers_activated": ["L3", "L5", "L6", "L7", "L8", "L10"],
  "layer_contribution": {
    "L4": 0.22,
    "L5": 0.28,
    "L6": 0.42,
    "L3": 0.08
  }
}
```

---

## 3. Request Flow: From Trigger to Recommendation

Here's the complete flow when a user says "Run a swarm simulation on the Fed statement":

```
User Voice/Text Input
        │
        ▼
┌───────────────────────────┐
│ Voice Bar (React)         │
│ MediaRecorder → audio blob│
└───────────┬───────────────┘
            │ POST /api/v1/voice/transcribe
            ▼
┌───────────────────────────┐
│ FastAPI: Voice Router     │
│ BytesIO → Whisper API     │  ← Circuit breaker wrapped
│ → transcript text         │
└───────────┬───────────────┘
            │ POST /api/v1/voice/process
            ▼
┌───────────────────────────┐
│ FastAPI: LangChain Brain  │
│ GPT-4o intent classifier  │  ← Circuit breaker wrapped
│ → "run_swarm_simulation"  │
└───────────┬───────────────┘
            │ invokeFunction('swarm-trigger', {...})
            ▼
┌───────────────────────────┐
│ Edge Function: swarm-trigger│
│ 1. Validate input         │
│ 2. Create simulation row  │
│ 3. Emit feed event (L6)   │──► Supabase Realtime ──► Transparency Feed
│ 4. Call FastAPI /swarm/run│
└───────────┬───────────────┘
            │ POST /api/v1/swarm/run
            ▼
┌───────────────────────────┐
│ FastAPI: Swarm Router     │
│ MiroFish engine runs:     │
│ ┌─ 500 agents spawn       │
│ │  40 rounds of debate    │
│ │  Opinion dynamics       │
│ │  Herding amplification  │
│ └─ Consensus extraction   │
│                           │
│ Streams rounds to DB ─────┼──► simulation_rounds (Realtime)
│ Finalizes simulation ─────┼──► simulations + simulation_reports
└───────────┬───────────────┘
            │
            ▼ (if autopilot active)
┌───────────────────────────┐
│ FastAPI: Debate (L7)      │
│ ┌─ Bull Agent (GPT-4o)    │  ← Concurrent, circuit breaker each
│ ├─ Bear Agent (GPT-4o)    │
│ ├─ Risk Agent (GPT-4o)    │
│ └─ Consensus Synthesizer  │
│ → BUY/SELL/HOLD/REDUCE    │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│ Edge Function: trade-execute│
│ Paper trade (ADR-008)     │
│ Position sizing validation│
│ Audit log (append-only)   │
│ Emit feed event (L10)     │──► Transparency Feed
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│ Edge Function: memory-update│
│ GraphRAG ingest (L9)      │
│ Entity extraction         │
│ Embedding + knowledge graph│
│ Learning log entry        │
└───────────────────────────┘
```

---

## 4. Container Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ DEPLOYMENT VIEW                                                  │
│                                                                  │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │   Vercel     │          │   Railway    │                     │
│  │   (Frontend) │          │   (FastAPI)  │                     │
│  │              │          │              │                     │
│  │  React app   │          │  Python 3.12 │                     │
│  │  CDN-backed  │          │  Uvicorn x2  │                     │
│  │  Edge cached │          │  Health check│                     │
│  └──────┬───────┘          └──────┬───────┘                     │
│         │                         │                              │
│         └──────────┬──────────────┘                              │
│                    │                                             │
│         ┌──────────▼──────────────┐                              │
│         │   Supabase Cloud (EU)   │                              │
│         │   Frankfurt (eu-central)│                              │
│         │                         │                              │
│         │  PostgreSQL 15          │                              │
│         │  + pgvector + pg_cron   │                              │
│         │  Edge Functions (Deno)  │                              │
│         │  Realtime (WebSocket)   │                              │
│         │  Storage (private)      │                              │
│         │  Auth (JWT)             │                              │
│         └─────────────────────────┘                              │
│                                                                  │
│  External APIs: OpenAI · Polygon · AlphaVantage · Polymarket    │
│                 NewsAPI · FRED · ElevenLabs                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Architecture Decision Records

### ADR-001: Supabase as Primary Backend
**Decision:** Supabase (Frankfurt EU region)
**Rationale:** EU data residency, PostgreSQL with RLS, pgvector, Realtime, Edge Functions, storage.
**Status:** ✅ Accepted

### ADR-002: React + TypeScript + Lovable for Frontend
**Decision:** React 18 + TypeScript + Vite + Tailwind + Recharts
**Rationale:** Best financial charting ecosystem, type safety enforces API contracts.
**Status:** ✅ Accepted

### ADR-003: Python FastAPI as Backend Service Layer
**Decision:** FastAPI for all AI/ML workloads
**Rationale:** LangChain, pandas, numpy, yfinance ecosystem. Async-first, OpenAPI-native.
**Status:** ✅ Accepted

### ADR-004: MiroFish Fork as Swarm Engine
**Decision:** Fork MiroFish (OASIS-based) and add financial personas
**Rationale:** Full simulation pipeline with GraphRAG seed extraction + ReportAgent synthesis.
**Status:** ✅ Accepted

### ADR-005: LangChain for Agent Orchestration
**Decision:** LangChain (Python) for multi-agent orchestration
**Rationale:** Native tool-calling, agent loop, memory integrations. Pin versions aggressively.
**Status:** ✅ Accepted

### ADR-006: GPT-4o Primary, Qwen-plus for Simulation
**Decision:** GPT-4o for reasoning, Qwen-plus for swarm agents (cost optimization)
**Rationale:** 40-round 500-agent sim = 2-4M tokens. Qwen at $0.0004/1K vs GPT-4o at $0.01/1K = 25x savings.
**Status:** ✅ Accepted

### ADR-007: Polymarket as L5 Signal Layer
**Decision:** Integrate Polymarket API (REST + WebSocket)
**Rationale:** Real-money-backed probabilities, forward-looking, orthogonal to technicals.
**Status:** ✅ Accepted

### ADR-008: Paper Trading Only
**Decision:** No real money execution in MVP
**Rationale:** Regulatory (MiFID II, ESMA, Wft). Real execution requires Dutch financial license.
**Status:** ✅ Accepted — Do not override.

### ADR-009: Offline Mode (Phase 2)
**Decision:** Ollama + Neo4j Community Edition for fully local operation
**Rationale:** Institutional clients won't send signals to external APIs. Privacy-first enterprise differentiator.
**Status:** ✅ Accepted for Phase 2

---

## 6. Resilience Model

Every external call passes through a **circuit breaker + retry** layer:

```
                        ┌─────────────────────┐
                        │  Incoming Request    │
                        └──────────┬──────────┘
                                   ▼
                        ┌─────────────────────┐
                        │ Circuit Breaker      │
                        │                      │
     ┌──────────────────│ Is circuit OPEN?     │
     │                  └──────────┬──────────┘│
     │ YES                         │ NO         │
     ▼                             ▼            │
┌──────────┐          ┌──────────────────┐     │
│ Fallback │          │ Retry with        │     │
│ (instant)│          │ Exponential       │     │
└──────────┘          │ Backoff (2x)      │     │
                      └────────┬─────────┘     │
                               │                │
                    ┌──────────▼──────────┐    │
                    │ Success?            │    │
                    └──────┬───────┬──────┘    │
                     YES   │       │ NO        │
                           │       ▼           │
                           │  ┌────────────┐  │
                           │  │ Register   │  │
                           │  │ failure    │  │
                           │  │ with       │  │
                           │  │ breaker    │  │
                           │  └─────┬──────┘  │
                           │        │         │
                           │        ▼         │
                           │  Threshold hit?──┼──► OPEN circuit
                           │        │         │
                           ▼        ▼         │
                    ┌──────────────────┐      │
                    │ Return result     │      │
                    │ or fallback       │──────┘
                    └──────────────────┘
```

### Circuit Breaker State Machine

| State | Behavior | Transition |
|-------|----------|------------|
| **CLOSED** | Requests flow normally | → OPEN after N failures |
| **OPEN** | Fail-fast to fallback (no call made) | → HALF_OPEN after cooldown |
| **HALF_OPEN** | One probe request allowed | → CLOSED on success, → OPEN on failure |

### Breaker Configuration

| Breaker | Threshold | Cooldown | Wraps |
|---------|-----------|----------|-------|
| `llm_breaker` | 5 failures | 30s | GPT-4o, Whisper, embeddings |
| `market_data_breaker` | 4 failures | 20s | Polygon, AlphaVantage, yfinance |
| `polymarket_breaker` | 3 failures | 45s | Polymarket REST + WS |
| `news_breaker` | 3 failures | 60s | NewsAPI |

---

## 7. Realtime Subscriptions

ORACLE uses Supabase Realtime (WebSocket) for live updates:

| Channel | Table | Events | Used By |
|---------|-------|--------|---------|
| `transparency-feed` | `oracle_feed.transparency_feed_events` | INSERT | Transparency Feed panel |
| `simulation-progress` | `oracle_simulation.simulation_rounds` | INSERT | Swarm progress bar |
| `simulation-status` | `oracle_simulation.simulations` | UPDATE | Swarm verdict display |
| `trade-events` | `oracle_portfolio.trades` | INSERT | Portfolio table |

Tables use `REPLICA IDENTITY FULL` to broadcast complete row data on changes.

> **Frontend subscription code:** [apps/web/src/components/TransparencyFeed.tsx](../apps/web/src/components/TransparencyFeed.tsx)

---

> **Next:** [API Reference →](API_REFERENCE.md) | [← Back to README](../README.md)
