// ════════════════════════════════════════════════════════════════
// ORACLE — App Root (§15)
// Route structure: /, /swarm, /strategy, /memory
// Persistent: TopBar (autopilot toggle), VoiceBar (fixed bottom)
// ════════════════════════════════════════════════════════════════
import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import TopBar from '@/components/TopBar'
import VoiceBar from '@/components/VoiceBar'
import TransparencyFeed from '@/components/TransparencyFeed'
import WarRoom from '@/pages/WarRoom'
import SwarmPage from '@/pages/SwarmPage'
import StrategyPage from '@/pages/StrategyPage'
import MemoryPage from '@/pages/MemoryPage'
import { useOracleStore } from '@/stores/oracle.store'

export default function App() {
  const startDemoFeed = useOracleStore((s) => s.startDemoFeed)
  const stopDemoFeed = useOracleStore((s) => s.stopDemoFeed)

  useEffect(() => {
    startDemoFeed()
    return () => stopDemoFeed()
  }, [startDemoFeed, stopDemoFeed])

  return (
    <div className="min-h-screen flex flex-col oracle-grid-bg">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-y-auto pb-24">
          <Routes>
            <Route path="/" element={<WarRoom />} />
            <Route path="/swarm" element={<SwarmPage />} />
            <Route path="/swarm/:id" element={<SwarmPage />} />
            <Route path="/strategy" element={<StrategyPage />} />
            <Route path="/memory" element={<MemoryPage />} />
          </Routes>
        </main>
        <TransparencyFeed />
      </div>
      <VoiceBar />
    </div>
  )
}
