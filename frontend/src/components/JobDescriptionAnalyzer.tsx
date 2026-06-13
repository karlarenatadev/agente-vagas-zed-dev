import { useState } from 'react'
import { BriefcaseBusiness, Loader2, Search } from 'lucide-react'
import type { JobDescriptionAnalysis, ResumeMatchReport as ResumeMatchReportData } from '../types'
import { ResumeMatchReport } from './ResumeMatchReport'
import { FeedbackState } from './ui/FeedbackState'
import { SectionCard } from './ui/SectionCard'
import { SkillTag } from './ui/SkillTag'

const MIN_DESCRIPTION_LENGTH = 40

function ResultList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null

  return (
    <SectionCard title={title}>
      <ul>
        {items.map(item => <li key={`${title}-${item}`}>{item}</li>)}
      </ul>
    </SectionCard>
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
        <SectionCard
          title="Palavras-chave principais"
          description="Termos que ajudam a entender o foco real da oportunidade."
        >
          <div className="job-analysis-tags">
            {analysis.keywords.map(keyword => (
              <SkillTag key={keyword} variant="partial">{keyword}</SkillTag>
            ))}
          </div>
        </SectionCard>
      )}

      {!!analysis.alerts.length && (
        <SectionCard
          title="Pontos de atenção"
          description="Sinais que merecem uma leitura cuidadosa antes da candidatura."
          variant="warning"
        >
          <ul>
            {analysis.alerts.map(alert => <li key={alert}>{alert}</li>)}
          </ul>
        </SectionCard>
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
  const [matchReport, setMatchReport] = useState<ResumeMatchReportData | null>(null)
  const [matchLoading, setMatchLoading] = useState(false)
  const [matchError, setMatchError] = useState('')

  const analyze = async () => {
    const cleanDescription = description.trim()
    if (cleanDescription.length < MIN_DESCRIPTION_LENGTH) {
      setError('Texto muito curto. Cole uma descrição mais completa da vaga para análise.')
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
      setMatchReport(null)
      setMatchError('')
      window.dispatchEvent(new Event('pipeline-updated'))
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

  const compareWithResume = async () => {
    setMatchLoading(true)
    setMatchError('')

    try {
      const response = await fetch('/api/resume-match/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_latest_job_analysis: true,
          use_latest_resume_analysis: true,
        }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Não foi possível comparar a vaga com o currículo.')
      }
      setMatchReport(data as ResumeMatchReportData)
      window.dispatchEvent(new Event('pipeline-updated'))
    } catch (requestError) {
      console.error('Falha na comparação da vaga com o currículo:', requestError)
      setMatchError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível comparar a vaga com o currículo.'
      )
    } finally {
      setMatchLoading(false)
    }
  }

  return (
    <div className="job-analyzer">
      <div className="job-analyzer-intro">
        <div className="resume-upload-icon" aria-hidden="true">
          <BriefcaseBusiness size={22} />
        </div>
        <div>
          <h3>Cole a descrição da vaga e descubra o que ela realmente está pedindo.</h3>
          <p>
            Vamos transformar o anúncio em requisitos, palavras-chave e próximos movimentos.
            A análise funciona localmente, mesmo sem uma API externa.
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
        <FeedbackState tone="error" title={error} description="Revise o texto e tente novamente." />
      )}

      {analysis && (
        <FeedbackState
          tone="success"
          title="Etapa concluída"
          description="A vaga foi mapeada. Agora você pode comparar com seu currículo."
        />
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
          {loading ? 'Lendo o mapa da vaga...' : 'Analisar descrição'}
        </button>
      </div>

      {loading && (
        <FeedbackState
          tone="loading"
          title="Lendo o mapa da vaga..."
          description="Identificando requisitos, ferramentas e sinais de senioridade."
        />
      )}

      {analysis && (
        <>
          <JobAnalysisResult analysis={analysis} />
          <ResumeMatchReport
            report={matchReport}
            loading={matchLoading}
            error={matchError}
            onCompare={compareWithResume}
          />
        </>
      )}
    </div>
  )
}

export default JobDescriptionAnalyzer
