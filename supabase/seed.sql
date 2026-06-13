-- ════════════════════════════════════════════════════════════════
-- ORACLE — Demo Seed Data §23
-- Generates realistic mock data for the hackathon demo.
-- Demo user ID is the canonical DEMO_USER_ID.
-- Run via: supabase db reset (applies migrations + seed.sql)
-- ════════════════════════════════════════════════════════════════

-- ── 1. Demo user profile ────────────────────────────────────────
-- Insert into auth.users first (for FK), then profile.
-- In local Supabase this row is created by the seed; in cloud use the
-- Supabase dashboard to create the user, then this seeds the profile.
INSERT INTO public.profiles (id, display_name, role, locale, timezone, demo_mode)
VALUES ('00000000-0000-0000-0000-000000000001', 'Oracle Demo Trader', 'user', 'en', 'Europe/Amsterdam', true)
ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name;

-- ════════════════════════════════════════════════════════════════
-- 2. Investor DNA profile
-- ════════════════════════════════════════════════════════════════
INSERT INTO oracle_memory.investor_profiles
    (user_id, stated_risk, revealed_risk, avg_hold_days, optimal_hold_days,
     early_exit_count, contrarian_score, macro_sensitivity,
     best_signal_combo, worst_signal_combo, active_personalizations, radar_scores)
VALUES
('00000000-0000-0000-0000-000000000001', 'moderate', 'aggressive', 11.3, 18.0,
 7, 0.62, 0.71, 'L5+L6', 'L3+L4',
 '[{"rule":"Trim tech when yield curve inverts","reason":"Revealed early-exit pattern in rate-hike cycles","applied_at":"2026-05-20T14:00:00Z","source_lesson":12}]'::jsonb,
 '{"risk_appetite":0.74,"patience":0.41,"conviction":0.68,"diversification":0.55,"momentum_bias":0.63,"macro_awareness":0.71}'::jsonb)
ON CONFLICT (user_id) DO NOTHING;

-- ════════════════════════════════════════════════════════════════
-- 3. Portfolio positions (5 seeded)
-- ════════════════════════════════════════════════════════════════
INSERT INTO oracle_portfolio.positions
    (user_id, symbol, asset_class, quantity, avg_entry_price, current_price,
     market_value, unrealized_pnl, unrealized_pct, oracle_signal, signal_confidence, signal_updated_at)
VALUES
('00000000-0000-0000-0000-000000000001','NVDA','equity',120,810.50,1188.25,142590.00,45330.00,0.4661,'HOLD',0.61, now()),
('00000000-0000-0000-0000-000000000001','AAPL','equity',300,172.10,189.40,56820.00,5190.00,0.1005,'BUY',0.58, now()),
('00000000-0000-0000-0000-000000000001','SPY','etf',250,481.20,503.10,125775.00,5475.00,0.0455,'HOLD',0.72, now()),
('00000000-0000-0000-0000-000000000001','BTC-USD','crypto',0.85,42000.00,67250.00,57162.50,21462.50,0.6018,'WATCH',0.49, now()),
('00000000-0000-0000-0000-000000000001','TLT','bond',400,93.40,89.10,35640.00,-1720.00,-0.0460,'HOLD',0.55, now())
ON CONFLICT (user_id, symbol) DO UPDATE SET
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value,
    updated_at = now();

-- ════════════════════════════════════════════════════════════════
-- 4. 90 days of portfolio snapshots (equity curve)
-- ════════════════════════════════════════════════════════════════
DO $$
DECLARE
    d integer;
    base_value numeric := 380000;
    spy_base numeric := 478.00;
    day_value numeric;
    spy_val numeric;
    prev numeric := base_value;
BEGIN
    FOR d IN 1..90 LOOP
        -- Deterministic-ish random walk with slight positive drift
        day_value := prev * (1 + (random() * 0.022 - 0.008));
        prev := day_value;
        spy_val := spy_base * (1 + (d / 90.0) * 0.052 + (random() * 0.02 - 0.01));
        INSERT INTO oracle_portfolio.portfolio_snapshots
            (user_id, snapshot_at, total_value, cash_balance, invested_value,
             daily_pnl, daily_pnl_pct, total_return, benchmark_value, is_paper)
        VALUES
        ('00000000-0000-0000-0000-000000000001',
         now() - ((90 - d) || ' days')::interval,
         round(day_value, 2), 50000, round(day_value - 50000, 2),
         round(day_value * (random() * 0.02 - 0.01), 2),
         round((random() * 0.02 - 0.01)::numeric, 4),
         round(((day_value / base_value) - 1)::numeric, 4),
         round(spy_val, 2), true);
    END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════
-- 5. 8 saved strategies with backtest results
-- ════════════════════════════════════════════════════════════════
INSERT INTO oracle_strategy.strategies
    (user_id, name, description, natural_language_input, parsed_conditions,
     layers_used, status, is_public)
VALUES
('00000000-0000-0000-0000-000000000001','RSI Dip Buyer','Buy oversold large-cap tech','Buy NVDA when RSI drops below 30',
 '{"entry":[{"layer":"L4","condition":"rsi","operator":"<","threshold":30,"asset":"NVDA"}],"exit":[{"layer":"L4","condition":"rsi","operator":">","threshold":65}],"risk":{"max_position_pct":0.15,"stop_loss_pct":0.08,"max_daily_trades":3}}'::jsonb,
 ARRAY['L4'],'backtested', true),
('00000000-0000-0000-0000-000000000001','Swarm-Momentum Hybrid','Combine swarm consensus with EMA trend','Buy when swarm bullish > 60% AND price above EMA50',
 '{"entry":[{"layer":"L6","condition":"swarm_bullish","operator":">","threshold":0.60},{"layer":"L4","condition":"above_ema50","operator":"=","threshold":1}],"exit":[{"layer":"L6","condition":"swarm_bearish","operator":">","threshold":0.55}],"risk":{"max_position_pct":0.12,"stop_loss_pct":0.06,"max_daily_trades":5}}'::jsonb,
 ARRAY['L4','L6'],'backtested', true),
('00000000-0000-0000-0000-000000000001','Polymarket Macro Tilt','Tilt toward rate-sensitive assets on Polymarket signal','Reduce TLT when Polymarket rate-hike prob > 70%',
 '{"entry":[{"layer":"L5","condition":"polymarket_prob","operator":">","threshold":0.70,"asset":"FED"}],"exit":[{"layer":"L5","condition":"polymarket_prob","operator":"<","threshold":0.45}],"risk":{"max_position_pct":0.20,"stop_loss_pct":0.05,"max_daily_trades":2}}'::jsonb,
 ARRAY['L2','L5'],'backtested', false),
('00000000-0000-0000-0000-000000000001','News Sentiment Fade','Fade extreme negative news sentiment on quality names','Buy AAPL when news sentiment very negative AND fundamentals strong',
 '{"entry":[{"layer":"L3","condition":"sentiment","operator":"<","threshold":-0.6,"asset":"AAPL"}],"exit":[{"layer":"L3","condition":"sentiment","operator":">","threshold":0.2}],"risk":{"max_position_pct":0.10,"stop_loss_pct":0.07,"max_daily_trades":4}}'::jsonb,
 ARRAY['L3'],'backtested', false),
('00000000-0000-0000-0000-000000000001','MACD Golden Cross','Classic MACD crossover on SPY','Buy SPY when MACD crosses above signal line',
 '{"entry":[{"layer":"L4","condition":"macd_cross_up","operator":"=","threshold":1,"asset":"SPY"}],"exit":[{"layer":"L4","condition":"macd_cross_down","operator":"=","threshold":1}],"risk":{"max_position_pct":0.25,"stop_loss_pct":0.04,"max_daily_trades":1}}'::jsonb,
 ARRAY['L4'],'deployed', true),
('00000000-0000-0000-0000-000000000001','Bollinger Bounce','Mean reversion off lower Bollinger Band','Buy when close below lower BB and RSI < 35',
 '{"entry":[{"layer":"L4","condition":"price_below_bb_lower","operator":"=","threshold":1},{"layer":"L4","condition":"rsi","operator":"<","threshold":35}],"exit":[{"layer":"L4","condition":"price_above_ema20","operator":"=","threshold":1}],"risk":{"max_position_pct":0.08,"stop_loss_pct":0.05,"max_daily_trades":6}}'::jsonb,
 ARRAY['L4'],'backtested', false),
('00000000-0000-0000-0000-000000000001','Full Oracle Stack','Uses all intelligence layers','Buy when swarm bullish + polymarket corroboration + technical confirmation',
 '{"entry":[{"layer":"L6","condition":"swarm_bullish","operator":">","threshold":0.60},{"layer":"L5","condition":"polymarket_prob","operator":">","threshold":0.60},{"layer":"L4","condition":"above_ema50","operator":"=","threshold":1}],"exit":[{"layer":"L8","condition":"risk_score","operator":">","threshold":7}],"risk":{"max_position_pct":0.18,"stop_loss_pct":0.09,"max_daily_trades":3}}'::jsonb,
 ARRAY['L4','L5','L6','L7','L8'],'deployed', true),
('00000000-0000-0000-0000-000000000001','BTC Volatility Harvest','Crypto-specific momentum with ATR filter','Buy BTC when EMA20 > EMA50 and ATR low',
 '{"entry":[{"layer":"L4","condition":"ema_cross_up","operator":"=","threshold":1,"asset":"BTC-USD"},{"layer":"L4","condition":"atr_low","operator":"=","threshold":1}],"exit":[{"layer":"L4","condition":"ema_cross_down","operator":"=","threshold":1}],"risk":{"max_position_pct":0.05,"stop_loss_pct":0.12,"max_daily_trades":2}}'::jsonb,
 ARRAY['L1','L4'],'draft', false)
ON CONFLICT DO NOTHING;

-- Backtest results for each strategy
INSERT INTO oracle_strategy.backtest_results
    (strategy_id, start_date, end_date, initial_capital, final_capital, total_return,
     benchmark_return, alpha, sharpe_ratio, sortino_ratio, max_drawdown, win_rate,
     profit_factor, total_trades, swarms_triggered, layer_contribution, equity_curve, monthly_returns)
SELECT s.id, '2022-01-03', '2026-06-01', 100000,
       100000 * (1 + (random() * 0.9 + 0.05)),
       random() * 0.9 + 0.05,
       0.38,
       (random() * 0.5),
       random() * 2.4 + 0.3,
       random() * 3.1 + 0.5,
       -(random() * 0.25 + 0.05),
       random() * 0.35 + 0.45,
       random() * 2.5 + 0.6,
       (random() * 200 + 40)::int,
       (random() * 80 + 10)::int,
       jsonb_build_object('L4', random()*0.5, 'L5', random()*0.4, 'L6', random()*0.6, 'L3', random()*0.2),
       '[{"date":"2022-03","value":102000,"spy_value":98000},{"date":"2023-03","value":145000,"spy_value":112000},{"date":"2024-03","value":178000,"spy_value":128000},{"date":"2025-03","value":156000,"spy_value":141000},{"date":"2026-03","value":198000,"spy_value":153000}]'::jsonb,
       '[{"month":"2024-01","return":0.041},{"month":"2024-02","return":-0.012},{"month":"2024-03","return":0.058}]'::jsonb
FROM oracle_strategy.strategies s;

-- ════════════════════════════════════════════════════════════════
-- 6. Past simulations (47) + accuracy records + learning log
-- ════════════════════════════════════════════════════════════════
DO $$
DECLARE
    i integer;
    sim_id uuid;
    bull numeric;
    bear numeric;
    neutr numeric;
    vtext text;
    seed_texts text[] := ARRAY[
        'Fed signals two rate hikes in 2026','NVDA beats earnings by 12%',
        'CPI comes in hotter than expected','ECB holds rates steady',
        'Apple announces $110B buyback','Tesla deliveries miss estimates',
        'Fed Powell dovish press conference','Oil prices spike on geopolitical tension',
        'Bitcoin breaks all-time high','Unemployment claims rise sharply',
        'Microsoft Azure revenue +29%','Meta announces dividend',
        'Semiconductor shortage eases','Recession odds jump on Polymarket',
        'Inflation cools to 2.8%','Bank earnings beat consensus',
        'Yield curve uninverts','AI capex spending surges',
        'Consumer spending slows','GDP growth revised down',
        'Factory orders decline','Job openings hit 3-year low',
        'Powell: higher for longer','PCE inflation inline with expectations',
        'Housing starts rebound','Retail sales beat expectations',
        'ISM manufacturing contracts','Initial jobless claims fall',
        'Treasury auction weak demand','Dollar strengthens on rate bets',
        'Gold hits record high','Oil drops on demand fears',
        'Tech selloff accelerates','Small caps rally on rate hopes',
        'Bitcoin ETF inflows surge','Stablecoin regulation passes',
        'AI chip export restrictions','Quantum computing breakthrough',
        'Cyberattack on major exchange','Hedge fund de-grossing',
        'Options market signals vol spike','Insider selling hits records',
        'Short interest at multi-year low','Margin debt rising',
        'JOLTs data disappoints','Philly Fed index negative',
        'Hawkish Fed minutes released','Dovish dot plot surprises market'
    ];
    is_correct boolean;
BEGIN
    FOR i IN 1..47 LOOP
        bull := round((random() * 0.8 + 0.05)::numeric, 4);
        bear := round((random() * (0.95 - bull))::numeric, 4);
        neutr := round((1 - bull - bear)::numeric, 4);
        IF bull > bear AND bull > neutr THEN vtext := 'BULLISH';
        ELSIF bear > bull AND bear > neutr THEN vtext := 'BEARISH';
        ELSE vtext := 'NEUTRAL'; END IF;

        INSERT INTO oracle_simulation.simulations
            (user_id, title, seed_text, seed_type, status, agent_count, round_count,
             current_round, llm_model, final_bullish, final_bearish, final_neutral,
             confidence, verdict, narrative, accuracy_verified, tokens_used, cost_usd,
             started_at, completed_at, created_at)
        VALUES
        ('00000000-0000-0000-0000-000000000001',
         left(seed_texts[i], 60), seed_texts[i],
         CASE WHEN i % 3 = 0 THEN 'earnings' WHEN i % 3 = 1 THEN 'fed_statement' ELSE 'news' END,
         'complete',
         (random() * 500 + 200)::int,
         CASE WHEN i % 2 = 0 THEN 40 ELSE 30 END,
         CASE WHEN i % 2 = 0 THEN 40 ELSE 30 END,
         CASE WHEN i % 2 = 0 THEN 'qwen-plus' ELSE 'gpt-4o-mini' END,
         bull, bear, neutr,
         round((random() * 0.4 + 0.5)::numeric, 4),
         vtext,
         CASE vtext WHEN 'BEARISH' THEN 'Rate fear overriding earnings optimism; retail panic emerging'
                    WHEN 'BULLISH' THEN 'Institutional accumulation detected; retail following with lag'
                    ELSE 'Mixed signals; institutions cautious, retail divided' END,
         i < 40,
         (random() * 3000000 + 200000)::int,
         round((random() * 2 + 0.1)::numeric, 4),
         now() - ((50 - i) || ' days')::interval,
         now() - ((50 - i) || ' days')::interval + '90 seconds'::interval,
         now() - ((50 - i) || ' days')::interval)
        RETURNING id INTO sim_id;

        -- accuracy record for verified sims
        IF i < 40 THEN
            is_correct := random() > 0.26;  -- ~74% accuracy per ADR-007
            INSERT INTO oracle_memory.simulation_accuracy
                (user_id, simulation_id, signal_combo, predicted_direction,
                 actual_direction, is_correct, confidence_at_prediction)
            VALUES
            ('00000000-0000-0000-0000-000000000001', sim_id,
             CASE WHEN i % 2 = 0 THEN 'L5+L6' ELSE 'L3+L6' END,
             vtext,
             CASE WHEN is_correct THEN vtext ELSE CASE vtext WHEN 'BULLISH' THEN 'BEARISH' ELSE 'BULLISH' END END,
             is_correct,
             round((random() * 0.3 + 0.6)::numeric, 4));

            -- learning log entry
            INSERT INTO oracle_memory.learning_log
                (user_id, lesson_text, confidence, tags, source_type, source_id,
                 signal_combo, validated, times_applied)
            VALUES
            ('00000000-0000-0000-0000-000000000001',
             CASE WHEN is_correct THEN
                'Swarm correctly predicted ' || vtext || ' reaction for: ' || left(seed_texts[i],40)
              ELSE
                'Swarm overestimated conviction on: ' || left(seed_texts[i],40) || ' — reduce confidence weight'
              END,
             (random() * 2 + 3)::int,
             ARRAY[CASE WHEN i % 2 = 0 THEN 'macro' ELSE 'earnings' END, vtext::text],
             'simulation_outcome', sim_id,
             CASE WHEN i % 2 = 0 THEN 'L5+L6' ELSE 'L3+L6' END,
             is_correct, (random() * 5)::int);
        END IF;
    END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════
-- 7. Signal events across all 5 layers (last 24h)
-- ════════════════════════════════════════════════════════════════
INSERT INTO oracle_signals.signal_events (layer, signal_type, asset, direction, strength, confidence, raw_value, context, detected_at)
VALUES
('L1','price_update','NVDA','bullish',4,0.92,1188.25,'NVDA +2.3% on heavy volume', now() - interval '12 min'),
('L1','price_update','SPY','neutral',2,0.7,503.10,'SPY flat intraday', now() - interval '12 min'),
('L2','macro','10y_treasury','bearish',3,0.81,4.32,'10Y yield rising — pressure on growth names', now() - interval '40 min'),
('L2','macro','yield_curve','contrarian',3,0.76,-0.18,'Yield curve inverted — recession signal', now() - interval '1 hour'),
('L3','news_sentiment','NVDA','bullish',4,0.78,0.62,'Positive earnings sentiment across 23 articles', now() - interval '25 min'),
('L3','news_sentiment','tech_sector','bearish',3,0.69,-0.34,'Rate-hike fear dominating fintwit', now() - interval '25 min'),
('L4','technical','NVDA','neutral',2,0.65,52.1,'RSI 52 — neither overbought nor oversold', now() - interval '8 min'),
('L4','technical','AAPL','bullish',4,0.74,1,'MACD golden cross detected', now() - interval '8 min'),
('L5','polymarket','FED','bearish',5,0.88,0.71,'Rate hike probability: 71% (up from 62%)', now() - interval '20 min'),
('L5','polymarket','recession','bearish',3,0.62,0.34,'US recession 2026 probability: 34%', now() - interval '20 min');

-- Technical + macro + polymarket snapshots
INSERT INTO oracle_signals.technical_snapshots (asset, rsi, macd, macd_signal, bb_upper, bb_lower, ema_20, ema_50, atr, signal_read)
VALUES
('NVDA',52.1,1.85,1.40,1210.0,1090.0,1160.0,1120.0,28.4,'neutral'),
('AAPL',58.3,0.92,0.71,195.0,181.0,187.5,184.2,3.1,'bullish_cross'),
('SPY',54.8,1.12,0.95,512.0,492.0,501.0,495.0,5.2,'neutral');

INSERT INTO oracle_signals.macro_snapshots (series_id, label, value, previous_value, change_pct)
VALUES
('FEDFUNDS','Fed Funds Rate',5.50,5.50,0.0),
('DGS10','10Y Treasury',4.32,4.28,0.0093),
('T10Y2Y','Yield Curve Spread',-0.18,-0.15,-0.20),
('CPIAUCSL','CPI YoY',2.9,3.1,-0.0645),
('UNRATE','Unemployment',4.1,4.0,0.025);

INSERT INTO oracle_signals.polymarket_snapshots (market_id, question, yes_probability, no_probability, volume_24h)
VALUES
('fed-hike','Will the Fed raise rates at the next meeting?',0.71,0.29,2400000),
('recession','Will there be a US recession in 2026?',0.34,0.66,1800000),
('sp500-up','Will S&P 500 end the month above current level?',0.42,0.58,950000);

-- ════════════════════════════════════════════════════════════════
-- 8. 100 transparency feed events (last session)
-- ════════════════════════════════════════════════════════════════
DO $$
DECLARE
    types text[] := ARRAY['data','simulation','action','risk_alert','learning','debate','system'];
    layers text[] := ARRAY['L1','L2','L3','L4','L5','L6','L7','L8','L9','L10'];
    icons text[] := ARRAY['📡','📰','📊','🌊','🤖','⚖️','✅','📚','⚡','🎯'];
    titles text[] := ARRAY['Market data synced','Breaking signal detected','Polymarket update','Swarm simulation launching','Swarm complete','Bull Agent argument','Bear Agent argument','Risk assessment','Action executed','Lesson learned'];
    details text[] := ARRAY['847 assets updated','Fed signals hold on rates — Reuters','Rate hold probability: 71%','500 agents initializing...','Verdict: BEARISH (71% confidence)','Momentum still intact — NVDA RSI oversold','Yield curve inversion + rate fear dominant','Portfolio risk: ELEVATED on tech sector','Reduced NVDA: 12% to 8% of portfolio','Polymarket >70% + bearish swarm = reduce'];
    i integer;
BEGIN
    FOR i IN 1..100 LOOP
        INSERT INTO oracle_feed.transparency_feed_events
            (user_id, event_type, layer, icon, title, detail, created_at)
        VALUES
        ('00000000-0000-0000-0000-000000000001',
         types[1 + (i % 7)],
         layers[1 + (i % 10)],
         icons[1 + (i % 10)],
         titles[1 + (i % 10)],
         details[1 + (i % 10)],
         now() - ((100 - i) || ' seconds')::interval);
    END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════
-- 9. Knowledge graph nodes (50 assets, 20 events, 10 strategies)
-- ════════════════════════════════════════════════════════════════
DO $$
DECLARE
    assets text[] := ARRAY['NVDA','AAPL','MSFT','GOOGL','AMZN','META','TSLA','JPM','SPY','QQQ','BTC','ETH','TLT','GLD','XLF','XLK','V','MA','NVDA','AMD'];
    a text;
    i integer;
BEGIN
    FOREACH a IN ARRAY assets LOOP
        INSERT INTO oracle_memory.memory_nodes (user_id, node_type, label, properties)
        VALUES ('00000000-0000-0000-0000-000000000001','asset', a,
                jsonb_build_object('class', CASE WHEN a IN ('BTC','ETH') THEN 'crypto' WHEN a IN ('TLT','GLD') THEN 'etf_bond' ELSE 'equity' END));
    END LOOP;

    FOR i IN 1..20 LOOP
        INSERT INTO oracle_memory.memory_nodes (user_id, node_type, label, properties)
        VALUES ('00000000-0000-0000-0000-000000000001','event', 'Event-' || i,
                jsonb_build_object('type', CASE i % 3 WHEN 0 THEN 'earnings' WHEN 1 THEN 'macro' ELSE 'fed' END,
                                   'impact', (random() * 0.1 - 0.05)));
    END LOOP;

    FOR i IN 1..10 LOOP
        INSERT INTO oracle_memory.memory_nodes (user_id, node_type, label, properties)
        VALUES ('00000000-0000-0000-0000-000000000001','strategy', 'Strategy-' || i,
                jsonb_build_object('alpha', random() * 0.4));
    END LOOP;
END $$;
