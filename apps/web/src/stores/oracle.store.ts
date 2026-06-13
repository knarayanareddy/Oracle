// ════════════════════════════════════════════════════════════════
// ORACLE — Zustand Store (§15)
// Central state: autopilot, active simulation, layer status,
// voice, transparency feed, demo mode.
// ════════════════════════════════════════════════════════════════
import { create } from 'zustand'
import type { AutopilotSession, Simulation, FeedEvent, VoiceState, Layer } from '@/types'

export type LayerStatus = 'active' | 'idle' | 'processing' | 'error'

interface OracleStore {
  // Autopilot
  autopilotActive: boolean
  autopilotSession: AutopilotSession | null
  setAutopilot: (active: boolean) => void

  // Active simulation
  activeSimulation: Simulation | null
  setActiveSimulation: (sim: Simulation | null) => void

  // Layer status
  layerStatus: Record<Layer, LayerStatus>
  updateLayerStatus: (layer: Layer, status: LayerStatus) => void

  // Voice
  voiceState: VoiceState
  setVoiceState: (state: VoiceState) => void
  voiceTranscript: string
  setVoiceTranscript: (t: string) => void

  // Transparency feed
  feedEvents: FeedEvent[]
  addFeedEvent: (event: FeedEvent) => void
  setFeedEvents: (events: FeedEvent[]) => void
  clearFeed: () => void

  // Demo
  isDemoMode: boolean
  demoFeedInterval: ReturnType<typeof setInterval> | null
  startDemoFeed: () => void
  stopDemoFeed: () => void
}

const initialLayerStatus = (): Record<Layer, LayerStatus> => ({
  L1: 'active', L2: 'active', L3: 'active', L4: 'active', L5: 'active',
  L6: 'idle', L7: 'idle', L8: 'idle', L9: 'active', L10: 'idle',
})

export const useOracleStore = create<OracleStore>((set, get) => ({
  autopilotActive: false,
  autopilotSession: null,
  setAutopilot: (active) => set({ autopilotActive: active }),

  activeSimulation: null,
  setActiveSimulation: (sim) => set({ activeSimulation: sim }),

  layerStatus: initialLayerStatus(),
  updateLayerStatus: (layer, status) =>
    set((state) => ({ layerStatus: { ...state.layerStatus, [layer]: status } })),

  voiceState: 'idle',
  setVoiceState: (voiceState) => set({ voiceState }),
  voiceTranscript: '',
  setVoiceTranscript: (voiceTranscript) => set({ voiceTranscript }),

  feedEvents: [],
  addFeedEvent: (event) =>
    set((state) => ({ feedEvents: [event, ...state.feedEvents].slice(0, 100) })),
  setFeedEvents: (feedEvents) => set({ feedEvents }),
  clearFeed: () => set({ feedEvents: [] }),

  isDemoMode: true,
  demoFeedInterval: null,
  startDemoFeed: () => {
    const existing = get().demoFeedInterval
    if (existing) clearInterval(existing)
    const sequence = DEMO_FEED_SEQUENCE
    let idx = 0
    const interval = setInterval(() => {
      const event = sequence[idx % sequence.length]
      get().addFeedEvent({
        id: crypto.randomUUID(),
        event_type: event.type,
        layer: event.layer as Layer | null,
        icon: event.icon,
        title: event.title,
        detail: event.detail,
        created_at: new Date().toISOString(),
      })
      idx++
      // Pulse layer status
      if (event.layer) {
        get().updateLayerStatus(event.layer as Layer, 'processing')
        setTimeout(() => get().updateLayerStatus(event.layer as Layer, 'active'), 1500)
      }
    }, 3500)
    set({ demoFeedInterval: interval })
  },
  stopDemoFeed: () => {
    const interval = get().demoFeedInterval
    if (interval) clearInterval(interval)
    set({ demoFeedInterval: null })
  },
}))

// ════════════════════════════════════════════════════════════════
// Demo Feed Sequence (§23) — auto-fires every 3-7s in demo mode
// The most visually impressive part of the demo.
// ════════════════════════════════════════════════════════════════
const DEMO_FEED_SEQUENCE = [
  { type: 'data' as const, layer: 'L1', icon: '📡', title: 'Market data synced', detail: '847 assets updated' },
  { type: 'data' as const, layer: 'L2', icon: '🏛️', title: 'Macro data refreshed', detail: 'FRED: CPI 2.9%, Unemployment 4.1%' },
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
