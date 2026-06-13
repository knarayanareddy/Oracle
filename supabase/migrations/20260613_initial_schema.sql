-- ════════════════════════════════════════════════════════════════
-- ORACLE — Initial Schema Migration
-- Single Source of Truth: Oracledesigndoc.md v1.0.0 §08
-- Supabase Frankfurt (eu-central-1) — GDPR/AVG compliant
-- ════════════════════════════════════════════════════════════════

-- ── Extensions ──────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";          -- gen_random_uuid
CREATE EXTENSION IF NOT EXISTS "vector";            -- pgvector (similarity)
CREATE EXTENSION IF NOT EXISTS "pg_cron";           -- scheduled jobs
CREATE EXTENSION IF NOT EXISTS "pg_net";            -- HTTP from SQL
CREATE EXTENSION IF NOT EXISTS "pgjwt";             -- JWT helpers

-- pg_cron needs the extensions on the right schema
CREATE EXTENSION IF NOT EXISTS pg_cron SCHEMA pgcron;

-- ── Schemas ─────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS oracle_portfolio;
CREATE SCHEMA IF NOT EXISTS oracle_simulation;
CREATE SCHEMA IF NOT EXISTS oracle_signals;
CREATE SCHEMA IF NOT EXISTS oracle_strategy;
CREATE SCHEMA IF NOT EXISTS oracle_memory;
CREATE SCHEMA IF NOT EXISTS oracle_autopilot;
CREATE SCHEMA IF NOT EXISTS oracle_feed;
CREATE SCHEMA IF NOT EXISTS oracle_audit;

-- ════════════════════════════════════════════════════════════════
-- public.profiles
-- ════════════════════════════════════════════════════════════════
CREATE TABLE public.profiles (
    id          uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name text NOT NULL,
    role        text NOT NULL DEFAULT 'user'
                    CHECK (role IN ('user', 'analyst', 'system')),
    locale      text NOT NULL DEFAULT 'en',
    timezone    text NOT NULL DEFAULT 'Europe/Amsterdam',
    demo_mode   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Auto-create a profile row when an auth user is created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, display_name)
    VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)));
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ════════════════════════════════════════════════════════════════
-- oracle_portfolio
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_portfolio.portfolio_snapshots (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    snapshot_at     timestamptz NOT NULL DEFAULT now(),
    total_value     numeric(18,4) NOT NULL,
    cash_balance    numeric(18,4) NOT NULL DEFAULT 0,
    invested_value  numeric(18,4) NOT NULL DEFAULT 0,
    daily_pnl       numeric(18,4),
    daily_pnl_pct   numeric(8,4),
    total_return    numeric(8,4),
    sharpe_ratio    numeric(8,4),
    benchmark_value numeric(18,4),   -- SPY comparison
    is_paper        boolean NOT NULL DEFAULT true,
    metadata        jsonb NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_port_snap_user_time
    ON oracle_portfolio.portfolio_snapshots (user_id, snapshot_at DESC);

CREATE TABLE oracle_portfolio.positions (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol            text NOT NULL,
    asset_class       text NOT NULL
                        CHECK (asset_class IN ('equity', 'etf', 'crypto', 'bond', 'commodity')),
    quantity          numeric(18,8) NOT NULL,
    avg_entry_price   numeric(18,4) NOT NULL,
    current_price     numeric(18,4),
    market_value      numeric(18,4),
    unrealized_pnl    numeric(18,4),
    unrealized_pct    numeric(8,4),
    oracle_signal     text CHECK (oracle_signal IN ('BUY', 'SELL', 'HOLD', 'REDUCE', 'WATCH', NULL)),
    signal_confidence numeric(5,4),
    signal_updated_at timestamptz,
    is_paper          boolean NOT NULL DEFAULT true,
    opened_at         timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_positions_user_symbol ON oracle_portfolio.positions (user_id, symbol);
CREATE INDEX idx_positions_user ON oracle_portfolio.positions (user_id);

CREATE TABLE oracle_portfolio.trades (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    position_id       uuid REFERENCES oracle_portfolio.positions(id) ON DELETE SET NULL,
    simulation_id     uuid REFERENCES oracle_simulation.simulations(id) ON DELETE SET NULL,
    strategy_id       uuid REFERENCES oracle_strategy.strategies(id) ON DELETE SET NULL,
    symbol            text NOT NULL,
    action            text NOT NULL CHECK (action IN ('BUY', 'SELL', 'REBALANCE')),
    quantity          numeric(18,8) NOT NULL,
    price             numeric(18,4) NOT NULL,
    total_value       numeric(18,4) NOT NULL,
    reasoning         text,             -- L10 explanation
    layers_activated  text[] NOT NULL DEFAULT '{}',
    layer_signals     jsonb NOT NULL DEFAULT '{}',
    swarm_bullish_pct numeric(5,4),     -- L6 output at time of trade
    polymarket_prob   numeric(5,4),     -- L5 output at time of trade
    is_paper          boolean NOT NULL DEFAULT true,
    is_autopilot      boolean NOT NULL DEFAULT false,
    executed_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_trades_user_time ON oracle_portfolio.trades (user_id, executed_at DESC);
CREATE INDEX idx_trades_simulation ON oracle_portfolio.trades (simulation_id);

-- ════════════════════════════════════════════════════════════════
-- oracle_simulation
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_simulation.simulations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title           text NOT NULL,
    seed_text       text NOT NULL,
    seed_type       text CHECK (seed_type IN (
                        'news', 'earnings', 'macro', 'fed_statement',
                        'user_thesis', 'geopolitical', 'other')),
    status          text NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'running', 'complete', 'failed')),
    agent_count     integer NOT NULL DEFAULT 500
                        CHECK (agent_count BETWEEN 1 AND 1000),
    round_count     integer NOT NULL DEFAULT 40
                        CHECK (round_count BETWEEN 1 AND 40),
    current_round   integer NOT NULL DEFAULT 0,
    agent_mix       jsonb NOT NULL DEFAULT '{"institutional":35,"retail":50,"media":15}',
    llm_model       text NOT NULL DEFAULT 'gpt-4o-mini',
    environments    text[] NOT NULL DEFAULT ARRAY['twitter','reddit'],
    final_bullish   numeric(5,4),
    final_bearish   numeric(5,4),
    final_neutral   numeric(5,4),
    confidence      numeric(5,4),
    verdict         text CHECK (verdict IN ('BULLISH', 'BEARISH', 'NEUTRAL', NULL)),
    narrative       text,
    predicted_impact jsonb,
    accuracy_verified boolean DEFAULT false,
    actual_outcome  text,
    tokens_used     integer,
    cost_usd        numeric(8,4),
    started_at      timestamptz,
    completed_at    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_sims_user_time ON oracle_simulation.simulations (user_id, created_at DESC);
CREATE INDEX idx_sims_status ON oracle_simulation.simulations (status);

CREATE TABLE oracle_simulation.simulation_rounds (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id       uuid NOT NULL REFERENCES oracle_simulation.simulations(id) ON DELETE CASCADE,
    round_number        integer NOT NULL,
    bullish_pct         numeric(5,4),
    bearish_pct         numeric(5,4),
    neutral_pct         numeric(5,4),
    interactions        integer,
    opinion_shifts      integer,
    coalitions          integer,
    dominant_narrative  text,
    agent_activity      jsonb,          -- per-archetype activity summary
    recorded_at         timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_sim_rounds ON oracle_simulation.simulation_rounds (simulation_id, round_number);

CREATE TABLE oracle_simulation.simulation_reports (
    id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id             uuid NOT NULL UNIQUE
                                REFERENCES oracle_simulation.simulations(id) ON DELETE CASCADE,
    verdict                   text NOT NULL,
    confidence                numeric(5,4) NOT NULL,
    executive_summary         text NOT NULL,
    narrative_themes          jsonb,    -- array of {theme, prevalence, agents}
    institutional_consensus   text,
    retail_consensus          text,
    media_framing             text,
    predicted_impacts         jsonb,
    polymarket_corroboration  jsonb,
    recommended_actions       jsonb,    -- array of {action, asset, rationale}
    report_agent_reasoning    text,
    generated_at              timestamptz NOT NULL DEFAULT now()
);

-- ════════════════════════════════════════════════════════════════
-- oracle_signals
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_signals.signal_events (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    layer       text NOT NULL
                    CHECK (layer IN ('L1','L2','L3','L4','L5','L6','L7','L8','L9','L10')),
    signal_type text NOT NULL,
    asset       text,               -- NULL for macro/market-wide signals
    direction   text CHECK (direction IN ('bullish','bearish','neutral','contrarian',NULL)),
    strength    integer CHECK (strength BETWEEN 1 AND 5),
    confidence  numeric(5,4),
    raw_value   numeric(18,4),
    context     text,
    source_url  text,
    metadata    jsonb NOT NULL DEFAULT '{}',
    expires_at  timestamptz,
    detected_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_signals_layer_time ON oracle_signals.signal_events (layer, detected_at DESC);
CREATE INDEX idx_signals_asset ON oracle_signals.signal_events (asset);

CREATE TABLE oracle_signals.polymarket_snapshots (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id       text NOT NULL,
    question        text NOT NULL,
    yes_probability numeric(6,4),
    no_probability  numeric(6,4),
    volume_24h      numeric(18,4),
    last_updated    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_polymarket_time ON oracle_signals.polymarket_snapshots (last_updated DESC);

CREATE TABLE oracle_signals.news_events (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    headline    text NOT NULL,
    source      text,
    url         text,
    published_at timestamptz,
    sentiment   text CHECK (sentiment IN ('positive','negative','neutral')),
    sentiment_score numeric(5,4),
    entities    text[],
    captured_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_news_time ON oracle_signals.news_events (published_at DESC);

CREATE TABLE oracle_signals.technical_snapshots (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    asset       text NOT NULL,
    rsi         numeric(8,4),
    macd        numeric(8,4),
    macd_signal numeric(8,4),
    bb_upper    numeric(18,4),
    bb_lower    numeric(18,4),
    ema_20      numeric(18,4),
    ema_50      numeric(18,4),
    atr         numeric(18,4),
    signal_read text,
    captured_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_technical_asset_time ON oracle_signals.technical_snapshots (asset, captured_at DESC);

CREATE TABLE oracle_signals.macro_snapshots (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    series_id           text NOT NULL,
    label               text NOT NULL,
    value               numeric(18,4),
    previous_value      numeric(18,4),
    change_pct          numeric(8,4),
    captured_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_macro_series_time ON oracle_signals.macro_snapshots (series_id, captured_at DESC);

-- ════════════════════════════════════════════════════════════════
-- oracle_strategy
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_strategy.strategies (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name                  text NOT NULL,
    description           text,
    natural_language_input text NOT NULL,
    parsed_conditions     jsonb NOT NULL,
    asset_universe        text NOT NULL DEFAULT 'US_EQUITIES',
    layers_used           text[] NOT NULL DEFAULT '{}',
    version               integer NOT NULL DEFAULT 1,
    status                text NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft','backtested','deployed','archived')),
    is_public             boolean NOT NULL DEFAULT false,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_strategies_user ON oracle_strategy.strategies (user_id);

CREATE TABLE oracle_strategy.backtest_results (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id         uuid NOT NULL REFERENCES oracle_strategy.strategies(id) ON DELETE CASCADE,
    start_date          date NOT NULL,
    end_date            date NOT NULL,
    initial_capital     numeric(18,4) NOT NULL DEFAULT 100000,
    final_capital       numeric(18,4),
    total_return        numeric(8,4),
    benchmark_return    numeric(8,4),   -- SPY over same period
    alpha               numeric(8,4),
    sharpe_ratio        numeric(8,4),
    sortino_ratio       numeric(8,4),
    max_drawdown        numeric(8,4),
    win_rate            numeric(5,4),
    profit_factor       numeric(8,4),
    total_trades        integer,
    swarms_triggered    integer,
    layer_contribution  jsonb,
    equity_curve        jsonb,          -- array of {date, value, spy_value}
    monthly_returns     jsonb,          -- array of {month, return}
    computed_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_backtest_strategy ON oracle_strategy.backtest_results (strategy_id);

CREATE TABLE oracle_strategy.backtest_trades (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_result_id  uuid NOT NULL REFERENCES oracle_strategy.backtest_results(id) ON DELETE CASCADE,
    date                date NOT NULL,
    symbol              text NOT NULL,
    action              text NOT NULL CHECK (action IN ('BUY','SELL')),
    quantity            numeric(18,8),
    price               numeric(18,4),
    pnl                 numeric(18,4)
);

CREATE TABLE oracle_strategy.deployed_strategies (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    strategy_id         uuid NOT NULL REFERENCES oracle_strategy.strategies(id) ON DELETE CASCADE,
    autopilot_session_id uuid REFERENCES oracle_autopilot.autopilot_sessions(id) ON DELETE SET NULL,
    deployed_at         timestamptz NOT NULL DEFAULT now()
);

-- ════════════════════════════════════════════════════════════════
-- oracle_memory
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_memory.memory_nodes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    node_type       text NOT NULL,   -- asset, event, strategy, risk_factor, simulation
    label           text NOT NULL,
    properties      jsonb NOT NULL DEFAULT '{}',
    embedding       vector(1536),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_memory_nodes_user_type ON oracle_memory.memory_nodes (user_id, node_type);

CREATE TABLE oracle_memory.memory_edges (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id   uuid NOT NULL REFERENCES oracle_memory.memory_nodes(id) ON DELETE CASCADE,
    target_id   uuid NOT NULL REFERENCES oracle_memory.memory_nodes(id) ON DELETE CASCADE,
    relation    text NOT NULL,
    weight      numeric(5,4) DEFAULT 1.0,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_memory_edges_source ON oracle_memory.memory_edges (source_id);
CREATE INDEX idx_memory_edges_target ON oracle_memory.memory_edges (target_id);

CREATE TABLE oracle_memory.investor_profiles (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 uuid NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    stated_risk             text CHECK (stated_risk IN ('conservative','moderate','aggressive',NULL)),
    revealed_risk           text CHECK (revealed_risk IN ('conservative','moderate','aggressive',NULL)),
    risk_discrepancy        boolean GENERATED ALWAYS AS
                                (stated_risk IS DISTINCT FROM revealed_risk) STORED,
    avg_hold_days           numeric(8,2),
    optimal_hold_days       numeric(8,2),
    early_exit_count        integer DEFAULT 0,
    contrarian_score        numeric(5,4),
    macro_sensitivity       numeric(5,4),
    best_signal_combo       text,    -- e.g. 'L5+L6'
    worst_signal_combo      text,
    active_personalizations jsonb NOT NULL DEFAULT '[]',
    radar_scores            jsonb,   -- {risk_appetite, patience, conviction, ...}
    last_updated            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE oracle_memory.learning_log (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    lesson_number   integer GENERATED BY DEFAULT AS IDENTITY,
    lesson_text     text NOT NULL,
    confidence      integer NOT NULL DEFAULT 3 CHECK (confidence BETWEEN 1 AND 5),
    tags            text[] NOT NULL DEFAULT '{}',
    source_type     text CHECK (source_type IN (
                        'simulation_outcome','trade_result',
                        'behavior_pattern','signal_calibration')),
    source_id       uuid,            -- simulation_id or trade_id
    signal_combo    text,            -- e.g. 'L5+L6'
    validated       boolean DEFAULT false,
    times_applied   integer DEFAULT 0,
    learned_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_learning_user ON oracle_memory.learning_log (user_id, learned_at DESC);

CREATE TABLE oracle_memory.simulation_accuracy (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    simulation_id           uuid NOT NULL UNIQUE
                                REFERENCES oracle_simulation.simulations(id) ON DELETE CASCADE,
    signal_combo            text,
    predicted_direction     text,
    actual_direction        text,
    is_correct              boolean,
    confidence_at_prediction numeric(5,4),
    evaluated_at            timestamptz NOT NULL DEFAULT now()
);

-- ════════════════════════════════════════════════════════════════
-- oracle_autopilot
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_autopilot.autopilot_sessions (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status                  text NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','paused','stopped')),
    paper_mode              boolean NOT NULL DEFAULT true,
    require_confirm_above   numeric(18,4) DEFAULT 5000,
    max_daily_trades        integer DEFAULT 5,
    scan_interval_seconds   integer DEFAULT 300,
    deployed_strategy_ids   uuid[] NOT NULL DEFAULT '{}',
    session_start           timestamptz NOT NULL DEFAULT now(),
    session_end             timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_autopilot_sessions_status ON oracle_autopilot.autopilot_sessions (status);

CREATE TABLE oracle_autopilot.autopilot_decisions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          uuid NOT NULL REFERENCES oracle_autopilot.autopilot_sessions(id) ON DELETE CASCADE,
    user_id             uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    trigger_signal      text NOT NULL,
    trigger_layer       text NOT NULL,
    simulation_id       uuid,     -- if swarm was triggered
    bull_argument       text,
    bear_argument       text,
    risk_assessment     text,
    consensus           text NOT NULL CHECK (consensus IN (
                            'BUY','SELL','HOLD','REDUCE','REBALANCE')),
    consensus_confidence numeric(5,4),
    action_taken        text,
    reasoning_trail     jsonb NOT NULL DEFAULT '{}',
    layers_activated    text[] NOT NULL DEFAULT '{}',
    decided_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_autopilot_decisions_session ON oracle_autopilot.autopilot_decisions (session_id, decided_at DESC);

CREATE TABLE oracle_autopilot.autopilot_trades (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          uuid NOT NULL REFERENCES oracle_autopilot.autopilot_sessions(id) ON DELETE CASCADE,
    user_id             uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    decision_id         uuid REFERENCES oracle_autopilot.autopilot_decisions(id) ON DELETE SET NULL,
    trade_id            uuid REFERENCES oracle_portfolio.trades(id) ON DELETE SET NULL,
    executed_at         timestamptz NOT NULL DEFAULT now()
);

-- ════════════════════════════════════════════════════════════════
-- oracle_feed
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_feed.transparency_feed_events (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id  uuid,
    event_type  text NOT NULL CHECK (event_type IN (
                    'data','simulation','action','risk_alert','learning','debate','system')),
    layer       text CHECK (layer IN ('L1','L2','L3','L4','L5','L6','L7','L8','L9','L10',NULL)),
    icon        text NOT NULL,    -- emoji
    title       text NOT NULL,
    detail      text,
    metadata    jsonb NOT NULL DEFAULT '{}',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_feed_user_time ON oracle_feed.transparency_feed_events (user_id, created_at DESC);

-- Full replica identity for realtime to broadcast pre/post images
ALTER TABLE oracle_feed.transparency_feed_events REPLICA IDENTITY FULL;
ALTER TABLE oracle_simulation.simulation_rounds REPLICA IDENTITY FULL;

-- ════════════════════════════════════════════════════════════════
-- oracle_audit
-- ════════════════════════════════════════════════════════════════
CREATE TABLE oracle_audit.audit_log (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES public.profiles(id) ON DELETE SET NULL,
    action          text NOT NULL,
    resource_type   text NOT NULL,
    resource_id     uuid,
    sensitive_class text CHECK (sensitive_class IN ('financial','simulation','memory',NULL)),
    ip_address      inet,
    user_agent      text,
    metadata        jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_user_time ON oracle_audit.audit_log (user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON oracle_audit.audit_log (resource_type, resource_id);

-- ════════════════════════════════════════════════════════════════
-- Helper: auto-update updated_at columns
-- ════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_positions_updated_at
    BEFORE UPDATE ON oracle_portfolio.positions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_strategies_updated_at
    BEFORE UPDATE ON oracle_strategy.strategies
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Expose schemas to PostgREST / realtime via the exposed schemas config
-- (set in supabase/config.toml: db_schema + realtime tables)
