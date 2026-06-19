import { useEffect, useState } from 'react'
import {
  CheckCircle2,
  Loader2,
  Scale,
  Sparkles,
} from 'lucide-react'
import { useScrollToResult } from '../hooks/useScrollToResult'
import { getFriendlyErrorMessage } from '../lib/errorMessages'
import type {
  ApplicationFocus,
  ReconciliationConflict,
  ReconciliationReport as ReconciliationReportData,
  ResumeMatchReport as ResumeMatchReportData,
} from '../types'
import { ResumeTailoringSuggestions } from './ResumeTailoringSuggestions'
import { FeedbackState } from './ui/FeedbackState'
import { GeneratedResultNotice } from './ui/GeneratedResultNotice'
import { SectionCard } from './ui/SectionCard'
import { SkillTag } from './ui/SkillTag'

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
    <SectionCard
      title={title}
      className={`match-tag-group ${variant}`}
      variant={variant === 'missing' ? 'danger' : variant === 'partial' ? 'warning' : 'success'}
    >
      <div>
        {items.length
          ? items.map(item => (
            <SkillTag key={`${title}-${item}`} variant={variant}>{item}</SkillTag>
          ))
          : <small>Nenhum item</small>}
      </div>
    </SectionCard>
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
    <SectionCard
      title={title}
      className={`match-list ${critical ? 'critical' : ''}`}
      variant={critical ? 'danger' : 'default'}
    >
      <ul>
        {items.map(item => <li key={`${title}-${item}`}>{item}</li>)}
      </ul>
    </SectionCard>
  )
}

function ConflictList({
  title,
  conflicts,
}: {
  title: string
  conflicts: ReconciliationConflict[]
}) {
  return (
    <SectionCard
      title={title}
      variant={conflicts.length ? 'danger' : 'success'}
    >
      {conflicts.length ? (
        <ul>
          {conflicts.map(conflict => (
            <li key={`${title}-${conflict.field}-${conflict.profile_value}-${conflict.other_value}`}>
              <strong>{conflict.field}:</strong> perfil "{conflict.profile_value}" vs outro "{conflict.other_value}"
              <small> Severidade: {conflict.severity}</small>
            </li>
          ))}
        </ul>
      ) : (
        <small>Nenhum conflito detectado</small>
      )}
    </SectionCard>
  )
}

function ReconciliationStep() {
  const [focus, setFocus] = useState<ApplicationFocus>('vaga')
  const [report, setReport] = useState<ReconciliationReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadLatest() {
      setInitialLoading(true)
      try {
        const response = await fetch('/api/reconciliation/latest', { cache: 'no-store' })
        if (response.status === 404) return
        const data = await response.json()
        if (!response.ok) {
          throw new Error(data.detail || 'Não foi possível carregar a reconciliação salva.')
        }
        if (active) {
          const latest = data as ReconciliationReportData
          setReport(latest)
          setFocus(latest.focus)
        }
      } catch (requestError) {
        if (active) {
          setError(getFriendlyErrorMessage(
            requestError,
            'Não foi possível carregar a reconciliação salva.'
          ))
        }
      } finally {
        if (active) setInitialLoading(false)
      }
    }

    void loadLatest()
    return () => {
      active = false
    }
  }, [])

  const analyze = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/reconciliation/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_latest_profile: true,
          use_latest_resume_analysis: true,
          use_latest_job_analysis: true,
          use_latest_match_report: true,
          focus,
        }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Não foi possível reconciliar perfil, currículo e vaga.')
      }
      setReport(data as ReconciliationReportData)
      window.dispatchEvent(new Event('pipeline-updated'))
    } catch (requestError) {
      console.error('Falha na reconciliação da candidatura:', requestError)
      setError(getFriendlyErrorMessage(
        requestError,
        'Não foi possível reconciliar perfil, currículo e vaga.'
      ))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="reconciliation-step">
      <div className="reconciliation-callout">
        <div>
          <p className="eyebrow"><Scale size={13} aria-hidden="true" /> Reconciliação</p>
          <h3>Escolher o foco da candidatura</h3>
          <p>
            Cruze perfil, currículo e vaga antes de adaptar sua apresentação. O foco define
            qual fonte deve prevalecer quando houver conflito.
          </p>
        </div>
        <div className="reconciliation-actions">
          <div className="focus-choice-group" aria-label="Foco da candidatura">
            {([
              ['vaga', 'Vaga'],
              ['curriculo', 'Currículo'],
              ['perfil', 'Perfil'],
            ] as const).map(([value, label]) => (
              <button
                type="button"
                key={value}
                className={focus === value ? 'selected' : ''}
                onClick={() => setFocus(value)}
                disabled={loading}
                aria-pressed={focus === value}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="primary-action-button"
            onClick={analyze}
            disabled={loading || initialLoading}
          >
            {loading
              ? <Loader2 size={16} className="spin" aria-hidden="true" />
              : <Scale size={16} aria-hidden="true" />}
            {loading ? 'Reconciliando...' : report ? 'Reconciliar novamente' : 'Reconciliar candidatura'}
          </button>
        </div>
      </div>

      {initialLoading && (
        <FeedbackState
          tone="loading"
          title="Buscando reconciliação salva..."
          description="Se não houver relatório salvo, você escolhe o foco e gera um novo."
        />
      )}

      {error && (
        <FeedbackState
          tone="error"
          title={error}
          description="Verifique se perfil, currículo, vaga e match já existem."
        />
      )}

      {report && (
        <div className="reconciliation-result generated-result" tabIndex={-1}>
          <GeneratedResultNotice
            title="Reconciliação concluída"
            nextStep="Próximo passo: gere sugestões seguras respeitando o foco escolhido."
          />

          <div className="reconciliation-summary">
            <div>
              <span>Consistência</span>
              <strong>{report.consistency_score}/100</strong>
            </div>
            <div>
              <span>Nível</span>
              <strong>{report.consistency_level}</strong>
            </div>
            <div>
              <span>Foco</span>
              <strong>{report.focus === 'curriculo' ? 'currículo' : report.focus}</strong>
            </div>
          </div>

          <div className="job-analysis-grid">
            <ConflictList title="Conflitos perfil x currículo" conflicts={report.profile_resume_conflicts} />
            <ConflictList title="Conflitos perfil x vaga" conflicts={report.profile_job_conflicts} />
          </div>

          <div className="job-analysis-grid">
            <MatchList title="Campos alinhados" items={report.aligned_fields} />
            <MatchList title="Recomendações pelo foco" items={report.focus_recommendations} />
            <MatchList title="Próximos passos" items={report.next_steps} />
          </div>

          <div className="job-analysis-saved" role="status">
            <CheckCircle2 size={15} aria-hidden="true" />
            Reconciliação salva em data/reconciliation.md
          </div>
        </div>
      )}

      {report && <ResumeTailoringSuggestions />}
    </section>
  )
}

export function ResumeMatchReport({ report, loading, error, onCompare }: Props) {
  const {
    reveal,
    targetRef,
  } = useScrollToResult<HTMLDivElement>()
  const {
    reveal: revealError,
    targetRef: errorRef,
  } = useScrollToResult<HTMLDivElement>()

  useEffect(() => {
    if (report) reveal()
  }, [report, reveal])

  useEffect(() => {
    if (error) revealError()
  }, [error, revealError])

  return (
    <section className="resume-match">
      <div className="resume-match-callout">
        <div>
          <p className="eyebrow"><Scale size={13} aria-hidden="true" /> Próxima etapa</p>
          <h3>Comparar vaga com meu currículo</h3>
          <p>
            Descubra o quanto seu currículo conversa com essa vaga. Só usamos evidências
            encontradas nos artefatos salvos.
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
        <div ref={errorRef} tabIndex={-1}>
          <FeedbackState
            tone="error"
            title={error}
            description="Antes de comparar, precisamos de currículo e vaga analisados."
          />
        </div>
      )}

      {loading && (
        <FeedbackState
          tone="loading"
          title="Cruzando as rotas..."
          description="Comparando evidências fortes, parciais e ausentes."
        />
      )}

      {!report && !loading && !error && (
        <FeedbackState
          tone="empty"
          title="Match aguardando currículo e vaga"
          description="Analise uma vaga e um currículo para liberar a comparação de aderência."
        />
      )}

      {report && (
        <div
          ref={targetRef}
          className="resume-match-result generated-result"
          tabIndex={-1}
        >
          <GeneratedResultNotice
            title="Relatório de aderência gerado"
            nextStep="Próximo passo: gere sugestões seguras para adaptar a apresentação do currículo."
          />
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
              <span>Score de aderência</span>
              <h3>{report.readiness_level}</h3>
              <p>O quanto seu currículo conversa com {report.job_title}.</p>
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
            <TagGroup title="Evidência forte: aparece claramente no currículo" items={report.strong_evidence} variant="strong" />
            <TagGroup title="Evidência parcial: existe indício" items={report.partial_evidence} variant="partial" />
            <TagGroup title="Ausente: falta evidência suficiente" items={report.missing_requirements} variant="missing" />
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

          <MatchList title="Não afirmar ainda: espere até ter evidência real" items={report.do_not_claim} critical />

          <div className="job-analysis-saved" role="status">
            <CheckCircle2 size={15} aria-hidden="true" />
            Relatório salvo em data/resume-match-report.md
          </div>

          <p className="match-future-note">
            <Sparkles size={14} aria-hidden="true" />
            Antes das sugestões, escolha se a candidatura deve priorizar a vaga,
            o currículo real ou o perfil declarado.
          </p>

          <ReconciliationStep />
        </div>
      )}
    </section>
  )
}

export default ResumeMatchReport
