-- ════════════════════════════════════════════════════════════════
-- ORACLE — Canonical RLS Policies (Addendum A)
-- Single Source of Truth: Oracledesigndoc.md §09 + Addendum A
-- EVERY table has RLS enabled. No exceptions.
-- Service-role key is used ONLY in Edge Functions + FastAPI backend.
-- ════════════════════════════════════════════════════════════════

-- ── Demo-mode helper ────────────────────────────────────────────
-- In demo mode (no auth), a fixed DEMO_USER_ID allows anonymous read/write.
-- Set as a custom GUC via: alter role anon set request.jwt.claims...
-- For hackathon simplicity, we read from a stable config value.
-- Production (Phase 2) MUST remove the demo bypass.

CREATE OR REPLACE FUNCTION oracle_feed.demo_user_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER SET search_path = public
AS $$
    SELECT COALESCE(
        NULLIF(current_setting('app.demo_user_id', true), '')::uuid,
        '00000000-0000-0000-0000-000000000001'::uuid
    )
$$;

-- ════════════════════════════════════════════════════════════════
-- Helper macro: enable RLS + user-scope policy on a table
-- ════════════════════════════════════════════════════════════════

-- ── public.profiles ─────────────────────────────────────────────
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own" ON public.profiles
    FOR SELECT USING (
        auth.uid() = id OR id = oracle_feed.demo_user_id()
    );
CREATE POLICY "profiles_update_own" ON public.profiles
    FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- ── oracle_portfolio.portfolio_snapshots ────────────────────────
ALTER TABLE oracle_portfolio.portfolio_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "snapshots_user_all" ON oracle_portfolio.portfolio_snapshots
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_portfolio.positions ──────────────────────────────────
ALTER TABLE oracle_portfolio.positions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "positions_user_all" ON oracle_portfolio.positions
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_portfolio.trades ─────────────────────────────────────
ALTER TABLE oracle_portfolio.trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY "trades_user_all" ON oracle_portfolio.trades
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_simulation.simulations ───────────────────────────────
ALTER TABLE oracle_simulation.simulations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "simulations_user_all" ON oracle_simulation.simulations
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_simulation.simulation_rounds ─────────────────────────
ALTER TABLE oracle_simulation.simulation_rounds ENABLE ROW LEVEL SECURITY;
CREATE POLICY "sim_rounds_user_read" ON oracle_simulation.simulation_rounds
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM oracle_simulation.simulations s
            WHERE s.id = simulation_rounds.simulation_id
              AND (s.user_id = auth.uid() OR s.user_id = oracle_feed.demo_user_id())
        )
    );

-- ── oracle_simulation.simulation_reports ────────────────────────
ALTER TABLE oracle_simulation.simulation_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "sim_reports_user_read" ON oracle_simulation.simulation_reports
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM oracle_simulation.simulations s
            WHERE s.id = simulation_reports.simulation_id
              AND (s.user_id = auth.uid() OR s.user_id = oracle_feed.demo_user_id())
        )
    );

-- ── oracle_signals.* (read-only for authenticated/demo users) ───
ALTER TABLE oracle_signals.signal_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "signals_read_all" ON oracle_signals.signal_events
    FOR SELECT TO authenticated, anon USING (true);
-- Writes only via service role (bypasses RLS)

ALTER TABLE oracle_signals.polymarket_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "polymarket_read_all" ON oracle_signals.polymarket_snapshots
    FOR SELECT TO authenticated, anon USING (true);

ALTER TABLE oracle_signals.news_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "news_read_all" ON oracle_signals.news_events
    FOR SELECT TO authenticated, anon USING (true);

ALTER TABLE oracle_signals.technical_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "technical_read_all" ON oracle_signals.technical_snapshots
    FOR SELECT TO authenticated, anon USING (true);

ALTER TABLE oracle_signals.macro_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "macro_read_all" ON oracle_signals.macro_snapshots
    FOR SELECT TO authenticated, anon USING (true);

-- ── oracle_strategy.strategies ──────────────────────────────────
ALTER TABLE oracle_strategy.strategies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "strategies_user_all" ON oracle_strategy.strategies
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
        OR is_public = true
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_strategy.backtest_results ────────────────────────────
ALTER TABLE oracle_strategy.backtest_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "backtest_user_read" ON oracle_strategy.backtest_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM oracle_strategy.strategies s
            WHERE s.id = backtest_results.strategy_id
              AND (s.user_id = auth.uid() OR s.user_id = oracle_feed.demo_user_id() OR s.is_public)
        )
    );

-- ── oracle_strategy.backtest_trades ─────────────────────────────
ALTER TABLE oracle_strategy.backtest_trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bt_trades_user_read" ON oracle_strategy.backtest_trades
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM oracle_strategy.backtest_results br
            JOIN oracle_strategy.strategies s ON s.id = br.strategy_id
            WHERE br.id = backtest_trades.backtest_result_id
              AND (s.user_id = auth.uid() OR s.user_id = oracle_feed.demo_user_id())
        )
    );

-- ── oracle_strategy.deployed_strategies ─────────────────────────
ALTER TABLE oracle_strategy.deployed_strategies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "deployed_user_all" ON oracle_strategy.deployed_strategies
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_memory.* (all user-scoped, sensitive) ────────────────
ALTER TABLE oracle_memory.memory_nodes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "mem_nodes_user_all" ON oracle_memory.memory_nodes
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

ALTER TABLE oracle_memory.memory_edges ENABLE ROW LEVEL SECURITY;
CREATE POLICY "mem_edges_user_read" ON oracle_memory.memory_edges
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM oracle_memory.memory_nodes n
            WHERE n.id = memory_edges.source_id
              AND (n.user_id = auth.uid() OR n.user_id = oracle_feed.demo_user_id())
        )
    );

ALTER TABLE oracle_memory.investor_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "investor_profiles_user_all" ON oracle_memory.investor_profiles
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

ALTER TABLE oracle_memory.learning_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "learning_log_user_all" ON oracle_memory.learning_log
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

ALTER TABLE oracle_memory.simulation_accuracy ENABLE ROW LEVEL SECURITY;
CREATE POLICY "sim_accuracy_user_all" ON oracle_memory.simulation_accuracy
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_autopilot.* ──────────────────────────────────────────
ALTER TABLE oracle_autopilot.autopilot_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "ap_sessions_user_all" ON oracle_autopilot.autopilot_sessions
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

ALTER TABLE oracle_autopilot.autopilot_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "ap_decisions_user_read" ON oracle_autopilot.autopilot_decisions
    FOR SELECT USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

ALTER TABLE oracle_autopilot.autopilot_trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY "ap_trades_user_read" ON oracle_autopilot.autopilot_trades
    FOR SELECT USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_feed.transparency_feed_events ────────────────────────
ALTER TABLE oracle_feed.transparency_feed_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "feed_events_user_all" ON oracle_feed.transparency_feed_events
    FOR ALL USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    ) WITH CHECK (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );

-- ── oracle_audit.audit_log (insert-only, user-scoped read) ──────
ALTER TABLE oracle_audit.audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "audit_log_insert" ON oracle_audit.audit_log
    FOR INSERT WITH CHECK (true);   -- inserts via service role / RLS-wrapped RPC

CREATE POLICY "audit_log_user_read" ON oracle_audit.audit_log
    FOR SELECT USING (
        auth.uid() = user_id OR user_id = oracle_feed.demo_user_id()
    );
-- No UPDATE or DELETE policy → append-only enforced.
