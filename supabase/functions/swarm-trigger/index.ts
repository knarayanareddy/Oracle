// ════════════════════════════════════════════════════════════════
// Edge Function: swarm-trigger
// §10 — Validates sim request, creates record, calls FastAPI, writes rounds.
// ════════════════════════════════════════════════════════════════
import { getServiceClient, resolveUserId, jsonResponse, emitFeedEvent, corsHeaders } from '../_shared/oracle.ts'

interface SwarmRequest {
  seed_text: string
  seed_type?: string
  agent_count?: number
  round_count?: number
  agent_mix?: Record<string, number>
  llm_model?: string
  environments?: string[]
  title?: string
}

const MAX_AGENTS = Number(Deno.env.get('ORACLE_MAX_AGENTS') ?? 1000)
const MAX_ROUNDS = Number(Deno.env.get('ORACLE_MAX_ROUNDS') ?? 40)

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (req.method !== 'POST') return jsonResponse({ error: 'Method not allowed' }, 405)

  try {
    const body: SwarmRequest = await req.json()

    // ── Validate ──
    if (!body.seed_text || body.seed_text.trim().length < 10) {
      return jsonResponse({ error: 'seed_text must be at least 10 characters' }, 400)
    }
    const agentCount = Math.min(body.agent_count ?? 500, MAX_AGENTS)
    const roundCount = Math.min(body.round_count ?? 40, MAX_ROUNDS)
    const userId = resolveUserId(req)
    const supabase = getServiceClient()

    // ── Create simulation record ──
    const { data: sim, error: simErr } = await supabase
      .from('simulations')
      .insert({
        user_id: userId,
        title: body.title ?? body.seed_text.slice(0, 60),
        seed_text: body.seed_text,
        seed_type: body.seed_type ?? 'user_thesis',
        status: 'running',
        agent_count: agentCount,
        round_count: roundCount,
        current_round: 0,
        agent_mix: body.agent_mix ?? { institutional: 35, retail: 50, media: 15 },
        llm_model: body.llm_model ?? 'gpt-4o-mini',
        environments: body.environments ?? ['twitter', 'reddit'],
        started_at: new Date().toISOString(),
      })
      .select()
      .single()
    if (simErr) return jsonResponse({ error: simErr.message }, 500)

    await emitFeedEvent(supabase, {
      userId, eventType: 'simulation', layer: 'L6', icon: '🌊',
      title: 'Swarm simulation launching',
      detail: `${agentCount} agents initializing...`,
      metadata: { simulation_id: sim.id },
    })

    // ── Call FastAPI swarm engine (fire-and-track) ──
    const fastapiUrl = Deno.env.get('FASTAPI_URL_LOCAL') ?? Deno.env.get('FASTAPI_URL')
    const fastapiSecret = Deno.env.get('FASTAPI_SECRET_KEY') ?? ''

    let engineError: string | undefined
    try {
      const resp = await fetch(`${fastapiUrl}/api/v1/swarm/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Oracle-Secret': fastapiSecret,
        },
        body: JSON.stringify({
          simulation_id: sim.id,
          seed_text: body.seed_text,
          seed_type: body.seed_type ?? 'user_thesis',
          agent_count: agentCount,
          round_count: roundCount,
          agent_mix: body.agent_mix ?? { institutional: 35, retail: 50, media: 15 },
          llm_model: body.llm_model ?? 'gpt-4o-mini',
          environments: body.environments ?? ['twitter', 'reddit'],
          supabase_simulation_id: sim.id,
        }),
      })
      if (!resp.ok) {
        engineError = `FastAPI returned ${resp.status}`
      }
    } catch (e) {
      engineError = String(e)
    }

    if (engineError) {
      await supabase.from('simulations').update({ status: 'failed' }).eq('id', sim.id)
      await emitFeedEvent(supabase, {
        userId, eventType: 'system', icon: '⚠️',
        title: 'Simulation failed', detail: engineError,
      })
      return jsonResponse({ simulation_id: sim.id, status: 'failed', error: engineError }, 502)
    }

    return jsonResponse({ simulation_id: sim.id, status: 'running' })
  } catch (err) {
    console.error('swarm-trigger error:', err)
    return jsonResponse({ error: 'Internal error' }, 500)
  }
})
