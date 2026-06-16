import { useEffect, useState } from 'react'
import {
  CalendarRange,
  Check,
  Clipboard,
  Loader2,
  Target,
} from 'lucide-react'
import { useScrollToResult } from '../hooks/useScrollToResult'
import { getFriendlyErrorMessage } from '../lib/errorMessages'
import type { PdiPlan as PdiPlanData } from '../types'
import { FeedbackState } from './ui/FeedbackState'
import { GeneratedResultNotice } from './ui/GeneratedResultNotice'

async function copyText(value: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  textarea.remove()
}

function PdiSection({
  title,
  items,
  priority = false,
}: {
  title: string
  items: string[]
  priority?: boolean
}) {
  const [copied, setCopied] = useState(false)
  if (!items.length) return null

  const copy = async () => {
    try {
      await copyText(items.map(item => `- ${item}`).join('\n'))
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <section className={`pdi-section ${priority ? 'priority' : ''}`}>
      <div className="pdi-section-header">
        <h4>{title}</h4>
        <button type="button" onClick={copy} aria-label={`Copiar ${title}`}>
          {copied ? <Check size={13} /> : <Clipboard size={13} />}
          {copied ? 'Copiado' : 'Copiar'}
        </button>
      </div>
      <ul>
        {items.map(item => <li key={`${title}-${item}`}>{item}</li>)}
      </ul>
    </section>
  )
}

export function PdiPlan() {
  const [data, setData] = useState<PdiPlanData | null>(null)
  const [loadingSaved, setLoadingSaved] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [generatedNow, setGeneratedNow] = useState(false)
  const {
    reveal,
    targetRef,
  } = useScrollToResult<HTMLDivElement>()
  const {
    reveal: revealError,
    targetRef: errorRef,
  } = useScrollToResult<HTMLDivElement>()

  useEffect(() => {
    let active = true

    const loadSavedPlan = async () => {
      try {
        const response = await fetch('/api/pdi/latest', { cache: 'no-store' })
        if (response.status === 404) return

        const result = await response.json()
        if (!response.ok) {
          throw new Error(result.detail || 'Não foi possível carregar o PDI salvo.')
        }
        if (active) setData(result as PdiPlanData)
      } catch (requestError) {
        console.error('Falha ao carregar PDI:', requestError)
        if (active) {
          setError(getFriendlyErrorMessage(
            requestError,
            'Não foi possível carregar o PDI salvo.'
          ))
        }
      } finally {
        if (active) setLoadingSaved(false)
      }
    }

    void loadSavedPlan()
    return () => {
      active = false
    }
  }, [])

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/pdi/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_latest_resume_analysis: true,
          use_latest_job_analysis: true,
          use_latest_match_report: true,
          use_latest_tailoring_suggestions: true,
        }),
      })
      const result = await response.json()
      if (!response.ok) {
        throw new Error(result.detail || 'Não foi possível gerar o PDI.')
      }
      setData(result as PdiPlanData)
      setGeneratedNow(true)
      reveal()
      window.dispatchEvent(new Event('pipeline-updated'))
    } catch (requestError) {
      console.error('Falha ao gerar PDI:', requestError)
      setError(getFriendlyErrorMessage(
        requestError,
        'Não foi possível gerar o PDI.'
      ))
      revealError()
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="pdi-plan">
      <div className="pdi-callout">
        <div>
          <p className="eyebrow"><Target size={13} aria-hidden="true" /> Desenvolvimento</p>
          <h3>Gerar PDI para essa vaga</h3>
          <p>
            Transforma lacunas reais em tarefas de 7, 30 e 60 dias, projetos e evidências
            futuras. Estudo e projeto nunca são apresentados como experiência já adquirida.
          </p>
        </div>
        <button
          type="button"
          className="primary-action-button"
          onClick={generate}
          disabled={loading || loadingSaved}
        >
          {loading || loadingSaved
            ? <Loader2 size={16} className="spin" aria-hidden="true" />
            : <CalendarRange size={16} aria-hidden="true" />}
          {loading
            ? 'Gerando PDI...'
            : loadingSaved
              ? 'Carregando PDI...'
              : data
                ? 'Gerar novamente'
                : 'Gerar PDI para essa vaga'}
        </button>
      </div>

      {error && (
        <div
          ref={errorRef}
          tabIndex={-1}
        >
          <FeedbackState
            tone="error"
            title={error}
            description="Para gerar o PDI, conclua currículo, vaga, match e sugestões seguras. Se já fez isso, tente novamente em alguns instantes."
          />
        </div>
      )}

      {!loadingSaved && !loading && !error && !data && (
        <FeedbackState
          tone="empty"
          title="PDI aguardando pré-requisitos"
          description="Conclua as sugestões seguras da etapa anterior para liberar um plano de 7, 30 e 60 dias."
        />
      )}

      {data && (
        <div
          ref={targetRef}
          className="pdi-result generated-result"
          tabIndex={-1}
        >
          {generatedNow && (
            <GeneratedResultNotice
              title="Plano de desenvolvimento gerado"
              nextStep="Próximo passo: use o plano e avance para o treino de entrevista."
            />
          )}
          {!generatedNow && (
            <GeneratedResultNotice
              title="PDI salvo carregado"
              nextStep="Você pode revisar este plano ou gerar novamente depois de atualizar vaga, match ou sugestões."
            />
          )}
          <div className="pdi-summary">
            <div><span>Vaga</span><strong>{data.target_role}</strong></div>
            <div><span>Score atual</span><strong>{data.overall_score}/100</strong></div>
            <div><span>Prontidão</span><strong>{data.readiness_level}</strong></div>
          </div>

          <div className="pdi-main-goal">
            <Target size={17} aria-hidden="true" />
            <div><span>Objetivo principal</span><strong>{data.main_goal}</strong></div>
          </div>

          <PdiSection title="Lacunas prioritárias" items={data.priority_gaps} priority />
          <PdiSection title="Ganhos rápidos" items={data.quick_wins} />

          <div className="pdi-timeline">
            <PdiSection title="Plano de 7 dias" items={data.seven_day_plan} />
            <PdiSection title="Plano de 30 dias" items={data.thirty_day_plan} />
            <PdiSection title="Plano de 60 dias" items={data.sixty_day_plan} />
          </div>

          <div className="pdi-grid">
            <PdiSection title="Projetos práticos" items={data.portfolio_projects} />
            <PdiSection title="Evidências para criar" items={data.resume_evidence_to_create} />
            <PdiSection title="Estudos recomendados" items={data.study_resources} />
            <PdiSection title="Preparação para entrevista" items={data.interview_preparation} />
          </div>

          <PdiSection title="Próximos passos" items={data.next_steps} />

          <div className="job-analysis-saved" role="status">
            <Check size={15} aria-hidden="true" />
            PDI salvo em data/pdi-plan.md
          </div>
        </div>
      )}
    </section>
  )
}

export default PdiPlan
