import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Scale,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
import type { ResumeMatchReport as ResumeMatchReportData } from '../types'
import { ResumeTailoringSuggestions } from './ResumeTailoringSuggestions'

interface Props {
  report: ResumeMatchReportData | null
  loading: boolean
  error: string
  onCompare: () => void
}

function TagGroup({
  title,
  items,
  variant,
}: {
  title: string
  items: string[]
  variant: 'strong' | 'partial' | 'missing'
}) {
  return (
    <section className={`match-tag-group ${variant}`}>
      <h4>{title}</h4>
      <div>
        {items.length
          ? items.map(item => <span key={`${title}-${item}`}>{item}</span>)
          : <small>Nenhum item</small>}
      </div>
    </section>
  )
}

function MatchList({
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
    <section className={`match-list ${critical ? 'critical' : ''}`}>
      <h4>{critical && <ShieldAlert size={14} aria-hidden="true" />}{title}</h4>
      <ul>
        {items.map(item => <li key={`${title}-${item}`}>{item}</li>)}
      </ul>
    </section>
  )
}

export function ResumeMatchReport({ report, loading, error, onCompare }: Props) {
  return (
    <section className="resume-match">
      <div className="resume-match-callout">
        <div>
          <p className="eyebrow"><Scale size={13} aria-hidden="true" /> Próxima etapa</p>
          <h3>Comparar vaga com meu currículo</h3>
          <p>
            O match usa apenas evidências presentes nas análises salvas. Ausências e indícios
            parciais nunca são tratados como experiência profissional.
          </p>
        </div>
        <button
          type="button"
          className="primary-action-button"
          onClick={onCompare}
          disabled={loading}
        >
          {loading
            ? <Loader2 size={16} className="spin" aria-hidden="true" />
            : <Scale size={16} aria-hidden="true" />}
          {loading ? 'Comparando...' : report ? 'Comparar novamente' : 'Comparar com meu currículo'}
        </button>
      </div>

      {error && (
        <div className="resume-upload-message error" role="alert">
          <AlertCircle size={15} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {report && (
        <div className="resume-match-result">
          <div className="match-score-card">
            <div
              className="match-score-ring"
              style={{ '--match-score': `${report.overall_score * 3.6}deg` } as React.CSSProperties}
              aria-label={`Score geral ${report.overall_score} de 100`}
            >
              <strong>{report.overall_score}</strong>
              <span>/100</span>
            </div>
            <div>
              <span>Nível de prontidão</span>
              <h3>{report.readiness_level}</h3>
              <p>{report.job_title}</p>
            </div>
          </div>

          <div className="match-breakdown">
            <span>Hard skills <strong>{report.score_breakdown.hard_skills}/45</strong></span>
            <span>Ferramentas <strong>{report.score_breakdown.tools}/20</strong></span>
            <span>Soft skills <strong>{report.score_breakdown.soft_skills}/15</strong></span>
            <span>Palavras-chave <strong>{report.score_breakdown.keywords}/10</strong></span>
            <span>Área e nível <strong>{report.score_breakdown.seniority_area}/10</strong></span>
          </div>

          <div className="match-evidence-grid">
            <TagGroup title="Evidência forte" items={report.strong_evidence} variant="strong" />
            <TagGroup title="Evidência parcial" items={report.partial_evidence} variant="partial" />
            <TagGroup title="Ausente" items={report.missing_requirements} variant="missing" />
          </div>

          <div className="match-detail-grid">
            <TagGroup title="Hard skills encontradas" items={report.hard_skills_found} variant="strong" />
            <TagGroup title="Hard skills ausentes" items={report.hard_skills_missing} variant="missing" />
            <TagGroup title="Soft skills encontradas" items={report.soft_skills_found} variant="strong" />
            <TagGroup title="Soft skills ausentes" items={report.soft_skills_missing} variant="missing" />
            <TagGroup title="Ferramentas encontradas" items={report.tools_found} variant="strong" />
            <TagGroup title="Ferramentas ausentes" items={report.tools_missing} variant="missing" />
            <TagGroup title="Palavras-chave encontradas" items={report.matched_keywords} variant="partial" />
            <TagGroup title="Palavras-chave ausentes" items={report.missing_keywords} variant="missing" />
          </div>

          <div className="job-analysis-grid">
            <MatchList title="Pontos fortes" items={report.strengths} />
            <MatchList title="Lacunas críticas" items={report.critical_gaps} critical />
            <MatchList title="Sugestões seguras" items={report.safe_resume_suggestions} />
            <MatchList title="Próximos passos" items={report.next_steps} />
          </div>

          <MatchList title="Não afirmar ainda" items={report.do_not_claim} critical />

          <div className="job-analysis-saved" role="status">
            <CheckCircle2 size={15} aria-hidden="true" />
            Relatório salvo em data/resume-match-report.md
          </div>

          <p className="match-future-note">
            <Sparkles size={14} aria-hidden="true" />
            Este relatório está pronto para alimentar sugestões de adaptação e o futuro PDI,
            sem editar o currículo nesta etapa.
          </p>

          <ResumeTailoringSuggestions />
        </div>
      )}
    </section>
  )
}

export default ResumeMatchReport
