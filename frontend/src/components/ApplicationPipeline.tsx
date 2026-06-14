import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  FileCheck2,
  FileText,
  Flag,
  Map,
  Scale,
  Sparkles,
  Target,
  UserRoundCheck,
} from 'lucide-react'
import type { PipelineStatus, SessionMode } from '../types'
import { StatusBadge } from './ui/StatusBadge'

interface Props {
  mode: SessionMode
  onOpenResume: () => void
  onOpenJob: () => void
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
  tailoring: boolean
  pdi: boolean
  failed: boolean
}

const RESUME_ANALYSIS_STORAGE_KEY = 'import-vagas:resume-analysis-complete'

const INVALID_MARKERS = [
  'nenhuma análise realizada',
  'nenhuma comparação realizada',
  'nenhuma sugestão gerada',
  'nenhum plano gerado',
  'não calculado',
  'aguardando análise válida',
]

function hasValidContent(data: DataFileResponse | null): boolean {
  if (!data?.exists || !data.content.trim()) return false
  const normalized = data.content.toLocaleLowerCase('pt-BR')
  return !INVALID_MARKERS.some(marker => normalized.includes(marker))
}

async function readDataFile(path: string): Promise<DataFileResponse> {
  const response = await fetch(path, { cache: 'no-store' })
  if (!response.ok) throw new Error('Não foi possível ler o progresso salvo.')
  return response.json() as Promise<DataFileResponse>
}

export function ApplicationPipeline({
  mode,
  onOpenResume,
  onOpenJob,
  onStartInterview,
}: Props) {
  const [snapshot, setSnapshot] = useState<PipelineSnapshot>({
    resume: false,
    job: false,
    match: false,
    tailoring: false,
    pdi: false,
    failed: false,
  })

  const refresh = useCallback(async () => {
    try {
      const [resumeAnalysis, job, match, tailoring, pdi] = await Promise.all([
        readDataFile('/api/data/resume-analysis'),
        readDataFile('/api/data/job-description'),
        readDataFile('/api/data/resume-match'),
        readDataFile('/api/data/resume-tailoring'),
        readDataFile('/api/data/pdi'),
      ])
      const matchCompleted = hasValidContent(match)
      const tailoringCompleted = hasValidContent(tailoring)
      
      // Prioriza arquivo real, fallback para localStorage, fallback para artefatos dependentes
      const resumeCompleted = hasValidContent(resumeAnalysis)
        || window.localStorage.getItem(RESUME_ANALYSIS_STORAGE_KEY) === 'true'
        || matchCompleted
        || tailoringCompleted

      if (resumeCompleted) {
        window.localStorage.setItem(RESUME_ANALYSIS_STORAGE_KEY, 'true')
      }

      setSnapshot({
        resume: resumeCompleted,
        job: hasValidContent(job),
        match: matchCompleted,
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
    const jobCompleted = snapshot.job || snapshot.match || snapshot.tailoring
    const matchCompleted = snapshot.match || snapshot.tailoring
    const tailoringCompleted = snapshot.tailoring
    const pdiCompleted = snapshot.pdi

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
        key: 'tailoring',
        label: 'Sugestões',
        description: 'Reposicione evidências sem inventar experiência.',
        next: tailoringCompleted
          ? 'Ajustes seguros disponíveis.'
          : matchCompleted
            ? 'Gere os ajustes no relatório.'
            : 'Conclua o match primeiro.',
        status: (tailoringCompleted ? 'completed' : matchCompleted ? 'available' : 'blocked') as PipelineStatus,
        icon: Sparkles,
        action: onOpenJob,
        actionLabel: tailoringCompleted ? 'Ver sugestões' : 'Abrir relatório',
      },
      {
        key: 'pdi',
        label: 'PDI',
        description: 'Transforme lacunas em um plano de evolução.',
        next: pdiCompleted ? 'Plano de evolução salvo.' : 'Fase futura da jornada.',
        status: (pdiCompleted ? 'completed' : 'pending') as PipelineStatus,
        icon: Map,
      },
      {
        key: 'interview',
        label: 'Entrevista',
        description: 'Treine respostas para a oportunidade.',
        next: mode === 'coach' ? 'Treino em andamento.' : 'Disponível no Coach.',
        status: (mode === 'coach' ? 'completed' : 'available') as PipelineStatus,
        icon: UserRoundCheck,
        action: onStartInterview,
        actionLabel: mode === 'coach' ? 'Continuar treino' : 'Treinar entrevista',
      },
    ]
  }, [mode, onOpenJob, onOpenResume, onStartInterview, snapshot])

  const currentIndex = steps.findIndex(step => step.status === 'available')
  const activeIndex = currentIndex === -1 ? steps.findIndex(step => step.status === 'pending') : currentIndex

  return (
    <section className="application-pipeline" aria-labelledby="pipeline-title">
      <header className="pipeline-header">
        <div>
          <p className="eyebrow">
            <Flag size={13} aria-hidden="true" />
            Career Arcade Pipeline
          </p>
          <h2 id="pipeline-title">Sua rota de candidatura</h2>
          <p>Avance uma etapa por vez. Cada ponto iluminado libera o próximo movimento.</p>
        </div>
        <span className="pipeline-progress-label">
          <FileCheck2 size={14} aria-hidden="true" />
          {steps.slice(0, 4).filter(step => step.status === 'completed').length} de 4 etapas-base concluídas
        </span>
      </header>

      {snapshot.failed && (
        <p className="pipeline-sync-note">
          O mapa não conseguiu sincronizar os arquivos agora. As ações continuam disponíveis.
        </p>
      )}

      <div className="pipeline-track">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isCurrent = index === activeIndex
          const isDisabled = !step.action || step.status === 'blocked' || step.status === 'pending'

          return (
            <article
              key={step.key}
              className={`pipeline-step ${step.status} ${isCurrent ? 'current' : ''}`}
              aria-current={isCurrent ? 'step' : undefined}
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
            </article>
          )
        })}
      </div>
    </section>
  )
}
