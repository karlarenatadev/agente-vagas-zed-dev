import { lazy, Suspense, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Briefcase, PanelLeft, Sparkles } from 'lucide-react'

import { AgentBadge } from './components/AgentBadge'
import { ChatInput } from './components/ChatInput'
import { ChatTerminal } from './components/ChatTerminal'
import { ProfilePanel } from './components/ProfilePanel'
import { ResumeUpload } from './components/ResumeUpload'
import { StatusBar } from './components/StatusBar'
import { useWebSocket } from './hooks/useWebSocket'
import type { SessionMode } from './types'

const QuizPanel = lazy(() => import('./components/QuizPanel'))
const ApplicationTracker = lazy(() => import('./components/ApplicationTracker'))

const MODE_STATUS: Record<SessionMode, (step: number) => string> = {
  init: () => 'Preparando a conversa',
  quiz: step => `Quiz de perfil: pergunta ${Math.min(step + 1, 7)} de 7`,
  quiz_resume: step => `Retomando perfil: pergunta ${Math.min(step + 1, 7)} de 7`,
  menu: () => 'Escolha uma ação para continuar',
  scout: () => 'Scout analisando vagas compatíveis',
  curator: () => 'Curator montando recomendações',
  coach: () => 'Coach conduzindo entrevista',
  agent_running: () => 'Agente especializado em execução',
}

function extractCurrentQuestion(content: string): string {
  const match = content.match(/\*\*Pergunta\s+\d+\/7:\*\*\s*([\s\S]+?)(?:\n\n|$)/)
  if (match) return match[1].trim()

  const lines = content.split('\n').map(line => line.trim()).filter(Boolean)
  return lines[lines.length - 1] ?? content
}

export default function App() {
  const {
    activeAgent,
    connectionStatus,
    isConnected,
    isStreaming,
    messages,
    session,
    sendMessage,
  } = useWebSocket()

  const [trackerOpen, setTrackerOpen] = useState(false)
  const [resumeUploadOpen, setResumeUploadOpen] = useState(true)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    typeof window !== 'undefined'
      ? window.matchMedia('(max-width: 1024px)').matches
      : false
  )

  const isQuiz = session.mode === 'quiz' || session.mode === 'quiz_resume'
  const disabled = isStreaming || !isConnected

  const currentQuestion = useMemo(() => {
    const lastAgentMsg = [...messages].reverse().find(message => message.role === 'agent')
    return lastAgentMsg ? extractCurrentQuestion(lastAgentMsg.content) : ''
  }, [messages])

  const statusText = MODE_STATUS[session.mode]?.(session.quiz_step) ?? 'Pronto'

  const handleQuickStart = (message: string) => {
    if (!disabled) sendMessage(message)
  }

  return (
    <div className="app-shell noise">
      <StatusBar
        activeAgent={activeAgent}
        connectionStatus={connectionStatus}
        isConnected={isConnected}
        isStreaming={isStreaming}
        mode={session.mode}
      />

      <div className="main-layout">
        {!sidebarCollapsed && (
          <button
            className="sidebar-backdrop"
            type="button"
            aria-label="Fechar painel de perfil"
            onClick={() => setSidebarCollapsed(true)}
          />
        )}

        <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <ProfilePanel
            onStartProfile={() => handleQuickStart('Quero criar meu perfil profissional')}
            onToggleCollapse={() => setSidebarCollapsed(value => !value)}
          />
        </div>

        <main className="main-content" aria-label="Conversa com o Maestro">
          <section className="workspace-header" aria-label="Contexto atual">
            <div className="workspace-title">
              <button
                className="icon-button"
                type="button"
                aria-label={sidebarCollapsed ? 'Abrir painel de perfil' : 'Fechar painel de perfil'}
                onClick={() => setSidebarCollapsed(value => !value)}
              >
                <PanelLeft size={18} />
              </button>

              <div>
                <p className="eyebrow">
                  <Sparkles size={13} aria-hidden="true" />
                  Maestro
                </p>
                <h1>Copiloto de carreira com IA</h1>
              </div>
            </div>

            <div className="workspace-actions">
              <span className="mode-pill">{statusText}</span>
              <AgentBadge activeAgent={activeAgent} mode={session.mode} isStreaming={isStreaming} />

              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setTrackerOpen(true)}
                className="applications-btn"
                type="button"
                aria-label="Abrir painel de candidaturas"
              >
                <Briefcase size={15} />
                <span className="btn-text">Candidaturas</span>
              </motion.button>
            </div>
          </section>

          {isQuiz ? (
            <Suspense fallback={<div className="loading-fallback">Carregando quiz...</div>}>
              <div className="quiz-flow">
                {resumeUploadOpen && (
                  <ResumeUpload onContinueQuiz={() => setResumeUploadOpen(false)} />
                )}
                <QuizPanel
                  step={session.quiz_step}
                  question={currentQuestion}
                  onAnswer={sendMessage}
                  disabled={disabled}
                />
              </div>
            </Suspense>
          ) : (
            <>
              <ChatTerminal
                disabled={disabled}
                isStreaming={isStreaming}
                messages={messages}
                onQuickAction={handleQuickStart}
              />
              <ChatInput
                onSend={sendMessage}
                disabled={disabled}
                mode={session.mode}
              />
            </>
          )}
        </main>
      </div>

      <Suspense fallback={<div className="loading-fallback">Carregando...</div>}>
        <ApplicationTracker isOpen={trackerOpen} onClose={() => setTrackerOpen(false)} />
      </Suspense>
    </div>
  )
}
