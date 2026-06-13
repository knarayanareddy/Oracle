// ════════════════════════════════════════════════════════════════
// ORACLE — Shared Types (shared between web + edge functions)
// Re-exports the canonical types from the web app.
// ════════════════════════════════════════════════════════════════
export type {
  SignalDirection, Layer, OracleSignal, Verdict, AssetClass, VoiceState,
  Position, PortfolioSnapshot, Trade, Simulation, SimulationRound, SimulationReport,
  SignalEvent, Strategy, BacktestResult, InvestorProfile, LearningLogEntry,
  AutopilotSession, AutopilotDecision, FeedEvent,
} from '../../apps/web/src/types'
