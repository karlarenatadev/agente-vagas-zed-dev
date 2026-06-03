import { motion, AnimatePresence } from 'framer-motion'
import type { SessionMode } from '../types'

interface Props {
  mode: SessionMode
  isStreaming: boolean
}

const AGENT_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  scout:   { label: 'Scout',   color: '#a78bfa', bg: 'rgba(124,58,237,0.12)' },
  curator: { label: 'Curator', color: 'var(--cyan)', bg: 'rgba(34,211,238,0.10)' },
  coach:   { label: 'Coach',   color: 'var(--emerald)', bg: 'rgba(52,211,153,0.10)' },
  maestro: { label: 'Maestro', color: '#a78bfa', bg: 'rgba(124,58,237,0.12)' },
}

export function AgentBadge({ mode, isStreaming }: Props) {
  const agentKey = mode === 'agent_running' ? 'maestro' : mode
  const config = AGENT_CONFIG[agentKey] ?? AGENT_CONFIG.maestro

  return (
    <AnimatePresence>
      {isStreaming && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: -4 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: -4 }}
          transition={{ duration: 0.2 }}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '5px 12px',
            borderRadius: 'var(--radius-full)',
            background: config.bg,
            border: `1px solid ${config.color}30`,
          }}
        >
          {/* Dot pulsante */}
          <div className="agent-pulse" style={{
            width: '6px', height: '6px',
            borderRadius: '50%',
            backgroundColor: config.color,
            flexShrink: 0,
          }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: config.color, fontFamily: 'var(--font-sans)' }}>
            {config.label}
          </span>
          {/* Dots de loading */}
          <div style={{ display: 'flex', gap: '3px', alignItems: 'center' }}>
            {[0, 1, 2].map(i => (
              <motion.div
                key={i}
                animate={{ opacity: [0.2, 1, 0.2], y: [0, -2, 0] }}
                transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
                style={{ width: '3px', height: '3px', borderRadius: '50%', backgroundColor: config.color }}
              />
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
