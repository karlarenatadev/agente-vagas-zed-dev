import { type KeyboardEvent, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUp, GraduationCap, RotateCcw, Search, UserRoundCheck } from 'lucide-react'
import type { SessionMode } from '../types'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
  isStreaming: boolean
  mode: SessionMode
}

const MENU_OPTIONS = [
  { command: 'A', title: 'Encontrar oportunidades', helper: 'Scout busca vagas compatíveis', icon: Search, accent: 'scout' },
  { command: 'B', title: 'Mapear lacunas e evolução', helper: 'Curator monta sua trilha', icon: GraduationCap, accent: 'curator' },
  { command: 'C', title: 'Simular entrevista', helper: 'Coach treina suas respostas', icon: UserRoundCheck, accent: 'coach' },
  { command: 'D', title: 'Refazer diagnóstico', helper: 'Maestro reinicia seu perfil', icon: RotateCcw, accent: 'maestro' },
] as const

export function ChatInput({ onSend, disabled, isStreaming, mode }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const hasValue = value.trim().length > 0

  // Cards de opção entram apenas quando o menu está pronto, ou seja, quando o
  // agente terminou de digitar. Durante o streaming a barra de escrita continua.
  const showOptions = mode === 'menu' && !isStreaming

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return

    onSend(trimmed)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const element = textareaRef.current
    if (!element) return

    element.style.height = 'auto'
    element.style.height = `${Math.min(element.scrollHeight, 128)}px`
  }

  return (
    <footer className="chat-input-shell">
      <AnimatePresence mode="wait" initial={false}>
        {showOptions ? (
          <motion.div
            key="menu-options"
            className="menu-options"
            role="group"
            aria-label="Escolha uma opção da esteira"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          >
            {MENU_OPTIONS.map((option, index) => {
              const Icon = option.icon
              return (
                <motion.button
                  key={option.command}
                  type="button"
                  className={`menu-option accent-${option.accent}`}
                  onClick={() => onSend(option.command)}
                  disabled={disabled}
                  initial={{ opacity: 0, y: 14, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ delay: 0.05 + index * 0.06, duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  whileHover={disabled ? undefined : { y: -3 }}
                  whileTap={disabled ? undefined : { scale: 0.97 }}
                >
                  <span className="menu-option-key">{option.command}</span>
                  <span className="menu-option-icon" aria-hidden="true">
                    <Icon size={18} />
                  </span>
                  <span className="menu-option-copy">
                    <strong>{option.title}</strong>
                    <small>{option.helper}</small>
                  </span>
                </motion.button>
              )
            })}
          </motion.div>
        ) : (
          <motion.div
            key="composer"
            className={`composer floating ${hasValue ? 'has-value' : ''}`}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          >
            <textarea
              ref={textareaRef}
              value={value}
              onChange={event => setValue(event.target.value)}
              onKeyDown={handleKeyDown}
              onInput={handleInput}
              disabled={disabled}
              placeholder={disabled ? 'Aguardando resposta...' : 'Escreva sua mensagem para o Maestro...'}
              rows={1}
              aria-label="Mensagem para o Maestro"
            />

            <motion.button
              className="send-button"
              type="button"
              whileHover={hasValue && !disabled ? { scale: 1.05 } : undefined}
              whileTap={hasValue && !disabled ? { scale: 0.94 } : undefined}
              onClick={handleSend}
              disabled={disabled || !hasValue}
              aria-label="Enviar mensagem"
            >
              <ArrowUp size={17} strokeWidth={2.5} aria-hidden="true" />
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </footer>
  )
}
