import { type KeyboardEvent, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowUp,
  ClipboardList,
  FileText,
  GitCompare,
  GraduationCap,
  RotateCcw,
  Scale,
  Search,
  Sparkles,
  UserRoundCheck,
} from 'lucide-react'
import type { SessionMode } from '../types'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
  isStreaming: boolean
  mode: SessionMode
}

type Accent = 'scout' | 'curator' | 'coach' | 'maestro' | 'match' | 'tailor' | 'pdi' | 'recon'

interface MenuOption {
  command: string
  title: string
  helper: string
  icon: typeof Search
  accent: Accent
}

interface MenuSection {
  label: string
  options: MenuOption[]
}

const MENU_SECTIONS: MenuSection[] = [
  {
    label: 'Esteira de Carreira',
    options: [
      { command: 'A', title: 'Encontrar oportunidades', helper: 'Scout busca vagas compatíveis', icon: Search, accent: 'scout' },
      { command: 'B', title: 'Mapear lacunas e evolução', helper: 'Curator monta sua trilha', icon: GraduationCap, accent: 'curator' },
      { command: 'C', title: 'Simular entrevista', helper: 'Coach treina suas respostas', icon: UserRoundCheck, accent: 'coach' },
      { command: 'D', title: 'Refazer diagnóstico', helper: 'Maestro reinicia seu perfil', icon: RotateCcw, accent: 'maestro' },
    ],
  },
  {
    label: 'Esteira de Candidatura',
    options: [
      { command: 'E', title: 'Analisar vaga', helper: 'Cole a descrição da vaga', icon: FileText, accent: 'match' },
      { command: 'F', title: 'Comparar vaga × currículo', helper: 'Score de aderência', icon: GitCompare, accent: 'match' },
      { command: 'G', title: 'Sugestões de currículo', helper: 'Como adaptar com segurança', icon: Sparkles, accent: 'tailor' },
      { command: 'H', title: 'Gerar PDI', helper: 'Plano de desenvolvimento', icon: ClipboardList, accent: 'pdi' },
      { command: 'I', title: 'Reconciliar perfil', helper: 'Perfil × currículo × vaga', icon: Scale, accent: 'recon' },
    ],
  },
]

export function ChatInput({ onSend, disabled, isStreaming, mode }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const hasValue = value.trim().length > 0

  // Cards de opção entram apenas quando o menu está pronto, ou seja, quando o
  // agente terminou de digitar. Durante o streaming a barra de escrita continua.
  const showOptions = mode === 'menu' && !isStreaming
  const isAwaitingJob = mode === 'await_job_description'

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

  const placeholder = disabled
    ? 'Aguardando resposta...'
    : isAwaitingJob
      ? 'Cole a descrição da vaga aqui... (menu para cancelar)'
      : 'Escreva sua mensagem para o Maestro...'

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
            {MENU_SECTIONS.map((section, sectionIndex) => (
              <div key={section.label} className={`menu-section menu-section-${sectionIndex}`}>
                <p className="menu-section-label">{section.label}</p>
                <div className="menu-section-options">
                  {section.options.map((option, index) => {
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
                </div>
              </div>
            ))}
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
              placeholder={placeholder}
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
