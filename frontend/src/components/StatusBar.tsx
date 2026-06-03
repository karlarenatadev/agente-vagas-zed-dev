import { motion, AnimatePresence } from 'framer-motion'
import type { SessionMode } from '../types'

interface Props {
  isConnected: boolean
  isStreaming: boolean
  mode: SessionMode
}

const MODE_META: Record<SessionMode, { label: string; color: string }> = {
  init:          { label: 'Inicializando',       color: 'var(--text-muted)' },
  quiz:          { label: 'Criando seu perfil',   color: 'var(--amber)' },
  quiz_resume:   { label: 'Retomando perfil',     color: 'var(--amber)' },
  menu:          { label: 'Pronto',               color: 'var(--emerald)' },
  scout:         { label: 'Buscando vagas',        color: 'var(--violet-light)' },
  curator:       { label: 'Buscando cursos',       color: 'var(--cyan)' },
  coach:         { label: 'Entrevista em curso',   color: 'var(--emerald)' },
  agent_running: { label: 'Processando',           color: 'var(--violet-light)' },
}

export function StatusBar({ isConnected, isStreaming, mode }: Props) {
  const meta = MODE_META[mode] ?? MODE_META.init

  return (
    <header
      className="flex items-center justify-between shrink-0"
      style={{
        height: '56px',
        padding: '0 24px',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
      }}
    >
      {/* ── Logo ── */}
      <div className="flex items-center gap-3">
        {/* Ícone */}
        <div
          className="flex items-center justify-center"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--violet) 0%, #5b21b6 100%)',
            boxShadow: '0 0 16px rgba(124,58,237,0.4)',
            flexShrink: 0,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 4h10M3 8h7M3 12h5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="13" cy="11" r="2.5" stroke="white" strokeWidth="1.2"/>
            <path d="M13 9.5V8" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
        </div>

        {/* Nome */}
        <div className="flex items-baseline gap-2">
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 800,
              fontSize: '17px',
              letterSpacing: '-0.03em',
              color: 'var(--text-primary)',
            }}
          >
            import
          </span>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 800,
              fontSize: '17px',
              letterSpacing: '-0.03em',
              background: 'linear-gradient(90deg, var(--violet-light), var(--cyan))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            vagas
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              color: 'var(--text-muted)',
              letterSpacing: '0.05em',
              marginLeft: '2px',
            }}
          >
            v1.0
          </span>
        </div>
      </div>

      {/* ── Status central ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={mode}
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          transition={{ duration: 0.2 }}
          className="flex items-center gap-2"
        >
          {isStreaming && (
            <motion.div
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              style={{
                width: '5px',
                height: '5px',
                borderRadius: '50%',
                backgroundColor: meta.color,
                boxShadow: `0 0 6px ${meta.color}`,
              }}
            />
          )}
          <span
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '12px',
              fontWeight: 500,
              color: isStreaming ? meta.color : 'var(--text-muted)',
              letterSpacing: '0.01em',
            }}
          >
            {isStreaming ? meta.label : 'import vagas · IA de carreira'}
          </span>
        </motion.div>
      </AnimatePresence>

      {/* ── Conexão ── */}
      <div className="flex items-center gap-3">
        {/* Indicador de streaming */}
        <AnimatePresence>
          {isStreaming && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full"
              style={{
                background: 'rgba(124,58,237,0.12)',
                border: '1px solid rgba(124,58,237,0.25)',
              }}
            >
              <motion.div
                animate={{ opacity: [1, 0.2, 1] }}
                transition={{ duration: 0.7, repeat: Infinity }}
                style={{
                  width: '4px', height: '4px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--violet-light)',
                }}
              />
              <span style={{ fontSize: '11px', color: 'var(--violet-light)', fontFamily: 'var(--font-mono)' }}>
                processando
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dot de conexão */}
        <div className="flex items-center gap-1.5">
          <motion.div
            animate={isConnected ? { scale: [1, 1.4, 1] } : {}}
            transition={{ duration: 2.5, repeat: Infinity }}
            style={{
              width: '6px', height: '6px',
              borderRadius: '50%',
              backgroundColor: isConnected ? 'var(--emerald)' : 'var(--rose)',
              boxShadow: isConnected ? '0 0 8px var(--emerald)' : 'none',
            }}
          />
          <span style={{ fontSize: '11px', color: isConnected ? 'var(--emerald)' : 'var(--rose)', fontFamily: 'var(--font-mono)' }}>
            {isConnected ? 'online' : 'offline'}
          </span>
        </div>
      </div>
    </header>
  )
}
