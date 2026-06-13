-- ════════════════════════════════════════════════════════════════
-- ORACLE — Scheduled Jobs (pg_cron) §18
-- Requires pg_cron + pg_net extensions (installed in initial migration).
-- These schedules call Edge Functions / FastAPI via net.http_post.
-- Set the following GUCs before running in production:
--   alter role postgres set app.supabase_functions_url = 'https://<project>.functions.supabase.co';
--   alter role postgres set app.fastapi_url = 'https://oracle-api.railway.app';
--   alter role postgres set app.service_role_key = '<service-role>';
-- ════════════════════════════════════════════════════════════════

-- ── Autopilot monitoring loop (every 5 minutes) ────────────────
SELECT cron.schedule(
    'oracle-autopilot-loop',
    '*/5 * * * *',
    $$SELECT net.http_post(
        url := current_setting('app.supabase_functions_url') || '/autopilot-loop',
        headers := jsonb_build_object(
            'Authorization', 'Bearer ' || current_setting('app.service_role_key'),
            'Content-Type', 'application/json'
        ),
        body := '{}'::jsonb
    )$$
);

-- ── Signal pipeline refresh (every 15 minutes) ──────────────────
SELECT cron.schedule(
    'oracle-signal-refresh',
    '*/15 * * * *',
    $$SELECT net.http_post(
        url := current_setting('app.fastapi_url') || '/api/v1/signals/refresh',
        headers := jsonb_build_object('Content-Type', 'application/json'),
        body := '{}'::jsonb
    )$$
);

-- ── Voice cache cleanup (daily at 3am UTC) ──────────────────────
SELECT cron.schedule(
    'oracle-voice-cache-cleanup',
    '0 3 * * *',
    $$DELETE FROM storage.objects
      WHERE bucket_id = 'oracle-voice-cache'
        AND created_at < now() - interval '24 hours'$$
);

-- ── Simulation accuracy evaluation (daily at 4am UTC) ───────────
-- Checks simulations from 5 days ago against actual prices.
SELECT cron.schedule(
    'oracle-accuracy-evaluation',
    '0 4 * * *',
    $$SELECT net.http_post(
        url := current_setting('app.fastapi_url') || '/api/v1/accuracy/evaluate',
        headers := jsonb_build_object('Content-Type', 'application/json'),
        body := '{}'::jsonb
    )$$
);

-- ── Portfolio snapshot (weekdays at 5pm UTC ≈ market close) ─────
SELECT cron.schedule(
    'oracle-portfolio-snapshot',
    '0 17 * * 1-5',
    $$INSERT INTO oracle_portfolio.portfolio_snapshots
        (user_id, total_value, cash_balance, invested_value, is_paper)
      SELECT p.user_id,
             COALESCE(SUM(p.market_value), 0) + 50000,
             50000,
             COALESCE(SUM(p.market_value), 0),
             true
      FROM oracle_portfolio.positions p
      GROUP BY p.user_id$$
);

-- ── Transparency feed cleanup (weekly, Sunday 2am UTC) ──────────
SELECT cron.schedule(
    'oracle-feed-cleanup',
    '0 2 * * 0',
    $$DELETE FROM oracle_feed.transparency_feed_events
      WHERE created_at < now() - interval '30 days'$$
);
