// ════════════════════════════════════════════════════════════════
// TopBar — Navigation + Autopilot Toggle + Layer Status
// ════════════════════════════════════════════════════════════════
import { NavLink, useLocation } from 'react-router-dom'
import { Activity, Brain, Sparkles, Waves, Zap } from 'lucide-react'
import { useState } from 'react'
import { useOracleStore } from '@/stores/oracle.store'
import { LAYERS } from '@/types'
import { motion, AnimatePresence } from 'framer-motion'

const NAV = [
  { to: '/', label: 'War Room', icon: Activity },
  { to: '/swarm', label: 'Swarm', icon: Waves },
  { to: '/strategy', label: 'Strategy', icon: Sparkles },
  { to: '/memory', label: 'Memory', icon: Brain },
]

export default function TopBar() {
  const { autopilotActive, setAutopilot, layerStatus } = useOracleStore()
  const [showConfirm, setShowConfirm] = useState(false)
  const loc = useLocation()

  return (
    <header className="border-b border-oracle-border bg-oracle-surface/80 backdrop-blur-xl z-30 sticky top-0">
      <div className="flex items-center justify-between px-6 h-16">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="relative w-9 h-9 flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-br from-oracle-primary to-oracle-accent rounded-lg opacity-80" />
            <Zap className="w-5 h-5 text-white relative z-10" fill="white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">
              ORACLE
            </h1>
            <p className="text-[10px] text-oracle-muted font-mono -mt-0.5">
              SWARM INTELLIGENCE BROKER
            </p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive || (to === '/' && loc.pathname === '/')
                    ? 'bg-oracle-primary/15 text-oracle-primary2'
                    : 'text-oracle-muted hover:text-oracle-text hover:bg-oracle-surface2'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Autopilot + Layers */}
        <div className="flex items-center gap-4">
          {/* Layer status dots */}
          <div className="hidden lg:flex items-center gap-1" title="10-Layer Intelligence Stack">
            {LAYERS.map((l) => {
              const status = layerStatus[l.id]
              const color =
                status === 'active' ? 'bg-oracle-success' :
                status === 'processing' ? 'bg-oracle-primary animate-pulse' :
                status === 'error' ? 'bg-oracle-danger' : 'bg-oracle-muted'
              return (
                <div
                  key={l.id}
                  className={`w-2 h-2 rounded-full ${color}`}
                  title={`${l.id} — ${l.name}: ${status}`}
                />
              )
            })}
          </div>

          {/* Autopilot toggle */}
          <button
            onClick={() => (autopilotActive ? setAutopilot(false) : setShowConfirm(true))}
            className={`oracle-btn flex items-center gap-2 ${
              autopilotActive
                ? 'bg-oracle-success/20 text-oracle-success border border-oracle-success/40 glow-success'
                : 'bg-oracle-surface2 text-oracle-text border border-oracle-border'
            }`}
          >
            <div className={`w-2 h-2 rounded-full ${autopilotActive ? 'bg-oracle-success animate-pulse' : 'bg-oracle-muted'}`} />
            Autopilot {autopilotActive ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Autopilot confirmation modal */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center"
            onClick={() => setShowConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9 }}
              className="oracle-card max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-oracle-success/15 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-oracle-success" />
                </div>
                <h3 className="text-lg font-semibold">Activate Autopilot?</h3>
              </div>
              <p className="text-sm text-oracle-muted mb-4">
                ORACLE will autonomously monitor all 10 intelligence layers, trigger swarm simulations on material
                signals, run multi-agent debates, and execute paper trades. Every action is logged to the
                Transparency Feed.
              </p>
              <div className="bg-oracle-bg rounded-lg p-3 mb-4 text-xs text-oracle-muted font-mono">
                ⚠️ PAPER TRADING ONLY — no real money execution (ADR-008)
                <br />• Max 5 trades/day • Position cap: 25%
              </div>
              <div className="flex gap-2">
                <button onClick={() => setShowConfirm(false)} className="oracle-btn-ghost flex-1">
                  Cancel
                </button>
                <button
                  onClick={() => { setAutopilot(true); setShowConfirm(false) }}
                  className="oracle-btn-primary flex-1"
                >
                  Activate
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
