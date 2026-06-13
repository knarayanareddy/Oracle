// ════════════════════════════════════════════════════════════════
// MemoryPage — GraphRAG Persistent Intelligence (§04 Module 5)
// Investor DNA radar, accuracy tracker, learning log, graph viz.
// ════════════════════════════════════════════════════════════════
import { useState, useEffect } from 'react'
import { Brain, Target, BookOpen, Radar as RadarIcon } from 'lucide-react'
import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from 'recharts'
import { supabase, DEMO_USER_ID } from '@/lib/supabase'
import type { InvestorProfile, LearningLogEntry } from '@/types'

export default function MemoryPage() {
  const [profile, setProfile] = useState<InvestorProfile | null>(null)
  const [lessons, setLessons] = useState<LearningLogEntry[]>([])
  const [accuracy, setAccuracy] = useState<any>(null)

  useEffect(() => {
    async function load() {
      const [prof, les, acc] = await Promise.all([
        supabase.from('investor_profiles').select('*').eq('user_id', DEMO_USER_ID).maybeSingle(),
        supabase.from('learning_log').select('*').eq('user_id', DEMO_USER_ID).order('learned_at', { ascending: false }).limit(15),
        supabase.from('simulation_accuracy').select('*').eq('user_id', DEMO_USER_ID),
      ])
      setProfile(prof.data as InvestorProfile)
      setLessons((les.data as LearningLogEntry[]) || [])
      // Compute accuracy stats
      const accData = (acc.data as any[]) || []
      if (accData.length > 0) {
        const correct = accData.filter((a) => a.is_correct).length
        const byCombo: Record<string, { total: number; correct: number }> = {}
        for (const a of accData) {
          const combo = a.signal_combo || 'unknown'
          byCombo[combo] = byCombo[combo] || { total: 0, correct: 0 }
          byCombo[combo].total++
          if (a.is_correct) byCombo[combo].correct++
        }
        setAccuracy({
          total: accData.length,
          rate: correct / accData.length,
          byCombo: Object.fromEntries(
            Object.entries(byCombo).map(([k, v]) => [k, { rate: v.correct / v.total, count: v.total }]),
          ),
        })
      }
    }
    load()
  }, [])

  const radarData = profile?.radar_scores
    ? [
        { metric: 'Risk Appetite', value: (profile.radar_scores.risk_appetite || 0) * 100 },
        { metric: 'Patience', value: (profile.radar_scores.patience || 0) * 100 },
        { metric: 'Conviction', value: (profile.radar_scores.conviction || 0) * 100 },
        { metric: 'Diversification', value: (profile.radar_scores.diversification || 0) * 100 },
        { metric: 'Momentum Bias', value: (profile.radar_scores.momentum_bias || 0) * 100 },
        { metric: 'Macro Awareness', value: (profile.radar_scores.macro_awareness || 0) * 100 },
      ]
    : []

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-400" />
          Memory & Learning
        </h1>
        <p className="text-sm text-oracle-muted">
          Investor DNA, simulation accuracy, and persistent learning across sessions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Investor DNA Radar */}
        <div className="oracle-card lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <RadarIcon className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold">Investor DNA Profile</h2>
          </div>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#242D44" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#94A3B8', fontSize: 11 }} />
                <Radar dataKey="value" stroke="#A855F7" fill="#A855F7" fillOpacity={0.25} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[280px] flex items-center justify-center text-oracle-muted">Loading...</div>
          )}
        </div>

        {/* Risk Profile Summary */}
        <div className="oracle-card">
          <h2 className="text-sm font-semibold mb-4">Behavioral Insights</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center pb-2 border-b border-oracle-border">
              <span className="text-oracle-muted">Stated Risk</span>
              <span className="font-medium capitalize">{profile?.stated_risk || '—'}</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-oracle-border">
              <span className="text-oracle-muted">Revealed Risk</span>
              <span className={`font-medium capitalize ${profile?.risk_discrepancy ? 'text-oracle-warning' : ''}`}>
                {profile?.revealed_risk || '—'}
              </span>
            </div>
            {profile?.risk_discrepancy && (
              <div className="bg-oracle-warning/10 rounded-lg p-2 text-xs text-oracle-warning">
                ⚠️ Discrepancy detected: you say {profile.stated_risk} but act {profile.revealed_risk}
              </div>
            )}
            <div className="flex justify-between items-center pb-2 border-b border-oracle-border">
              <span className="text-oracle-muted">Avg Hold Days</span>
              <span className="font-mono">{profile?.avg_hold_days?.toFixed(1) || '—'}</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-oracle-border">
              <span className="text-oracle-muted">Best Signal Combo</span>
              <span className="oracle-layer-pill text-[10px]">{profile?.best_signal_combo || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-oracle-muted">Worst Signal Combo</span>
              <span className="oracle-layer-pill text-[10px] bg-oracle-danger/15 text-oracle-danger border-oracle-danger/30">{profile?.worst_signal_combo || '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Accuracy Stats */}
      {accuracy && (
        <div className="oracle-card">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-4 h-4 text-oracle-accent" />
            <h2 className="text-sm font-semibold">Simulation Accuracy Tracker</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-oracle-bg rounded-lg p-3">
              <p className="text-xs text-oracle-muted">Total Simulations</p>
              <p className="text-2xl font-bold">{accuracy.total}</p>
            </div>
            <div className="bg-oracle-bg rounded-lg p-3">
              <p className="text-xs text-oracle-muted">Overall Accuracy</p>
              <p className={`text-2xl font-bold ${(accuracy.rate * 100) >= 70 ? 'text-oracle-success' : 'text-oracle-warning'}`}>
                {(accuracy.rate * 100).toFixed(0)}%
              </p>
            </div>
            {Object.entries(accuracy.byCombo).map(([combo, stats]: [string, any]) => (
              <div key={combo} className="bg-oracle-bg rounded-lg p-3">
                <p className="text-xs text-oracle-muted">{combo} Accuracy</p>
                <p className={`text-2xl font-bold ${(stats.rate * 100) >= 70 ? 'text-oracle-success' : 'text-oracle-warning'}`}>
                  {(stats.rate * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-oracle-muted mt-1">{stats.count} sims</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learning Log */}
      <div className="oracle-card">
        <div className="flex items-center gap-2 mb-4">
          <BookOpen className="w-4 h-4 text-oracle-primary2" />
          <h2 className="text-sm font-semibold">Learning Log</h2>
        </div>
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {lessons.map((l) => (
            <div key={l.id} className="border-l-2 border-oracle-primary/30 pl-3 py-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-oracle-primary2">#{l.lesson_number}</span>
                <div className="flex gap-1">
                  {l.tags?.map((tag) => (
                    <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-oracle-surface2 text-oracle-muted">{tag}</span>
                  ))}
                </div>
                <span className="text-[10px] text-oracle-muted ml-auto">{l.confidence}/5 confidence</span>
              </div>
              <p className="text-xs text-oracle-text leading-relaxed">{l.lesson_text}</p>
              {l.signal_combo && (
                <span className="oracle-layer-pill text-[10px] mt-1 inline-block">{l.signal_combo}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
