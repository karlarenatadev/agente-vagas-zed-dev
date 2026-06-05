import { useEffect, useRef, useState } from 'react'
import type {
  AgentName,
  ChatMessage,
  ConnectionStatus,
  LoadingState,
  SessionState,
  WsIncoming,
  WsOutgoing,
} from '../types'

const INTERNAL_AGENT_RUNNING = '__STATE__:agent_running:'

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

function generateId(): string {
  return Math.random().toString(36).slice(2, 10)
}

function getWebSocketUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/chat`
}

function agentFromSession(session: SessionState): AgentName {
  if (session.active_agent) return session.active_agent
  if (session.mode === 'scout') return 'Scout'
  if (session.mode === 'curator') return 'Curator'
  if (session.mode === 'coach') return 'Coach'
  return 'Maestro'
}

function loadingKeyToAgent(key: keyof LoadingState): AgentName {
  const map: Record<keyof LoadingState, AgentName> = {
    scout: 'Scout',
    curator: 'Curator',
    coach: 'Coach',
    maestro: 'Maestro',
  }

  return map[key]
}

export function useWebSocket() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [session, setSession] = useState<SessionState>(() => {
    const saved = localStorage.getItem('recoloca-session')
    return saved ? JSON.parse(saved) : INITIAL_SESSION
  })
  const [loadingState, setLoadingState] = useState<LoadingState>(INITIAL_LOADING)
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [activeAgent, setActiveAgent] = useState<AgentName>(() => agentFromSession(session))

  const wsRef = useRef<WebSocket | null>(null)
  const streamingIdRef = useRef<string | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const destroyedRef = useRef(false)
  const sessionRef = useRef(session)
  const hasConnectedRef = useRef(false)
  const activeAgentRef = useRef<AgentName>('Maestro')

  useEffect(() => {
    sessionRef.current = session
    activeAgentRef.current = agentFromSession(session)
  }, [session])

  useEffect(() => {
    localStorage.setItem('recoloca-session', JSON.stringify(session))
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

      const socket = new WebSocket(getWebSocketUrl())
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

        setIsConnected(false)
        setConnectionStatus(hasConnectedRef.current ? 'reconnecting' : 'offline')
        reconnectTimerRef.current = setTimeout(connect, 2000)
      }

      socket.onerror = () => {
        setIsConnected(false)
        setConnectionStatus(hasConnectedRef.current ? 'reconnecting' : 'offline')
      }

      socket.onmessage = (event) => {
        if (destroyedRef.current) return

        let data: WsIncoming
        try {
          data = JSON.parse(event.data)
        } catch (error) {
          console.error('Mensagem WebSocket inválida:', error)
          return
        }

        if (data.type === 'token') {
          const token = data.content as string

          if (token.startsWith(INTERNAL_AGENT_RUNNING)) {
            const key = token.replace(INTERNAL_AGENT_RUNNING, '').trim() as keyof LoadingState
            if (key in INITIAL_LOADING) {
              const agent = loadingKeyToAgent(key)
              activeAgentRef.current = agent
              setActiveAgent(agent)
              setLoadingState(prev => ({ ...prev, [key]: true }))
            }
            setIsStreaming(true)
            return
          }

          setMessages(prev => {
            const streamId = streamingIdRef.current

            if (!streamId) {
              const newId = generateId()
              streamingIdRef.current = newId

              return [
                ...prev,
                {
                  id: newId,
                  role: 'agent',
                  content: token,
                  agent: activeAgentRef.current,
                  timestamp: new Date(),
                  isStreaming: true,
                },
              ]
            }

            return prev.map(msg =>
              msg.id === streamId
                ? { ...msg, content: msg.content + token, agent: activeAgentRef.current }
                : msg
            )
          })

          setIsStreaming(true)
        }

        else if (data.type === 'state') {
          const nextSession = data.content as SessionState
          const nextAgent = agentFromSession(nextSession)

          activeAgentRef.current = nextAgent
          setActiveAgent(nextAgent)
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
          setMessages(prev => [
            ...prev,
            {
              id: generateId(),
              role: 'system',
              content: 'Não consegui completar a resposta agora. Verifique a conexão e tente novamente.',
              timestamp: new Date(),
            },
          ])
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
  }, [])

  function sendMessage(content: string) {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    if (isStreaming) return

    setMessages(prev => [
      ...prev,
      {
        id: generateId(),
        role: 'user',
        content,
        timestamp: new Date(),
      },
    ])

    const payload: WsOutgoing = {
      type: 'message',
      content,
      state: sessionRef.current,
    }

    wsRef.current.send(JSON.stringify(payload))
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
