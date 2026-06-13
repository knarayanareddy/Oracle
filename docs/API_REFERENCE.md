# 🔌 ORACLE — API Reference

> **Navigation:** [← Back to README](../README.md) | [Architecture](ARCHITECTURE.md) | [Database](DATABASE.md)

Complete reference for all 12 FastAPI endpoints and 5 Supabase Edge Functions.

**Base URL:** `http://localhost:8000` (local) · `https://oracle-api.railway.app` (production)

**Interactive docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc)

---

## Table of Contents

- [Authentication](#authentication)
- [FastAPI Endpoints](#fastapi-endpoints)
  - [Health](#health)
  - [Swarm](#swarm)
  - [Voice](#voice)
  - [Strategy](#strategy)
  - [Signals](#signals)
  - [Recommendations](#recommendations)
  - [Accuracy](#accuracy)
- [Edge Functions](#edge-functions)
- [Supabase PostgREST](#supabase-postgrest)
- [Error Codes](#error-codes)

---

## Authentication

FastAPI endpoints are called by Edge Functions (service-to-service) using the
`X-Oracle-Secret` header. The frontend never calls FastAPI directly — it goes
through Supabase PostgREST + Edge Functions.

```
┌────────────┐    Edge Function     ┌──────────┐
│  Frontend  │ ──────────────────► │ FastAPI  │
│ (anon key) │  X-Oracle-Secret    │          │
└────────────┘                     └──────────┘
```

| Header | Value | Required By |
|--------|-------|-------------|
| `X-Oracle-Secret` | `FASTAPI_SECRET_KEY` | All FastAPI endpoints (except `/health`) |
| `Authorization` | `Bearer <service-role-key>` | Edge Functions |
| `apikey` | `<service-role-key>` | PostgREST (service writes) |

---

## FastAPI Endpoints

### Health

#### `GET /health`

Liveness + readiness probe. Reports service connectivity.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "supabase": "connected",
    "openai": "connected",
    "alpha_vantage": "no-key",
    "polymarket": "ready",
    "mirofish": "ready"
  },
  "offline_mode": false,
  "timestamp": "2026-06-13T17:45:19.460894Z"
}
```

---

### Swarm

#### `POST /api/v1/swarm/run`

Execute a swarm simulation. Called by the `swarm-trigger` Edge Function.

```bash
curl -X POST http://localhost:8000/api/v1/swarm/run \
  -H "Content-Type: application/json" \
  -H "X-Oracle-Secret: $FASTAPI_SECRET_KEY" \
  -d '{
    "simulation_id": "uuid-here",
    "seed_text": "Fed signals two rate hikes in 2026 as inflation proves sticky",
    "seed_type": "fed_statement",
    "agent_count": 500,
    "round_count": 40,
    "agent_mix": {"institutional": 35, "retail": 50, "media": 15},
    "llm_model": "qwen-plus",
    "environments": ["twitter", "reddit"]
  }'
```

**Request Body:**

| Field | Type | Default | Constraints |
|-------|------|---------|-------------|
| `simulation_id` | string | — | **required** |
| `seed_text` | string | — | **required**, min 10 chars |
| `seed_type` | string | `"user_thesis"` | `news\|earnings\|macro\|fed_statement\|user_thesis\|geopolitical\|other` |
| `agent_count` | int | `500` | 1–1000 |
| `round_count` | int | `40` | 1–40 |
| `agent_mix` | object | `{inst:35,retail:50,media:15}` | Must sum to 100 |
| `llm_model` | string | `"gpt-4o-mini"` | Any OpenAI/Qwen model |
| `environments` | string[] | `["twitter","reddit"]` | — |

**Response:**
```json
{
  "simulation_id": "uuid-here",
  "status": "complete",
  "rounds": [
    {
      "round_number": 1,
      "bullish_pct": 0.42,
      "bearish_pct": 0.35,
      "neutral_pct": 0.23,
      "interactions": 287,
      "opinion_shifts": 42,
      "coalitions": 12,
      "dominant_narrative": "Institutional accumulation driving retail FOMO"
    }
  ],
  "report": {
    "verdict": "BEARISH",
    "confidence": 0.71,
    "final_bullish": 0.25,
    "final_bearish": 0.63,
    "final_neutral": 0.12,
    "executive_summary": "Swarm reached bearish consensus...",
    "narrative_themes": [
      {"theme": "Rate-hike anxiety", "prevalence": 0.38, "agents": 190}
    ],
    "institutional_consensus": "De-risking, raising cash buffers",
    "retail_consensus": "Panic selling patterns emerging",
    "media_framing": "Fear-based narratives amplifying downside",
    "predicted_impacts": {"tech": -0.032, "bonds": 0.011},
    "recommended_actions": [
      {"action": "REDUCE", "asset": "NVDA", "rationale": "Bearish swarm + macro risk"}
    ]
  },
  "tokens_used": 847293,
  "cost_usd": 0.34
}
```

#### `POST /api/v1/swarm/debate`

Run the L7 multi-agent debate (Bull vs Bear vs Risk → Consensus).

```bash
curl -X POST http://localhost:8000/api/v1/swarm/debate \
  -H "Content-Type: application/json" \
  -H "X-Oracle-Secret: $FASTAPI_SECRET_KEY" \
  -d '{
    "swarm_report": {"verdict": "BEARISH", "confidence": 0.71},
    "signals": [{"layer": "L5", "direction": "bearish"}]
  }'
```

**Response:**
```json
{
  "bull_argument": "Momentum still intact — NVDA RSI oversold...",
  "bear_argument": "Yield curve inversion + rate fear dominant...",
  "risk_assessment": 7,
  "consensus": "REDUCE",
  "confidence": 0.74,
  "reasoning_trail": {
    "bull_signals": ["rsi_oversold", "institutional_accumulation"],
    "bear_signals": ["yield_curve", "rate_fear"],
    "explanation": "Bearish signals outweigh momentum..."
  },
  "recommended_action": {
    "asset": "NVDA", "action": "REDUCE",
    "from_pct": 0.12, "to_pct": 0.08,
    "rationale": "Swarm-driven consensus"
  },
  "layers_activated": ["L6", "L7", "L8", "L10"],
  "mode": "llm"
}
```

> **Note:** The `mode` field discloses whether the debate used real LLM (`"llm"`) or
> fell back to deterministic logic (`"no_llm"`, `"circuit_open"`, `"partial_fallback"`).

---

### Voice

#### `POST /api/v1/voice/transcribe`

Transcribe audio via Whisper. Accepts `multipart/form-data`.

```bash
curl -X POST http://localhost:8000/api/v1/voice/transcribe \
  -F "file=@audio.webm"
```

**Response:**
```json
{
  "transcript": "Run a swarm simulation on today's CPI report",
  "confidence": 0.97,
  "language": "en",
  "status": "success"
}
```

| `status` | Meaning |
|----------|---------|
| `"success"` | Transcription succeeded |
| `"whisper_unavailable"` | No OpenAI API key configured |
| `"transcription_failed"` | Whisper failed (returns empty, NOT a fake transcript) |
| `"empty_audio"` | No audio data received |

#### `POST /api/v1/voice/process`

Route a transcript to the correct ORACLE module via intent classification.

```bash
curl -X POST http://localhost:8000/api/v1/voice/process \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Run a swarm on the Fed statement"}'
```

**Response:**
```json
{
  "intent": "run_swarm_simulation",
  "parameters": {"seed_text": "Run a swarm on the Fed statement"},
  "response_text": "Launching a swarm simulation...",
  "response_audio_url": null,
  "layers_activated": ["L6", "L7", "L8", "L10"],
  "action_available": true,
  "action_label": "Run Simulation",
  "action_payload": {"seed_text": "..."}
}
```

**Possible intents:** `run_swarm_simulation`, `query_portfolio`, `build_strategy`, `generate_recommendation`, `set_autopilot`

---

### Strategy

#### `POST /api/v1/strategy/parse`

Parse natural language into structured strategy conditions.

```bash
curl -X POST http://localhost:8000/api/v1/strategy/parse \
  -H "Content-Type: application/json" \
  -d '{"description": "Buy NVDA when RSI below 30 and swarm bullish above 60%"}'
```

**Response:**
```json
{
  "name": "RSI Dip Buyer with Swarm Confirmation",
  "entry": [
    {"layer": "L4", "condition": "rsi", "operator": "<", "threshold": 30},
    {"layer": "L6", "condition": "swarm_bullish", "operator": ">", "threshold": 0.60}
  ],
  "exit": [
    {"layer": "L4", "condition": "rsi", "operator": ">", "threshold": 65}
  ],
  "risk": {
    "max_position_pct": 0.15,
    "stop_loss_pct": 0.08,
    "max_daily_trades": 3
  }
}
```

#### `POST /api/v1/strategy/backtest`

Run a historical backtest on parsed conditions.

```bash
curl -X POST http://localhost:8000/api/v1/strategy/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "conditions": {
      "entry": [{"layer": "L4", "condition": "rsi", "operator": "<", "threshold": 30}],
      "exit": [{"layer": "L4", "condition": "rsi", "operator": ">", "threshold": 65}],
      "risk": {"max_position_pct": 0.15, "stop_loss_pct": 0.08, "max_daily_trades": 3}
    },
    "symbol": "NVDA",
    "start_date": "2022-01-03",
    "end_date": "2026-06-01",
    "initial_capital": 100000,
    "layers_used": ["L4"]
  }'
```

**Response:**
```json
{
  "start_date": "2022-01-03",
  "end_date": "2026-05-30",
  "initial_capital": 100000,
  "final_capital": 178432.50,
  "total_return": 0.7843,
  "benchmark_return": 0.3800,
  "alpha": 0.4043,
  "sharpe_ratio": 1.82,
  "sortino_ratio": 2.41,
  "max_drawdown": -0.18,
  "win_rate": 0.58,
  "profit_factor": 2.1,
  "total_trades": 87,
  "equity_curve": [
    {"date": "2022-01-03", "value": 100000, "spy_value": 478.00},
    {"date": "2024-06-01", "value": 178432.50, "spy_value": 503.10}
  ],
  "layer_contribution": {"L4": 1.0}
}
```

---

### Signals

#### `GET /api/v1/signals/latest?limit=50`

Fetch the latest L1–L5 signals from all providers.

```bash
curl http://localhost:8000/api/v1/signals/latest?limit=20
```

#### `POST /api/v1/signals/refresh`

Trigger a full signal pipeline refresh. Called by pg_cron every 15 minutes.

```bash
curl -X POST http://localhost:8000/api/v1/signals/refresh
```

**Response:**
```json
{
  "signals_collected": 42,
  "errors": [],
  "by_layer": {"L1": 12, "L2": 5, "L3": 8, "L4": 6, "L5": 5}
}
```

---

### Recommendations

#### `POST /api/v1/recommendations/generate`

Full L1–L10 recommendation pipeline.

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/generate \
  -H "Content-Type: application/json" \
  -H "X-Oracle-Secret: $FASTAPI_SECRET_KEY" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001", "query": "What should I do with tech?"}'
```

**Response:**
```json
{
  "consensus": "REDUCE",
  "confidence": 0.71,
  "explanation": "ORACLE recommends REDUCE with 71% confidence...",
  "bull_argument": "...",
  "bear_argument": "...",
  "risk_assessment": 7,
  "recommended_action": {"asset": "NVDA", "action": "REDUCE", "to_pct": 0.08},
  "layers_activated": ["L1","L3","L5","L6","L7","L8","L9","L10"],
  "memory_context": {
    "investor_risk": "aggressive",
    "best_signal_combo": "L5+L6",
    "recent_lessons": 5
  }
}
```

---

### Accuracy

#### `POST /api/v1/accuracy/evaluate`

Evaluate past simulation accuracy against actual outcomes. Called by pg_cron daily.

#### `GET /api/v1/accuracy/stats?user_id={uuid}`

Get accuracy statistics for a user.

**Response:**
```json
{
  "total": 39,
  "accuracy": 0.7436,
  "by_combo": {
    "L5+L6": {"accuracy": 0.81, "count": 20},
    "L3+L6": {"accuracy": 0.68, "count": 19}
  }
}
```

---

## Edge Functions

All Edge Functions run on Supabase (Deno runtime).

### `POST /functions/v1/swarm-trigger`

Validates simulation request, creates record, calls FastAPI, writes rounds to DB.

| Input | Auth | Writes To |
|-------|------|-----------|
| `{seed_text, seed_type, agent_count, ...}` | JWT or service role | `simulations`, `transparency_feed_events` |

### `POST /functions/v1/autopilot-loop`

Called by pg_cron every 5 min. Monitors signals, triggers swarms, runs debates, executes paper trades.

| Input | Auth | Writes To |
|-------|------|-----------|
| `{}` (reads from DB) | Service role only | `autopilot_decisions`, `trades`, `positions`, `feed`, `learning_log` |

### `POST /functions/v1/signal-ingest`

Receives signal data from FastAPI pipeline. Batch insert supported.

| Input | Auth | Writes To |
|-------|------|-----------|
| `{layer, signal_type, asset, direction, strength, ...}` or array | Service role only | `signal_events` |

### `POST /functions/v1/memory-update`

After every simulation/trade: extracts lessons, updates investor profile, records accuracy.

| Input | Auth | Writes To |
|-------|------|-----------|
| `{user_id, event_type, event_id, outcome_data}` | Service role only | `learning_log`, `investor_profiles`, `simulation_accuracy` |

### `POST /functions/v1/trade-execute`

Paper-executes a trade. Validates position sizing, checks daily limits.

| Input | Auth | Writes To |
|-------|------|-----------|
| `{user_id, symbol, action, quantity, price, ...}` | Service role only | `trades`, `positions`, `transparency_feed_events`, `audit_log` |

---

## Supabase PostgREST

The frontend reads data directly from Supabase PostgREST (auto-generated REST API from the
PostgreSQL schema), protected by RLS policies.

```typescript
// Example: fetch positions
const { data } = await supabase
  .from('positions')
  .select('*')
  .eq('user_id', userId)
  .order('market_value', { ascending: false })

// Example: subscribe to real-time feed events
supabase
  .channel('transparency-feed')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'oracle_feed',
    table: 'transparency_feed_events',
    filter: `user_id=eq.${userId}`,
  }, (payload) => {
    console.log('New feed event:', payload.new)
  })
  .subscribe()
```

> **Full schema reference:** [DATABASE.md](DATABASE.md)

---

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | — |
| `400` | Bad request (validation error) | Check request body |
| `403` | Invalid service secret | Verify `X-Oracle-Secret` header |
| `405` | Method not allowed | Use POST |
| `422` | Unprocessable (position size exceeds cap) | Reduce trade size |
| `429` | Rate limited (>100 req/min) | Wait and retry |
| `500` | Internal error | Check logs |
| `502` | Upstream (FastAPI) failed | Check if FastAPI is running |

---

> **Next:** [Database Guide →](DATABASE.md) | [← Back to README](../README.md)
