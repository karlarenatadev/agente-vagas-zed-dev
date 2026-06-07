import { motion } from 'framer-motion'
import { AlertCircle, Bot, GraduationCap, Search, User, UserRoundCheck } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { AgentName, ChatMessage as ChatMessageType } from '../types'

interface Props {
  message: ChatMessageType
}

const AGENT_META = {
  Maestro: {
    label: 'Maestro',
    helper: 'orquestrador',
    className: 'message-agent-maestro',
    icon: Bot,
  },
  Scout: {
    label: 'Scout',
    helper: 'vagas',
    className: 'message-agent-scout',
    icon: Search,
  },
  Curator: {
    label: 'Curator',
    helper: 'aprendizado',
    className: 'message-agent-curator',
    icon: GraduationCap,
  },
  Coach: {
    label: 'Coach',
    helper: 'entrevista',
    className: 'message-agent-coach',
    icon: UserRoundCheck,
  },
} satisfies Record<AgentName, {
  label: string
  helper: string
  className: string
  icon: typeof Bot
}>

const CAREER_MENU_PATTERN = /(?:O que voc[eê] gostaria de fazer\??[\s\S]*?Digite\s+A,\s*B,\s*C\s+ou\s+D:?)|(?:A\s*[—-].*(?:Buscar|Encontrar).*[\s\S]*?B\s*[—-].*(?:curso|material|lacuna).*[\s\S]*?C\s*[—-].*(?:entrevista|Praticar).*[\s\S]*?D\s*[—-].*(?:quiz|diagn[oó]stico))/i

function getRenderableContent(content: string) {
  let visibleContent = content
  let previousContent = ''

  while (visibleContent !== previousContent) {
    previousContent = visibleContent
    visibleContent = visibleContent.replace(CAREER_MENU_PATTERN, '')
  }

  const hasCareerMenu = visibleContent !== content
  const cleanedContent = visibleContent
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  return {
    hasCareerMenu,
    visibleContent: cleanedContent,
  }
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const agent = message.agent ?? 'Maestro'
  const meta = AGENT_META[agent]
  const AgentIcon = meta.icon
  const { hasCareerMenu, visibleContent } = getRenderableContent(message.content)
  const hasStructuredCareerData = /score_aderencia|prioridade|habilidades_faltantes|curso_gratuito|projeto_pratico|pontuacao_final|nota_parcial/i
    .test(message.content)

  if (isSystem) {
    return (
      <motion.div
        className="message-row system"
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="system-message" role="status">
          <AlertCircle size={14} aria-hidden="true" />
          <span>{message.content}</span>
        </div>
      </motion.div>
    )
  }

  if (isUser) {
    return (
      <motion.div
        className="message-row user"
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.18 }}
      >
        <div className="message-bubble user-bubble">
          <div className="message-author user-author">
            <span>Você</span>
            <User size={13} aria-hidden="true" />
          </div>
          <p>{message.content}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      className={`message-row agent ${meta.className}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="message-avatar" aria-hidden="true">
        <AgentIcon size={17} />
      </div>

      <article className={`message-bubble agent-bubble ${hasStructuredCareerData ? 'structured-agent-bubble' : ''}`}>
        <div className="message-author">
          <div>
            <strong>{meta.label}</strong>
            <span>{meta.helper}</span>
          </div>
          <time dateTime={message.timestamp.toISOString()}>
            {message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </time>
        </div>

        <div className="prose-chat">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ children }) => <div className="table-scroll"><table>{children}</table></div>,
              a: ({ children, href }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            }}
          >
            {visibleContent || 'A esteira de carreira está pronta para a próxima ação.'}
          </ReactMarkdown>

          {hasCareerMenu && (
            <div className="compact-career-menu" role="note" aria-label="Menu de carreira compactado">
              <strong>Menu A/B/C/D compactado</strong>
              <span>Use a esteira visual de ações para escolher a próxima etapa.</span>
            </div>
          )}

          {message.isStreaming && (
            <span className="typing-indicator" aria-label="Resposta em andamento">
              <span />
              <span />
              <span />
            </span>
          )}
        </div>
      </article>
    </motion.div>
  )
}
