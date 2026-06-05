import { AnimatePresence, motion } from 'framer-motion'
import { Bot, GraduationCap, Search, UserRoundCheck } from 'lucide-react'
import type { AgentName, SessionMode } from '../types'

interface Props {
  activeAgent: AgentName
  mode: SessionMode
  isStreaming: boolean
}

const AGENT_CONFIG = {
  Maestro: {
    label: 'Maestro ativo',
    detail: 'orquestra o fluxo',
    className: 'agent-maestro',
    icon: Bot,
  },
  Scout: {
    label: 'Scout analisando',
    detail: 'vagas e match',
    className: 'agent-scout',
    icon: Search,
  },
  Curator: {
    label: 'Curator pesquisando',
    detail: 'cursos e lacunas',
    className: 'agent-curator',
    icon: GraduationCap,
  },
  Coach: {
    label: 'Coach em sessão',
    detail: 'entrevista simulada',
    className: 'agent-coach',
    icon: UserRoundCheck,
  },
} satisfies Record<AgentName, {
  label: string
  detail: string
  className: string
  icon: typeof Bot
}>

function resolveAgent(activeAgent: AgentName, mode: SessionMode): AgentName {
  if (mode === 'scout') return 'Scout'
  if (mode === 'curator') return 'Curator'
  if (mode === 'coach') return 'Coach'
  return activeAgent
}

export function AgentBadge({ activeAgent, mode, isStreaming }: Props) {
  const config = AGENT_CONFIG[resolveAgent(activeAgent, mode)]
  const Icon = config.icon

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={config.label}
        className={`agent-badge ${config.className} ${isStreaming ? 'is-active' : ''}`}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={{ duration: 0.18 }}
      >
        <span className="agent-badge-icon">
          <Icon size={14} aria-hidden="true" />
        </span>
        <span className="agent-badge-copy">
          <strong>{config.label}</strong>
          <small>{isStreaming ? 'respondendo agora' : config.detail}</small>
        </span>
        {isStreaming && <span className="agent-live-dot" aria-label="Agente processando" />}
      </motion.div>
    </AnimatePresence>
  )
}
