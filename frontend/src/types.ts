// ── Tipos do sistema import vagas ────────────────────────────────────

export type AgentName = 'Maestro' | 'Scout' | 'Curator' | 'Coach'

export type SessionMode =
  | 'init'
  | 'quiz'
  | 'quiz_resume'
  | 'menu'
  | 'scout'
  | 'curator'
  | 'coach'
  | 'agent_running'

export interface SessionState {
  mode: SessionMode
  quiz_step: number
  quiz_answers: Record<string, string>
  coach_step: number
  interview_context: string
  active_agent?: AgentName
}

export type MessageRole = 'user' | 'agent' | 'system'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  agent?: AgentName
  timestamp: Date
  isStreaming?: boolean
}

export interface UserProfile {
  'Área de interesse'?: string
  'Nível de experiência'?: string
  'Preferências de trabalho'?: string
  'Localização'?: string
  'Soft skills'?: string
  'Objetivo de carreira'?: string
  'Habilidades atuais'?: string
  'Funções alvo'?: string
  'Concluído'?: string
}

// ── Tracker de candidaturas ───────────────────────────────────────────

export type ApplicationStatus =
  | 'salva'
  | 'aplicada'
  | 'em_processo'
  | 'entrevista'
  | 'oferta'
  | 'recusada'
  | 'desistiu'

export interface JobApplication {
  id: string
  titulo: string
  empresa: string
  localizacao: string
  link: string
  salario?: string
  habilidades_correspondentes?: string
  habilidades_faltantes?: string
  contagem_correspondencia?: string
  status: ApplicationStatus
  data_salva: string        // ISO date
  data_aplicacao?: string   // ISO date
  notas?: string
}

// ── WebSocket ─────────────────────────────────────────────────────────

export type WsMessageType = 'token' | 'state' | 'done' | 'error'

export interface WsIncoming {
  type: WsMessageType
  content: string | SessionState
}

export interface WsOutgoing {
  type: 'message'
  content: string
  state: SessionState
}
