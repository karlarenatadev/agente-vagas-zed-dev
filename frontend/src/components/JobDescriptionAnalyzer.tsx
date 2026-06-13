import { useState } from 'react'
import { AlertCircle, BriefcaseBusiness, CheckCircle2, Loader2, Search } from 'lucide-react'
import type { JobDescriptionAnalysis } from '../types'

const MIN_DESCRIPTION_LENGTH = 40

function ResultList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null

  return (
    <section className="job-analysis-section">
      <h3>{title}</h3>
      <ul>
        {items.map(item => <li key={`${title}-${item}`}>{item}</li>)}
      </ul>
    </section>
  )
}

function JobAnalysisResult({ analysis }: { analysis: JobDescriptionAnalysis }) {
  return (
    <div className="job-analysis-result">
      <div className="job-analysis-summary">
        <div><span>Título</span><strong>{analysis.title}</strong></div>
        <div><span>Empresa</span><strong>{analysis.company}</strong></div>
        <div><span>Senioridade</span><strong>{analysis.seniority}</strong></div>
        <div><span>Modalidade</span><strong>{analysis.modality}</strong></div>
        <div><span>Localização</span><strong>{analysis.location}</strong></div>
      </div>

      {!!analysis.keywords.length && (
        <section className="job-analysis-section">
          <h3>Palavras-chave principais</h3>
          <div className="job-analysis-tags">
            {analysis.keywords.map(keyword => <span key={keyword}>{keyword}</span>)}
          </div>
        </section>
      )}

      {!!analysis.alerts.length && (
        <section className="job-analysis-alerts">
          <h3><AlertCircle size={15} aria-hidden="true" /> Alertas</h3>
          <ul>
            {analysis.alerts.map(alert => <li key={alert}>{alert}</li>)}
          </ul>
        </section>
      )}

      <div className="job-analysis-grid">
        <ResultList title="Hard skills" items={analysis.hard_skills} />
        <ResultList title="Soft skills" items={analysis.soft_skills} />
        <ResultList title="Ferramentas" items={analysis.tools} />
        <ResultList title="Responsabilidades" items={analysis.responsibilities} />
        <ResultList title="Requisitos obrigatórios" items={analysis.required_requirements} />
        <ResultList title="Requisitos desejáveis" items={analysis.nice_to_have} />
      </div>

      <ResultList title="Próximos passos sugeridos" items={analysis.next_steps} />
    </div>
  )
}

export function JobDescriptionAnalyzer() {
  const [description, setDescription] = useState('')
  const [analysis, setAnalysis] = useState<JobDescriptionAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyze = async () => {
    const cleanDescription = description.trim()
    if (cleanDescription.length < MIN_DESCRIPTION_LENGTH) {
      setError('Cole uma descrição de vaga com pelo menos 40 caracteres.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/job-description/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: cleanDescription }),
      })
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Não foi possível analisar a descrição.')
      }

      setAnalysis(data as JobDescriptionAnalysis)
    } catch (requestError) {
      console.error('Falha na análise da descrição da vaga:', requestError)
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível analisar a descrição da vaga.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="job-analyzer">
      <div className="job-analyzer-intro">
        <div className="resume-upload-icon" aria-hidden="true">
          <BriefcaseBusiness size={22} />
        </div>
        <div>
          <p>
            Cole o anúncio completo. A análise local identifica requisitos, ferramentas,
            responsabilidades e sinais de senioridade sem depender de API externa.
          </p>
        </div>
      </div>

      <label className="job-description-field">
        <span>Descrição da vaga</span>
        <textarea
          value={description}
          onChange={event => {
            setDescription(event.target.value)
            if (error) setError('')
          }}
          placeholder="Cole aqui o título, empresa, responsabilidades e requisitos da vaga..."
          rows={12}
          maxLength={50000}
          disabled={loading}
        />
        <small>{description.trim().length.toLocaleString('pt-BR')} caracteres</small>
      </label>

      {error && (
        <div className="resume-upload-message error" role="alert">
          <AlertCircle size={15} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {analysis && (
        <div className="job-analysis-saved" role="status">
          <CheckCircle2 size={15} aria-hidden="true" />
          Análise salva em data/job-description-analysis.md
        </div>
      )}

      <div className="job-analyzer-actions">
        <button
          type="button"
          className="primary-action-button"
          onClick={analyze}
          disabled={loading}
        >
          {loading
            ? <Loader2 size={16} className="spin" aria-hidden="true" />
            : <Search size={16} aria-hidden="true" />}
          {loading ? 'Analisando...' : 'Analisar descrição'}
        </button>
      </div>

      {analysis && <JobAnalysisResult analysis={analysis} />}
    </div>
  )
}

export default JobDescriptionAnalyzer
