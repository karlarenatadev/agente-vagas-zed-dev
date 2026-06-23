import { type KeyboardEvent, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowUp,
  ClipboardList,
  Compass,
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
  key: string
  label: string
  caption: string
  icon: typeof Search
  accent: Accent
  options: MenuOption[]
}

// Fluxo master/detail: 2 botões compactos de esteira. Ao clicar em um,
// o outro (e todo o resto) some e ficam só as opções daquela esteira,
// com um botão "Esteiras" para voltar. Tudo animado.
const MENU_SECTIONS: MenuSection[] = [
  {
    key: 'career',
    label: 'Esteira de Carreira',
    caption: 'Perfil, vagas, evolução e entrevista',
    icon: Compass,
    accent: 'scout',
    options: [
      { command: 'A', title: 'Encontrar oportunidades', helper: 'Scout busca vagas compatíveis', icon: Search, accent: 'scout' },
      { command: 'B', title: 'Mapear lacunas e evolução', helper: 'Curator monta sua trilha', icon: GraduationCap, accent: 'curator' },
      { command: 'C', title: 'Simular entrevista', helper: 'Coach treina suas respostas', icon: UserRoundCheck, accent: 'coach' },
      { command: 'D', title: 'Refazer diagnóstico', helper: 'Maestro reinicia seu perfil', icon: RotateCcw, accent: 'maestro' },
    ],
  },
  {
    key: 'application',
    label: 'Esteira de Candidatura',
    caption: 'Da vaga ao PDI para uma candidatura específica',
    icon: ClipboardList,
    accent: 'match',
    options: [
      { command: 'E', title: 'Analisar vaga', helper: 'Cole a descrição da vaga', icon: FileText, accent: 'match' },
      { command: 'F', title: 'Comparar vaga × currículo', helper: 'Score de aderência', icon: GitCompare, accent: 'match' },
      { command: 'G', title: 'Sugestões de currículo', helper: 'Como adaptar com segurança', icon: Sparkles, accent: 'tailor' },
      { command: 'H', title: 'Gerar PDI', helper: 'Plano de desenvolvimento', icon: ClipboardList, accent: 'pdi' },
      { command: 'I', title: 'Reconciliar perfil', helper: 'Perfil × currículo × vaga', icon: Scale, accent: 'recon' },
    ],
  },
]

const EASE = [0.22, 1, 0.36, 1] as const

export function ChatInput({ onSend, disabled, isStreaming, mode }: Props) {
  const [value, setValue] = useState('')
  // null = mostrando os 2 botões de esteira (master).
  // string = esteira aberta, mostrando só as opções dela (detail).
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const hasValue = value.trim().length > 0

  // Cards de opção entram só quando o menu está pronto (agente parou de digitar).
  const showOptions = mode === 'menu' && !isStreaming
  const isAwaitingJob = mode === 'await_job_description'

  // Ao sair do menu (ex.: um agente assume), volta para a seleção de esteiras,
  // para que o usuário sempre reencontre os 2 botões ao retornar. Ajuste de
  // estado durante o render (padrão recomendado pelo React) em vez de useEffect.
  const [prevShowOptions, setPrevShowOptions] = useState(showOptions)
  if (prevShowOptions !== showOptions) {
    setPrevShowOptions(showOptions)
    if (!showOptions && activeSection !== null) setActiveSection(null)
  }

  const current = MENU_SECTIONS.find(section => section.key === activeSection) ?? null

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
            key="esteira-flow"
            className="esteira-flow"
            role="group"
            aria-label="Escolha uma esteira"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.28, ease: EASE }}
          >
            <AnimatePresence mode="wait" initial={false}>
              {current ? (
                <motion.div
                  key={`detail-${current.key}`}
                  className="esteira-detail"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8, scale: 0.985 }}
                  transition={{ duration: 0.3, ease: EASE }}
                >
                  <div className="esteira-detail-head">
                    <button
                      type="button"
                      className="esteira-back"
                      onClick={() => setActiveSection(null)}
                      disabled={disabled}
                      aria-label="Voltar para a seleção de esteiras"
                    >
                      <ArrowLeft size={16} aria-hidden="true" />
                      Esteiras
                    </button>
                    <span className={`esteira-active accent-${current.accent}`}>
                      <current.icon size={15} aria-hidden="true" />
                      {current.label}
                    </span>
                  </div>

                  <div className="esteira-options">
                    {current.options.map((option, index) => {
                      const Icon = option.icon
                      return (
                        <motion.button
                          key={option.command}
                          type="button"
                          className={`menu-option accent-${option.accent}`}
                          onClick={() => onSend(option.command)}
                          disabled={disabled}
                          initial={{ opacity: 0, y: 10, scale: 0.97 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          transition={{ delay: 0.04 + index * 0.05, duration: 0.32, ease: EASE }}
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
                </motion.div>
              ) : (
                <motion.div
                  key="picker"
                  className="esteira-picker"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8, scale: 0.985 }}
                  transition={{ duration: 0.3, ease: EASE }}
                >
                  {MENU_SECTIONS.map((section, index) => {
                    const Icon = section.icon
                    return (
                      <motion.button
                        key={section.key}
                        type="button"
                        className={`esteira-pill accent-${section.accent}`}
                        onClick={() => setActiveSection(section.key)}
                        disabled={disabled}
                        aria-label={`Abrir ${section.label}`}
                        initial={{ opacity: 0, y: 10, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: 0.05 * index, duration: 0.3, ease: EASE }}
                        whileHover={disabled ? undefined : { y: -2 }}
                        whileTap={disabled ? undefined : { scale: 0.98 }}
                      >
                        <span className="esteira-pill-icon" aria-hidden="true">
                          <Icon size={16} />
                        </span>
                        <span className="esteira-pill-copy">
                          <strong>{section.label}</strong>
                          <small>{section.caption}</small>
                        </span>
                      </motion.button>
                    )
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ) : (
          <motion.div
            key="composer"
            className={`composer floating ${hasValue ? 'has-value' : ''}`}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.28, ease: EASE }}
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
