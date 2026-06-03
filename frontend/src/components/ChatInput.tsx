import { type KeyboardEvent, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowUp } from 'lucide-react'
import type { SessionMode } from '../types'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
  mode: SessionMode
}

const MENU_ACTIONS = [
  { key: 'A', label: 'Buscar Vagas',     icon: '⚔',  color: '#a78bfa', bg: 'rgba(124,58,237,0.1)',  border: 'rgba(124,58,237,0.25)' },
  { key: 'B', label: 'Cursos',           icon: '📚', color: '#22d3ee', bg: 'rgba(34,211,238,0.08)', border: 'rgba(34,211,238,0.2)' },
  { key: 'C', label: 'Entrevista',       icon: '🎯', color: '#34d399', bg: 'rgba(52,211,153,0.08)', border: 'rgba(52,211,153,0.2)' },
  { key: 'D', label: 'Refazer Quiz',     icon: '↺',  color: '#fbbf24', bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.2)' },
]

export function ChatInput({ onSend, disabled, mode }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isMenu = mode === 'menu'
  const hasValue = value.trim().length > 0

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`
  }

  return (
    <div style={{
      padding: '16px 24px 20px',
      backgroundColor: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-subtle)',
    }}>
      {/* ── Ações rápidas do menu ── */}
      <AnimatePresence>
        {isMenu && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ overflow: 'hidden', marginBottom: '12px' }}
          >
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {MENU_ACTIONS.map(({ key, label, icon, color, bg, border }) => (
                <motion.button
                  key={key}
                  whileHover={{ scale: 1.03, y: -1 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => !disabled && onSend(key)}
                  disabled={disabled}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '7px',
                    padding: '7px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: bg,
                    border: `1px solid ${border}`,
                    color,
                    fontSize: '13px', fontWeight: 600,
                    fontFamily: 'var(--font-sans)',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    opacity: disabled ? 0.45 : 1,
                    transition: 'opacity 0.15s',
                  }}
                >
                  <span style={{ fontSize: '14px' }}>{icon}</span>
                  <span>{label}</span>
                  <span style={{ fontSize: '10px', opacity: 0.55, fontFamily: 'var(--font-mono)' }}>[{key}]</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Campo de input ── */}
      <div
        style={{
          display: 'flex', alignItems: 'flex-end', gap: '10px',
          padding: '12px 14px',
          borderRadius: 'var(--radius-lg)',
          background: 'var(--bg-elevated)',
          border: `1px solid ${hasValue ? 'var(--border-focus)' : 'var(--border-default)'}`,
          boxShadow: hasValue ? '0 0 0 3px rgba(124,58,237,0.08)' : 'none',
          transition: 'border-color 0.2s, box-shadow 0.2s',
        }}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder={disabled ? 'Aguardando resposta...' : 'Escreva sua mensagem...'}
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: '14px',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)',
            lineHeight: '1.55',
            caretColor: 'var(--violet-light)',
          }}
        />

        {/* Botão enviar */}
        <motion.button
          whileHover={hasValue && !disabled ? { scale: 1.08 } : {}}
          whileTap={hasValue && !disabled ? { scale: 0.92 } : {}}
          onClick={handleSend}
          disabled={disabled || !hasValue}
          style={{
            width: '32px', height: '32px',
            borderRadius: 'var(--radius-md)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: hasValue && !disabled
              ? 'linear-gradient(135deg, var(--violet) 0%, #5b21b6 100%)'
              : 'var(--bg-overlay)',
            border: 'none',
            cursor: hasValue && !disabled ? 'pointer' : 'not-allowed',
            transition: 'background 0.2s',
            flexShrink: 0,
            boxShadow: hasValue && !disabled ? '0 0 12px rgba(124,58,237,0.35)' : 'none',
          }}
        >
          <ArrowUp
            size={15}
            color={hasValue && !disabled ? 'white' : 'var(--text-ghost)'}
            strokeWidth={2.5}
          />
        </motion.button>
      </div>

      {/* ── Hint ── */}
      <p style={{
        fontSize: '11px', color: 'var(--text-ghost)',
        textAlign: 'center', marginTop: '8px',
        fontFamily: 'var(--font-mono)',
      }}>
        Enter para enviar · Shift+Enter para nova linha
      </p>
    </div>
  )
}
