# ORACLE Engineering Design Suite
## Single Source of Truth (SSOT) — v1.0.0
**Project:** ORACLE — Swarm Intelligence Broker
**Tagline:** *"We don't predict markets. We simulate the humans that move them."**
**Version:** 1.0.0
**Date:** 2026-06-13
**Status:** Active — Hackathon Build (Amsterdam AI Broker Hackathon 2026)
**Jurisdiction:** Netherlands / EU (GDPR/AVG compliant)
**Canonical Owner:** This document supersedes all other specs, prompts, and notes. If any other artifact conflicts with this document, this document wins. Update the conflicting artifact.

---

## DOCUMENT PRECEDENCE & CANONICALITY RULES

```
PRECEDENCE ORDER (highest → lowest):
1. This document (designdoc.md v1.0.0)
2. Addendum A — Canonical RLS Policies
3. Addendum B — Canonical Field Name Reference
4. Addendum C — API Contract Definitions
5. Addendum D — Environment Variable Registry
6. All other artifacts (prompts, READMEs, inline comments)

RECONCILIATION RULE:
If seed files, Edge Functions, frontend types, or Lovable output
conflict with this document → update those artifacts to match
this document. Never update this document to match broken artifacts
without a formal version bump and changelog entry.
```

---

## TABLE OF CONTENTS

```
00 — Executive Summary
01 — Problem & Opportunity
02 — Product Vision & Constraints
03 — Users & Actors
04 — Feature Model: The 7 ORACLE Modules
05 — MVP Definition & Phased Roadmap
06 — Architecture Decision Records (ADRs)
07 — System Architecture (Container Diagram)
08 — Database Design & Schema
09 — Row Level Security (RLS) Model
10 — Edge Functions & Agentic Logic
11 — MiroFish Swarm Engine Integration
12 — LLM Layer & Agent Orchestration
13 — Market Data & Signal Pipeline
14 — Voice Interface Architecture
15 — Frontend Architecture (Lovable + React)
16 — Authentication & Session Model
17 — Storage Model
18 — Scheduled Jobs (pg_cron)
19 — Security & Compliance
20 — Observability & Monitoring
21 — Developer Workflow & CI/CD
22 — Local Setup & Runbook
23 — Demo Mode & Hackathon Checklist
24 — Glossary
25 — Open Questions & Human Action Items
```

---

## 00 — EXECUTIVE SUMMARY

ORACLE is an **AI-native brokerage intelligence platform** that simulates human market psychology before making any investment recommendation. Unlike traditional broker tools that model assets, ORACLE models the *people* who move assets — deploying swarms of thousands of intelligent agents with independent personas, behavioral logic, and persistent memory to simulate how markets will react to real-world triggers before a single trade is recommended.

ORACLE is built as a **hackathon submission** for the Amsterdam AI Broker Hackathon 2026, organized by the Amsterdam Investment Club and Amsterdam Quant Society. It is designed to be **deployable within a single hackathon session**, visually stunning for live demo, technically deep for quant judges, and architecturally extensible for post-hackathon development.

### Core Capability Summary

```
INPUT:   Any financial trigger (earnings report, Fed speech,
         news article, macro data, user thesis)
         
PROCESS: 10-layer intelligence stack culminating in a
         MiroFish swarm simulation of 100–1,000 AI agents
         
OUTPUT:  Structured investment recommendation with full
         transparent reasoning trail + backtest + autopilot
```

### What ORACLE Is NOT
- Not a live trading platform (paper trading only for MVP)
- Not a regulated financial advisor
- Not a black-box AI ("every decision is explained")
- Not a static dashboard ("it acts, not just displays")

---

## 01 — PROBLEM & OPPORTUNITY

### The Core Problem
Traditional quantitative finance tools model markets as mathematical systems. They feed in prices and output probabilities. But markets are not mathematical systems — they are **social systems**. Markets move because humans panic, herd, overcorrect, and overreact. The very irrationality that breaks traditional models is exactly what ORACLE is designed to simulate.

### The Market Opportunity

**Agentic AI is the defining shift of 2026.** While generative AI dominated 2024–2025, the current wave is agentic — systems that don't just respond to prompts but autonomously perceive, reason, and act across multi-step workflows. Financial services is one of the highest-value domains for this shift.

Key signals:
- Robinhood launched Agentic Trading in 2026 for retail — validating the market
- QuantConnect's Mia serves 300,000+ users with AI-assisted quant strategy
- The Polymarket trading bot case study (MiroFish + 2,847 agent sim → $4,266 profit across 338 trades) proved swarm simulation can generate real alpha
- NeurIPS 2025 Workshop featured AgenticTrading Lab — academic validation of the space

### The Insight
> The winning broker of the next decade will not be the one with the best price feed. It will be the one that best understands collective human psychology before prices move.

---

## 02 — PRODUCT VISION & CONSTRAINTS

### Vision Statement
ORACLE is the first broker intelligence platform that simulates human market psychology at scale — giving any investor access to the kind of collective behavioral insight previously available only to the largest hedge funds.

### Hard Constraints (Non-Negotiable)

```
CONSTRAINT                    REASON
──────────────────────────────────────────────────────────────────
No real money execution        Hackathon scope; regulatory risk
No BSN or financial IDs        GDPR; not needed for MVP
No black-box recommendations   Transparency is the core UX promise
No real user data in demo      Mock data only; privacy first
No impersonation of humans     AI must disclose itself as AI
EU data residency              Supabase Frankfurt region
Paper trading only             Safety; demo credibility
Voice is optional fallback     Browser support inconsistency
```

### Design Principles (In Priority Order)
1. **Transparency First** — every ORACLE recommendation shows its full reasoning chain
2. **Simulation Over Statistics** — simulate human behavior, don't just model price history
3. **Modular Intelligence** — 10 layers, each independently testable and explainable
4. **Demo-Driven Development** — every feature must be demoable in 5 minutes
5. **Institutional Grade** — aesthetic and analytical rigor that quant judges respect
6. **Privacy by Architecture** — RLS, signed URLs, no PII in logs

---

## 03 — USERS & ACTORS

### Actor Model

```
ACTOR              TYPE           ACCESS LEVEL       PRIMARY INTERFACE
──────────────────────────────────────────────────────────────────────
Demo User          Single role    Full read/write    War Room dashboard
(Hackathon)        (no auth)      (demo mode)        + all 4 screens
──────────────────────────────────────────────────────────────────────
Registered User    Authenticated  Personal           All screens +
(Post-hackathon)   via Supabase   portfolio only     persistent memory
──────────────────────────────────────────────────────────────────────
Analyst            Authenticated  Multi-portfolio    Strategy library +
(Post-hackathon)   + role claim   read access        shared simulations
──────────────────────────────────────────────────────────────────────
System / Autopilot Internal       Service role       Edge Functions only
```

### For MVP (Hackathon): Single Actor
The hackathon build assumes a **single demo user** with no authentication barrier. All data is seeded mock data. The architecture is designed so that authentication and multi-user isolation can be added post-hackathon without structural changes.

---

## 04 — FEATURE MODEL: THE 7 ORACLE MODULES

### Module 1 — ORACLE SWARM (MiroFish Simulation Engine)
**Purpose:** Simulate 100–1,000 AI agents with distinct personas reacting to a financial trigger and extract emergent consensus as a structured market signal.

**Core Capabilities:**
- Accept any text seed (news article, earnings report, Fed statement, user thesis)
- Extract entities and construct a knowledge graph via GraphRAG
- Spawn agents across three archetypes: Institutional, Retail, Media/Analyst
- Run agent interactions across two simulated environments (Twitter-like, Reddit-like)
- Extract emergent narrative and directional consensus (Bullish %, Bearish %, Neutral %)
- Produce a structured Oracle Report with confidence score, key narrative, and predicted impact
- Log simulation results to database with accuracy tracking

**What is explicitly OUT of SWARM scope:**
- Real-time market data injection into simulation (Phase 2)
- Agent learning across simulations (Phase 2)
- More than 1,000 agents in a single run (Phase 2)
- Financial instrument-specific agent personas (Phase 2)

---

### Module 2 — ORACLE VOICE (Voice Command Interface)
**Purpose:** Allow users to speak natural language commands to ORACLE and receive spoken + visual responses with full layer activation transparency.

**Core Capabilities:**
- Hold-to-speak microphone activation with visual waveform feedback
- Text fallback input for all voice commands
- Intent routing to correct ORACLE module via LangChain tool-calling
- Contextual response with layer activation pills (which of L1–L10 fired)
- Spoken response via ElevenLabs or Web Speech API
- Suggested command pills for discoverability
- Response cards with "Execute" / "Dismiss" actions

**What is explicitly OUT of VOICE scope:**
- Wake word detection ("Hey ORACLE") — Phase 2
- Multi-turn voice conversation — Phase 2
- Language support beyond English — Phase 2
- Voice biometric authentication — never (privacy)

---

### Module 3 — ORACLE STRATEGY (Plain English Strategy Builder)
**Purpose:** Allow users to describe a trading strategy in plain English and instantly receive a parsed, backtested, deployable strategy.

**Core Capabilities:**
- Natural language strategy input with template examples
- GPT-4o powered parsing into structured strategy JSON (conditions + rules)
- Integration of swarm signals and Polymarket odds as valid strategy conditions
- Backtesting against historical OHLCV data (2020–2026)
- Equity curve visualization vs SPY benchmark
- Performance metrics: Sharpe, Sortino, Win Rate, Max Drawdown, Profit Factor
- Layer contribution analysis (which intelligence layers contributed most alpha)
- One-click deploy to Autopilot
- Strategy save/export (JSON, PDF)

**What is explicitly OUT of STRATEGY scope:**
- Options/derivatives strategies — Phase 2
- Multi-asset portfolio-level backtesting — Phase 2
- Walk-forward optimization — Phase 2
- Live execution against real brokers — never in hackathon build

---

### Module 4 — ORACLE AUTOPILOT (Agentic Autonomous Mode)
**Purpose:** Allow ORACLE to autonomously monitor all 10 intelligence layers, trigger swarm simulations on material signals, and execute paper trades with full transparent reasoning.

**Core Capabilities:**
- Autopilot toggle in top bar with activation confirmation modal
- Autonomous monitoring loop (APScheduler, configurable interval)
- Signal detection across L1–L5 with threshold-based trigger logic
- Auto-triggering of SWARM module on material signals
- Multi-agent internal debate: Bull Agent vs Bear Agent vs Risk Agent
- Consensus-based decision: BUY / SELL / HOLD / REBALANCE
- Paper trade execution with position sizing rules
- Live Transparency Feed (Supabase Realtime) showing every reasoning step
- Learning Log: post-decision lesson extraction and storage
- Max daily trade limits and per-position size caps

**What is explicitly OUT of AUTOPILOT scope:**
- Real money execution — never in hackathon build
- Cross-account portfolio management — Phase 2
- Regulatory reporting — Phase 2
- Risk limits beyond simple position caps — Phase 2

---

### Module 5 — ORACLE MEMORY (GraphRAG Persistent Intelligence)
**Purpose:** Give ORACLE persistent memory across sessions — learning from every simulation, trade, and interaction to produce increasingly personalized and accurate recommendations.

**Core Capabilities:**
- Knowledge graph construction via GraphRAG (entities: assets, events, strategies, risk factors, simulations)
- Persistent agent memory via Zep Cloud or Neo4j Community Edition
- Investor DNA profiling: revealed vs. stated risk tolerance, behavioral patterns
- Personalization layer: ORACLE adapts recommendations based on learned profile
- Simulation accuracy tracking: per signal-combination accuracy over time
- Learning Log: structured lessons with confidence scores, tags, and timestamps
- Interactive knowledge graph visualization (D3.js / react-force-graph)
- Memory export and reset controls

**What is explicitly OUT of MEMORY scope:**
- Cross-user memory sharing — Phase 2
- Memory fine-tuning of base LLM — Phase 3
- Regulatory-grade audit trail of memory — Phase 2

---

### Module 6 — ORACLE LAYERS (10-Layer Intelligence Stack)
**Purpose:** Define the canonical 10-layer intelligence stack that powers all ORACLE reasoning. Every recommendation must be traceable to which layers activated and with what weight.

```
LAYER   NAME                    SOURCE                    UPDATE FREQ
─────────────────────────────────────────────────────────────────────
L1      Market Data             yfinance / Alpha Vantage  Real-time/1min
L2      Macro Signals           FRED API / manual feed    Daily
L3      News + Sentiment NLP    NewsAPI + FinBERT/GPT-4o  15 minutes
L4      Technical Indicators    Computed from L1          Real-time
L5      Polymarket Signals      Polymarket API            15 minutes
L6      Swarm Engine            MiroFish / OASIS          On-demand
L7      Multi-Agent Debate      LangChain agents          Per L6 run
L8      Risk Scoring            Custom engine             Per recommendation
L9      GraphRAG Memory         Neo4j / Zep Cloud         Per interaction
L10     Explanation Generator   GPT-4o                    Per recommendation
```

**Layer Activation Rules:**
- L1–L5 are always active (passive monitoring)
- L6 is triggered when: material signal detected in L1–L5, user requests swarm, Autopilot threshold hit
- L7 fires after every L6 completion
- L8 fires after every L7 consensus
- L9 is queried at start of every recommendation and updated after
- L10 fires last, synthesizing all layer outputs into human-readable explanation

---

### Module 7 — ORACLE WAR ROOM (Command Center Dashboard)
**Purpose:** The primary UI surface — a real-time command center showing portfolio status, active simulations, market signals, and the live transparency feed simultaneously.

**Core Capabilities:**
- Portfolio equity curve vs SPY benchmark
- Active position table with per-position ORACLE signal
- Live active swarm simulation panel with real-time progress
- Signal matrix showing all active L1–L5 signals with strength and confidence
- Layer status indicator (all 10 layers, health/activity state)
- Latest learning summary card
- Voice command bar (fixed bottom)
- Right-panel Transparency Feed (real-time, Supabase Realtime)
- Autopilot toggle and status

---

## 05 — MVP DEFINITION & PHASED ROADMAP

### MVP Definition (Hackathon Build)
**Target:** Fully demoable in 5 minutes, live in front of judges at the Amsterdam AI Broker Hackathon 2026.
**Scope:** All 7 modules at demo-grade quality, paper trading only, mock/seeded data for portfolio, real API calls for market data and LLM layers.

```
MODULE              MVP SCOPE                          OUT OF MVP
──────────────────────────────────────────────────────────────────────
SWARM               40-round sim, 3 agent types,       >1000 agents,
                    mock OASIS or live if time allows  agent learning
                    
VOICE               Hold-to-speak, Whisper, intent     Wake word,
                    routing, Web Speech API fallback   multi-turn conv.
                    
STRATEGY            NL parser, backtest 2020-2026,     Options,
                    equity curve, deploy to autopilot  multi-asset
                    
AUTOPILOT           Monitoring loop, auto-sim trigger, Real execution,
                    transparency feed, paper trades    cross-account
                    
MEMORY              Investor DNA, accuracy tracker,    Cross-user,
                    learning log, graph viz (mock)     LLM fine-tuning
                    
LAYERS              All 10 active, layer activation    Custom weights,
                    visible in every recommendation    live calibration
                    
WAR ROOM            Full dashboard, all panels,        Multi-portfolio,
                    realtime feed, voice bar           watchlists
```

### Phase 0 — Foundation (Pre-hackathon, done)
- Lovable UI shell (all 4 screens)
- Supabase project initialized (Frankfurt region)
- FastAPI backend scaffolded
- Mock data files created
- MiroFish fork configured

### Phase 1 — Hackathon MVP (Day of event)
- All 7 modules wired together
- Voice interface live
- Swarm simulation running (mock or live OASIS)
- Strategy builder with backtest
- Autopilot with transparency feed
- Demo script rehearsed x3

### Phase 2 — Post-Hackathon Depth (Month 1–3)
- Real user authentication (Supabase Auth)
- Live MedMij / broker API integration
- PSD2 transaction intercept (scam layer)
- Neo4j knowledge graph (persistent, live)
- Zep Cloud memory (multi-session)
- Offline OASIS simulation (MiroFish-Offline fork)
- Mobile responsive polish

### Phase 3 — Scale (Month 3–12)
- Multi-user platform
- Strategy marketplace (copy trading)
- Agent reputation system
- Institutional API (white-label)
- Regulatory framework (MiFID II alignment)
- External pentest + security audit

---

## 06 — ARCHITECTURE DECISION RECORDS (ADRs)

### ADR-001: Supabase as Primary Backend
**Decision:** Use Supabase (Frankfurt EU region) as the primary backend platform.
**Rationale:** EU data residency, PostgreSQL with RLS for access control, pgvector for similarity search, PostGIS-ready, real-time subscriptions (Transparency Feed), storage (signed URLs), Edge Functions (Deno) for privileged workflows, strong local dev tooling.
**Consequences:** Team must understand RLS; canonical RLS is in Addendum A; do not bypass RLS with service-role key in frontend code.
**Status:** Accepted.

### ADR-002: React + TypeScript + Lovable for Frontend
**Decision:** Use Lovable to generate the React/TypeScript frontend, with Tailwind CSS and Recharts.
**Rationale:** Hackathon speed; Lovable's 100-credit allowance enables full UI shell generation; React ecosystem has best financial charting support (Recharts); TypeScript enforces API contracts.
**Consequences:** Lovable output must be reviewed for RLS compliance; generated code must not use service-role keys; typegen from Supabase must be run after every migration.
**Status:** Accepted.

### ADR-003: Python FastAPI as Backend Service Layer
**Decision:** Use Python FastAPI as the primary backend service for all AI/ML workloads.
**Rationale:** Python has the best ecosystem for LangChain, MiroFish/OASIS, FinBERT, backtesting libraries (yfinance, pandas, numpy); FastAPI is async-first and OpenAPI-compatible; Supabase Edge Functions handle auth-sensitive workflows while FastAPI handles compute-heavy AI tasks.
**Consequences:** Two backend surfaces (FastAPI + Supabase Edge Functions) — clear separation required; see Section 10 for function routing.
**Status:** Accepted.

### ADR-004: MiroFish Fork as Swarm Engine
**Decision:** Fork the MiroFish open-source repository and modify it for financial seed inputs.
**Rationale:** MiroFish provides the full OASIS-backed simulation pipeline, GraphRAG seed extraction, and ReportAgent synthesis; forking allows customization of agent personas and financial seed parsers without waiting for upstream.
**Consequences:** Must track upstream MiroFish for security patches; financial persona definitions are ORACLE's primary IP layer on top of MiroFish; see Section 11 for fork modification spec.
**Status:** Accepted.

### ADR-005: LangChain for Agent Orchestration
**Decision:** Use LangChain (Python) for all multi-agent orchestration, tool-calling, and the Autopilot reasoning loop.
**Rationale:** LangChain has native tool-calling, agent loop, and memory integrations; well-documented for financial agent use cases; compatible with all target LLMs (GPT-4o, Qwen, local Ollama).
**Consequences:** LangChain version pinned in requirements.txt; breaking changes in LangChain v0.x are common — pin aggressively.
**Status:** Accepted.

### ADR-006: GPT-4o as Primary LLM, Qwen-plus as Simulation LLM
**Decision:** Use GPT-4o for all primary reasoning (strategy parsing, explanation generation, debate agents) and Qwen-plus (or GPT-4o-mini) for simulation agents to manage cost.
**Rationale:** A 40-round, 500-agent simulation can consume 2–4M tokens; using Qwen-plus at ~$0.0004/1K tokens vs GPT-4o at ~$0.01/1K tokens is a ~25x cost saving for the simulation layer while preserving quality for final reasoning.
**Consequences:** Two LLM provider credentials required; simulation LLM is configurable per run; see Addendum D for environment variable registry.
**Status:** Accepted.

### ADR-007: Polymarket API as Prediction Market Signal Layer (L5)
**Decision:** Integrate Polymarket API as Layer 5 of the intelligence stack.
**Rationale:** Polymarket provides real-money-backed probability estimates on macro events (rate decisions, elections, etc.); these probabilities are forward-looking and orthogonal to technical indicators; the Polymarket + swarm combination showed 74% accuracy in backtests.
**Consequences:** Polymarket API rate limits must be respected (15-min polling); fallback to cached values if API unavailable; prediction market data is informational only, not financial advice.
**Status:** Accepted.

### ADR-008: Paper Trading Only (No Real Execution)
**Decision:** ORACLE will execute paper trades only. No integration with real brokerage execution APIs in MVP.
**Rationale:** Regulatory (MiFID II, ESMA guidelines); hackathon scope; liability. Real execution requires licensed status in the Netherlands under Wft (Wet op het financieel toezicht).
**Consequences:** All "trade executed" events are simulation state changes in the database; Autopilot P&L is simulated; post-hackathon path to real execution requires legal/compliance review.
**Status:** Accepted. Do not override this in any Phase 1 code.

### ADR-009: Offline Mode via MiroFish-Offline Fork
**Decision:** Phase 2 will support a fully local/offline simulation mode using Ollama + Neo4j Community Edition.
**Rationale:** Institutional clients will not send financial signals to external APIs; privacy-first offline mode is a key enterprise differentiator and addresses GDPR data minimization.
**Consequences:** Phase 2 architecture addition; MVP assumes cloud LLMs; offline mode flag in config will be a no-op in Phase 1.
**Status:** Accepted for Phase 2. Not in MVP.

---

## 07 — SYSTEM ARCHITECTURE

### Container Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                          │
│                                                                   │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐  │
│  │   ORACLE Web App        │   │   ORACLE Mobile (Phase 2)   │  │
│  │   React + TypeScript    │   │   React Native / Expo       │  │
│  │   Lovable-generated     │   │                             │  │
│  │   Vercel deployment     │   │                             │  │
│  └────────────┬────────────┘   └─────────────────────────────┘  │
└───────────────┼─────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│                                                                   │
│  ┌──────────────────────┐   ┌──────────────────────────────┐    │
│  │  Supabase PostgREST  │   │  FastAPI (Python)            │    │
│  │  Auto-generated REST │   │  AI/ML compute workloads     │    │
│  │  from Postgres schema│   │  Railway / Render deploy     │    │
│  │  JWT auth enforced   │   │  Port 8000, /api/v1/*        │    │
│  └──────────┬───────────┘   └──────────────┬───────────────┘    │
└─────────────┼──────────────────────────────┼────────────────────┘
              │                              │
┌─────────────▼──────────────────────────────▼────────────────────┐
│                     SUPABASE PLATFORM (Frankfurt EU)             │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐   │
│  │  PostgreSQL  │  │ Supabase     │  │  Supabase Storage     │   │
│  │  + pgvector  │  │ Auth (JWT)   │  │  Private buckets only │   │
│  │  + pg_cron   │  │              │  │  Signed URLs          │   │
│  │  RLS on ALL  │  │              │  │                       │   │
│  │  tables      │  │              │  │                       │   │
│  └──────┬───────┘  └──────────────┘  └───────────────────────┘   │
│         │                                                         │
│  ┌──────▼────────────────────────────────────────────────────┐   │
│  │              Supabase Edge Functions (Deno)                │   │
│  │  /swarm-trigger  /autopilot-loop  /signal-ingest           │   │
│  │  /memory-update  /trade-execute  /report-generate          │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Supabase Realtime                           │    │
│  │  transparency_feed_events table → broadcast channel      │    │
│  │  simulation_state table → broadcast channel              │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    ORACLE AI ENGINE (FastAPI)                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                  ORACLE BRAIN                            │    │
│  │  LangChain Orchestrator                                  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │    │
│  │  │Bull Agent│ │Bear Agent│ │RiskAgent │ │ReprtAgent │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────────┘   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────┐   ┌──────────────────────────────┐      │
│  │  MiroFish Engine    │   │  Signal Pipeline              │      │
│  │  (forked OASIS)     │   │  L1: yfinance/AlphaVantage    │      │
│  │  500-1000 agents    │   │  L2: FRED API                 │      │
│  │  GraphRAG seed      │   │  L3: NewsAPI + FinBERT        │      │
│  │  ReportAgent synth  │   │  L4: Technical (pandas-ta)    │      │
│  └─────────────────────┘   │  L5: Polymarket API           │      │
│                             └──────────────────────────────┘      │
│                                                                   │
│  ┌─────────────────────┐   ┌──────────────────────────────┐      │
│  │  Memory Layer       │   │  Backtest Engine              │      │
│  │  Neo4j / Zep Cloud  │   │  pandas + numpy + yfinance    │      │
│  │  GraphRAG queries   │   │  Custom strategy runner       │      │
│  │  Embeddings store   │   │  Sharpe, Sortino, drawdown    │      │
│  └─────────────────────┘   └──────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│                                                                   │
│  OpenAI API (GPT-4o, Whisper, Embeddings)                        │
│  Qwen API (Simulation agents — cost-optimized)                   │
│  ElevenLabs API (TTS voice responses)                            │
│  Alpha Vantage API (market data — primary)                       │
│  yfinance (market data — fallback, no API key)                   │
│  NewsAPI (news feed — L3)                                        │
│  FRED API (macro data — L2)                                      │
│  Polymarket API (prediction market — L5)                         │
│  Zep Cloud (agent memory — Phase 1 option)                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 08 — DATABASE DESIGN & SCHEMA

### Schema Overview

```
SCHEMA              TABLES
────────────────────────────────────────────────────────────────
public              profiles, sessions
oracle_portfolio    portfolio_snapshots, positions, trades
oracle_simulation   simulations, simulation_rounds,
                    simulation_agents, simulation_reports
oracle_signals      signal_events, polymarket_snapshots,
                    news_events, technical_snapshots,
                    macro_snapshots
oracle_strategy     strategies, backtest_results,
                    backtest_trades, deployed_strategies
oracle_memory       memory_nodes, memory_edges,
                    investor_profiles, learning_log,
                    simulation_accuracy
oracle_autopilot    autopilot_sessions, autopilot_decisions,
                    autopilot_trades
oracle_feed         transparency_feed_events
oracle_audit        audit_log
```

---

### Table: `public.profiles`
```sql
CREATE TABLE public.profiles (
  id              uuid PRIMARY KEY REFERENCES auth.users(id),
  display_name    text NOT NULL,
  role            text NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user', 'analyst', 'system')),
  locale          text NOT NULL DEFAULT 'en',
  timezone        text NOT NULL DEFAULT 'Europe/Amsterdam',
  demo_mode       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

-- CANONICAL FIELD NAMES (see Addendum B):
-- id, display_name, role, locale, timezone, demo_mode
```

---

### Table: `oracle_portfolio.portfolio_snapshots`
```sql
CREATE TABLE oracle_portfolio.portfolio_snapshots (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  snapshot_at     timestamptz NOT NULL DEFAULT now(),
  total_value     numeric(18,4) NOT NULL,
  cash_balance    numeric(18,4) NOT NULL DEFAULT 0,
  invested_value  numeric(18,4) NOT NULL DEFAULT 0,
  daily_pnl       numeric(18,4),
  daily_pnl_pct   numeric(8,4),
  total_return    numeric(8,4),
  sharpe_ratio    numeric(8,4),
  benchmark_value numeric(18,4),  -- SPY comparison
  is_paper        boolean NOT NULL DEFAULT true,
  metadata        jsonb DEFAULT '{}'
);
```

---

### Table: `oracle_portfolio.positions`
```sql
CREATE TABLE oracle_portfolio.positions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  symbol          text NOT NULL,
  asset_class     text NOT NULL
                  CHECK (asset_class IN (
                    'equity', 'etf', 'crypto', 'bond', 'commodity'
                  )),
  quantity        numeric(18,8) NOT NULL,
  avg_entry_price numeric(18,4) NOT NULL,
  current_price   numeric(18,4),
  market_value    numeric(18,4),
  unrealized_pnl  numeric(18,4),
  unrealized_pct  numeric(8,4),
  oracle_signal   text CHECK (oracle_signal IN (
                    'BUY', 'SELL', 'HOLD', 'REDUCE', 'WATCH', NULL
                  )),
  signal_confidence numeric(5,4),
  signal_updated_at timestamptz,
  is_paper        boolean NOT NULL DEFAULT true,
  opened_at       timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_portfolio.trades`
```sql
CREATE TABLE oracle_portfolio.trades (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid NOT NULL REFERENCES public.profiles(id),
  position_id       uuid REFERENCES oracle_portfolio.positions(id),
  simulation_id     uuid,  -- FK to oracle_simulation.simulations
  strategy_id       uuid,  -- FK to oracle_strategy.strategies
  symbol            text NOT NULL,
  action            text NOT NULL
                    CHECK (action IN ('BUY', 'SELL', 'REBALANCE')),
  quantity          numeric(18,8) NOT NULL,
  price             numeric(18,4) NOT NULL,
  total_value       numeric(18,4) NOT NULL,
  reasoning         text,           -- L10 explanation
  layers_activated  text[],         -- e.g. ['L3','L5','L6','L7']
  layer_signals     jsonb,          -- per-layer signal details
  swarm_bullish_pct numeric(5,4),   -- L6 output at time of trade
  polymarket_prob   numeric(5,4),   -- L5 output at time of trade
  is_paper          boolean NOT NULL DEFAULT true,
  is_autopilot      boolean NOT NULL DEFAULT false,
  executed_at       timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_simulation.simulations`
```sql
CREATE TABLE oracle_simulation.simulations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  title           text NOT NULL,
  seed_text       text NOT NULL,
  seed_type       text CHECK (seed_type IN (
                    'news', 'earnings', 'macro', 'fed_statement',
                    'user_thesis', 'geopolitical', 'other'
                  )),
  status          text NOT NULL DEFAULT 'pending'
                  CHECK (status IN (
                    'pending', 'running', 'complete', 'failed'
                  )),
  agent_count     integer NOT NULL DEFAULT 500,
  round_count     integer NOT NULL DEFAULT 40,
  current_round   integer NOT NULL DEFAULT 0,
  agent_mix       jsonb NOT NULL DEFAULT
                  '{"institutional":35,"retail":50,"media":15}',
  llm_model       text NOT NULL DEFAULT 'gpt-4o-mini',
  environments    text[] NOT NULL DEFAULT ARRAY['twitter','reddit'],
  final_bullish   numeric(5,4),
  final_bearish   numeric(5,4),
  final_neutral   numeric(5,4),
  confidence      numeric(5,4),
  verdict         text CHECK (verdict IN (
                    'BULLISH', 'BEARISH', 'NEUTRAL', NULL
                  )),
  narrative       text,
  predicted_impact jsonb,  -- e.g. {"tech": -0.032, "bonds": 0.011}
  accuracy_verified boolean DEFAULT false,
  actual_outcome  text,    -- populated post-event
  tokens_used     integer,
  cost_usd        numeric(8,4),
  started_at      timestamptz,
  completed_at    timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_simulation.simulation_rounds`
```sql
CREATE TABLE oracle_simulation.simulation_rounds (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_id   uuid NOT NULL
                  REFERENCES oracle_simulation.simulations(id)
                  ON DELETE CASCADE,
  round_number    integer NOT NULL,
  bullish_pct     numeric(5,4),
  bearish_pct     numeric(5,4),
  neutral_pct     numeric(5,4),
  interactions    integer,
  opinion_shifts  integer,
  coalitions      integer,
  dominant_narrative text,
  agent_activity  jsonb,  -- per-archetype activity summary
  recorded_at     timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_simulation.simulation_reports`
```sql
CREATE TABLE oracle_simulation.simulation_reports (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_id   uuid NOT NULL UNIQUE
                  REFERENCES oracle_simulation.simulations(id)
                  ON DELETE CASCADE,
  verdict         text NOT NULL,
  confidence      numeric(5,4) NOT NULL,
  executive_summary text NOT NULL,
  narrative_themes  jsonb,    -- array of {theme, prevalence, agents}
  institutional_consensus text,
  retail_consensus    text,
  media_framing       text,
  predicted_impacts   jsonb,
  polymarket_corroboration jsonb,
  recommended_actions jsonb,  -- array of {action, asset, rationale}
  report_agent_reasoning text,
  generated_at    timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_signals.signal_events`
```sql
CREATE TABLE oracle_signals.signal_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  layer           text NOT NULL
                  CHECK (layer IN (
                    'L1','L2','L3','L4','L5','L6','L7',
                    'L8','L9','L10'
                  )),
  signal_type     text NOT NULL,
  asset           text,         -- NULL for macro/market-wide signals
  direction       text CHECK (direction IN (
                    'bullish','bearish','neutral','contrarian',NULL
                  )),
  strength        integer CHECK (strength BETWEEN 1 AND 5),
  confidence      numeric(5,4),
  raw_value       numeric(18,4),
  context         text,
  source_url      text,
  metadata        jsonb DEFAULT '{}',
  expires_at      timestamptz,
  detected_at     timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_strategy.strategies`
```sql
CREATE TABLE oracle_strategy.strategies (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  name            text NOT NULL,
  description     text,
  natural_language_input text NOT NULL,
  parsed_conditions jsonb NOT NULL,
  -- Structure: {
  --   entry: [{layer, condition, operator, threshold, asset}],
  --   exit:  [{layer, condition, operator, threshold}],
  --   risk:  {max_position_pct, stop_loss_pct, max_daily_trades}
  -- }
  asset_universe  text NOT NULL DEFAULT 'US_EQUITIES',
  layers_used     text[],
  version         integer NOT NULL DEFAULT 1,
  status          text NOT NULL DEFAULT 'draft'
                  CHECK (status IN (
                    'draft','backtested','deployed','archived'
                  )),
  is_public       boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_strategy.backtest_results`
```sql
CREATE TABLE oracle_strategy.backtest_results (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id     uuid NOT NULL
                  REFERENCES oracle_strategy.strategies(id)
                  ON DELETE CASCADE,
  start_date      date NOT NULL,
  end_date        date NOT NULL,
  initial_capital numeric(18,4) NOT NULL DEFAULT 100000,
  final_capital   numeric(18,4),
  total_return    numeric(8,4),
  benchmark_return numeric(8,4),   -- SPY over same period
  alpha           numeric(8,4),
  sharpe_ratio    numeric(8,4),
  sortino_ratio   numeric(8,4),
  max_drawdown    numeric(8,4),
  win_rate        numeric(5,4),
  profit_factor   numeric(8,4),
  total_trades    integer,
  swarms_triggered integer,
  layer_contribution jsonb,
  -- {L4: 0.22, L5: 0.28, L6: 0.42, L3: 0.08}
  equity_curve    jsonb,  -- array of {date, value, spy_value}
  monthly_returns jsonb,  -- array of {month, return}
  computed_at     timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_memory.investor_profiles`
```sql
CREATE TABLE oracle_memory.investor_profiles (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL UNIQUE
                  REFERENCES public.profiles(id),
  stated_risk     text CHECK (stated_risk IN (
                    'conservative','moderate','aggressive',NULL
                  )),
  revealed_risk   text CHECK (revealed_risk IN (
                    'conservative','moderate','aggressive',NULL
                  )),
  risk_discrepancy boolean GENERATED ALWAYS AS
                  (stated_risk IS DISTINCT FROM revealed_risk)
                  STORED,
  avg_hold_days   numeric(8,2),
  optimal_hold_days numeric(8,2),
  early_exit_count integer DEFAULT 0,
  contrarian_score numeric(5,4),
  macro_sensitivity numeric(5,4),
  best_signal_combo text,    -- e.g. 'L5+L6'
  worst_signal_combo text,
  active_personalizations jsonb DEFAULT '[]',
  -- [{rule, reason, applied_at, source_lesson}]
  radar_scores    jsonb,
  -- {risk_appetite, patience, conviction,
  --  diversification, momentum_bias, macro_awareness}
  last_updated    timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_memory.learning_log`
```sql
CREATE TABLE oracle_memory.learning_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  lesson_number   serial,
  lesson_text     text NOT NULL,
  confidence      integer NOT NULL DEFAULT 3
                  CHECK (confidence BETWEEN 1 AND 5),
  tags            text[] DEFAULT '{}',
  source_type     text CHECK (source_type IN (
                    'simulation_outcome','trade_result',
                    'behavior_pattern','signal_calibration'
                  )),
  source_id       uuid,   -- simulation_id or trade_id
  signal_combo    text,   -- e.g. 'L5+L6'
  validated       boolean DEFAULT false,
  times_applied   integer DEFAULT 0,
  learned_at      timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_memory.simulation_accuracy`
```sql
CREATE TABLE oracle_memory.simulation_accuracy (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  simulation_id   uuid NOT NULL UNIQUE
                  REFERENCES oracle_simulation.simulations(id),
  signal_combo    text,
  predicted_direction text,
  actual_direction    text,
  is_correct      boolean,
  confidence_at_prediction numeric(5,4),
  evaluated_at    timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_autopilot.autopilot_sessions`
```sql
CREATE TABLE oracle_autopilot.autopilot_sessions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  status          text NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active','paused','stopped')),
  paper_mode      boolean NOT NULL DEFAULT true,
  require_confirm_above numeric(18,4) DEFAULT 5000,
  max_daily_trades integer DEFAULT 5,
  scan_interval_seconds integer DEFAULT 300,
  deployed_strategy_ids uuid[],
  session_start   timestamptz NOT NULL DEFAULT now(),
  session_end     timestamptz,
  total_trades    integer DEFAULT 0,
  session_pnl     numeric(18,4) DEFAULT 0
);
```

---

### Table: `oracle_autopilot.autopilot_decisions`
```sql
CREATE TABLE oracle_autopilot.autopilot_decisions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      uuid NOT NULL
                  REFERENCES oracle_autopilot.autopilot_sessions(id),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  trigger_signal  text NOT NULL,
  trigger_layer   text NOT NULL,
  simulation_id   uuid,  -- if swarm was triggered
  bull_argument   text,
  bear_argument   text,
  risk_assessment text,
  consensus       text NOT NULL
                  CHECK (consensus IN (
                    'BUY','SELL','HOLD','REDUCE','REBALANCE'
                  )),
  consensus_confidence numeric(5,4),
  action_taken    text,
  reasoning_trail jsonb,  -- full step-by-step reasoning
  layers_activated text[],
  decided_at      timestamptz NOT NULL DEFAULT now()
);
```

---

### Table: `oracle_feed.transparency_feed_events`
```sql
CREATE TABLE oracle_feed.transparency_feed_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES public.profiles(id),
  session_id      uuid,
  event_type      text NOT NULL CHECK (event_type IN (
                    'data','simulation','action',
                    'risk_alert','learning','debate','system'
                  )),
  layer           text CHECK (layer IN (
                    'L1','L2','L3','L4','L5','L6',
                    'L7','L8','L9','L10',NULL
                  )),
  icon            text NOT NULL,  -- emoji
  title           text NOT NULL,
  detail          text,
  metadata        jsonb DEFAULT '{}',
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- Realtime enabled on this table:
-- ALTER TABLE oracle_feed.transparency_feed_events
--   REPLICA IDENTITY FULL;
```

---

### Table: `oracle_audit.audit_log`
```sql
CREATE TABLE oracle_audit.audit_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES public.profiles(id),
  action          text NOT NULL,
  resource_type   text NOT NULL,
  resource_id     uuid,
  sensitive_class text CHECK (sensitive_class IN (
                    'financial','simulation','memory',NULL
                  )),
  ip_address      inet,
  user_agent      text,
  metadata        jsonb DEFAULT '{}',
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- This table is append-only. No UPDATE or DELETE RLS policies.
```

---

## 09 — ROW LEVEL SECURITY (RLS) MODEL

> ⚠️ **CANONICAL RLS SOURCE IS ADDENDUM A.**
> The snippets below are **illustrative**. The authoritative policies are in Addendum A. If any conflict exists, Addendum A wins.

### RLS Philosophy
Every table in ORACLE has RLS enabled. The service-role key is used **only** in Edge Functions and the FastAPI backend via environment variables. The frontend client uses the anon key + JWT. No exceptions.

### Core Pattern (User-Scoped Tables)
```sql
-- Enable RLS on every table
ALTER TABLE oracle_portfolio.positions ENABLE ROW LEVEL SECURITY;

-- Users see only their own rows
CREATE POLICY "users_own_positions"
  ON oracle_portfolio.positions
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- System/autopilot can insert/update via service role
-- (service role bypasses RLS — used in Edge Functions only)
```

### Demo Mode Pattern
```sql
-- In demo mode (no auth), use a fixed demo_user_id
-- Set in Supabase project settings as an environment variable
-- All demo data is seeded under this ID
-- Frontend uses anon key only in demo mode
```

### Append-Only Audit Log
```sql
-- No user can UPDATE or DELETE audit_log rows
CREATE POLICY "audit_log_insert_only"
  ON oracle_audit.audit_log
  FOR INSERT
  WITH CHECK (true);

-- Users can only read their own audit rows
CREATE POLICY "audit_log_user_read"
  ON oracle_audit.audit_log
  FOR SELECT
  USING (auth.uid() = user_id);
```

### Realtime Security (Transparency Feed)
```sql
-- Users only subscribe to their own feed events
CREATE POLICY "feed_events_user_only"
  ON oracle_feed.transparency_feed_events
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

---

## 10 — EDGE FUNCTIONS & AGENTIC LOGIC

### Function Routing: Edge Functions vs FastAPI

```
WORKLOAD                        HANDLED BY
────────────────────────────────────────────────────────────
Auth-sensitive DB writes        Supabase Edge Functions (Deno)
(trades, decisions, feed events)

Heavy AI/ML compute             FastAPI (Python)
(simulation, backtest, NLP)

Real-time signal ingestion      FastAPI → Supabase via REST

Voice transcription             FastAPI (proxies Whisper API)

LLM reasoning chain             FastAPI (LangChain)

pg_cron scheduled jobs          Postgres (cron → Edge Function
                                 or SQL directly)
```

### Edge Function Specifications

#### `POST /functions/v1/swarm-trigger`
```
Purpose:    Validates simulation request, creates simulation
            record, calls FastAPI /api/v1/swarm/run,
            writes rounds to DB, finalizes simulation record
Input:      {seed_text, seed_type, agent_count, round_count,
             agent_mix, llm_model, environments}
Output:     {simulation_id, status}
Auth:       JWT (user) or service role (autopilot)
Writes to:  oracle_simulation.simulations
            oracle_feed.transparency_feed_events
```

#### `POST /functions/v1/autopilot-loop`
```
Purpose:    Called by pg_cron every N minutes when autopilot
            sessions are active. Fetches active sessions,
            reads latest L1-L5 signals, applies strategy
            conditions, triggers swarms if threshold met,
            calls FastAPI /api/v1/debate for consensus,
            executes paper trades, writes decisions + feed.
Input:      {} (no body — reads from DB)
Output:     {sessions_processed, decisions_made, trades_executed}
Auth:       Service role only
Writes to:  oracle_autopilot.autopilot_decisions
            oracle_portfolio.trades
            oracle_portfolio.positions
            oracle_feed.transparency_feed_events
            oracle_memory.learning_log
```

#### `POST /functions/v1/signal-ingest`
```
Purpose:    Receives signal data from FastAPI signal pipeline
            and writes to oracle_signals tables with proper
            classification and expiry
Input:      {layer, signal_type, asset, direction, strength,
             confidence, raw_value, context, metadata}
Output:     {signal_id, created}
Auth:       Service role only (called from FastAPI)
Writes to:  oracle_signals.signal_events
```

#### `POST /functions/v1/memory-update`
```
Purpose:    After every simulation or trade, extract lessons
            and update investor profile personalizations
Input:      {user_id, event_type, event_id, outcome_data}
Output:     {lessons_created, profile_updated}
Auth:       Service role only
Writes to:  oracle_memory.learning_log
            oracle_memory.investor_profiles
            oracle_memory.simulation_accuracy
```

#### `POST /functions/v1/trade-execute`
```
Purpose:    Paper-executes a trade decision. Validates position
            sizing rules, checks autopilot daily limits, writes
            trade record, updates position, emits feed event.
Input:      {user_id, symbol, action, quantity, price,
             decision_id, reasoning, layers_activated}
Output:     {trade_id, position_id, executed}
Auth:       Service role only
Writes to:  oracle_portfolio.trades
            oracle_portfolio.positions
            oracle_feed.transparency_feed_events
            oracle_audit.audit_log
```

---

## 11 — MIROFISH SWARM ENGINE INTEGRATION

### Fork Specification

**Upstream:** `github.com/[mirofish-repo]`
**ORACLE Fork:** `github.com/[your-org]/oracle-swarm`
**Branch strategy:** `main` = stable, `dev` = active, `upstream-sync` = tracking upstream

### Modifications to MiroFish for ORACLE

```
MODIFICATION                    LOCATION
────────────────────────────────────────────────────────────
1. Financial Agent Personas      /personas/financial/
   - InstitutionalTrader.yaml
   - RetailInvestor.yaml
   - FinancialJournalist.yaml
   - MacroEconomist.yaml
   - HedgeFundManager.yaml
   - PanicSeller.yaml (retail subtype)
   - MomentumChaser.yaml (retail subtype)
   - RiskOfficer.yaml (institutional subtype)

2. Financial Seed Parser         /seed/financial_parser.py
   Extracts: tickers, macro indicators, sentiment signals,
   event types, time horizons from financial text

3. Environment Configs           /environments/
   - twitter_financial.yaml
   - reddit_investing.yaml

4. ORACLE Report Template        /report/oracle_report.py
   Outputs structured JSON matching
   oracle_simulation.simulation_reports schema

5. Supabase Callback             /callbacks/supabase_writer.py
   Writes rounds + final report to Supabase in real-time
   (uses service role key via environment variable)

6. Cost Tracker                  /utils/cost_tracker.py
   Tracks tokens per model per run, writes to simulation
   record cost_usd field

7. Offline Mode Flag             /config/settings.py
   OFFLINE_MODE = False (Phase 2 activation point)
```

### Financial Agent Persona Schema (YAML)
```yaml
# Example: /personas/financial/RetailInvestor.yaml
name: RetailInvestor
archetype: retail
count_weight: 0.50  # proportion of agent pool
behavioral_traits:
  - loss_aversion: HIGH
  - herding_tendency: HIGH
  - news_reactivity: HIGH
  - fundamental_analysis: LOW
  - risk_tolerance: MODERATE
  - panic_threshold: 0.15  # 15% portfolio loss triggers panic
information_sources:
  - reddit_wsb
  - twitter_fintwit
  - cnbc_headlines
  - robinhood_app
vocabulary_biases:
  bullish_words: ["moon", "calls", "buy the dip", "diamond hands"]
  bearish_words: ["crash", "puts", "sell everything", "recession"]
simulation_behaviors:
  - follows_institutional_with_lag: 2-5 rounds
  - prone_to_overshooting: true
  - contrarian_signals_trigger_curiosity: true
```

### Simulation API Contract (FastAPI → MiroFish)
```python
# POST /api/v1/swarm/run
# Request body:
{
  "simulation_id": "uuid",
  "seed_text": "Fed signals two rate hikes...",
  "seed_type": "fed_statement",
  "agent_count": 500,
  "round_count": 40,
  "agent_mix": {"institutional": 35, "retail": 50, "media": 15},
  "llm_model": "qwen-plus",
  "environments": ["twitter", "reddit"],
  "callback_url": "https://[project].supabase.co/functions/v1/",
  "supabase_simulation_id": "uuid"
}

# Response (streamed, then final):
{
  "simulation_id": "uuid",
  "status": "complete",
  "rounds": [...],  # per-round summary objects
  "report": {
    "verdict": "BEARISH",
    "confidence": 0.71,
    "final_bullish": 0.25,
    "final_bearish": 0.63,
    "final_neutral": 0.12,
    "narrative": "Rate fear is overriding earnings optimism...",
    "predicted_impacts": {"tech": -0.032, "bonds": 0.011},
    "institutional_consensus": "...",
    "retail_consensus": "...",
    "recommended_actions": [...]
  },
  "tokens_used": 847293,
  "cost_usd": 0.34
}
```

---

## 12 — LLM LAYER & AGENT ORCHESTRATION

### LangChain Agent Architecture

```
ORACLE BRAIN (LangChain AgentExecutor)
│
├── INTENT ROUTER
│   Input: user voice/text command
│   Model: GPT-4o
│   Output: routes to one of 5 tools
│
├── TOOL: run_swarm_simulation
│   Calls: POST /api/v1/swarm/run
│
├── TOOL: query_portfolio
│   Calls: Supabase PostgREST + positions table
│
├── TOOL: build_strategy
│   Calls: POST /api/v1/strategy/parse + /backtest
│
├── TOOL: fetch_market_signals
│   Calls: Signal pipeline L1–L5
│
└── TOOL: generate_recommendation
    Calls: Debate agents (below) + L10 explanation
```

### Debate Agent Architecture (L7)
```
DEBATE SESSION (triggered after every L6 swarm)
│
├── BULL AGENT (GPT-4o)
│   System prompt: "You are an optimistic equity analyst.
│   Given the swarm results and market signals, construct
│   the strongest possible bullish argument. Be specific,
│   data-driven, and reference layer signals."
│   Input: swarm report + L1-L5 signals + memory context
│   Output: {argument, supporting_signals, confidence}
│
├── BEAR AGENT (GPT-4o)
│   System prompt: "You are a risk-focused portfolio manager.
│   Given the swarm results and market signals, construct
│   the strongest possible bearish/cautious argument..."
│   Input: same as Bull Agent
│   Output: {argument, supporting_signals, confidence}
│
├── RISK AGENT (GPT-4o)
│   System prompt: "You are a risk officer. Given the bull
│   and bear arguments, assess portfolio-level risk implications.
│   Output a risk score and position sizing recommendation."
│   Input: bull_argument + bear_argument + portfolio state
│   Output: {risk_score, position_sizing, max_exposure}
│
└── CONSENSUS SYNTHESIZER (GPT-4o)
    Input: all three agent outputs + swarm verdict
    Output: {
      consensus: "REDUCE",
      confidence: 0.74,
      reasoning: "...",
      recommended_action: {
        asset: "NVDA",
        action: "REDUCE",
        from_pct: 0.12,
        to_pct: 0.08,
        rationale: "..."
      }
    }
```

### L10 Explanation Generator
```python
# Every recommendation must pass through L10
# before reaching the user

EXPLANATION_PROMPT = """
You are ORACLE's explanation engine. Given a trading recommendation
and the full reasoning chain that produced it, generate a clear,
concise explanation for the user.

Requirements:
- Write in plain English, no jargon
- Explain WHICH layers activated and WHY they matter
- Quantify the key signals (e.g., "63% of simulated agents...")
- State what the recommendation is and why
- Acknowledge uncertainty honestly
- Never claim certainty about market outcomes
- End with what ORACLE will do if conditions change

Format: 2-3 sentences max for main explanation,
then bullet points for key factors.
"""
```

### Memory Integration (L9)
```python
# At start of every recommendation:
async def get_memory_context(user_id: str, query: str) -> dict:
    # 1. Vector similarity search on past simulations
    # 2. Fetch investor profile personalizations
    # 3. Get relevant learning log entries
    # 4. Return structured memory context
    return {
        "relevant_lessons": [...],
        "user_personalizations": [...],
        "similar_past_simulations": [...],
        "investor_risk_profile": {...}
    }

# After every recommendation:
async def update_memory(user_id: str, event: dict) -> None:
    # 1. Extract new entities for knowledge graph
    # 2. Check if new lesson should be recorded
    # 3. Update investor profile if behavioral pattern detected
    # 4. Update simulation accuracy if outcome is known
```

---

## 13 — MARKET DATA & SIGNAL PIPELINE

### L1 — Market Data
```python
# Primary: Alpha Vantage (requires API key)
# Fallback: yfinance (no API key, rate-limited)
# Pattern: prefer Alpha Vantage, auto-fallback to yfinance

SUPPORTED_ASSETS = {
  "equities": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN",
               "META", "TSLA", "JPM", "SPY", "QQQ"],
  "crypto": ["BTC-USD", "ETH-USD"],
  "bonds": ["TLT", "IEF", "SHY"],
  "volatility": ["VIX"]
}

DATA_FIELDS = ["open", "high", "low", "close", "volume",
               "adjusted_close"]
INTERVALS = ["1min", "5min", "15min", "1h", "1d"]
HISTORY_YEARS = 6  # 2020-2026 for backtest coverage
```

### L2 — Macro Signals
```python
# Source: FRED API (Federal Reserve Economic Data)
# Free tier, reliable, EU-accessible

MACRO_SERIES = {
  "fed_funds_rate": "FEDFUNDS",
  "10y_treasury": "DGS10",
  "2y_treasury": "DGS2",
  "yield_curve_spread": "T10Y2Y",
  "cpi_yoy": "CPIAUCSL",
  "unemployment": "UNRATE",
  "gdp_growth": "A191RL1Q225SBEA"
}

UPDATE_FREQUENCY = "daily"
```

### L3 — News & Sentiment NLP
```python
# Source: NewsAPI (financial category)
# Processing: FinBERT for financial sentiment
# Fallback: GPT-4o-mini sentiment analysis

TRACKED_TOPICS = ["Federal Reserve", "interest rates", "inflation",
                  "earnings", "NVDA", "tech sector", "recession",
                  "S&P 500", "bond yields"]

SENTIMENT_LABELS = ["positive", "negative", "neutral"]
FINBERT_MODEL = "ProsusAI/finbert"
ARTICLE_LIMIT = 100  # per 15-min cycle
```

### L4 — Technical Indicators
```python
# Library: pandas-ta
# Computed from L1 OHLCV data

INDICATORS = {
  "rsi": {"period": 14},
  "macd": {"fast": 12, "slow": 26, "signal": 9},
  "bollinger_bands": {"period": 20, "std": 2},
  "ema_20": {"period": 20},
  "ema_50": {"period": 50},
  "atr": {"period": 14},
  "volume_sma": {"period": 20}
}

SIGNAL_RULES = {
  "rsi_oversold": "RSI < 30 → bullish signal",
  "rsi_overbought": "RSI > 70 → bearish signal",
  "macd_cross_up": "MACD > Signal → bullish",
  "price_below_bb_lower": "Close < BB_lower → bullish",
  "above_ema50": "Close > EMA50 → trend bullish"
}
```

### L5 — Polymarket Integration
```python
# Source: Polymarket API (public, no auth required)
# Update frequency: 15 minutes
# Fallback: cached last known value (TTL: 1 hour)

TRACKED_MARKETS = [
  "Will the Fed raise rates at the next meeting?",
  "Will inflation exceed 3% this quarter?",
  "Will S&P 500 end month above current level?",
  "Will there be a US recession in 2026?"
]

# For each market:
FIELDS = ["market_id", "question", "yes_probability",
          "no_probability", "volume_24h", "last_updated"]
```

---

## 14 — VOICE INTERFACE ARCHITECTURE

### Voice Pipeline

```
USER HOLDS MIC BUTTON
        │
        ▼
BROWSER MediaRecorder API
(records audio as webm/opus)
        │
        ▼
POST /api/v1/voice/transcribe
(FastAPI receives audio blob)
        │
        ▼
OpenAI Whisper API
(transcription → text)
        │
        ▼
GPT-4o Intent Classifier
(classifies intent → tool selection)
│
├── "Run a swarm simulation on [X]"
│   → run_swarm_simulation(seed_text=X)
│
├── "What's my risk exposure?"
│   → query_portfolio(query="risk_exposure")
│
├── "Build a strategy that [X]"
│   → build_strategy(description=X)
│
├── "Rebalance my portfolio"
│   → generate_recommendation(type="rebalance")
│
└── "Activate/deactivate autopilot"
    → set_autopilot(status=true/false)
        │
        ▼
ORACLE MODULE EXECUTION
(returns structured response)
        │
        ▼
L10 Explanation Generator
(converts to conversational response text)
        │
        ▼
ElevenLabs TTS API
(response text → audio)
OR
Web Speech API (browser fallback)
        │
        ▼
AUDIO PLAYED TO USER
+ Response card rendered in UI
+ Layer activation pills shown
```

### Voice API Contracts

```python
# POST /api/v1/voice/transcribe
# Request: multipart/form-data with audio file
# Response:
{
  "transcript": "Run a swarm simulation on today's CPI report",
  "confidence": 0.97,
  "language": "en"
}

# POST /api/v1/voice/process
# Request:
{
  "transcript": "...",
  "user_id": "uuid",
  "session_context": {...}  # current portfolio state, active sims
}
# Response:
{
  "intent": "run_swarm_simulation",
  "parameters": {"seed_text": "..."},
  "response_text": "Launching a 500-agent swarm simulation...",
  "response_audio_url": "signed_url_to_audio",
  "layers_activated": ["L3", "L5", "L6"],
  "action_available": true,
  "action_label": "Execute Recommendation",
  "action_payload": {...}
}
```

---

## 15 — FRONTEND ARCHITECTURE

### Technology Stack
```
LAYER               TECHNOLOGY                  VERSION
───────────────────────────────────────────────────────
Framework           React                       18.x
Language            TypeScript                  5.x
Build tool          Vite (via Lovable)           5.x
Styling             Tailwind CSS                3.x
Animation           Framer Motion               11.x
Charts              Recharts                    2.x
Graph viz           react-force-graph           1.x
Routing             React Router                6.x
State               Zustand                     4.x
Server state        TanStack Query              5.x
Supabase client     @supabase/supabase-js       2.x
Forms               React Hook Form             7.x
Icons               Lucide React                0.x
Deployment          Vercel                      latest
```

### Route Structure
```
/                   War Room (Main Dashboard)
/swarm              Swarm Simulation Chamber
/swarm/:id          Simulation Detail View
/strategy           Strategy Builder
/strategy/:id       Strategy Detail + Backtest
/memory             Memory & Learning
/memory/graph       Full Knowledge Graph View
/settings           Settings (Phase 2)
```

### State Architecture (Zustand Stores)

```typescript
// stores/oracle.store.ts
interface OracleStore {
  // Autopilot
  autopilotActive: boolean
  autopilotSession: AutopilotSession | null
  setAutopilot: (active: boolean) => void

  // Active simulation
  activeSimulation: Simulation | null
  setActiveSimulation: (sim: Simulation | null) => void

  // Layer status
  layerStatus: Record<string, LayerStatus>
  updateLayerStatus: (layer: string, status: LayerStatus) => void

  // Voice
  voiceState: 'idle' | 'listening' | 'processing' | 'responding'
  setVoiceState: (state: VoiceState) => void

  // Transparency feed
  feedEvents: FeedEvent[]
  addFeedEvent: (event: FeedEvent) => void
  clearFeed: () => void

  // Demo mode
  isDemoMode: boolean
}
```

### Supabase Realtime Subscriptions
```typescript
// Transparency Feed — real-time updates
supabase
  .channel('transparency-feed')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'oracle_feed',
    table: 'transparency_feed_events',
    filter: `user_id=eq.${userId}`
  }, (payload) => {
    addFeedEvent(payload.new)
  })
  .subscribe()

// Simulation Progress — real-time round updates
supabase
  .channel('simulation-progress')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'oracle_simulation',
    table: 'simulation_rounds',
    filter: `simulation_id=eq.${activeSimulationId}`
  }, (payload) => {
    updateSimulationProgress(payload.new)
  })
  .subscribe()
```

### Type Generation
```bash
# Run after every DB migration — canonical types from schema
supabase gen types typescript --project-id [PROJECT_ID] \
  --schema public,oracle_portfolio,oracle_simulation,\
oracle_signals,oracle_strategy,oracle_memory,\
oracle_autopilot,oracle_feed,oracle_audit \
  > src/types/database.types.ts
```

---

## 16 — AUTHENTICATION & SESSION MODEL

### Hackathon MVP: Demo Mode (No Auth)
```typescript
// In demo mode:
// 1. No Supabase Auth required
// 2. Use fixed DEMO_USER_ID (seeded in DB)
// 3. All API calls use anon key
// 4. RLS policies have a demo bypass:
//    USING (user_id = 'DEMO_USER_ID'::uuid OR auth.uid() = user_id)

const DEMO_USER_ID = process.env.NEXT_PUBLIC_DEMO_USER_ID
```

### Post-Hackathon: Supabase Auth
```typescript
// Authentication flow (Phase 2):
// 1. Email + password OR magic link
// 2. JWT issued by Supabase Auth
// 3. JWT included in all API requests (Authorization header)
// 4. RLS enforces user_id = auth.uid() on all tables
// 5. Service role key NEVER exposed to frontend
```

---

## 17 — STORAGE MODEL

### Buckets (All Private — No Public Buckets)

```
BUCKET                  CONTENTS                  RETENTION
────────────────────────────────────────────────────────────
oracle-simulation-seeds Seed document uploads     90 days
oracle-reports          Generated PDF reports     1 year
oracle-exports          Strategy export files     30 days
oracle-voice-cache      TTS audio responses       24 hours
oracle-avatars          User profile photos       Indefinite
```

### Access Pattern
```typescript
// All file access via signed URLs (1-hour expiry for reads)
const { data } = await supabase
  .storage
  .from('oracle-reports')
  .createSignedUrl(`${userId}/${reportId}.pdf`, 3600)

// Never use public URLs
// Never use download with token in URL params (use Authorization header)
```

---

## 18 — SCHEDULED JOBS (pg_cron)

```sql
-- Autopilot monitoring loop (every 5 minutes)
SELECT cron.schedule(
  'autopilot-loop',
  '*/5 * * * *',
  $$SELECT net.http_post(
    url := current_setting('app.supabase_functions_url')
           || '/autopilot-loop',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || 
      current_setting('app.service_role_key')
    )
  )$$
);

-- Signal pipeline refresh (every 15 minutes)
SELECT cron.schedule(
  'signal-refresh',
  '*/15 * * * *',
  $$SELECT net.http_post(
    url := current_setting('app.fastapi_url') 
           || '/api/v1/signals/refresh'
  )$$
);

-- Voice cache cleanup (daily at 3am UTC)
SELECT cron.schedule(
  'voice-cache-cleanup',
  '0 3 * * *',
  $$
  DELETE FROM storage.objects
  WHERE bucket_id = 'oracle-voice-cache'
  AND created_at < now() - interval '24 hours'
  $$
);

-- Simulation accuracy evaluation (daily at 4am UTC)
-- Checks simulations from 5 days ago against actual prices
SELECT cron.schedule(
  'accuracy-evaluation',
  '0 4 * * *',
  $$
  -- For each unverified simulation older than 5 days,
  -- fetch actual price outcome and update accuracy record
  SELECT net.http_post(
    url := current_setting('app.fastapi_url') 
           || '/api/v1/accuracy/evaluate'
  )$$
);

-- Portfolio snapshot (daily at market close, 5pm UTC)
SELECT cron.schedule(
  'portfolio-snapshot',
  '0 17 * * 1-5',  -- weekdays only
  $$
  INSERT INTO oracle_portfolio.portfolio_snapshots
    (user_id, total_value, ...)
  SELECT user_id, SUM(market_value), ...
  FROM oracle_portfolio.positions
  GROUP BY user_id
  $$
);

-- Transparency feed cleanup (weekly Sunday 2am UTC)
SELECT cron.schedule(
  'feed-cleanup',
  '0 2 * * 0',
  $$
  DELETE FROM oracle_feed.transparency_feed_events
  WHERE created_at < now() - interval '30 days'
  $$
);
```

---

## 19 — SECURITY & COMPLIANCE

### Security Principles
```
PRINCIPLE                   IMPLEMENTATION
────────────────────────────────────────────────────────────
RLS on every table          Enforced; no exceptions
No service role in frontend Never expose SUPABASE_SERVICE_ROLE_KEY
                            to browser; Edge Functions only
No PII in logs              Logs contain user_id (UUID), not names
                            or email addresses
Signed URLs only            No public storage access
Secrets in env vars         Never hardcode API keys in code
HTTPS only                  All API communication TLS 1.2+
CORS restricted             FastAPI CORS whitelist = 
                            Vercel domain only
Rate limiting               FastAPI: 100 req/min per IP
                            Supabase: default limits
Input sanitization          All text inputs sanitized before
                            LLM prompts (prompt injection defense)
```

### Data Classification
```
CLASS       EXAMPLES                    CONTROLS
────────────────────────────────────────────────────────────
PUBLIC      Market prices, signals,     No special controls
            simulation verdicts

PRIVATE     Portfolio positions,        RLS user-scoped,
            trade history               audit log

SENSITIVE   Investor profile,           RLS + audit log +
            behavioral data             explicit consent UI

SYSTEM      Service role keys,          Env vars only,
            API credentials             never in DB
```

### Hard Security Rules
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

### GDPR / AVG Compliance (Netherlands/EU)
```
OBLIGATION          IMPLEMENTATION
────────────────────────────────────────────────────────────
Data minimization   Only collect data needed for ORACLE function
Purpose limitation  Data used only for investment recommendations
Storage limitation  Retention cron jobs (see Section 18)
User rights         Memory reset button in UI (right to erasure)
Data portability    Strategy export (JSON/PDF)
Consent             Demo mode = implicit; auth mode = explicit
                    consent on registration
Transparency        Full reasoning trail visible for every decision
```

---

## 20 — OBSERVABILITY & MONITORING

### Logging Architecture
```python
# FastAPI structured logging
import structlog

logger = structlog.get_logger()

# Log format: JSON, never log PII
logger.info("swarm_simulation_started",
  simulation_id=sim_id,
  agent_count=500,
  round_count=40,
  llm_model="qwen-plus",
  # NEVER log: seed_text, user_id in plain, API keys
)
```

### Key Metrics to Track
```
METRIC                          ALERT THRESHOLD
────────────────────────────────────────────────────────────
Simulation completion rate      < 95% → alert
Average simulation time         > 120s → alert
LLM API error rate              > 5% → alert
Supabase connection errors      > 0 → alert (Railway restart)
Signal pipeline freshness       > 20 min stale → alert
Autopilot decision latency      > 30s → alert
Frontend load time              > 3s → investigate
Realtime subscription drops     > 0 → reconnect + alert
```

### Health Check Endpoints
```python
# FastAPI health check (for Railway deployment)
GET /health
Response: {
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "supabase": "connected",
    "openai": "connected",
    "alpha_vantage": "connected",
    "polymarket": "connected",
    "mirofish": "ready"
  },
  "timestamp": "2026-06-13T..."
}
```

---

## 21 — DEVELOPER WORKFLOW & CI/CD

### Monorepo Structure
```
oracle/
├── apps/
│   ├── web/                    # Lovable-generated React app
│   │   ├── src/
│   │   │   ├── components/     # UI components
│   │   │   ├── pages/          # Route pages
│   │   │   ├── stores/         # Zustand stores
│   │   │   ├── hooks/          # Custom hooks
│   │   │   ├── types/          # TypeScript types
│   │   │   │   └── database.types.ts  # Supabase generated
│   │   │   └── lib/            # Utility functions
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── api/                    # FastAPI Python backend
│       ├── main.py             # FastAPI app entry
│       ├── routers/            # Route modules
│       │   ├── swarm.py        # /api/v1/swarm/*
│       │   ├── voice.py        # /api/v1/voice/*
│       │   ├── strategy.py     # /api/v1/strategy/*
│       │   ├── signals.py      # /api/v1/signals/*
│       │   ├── accuracy.py     # /api/v1/accuracy/*
│       │   └── health.py       # /health
│       ├── services/           # Business logic
│       │   ├── mirofish.py     # MiroFish wrapper
│       │   ├── langchain_brain.py  # LangChain agents
│       │   ├── backtest.py     # Backtest engine
│       │   ├── memory.py       # Memory layer
│       │   └── signals/        # L1-L5 pipelines
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/
│   ├── shared-types/           # Shared TypeScript types
│   └── mock-data/              # Demo seed data
│
├── supabase/
│   ├── migrations/             # SQL migration files
│   │   └── 20260613_initial.sql
│   ├── seed.sql                # Demo data seed
│   ├── functions/              # Edge Functions (Deno)
│   │   ├── swarm-trigger/
│   │   ├── autopilot-loop/
│   │   ├── signal-ingest/
│   │   ├── memory-update/
│   │   └── trade-execute/
│   └── config.toml
│
├── oracle-swarm/               # MiroFish fork (git submodule)
│
├── .env.example                # Template (see Addendum D)
├── .env.local                  # Local secrets (gitignored)
├── pnpm-workspace.yaml
├── package.json
└── README.md
```

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: ORACLE CI

on: [push, pull_request]

jobs:
  # 1. Type safety
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm --filter web typecheck

  # 2. Python tests
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -r apps/api/requirements.txt
      - run: pytest apps/api/tests/

  # 3. RLS policy tests
  rls-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase start
      - run: supabase db reset
      - run: pnpm run test:rls  # pgTAP tests

  # 4. Deploy to Vercel (frontend) — on main only
  deploy-frontend:
    needs: [typecheck, rls-tests]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: vercel deploy --prod

  # 5. Deploy to Railway (API) — on main only
  deploy-api:
    needs: [api-tests]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: railway up --service oracle-api
```

---

## 22 — LOCAL SETUP & RUNBOOK

### Prerequisites
```bash
# Required
node >= 20.x
pnpm >= 9.x
python >= 3.12
docker desktop (for Supabase local)
supabase CLI >= 1.x

# Install Supabase CLI
brew install supabase/tap/supabase

# Install Railway CLI (for API deployment)
npm install -g @railway/cli
```

### Step-by-Step Setup
```bash
# 1. Clone the repo
git clone https://github.com/[your-org]/oracle.git
cd oracle
git submodule update --init --recursive  # MiroFish fork

# 2. Install dependencies
pnpm install
pip install -r apps/api/requirements.txt

# 3. Copy environment variables
cp .env.example .env.local
# → Open .env.local and fill in all values (see Addendum D)

# 4. Start Supabase locally
supabase start
# Note the API URL and anon key printed — copy to .env.local

# 5. Run database migrations + seed demo data
supabase db reset  # applies all migrations + seed.sql

# 6. Generate TypeScript types from schema
supabase gen types typescript --local \
  > apps/web/src/types/database.types.ts

# 7. Serve Edge Functions locally
supabase functions serve

# 8. Start FastAPI backend
cd apps/api
uvicorn main:app --reload --port 8000

# 9. Start React frontend
cd apps/web
pnpm dev
# → Opens on http://localhost:5173

# 10. Run MiroFish engine test
cd oracle-swarm
python test_simulation.py --seed "Fed raises rates by 50bps" \
  --agents 100 --rounds 10
```

### Verify Setup
```bash
# All of these should return success:
curl http://localhost:8000/health          # FastAPI health
curl http://localhost:54321/rest/v1/       # Supabase PostgREST
open http://localhost:5173                 # React app
# → Should show War Room with mock data populated
```

---

## 23 — DEMO MODE & HACKATHON CHECKLIST

### Demo Data Seed
```sql
-- seed.sql provides:
-- 1. Demo user profile (DEMO_USER_ID)
-- 2. 5 seeded portfolio positions (NVDA, AAPL, SPY, BTC, TLT)
-- 3. 90 days of portfolio snapshots for equity curve
-- 4. 47 past simulations with accuracy records
-- 5. 47 learning log entries
-- 6. Investor DNA profile (populated)
-- 7. 8 saved strategies with backtest results
-- 8. Signal events across all 5 layers (last 24 hours)
-- 9. 100 transparency feed events (last session)
-- 10. Knowledge graph nodes (50 assets, 20 events, 10 strategies)
```

### Autopilot Demo Auto-Fire
```typescript
// In demo mode, transparency feed fires automatically
// every 3-7 seconds to simulate a live running session
// This is the most visually impressive part of the demo

const DEMO_FEED_SEQUENCE = [
  {icon: "📡", layer: "L1", title: "Market data synced", 
   detail: "847 assets updated"},
  {icon: "📰", layer: "L3", title: "Breaking signal detected",
   detail: "Fed signals hold on rates — Reuters"},
  {icon: "📊", layer: "L5", title: "Polymarket update",
   detail: "Rate hold probability: 71%"},
  {icon: "🌊", layer: "L6", title: "Swarm simulation launching",
   detail: "500 agents initializing..."},
  {icon: "🌊", layer: "L6", title: "Simulation in progress",
   detail: "Round 20/40 — 63% bearish emerging"},
  {icon: "🌊", layer: "L6", title: "Swarm complete",
   detail: "Verdict: BEARISH (71% confidence)"},
  {icon: "🤖", layer: "L7", title: "Bull Agent argument",
   detail: "Momentum still intact — NVDA RSI oversold"},
  {icon: "🤖", layer: "L7", title: "Bear Agent argument",
   detail: "Yield curve inversion + rate fear dominant"},
  {icon: "⚖️", layer: "L8", title: "Risk assessment",
   detail: "Portfolio risk: ELEVATED on tech sector"},
  {icon: "✅", layer: "L10", title: "Action executed",
   detail: "Reduced NVDA: 12% → 8% of portfolio"},
  {icon: "📚", layer: "L9", title: "Lesson learned",
   detail: "Lesson #48: Polymarket >70% + bearish swarm → reduce"}
]
```

### Hackathon Day Checklist
```
PRE-DEMO (30 minutes before)
□ Open ORACLE on demo machine — check all 4 screens load
□ Verify transparency feed is auto-firing
□ Test voice button — confirm microphone works
□ Load swarm simulation screen — confirm animation runs
□ Test strategy builder with "Buy NVDA when RSI < 30 
  AND swarm bullish > 60%" — confirm backtest loads
□ Activate Autopilot — confirm modal + feed fires
□ Confirm all mock data looks realistic
□ Battery: laptop plugged in
□ Browser: Chrome, fullscreen, zoom at 90%
□ Backup: Loom recording of full demo ready as fallback

DEMO SCRIPT (5 minutes)
□ [0:00] Hook — "We simulate the humans that move markets"
□ [0:30] Paste Fed statement → Run Swarm → show live agents
□ [1:30] Voice command → "What should I do with tech?"
□ [2:30] Strategy builder → type strategy → show backtest
□ [3:30] Flip Autopilot → show transparency feed live
□ [4:30] Close → "This is what Robinhood will look like 
         in 3 years, built for institutional quant clients"

POST-DEMO
□ Share GitHub link with judges
□ Share Vercel deployment URL
□ Share this design doc (redact API keys)
```

---

## 24 — GLOSSARY

```
TERM                DEFINITION
────────────────────────────────────────────────────────────
OASIS               Open Agent Social Interaction Simulations
                    (CAMEL-AI) — the underlying simulation
                    engine MiroFish is built on top of

MiroFish            Open-source AI prediction engine that uses
                    OASIS to simulate social consensus. ORACLE
                    forks MiroFish and adds financial personas.

GraphRAG            Graph-based Retrieval Augmented Generation.
                    Used to extract structured knowledge from
                    seed text and build the knowledge graph.

ReportAgent         The final synthesis agent in MiroFish that
                    reads simulation outcomes and produces a
                    structured prediction report.

Oracle Report       The structured output of an ORACLE swarm
                    simulation. Contains verdict, confidence,
                    narrative themes, predicted impacts, and
                    recommended actions.

L1–L10              The 10 intelligence layers of the ORACLE
                    brain. Each layer has a specific data source
                    and signal type. See Section 04, Module 6.

Transparency Feed   The live scrolling log of every reasoning
                    step ORACLE takes. Powered by Supabase
                    Realtime on transparency_feed_events.

Investor DNA        ORACLE's behavioral profile of a user,
                    derived from revealed behavior rather than
                    stated preferences. Stored in
                    oracle_memory.investor_profiles.

Paper Trading       Simulated trade execution with no real money.
                    All ORACLE trades in MVP are paper trades.

SSOT                Single Source of Truth — this document.
                    All conflicts resolved by this document.

RLS                 Row Level Security — PostgreSQL feature
                    enforcing data access at the database layer.
                    Canonical RLS policies in Addendum A.

Swarm               A single MiroFish simulation run. Produces
                    one Oracle Report. May involve 100–1,000
                    agents across 10–40 rounds.

Debate Session      The L7 process where Bull Agent, Bear Agent,
                    and Risk Agent argue over swarm results to
                    produce a consensus trading recommendation.

Autopilot           ORACLE's autonomous trading mode. Monitors
                    L1–L5 continuously, triggers swarms, runs
                    debates, and executes paper trades without
                    user prompts.

Alpha               Risk-adjusted outperformance vs benchmark
                    (SPY). Strategy alpha = strategy return -
                    SPY return, adjusted for risk.

Polymarket          Prediction market platform. ORACLE uses
                    Polymarket probabilities as L5 signals.

FinBERT             Financial domain-specific BERT model for
                    sentiment analysis of financial text.
                    Used in L3 news processing pipeline.
```

---

## 25 — OPEN QUESTIONS & HUMAN ACTION ITEMS

```
ITEM    OWNER     PRIORITY    DESCRIPTION
────────────────────────────────────────────────────────────
HQ-001  Lead Dev  BLOCKER     Obtain all API keys (OpenAI,
                              Alpha Vantage, NewsAPI, 
                              ElevenLabs, Polymarket, FRED)
                              and populate .env.local
                              
HQ-002  Lead Dev  BLOCKER     Initialize Supabase project
                              in Frankfurt region and copy
                              project URL + anon key to env

HQ-003  Lead Dev  BLOCKER     Test MiroFish fork locally with
                              a financial seed — verify output
                              matches oracle_simulation schema
                              before hackathon day

HQ-004  Lead Dev  HIGH        Decide: Zep Cloud vs Neo4j
                              Community for memory layer.
                              Zep Cloud = faster to set up,
                              Neo4j = more control.
                              Recommendation: Zep Cloud for MVP

HQ-005  Lead Dev  HIGH        Decide: ElevenLabs vs Web Speech
                              API for TTS. ElevenLabs = better
                              voice quality. Web Speech = free,
                              no API key. Recommendation: 
                              Web Speech for hackathon,
                              ElevenLabs post-hackathon

HQ-006  Team      HIGH        Rehearse the 5-minute demo script
                              at least 3 times before judges.
                              Timing is critical.

HQ-007  Lead Dev  MEDIUM      Verify Polymarket API is
                              accessible from EU region (some
                              geo-restrictions reported)

HQ-008  Lead Dev  MEDIUM      Set up Railway deployment for
                              FastAPI backend before hackathon
                              day — don't rely on localhost
                              during demo

HQ-009  Team      LOW         Post-hackathon: legal review of
                              operating an agentic trading
                              platform in the Netherlands
                              under Wft (Wet op het financieel
                              toezicht)

HQ-010  Team      LOW         Post-hackathon: formal GDPR/AVG
                              compliance review if ORACLE
                              handles real user financial data
```

---

## ADDENDUM A — CANONICAL RLS POLICIES
*(Full RLS policy SQL lives here. Illustrative snippets in Section 09.)*
`Status: To be written in supabase/migrations/rls_policies.sql`

## ADDENDUM B — CANONICAL FIELD NAME REFERENCE
*(If any migration, type, or API contract uses a different field name than defined here, update that artifact.)*
`Status: To be written — extract from Section 08 DDL`

## ADDENDUM C — API CONTRACT DEFINITIONS
*(Full OpenAPI/JSON Schema definitions for all FastAPI endpoints.)*
`Status: Auto-generated from FastAPI — run: python -m apps.api.main > openapi.json`

## ADDENDUM D — ENVIRONMENT VARIABLE REGISTRY
```bash
# .env.example — copy to .env.local and fill all values

# Supabase (Frankfurt EU)
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Edge Functions + FastAPI only
SUPABASE_JWT_SECRET=...

# LLM Providers
OPENAI_API_KEY=sk-...             # GPT-4o + Whisper + Embeddings
QWEN_API_KEY=...                  # Simulation agents (cost saving)

# Market Data
ALPHA_VANTAGE_API_KEY=...         # L1 primary market data
FRED_API_KEY=...                  # L2 macro signals

# News & Prediction Markets
NEWS_API_KEY=...                  # L3 news feed
POLYMARKET_API_URL=https://gamma-api.polymarket.com  # L5 (no key)

# Voice
ELEVENLABS_API_KEY=...            # TTS voice (Phase 2)

# Memory
ZEP_API_KEY=...                   # Zep Cloud memory (or local)
ZEP_API_URL=https://api.getzep.com

# Demo Mode
NEXT_PUBLIC_DEMO_USER_ID=...      # Fixed UUID for demo mode
NEXT_PUBLIC_DEMO_MODE=true        # Enable demo bypass

# FastAPI
FASTAPI_URL=https://oracle-api.railway.app  # Production
FASTAPI_URL_LOCAL=http://localhost:8000      # Local dev
FASTAPI_SECRET_KEY=...            # For internal service auth

# Deployment
VERCEL_PROJECT_ID=...
RAILWAY_PROJECT_ID=...

# Feature Flags
ORACLE_OFFLINE_MODE=false         # Phase 2 activation
ORACLE_MAX_AGENTS=1000            # Simulation cap
ORACLE_MAX_ROUNDS=40              # Simulation round cap
ORACLE_SIGNAL_REFRESH_MINUTES=15  # L1-L5 refresh interval
```

---

*ORACLE Design Suite v1.0.0 — Last updated 2026-06-13*
*Next version bump required for: any architectural change, new module addition, schema modification, or ADR addition.*
*All conflicts with this document resolved in favor of this document.*
