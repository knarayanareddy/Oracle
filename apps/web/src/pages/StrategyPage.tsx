// ════════════════════════════════════════════════════════════════
// StrategyPage — Plain English Strategy Builder (§04 Module 3)
// NL input → parse → backtest → equity curve + metrics.
// ════════════════════════════════════════════════════════════════
import { useState } from 'react'
import { Sparkles, Play, Loader2, Rocket, FileBarChart } from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import { parseStrategy, backtestStrategy } from '@/lib/api'

const EXAMPLES = [
  'Buy NVDA when RSI drops below 30 and swarm bullish above 60%',
  'Reduce TLT when Polymarket rate-hike probability exceeds 70%',
  'Buy SPY when MACD crosses above signal line',
  'Buy AAPL when news sentiment is very negative and price above EMA50',
]

export default function StrategyPage() {
  const [description, setDescription] = useState('')
  const [parsed, setParsed] = useState<any>(null)
  const [backtest, setBacktest] = useState<any>(null)
  const [loading, setLoading] = useState<'parse' | 'backtest' | null>(null)
  const [error, setError] = useState('')

  const handleParse = async () => {
    if (description.length < 5) return
    setLoading('parse')
    setError('')
    try {
      const result = await parseStrategy(description)
      setParsed(result)
    } catch (e) {
      setError(String(e))
    }
    setLoading(null)
  }

  const handleBacktest = async () => {
    if (!parsed) return
    setLoading('backtest')
    setError('')
    try {
      const result = await backtestStrategy({
        conditions: { entry: parsed.entry, exit: parsed.exit, risk: parsed.risk },
        symbol: 'NVDA',
        layers_used: parsed.entry?.map((e: any) => e.layer).filter(Boolean) || ['L4'],
      })
      setBacktest(result)
    } catch (e) {
      setError(String(e))
    }
    setLoading(null)
  }

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-oracle-primary" />
          Strategy Builder
        </h1>
        <p className="text-sm text-oracle-muted">
          Describe a strategy in plain English — ORACLE parses, backtests, and deploys it
        </p>
      </div>

      {/* NL Input */}
      <div className="oracle-card">
        <label className="text-xs font-medium text-oracle-muted mb-2 block">DESCRIBE YOUR STRATEGY</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. Buy NVDA when RSI drops below 30 and swarm bullish above 60%"
          rows={3}
          className="oracle-input resize-none"
        />
        <div className="flex flex-wrap gap-2 mt-3">
          {EXAMPLES.map((ex) => (
            <button key={ex} onClick={() => setDescription(ex)}
              className="text-xs px-3 py-1.5 rounded-lg bg-oracle-surface2 text-oracle-muted hover:text-oracle-text hover:bg-oracle-border transition-colors">
              {ex.length > 50 ? ex.slice(0, 50) + '...' : ex}
            </button>
          ))}
        </div>
        <div className="flex gap-2 mt-4">
          <button onClick={handleParse} disabled={description.length < 5 || loading !== null}
            className="oracle-btn-primary flex items-center gap-2">
            {loading === 'parse' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Parse Strategy
          </button>
        </div>
      </div>

      {error && <div className="bg-oracle-danger/10 border border-oracle-danger/30 rounded-lg p-3 text-sm text-oracle-danger">{error}</div>}

      {/* Parsed Conditions */}
      {parsed && (
        <div className="oracle-card animate-slide-up">
          <h2 className="text-sm font-semibold mb-4">Parsed Conditions (Structured JSON)</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 className="text-xs text-oracle-muted mb-2">Entry Rules</h3>
              <div className="space-y-2">
                {parsed.entry?.map((rule: any, i: number) => (
                  <div key={i} className="bg-oracle-bg rounded-lg p-2 text-xs">
                    <span className="oracle-layer-pill text-[10px]">{rule.layer}</span>
                    <span className="text-oracle-text ml-2 font-mono">{rule.condition} {rule.operator} {rule.threshold}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-xs text-oracle-muted mb-2">Exit Rules</h3>
              <div className="space-y-2">
                {parsed.exit?.map((rule: any, i: number) => (
                  <div key={i} className="bg-oracle-bg rounded-lg p-2 text-xs">
                    <span className="oracle-layer-pill text-[10px]">{rule.layer}</span>
                    <span className="text-oracle-text ml-2 font-mono">{rule.condition} {rule.operator} {rule.threshold}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-xs text-oracle-muted mb-2">Risk Config</h3>
              <div className="bg-oracle-bg rounded-lg p-2 text-xs space-y-1">
                <div className="flex justify-between"><span className="text-oracle-muted">Max Position</span><span className="font-mono">{(parsed.risk?.max_position_pct * 100).toFixed(0)}%</span></div>
                <div className="flex justify-between"><span className="text-oracle-muted">Stop Loss</span><span className="font-mono">{(parsed.risk?.stop_loss_pct * 100).toFixed(0)}%</span></div>
                <div className="flex justify-between"><span className="text-oracle-muted">Daily Trades</span><span className="font-mono">{parsed.risk?.max_daily_trades}</span></div>
              </div>
            </div>
          </div>
          <button onClick={handleBacktest} disabled={loading !== null}
            className="oracle-btn-primary mt-4 flex items-center gap-2">
            {loading === 'backtest' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileBarChart className="w-4 h-4" />}
            Backtest 2020-2026
          </button>
        </div>
      )}

      {/* Backtest Results */}
      {backtest && (
        <div className="space-y-6 animate-slide-up">
          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Metric label="Total Return" value={`${(backtest.total_return * 100).toFixed(1)}%`} good={backtest.total_return > 0} />
            <Metric label="Alpha vs SPY" value={`${(backtest.alpha * 100).toFixed(1)}%`} good={backtest.alpha > 0} />
            <Metric label="Sharpe" value={backtest.sharpe_ratio.toFixed(2)} good={backtest.sharpe_ratio > 1} />
            <Metric label="Max DD" value={`${(backtest.max_drawdown * 100).toFixed(1)}%`} good={backtest.max_drawdown > -0.2} />
            <Metric label="Win Rate" value={`${(backtest.win_rate * 100).toFixed(0)}%`} good={backtest.win_rate > 0.5} />
          </div>

          {/* Equity Curve */}
          <div className="oracle-card">
            <h2 className="text-sm font-semibold mb-4">Equity Curve</h2>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={backtest.equity_curve}>
                <defs>
                  <linearGradient id="stratGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366F1" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#242D44" />
                <XAxis dataKey="date" tick={{ fill: '#64748B', fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fill: '#64748B', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#111726', border: '1px solid #242D44', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="value" stroke="#6366F1" strokeWidth={2} fill="url(#stratGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Layer Contribution */}
          {backtest.layer_contribution && Object.keys(backtest.layer_contribution).length > 0 && (
            <div className="oracle-card">
              <h2 className="text-sm font-semibold mb-4">Layer Contribution Analysis</h2>
              <div className="space-y-2">
                {Object.entries(backtest.layer_contribution).map(([layer, weight]: [string, any]) => (
                  <div key={layer} className="flex items-center gap-3">
                    <span className="oracle-layer-pill text-[10px] w-8 justify-center">{layer}</span>
                    <div className="flex-1 h-2 bg-oracle-bg rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-oracle-primary to-oracle-accent" style={{ width: `${weight * 100}%` }} />
                    </div>
                    <span className="text-xs font-mono text-oracle-muted w-12 text-right">{(weight * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
              <button className="oracle-btn-ghost mt-4 flex items-center gap-2 w-full justify-center">
                <Rocket className="w-4 h-4" />
                Deploy to Autopilot
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, good }: { label: string; value: string; good: boolean }) {
  return (
    <div className="oracle-card-hover">
      <p className="text-xs text-oracle-muted">{label}</p>
      <p className={`text-lg font-bold font-mono ${good ? 'text-oracle-success' : 'text-oracle-danger'}`}>{value}</p>
    </div>
  )
}
