import { AnimatePresence, motion } from 'framer-motion'
import { Activity, BriefcaseBusiness, CheckCircle2, CloudOff, Loader2, Radio } from 'lucide-react'
import type { AgentName, ConnectionStatus, SessionMode } from '../types'

interface Props {
  activeAgent: AgentName
  connectionStatus: ConnectionStatus
  isConnected: boolean
  isStreaming: boolean
  mode: SessionMode
}

const CONNECTION_LABEL: Record<ConnectionStatus, string> = {
  connecting: 'Conectando',
  connected: 'Conectado',
  reconnecting: 'Reconectando...',
  offline: 'Sem conexão',
}

const MODE_LABEL: Record<SessionMode, string> = {
  init: 'Inicializando',
  quiz: 'Criando perfil',
  quiz_resume: 'Retomando perfil',
  menu: 'Menu principal',
  scout: 'Vagas',
  curator: 'Cursos',
  coach: 'Entrevista',
  agent_running: 'Processando',
}

const ROUTE_STEPS: Array<{ key: string; label: string; modes: SessionMode[] }> = [
  { key: 'diagnostico', label: 'Diagnóstico', modes: ['init', 'quiz', 'quiz_resume'] },
  { key: 'oportunidades', label: 'Oportunidades', modes: ['menu', 'scout'] },
  { key: 'evolucao', label: 'Evolução', modes: ['curator'] },
  { key: 'entrevista', label: 'Entrevista', modes: ['coach'] },
]

export function StatusBar({
  activeAgent,
  connectionStatus,
  isConnected,
  isStreaming,
  mode,
}: Props) {
  const connected = isConnected && connectionStatus === 'connected'
  const connectionIcon = connected ? CheckCircle2 : connectionStatus === 'offline' ? CloudOff : Loader2
  const ConnectionIcon = connectionIcon
  const activeRouteIndex = Math.max(0, ROUTE_STEPS.findIndex(step => step.modes.includes(mode)))

  return (
    <header className="status-bar">
      <div className="brand-lockup" aria-label="import vagas">
        <div className="brand-mark" aria-hidden="true">
          <BriefcaseBusiness size={18} />
        </div>

        <div className="brand-copy">
          <div className="brand-name">
            <span>import</span>
            <strong>vagas</strong>
          </div>
          <span className="brand-subtitle">multi-agente de carreira</span>
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={`${mode}-${activeAgent}-${isStreaming}`}
          className="status-center"
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          transition={{ duration: 0.18 }}
        >
          {isStreaming ? (
            <Activity size={14} aria-hidden="true" />
          ) : (
            <Radio size={14} aria-hidden="true" />
          )}
          <span>{isStreaming ? `${activeAgent} respondendo` : MODE_LABEL[mode]}</span>
        </motion.div>
      </AnimatePresence>

      <nav className="hud-route" aria-label="Esteira de carreira">
        {ROUTE_STEPS.map((step, index) => (
          <span
            key={step.key}
            className={`hud-route-step ${index <= activeRouteIndex ? 'reached' : ''} ${index === activeRouteIndex ? 'current' : ''}`}
          >
            <span aria-hidden="true" />
            <small>{step.label}</small>
          </span>
        ))}
      </nav>

      <div className={`connection-chip ${connected ? 'connected' : 'offline'}`}>
        <ConnectionIcon size={14} className={connectionStatus === 'connecting' || connectionStatus === 'reconnecting' ? 'spin' : ''} />
        <span>{CONNECTION_LABEL[connectionStatus]}</span>
      </div>
    </header>
  )
}
