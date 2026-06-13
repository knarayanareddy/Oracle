# 🗄️ ORACLE — Database Guide

> **Navigation:** [← Back to README](../README.md) | [Architecture](ARCHITECTURE.md) | [API Reference](API_REFERENCE.md)

Complete reference for the PostgreSQL schema, Row Level Security (RLS) model,
pgvector GraphRAG, and pg_cron scheduled jobs.

---

## Table of Contents

1. [Schema Overview](#1-schema-overview)
2. [Schema Reference](#2-schema-reference)
3. [Row Level Security (RLS)](#3-row-level-security-rls)
4. [GraphRAG Vector Search](#4-graphrag-vector-search)
5. [Scheduled Jobs (pg_cron)](#5-scheduled-jobs-pg_cron)
6. [Migrations](#6-migrations)
7. [Seed Data](#7-seed-data)

---

## 1. Schema Overview

ORACLE uses **8 PostgreSQL schemas** organized by domain:

```
public              profiles, sessions
oracle_portfolio    portfolio_snapshots, positions, trades
oracle_simulation   simulations, simulation_rounds, simulation_reports
oracle_signals      signal_events, polymarket_snapshots, news_events,
                    technical_snapshots, macro_snapshots
oracle_strategy     strategies, backtest_results, backtest_trades,
                    deployed_strategies
oracle_memory       memory_nodes, memory_edges, investor_profiles,
                    learning_log, simulation_accuracy
oracle_autopilot    autopilot_sessions, autopilot_decisions, autopilot_trades
oracle_feed         transparency_feed_events
oracle_audit        audit_log
```

**Total:** 25 tables across 8 schemas. All have RLS enabled.

---

## 2. Schema Reference

### `public.profiles`

User profiles. Auto-created when a Supabase Auth user signs up.

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| `id` | uuid PK | — | FK → `auth.users(id)` |
| `display_name` | text | — | Required |
| `role` | text | `'user'` | `user \| analyst \| system` |
| `locale` | text | `'en'` | — |
| `timezone` | text | `'Europe/Amsterdam'` | — |
| `demo_mode` | boolean | `true` | Hackathon demo flag |

### `oracle_portfolio.positions`

Current portfolio holdings.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | — |
| `user_id` | uuid FK | → profiles |
| `symbol` | text | e.g., `NVDA`, `BTC-USD` |
| `asset_class` | text | `equity \| etf \| crypto \| bond \| commodity` |
| `quantity` | numeric(18,8) | — |
| `avg_entry_price` | numeric(18,4) | — |
| `current_price` | numeric(18,4) | — |
| `market_value` | numeric(18,4) | — |
| `unrealized_pnl` | numeric(18,4) | — |
| `oracle_signal` | text | `BUY \| SELL \| HOLD \| REDUCE \| WATCH` |

**Unique constraint:** `(user_id, symbol)` — one position per symbol per user.

### `oracle_portfolio.trades`

Trade execution log. Every trade has a reasoning trail.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | — |
| `symbol` | text | — |
| `action` | text | `BUY \| SELL \| REBALANCE` |
| `quantity` | numeric(18,8) | — |
| `price` | numeric(18,4) | — |
| `reasoning` | text | L10 explanation |
| `layers_activated` | text[] | e.g., `['L3','L5','L6','L7']` |
| `swarm_bullish_pct` | numeric(5,4) | L6 output at trade time |
| `polymarket_prob` | numeric(5,4) | L5 output at trade time |
| `is_paper` | boolean | Always `true` in MVP (ADR-008) |
| `is_autopilot` | boolean | `true` if autopilot triggered |

### `oracle_simulation.simulations`

Swarm simulation records.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | — |
| `seed_text` | text | The financial trigger text |
| `seed_type` | text | `news \| earnings \| macro \| fed_statement \| ...` |
| `status` | text | `pending \| running \| complete \| failed` |
| `agent_count` | integer | 1–1000 |
| `round_count` | integer | 1–40 |
| `final_bullish` | numeric(5,4) | Final bullish % |
| `verdict` | text | `BULLISH \| BEARISH \| NEUTRAL` |
| `confidence` | numeric(5,4) | 0.0–1.0 |
| `tokens_used` | integer | For cost tracking |
| `cost_usd` | numeric(8,4) | LLM cost |

### `oracle_simulation.simulation_rounds`

Per-round simulation data. Broadcast over Supabase Realtime.

| Column | Type | Notes |
|--------|------|-------|
| `simulation_id` | uuid FK | → simulations |
| `round_number` | integer | 1–40 |
| `bullish_pct` | numeric(5,4) | — |
| `bearish_pct` | numeric(5,4) | — |
| `neutral_pct` | numeric(5,4) | — |
| `interactions` | integer | Agent interactions this round |
| `opinion_shifts` | integer | — |
| `dominant_narrative` | text | — |
| `agent_activity` | jsonb | Per-archetype activity summary |

### `oracle_signals.signal_events`

All L1–L10 signal events. Read-only for users; writes via service role only.

| Column | Type | Notes |
|--------|------|-------|
| `layer` | text | `L1–L10` |
| `signal_type` | text | e.g., `price_update`, `news_sentiment`, `polymarket_prediction` |
| `asset` | text | Nullable for macro signals |
| `direction` | text | `bullish \| bearish \| neutral \| contrarian` |
| `strength` | integer | 1–5 |
| `confidence` | numeric(5,4) | — |

### `oracle_memory.memory_nodes` ⭐ pgvector

Knowledge graph nodes with vector embeddings for semantic search.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | — |
| `user_id` | uuid FK | → profiles |
| `node_type` | text | `asset \| concept \| event \| strategy \| memory` |
| `label` | text | e.g., `NVDA`, `inflation`, `fed_statement` |
| `properties` | jsonb | Arbitrary metadata |
| `embedding` | vector(1536) | OpenAI text-embedding-3-small |

### `oracle_memory.memory_edges`

Typed edges between knowledge graph nodes.

| Column | Type | Notes |
|--------|------|-------|
| `source_id` | uuid FK | → memory_nodes |
| `target_id` | uuid FK | → memory_nodes |
| `relation` | text | `mentions \| co_occurs_with \| ...` |
| `weight` | numeric(5,4) | Edge strength |

### `oracle_memory.investor_profiles`

Investor DNA — behavioral profile derived from actions.

| Column | Type | Notes |
|--------|------|-------|
| `stated_risk` | text | What user says (`conservative \| moderate \| aggressive`) |
| `revealed_risk` | text | What behavior shows |
| `risk_discrepancy` | boolean | **Generated column**: true if stated ≠ revealed |
| `best_signal_combo` | text | e.g., `L5+L6` |
| `radar_scores` | jsonb | `{risk_appetite, patience, conviction, ...}` |

### `oracle_feed.transparency_feed_events`

Live transparency feed events. Broadcast over Realtime. Uses `REPLICA IDENTITY FULL`.

| Column | Type | Notes |
|--------|------|-------|
| `event_type` | text | `data \| simulation \| action \| risk_alert \| learning \| debate \| system` |
| `layer` | text | `L1–L10` or NULL |
| `icon` | text | Emoji icon |
| `title` | text | — |
| `detail` | text | — |

### `oracle_audit.audit_log`

Append-only audit log. No UPDATE or DELETE policy exists.

| Column | Type | Notes |
|--------|------|-------|
| `action` | text | e.g., `PAPER_TRADE_BUY` |
| `resource_type` | text | e.g., `trade` |
| `sensitive_class` | text | `financial \| simulation \| memory` |
| `ip_address` | inet | — |

---

## 3. Row Level Security (RLS)

**Every table has RLS enabled. No exceptions.**

### Philosophy

```
┌─────────────┐     anon key + JWT      ┌──────────────┐
│  Frontend   │ ──────────────────────► │  PostgreSQL  │
│             │                          │              │
│ NEVER has   │                          │  RLS checks  │
│ service     │                          │  auth.uid()  │
│ role key    │                          │  = user_id   │
└─────────────┘                          └──────────────┘

┌─────────────────┐  service role (bypasses RLS)  ┌──────────────┐
│ Edge Functions  │ ────────────────────────────► │  PostgreSQL  │
│ FastAPI         │                                │              │
│ (server only)   │                                │  Full access │
└─────────────────┘                                └──────────────┘
```

### Core Pattern (User-Scoped Tables)

```sql
ALTER TABLE oracle_portfolio.positions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "positions_user_all" ON oracle_portfolio.positions
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );
```

### Demo Mode Pattern

In demo mode (hackathon), a fixed `DEMO_USER_ID` allows anonymous access:

```sql
CREATE OR REPLACE FUNCTION oracle_feed.demo_user_id()
RETURNS uuid LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT COALESCE(
        NULLIF(current_setting('app.demo_user_id', true), '')::uuid,
        '00000000-0000-0000-0000-000000000001'::uuid
    )
$$;
```

### Public Read Tables (Signals)

Signal data is market-wide, readable by all authenticated users:

```sql
CREATE POLICY "signals_read_all" ON oracle_signals.signal_events
    FOR SELECT TO authenticated, anon USING (true);
-- Writes only via service role (bypasses RLS)
```

### Append-Only Audit Log

```sql
CREATE POLICY "audit_log_insert" ON oracle_audit.audit_log
    FOR INSERT WITH CHECK (true);       -- anyone can INSERT

CREATE POLICY "audit_log_user_read" ON oracle_audit.audit_log
    FOR SELECT USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );
-- No UPDATE or DELETE policy → append-only enforced by absence
```

### RLS Testing

```bash
# Run pgTAP RLS tests (requires local Supabase)
supabase test db
```

Test file: [supabase/tests/rls_policies.test.sql](../supabase/tests/rls_policies.test.sql)

---

## 4. GraphRAG Vector Search

### HNSW Index

```sql
CREATE INDEX idx_memory_nodes_embedding_hnsw
    ON oracle_memory.memory_nodes
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

### `match_memory_nodes` RPC

Semantic similarity search via cosine distance:

```sql
SELECT * FROM oracle_memory.match_memory_nodes(
    '00000000-0000-0000-0000-000000000001'::uuid,  -- user_id
    '[0.1, 0.2, ...]'::vector(1536),               -- query embedding
    'event',                                        -- node_type filter (optional)
    0.72,                                           -- similarity threshold
    5                                               -- max results
);
```

Returns nodes with similarity score ≥ threshold, ordered by similarity.

### `get_memory_subgraph` RPC

Returns a user's knowledge graph for visualization:

```sql
SELECT * FROM oracle_memory.get_memory_subgraph(
    '00000000-0000-0000-0000-000000000001'::uuid,  -- user_id
    NULL,                                           -- center node (optional)
    50                                              -- max nodes
);
-- Returns: { nodes: [...], edges: [...] }
```

---

## 5. Scheduled Jobs (pg_cron)

```sql
-- View all scheduled jobs
SELECT jobid, schedule, command FROM cron.jobs;
```

| Job | Schedule | Purpose |
|-----|----------|---------|
| `oracle-autopilot-loop` | `*/5 * * * *` | Monitor signals, trigger swarms, execute paper trades |
| `oracle-signal-refresh` | `*/15 * * * *` | Refresh L1–L5 signal pipeline via FastAPI |
| `oracle-voice-cache-cleanup` | `0 3 * * *` | Delete voice audio >24h old |
| `oracle-accuracy-evaluation` | `0 4 * * *` | Evaluate 5-day-old sims against actual prices |
| `oracle-portfolio-snapshot` | `0 17 * * 1-5` | Weekday market-close snapshot |
| `oracle-feed-cleanup` | `0 2 * * 0` | Delete feed events >30 days old |

Migration file: [supabase/migrations/20260613_scheduled_jobs.sql](../supabase/migrations/20260613_scheduled_jobs.sql)

---

## 6. Migrations

Migrations are applied in alphabetical order. Files:

| File | Scope |
|------|-------|
| `20260613_initial_schema.sql` | All 8 schemas, 25 tables, indexes, triggers |
| `20260613_rls_policies.sql` | RLS enable + policies on every table |
| `20260613_scheduled_jobs.sql` | pg_cron schedules |
| `20260613_storage_buckets.sql` | Private storage buckets + policies |
| `20260613_graphrag_vector.sql` | HNSW index + match_memory_nodes + get_memory_subgraph RPCs |

```bash
# Apply all migrations + seed data
supabase db reset

# Generate TypeScript types from schema
supabase gen types typescript --local \
  --schema public,oracle_portfolio,oracle_simulation,oracle_signals,\
oracle_strategy,oracle_memory,oracle_autopilot,oracle_feed,oracle_audit \
  > apps/web/src/types/database.types.ts
```

---

## 7. Seed Data

The seed file (`supabase/seed.sql`) creates realistic demo data:

| Data | Count | Purpose |
|------|-------|---------|
| Demo user profile | 1 | `DEMO_USER_ID` |
| Portfolio positions | 5 | NVDA, AAPL, SPY, BTC, TLT |
| Portfolio snapshots | 90 | ~3 months equity curve |
| Past simulations | 47 | With verdicts + accuracy records |
| Learning log entries | ~40 | Behavioral lessons |
| Investor DNA profile | 1 | Populated radar scores |
| Saved strategies | 8 | With backtest results |
| Signal events | 10 | Across L1–L5 |
| Transparency feed events | 100 | Last session activity |
| Knowledge graph nodes | 80 | 50 assets, 20 events, 10 strategies |

---

> **Next:** [Deployment Guide →](DEPLOYMENT.md) | [← Back to README](../README.md)
