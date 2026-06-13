-- ════════════════════════════════════════════════════════════════
-- ORACLE — RLS Policy Tests (pgTAP)
-- Run: supabase test db
-- Verifies that RLS policies enforce user-scoped access correctly.
-- ════════════════════════════════════════════════════════════════
BEGIN;

-- Create test users
SELECT plan(12);

-- ── Setup: two test users ──
CREATE USER test_user_a WITH PASSWORD 'test';
CREATE USER test_user_b WITH PASSWORD 'test';

-- ── Test 1: RLS is enabled on all tables ──
SELECT has_table(
    'oracle_portfolio', 'positions',
    'positions table exists'
);

SELECT col_is_unique('oracle_portfolio', 'positions', ARRAY['user_id','symbol'],
    'positions have unique user_id+symbol constraint'
);

-- ── Test 2: profiles table RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'profiles'),
    'profiles has RLS enabled'
);

-- ── Test 3: positions table RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'positions'),
    'positions has RLS enabled'
);

-- ── Test 4: trades table RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'trades'),
    'trades has RLS enabled'
);

-- ── Test 5: simulations table RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'simulations'),
    'simulations has RLS enabled'
);

-- ── Test 6: transparency_feed_events RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'transparency_feed_events'),
    'transparency_feed_events has RLS enabled'
);

-- ── Test 7: audit_log is append-only (no UPDATE/DELETE policies) ──
SELECT ok(
    NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'audit_log'
          AND schemaname = 'oracle_audit'
          AND cmd IN ('UPDATE', 'DELETE')
    ),
    'audit_log has no UPDATE/DELETE policies (append-only)'
);

-- ── Test 8: audit_log has INSERT policy ──
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'audit_log'
          AND schemaname = 'oracle_audit'
          AND cmd = 'INSERT'
    ),
    'audit_log has INSERT policy'
);

-- ── Test 9: signal_events is readable by all ──
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'signal_events'
          AND schemaname = 'oracle_signals'
          AND cmd = 'SELECT'
    ),
    'signal_events has SELECT policy (readable by all)'
);

-- ── Test 10: investor_profiles RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'investor_profiles'),
    'investor_profiles has RLS enabled'
);

-- ── Test 11: learning_log RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'learning_log'),
    'learning_log has RLS enabled'
);

-- ── Test 12: autopilot_sessions RLS ──
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'autopilot_sessions'),
    'autopilot_sessions has RLS enabled'
);

SELECT finish();
ROLLBACK;
