import { useCallback, useEffect, useRef, useState } from 'react'
import { getSessionId } from '../lib/session'
import type {
  AgentName,
  ChatMessage,
  ConnectionStatus,
  DateFilter,
  LoadingState,
  SessionState,
  WsDateFilter,
  WsIncoming,
  WsOutgoing,
} from '../types'

const INITIAL_SESSION: SessionState = {
  mode: 'init',
  quiz_step: 0,
  quiz_answers: {},
  coach_step: 0,
  interview_context: '',
}

const INITIAL_LOADING: LoadingState = {
  scout: false,
  curator: false,
  coach: false,
  maestro: false,
}

const SEND_INTERRUPTED_MESSAGE =
  'Não foi possível enviar agora porque a conexão foi interrompida. Aguarde reconectar e tente novamente.'
const EMPTY_MESSAGE = 'Digite uma mensagem antes de enviar.'

function generateId(): string {
  return Math.random().toString(36).slice(2, 10)
}

function getWebSocketUrl(replay: boolean): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const sessionId = encodeURIComponent(getSessionId())
  // replay=1 só na 1ª conexão do tab (reload): pede ao backend para repintar o
  // prompt atual da sessão restaurada. Em reconexões transitórias o param fica
  // de fora, então a reconexão não é exposta nem o prompt é duplicado.
  const replayParam = replay ? '&replay=1' : ''
  return `${protocol}//${window.location.host}/ws/chat?session_id=${sessionId}${replayParam}`
}

function agentFromSession(session: SessionState): AgentName {
  if (session.active_agent) return session.active_agent
  if (session.mode === 'scout') return 'Scout'
  if (session.mode === 'curator') return 'Curator'
  if (session.mode === 'coach') return 'Coach'
  return 'Maestro'
}

function loadingFromSession(session: SessionState): LoadingState {
  if (session.mode !== 'agent_running' || !session.active_agent) {
    return INITIAL_LOADING
  }

  const key = session.active_agent.toLowerCase() as keyof LoadingState
  if (!(key in INITIAL_LOADING)) {
    return INITIAL_LOADING
  }

  return { ...INITIAL_LOADING, [key]: true }
}

function isSessionState(value: unknown): value is SessionState {
  if (!value || typeof value !== 'object') return false
  const state = value as Record<string, unknown>
  return (
    typeof state.mode === 'string'
    && typeof state.quiz_step === 'number'
    && typeof state.quiz_answers === 'object'
    && state.quiz_answers !== null
    && typeof state.coach_step === 'number'
    && typeof state.interview_context === 'string'
  )
}

function isWsIncoming(value: unknown): value is WsIncoming {
  if (!value || typeof value !== 'object') return false
  const message = value as Record<string, unknown>

  if (message.type === 'state') {
    return isSessionState(message.content)
  }

  return (
    ['token', 'done', 'error'].includes(String(message.type))
    && typeof message.content === 'string'
  )
}

function isWsDateFilter(value: DateFilter): value is WsDateFilter {
  return value !== 'all'
}

export function useWebSocket() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [session, setSession] = useState<SessionState>(INITIAL_SESSION)
  const [loadingState, setLoadingState] = useState<LoadingState>(INITIAL_LOADING)
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [activeAgent, setActiveAgent] = useState<AgentName>(() => agentFromSession(session))

  const wsRef = useRef<WebSocket | null>(null)
  const streamingIdRef = useRef<string | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const destroyedRef = useRef(false)
  const hasConnectedRef = useRef(false)
  const activeAgentRef = useRef<AgentName>('Maestro')

  const addSystemMessage = useCallback((content: string) => {
    setMessages(prev => [
      ...prev,
      {
        id: generateId(),
        role: 'system',
        content,
        timestamp: new Date(),
      },
    ])
  }, [])

  useEffect(() => {
    activeAgentRef.current = agentFromSession(session)
  }, [session])

  useEffect(() => {
    destroyedRef.current = false

    function connect() {
      if (destroyedRef.current) return

      const ws = wsRef.current
      if (ws) {
        if (ws.readyState === WebSocket.OPEN) return
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onclose = null
          ws.onerror = null
          ws.close()
          wsRef.current = null
        }
      }

      setConnectionStatus(hasConnectedRef.current ? 'reconnecting' : 'connecting')

      // Pede replay do prompt atual só na 1ª conexão (reload), nunca em
      // reconexões transitórias — assim a reconexão não é exposta ao usuário.
      const socket = new WebSocket(getWebSocketUrl(!hasConnectedRef.current))
      wsRef.current = socket

      socket.onopen = () => {
        if (destroyedRef.current) {
          socket.close()
          return
        }

        hasConnectedRef.current = true
        setIsConnected(true)
        setConnectionStatus('connected')
      }

      socket.onclose = () => {
        if (destroyedRef.current) return

        const interruptedStreamId = streamingIdRef.current
        streamingIdRef.current = null
        if (interruptedStreamId) {
          setMessages(prev =>
            prev.map(message =>
              message.id === interruptedStreamId
                ? { ...message, isStreaming: false }
                : message
            )
          )
        }
        setIsConnected(false)
        setIsStreaming(false)
        setLoadingState(INITIAL_LOADING)
        setConnectionStatus(hasConnectedRef.current ? 'reconnecting' : 'offline')
        reconnectTimerRef.current = setTimeout(connect, 2000)
      }

      socket.onerror = () => {
        setIsConnected(false)
        setConnectionStatus(hasConnectedRef.current ? 'reconnecting' : 'offline')
      }

      socket.onmessage = (event) => {
        if (destroyedRef.current) return

        let parsed: unknown
        try {
          parsed = JSON.parse(event.data)
        } catch (error) {
          console.error('Mensagem WebSocket inválida:', error)
          return
        }
        if (!isWsIncoming(parsed)) {
          console.error('Mensagem WebSocket fora do contrato.')
          return
        }
        const data = parsed

        if (data.type === 'token') {
          const token = data.content
          setIsStreaming(true)

          // A mutação do ref fica FORA do updater do setMessages: no modo
          // concorrente do React o updater pode ser chamado e descartado mais
          // de uma vez, e setar o ref ali dentro fazia tokens irem para uma
          // bolha errada (resposta aparecia acima da mensagem do usuário).
          const agent = activeAgentRef.current
          const streamId = streamingIdRef.current

          if (!streamId) {
            const newId = generateId()
            streamingIdRef.current = newId
            setMessages(prev => [
              ...prev,
              {
                id: newId,
                role: 'agent',
                content: token,
                agent,
                timestamp: new Date(),
                isStreaming: true,
              },
            ])
          } else {
            setMessages(prev =>
              prev.map(msg =>
                msg.id === streamId
                  ? { ...msg, content: msg.content + token, agent }
                  : msg
              )
            )
          }
        }

        else if (data.type === 'state') {
          const nextSession = data.content
          const nextAgent = agentFromSession(nextSession)

          activeAgentRef.current = nextAgent
          setActiveAgent(nextAgent)
          setLoadingState(loadingFromSession(nextSession))
          setSession(nextSession)
        }

        else if (data.type === 'done') {
          const sid = streamingIdRef.current
          streamingIdRef.current = null

          if (sid) {
            setMessages(prev =>
              prev.map(msg => msg.id === sid ? { ...msg, isStreaming: false } : msg)
            )
          }

          setLoadingState(INITIAL_LOADING)
          setIsStreaming(false)
          window.dispatchEvent(new Event('profile-updated'))
        }

        else if (data.type === 'error') {
          console.error('Erro recebido do WebSocket:', data.content)
          addSystemMessage(
            data.content.trim()
            || 'Não consegui completar a resposta agora. Verifique a conexão e tente novamente.'
          )
          streamingIdRef.current = null
          setLoadingState(INITIAL_LOADING)
          setIsStreaming(false)
        }
      }
    }

    connect()

    return () => {
      destroyedRef.current = true

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }

      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [addSystemMessage])

  function sendMessage(content: string, dateFilter?: DateFilter): boolean {
    const normalizedContent = typeof content === 'string' ? content.trim() : ''
    if (!normalizedContent) {
      addSystemMessage(EMPTY_MESSAGE)
      return false
    }

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addSystemMessage(SEND_INTERRUPTED_MESSAGE)
      setLoadingState(INITIAL_LOADING)
      setIsStreaming(false)
      return false
    }
    if (isStreaming) return false

    // Nova mensagem do usuário → a próxima resposta deve abrir uma bolha nova
    // logo abaixo, nunca anexar à resposta anterior.
    streamingIdRef.current = null

    setMessages(prev => [
      ...prev,
      {
        id: generateId(),
        role: 'user',
        content: normalizedContent,
        timestamp: new Date(),
      },
    ])

    const payload: WsOutgoing = {
      type: 'message',
      content: normalizedContent,
    }
    // Só envia o filtro quando há recorte de data (todas = sem filtro).
    if (dateFilter && isWsDateFilter(dateFilter)) {
      payload.date_filter = dateFilter
    }

    wsRef.current.send(JSON.stringify(payload))
    return true
  }

  return {
    messages,
    session,
    isConnected,
    isStreaming,
    loadingState,
    connectionStatus,
    activeAgent,
    sendMessage,
  }
}
