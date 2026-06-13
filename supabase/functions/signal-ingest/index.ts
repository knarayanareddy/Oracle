// ════════════════════════════════════════════════════════════════
// Edge Function: signal-ingest  (§10)
// Receives signal data from FastAPI pipeline, writes to oracle_signals.
// Auth: Service role only (called from FastAPI).
// ════════════════════════════════════════════════════════════════
import { getServiceClient, jsonResponse, corsHeaders } from '../_shared/oracle.ts'

const VALID_LAYERS = ['L1','L2','L3','L4','L5','L6','L7','L8','L9','L10']
const VALID_DIRECTIONS = ['bullish','bearish','neutral','contrarian']

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (req.method !== 'POST') return jsonResponse({ error: 'Method not allowed' }, 405)

  const supabase = getServiceClient()

  try {
    const body = await req.json()
    // Support single object or array of signals
    const signals = Array.isArray(body) ? body : [body]

    const rows = signals.map((s: Record<string, unknown>) => {
      if (!VALID_LAYERS.includes(s.layer as string)) {
        throw new Error(`Invalid layer: ${s.layer}`)
      }
      if (s.direction && !VALID_DIRECTIONS.includes(s.direction as string)) {
        throw new Error(`Invalid direction: ${s.direction}`)
      }
      const strength = s.strength as number | undefined
      if (strength !== undefined && (strength < 1 || strength > 5)) {
        throw new Error(`Invalid strength: ${strength}`)
      }
      return {
        layer: s.layer,
        signal_type: s.signal_type,
        asset: s.asset ?? null,
        direction: s.direction ?? null,
        strength: strength ?? null,
        confidence: s.confidence ?? null,
        raw_value: s.raw_value ?? null,
        context: s.context ?? null,
        source_url: s.source_url ?? null,
        metadata: s.metadata ?? {},
        expires_at: s.expires_at ?? null,
      }
    })

    const { data, error } = await supabase
      .from('signal_events')
      .insert(rows)
      .select('id')

    if (error) return jsonResponse({ error: error.message }, 500)

    return jsonResponse({ created: data?.length ?? 0, signal_ids: data?.map((r) => r.id) })
  } catch (err) {
    console.error('signal-ingest error:', err)
    return jsonResponse({ error: String(err) }, 400)
  }
})
