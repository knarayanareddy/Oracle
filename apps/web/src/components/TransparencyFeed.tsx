// ════════════════════════════════════════════════════════════════
// TransparencyFeed — Live scrolling log (§04 Module 7)
// Right-panel real-time feed powered by Supabase Realtime + demo.
// ════════════════════════════════════════════════════════════════
import { useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useOracleStore } from '@/stores/oracle.store'
import { supabase, IS_DEMO_MODE } from '@/lib/supabase'
import type { FeedEvent } from '@/types'

const EVENT_STYLES: Record<string, string> = {
  data: 'border-oracle-accent/30',
  simulation: 'border-oracle-primary/30',
  action: 'border-oracle-success/30',
  risk_alert: 'border-oracle-warning/30',
  learning: 'border-purple-500/30',
  debate: 'border-blue-500/30',
  system: 'border-oracle-muted/30',
}

export default function TransparencyFeed() {
  const { feedEvents, addFeedEvent } = useOracleStore()

  // ── Supabase Realtime subscription (§15) ──
  useEffect(() => {
    if (IS_DEMO_MODE) return // demo mode uses local feed sequence

    const channel = supabase
      .channel('transparency-feed')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'oracle_feed',
          table: 'transparency_feed_events',
        },
        (payload) => {
          addFeedEvent(payload.new as FeedEvent)
        },
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [addFeedEvent])

  return (
    <aside className="w-80 border-l border-oracle-border bg-oracle-surface/50 flex flex-col">
      <div className="px-4 py-3 border-b border-oracle-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-oracle-success animate-pulse" />
          <h3 className="text-sm font-semibold">Transparency Feed</h3>
        </div>
        <span className="text-xs text-oracle-muted font-mono">{feedEvents.length}</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        <AnimatePresence initial={false}>
          {feedEvents.map((event) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: 20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: 'auto' }}
              exit={{ opacity: 0 }}
              className={`border-l-2 ${EVENT_STYLES[event.event_type] || EVENT_STYLES.system} pl-3 py-2`}
            >
              <div className="flex items-start gap-2">
                <span className="text-base leading-none">{event.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {event.layer && (
                      <span className="oracle-layer-pill text-[10px]">{event.layer}</span>
                    )}
                    <p className="text-xs font-medium text-oracle-text truncate">{event.title}</p>
                  </div>
                  {event.detail && (
                    <p className="text-xs text-oracle-muted mt-0.5 leading-relaxed">{event.detail}</p>
                  )}
                  <p className="text-[10px] text-oracle-muted/60 mt-1 font-mono">
                    {new Date(event.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {feedEvents.length === 0 && (
          <div className="text-center text-oracle-muted text-xs mt-8">
            Waiting for ORACLE activity...
          </div>
        )}
      </div>
    </aside>
  )
}
