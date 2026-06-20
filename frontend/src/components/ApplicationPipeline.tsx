import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ChevronDown,
  FileCheck2,
  FileText,
  Flag,
  Map,
  Scale,
  Sparkles,
  Target,
  UserRoundCheck,
} from 'lucide-react'
import { apiRequest } from '../lib/api'
import type { PipelineStatus, SessionMode } from '../types'
import { StatusBadge } from './ui/StatusBadge'

interface Props {
  mode: SessionMode
  onOpenResume: () => void
  onOpenJob: () => void
  onOpenPdi: () => void
  onStartInterview: () => void
}

interface DataFileResponse {
  exists: boolean
  content: string
}

interface PipelineSnapshot {
  resume: boolean
  job: boolean
  match: boolean
  reconciliation: boolean
  tailoring: boolean
  pdi: boolean
  failed: boolean
}

const RESUME_ANALYSIS_STORAGE_KEY = 'import-vagas:resume-analysis-complete'
const PIPELINE_COLLAPSED_STORAGE_KEY = 'import-vagas:pipeline-collapsed'

const INVALID_MARKERS = [
  'não analisado',
  'nenhuma análise realizada',
  'nenhuma comparação realizada',
  'nenhuma sugestão gerada',
  'nenhum plano gerado',
  'não calculado',
  'aguardando análise válida',
]

function getStatusLabel(status: PipelineStatus): string {
  if (status === 'completed') return 'concluido'
  if (status === 'available') return 'disponivel agora'
  if (status === 'blocked') return 'bloqueado'
  return 'pendente'
}

function hasValidContent(data: DataFileResponse | null): boolean {
  if (!data?.exists || !data.content.trim()) return false
  const normalized = data.content.toLocaleLowerCase('pt-BR')
  return !INVALID_MARKERS.some(marker => normalized.includes(marker))
}

async function readDataFile(path: string): Promise<DataFileResponse> {
  return apiRequest<DataFileResponse>(path, { cache: 'no-store' })
}

export function ApplicationPipeline({
  mode,
  onOpenResume,
  onOpenJob,
  onOpenPdi,
  onStartInterview,
}: Props) {
  const [snapshot, setSnapshot] = useState<PipelineSnapshot>({
    resume: false,
    job: false,
    match: false,
    reconciliation: false,
    tailoring: false,
    pdi: false,
    failed: false,
  })

  const [collapsed, setCollapsed] = useState(() =>
    typeof window !== 'undefined'
      && window.localStorage.getItem(PIPELINE_COLLAPSED_STORAGE_KEY) === 'true'
  )

  const toggleCollapsed = useCallback(() => {
    setCollapsed(current => {
      const next = !current
      window.localStorage.setItem(PIPELINE_COLLAPSED_STORAGE_KEY, String(next))
      return next
    })
  }, [])

  const refresh = useCallback(async () => {
    try {
      const [resumeAnalysis, job, match, reconciliation, tailoring, pdi] = await Promise.all([
        readDataFile('/api/data/resume-analysis'),
        readDataFile('/api/data/job-description'),
        readDataFile('/api/data/resume-match'),
        readDataFile('/api/data/reconciliation'),
        readDataFile('/api/data/resume-tailoring'),
        readDataFile('/api/data/pdi'),
      ])
      const matchCompleted = hasValidContent(match)
      const reconciliationCompleted = hasValidContent(reconciliation)
      const tailoringCompleted = hasValidContent(tailoring)
      
      // A API é a fonte principal; artefatos dependentes preservam compatibilidade.
      const resumeCompleted = hasValidContent(resumeAnalysis)
        || matchCompleted
        || tailoringCompleted

      if (resumeCompleted) {
        window.localStorage.setItem(RESUME_ANALYSIS_STORAGE_KEY, 'true')
      } else {
        window.localStorage.removeItem(RESUME_ANALYSIS_STORAGE_KEY)
      }

      setSnapshot({
        resume: resumeCompleted,
        job: hasValidContent(job),
        match: matchCompleted,
        reconciliation: reconciliationCompleted,
        tailoring: tailoringCompleted,
        pdi: hasValidContent(pdi),
        failed: false,
      })
    } catch {
      setSnapshot(current => ({ ...current, failed: true }))
    }
  }, [])

  useEffect(() => {
    const initialRefresh = window.setTimeout(() => {
      void refresh()
    }, 0)
    window.addEventListener('pipeline-updated', refresh)
    window.addEventListener('profile-updated', refresh)
    return () => {
      window.clearTimeout(initialRefresh)
      window.removeEventListener('pipeline-updated', refresh)
      window.removeEventListener('profile-updated', refresh)
    }
  }, [refresh])

  const steps = useMemo(() => {
    const resumeCompleted = snapshot.resume
    const jobCompleted = snapshot.job || snapshot.match || snapshot.reconciliation || snapshot.tailoring
    const matchCompleted = snapshot.match || snapshot.reconciliation || snapshot.tailoring
    const reconciliationCompleted = snapshot.reconciliation || snapshot.tailoring
    const tailoringCompleted = snapshot.tailoring
    const pdiCompleted = snapshot.pdi
    const interviewCompleted = mode === 'coach'
    const interviewAvailable = pdiCompleted || interviewCompleted

    return [
      {
        key: 'resume',
        label: 'Currículo',
        description: 'Seu ponto de partida e suas evidências reais.',
        next: resumeCompleted ? 'Base pronta para o match.' : 'Envie ou revise seu currículo.',
        status: (resumeCompleted ? 'completed' : 'available') as PipelineStatus,
        icon: FileText,
        action: onOpenResume,
        actionLabel: resumeCompleted ? 'Revisar currículo' : 'Analisar currículo',
      },
      {
        key: 'job',
        label: 'Vaga',
        description: 'Transforme o anúncio em requisitos claros.',
        next: jobCompleted ? 'Mapa da vaga pronto.' : 'Cole a descrição da oportunidade.',
        status: (jobCompleted ? 'completed' : 'available') as PipelineStatus,
        icon: Target,
        action: onOpenJob,
        actionLabel: jobCompleted ? 'Revisar vaga' : 'Analisar vaga',
      },
      {
        key: 'match',
        label: 'Match',
        description: 'Veja onde currículo e vaga se encontram.',
        next: matchCompleted
          ? 'Aderência calculada.'
          : jobCompleted
            ? 'Compare dentro da análise da vaga.'
            : 'Analise uma vaga primeiro.',
        status: (matchCompleted ? 'completed' : jobCompleted ? 'available' : 'blocked') as PipelineStatus,
        icon: Scale,
        action: onOpenJob,
        actionLabel: matchCompleted ? 'Ver match' : 'Abrir vaga',
      },
      {
        key: 'reconciliation',
        label: 'Reconciliação',
        description: 'Escolha se perfil, currículo ou vaga manda quando houver conflito.',
        next: reconciliationCompleted
          ? 'Foco da candidatura definido.'
          : matchCompleted
            ? 'Escolha o foco dentro do relatório.'
            : 'Conclua o match primeiro.',
        status: (reconciliationCompleted ? 'completed' : matchCompleted ? 'available' : 'blocked') as PipelineStatus,
        icon: Scale,
        action: onOpenJob,
        actionLabel: reconciliationCompleted ? 'Ver foco' : 'Escolher foco',
      },
      {
        key: 'tailoring',
        label: 'Sugestões',
        description: 'Reposicione evidências sem inventar experiência.',
        next: tailoringCompleted
          ? 'Ajustes seguros disponíveis.'
          : reconciliationCompleted
            ? 'Gere os ajustes no relatório.'
            : 'Defina o foco da candidatura primeiro.',
        status: (tailoringCompleted ? 'completed' : reconciliationCompleted ? 'available' : 'blocked') as PipelineStatus,
        icon: Sparkles,
        action: onOpenJob,
        actionLabel: tailoringCompleted ? 'Ver sugestões' : 'Abrir relatório',
      },
      {
        key: 'pdi',
        label: 'PDI',
        description: 'Transforme lacunas em um plano de evolução.',
        next: pdiCompleted
          ? 'Plano de evolução salvo.'
          : tailoringCompleted
            ? 'Gere um plano de 7, 30 e 60 dias.'
            : 'Conclua as sugestões primeiro.',
        status: (pdiCompleted ? 'completed' : tailoringCompleted ? 'available' : 'blocked') as PipelineStatus,
        icon: Map,
        action: onOpenPdi,
        actionLabel: pdiCompleted ? 'Ver PDI' : 'Gerar PDI',
      },
      {
        key: 'interview',
        label: 'Entrevista',
        description: 'Treine respostas para a oportunidade.',
        next: interviewCompleted
          ? 'Treino em andamento.'
          : interviewAvailable
            ? 'PDI pronto. Agora treine respostas para a vaga.'
            : 'Gere o PDI antes de iniciar o treino.',
        status: (interviewCompleted ? 'completed' : interviewAvailable ? 'available' : 'blocked') as PipelineStatus,
        icon: UserRoundCheck,
        action: onStartInterview,
        actionLabel: interviewCompleted ? 'Continuar treino' : 'Treinar entrevista',
      },
    ]
  }, [mode, onOpenJob, onOpenPdi, onOpenResume, onStartInterview, snapshot])

  const currentIndex = steps.findIndex(step => step.status === 'available')
  const activeIndex = currentIndex === -1
    ? steps.findIndex(step => step.status === 'blocked')
    : currentIndex
  const completedCount = steps.filter(step => step.status === 'completed').length
  const recommendedStep = steps.find(step => step.status === 'available')
    ?? steps.find(step => step.status === 'blocked')
    ?? steps[steps.length - 1]

  return (
    <section
      className={`application-pipeline ${collapsed ? 'collapsed' : ''}`}
      aria-label="Rota de candidatura"
    >
      <header className="pipeline-header">
        <div className="pipeline-heading">
          <p className="eyebrow">
            <Flag size={13} aria-hidden="true" />
            Career Arcade Pipeline
          </p>
          <h2 id="pipeline-title">Sua rota de candidatura</h2>
          <p>Avance uma etapa por vez. Cada ponto iluminado libera o próximo movimento.</p>
        </div>

        {collapsed && (
          <div
            className="pipeline-minibar"
            role="list"
            aria-label={`Progresso da rota: ${completedCount} de ${steps.length} etapas concluidas. Proximo passo: ${recommendedStep.label}. ${recommendedStep.next}`}
          >
            {steps.map((step, index) => (
              <div
                className="minibar-segment"
                key={step.key}
                role="listitem"
                aria-label={`${step.label}: ${getStatusLabel(step.status)}. ${step.next}`}
              >
                <span
                  className={`minibar-node ${step.status} ${index === activeIndex ? 'current' : ''}`}
                  title={`${step.label} - ${getStatusLabel(step.status)}. ${step.next}`}
                />
                {index < steps.length - 1 && (
                  <span className={`minibar-link ${step.status === 'completed' ? 'filled' : ''}`} aria-hidden="true" />
                )}
              </div>
            ))}
          </div>
        )}

        <div className="pipeline-header-actions">
          <span className="pipeline-progress-label">
            <FileCheck2 size={14} aria-hidden="true" />
            {completedCount} de {steps.length} etapas concluídas
          </span>
          <button
            type="button"
            className="pipeline-toggle"
            onClick={toggleCollapsed}
            aria-expanded={!collapsed}
            aria-controls="pipeline-track"
            aria-label={collapsed ? 'Mostrar rota de candidatura' : 'Ocultar rota de candidatura'}
          >
            <ChevronDown
              size={18}
              className={`pipeline-chevron ${collapsed ? 'collapsed' : ''}`}
              aria-hidden="true"
            />
          </button>
        </div>
      </header>

      {!collapsed && (
        <p className="pipeline-next-step" role="status">
          <strong>Próximo passo recomendado:</strong> {recommendedStep.label} - {recommendedStep.next}
        </p>
      )}

      {!collapsed && snapshot.failed && (
        <p className="pipeline-sync-note">
          O mapa não conseguiu sincronizar os arquivos agora. As ações continuam disponíveis.
        </p>
      )}

      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            className="pipeline-track-wrap"
            key="pipeline-track-wrap"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{
              height: { duration: 0.4, ease: [0.22, 1, 0.36, 1] },
              opacity: { duration: 0.28, ease: 'easeOut' },
            }}
            style={{ overflow: 'hidden' }}
          >
            <div className="pipeline-track" id="pipeline-track">
              {steps.map((step, index) => {
                const Icon = step.icon
                const isCurrent = index === activeIndex
                const isDisabled = !step.action || step.status === 'blocked' || step.status === 'pending'

                return (
                  <motion.article
                    key={step.key}
                    className={`pipeline-step ${step.status} ${isCurrent ? 'current' : ''}`}
                    aria-current={isCurrent ? 'step' : undefined}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.06 + index * 0.05, duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <span className="pipeline-connector" aria-hidden="true" />
                    <span className="pipeline-node" aria-hidden="true">
                      <Icon size={17} />
                    </span>
                    <div className="pipeline-step-copy">
                      <div className="pipeline-step-title">
                        <small>Fase {String(index + 1).padStart(2, '0')}</small>
                        <StatusBadge status={step.status} />
                      </div>
                      <h3>{step.label}</h3>
                      <p>{step.description}</p>
                      <span>{step.next}</span>
                      {step.action && (
                        <button type="button" onClick={step.action} disabled={isDisabled}>
                          {step.actionLabel}
                        </button>
                      )}
                    </div>
                  </motion.article>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}
