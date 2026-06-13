// ════════════════════════════════════════════════════════════════
// WarRoom — Main Dashboard (§04 Module 7)
// Portfolio equity curve, positions, signal matrix, layer status,
// latest learning summary.
// ════════════════════════════════════════════════════════════════
import { useEffect, useState } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine, Line,
  ComposedChart,
} from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Activity, Brain } from 'lucide-react'
import { supabase, DEMO_USER_ID } from '@/lib/supabase'
import { LAYERS, type Position, type PortfolioSnapshot, type SignalEvent, type LearningLogEntry } from '@/types'
import { useOracleStore } from '@/stores/oracle.store'

export default function WarRoom() {
  const [positions, setPositions] = useState<Position[]>([])
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([])
  const [signals, setSignals] = useState<SignalEvent[]>([])
  const [lessons, setLessons] = useState<LearningLogEntry[]>([])
  const { layerStatus } = useOracleStore()

  useEffect(() => {
    async function load() {
      const [pos, snaps, sigs, les] = await Promise.all([
        supabase.from('positions').select('*').eq('user_id', DEMO_USER_ID).order('market_value', { ascending: false }),
        supabase.from('portfolio_snapshots').select('*').eq('user_id', DEMO_USER_ID).order('snapshot_at', { ascending: true }),
        supabase.from('signal_events').select('*').order('detected_at', { ascending: false }).limit(12),
        supabase.from('learning_log').select('*').eq('user_id', DEMO_USER_ID).order('learned_at', { ascending: false }).limit(3),
      ])
      setPositions((pos.data as Position[]) || [])
      setSnapshots((snaps.data as PortfolioSnapshot[]) || [])
      setSignals((sigs.data as SignalEvent[]) || [])
      setLessons((les.data as LearningLogEntry[]) || [])
    }
    load()
  }, [])

  const totalValue = positions.reduce((s, p) => s + (p.market_value || 0), 0) + 50000
  const totalPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || 0), 0)
  const totalPnlPct = positions.length > 0 ? totalPnl / positions.reduce((s, p) => s + p.avg_entry_price * p.quantity, 0) : 0

  const chartData = snapshots.slice(-30).map((s) => ({
    date: new Date(s.snapshot_at).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
    value: s.total_value,
    spy: s.benchmark_value,
  }))

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">War Room</h1>
        <p className="text-sm text-oracle-muted">
          Real-time command center — portfolio, signals, and 10-layer intelligence
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard
          icon={DollarSign}
          label="Portfolio Value"
          value={`$${totalValue.toLocaleString('en', { maximumFractionDigits: 0 })}`}
          sublabel="Paper Trading"
          color="text-oracle-accent"
        />
        <KpiCard
          icon={totalPnl >= 0 ? TrendingUp : TrendingDown}
          label="Unrealized P&L"
          value={`${totalPnl >= 0 ? '+' : ''}$${totalPnl.toLocaleString('en', { maximumFractionDigits: 0 })}`}
          sublabel={`${(totalPnlPct * 100).toFixed(2)}% return`}
          color={totalPnl >= 0 ? 'text-oracle-success' : 'text-oracle-danger'}
        />
        <KpiCard
          icon={Activity}
          label="Active Signals"
          value={String(signals.length)}
          sublabel="L1-L5 live"
          color="text-oracle-primary2"
        />
        <KpiCard
          icon={Brain}
          label="Lessons Learned"
          value="47"
          sublabel="74% accuracy"
          color="text-purple-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Equity Curve */}
        <div className="lg:col-span-2 oracle-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold">Equity Curve vs SPY</h2>
            <span className="text-xs text-oracle-muted">Last 30 days</span>
          </div>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={chartData}>
                <defs>
                  <linearGradient id="portfolioGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366F1" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} domain={['dataMin - 5000', 'dataMax + 5000']} />
                <Tooltip
                  contentStyle={{ background: '#111726', border: '1px solid #242D44', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#64748B' }}
                />
                <Area type="monotone" dataKey="value" stroke="#6366F1" strokeWidth={2} fill="url(#portfolioGrad)" />
                <Line type="monotone" dataKey="spy" stroke="#22D3EE" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-oracle-muted text-sm">Loading...</div>
          )}
        </div>

        {/* Layer Status */}
        <div className="oracle-card">
          <h2 className="text-sm font-semibold mb-4">10-Layer Intelligence Stack</h2>
          <div className="space-y-2">
            {LAYERS.map((l) => {
              const status = layerStatus[l.id]
              return (
                <div key={l.id} className="flex items-center gap-3">
                  <span className="text-base">{l.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="oracle-layer-pill text-[10px]">{l.id}</span>
                      <span className="text-xs font-medium truncate">{l.name}</span>
                    </div>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${
                    status === 'active' ? 'bg-oracle-success' :
                    status === 'processing' ? 'bg-oracle-primary animate-pulse' :
                    status === 'error' ? 'bg-oracle-danger' : 'bg-oracle-muted/40'
                  }`} />
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Positions */}
        <div className="lg:col-span-2 oracle-card">
          <h2 className="text-sm font-semibold mb-4">Active Positions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-oracle-muted border-b border-oracle-border">
                  <th className="pb-2 font-medium">Symbol</th>
                  <th className="pb-2 font-medium text-right">Qty</th>
                  <th className="pb-2 font-medium text-right">Price</th>
                  <th className="pb-2 font-medium text-right">Value</th>
                  <th className="pb-2 font-medium text-right">P&L</th>
                  <th className="pb-2 font-medium text-center">Signal</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((p) => (
                  <tr key={p.id} className="border-b border-oracle-border/50 hover:bg-oracle-surface2/50">
                    <td className="py-2.5 font-mono font-semibold">{p.symbol}</td>
                    <td className="py-2.5 text-right text-oracle-muted">{p.quantity}</td>
                    <td className="py-2.5 text-right">${(p.current_price || 0).toFixed(2)}</td>
                    <td className="py-2.5 text-right">${(p.market_value || 0).toLocaleString('en', { maximumFractionDigits: 0 })}</td>
                    <td className={`py-2.5 text-right font-mono ${(p.unrealized_pnl || 0) >= 0 ? 'text-oracle-success' : 'text-oracle-danger'}`}>
                      {(p.unrealized_pnl || 0) >= 0 ? '+' : ''}{((p.unrealized_pnl || 0)).toLocaleString('en', { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-2.5 text-center">
                      {p.oracle_signal && (
                        <span className={`oracle-pill text-[10px] ${
                          p.oracle_signal === 'BUY' ? 'bg-oracle-success/15 text-oracle-success' :
                          p.oracle_signal === 'SELL' || p.oracle_signal === 'REDUCE' ? 'bg-oracle-danger/15 text-oracle-danger' :
                          p.oracle_signal === 'WATCH' ? 'bg-oracle-warning/15 text-oracle-warning' :
                          'bg-oracle-muted/15 text-oracle-muted'
                        }`}>
                          {p.oracle_signal}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Latest lessons */}
        <div className="oracle-card">
          <h2 className="text-sm font-semibold mb-4">Latest Learning</h2>
          <div className="space-y-3">
            {lessons.length > 0 ? lessons.map((l) => (
              <div key={l.id} className="border-l-2 border-purple-500/30 pl-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-purple-400">#{l.lesson_number}</span>
                  <span className="text-xs text-oracle-muted">Confidence: {l.confidence}/5</span>
                </div>
                <p className="text-xs text-oracle-text leading-relaxed">{l.lesson_text}</p>
              </div>
            )) : (
              <p className="text-xs text-oracle-muted">Loading lessons...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function KpiCard({ icon: Icon, label, value, sublabel, color }: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  sublabel: string
  color: string
}) {
  return (
    <div className="oracle-card-hover">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-oracle-muted font-medium">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-oracle-muted mt-1">{sublabel}</p>
    </div>
  )
}
