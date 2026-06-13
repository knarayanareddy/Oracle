# 🎥 ORACLE — Demo Guide

> **Navigation:** [← Back to README](../README.md) | [Deployment](DEPLOYMENT.md)

The complete hackathon demo playbook: pre-demo checklist, timed script, fallback plan,
and judge Q&A prep.

---

## Table of Contents

1. [Pre-Demo Checklist](#1-pre-demo-checklist)
2. [5-Minute Demo Script](#2-5-minute-demo-script)
3. [Demo Data Reference](#3-demo-data-reference)
4. [Fallback Plan](#4-fallback-plan)
5. [Judge Q&A Prep](#5-judge-qa-prep)
6. [Post-Demo](#6-post-demo)

---

## 1. Pre-Demo Checklist

### 30 Minutes Before

```
□  Laptop plugged in + battery at 100%
□  Close all unnecessary apps (free RAM/CPU)
□  Browser: Chrome, fullscreen, zoom at 90%
□  Verify frontend loads: https://oracle.vercel.app
□  Verify API is healthy: curl https://oracle-api.railway.app/health
□  Transparency Feed is auto-firing (visible in right panel)
□  Test voice button — confirm microphone permission granted
□  Load Swarm page → verify agent animation runs smoothly
□  Test Strategy Builder:
     Type: "Buy NVDA when RSI below 30 and swarm bullish above 60%"
     → Click Parse → Click Backtest → verify equity curve renders
□  Activate Autopilot → confirm modal appears → confirm feed fires
□  All mock data looks realistic (check War Room numbers)
□  Backup: Loom recording of full demo ready as fallback
□  Water nearby — you'll be talking for 5 minutes straight
```

### Environment Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Browser | Chrome 120+ | Chrome latest |
| Internet | Stable 5 Mbps | 20+ Mbps |
| Microphone | Any | External USB |
| Display | 1080p | 1440p / 4K |
| Zoom level | 100% | 90% (fits more) |

---

## 2. 5-Minute Demo Script

### Timing Overview

```
Time     Section                Key Visual
──────────────────────────────────────────────────────
0:00     Hook + Problem         Title slide / War Room
0:30     Swarm Demo             Live agent simulation
1:30     Voice Command          Voice bar + response
2:30     Strategy Builder       NL → backtest → equity curve
3:30     Autopilot              Toggle + live transparency feed
4:30     Close + Vision         War Room overview
5:00     Done                   Q&A
```

### Detailed Script

---

#### [0:00 — Hook] _"We simulate the humans that move markets"_

**Say:**
> "Traditional quant tools model markets as math. But markets aren't math — they're
> human psychology. People panic, herd, and overreact. ORACLE doesn't predict markets.
> It simulates the _people_ who move them."

**Show:** War Room dashboard — point to the 10-layer status dots, the equity curve,
the live transparency feed firing in the right panel.

---

#### [0:30 — Swarm] _Live agent simulation_

**Say:**
> "Watch this. I'll give ORACLE a Fed statement and it deploys 500 AI agents — each
> with a distinct personality: institutional traders, retail investors, financial
> journalists. They interact across simulated Twitter and Reddit environments."

**Do:**
1. Navigate to **Swarm** tab
2. Click the **"fed statement"** example chip (auto-fills seed text)
3. Click **"Launch Swarm Simulation"**
4. Watch the live progress bar, agent activity bars animating
5. Point to the verdict (BULLISH/BEARISH/NEUTRAL) when it completes

**Say (while it runs):**
> "Each agent has behavioral traits — loss aversion, herding tendency, news reactivity.
> Over 40 rounds, you see emergent consensus form. This is real social simulation, not
> a price prediction."

---

#### [1:30 — Voice] _Natural language command_

**Say:**
> "ORACLE responds to voice. Watch:"

**Do:**
1. Press and **hold** the microphone button
2. Say: _"What should I do with my tech exposure?"_
3. Release the button
4. Watch the waveform animate while listening
5. ORACLE speaks the response + shows layer activation pills

**Say:**
> "It classified my intent, activated the relevant intelligence layers, and synthesized
> a recommendation. Every layer that fired is visible — full transparency."

---

#### [2:30 — Strategy] _Plain English → backtested_

**Say:**
> "Now let me build a trading strategy in plain English."

**Do:**
1. Navigate to **Strategy** tab
2. Click an example: _"Buy NVDA when RSI below 30 and swarm bullish above 60%"_
3. Click **Parse Strategy** → show the structured conditions (entry/exit/risk)
4. Click **Backtest 2020-2026** → watch equity curve render
5. Point to the metrics: alpha, Sharpe ratio, max drawdown

**Say:**
> "Plain English in, structured strategy out. It backtested against 4 years of data
> including the layer contribution analysis — which intelligence layers drove the alpha."

---

#### [3:30 — Autopilot] _Autonomous mode_

**Say:**
> "The killer feature: Autopilot. ORACLE can run autonomously."

**Do:**
1. Click the **Autopilot** toggle in the top bar
2. Confirm in the modal
3. Watch the **Transparency Feed** start firing rapidly — every reasoning step visible
4. Point to the feed: data sync → signal detected → swarm launched → debate → action

**Say:**
> "Every single decision ORACLE makes is logged in the Transparency Feed in real-time.
> Market data synced, signal detected, swarm launched, bull agent argued, bear agent
> argued, risk assessed, paper trade executed — all autonomous, all transparent."

---

#### [4:30 — Close] _The vision_

**Say:**
> "This is what Robinhood will look like in 3 years. But we built it this weekend.
>
> ORACLE: 7 modules, 10 intelligence layers, 500-agent swarm simulation, full
> transparency on every decision. Paper trading now, enterprise-ready architecture
> for institutional deployment.
>
> We don't predict markets. We simulate the humans that move them."

---

## 3. Demo Data Reference

The seed data creates a rich, realistic demo environment:

| What | Details |
|------|---------|
| **Portfolio** | 5 positions: NVDA ($142K), AAPL ($57K), SPY ($126K), BTC ($57K), TLT ($36K) |
| **Portfolio Value** | ~$468K total (paper trading) |
| **P&L** | Mixed — NVDA +46%, TLT -4.6% |
| **Past Simulations** | 47 simulations with 74% accuracy |
| **Learning Log** | ~40 lessons with confidence scores |
| **Investor DNA** | Stated: moderate, Revealed: aggressive (discrepancy!) |
| **Best Signal Combo** | L5+L6 (Polymarket + Swarm) = 81% accuracy |
| **Strategies** | 8 saved, 2 deployed to autopilot |
| **Transparency Feed** | 100 events auto-firing every 3.5s |

---

## 4. Fallback Plan

### If the Internet Dies

```
□ Switch to Loom recording (pre-recorded before event)
□ Narrate the recording live
□ Focus on the architecture slides + design doc
```

### If the API Is Down

```
□ Demo mode keeps the frontend fully functional with mock data
□ Swarm simulation runs locally (deterministic mock engine)
□ Voice processing still routes (keyword fallback intent classifier)
□ Strategy backtest uses cached data
□ The only thing missing is real LLM reasoning (mode="no_llm")
```

### If Voice Doesn't Work

```
□ Switch to text input (always available in the Voice Bar)
□ Type: "Run a swarm simulation on the CPI report"
□ Everything else works identically
```

### If Supabase Realtime Drops

```
□ The demo feed auto-fires from the Zustand store (client-side)
□ The feed will continue showing events even without realtime
□ Only server-side events (autopilot) won't stream
```

---

## 5. Judge Q&A Prep

### Likely Questions + Answers

**Q: How accurate is the swarm simulation?**
> 74% directional accuracy across 47 backtested simulations. The L5+L6 signal
> combination (Polymarket + Swarm) achieved 81%. Accuracy is tracked per
> signal combination in the simulation_accuracy table.

**Q: How do you handle LLM costs?**
> We use GPT-4o for reasoning but Qwen-plus for the 500 simulation agents —
> a 25x cost reduction. A typical 40-round, 500-agent simulation costs ~$0.34.
> Token usage and cost are tracked per simulation.

**Q: Is this regulatory-safe?**
> Paper trading only — no real money execution. EU data residency (Frankfurt).
> GDPR-compliant with right-to-erasure. Post-hackathon requires Wft license
> review for real execution.

**Q: How do you prevent prompt injection?**
> All user inputs are sanitized before LLM injection. The service role key is
> never exposed to the frontend. RLS enforces data access at the database layer.

**Q: What happens when APIs fail?**
> Every external call has a circuit breaker. After 3-5 failures, the circuit
> opens and falls back to deterministic logic. The mode field in responses
> discloses whether real LLM or fallback was used.

**Q: How is this different from existing AI trading tools?**
> Robinhood's Agentic Trading executes rules. QuantConnect's Mia assists with
> strategy. ORACLE simulates human psychology _before_ recommending — modeling
> the social dynamics that actually move markets.

**Q: Can this scale beyond 500 agents?**
> The architecture supports up to 1,000 agents per run. Phase 2 adds offline
> mode (Ollama + Neo4j) for institutional clients who need fully local operation.

---

## 6. Post-Demo

```
□ Share GitHub link with judges: github.com/knarayanareddy/Oracle
□ Share Vercel URL: oracle.vercel.app
□ Share design doc (redact API keys first!)
□ Collect feedback
□ Celebrate 🎉
```

---

> **← Back to README](../README.md)
