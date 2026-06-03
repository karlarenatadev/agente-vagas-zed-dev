import { useState } from 'react'
import { Briefcase } from 'lucide-react'
import { motion } from 'framer-motion'

import { StatusBar }            from './components/StatusBar'
import { ProfilePanel }         from './components/ProfilePanel'
import { ChatTerminal }         from './components/ChatTerminal'
import { ChatInput }            from './components/ChatInput'
import { AgentBadge }           from './components/AgentBadge'
import { QuizPanel }            from './components/QuizPanel'
import { ApplicationTracker }   from './components/ApplicationTracker'
import { useWebSocket }         from './hooks/useWebSocket'

// Extrai a pergunta atual do último token de mensagem do agente
function extractCurrentQuestion(content: string): string {
  // Pega o texto após o último "Pergunta N/7:" ou usa o conteúdo completo
  const match = content.match(/\*\*Pergunta\s+\d+\/7:\*\*\s*([\s\S]+?)(?:\n\n|$)/)
  if (match) return match[1].trim()
  // Fallback: última linha não vazia
  const lines = content.split('\n').map(l => l.trim()).filter(Boolean)
  return lines[lines.length - 1] ?? content
}

export default function App() {
  const { messages, session, isConnected, isStreaming, sendMessage } = useWebSocket()
  const [trackerOpen, setTrackerOpen] = useState(false)

  const isQuiz = session.mode === 'quiz'

  // Pega a pergunta atual do último agente message
  const lastAgentMsg = [...messages].reverse().find(m => m.role === 'agent')
  const currentQuestion = lastAgentMsg ? extractCurrentQuestion(lastAgentMsg.content) : ''

  return (
    <div
      className="scanline noise"
      style={{
        display: 'flex', flexDirection: 'column',
        height: '100vh', width: '100vw',
        backgroundColor: 'var(--bg-void)',
        overflow: 'hidden',
      }}
    >
      {/* ── Topbar ── */}
      <StatusBar isConnected={isConnected} isStreaming={isStreaming} mode={session.mode} />

      {/* ── Layout principal ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Sidebar esquerda */}
        <ProfilePanel />

        {/* Área central */}
        <main style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden', minWidth: 0 }}>

          {/* ── Subheader ── */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0 20px',
            height: '44px',
            backgroundColor: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-subtle)',
            flexShrink: 0,
            gap: '12px',
          }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
              {isQuiz
                ? `quiz · pergunta ${session.quiz_step + 1} de 7`
                : session.mode === 'coach'
                ? `entrevista · pergunta ${session.coach_step} de 5`
                : session.mode === 'menu'
                ? 'pronto para receber comandos'
                : session.mode === 'init'
                ? 'inicializando...'
                : 'processando...'}
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AgentBadge mode={session.mode} isStreaming={isStreaming} />

              {/* Botão de candidaturas */}
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                onClick={() => setTrackerOpen(true)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  padding: '5px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-default)',
                  color: 'var(--text-secondary)',
                  fontSize: '12px', fontWeight: 500,
                  fontFamily: 'var(--font-sans)',
                  cursor: 'pointer',
                }}
              >
                <Briefcase size={13} />
                <span>Candidaturas</span>
              </motion.button>
            </div>
          </div>

          {/* ── Conteúdo principal: Quiz ou Chat ── */}
          {isQuiz ? (
            <QuizPanel
              step={session.quiz_step}
              question={currentQuestion}
              onAnswer={sendMessage}
              disabled={isStreaming || !isConnected}
            />
          ) : (
            <>
              <ChatTerminal messages={messages} isStreaming={isStreaming} />
              <ChatInput
                onSend={sendMessage}
                disabled={isStreaming || !isConnected}
                mode={session.mode}
              />
            </>
          )}
        </main>
      </div>

      {/* ── Tracker de candidaturas (drawer) ── */}
      <ApplicationTracker isOpen={trackerOpen} onClose={() => setTrackerOpen(false)} />
    </div>
  )
}
