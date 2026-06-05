import { type KeyboardEvent, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUp, GraduationCap, RefreshCcw, Search, UserRoundCheck } from 'lucide-react'
import type { SessionMode } from '../types'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
  mode: SessionMode
}

const MENU_ACTIONS = [
  {
    key: 'A',
    title: 'Buscar vagas',
    agent: 'Scout',
    description: 'Encontra vagas compatíveis e calcula match com suas habilidades.',
    icon: Search,
    className: 'menu-scout',
  },
  {
    key: 'B',
    title: 'Encontrar cursos',
    agent: 'Curator',
    description: 'Recomenda materiais para preencher lacunas técnicas.',
    icon: GraduationCap,
    className: 'menu-curator',
  },
  {
    key: 'C',
    title: 'Simular entrevista',
    agent: 'Coach',
    description: 'Treina perguntas técnicas e comportamentais com feedback.',
    icon: UserRoundCheck,
    className: 'menu-coach',
  },
  {
    key: 'D',
    title: 'Refazer perfil',
    agent: 'Maestro',
    description: 'Atualiza área, nível, preferências e habilidades.',
    icon: RefreshCcw,
    className: 'menu-maestro',
  },
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

  const handleQuickSend = (message: string) => {
    if (!disabled) onSend(message)
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
      <AnimatePresence>
        {isMenu && (
          <motion.section
            className="menu-actions"
            aria-label="Ações principais"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="menu-actions-header">
              <strong>Menu principal</strong>
              <span>Escolha um card ou digite A, B, C ou D.</span>
            </div>

            <div className="menu-action-grid">
              {MENU_ACTIONS.map(item => {
                const Icon = item.icon

                return (
                  <motion.button
                    key={item.key}
                    type="button"
                    className={`menu-action-card ${item.className}`}
                    disabled={disabled}
                    onClick={() => handleQuickSend(item.key)}
                    whileHover={disabled ? undefined : { y: -2 }}
                    whileTap={disabled ? undefined : { scale: 0.98 }}
                    aria-label={`${item.key}: ${item.title} com agente ${item.agent}`}
                  >
                    <span className="menu-card-key">{item.key}</span>
                    <span className="menu-card-icon">
                      <Icon size={18} aria-hidden="true" />
                    </span>
                    <span className="menu-card-copy">
                      <strong>{item.title}</strong>
                      <small>Agente: {item.agent}</small>
                      <em>{item.description}</em>
                    </span>
                  </motion.button>
                )
              })}
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      <div className={`composer ${hasValue ? 'has-value' : ''}`}>
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
      </div>

      <p className="composer-hint">Enter envia. Shift+Enter cria uma nova linha.</p>
    </footer>
  )
}
