import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage as ChatMessageType } from '../types'

interface Props {
  message: ChatMessageType
}

const AGENT_META: Record<string, { color: string; label: string; dot: string }> = {
  Maestro: { color: '#a78bfa', label: 'Maestro',  dot: '#7c3aed' },
  Scout:   { color: '#a78bfa', label: 'Scout',    dot: '#7c3aed' },
  Curator: { color: '#22d3ee', label: 'Curator',  dot: '#22d3ee' },
  Coach:   { color: '#34d399', label: 'Coach',    dot: '#34d399' },
}

export function ChatMessage({ message }: Props) {
  const isUser   = message.role === 'user'
  const isSystem = message.role === 'system'
  const meta = message.agent ? AGENT_META[message.agent] : AGENT_META.Maestro

  /* ── Mensagem de sistema (erro) ── */
  if (isSystem) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{ display: 'flex', justifyContent: 'center', margin: '8px 0' }}
      >
        <span style={{
          fontSize: '12px', padding: '4px 14px',
          borderRadius: 'var(--radius-full)',
          background: 'rgba(251,113,133,0.08)',
          border: '1px solid rgba(251,113,133,0.2)',
          color: 'var(--rose)',
          fontFamily: 'var(--font-mono)',
        }}>
          {message.content}
        </span>
      </motion.div>
    )
  }

  /* ── Mensagem do usuário ── */
  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.18 }}
        style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}
      >
        <div style={{
          maxWidth: '68%',
          padding: '10px 16px',
          borderRadius: 'var(--radius-lg)',
          borderBottomRightRadius: 'var(--radius-sm)',
          background: 'linear-gradient(135deg, rgba(124,58,237,0.2) 0%, rgba(124,58,237,0.12) 100%)',
          border: '1px solid rgba(124,58,237,0.25)',
          fontSize: '14px',
          color: 'var(--text-primary)',
          fontFamily: 'var(--font-sans)',
          lineHeight: 1.6,
        }}>
          {message.content}
        </div>
      </motion.div>
    )
  }

  /* ── Mensagem do agente ── */
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      style={{ display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'flex-start' }}
    >
      {/* Avatar do agente */}
      <div style={{
        width: '32px', height: '32px',
        borderRadius: 'var(--radius-md)',
        background: `linear-gradient(135deg, ${meta.dot}25 0%, ${meta.dot}10 100%)`,
        border: `1px solid ${meta.dot}30`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
        marginTop: '2px',
      }}>
        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: meta.dot, boxShadow: `0 0 8px ${meta.dot}` }} />
      </div>

      {/* Conteúdo */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Label */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span style={{
            fontSize: '12px', fontWeight: 700,
            color: meta.color,
            fontFamily: 'var(--font-sans)',
            letterSpacing: '0.01em',
          }}>
            {meta.label}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-ghost)', fontFamily: 'var(--font-mono)' }}>
            {message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Bubble */}
        <div style={{
          padding: '14px 16px',
          borderRadius: 'var(--radius-lg)',
          borderTopLeftRadius: 'var(--radius-sm)',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        }}>
          <div className="prose-chat">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {message.isStreaming && (
              <span className="cursor-blink" style={{ color: meta.color, marginLeft: '2px' }}>▌</span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
