import { Award, Briefcase, ExternalLink, Lightbulb, MapPin, Target, Wallet } from 'lucide-react'

interface Job {
  titulo?: string
  empresa?: string
  localizacao?: string
  salario?: string
  beneficios?: string
  link?: string
  score_aderencia?: string
  prioridade_candidatura?: string
  habilidades_correspondentes?: string
  soft_skills_correspondentes?: string
  habilidades_faltantes?: string
  contagem_correspondencia?: string
  dica_curriculo?: string
}

export interface ScoutData {
  resumo: string
  requisitos: { requisito: string; ocorrencias: string }[]
  vagas: Job[]
}

const NA = /^(n[ãa]o informad[oa]( na descri[çc][ãa]o)?|nenhum[a]?|-|)$/i

function isMeaningful(value?: string) {
  return !!value && !NA.test(value.trim())
}

function splitSkills(value?: string): string[] {
  if (!isMeaningful(value)) return []
  return value!
    .split(/[,;]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function scoreNumber(value?: string): number | null {
  if (!value) return null
  const match = value.match(/\d+/)
  return match ? Number(match[0]) : null
}

function scoreClass(score: number | null): string {
  if (score === null) return ''
  if (score >= 80) return 'score-high'
  if (score >= 50) return 'score-mid'
  return 'score-low'
}

function priorityClass(priority?: string): string {
  if (!priority) return ''
  const normalized = priority.toLowerCase()
  if (normalized.startsWith('alta')) return 'priority-high'
  if (normalized.startsWith('m')) return 'priority-mid'
  return 'priority-low'
}

export function ScoutReport({ data }: { data: ScoutData }) {
  return (
    <div className="scout-report">
      {data.resumo && <p className="scout-summary">{data.resumo}</p>}

      {data.requisitos.length > 0 && (
        <div className="scout-requirements">
          <span className="scout-requirements-label">Requisitos mais pedidos</span>
          <div className="scout-chips">
            {data.requisitos.map((req) => (
              <span key={req.requisito} className="scout-chip neutral">
                {req.requisito}
                {req.ocorrencias && req.ocorrencias !== '0' && (
                  <em>×{req.ocorrencias}</em>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="scout-jobs">
        {data.vagas.map((job, index) => {
          const score = scoreNumber(job.score_aderencia)
          const matched = splitSkills(job.habilidades_correspondentes)
          const soft = splitSkills(job.soft_skills_correspondentes)
          const missing = splitSkills(job.habilidades_faltantes)

          return (
            <article className="scout-card" key={index}>
              <header className="scout-card-head">
                <div className="scout-card-title">
                  <h4>{job.titulo || 'Vaga sem título'}</h4>
                  {isMeaningful(job.empresa) && (
                    <span className="scout-company">
                      <Briefcase size={12} aria-hidden="true" />
                      {job.empresa}
                    </span>
                  )}
                </div>
                {score !== null && (
                  <div className={`scout-score ${scoreClass(score)}`} title="Aderência ao seu perfil">
                    <Target size={13} aria-hidden="true" />
                    <strong>{score}</strong>
                    <small>/100</small>
                  </div>
                )}
              </header>

              <div className="scout-meta">
                {isMeaningful(job.localizacao) && (
                  <span><MapPin size={12} aria-hidden="true" />{job.localizacao}</span>
                )}
                {isMeaningful(job.salario) && (
                  <span><Wallet size={12} aria-hidden="true" />{job.salario}</span>
                )}
                {isMeaningful(job.prioridade_candidatura) && (
                  <span className={`scout-priority ${priorityClass(job.prioridade_candidatura)}`}>
                    <Award size={12} aria-hidden="true" />{job.prioridade_candidatura}
                  </span>
                )}
              </div>

              {(matched.length > 0 || soft.length > 0 || missing.length > 0) && (
                <div className="scout-skills">
                  {matched.map((skill) => (
                    <span key={`m-${skill}`} className="scout-chip match">{skill}</span>
                  ))}
                  {soft.map((skill) => (
                    <span key={`s-${skill}`} className="scout-chip soft">{skill}</span>
                  ))}
                  {missing.map((skill) => (
                    <span key={`x-${skill}`} className="scout-chip missing">{skill}</span>
                  ))}
                </div>
              )}

              {isMeaningful(job.dica_curriculo) && (
                <p className="scout-tip">
                  <Lightbulb size={13} aria-hidden="true" />
                  <span>{job.dica_curriculo}</span>
                </p>
              )}

              {isMeaningful(job.link) && (
                <a className="scout-link" href={job.link} target="_blank" rel="noopener noreferrer">
                  Ver vaga <ExternalLink size={13} aria-hidden="true" />
                </a>
              )}
            </article>
          )
        })}
      </div>
    </div>
  )
}
