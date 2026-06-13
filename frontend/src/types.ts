// Tipos do sistema import vagas

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
  loading?: LoadingState
}

export type MessageRole = 'user' | 'agent' | 'system'

export interface LoadingState {
  scout: boolean
  curator: boolean
  coach: boolean
  maestro: boolean
}

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

export interface ResumeAnalysis {
  detected_name: string
  professional_summary: string
  probable_areas: string[]
  estimated_level: string
  technical_skills: string[]
  soft_skills: string[]
  experience_summary: string
  education_summary: string
  suggested_target_roles: string[]
  strengths: string[]
  improvement_points: string[]
  fields_to_confirm: string[]
}

export interface ResumeUploadResponse {
  success: boolean
  message: string
  analysis?: ResumeAnalysis
  profile_updated?: boolean
}

export interface JobDescriptionAnalysis {
  title: string
  company: string
  seniority: string
  modality: string
  location: string
  keywords: string[]
  hard_skills: string[]
  soft_skills: string[]
  tools: string[]
  responsibilities: string[]
  required_requirements: string[]
  nice_to_have: string[]
  alerts: string[]
  next_steps: string[]
}

export interface ResumeMatchReport {
  overall_score: number
  readiness_level: string
  job_title: string
  resume_summary: string
  score_breakdown: {
    hard_skills: number
    tools: number
    soft_skills: number
    keywords: number
    seniority_area: number
  }
  strong_evidence: string[]
  partial_evidence: string[]
  missing_requirements: string[]
  hard_skills_found: string[]
  hard_skills_missing: string[]
  soft_skills_found: string[]
  soft_skills_missing: string[]
  tools_found: string[]
  tools_missing: string[]
  matched_keywords: string[]
  missing_keywords: string[]
  strengths: string[]
  critical_gaps: string[]
  safe_resume_suggestions: string[]
  do_not_claim: string[]
  next_steps: string[]
}

export interface ResumeTailoringSuggestions {
  job_title: string
  match_score: number
  readiness_level: string
  summary_suggestions: string[]
  skills_suggestions: string[]
  project_suggestions: string[]
  experience_suggestions: string[]
  keywords_to_include: string[]
  keywords_to_avoid_claiming: string[]
  can_highlight_better: string[]
  can_reposition: string[]
  needs_evidence: string[]
  do_not_claim: string[]
  safety_alerts: string[]
  next_steps: string[]
}

export interface PdiPlan {
  target_role: string
  overall_score: number
  readiness_level: string
  main_goal: string
  priority_gaps: string[]
  quick_wins: string[]
  seven_day_plan: string[]
  thirty_day_plan: string[]
  sixty_day_plan: string[]
  portfolio_projects: string[]
  resume_evidence_to_create: string[]
  study_resources: string[]
  interview_preparation: string[]
  next_steps: string[]
}

// Tracker de candidaturas

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
  data_salva: string
  data_aplicacao?: string
  notas?: string
}

// WebSocket

export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'offline'

export type PipelineStatus =
  | 'completed'
  | 'available'
  | 'pending'
  | 'blocked'
  | 'error'

export type WsMessageType = 'token' | 'state' | 'done' | 'error'

export interface WsIncoming {
  type: WsMessageType
  content: string | SessionState
}

export interface WsOutgoing {
  type: 'message'
  content: string
}
