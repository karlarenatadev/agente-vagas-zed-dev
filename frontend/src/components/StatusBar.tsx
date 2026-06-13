import { AnimatePresence, motion } from 'framer-motion'
import { Activity, BriefcaseBusiness, CheckCircle2, CloudOff, Loader2, Radio } from 'lucide-react'
import type { ConnectionStatus, SessionMode } from '../types'

interface Props {
  connectionStatus: ConnectionStatus
  isConnected: boolean
  isStreaming: boolean
  mode: SessionMode
  onGoHome: () => void
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

export function StatusBar({
  connectionStatus,
  isConnected,
  isStreaming,
  mode,
  onGoHome,
}: Props) {
  const connected = isConnected && connectionStatus === 'connected'
  const connectionIcon = connected ? CheckCircle2 : connectionStatus === 'offline' ? CloudOff : Loader2
  const ConnectionIcon = connectionIcon

  return (
    <header className="status-bar">
      <button
        type="button"
        className="brand-lockup"
        aria-label="Voltar para o painel inicial"
        onClick={onGoHome}
      >
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
      </button>

      <AnimatePresence mode="wait">
        <motion.div
          key={`${mode}-${isStreaming}`}
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
          <span>{isStreaming ? 'Respondendo...' : MODE_LABEL[mode]}</span>
        </motion.div>
      </AnimatePresence>

      <div className={`connection-chip ${connected ? 'connected' : 'offline'}`}>
        <ConnectionIcon size={14} className={connectionStatus === 'connecting' || connectionStatus === 'reconnecting' ? 'spin' : ''} />
        <span>{CONNECTION_LABEL[connectionStatus]}</span>
      </div>
    </header>
  )
}
