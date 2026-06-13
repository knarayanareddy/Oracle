// ════════════════════════════════════════════════════════════════
// ORACLE — Mock Data (§23 demo fallback)
// Used when Supabase is not configured (local dev / offline preview).
// ════════════════════════════════════════════════════════════════

export const MOCK_POSITIONS = [
  { symbol: 'NVDA', quantity: 120, avg_entry_price: 810.5, current_price: 1188.25, market_value: 142590, unrealized_pnl: 45330, oracle_signal: 'HOLD' },
  { symbol: 'AAPL', quantity: 300, avg_entry_price: 172.1, current_price: 189.4, market_value: 56820, unrealized_pnl: 5190, oracle_signal: 'BUY' },
  { symbol: 'SPY', quantity: 250, avg_entry_price: 481.2, current_price: 503.1, market_value: 125775, unrealized_pnl: 5475, oracle_signal: 'HOLD' },
  { symbol: 'BTC-USD', quantity: 0.85, avg_entry_price: 42000, current_price: 67250, market_value: 57162.5, unrealized_pnl: 21462.5, oracle_signal: 'WATCH' },
  { symbol: 'TLT', quantity: 400, avg_entry_price: 93.4, current_price: 89.1, market_value: 35640, unrealized_pnl: -1720, oracle_signal: 'HOLD' },
]

export const MOCK_FEED_SEQUENCE = [
  { type: 'data' as const, layer: 'L1', icon: '📡', title: 'Market data synced', detail: '847 assets updated' },
  { type: 'data' as const, layer: 'L3', icon: '📰', title: 'Breaking signal detected', detail: 'Fed signals hold on rates — Reuters' },
  { type: 'data' as const, layer: 'L5', icon: '📊', title: 'Polymarket update', detail: 'Rate hold probability: 71%' },
  { type: 'simulation' as const, layer: 'L6', icon: '🌊', title: 'Swarm simulation launching', detail: '500 agents initializing...' },
  { type: 'simulation' as const, layer: 'L6', icon: '🌊', title: 'Simulation in progress', detail: 'Round 20/40 — 63% bearish emerging' },
  { type: 'simulation' as const, layer: 'L6', icon: '🌊', title: 'Swarm complete', detail: 'Verdict: BEARISH (71% confidence)' },
  { type: 'debate' as const, layer: 'L7', icon: '🤖', title: 'Bull Agent argument', detail: 'Momentum still intact — NVDA RSI oversold' },
  { type: 'debate' as const, layer: 'L7', icon: '🤖', title: 'Bear Agent argument', detail: 'Yield curve inversion + rate fear dominant' },
  { type: 'risk_alert' as const, layer: 'L8', icon: '⚖️', title: 'Risk assessment', detail: 'Portfolio risk: ELEVATED on tech sector' },
  { type: 'action' as const, layer: 'L10', icon: '✅', title: 'Action executed', detail: 'Reduced NVDA: 12% → 8% of portfolio' },
  { type: 'learning' as const, layer: 'L9', icon: '📚', title: 'Lesson learned', detail: 'Lesson #48: Polymarket >70% + bearish swarm → reduce' },
]
