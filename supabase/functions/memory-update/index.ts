// ════════════════════════════════════════════════════════════════
// Edge Function: memory-update  (§10)
// After every simulation or trade, extract lessons and update
// investor profile personalizations.
// Auth: Service role only.
// ════════════════════════════════════════════════════════════════
import { getServiceClient, resolveUserId, jsonResponse, corsHeaders } from '../_shared/oracle.ts'

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (req.method !== 'POST') return jsonResponse({ error: 'Method not allowed' }, 405)

  const supabase = getServiceClient()

  try {
    const { user_id, event_type, event_id, outcome_data } = await req.json()
    const userId = user_id ?? resolveUserId(req)
    let lessonsCreated = 0

    // ── Extract a lesson based on event outcome ──
    if (outcome_data?.lesson_text) {
      const { error } = await supabase.from('learning_log').insert({
        user_id: userId,
        lesson_text: outcome_data.lesson_text,
        confidence: outcome_data.confidence ?? 3,
        tags: outcome_data.tags ?? [],
        source_type: event_type ?? 'simulation_outcome',
        source_id: event_id ?? null,
        signal_combo: outcome_data.signal_combo ?? null,
        validated: outcome_data.validated ?? false,
      })
      if (error) throw new Error(error.message)
      lessonsCreated++
    }

    // ── Update simulation accuracy if outcome is known ──
    let profileUpdated = false
    if (event_type === 'simulation_outcome' && outcome_data?.simulation_id) {
      const { error } = await supabase.from('simulation_accuracy').upsert({
        user_id: userId,
        simulation_id: outcome_data.simulation_id,
        signal_combo: outcome_data.signal_combo,
        predicted_direction: outcome_data.predicted_direction,
        actual_direction: outcome_data.actual_direction,
        is_correct: outcome_data.is_correct,
        confidence_at_prediction: outcome_data.confidence_at_prediction,
      }, { onConflict: 'simulation_id' })
      if (error) throw new Error(error.message)
      profileUpdated = true
    }

    // ── Update investor profile if personalization provided ──
    if (outcome_data?.personalization) {
      const { data: profile } = await supabase
        .from('investor_profiles')
        .select('active_personalizations')
        .eq('user_id', userId)
        .single()

      const existing = profile?.active_personalizations ?? []
      existing.push(outcome_data.personalization)
      await supabase
        .from('investor_profiles')
        .update({ active_personalizations: existing, last_updated: new Date().toISOString() })
        .eq('user_id', userId)
      profileUpdated = true
    }

    return jsonResponse({ lessons_created: lessonsCreated, profile_updated: profileUpdated })
  } catch (err) {
    console.error('memory-update error:', err)
    return jsonResponse({ error: String(err) }, 500)
  }
})
