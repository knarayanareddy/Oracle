// ════════════════════════════════════════════════════════════════
// ORACLE — FastAPI Client
// Typed wrappers for all backend endpoints.
// ════════════════════════════════════════════════════════════════
import { supabase } from './supabase'

const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000'

/** Invoke a Supabase Edge Function. */
export async function invokeFunction<T>(
  name: string,
  body: Record<string, unknown>,
): Promise<T> {
  const { data, error } = await supabase.functions.invoke(name, { body })
  if (error) throw error
  return data as T
}

/** Call FastAPI directly (used for backtest, strategy parse, etc.) */
export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${FASTAPI_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `API error ${resp.status}`)
  }
  return resp.json()
}

// ── Swarm ──
export const triggerSwarm = (params: {
  seed_text: string
  seed_type?: string
  agent_count?: number
  round_count?: number
  title?: string
}) => invokeFunction<{ simulation_id: string; status: string }>('swarm-trigger', params)

// ── Strategy ──
export const parseStrategy = (description: string) =>
  apiPost('/api/v1/strategy/parse', { description })

export const backtestStrategy = (params: {
  conditions: Record<string, unknown>
  symbol?: string
  layers_used?: string[]
}) => apiPost('/api/v1/strategy/backtest', params)

// ── Voice ──
export const processVoice = (transcript: string) =>
  apiPost('/api/v1/voice/process', { transcript })

// ── Signals ──
export const fetchLatestSignals = () =>
  apiPost<{ signals: unknown[] }>('/api/v1/signals/latest', {}).catch(() => ({ signals: [] }))

// ── Recommendations ──
export const generateRecommendation = (userId: string, query = '') =>
  apiPost('/api/v1/recommendations/generate', { user_id: userId, query })

// ── Trade ──
export const executeTrade = (params: {
  user_id: string
  symbol: string
  action: string
  quantity: number
  price: number
}) => invokeFunction<{ trade_id: string; executed: boolean }>('trade-execute', params)
