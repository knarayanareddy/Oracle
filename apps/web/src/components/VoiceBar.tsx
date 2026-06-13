// ════════════════════════════════════════════════════════════════
// VoiceBar — Hold-to-speak voice command interface (§14)
// Text fallback + waveform feedback + suggested command pills.
// ════════════════════════════════════════════════════════════════
import { useState, useRef, useCallback } from 'react'
import { Mic, Send, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { useOracleStore } from '@/stores/oracle.store'
import { processVoice } from '@/lib/api'

const SUGGESTIONS = [
  'Run a swarm simulation on today\'s CPI report',
  'What\'s my risk exposure on tech?',
  'Build a strategy: Buy NVDA when RSI < 30 and swarm bullish > 60%',
  'Rebalance my portfolio',
]

export default function VoiceBar() {
  const { voiceState, setVoiceState, voiceTranscript, setVoiceTranscript, addFeedEvent } =
    useOracleStore()
  const [text, setText] = useState('')
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startListening = useCallback(async () => {
    setVoiceState('listening')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      mediaRef.current = recorder
      recorder.start()
    } catch {
      // Fallback: no mic access, use text
      setVoiceState('idle')
    }
  }, [setVoiceState])

  const stopListening = useCallback(async () => {
    const recorder = mediaRef.current
    if (recorder && recorder.state === 'recording') {
      setVoiceState('processing')
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const stream = recorder.stream
        stream.getTracks().forEach((t) => t.stop())

        try {
          // Try Whisper transcription
          const formData = new FormData()
          formData.append('file', blob, 'voice.webm')
          const resp = await fetch(
            `${import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000'}/api/v1/voice/transcribe`,
            { method: 'POST', body: formData },
          )
          const data = await resp.json()
          const transcript = data.transcript
          setVoiceTranscript(transcript)
          setText(transcript)
          await processCommand(transcript)
        } catch {
          setVoiceState('idle')
        }
      }
      recorder.stop()
    } else {
      setVoiceState('idle')
    }
  }, [setVoiceState, setVoiceTranscript])

  const processCommand = async (transcript: string) => {
    setVoiceState('responding')
    try {
          const result = await processVoice(transcript) as { response_text?: string }
          setVoiceTranscript(transcript)
          // Emit feed events for activated layers
      addFeedEvent({
        id: crypto.randomUUID(),
        event_type: 'system',
        layer: null,
        icon: '🎙️',
        title: 'Voice command processed',
        detail: transcript.slice(0, 60),
        created_at: new Date().toISOString(),
      })
      // Simulate TTS via Web Speech API
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(result.response_text)
        utterance.rate = 1.05
        speechSynthesis.speak(utterance)
      }
    } catch {
      // graceful degradation
    }
    setVoiceState('idle')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    await processCommand(text)
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-oracle-surface/90 backdrop-blur-xl border-t border-oracle-border z-30">
      {/* Waveform visual (when listening) */}
      {voiceState === 'listening' && (
        <div className="flex items-center justify-center gap-1 h-8">
          {Array.from({ length: 24 }).map((_, i) => (
            <motion.div
              key={i}
              className="w-1 bg-oracle-primary rounded-full"
              animate={{ height: [4, 20, 4] }}
              transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.04 }}
            />
          ))}
        </div>
      )}

      <div className="px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          {/* Mic button */}
          <button
            onMouseDown={startListening}
            onMouseUp={stopListening}
            onTouchStart={startListening}
            onTouchEnd={stopListening}
            className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              voiceState === 'listening'
                ? 'bg-oracle-danger glow-danger scale-110'
                : voiceState === 'processing' || voiceState === 'responding'
                ? 'bg-oracle-primary glow-primary'
                : 'bg-oracle-surface2 hover:bg-oracle-primary/20'
            }`}
            title="Hold to speak"
          >
            {voiceState === 'processing' || voiceState === 'responding' ? (
              <Loader2 className="w-5 h-5 text-white animate-spin" />
            ) : (
              <Mic className={`w-5 h-5 ${voiceState === 'listening' ? 'text-white' : 'text-oracle-text'}`} />
            )}
          </button>

          {/* Text input (fallback) */}
          <form onSubmit={handleSubmit} className="flex-1 flex gap-2">
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={
                voiceState === 'listening' ? 'Listening...' :
                voiceState === 'processing' ? 'Processing...' :
                voiceState === 'responding' ? voiceTranscript :
                'Speak or type a command to ORACLE...'
              }
              disabled={voiceState === 'listening' || voiceState === 'processing'}
              className="oracle-input"
            />
            <button type="submit" className="oracle-btn-primary flex items-center gap-2">
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Suggested commands */}
        <div className="max-w-4xl mx-auto flex flex-wrap gap-2 mt-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setText(s)}
              className="text-xs px-3 py-1 rounded-full bg-oracle-surface2 text-oracle-muted hover:text-oracle-text hover:bg-oracle-border transition-colors"
            >
              {s.length > 45 ? s.slice(0, 45) + '...' : s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
