// ════════════════════════════════════════════════════════════════
// Edge Function: autopilot-loop  (§10)
// Called by pg_cron every N minutes. Reads active sessions, scans
// L1-L5 signals, triggers swarms on threshold, runs debate via
// FastAPI, executes paper trades, writes decisions + feed.
// Auth: Service role only (cron).
// ════════════════════════════════════════════════════════════════
import { getServiceClient, jsonResponse, emitFeedEvent, corsHeaders } from '../_shared/oracle.ts'

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (req.method !== 'POST') return jsonResponse({ error: 'Method not allowed' }, 405)

  const supabase = getServiceClient()
  const fastapiUrl = Deno.env.get('FASTAPI_URL_LOCAL') ?? Deno.env.get('FASTAPI_URL')
  const fastapiSecret = Deno.env.get('FASTAPI_SECRET_KEY') ?? ''
  let decisionsMade = 0
  let tradesExecuted = 0

  try {
    // ── Fetch active autopilot sessions ──
    const { data: sessions, error } = await supabase
      .from('autopilot_sessions')
      .select('*')
      .eq('status', 'active')
    if (error) throw new Error(error.message)

    for (const session of sessions ?? []) {
      const { user_id } = session

      // ── Daily trade limit check ──
      const today = new Date().toISOString().slice(0, 10)
      const { count } = await supabase
        .from('autopilot_trades')
        .select('id', { count: 'exact', head: true })
        .eq('session_id', session.id)
        .gte('executed_at', today)
      if ((count ?? 0) >= (session.max_daily_trades ?? 5)) continue

      // ── Read latest material signals (strength >= 4) ──
      const { data: signals } = await supabase
        .from('signal_events')
        .select('*')
        .in('layer', ['L1', 'L2', 'L3', 'L4', 'L5'])
        .gte('strength', 4)
        .order('detected_at', { ascending: false })
        .limit(5)

      if (!signals || signals.length === 0) continue

      const trigger = signals[0]
      await emitFeedEvent(supabase, {
        userId: user_id, eventType: 'data', layer: trigger.layer,
        icon: '⚡', title: 'Autopilot signal detected',
        detail: `${trigger.signal_type} on ${trigger.asset ?? 'market'} — ${trigger.direction}`,
      })

      // ── Call FastAPI debate for consensus ──
      const { data: decision } = await callDebate(fastapiUrl!, fastapiSecret, {
        user_id,
        session_id: session.id,
        trigger_signal: trigger.signal_type,
        trigger_layer: trigger.layer,
        trigger_asset: trigger.asset,
      }).catch((e) => {
        console.error('debate error:', e)
        return { data: null }
      })

      if (!decision) continue

      // ── Persist decision ──
      const { data: decRow } = await supabase
        .from('autopilot_decisions')
        .insert({
          session_id: session.id,
          user_id,
          trigger_signal: trigger.signal_type,
          trigger_layer: trigger.layer,
          bull_argument: decision.bull_argument,
          bear_argument: decision.bear_argument,
          risk_assessment: decision.risk_assessment,
          consensus: decision.consensus,
          consensus_confidence: decision.confidence,
          reasoning_trail: decision.reasoning_trail ?? {},
          layers_activated: decision.layers_activated ?? ['L6', 'L7', 'L8'],
        })
        .select()
        .single()

      decisionsMade++

      // ── Execute paper trade if actionable ──
      if (['BUY', 'SELL', 'REDUCE', 'REBALANCE'].includes(decision.consensus)) {
        await supabase.functions.invoke('trade-execute', {
          body: {
            user_id,
            symbol: decision.recommended_action?.asset ?? trigger.asset,
            action: decision.consensus,
            quantity: decision.recommended_action?.quantity ?? 1,
            price: decision.recommended_action?.price ?? 0,
            decision_id: decRow?.id,
            reasoning: decision.reasoning_trail?.explanation ?? '',
            layers_activated: decision.layers_activated,
          },
        })
        tradesExecuted++
      }

      await emitFeedEvent(supabase, {
        userId: user_id, eventType: 'action', layer: 'L10', icon: '✅',
        title: `Autopilot decision: ${decision.consensus}`,
        detail: decision.reasoning_trail?.explanation ?? '',
      })
    }

    return jsonResponse({
      sessions_processed: sessions?.length ?? 0,
      decisions_made: decisionsMade,
      trades_executed: tradesExecuted,
    })
  } catch (err) {
    console.error('autopilot-loop error:', err)
    return jsonResponse({ error: 'Internal error' }, 500)
  }
})

async function callDebate(url: string, secret: string, payload: unknown) {
  const resp = await fetch(`${url}/api/v1/debate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Oracle-Secret': secret },
    body: JSON.stringify(payload),
  })
  if (!resp.ok) throw new Error(`debate ${resp.status}`)
  return { data: await resp.json() }
}
