/**
 * Hook WebSocket com reconexão segura.
 *
 * Correções aplicadas:
 * - Flag `destroyed` impede reconexão após unmount do componente
 * - `reconnectTimer` é limpo no cleanup para não vazar timers
 * - `connect` usa ref em vez de useCallback para evitar ciclo de deps no StrictMode
 */

import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, SessionState, WsIncoming, WsOutgoing } from '../types'

const WS_URL = 'ws://localhost:8000/ws/chat'

const INITIAL_SESSION: SessionState = {
  mode: 'init',
  quiz_step: 0,
  quiz_answers: {},
  coach_step: 0,
  interview_context: '',
}

function generateId(): string {
  return Math.random().toString(36).slice(2, 10)
}

export function useWebSocket() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [session, setSession] = useState<SessionState>(INITIAL_SESSION)
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)

  const wsRef             = useRef<WebSocket | null>(null)
  const streamingIdRef    = useRef<string | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const destroyedRef      = useRef(false)   // true após unmount — bloqueia reconexão
  const sessionRef        = useRef(session) // ref espelho para usar dentro de callbacks sem deps

  // Mantém sessionRef sincronizado
  useEffect(() => { sessionRef.current = session }, [session])

  // ── Conexão ────────────────────────────────────────────────────────────

  useEffect(() => {
    destroyedRef.current = false

    function connect() {
      // Não reconecta se o componente foi desmontado
      if (destroyedRef.current) return

      // Não abre nova conexão se já existe uma aberta ou abrindo
      const ws = wsRef.current
      if (ws) {
        if (ws.readyState === WebSocket.OPEN) return
        if (ws.readyState === WebSocket.CONNECTING) {
          // Fecha silenciosamente antes de recriar
          ws.onclose = null
          ws.onerror = null
          ws.close()
          wsRef.current = null
        }
      }

      const socket = new WebSocket(WS_URL)
      wsRef.current = socket

      socket.onopen = () => {
        if (destroyedRef.current) { socket.close(); return }
        setIsConnected(true)
      }

      socket.onclose = () => {
        if (destroyedRef.current) return   // componente desmontado — não reagenda
        setIsConnected(false)
        // Reagenda reconexão com backoff fixo de 2s
        reconnectTimerRef.current = setTimeout(connect, 2000)
      }

      socket.onerror = () => {
        // onerror sempre precede onclose — apenas marca offline
        setIsConnected(false)
      }

      socket.onmessage = (event) => {
        if (destroyedRef.current) return

        let data: WsIncoming
        try {
          data = JSON.parse(event.data)
        } catch {
          return
        }

        if (data.type === 'token') {
          const token = data.content as string

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
                  agent: 'Maestro',
                  timestamp: new Date(),
                  isStreaming: true,
                },
              ]
            }

            return prev.map(msg =>
              msg.id === streamId
                ? { ...msg, content: msg.content + token }
                : msg
            )
          })

          setIsStreaming(true)
        }

        else if (data.type === 'state') {
          setSession(data.content as SessionState)
        }

        else if (data.type === 'done') {
          // Fecha a mensagem em streaming atual e reseta o ID
          // para que a próxima resposta abra uma nova bolha
          const sid = streamingIdRef.current
          streamingIdRef.current = null
          if (sid) {
            setMessages(prev =>
              prev.map(msg => msg.id === sid ? { ...msg, isStreaming: false } : msg)
            )
          }
          setIsStreaming(false)
        }

        else if (data.type === 'error') {
          setMessages(prev => [
            ...prev,
            {
              id: generateId(),
              role: 'system',
              content: `⚠ Erro: ${data.content as string}`,
              timestamp: new Date(),
            },
          ])
          streamingIdRef.current = null
          setIsStreaming(false)
        }
      }
    }

    connect()

    // Cleanup: marca como destruído, cancela timer e fecha socket
    return () => {
      destroyedRef.current = true

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }

      if (wsRef.current) {
        wsRef.current.onclose = null  // remove handler antes de fechar para não disparar reconexão
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, []) // array vazio — roda só uma vez

  // ── Envio de mensagem ──────────────────────────────────────────────────

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

  return { messages, session, isConnected, isStreaming, sendMessage }
}
