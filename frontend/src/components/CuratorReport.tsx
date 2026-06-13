import { BookOpen, ExternalLink, FileCode2, GraduationCap, Lightbulb, Rocket, Target, Zap } from 'lucide-react'

interface Resource {
  kind: 'free' | 'paid' | 'reference' | 'quick'
  label: string
  name: string
  platform?: string
  link?: string
}

export interface CuratorSkill {
  habilidade: string
  prioridade?: string
  nivel_recomendado?: string
  por_que_importa?: string
  alinhamento_com_perfil?: string
  projeto_pratico?: string
  tempo_estimado_estudo?: string
  relacao_com_vagas?: string
  impacto_esperado_aderencia?: string
  resources: Resource[]
}

interface Bucket {
  label: string
  skills: CuratorSkill[]
}

export interface CuratorData {
  resumo: string
  buckets: Bucket[]
}

const RESOURCE_ICON = {
  free: GraduationCap,
  paid: BookOpen,
  reference: FileCode2,
  quick: Zap,
} as const

function priorityClass(priority?: string): string {
  if (!priority) return ''
  const normalized = priority.toLowerCase()
  if (normalized.startsWith('alta')) return 'priority-high'
  if (normalized.startsWith('m')) return 'priority-mid'
  return 'priority-low'
}

function isMeaningful(value?: string): boolean {
  if (!value) return false
  const trimmed = value.trim()
  return trimmed !== '' && trimmed !== '-' && !/^n[ãa]o\s/i.test(trimmed)
}

export function CuratorReport({ data }: { data: CuratorData }) {
  return (
    <div className="scout-report curator-report">
      {data.resumo && <p className="scout-summary">{data.resumo}</p>}

      {data.buckets.map((bucket) => (
        <div className="curator-bucket" key={bucket.label}>
          <span className="curator-bucket-label">{bucket.label}</span>

          <div className="scout-jobs">
            {bucket.skills.map((skill, index) => (
              <article className="scout-card curator-card" key={index}>
                <header className="scout-card-head">
                  <div className="scout-card-title">
                    <h4>{skill.habilidade}</h4>
                    {isMeaningful(skill.nivel_recomendado) && (
                      <span className="scout-company">
                        <Target size={12} aria-hidden="true" />
                        Nível alvo: {skill.nivel_recomendado}
                      </span>
                    )}
                  </div>
                  {isMeaningful(skill.prioridade) && (
                    <span className={`scout-priority ${priorityClass(skill.prioridade)}`}>
                      {skill.prioridade}
                    </span>
                  )}
                </header>

                {isMeaningful(skill.por_que_importa) && (
                  <p className="curator-why">{skill.por_que_importa}</p>
                )}

                {skill.resources.length > 0 && (
                  <div className="curator-resources">
                    {skill.resources.map((res, i) => {
                      const Icon = RESOURCE_ICON[res.kind]
                      return (
                        <div className={`curator-resource ${res.kind}`} key={i}>
                          <span className="curator-resource-icon"><Icon size={14} aria-hidden="true" /></span>
                          <span className="curator-resource-copy">
                            <small>{res.label}</small>
                            <strong>{res.name}</strong>
                            {isMeaningful(res.platform) && <em>{res.platform}</em>}
                          </span>
                          {isMeaningful(res.link) && (
                            <a className="curator-resource-link" href={res.link} target="_blank" rel="noopener noreferrer" aria-label={`Abrir ${res.name}`}>
                              <ExternalLink size={13} aria-hidden="true" />
                            </a>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}

                {isMeaningful(skill.projeto_pratico) && (
                  <p className="scout-tip curator-project">
                    <Rocket size={13} aria-hidden="true" />
                    <span><strong>Projeto prático:</strong> {skill.projeto_pratico}</span>
                  </p>
                )}

                <div className="scout-meta">
                  {isMeaningful(skill.tempo_estimado_estudo) && (
                    <span><Zap size={12} aria-hidden="true" />{skill.tempo_estimado_estudo}</span>
                  )}
                  {isMeaningful(skill.impacto_esperado_aderencia) && (
                    <span><Lightbulb size={12} aria-hidden="true" />{skill.impacto_esperado_aderencia}</span>
                  )}
                </div>

                {isMeaningful(skill.relacao_com_vagas) && (
                  <p className="curator-relation">{skill.relacao_com_vagas}</p>
                )}
              </article>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
