import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChatMessage } from './ChatMessage'
import type { ChatMessage as ChatMessageType } from '../types'

interface Props {
  messages: ChatMessageType[]
  isStreaming: boolean
}

export function ChatTerminal({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div
      className="dot-grid"
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '28px 28px 8px',
        backgroundColor: 'var(--bg-base)',
      }}
    >
      {/* Estado vazio — splash */}
      {messages.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            height: '100%', textAlign: 'center', gap: '16px',
          }}
        >
          {/* Logo grande */}
          <div style={{
            width: '64px', height: '64px',
            borderRadius: '18px',
            background: 'linear-gradient(135deg, var(--violet) 0%, #5b21b6 100%)',
            boxShadow: '0 0 40px rgba(124,58,237,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '4px',
          }}>
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M5 7h18M5 14h13M5 21h9" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              <circle cx="22" cy="20" r="4.5" stroke="white" strokeWidth="2"/>
              <path d="M22 17.5V16" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>

          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 800, fontSize: '22px',
              letterSpacing: '-0.03em',
              marginBottom: '6px',
            }}>
              <span style={{ color: 'var(--text-primary)' }}>import </span>
              <span style={{
                background: 'linear-gradient(90deg, var(--violet-light), var(--cyan))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>vagas</span>
            </div>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', maxWidth: '280px', lineHeight: 1.6 }}>
              Conectando ao Maestro...
            </p>
          </div>

          {/* Dots de loading */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {[0, 1, 2].map(i => (
              <motion.div
                key={i}
                animate={{ opacity: [0.2, 1, 0.2], scale: [0.8, 1, 0.8] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--violet)' }}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Mensagens */}
      <AnimatePresence initial={false}>
        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </AnimatePresence>

      <div ref={bottomRef} style={{ height: '8px' }} />
    </div>
  )
}
