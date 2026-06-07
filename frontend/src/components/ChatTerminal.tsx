import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { GraduationCap, MessageSquareText, Search, Sparkles, Target, UserRoundCheck } from 'lucide-react'
import { ChatMessage } from './ChatMessage'
import type { ChatMessage as ChatMessageType, SessionMode } from '../types'

interface Props {
  disabled: boolean
  messages: ChatMessageType[]
  isStreaming: boolean
  mode: SessionMode
  onQuickAction: (message: string) => void
}

const WELCOME_ACTIONS = [
  {
    title: 'Criar perfil profissional',
    description: 'Fazer o diagnóstico guiado pelo Maestro.',
    command: 'Quero criar meu perfil profissional',
    icon: Target,
  },
  {
    title: 'Encontrar oportunidades',
    description: 'Buscar vagas alinhadas ao diagnóstico.',
    command: 'A',
    icon: Search,
  },
  {
    title: 'Mapear lacunas',
    description: 'Definir uma trilha de evolução.',
    command: 'B',
    icon: GraduationCap,
  },
  {
    title: 'Simular entrevista',
    description: 'Praticar uma entrevista direcionada.',
    command: 'C',
    icon: UserRoundCheck,
  },
]

export function ChatTerminal({ disabled, messages, mode, onQuickAction }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const visibleActions = mode === 'menu' ? WELCOME_ACTIONS : WELCOME_ACTIONS.slice(0, 1)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: messages.length > 2 ? 'smooth' : 'auto',
      block: 'end',
    })
  }, [messages])

  return (
    <section className="chat-terminal dot-grid" aria-label="Histórico da conversa">
      {messages.length === 0 && (
        <motion.div
          className="welcome-screen"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
        >
          <div className="welcome-hero">
            <div className="welcome-kicker">
              <Sparkles size={15} aria-hidden="true" />
              Maestro organiza sua esteira
            </div>

            <h2>Sua jornada de evolução profissional</h2>
            <p>
              Faça o diagnóstico, encontre oportunidades compatíveis, mapeie lacunas e prepare
              sua próxima entrevista com agentes especializados.
            </p>
          </div>

          <div className="agent-overview" aria-label="Agentes disponíveis">
            <span>Maestro: perfil e menu</span>
            <span>Scout: vagas</span>
            <span>Curator: cursos</span>
            <span>Coach: entrevistas</span>
          </div>

          <div className="welcome-actions">
            {visibleActions.map((item, index) => {
              const Icon = item.icon

              return (
                <motion.button
                  key={item.title}
                  type="button"
                  className="welcome-card"
                  disabled={disabled}
                  onClick={() => onQuickAction(item.command)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.08 * index, duration: 0.24 }}
                  whileHover={disabled ? undefined : { y: -2 }}
                  whileTap={disabled ? undefined : { scale: 0.98 }}
                >
                  <span className="welcome-card-icon">
                    <Icon size={18} aria-hidden="true" />
                  </span>
                  <span>
                    <strong>{item.title}</strong>
                    <small>{item.description}</small>
                  </span>
                </motion.button>
              )
            })}
          </div>

          <p className="welcome-hint">
            <MessageSquareText size={14} aria-hidden="true" />
            Você também pode escrever normalmente no campo abaixo.
          </p>
        </motion.div>
      )}

      <AnimatePresence initial={false}>
        {messages.map(message => (
          <ChatMessage key={message.id} message={message} />
        ))}
      </AnimatePresence>

      <div ref={bottomRef} className="chat-bottom-anchor" />
    </section>
  )
}
