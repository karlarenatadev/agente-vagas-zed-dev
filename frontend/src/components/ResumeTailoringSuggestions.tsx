import { useState } from 'react'
import {
  Check,
  FilePenLine,
  Loader2,
  Map,
} from 'lucide-react'
import type { ResumeTailoringSuggestions as TailoringData } from '../types'
import { CopyButton } from './ui/CopyButton'
import { FeedbackState } from './ui/FeedbackState'
import { SectionCard } from './ui/SectionCard'

function CopyableSection({
  title,
  items,
  critical = false,
}: {
  title: string
  items: string[]
  critical?: boolean
}) {
  if (!items.length) return null

  return (
    <SectionCard
      title={title}
      className={`tailoring-section ${critical ? 'critical' : ''}`}
      variant={critical ? 'danger' : 'default'}
      action={<CopyButton value={items.map(item => `- ${item}`).join('\n')} label={title} />}
    >
      <ul>
        {items.map(item => <li key={`${title}-${item}`}>{item}</li>)}
      </ul>
    </SectionCard>
  )
}

export function ResumeTailoringSuggestions() {
  const [data, setData] = useState<TailoringData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/resume-tailoring/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_latest_resume_analysis: true,
          use_latest_job_analysis: true,
          use_latest_match_report: true,
        }),
      })
      const result = await response.json()
      if (!response.ok) {
        throw new Error(result.detail || 'Não foi possível gerar as sugestões.')
      }
      setData(result as TailoringData)
      window.dispatchEvent(new Event('pipeline-updated'))
    } catch (requestError) {
      console.error('Falha ao gerar sugestões de currículo:', requestError)
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível gerar as sugestões de currículo.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="resume-tailoring">
      <div className="resume-tailoring-callout">
        <div>
          <p className="eyebrow"><FilePenLine size={13} aria-hidden="true" /> Currículo seguro</p>
          <h3>Sugerir ajustes no currículo</h3>
          <p>
            Melhore a forma de apresentar o que você já tem. Aqui não inventamos experiência:
            apenas reposicionamos evidências reais.
          </p>
        </div>
        <button
          type="button"
          className="primary-action-button"
          onClick={generate}
          disabled={loading}
        >
          {loading
            ? <Loader2 size={16} className="spin" aria-hidden="true" />
            : <FilePenLine size={16} aria-hidden="true" />}
          {loading ? 'Gerando...' : data ? 'Gerar novamente' : 'Sugerir ajustes no currículo'}
        </button>
      </div>

      {error && (
        <FeedbackState
          tone="error"
          title={error}
          description="Conclua o match antes de pedir os ajustes."
        />
      )}

      {loading && (
        <FeedbackState
          tone="loading"
          title="Organizando evidências..."
          description="Separando o que pode entrar, o que precisa de cuidado e o que ainda falta comprovar."
        />
      )}

      {data && (
        <div className="tailoring-result">
          <div className="tailoring-summary">
            <div><span>Vaga</span><strong>{data.job_title}</strong></div>
            <div><span>Score</span><strong>{data.match_score}/100</strong></div>
            <div><span>Prontidão</span><strong>{data.readiness_level}</strong></div>
          </div>

          <div className="tailoring-category-grid">
            <CopyableSection title="Pode destacar melhor" items={data.can_highlight_better} />
            <CopyableSection title="Pode reposicionar" items={data.can_reposition} />
            <CopyableSection title="Precisa criar evidência" items={data.needs_evidence} />
            <CopyableSection title="Não afirmar ainda" items={data.do_not_claim} critical />
          </div>

          <div className="tailoring-category-grid">
            <CopyableSection title="Resumo profissional" items={data.summary_suggestions} />
            <CopyableSection title="Seção de habilidades" items={data.skills_suggestions} />
            <CopyableSection title="Projetos" items={data.project_suggestions} />
            <CopyableSection title="Experiências" items={data.experience_suggestions} />
            <CopyableSection title="Palavras-chave seguras" items={data.keywords_to_include} />
            <CopyableSection title="Palavras-chave com cuidado" items={data.keywords_to_avoid_claiming} critical />
          </div>

          <CopyableSection title="Alertas de segurança" items={data.safety_alerts} critical />
          <CopyableSection title="Próximos passos" items={data.next_steps} />

          <div className="job-analysis-saved" role="status">
            <Check size={15} aria-hidden="true" />
            Sugestões salvas em data/resume-tailoring-suggestions.md
          </div>

          <div className="future-step-callout">
            <Map size={17} aria-hidden="true" />
            <span>
              <strong>Próximo movimento: PDI personalizado</strong>
              <small>Esta fase futura vai transformar as lacunas em um plano de evolução por vaga.</small>
            </span>
          </div>
        </div>
      )}
    </section>
  )
}

export default ResumeTailoringSuggestions
