// ════════════════════════════════════════════════════════════════
// ORACLE Edge Function — shared helpers
// Service-role key ONLY. Never expose to frontend.
// ════════════════════════════════════════════════════════════════
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.0'

export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers':
    'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  })
}

/**
 * Creates a Supabase client using the service-role key.
 * Service role bypasses RLS — use ONLY inside Edge Functions.
 */
export function getServiceClient() {
  const url = Deno.env.get('SUPABASE_URL')
  const key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  if (!url || !key) {
    throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  }
  return createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  })
}

/** Extract the user id from a JWT (anon path) or fall back to demo user. */
export function resolveUserId(req: Request): string {
  const demo = Deno.env.get('DEMO_USER_ID') ?? '00000000-0000-0000-0000-000000000001'
  const auth = req.headers.get('Authorization')
  if (!auth) return demo
  try {
    const token = auth.replace('Bearer ', '')
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub ?? demo
  } catch {
    return demo
  }
}

export interface FeedEventInput {
  userId: string
  eventType: 'data' | 'simulation' | 'action' | 'risk_alert' | 'learning' | 'debate' | 'system'
  layer?: string
  icon: string
  title: string
  detail?: string
  metadata?: Record<string, unknown>
}

/** Emits a transparency feed event (broadcast over Realtime). */
export async function emitFeedEvent(supabase: ReturnType<typeof getServiceClient>, e: FeedEventInput) {
  const { error } = await supabase.from('transparency_feed_events').insert({
    user_id: e.userId,
    event_type: e.eventType,
    layer: e.layer ?? null,
    icon: e.icon,
    title: e.title,
    detail: e.detail ?? null,
    metadata: e.metadata ?? {},
  })
  if (error) console.error('emitFeedEvent error:', error.message)
}
