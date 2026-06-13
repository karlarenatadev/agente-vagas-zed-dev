import { lazy, Suspense, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Briefcase,
  BriefcaseBusiness,
  FileText,
  GraduationCap,
  PanelLeft,
  RefreshCcw,
  Search,
  Sparkles,
  UserRoundCheck,
  X,
} from 'lucide-react'

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
const JobDescriptionAnalyzer = lazy(() => import('./components/JobDescriptionAnalyzer'))

const MODE_STATUS: Record<SessionMode, (step: number) => string> = {
  init: () => 'Preparando a conversa',
  quiz: step => `Quiz de perfil: pergunta ${Math.min(step + 1, 7)} de 7`,
  quiz_resume: () => 'Retomar ou refazer perfil',
  menu: () => 'Esteira de carreira pronta',
  scout: () => 'Scout analisando vagas compatíveis',
  curator: () => 'Curator montando recomendações',
  coach: () => 'Coach conduzindo entrevista',
  agent_running: () => 'Agente especializado em execução',
}

const CAREER_ACTIONS = [
  {
    key: 'A',
    title: 'Encontrar oportunidades',
    description: 'Radar de vagas compatíveis com o perfil.',
    icon: Search,
    className: 'workbench-scout',
    command: 'A',
  },
  {
    key: 'B',
    title: 'Mapear lacunas',
    description: 'Gaps, trilha e evolução prioritária.',
    icon: GraduationCap,
    className: 'workbench-curator',
    command: 'B',
  },
  {
    key: 'C',
    title: 'Simular entrevista',
    description: 'Treino direcionado às oportunidades.',
    icon: UserRoundCheck,
    className: 'workbench-coach',
    command: 'C',
  },
  {
    key: 'D',
    title: 'Refazer diagnóstico',
    description: 'Atualizar área, nível e preferências.',
    icon: RefreshCcw,
    className: 'workbench-maestro',
    command: 'D',
  },
]

const NEXT_ACTION: Record<SessionMode, { label: string; detail: string; command: string }> = {
  init: {
    label: 'Iniciar diagnóstico',
    detail: 'Monte a base que orienta vagas, lacunas e entrevista.',
    command: 'Quero criar meu perfil profissional',
  },
  quiz: {
    label: 'Concluir diagnóstico',
    detail: 'Finalize o perfil para liberar a esteira de carreira.',
    command: '',
  },
  quiz_resume: {
    label: 'Retomar perfil',
    detail: 'Continue ou refaça o diagnóstico antes das recomendações.',
    command: '',
  },
  menu: {
    label: 'Encontrar oportunidades',
    detail: 'Comece pelo radar de vagas compatíveis.',
    command: 'A',
  },
  scout: {
    label: 'Mapear lacunas',
    detail: 'Use os resultados do Scout para priorizar evolução.',
    command: 'B',
  },
  curator: {
    label: 'Simular entrevista',
    detail: 'Treine com base nas oportunidades e lacunas.',
    command: 'C',
  },
  coach: {
    label: 'Revisar respostas',
    detail: 'Continue a entrevista ou use o plano de preparação.',
    command: '',
  },
  agent_running: {
    label: 'Aguardar agente',
    detail: 'A esteira está processando a etapa atual.',
    command: '',
  },
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
  const [resumeModalOpen, setResumeModalOpen] = useState(false)
  const [jobAnalyzerOpen, setJobAnalyzerOpen] = useState(false)
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
  const nextAction = NEXT_ACTION[session.mode] ?? NEXT_ACTION.menu

  const handleQuickStart = (message: string) => {
    if (!disabled) sendMessage(message)
  }

  const handleWorkbenchAction = (command: string) => {
    if (command) handleQuickStart(command)
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
            activeAgent={activeAgent}
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
                onClick={() => setJobAnalyzerOpen(true)}
                className="applications-btn"
                type="button"
                aria-label="Analisar descrição de vaga"
              >
                <BriefcaseBusiness size={15} />
                <span className="btn-text">Analisar vaga</span>
              </motion.button>

              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setResumeModalOpen(true)}
                className="applications-btn"
                type="button"
                aria-label="Analisar currículo em PDF, DOCX ou TXT"
              >
                <FileText size={15} />
                <span className="btn-text">Currículo</span>
              </motion.button>

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
                <QuizPanel
                  mode={session.mode === 'quiz_resume' ? 'quiz_resume' : 'quiz'}
                  step={session.quiz_step}
                  question={currentQuestion}
                  onAnswer={sendMessage}
                  disabled={disabled}
                />
              </div>
            </Suspense>
          ) : (
            <>
              <section className="career-workbench" aria-label="Área de trabalho de carreira">
                <div className="career-workbench-copy">
                  <p className="eyebrow">
                    <Sparkles size={13} aria-hidden="true" />
                    Esteira de carreira
                  </p>
                  <h2>{nextAction.label}</h2>
                  <span>{nextAction.detail}</span>
                  <div className="career-signal-row" aria-label="Sinais usados pela IA">
                    <small>Perfil</small>
                    <small>Match</small>
                    <small>Lacunas</small>
                    <small>Entrevista</small>
                  </div>
                </div>

                <div className="career-workbench-actions" aria-label="Ações principais">
                  {CAREER_ACTIONS.map(action => {
                    const Icon = action.icon
                    const isRecommended = nextAction.command === action.command

                    return (
                      <motion.button
                        key={action.key}
                        type="button"
                        className={`career-action-card ${action.className} ${isRecommended ? 'recommended' : ''}`}
                        disabled={disabled}
                        onClick={() => handleWorkbenchAction(action.command)}
                        whileHover={disabled ? undefined : { y: -2 }}
                        whileTap={disabled ? undefined : { scale: 0.98 }}
                        aria-label={`${action.key}: ${action.title}`}
                      >
                        <span className="career-action-key" aria-hidden="true">{action.key}</span>
                        <span className="career-action-icon">
                          <Icon size={16} aria-hidden="true" />
                        </span>
                        <span>
                          <strong>{action.title}</strong>
                          <small>{action.description}</small>
                        </span>
                      </motion.button>
                    )
                  })}
                </div>
              </section>

              <ChatTerminal
                disabled={disabled}
                isStreaming={isStreaming}
                messages={messages}
                mode={session.mode}
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

      {resumeModalOpen && (
        <div className="resume-modal" role="dialog" aria-modal="true" aria-labelledby="resume-modal-title">
          <button
            type="button"
            className="resume-modal-backdrop"
            aria-label="Fechar upload de currículo"
            onClick={() => setResumeModalOpen(false)}
          />
          <section className="resume-modal-panel">
            <div className="resume-modal-header">
              <div>
                <p className="eyebrow">Currículo</p>
                <h2 id="resume-modal-title">Analisar PDF, DOCX ou TXT</h2>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Fechar upload de currículo"
                onClick={() => setResumeModalOpen(false)}
              >
                <X size={17} />
              </button>
            </div>
            <ResumeUpload onContinueQuiz={() => setResumeModalOpen(false)} />
          </section>
        </div>
      )}

      {jobAnalyzerOpen && (
        <div className="resume-modal" role="dialog" aria-modal="true" aria-labelledby="job-analyzer-title">
          <button
            type="button"
            className="resume-modal-backdrop"
            aria-label="Fechar análise de vaga"
            onClick={() => setJobAnalyzerOpen(false)}
          />
          <section className="resume-modal-panel job-analyzer-modal">
            <div className="resume-modal-header">
              <div>
                <p className="eyebrow">Inteligência de oportunidade</p>
                <h2 id="job-analyzer-title">Analisar descrição de vaga</h2>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Fechar análise de vaga"
                onClick={() => setJobAnalyzerOpen(false)}
              >
                <X size={17} />
              </button>
            </div>
            <Suspense fallback={<div className="loading-fallback">Carregando analisador...</div>}>
              <JobDescriptionAnalyzer />
            </Suspense>
          </section>
        </div>
      )}
    </div>
  )
}
