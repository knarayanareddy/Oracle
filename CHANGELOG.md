# 📋 ORACLE — Changelog

> **Navigation:** [← Back to README](README.md)

All notable changes to ORACLE are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] — 2026-06-13

### Added — Initial Release

#### 7 Modules
- 🌊 **Swarm Engine**: 100–1,000 AI agent simulation with opinion dynamics, herding
  amplification, and emergent consensus extraction
- 🎙️ **Voice Interface**: Hold-to-speak with Whisper transcription, intent routing via
  LangChain, and Web Speech API TTS fallback
- ✨ **Strategy Builder**: Plain English → structured conditions → historical backtest
  with Sharpe, Sortino, max drawdown, alpha, layer contribution
- 🤖 **Autopilot**: Autonomous monitoring loop, auto-swarm trigger, multi-agent debate,
  paper trade execution with transparency feed
- 🧠 **GraphRAG Memory**: pgvector semantic search (HNSW index), entity extraction,
  knowledge graph ingestion, Investor DNA profiling, right-to-erasure
- 🧩 **10-Layer Intelligence Stack**: L1–L10 with activation rules and weighted contributions
- 📊 **War Room**: Real-time command center with equity curve, positions, signal matrix,
  layer status, live transparency feed

#### Backend (FastAPI)
- 12 API endpoints: swarm, voice, strategy, signals, recommendations, accuracy, health
- 5 signal providers (L1–L5): yfinance/Polygon/AlphaVantage, FRED, NewsAPI, pandas-ta, Polymarket
- MiroFish swarm engine wrapper with deterministic mock fallback
- LangChain multi-agent debate (Bull/Bear/Risk/Consensus) with circuit breaker
- Backtest engine with RSI, MACD, Bollinger, EMA indicators
- Market data provider chain: Polygon → AlphaVantage → yfinance with automatic failover
- pgvector GraphRAG with OpenAI embeddings (text-embedding-3-small, 1536-dim)
- Circuit breaker + retry layer for all external calls (4 breakers)
- Runtime security guards (leak detection, config validation)
- Structured JSON logging (structlog)
- Rate limiting (100 req/min per IP)
- Service-to-service auth (X-Oracle-Secret)

#### Database (Supabase PostgreSQL)
- 8 schemas, 25 tables across portfolio, simulation, signals, strategy, memory, autopilot, feed, audit
- RLS enabled on every table with user-scoped policies
- Demo mode bypass for hackathon (fixed DEMO_USER_ID)
- pgvector HNSW index + match_memory_nodes + get_memory_subgraph RPCs
- pg_cron scheduled jobs (6 jobs: autopilot, signals, cleanup, snapshots, accuracy)
- 5 private storage buckets with signed URL access
- Append-only audit log (no UPDATE/DELETE)
- Realtime broadcast on transparency_feed_events, simulation_rounds, trades

#### Edge Functions (Deno)
- `swarm-trigger`: validates, creates record, calls FastAPI, streams rounds
- `autopilot-loop`: monitors signals, triggers swarms, runs debates, executes trades
- `signal-ingest`: batch signal insertion from FastAPI pipeline
- `memory-update`: lesson extraction, profile updates, accuracy tracking
- `trade-execute`: paper trade with position sizing validation + audit log

#### Frontend (React)
- 4 pages: War Room, Swarm Chamber, Strategy Builder, Memory & Learning
- TopBar with autopilot toggle + 10-layer status dots
- VoiceBar with hold-to-speak, waveform, text fallback, suggested commands
- Transparency Feed with Supabase Realtime subscription + demo auto-fire
- Zustand global state with demo feed sequence
- Tailwind institutional dark theme with Recharts visualizations
- Framer Motion animations
- TypeScript strict mode, canonical types

#### Swarm Engine Fork (oracle-swarm)
- 8 financial agent personas (YAML): Institutional Trader, Retail Investor, Financial
  Journalist, Hedge Fund Manager, Panic Seller, Momentum Chaser, Macro Economist, Risk Officer
- Financial seed parser (entity extraction → GraphRAG nodes)
- Supabase real-time callback writer
- Cost tracker with per-model pricing

#### DevOps
- CI/CD pipeline: security scan → typecheck → tests → deploy (Vercel + Railway)
- Security scan script (blocks service key leakage)
- Docker Compose for local dev
- Dockerfile for FastAPI (multi-stage, Railway-compatible)
- Vercel deployment config
- pnpm workspace monorepo

#### Documentation
- Comprehensive README with navigation hub
- Architecture deep dive (ADRs, data flows, resilience model)
- API reference (12 endpoints + 5 Edge Functions)
- Database guide (schema, RLS, GraphRAG, cron)
- Deployment guide (Supabase + Railway + Vercel)
- Demo guide (5-minute script + checklist + fallbacks)
- Security model (threat model, GDPR, key isolation)
- Development guide (setup, testing, debugging, codebase tour)
- Contributing guide

#### Testing
- 40 Python tests (resilience, GraphRAG, market data, security, API)
- pgTAP RLS policy tests
- TypeScript strict type checking
- CI security scan

### Security
- RLS on all 25 tables
- Service role key isolation (never in frontend)
- Runtime leak guard middleware
- CI security scan gate
- GDPR/AVG compliance (EU residency, right-to-erasure)
- Paper trading only (ADR-008)

---

## Roadmap (Future Phases)

### Phase 2 — Post-Hackathon Depth (Month 1–3)
- [ ] Real user authentication (Supabase Auth)
- [ ] Live broker API integration
- [ ] Neo4j persistent knowledge graph
- [ ] Zep Cloud multi-session memory
- [ ] Offline OASIS simulation (MiroFish-Offline fork)
- [ ] Mobile responsive polish
- [ ] ElevenLabs TTS integration
- [ ] Remove demo mode bypass

### Phase 3 — Scale (Month 3–12)
- [ ] Multi-user platform
- [ ] Strategy marketplace (copy trading)
- [ ] Agent reputation system
- [ ] Institutional API (white-label)
- [ ] Regulatory framework (MiFID II alignment)
- [ ] External pentest + security audit

---

> **← Back to README** | [Design Doc (SSOT)](https://github.com/knarayanareddy/Oracle/blob/main/Oracledesigndoc.md)
