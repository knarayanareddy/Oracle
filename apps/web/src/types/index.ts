// ════════════════════════════════════════════════════════════════
// ORACLE — TypeScript Types (§08 canonical field names)
// Single Source of Truth for frontend type definitions.
// ════════════════════════════════════════════════════════════════

export type SignalDirection = 'bullish' | 'bearish' | 'neutral' | 'contrarian'
export type SignalStrength = 1 | 2 | 3 | 4 | 5
export type Layer = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6' | 'L7' | 'L8' | 'L9' | 'L10'
export type OracleSignal = 'BUY' | 'SELL' | 'HOLD' | 'REDUCE' | 'WATCH'
export type Verdict = 'BULLISH' | 'BEARISH' | 'NEUTRAL'
export type AssetClass = 'equity' | 'etf' | 'crypto' | 'bond' | 'commodity'
export type VoiceState = 'idle' | 'listening' | 'processing' | 'responding'

// ── Portfolio ──
export interface Position {
  id: string
  user_id: string
  symbol: string
  asset_class: AssetClass
  quantity: number
  avg_entry_price: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pct: number
  oracle_signal: OracleSignal | null
  signal_confidence: number | null
  is_paper: boolean
}

export interface PortfolioSnapshot {
  id: string
  snapshot_at: string
  total_value: number
  cash_balance: number
  invested_value: number
  daily_pnl: number | null
  daily_pnl_pct: number | null
  total_return: number | null
  benchmark_value: number | null
}

export interface Trade {
  id: string
  symbol: string
  action: 'BUY' | 'SELL' | 'REBALANCE'
  quantity: number
  price: number
  total_value: number
  reasoning: string | null
  layers_activated: string[]
  swarm_bullish_pct: number | null
  polymarket_prob: number | null
  is_paper: boolean
  is_autopilot: boolean
  executed_at: string
}

// ── Simulation ──
export interface Simulation {
  id: string
  title: string
  seed_text: string
  seed_type: string
  status: 'pending' | 'running' | 'complete' | 'failed'
  agent_count: number
  round_count: number
  current_round: number
  agent_mix: Record<string, number>
  llm_model: string
  final_bullish: number | null
  final_bearish: number | null
  final_neutral: number | null
  confidence: number | null
  verdict: Verdict | null
  narrative: string | null
  tokens_used: number | null
  cost_usd: number | null
  created_at: string
}

export interface SimulationRound {
  id: string
  simulation_id: string
  round_number: number
  bullish_pct: number
  bearish_pct: number
  neutral_pct: number
  interactions: number
  opinion_shifts: number
  coalitions: number
  dominant_narrative: string | null
}

export interface SimulationReport {
  verdict: Verdict
  confidence: number
  executive_summary: string
  narrative_themes: { theme: string; prevalence: number; agents: number }[]
  institutional_consensus: string
  retail_consensus: string
  media_framing: string
  predicted_impacts: Record<string, number>
  recommended_actions: { action: string; asset: string; rationale: string }[]
}

// ── Signals ──
export interface SignalEvent {
  id: string
  layer: Layer
  signal_type: string
  asset: string | null
  direction: SignalDirection | null
  strength: number | null
  confidence: number | null
  raw_value: number | null
  context: string | null
  detected_at: string
}

// ── Strategy ──
export interface Strategy {
  id: string
  name: string
  description: string | null
  natural_language_input: string
  parsed_conditions: ParsedConditions
  layers_used: Layer[]
  status: 'draft' | 'backtested' | 'deployed' | 'archived'
  is_public: boolean
  created_at: string
}

export interface ParsedConditions {
  entry: Condition[]
  exit: Condition[]
  risk: RiskConfig
}

export interface Condition {
  layer: string
  condition: string
  operator: string
  threshold: number
  asset?: string
}

export interface RiskConfig {
  max_position_pct: number
  stop_loss_pct: number
  max_daily_trades: number
}

export interface BacktestResult {
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  benchmark_return: number
  alpha: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  win_rate: number
  profit_factor: number
  total_trades: number
  equity_curve: { date: string; value: number; spy_value: number }[]
  layer_contribution: Record<string, number>
}

// ── Memory ──
export interface InvestorProfile {
  stated_risk: string | null
  revealed_risk: string | null
  risk_discrepancy: boolean
  avg_hold_days: number | null
  best_signal_combo: string | null
  worst_signal_combo: string | null
  radar_scores: {
    risk_appetite: number
    patience: number
    conviction: number
    diversification: number
    momentum_bias: number
    macro_awareness: number
  }
}

export interface LearningLogEntry {
  id: string
  lesson_number: number
  lesson_text: string
  confidence: number
  tags: string[]
  source_type: string
  signal_combo: string | null
  validated: boolean
  times_applied: number
  learned_at: string
}

// ── Autopilot ──
export interface AutopilotSession {
  id: string
  status: 'active' | 'paused' | 'stopped'
  paper_mode: boolean
  max_daily_trades: number
  scan_interval_seconds: number
  session_start: string
  total_trades: number
  session_pnl: number
}

export interface AutopilotDecision {
  id: string
  trigger_signal: string
  trigger_layer: string
  bull_argument: string
  bear_argument: string
  consensus: 'BUY' | 'SELL' | 'HOLD' | 'REDUCE' | 'REBALANCE'
  consensus_confidence: number
  reasoning_trail: Record<string, unknown>
  layers_activated: string[]
  decided_at: string
}

// ── Transparency Feed ──
export interface FeedEvent {
  id: string
  event_type: 'data' | 'simulation' | 'action' | 'risk_alert' | 'learning' | 'debate' | 'system'
  layer: Layer | null
  icon: string
  title: string
  detail: string | null
  created_at: string
}

// ── Layer Metadata ──
export interface LayerInfo {
  id: Layer
  name: string
  source: string
  freq: string
  icon: string
}

export const LAYERS: LayerInfo[] = [
  { id: 'L1', name: 'Market Data', source: 'yfinance / Alpha Vantage', freq: 'Real-time', icon: '📡' },
  { id: 'L2', name: 'Macro Signals', source: 'FRED API', freq: 'Daily', icon: '🏛️' },
  { id: 'L3', name: 'News + Sentiment', source: 'NewsAPI + FinBERT', freq: '15 minutes', icon: '📰' },
  { id: 'L4', name: 'Technical Indicators', source: 'Computed from L1', freq: 'Real-time', icon: '📈' },
  { id: 'L5', name: 'Polymarket Signals', source: 'Polymarket API', freq: '15 minutes', icon: '📊' },
  { id: 'L6', name: 'Swarm Engine', source: 'MiroFish / OASIS', freq: 'On-demand', icon: '🌊' },
  { id: 'L7', name: 'Multi-Agent Debate', source: 'LangChain agents', freq: 'Per L6 run', icon: '🤖' },
  { id: 'L8', name: 'Risk Scoring', source: 'Custom engine', freq: 'Per rec', icon: '⚖️' },
  { id: 'L9', name: 'GraphRAG Memory', source: 'Neo4j / Zep Cloud', freq: 'Per interaction', icon: '🧠' },
  { id: 'L10', name: 'Explanation Generator', source: 'GPT-4o', freq: 'Per rec', icon: '✨' },
]
