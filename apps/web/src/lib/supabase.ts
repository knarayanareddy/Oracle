// ════════════════════════════════════════════════════════════════
// ORACLE — Supabase Client (§16)
// Frontend uses anon key + JWT ONLY. Never the service role key.
// Demo mode: uses a fixed DEMO_USER_ID for all queries.
// ════════════════════════════════════════════════════════════════
import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:54321'
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'

export const DEMO_USER_ID =
  import.meta.env.VITE_DEMO_USER_ID || '00000000-0000-0000-0000-000000000001'
export const IS_DEMO_MODE = (import.meta.env.VITE_DEMO_MODE ?? 'true') === 'true'

export const supabase: SupabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false, // demo mode = no auth
    autoRefreshToken: false,
  },
  realtime: {
    params: { eventsPerSecond: 10 },
  },
})

/** The active user ID — demo user in demo mode, or auth.uid() otherwise. */
export const getUserId = (): string => (IS_DEMO_MODE ? DEMO_USER_ID : '')
