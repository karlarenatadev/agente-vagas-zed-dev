import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { MotionConfig, motion } from 'framer-motion'
import {
  Briefcase,
  BriefcaseBusiness,
  FileText,
  Map,
  PanelLeft,
  Sparkles,
  X,
} from 'lucide-react'

import { AgentBadge } from './components/AgentBadge'
import { ApplicationPipeline } from './components/ApplicationPipeline'
import { ChatInput } from './components/ChatInput'
import { ProfilePanel } from './components/ProfilePanel'
import { ResumeUpload } from './components/ResumeUpload'
import { StatusBar } from './components/StatusBar'
import { useWebSocket } from './hooks/useWebSocket'
import type { DateFilter, SessionMode } from './types'

const QuizPanel = lazy(() => import('./components/QuizPanel'))
const ApplicationTracker = lazy(() => import('./components/ApplicationTracker'))
const JobDescriptionAnalyzer = lazy(() => import('./components/JobDescriptionAnalyzer'))
const PdiPlan = lazy(() => import('./components/PdiPlan'))
const ChatTerminal = lazy(() =>
  import('./components/ChatTerminal').then(module => ({ default: module.ChatTerminal }))
)

const SIDEBAR_COMPACT_STORAGE_KEY = 'import-vagas:sidebar-compact'

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

function extractCurrentQuestion(content: string): string {
  const match = content.match(/\*\*Pergunta\s+\d+\/7:\*\*\s*([\s\S]+?)(?:\n\n|$)/)
  if (match) return match[1].trim()

  const lines = content.split('\n').map(line => line.trim()).filter(Boolean)
  return (lines[lines.length - 1] ?? content).trim()
}

export default function App() {
  const {
    activeAgent,
    connectionStatus,
    isConnected,
    isStreaming,
    loadingState,
    messages,
    session,
    sendMessage,
  } = useWebSocket()

  const [trackerOpen, setTrackerOpen] = useState(false)
  const [resumeModalOpen, setResumeModalOpen] = useState(false)
  const [jobAnalyzerOpen, setJobAnalyzerOpen] = useState(false)
  const [pdiModalOpen, setPdiModalOpen] = useState(false)
  const resumeModalRef = useRef<HTMLElement>(null)
  const jobAnalyzerModalRef = useRef<HTMLElement>(null)
  const pdiModalRef = useRef<HTMLElement>(null)
  const [isMobileLayout, setIsMobileLayout] = useState(() =>
    typeof window !== 'undefined'
      ? window.matchMedia('(max-width: 1024px)').matches
      : false
  )
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    typeof window !== 'undefined'
      ? window.matchMedia('(max-width: 1024px)').matches
      : false
  )
  const [sidebarCompact, setSidebarCompact] = useState(() =>
    typeof window !== 'undefined'
      && window.localStorage.getItem(SIDEBAR_COMPACT_STORAGE_KEY) === 'true'
  )

  const isQuiz = session.mode === 'quiz' || session.mode === 'quiz_resume'
  const disabled = isStreaming || !isConnected

  const currentQuestion = useMemo(() => {
    const lastAgentMsg = [...messages].reverse().find(message => message.role === 'agent')
    return lastAgentMsg ? extractCurrentQuestion(lastAgentMsg.content) : ''
  }, [messages])

  const statusText = MODE_STATUS[session.mode]?.(session.quiz_step) ?? 'Pronto'
  const handleQuickStart = (message: string, dateFilter?: DateFilter) => {
    if (!disabled) sendMessage(message, dateFilter)
  }

  const handleContinueQuizAfterResume = () => {
    setResumeModalOpen(false)
    // Comando exato que o Maestro intercepta para (re)iniciar o diagnóstico
    // (ver START_PROFILE_COMMAND no backend). Reinicia o fluxo e pré-preenche
    // o quiz com as palavras-chave do currículo, perguntando só o que falta.
    handleQuickStart('quero criar meu perfil profissional')
  }

  const closeOverlays = () => {
    setTrackerOpen(false)
    setResumeModalOpen(false)
    setJobAnalyzerOpen(false)
    setPdiModalOpen(false)
  }

  useEffect(() => {
    const media = window.matchMedia('(max-width: 1024px)')
    const handleChange = (event: MediaQueryListEvent) => {
      setIsMobileLayout(event.matches)
      setSidebarCollapsed(event.matches)
    }

    media.addEventListener('change', handleChange)
    return () => media.removeEventListener('change', handleChange)
  }, [])

  useEffect(() => {
    const modal = resumeModalOpen
      ? resumeModalRef.current
      : jobAnalyzerOpen
        ? jobAnalyzerModalRef.current
        : pdiModalOpen
          ? pdiModalRef.current
          : null

    if (!modal) return

    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
    const focusableSelector = [
      'button:not(:disabled)',
      'a[href]',
      'input:not(:disabled)',
      'textarea:not(:disabled)',
      '[tabindex]:not([tabindex="-1"])',
    ].join(',')

    const focusableElements = () => [...modal.querySelectorAll<HTMLElement>(focusableSelector)]
      .filter(element => element.getClientRects().length > 0)

    window.requestAnimationFrame(() => {
      const preferredTarget = modal.querySelector<HTMLElement>('textarea, input:not([type="hidden"])')
      if (preferredTarget) {
        preferredTarget.focus()
      } else {
        focusableElements()[0]?.focus()
      }
    })

    const handleModalKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        if (resumeModalOpen) setResumeModalOpen(false)
        if (jobAnalyzerOpen) setJobAnalyzerOpen(false)
        if (pdiModalOpen) setPdiModalOpen(false)
        return
      }

      if (event.key !== 'Tab') return

      const elements = focusableElements()
      if (!elements.length) return
      const first = elements[0]
      const last = elements[elements.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleModalKeyDown)
    return () => {
      document.removeEventListener('keydown', handleModalKeyDown)
      previousFocus?.focus()
    }
  }, [jobAnalyzerOpen, pdiModalOpen, resumeModalOpen])

  const handleGoHome = () => {
    closeOverlays()
    if (window.matchMedia('(max-width: 1024px)').matches) {
      setSidebarCollapsed(true)
    }
    document.querySelector('.main-content')?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSidebarNavigate = (key: string, options?: { dateFilter?: DateFilter }) => {
    closeOverlays()
    if (key === 'opportunities') handleQuickStart('A', options?.dateFilter)
    if (key === 'growth') handleQuickStart('B')
    if (key === 'interview') handleQuickStart('C')
    if (key === 'resume') setResumeModalOpen(true)
    if (window.matchMedia('(max-width: 1024px)').matches) {
      setSidebarCollapsed(true)
    }
  }

  const toggleSidebar = () => {
    if (isMobileLayout) {
      setSidebarCollapsed(value => !value)
      return
    }

    setSidebarCompact(value => {
      const next = !value
      window.localStorage.setItem(SIDEBAR_COMPACT_STORAGE_KEY, String(next))
      return next
    })
  }

  return (
    <MotionConfig reducedMotion="user">
      <div className="app-shell arcade-shell noise">
      <div className="arcade-background" aria-hidden="true">
        <span className="maze-grid" />
        <span className="pellet-field" />
      </div>
      <StatusBar
        connectionStatus={connectionStatus}
        isConnected={isConnected}
        isStreaming={isStreaming}
        mode={session.mode}
        onGoHome={handleGoHome}
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

        <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''} ${sidebarCompact ? 'compact' : ''}`}>
          <ProfilePanel
            activeAgent={activeAgent}
            compact={sidebarCompact && !isMobileLayout}
            onStartProfile={() => handleQuickStart('Quero criar meu perfil profissional')}
            onNavigate={handleSidebarNavigate}
            onToggleCompact={toggleSidebar}
          />
        </div>

        <main className="main-content" aria-label="Conversa com o Maestro">
          <section className="workspace-header" aria-label="Contexto atual">
            <div className="workspace-title">
              {/* No desktop o toggle fica só dentro da sidebar (ProfilePanel).
                  No mobile, este botão é o único jeito de abrir o painel
                  off-canvas, então só aparece nessa largura. */}
              {isMobileLayout && (
                <button
                  className="icon-button"
                  type="button"
                  aria-expanded={!sidebarCollapsed}
                  aria-label={sidebarCollapsed ? 'Abrir painel de perfil' : 'Fechar painel de perfil'}
                  onClick={toggleSidebar}
                >
                  <PanelLeft size={18} />
                </button>
              )}

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
              <ApplicationPipeline
                mode={session.mode}
                onOpenResume={() => setResumeModalOpen(true)}
                onOpenJob={() => setJobAnalyzerOpen(true)}
                onOpenPdi={() => setPdiModalOpen(true)}
                onStartInterview={() => handleQuickStart('C')}
              />

              <Suspense fallback={<div className="loading-fallback">Preparando sua jornada...</div>}>
                <ChatTerminal
                  disabled={disabled}
                  scoutLoading={loadingState.scout}
                  isStreaming={isStreaming}
                  messages={messages}
                  mode={session.mode}
                  onQuickAction={handleQuickStart}
                />
              </Suspense>
              <ChatInput
                onSend={sendMessage}
                disabled={disabled}
                isStreaming={isStreaming}
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
          <section ref={resumeModalRef} className="resume-modal-panel">
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
            <ResumeUpload onContinueQuiz={handleContinueQuizAfterResume} />
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
          <section ref={jobAnalyzerModalRef} className="resume-modal-panel job-analyzer-modal">
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

      {pdiModalOpen && (
        <div className="resume-modal" role="dialog" aria-modal="true" aria-labelledby="pdi-modal-title">
          <button
            type="button"
            className="resume-modal-backdrop"
            aria-label="Fechar plano de desenvolvimento"
            onClick={() => setPdiModalOpen(false)}
          />
          <section ref={pdiModalRef} className="resume-modal-panel pdi-modal">
            <div className="resume-modal-header">
              <div>
                <p className="eyebrow"><Map size={13} aria-hidden="true" /> Desenvolvimento</p>
                <h2 id="pdi-modal-title">PDI personalizado para a vaga</h2>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Fechar plano de desenvolvimento"
                onClick={() => setPdiModalOpen(false)}
              >
                <X size={17} />
              </button>
            </div>
            <Suspense fallback={<div className="loading-fallback">Carregando PDI...</div>}>
              <PdiPlan />
            </Suspense>
          </section>
        </div>
      )}
      </div>
    </MotionConfig>
  )
}
