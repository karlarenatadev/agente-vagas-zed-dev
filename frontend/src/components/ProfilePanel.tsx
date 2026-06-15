import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Bookmark,
  Bot,
  BriefcaseBusiness,
  ChevronDown,
  Code2,
  Compass,
  FileText,
  GraduationCap,
  LayoutDashboard,
  MapPin,
  PanelLeftClose,
  PanelLeftOpen,
  Radio,
  Search,
  Sparkles,
  Target,
  UserRound,
  UserRoundCheck,
  Zap,
} from 'lucide-react'
import type { AgentName, DateFilter, UserProfile } from '../types'
import { FeedbackState } from './ui/FeedbackState'
import { SkillTag } from './ui/SkillTag'

interface Props {
  activeAgent: AgentName
  compact?: boolean
  onStartProfile?: () => void
  onNavigate: (key: string, options?: { dateFilter?: DateFilter }) => void
  onToggleCompact?: () => void
}

const DATE_FILTERS: Array<{ value: DateFilter; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7 dias' },
  { value: '1m', label: '1 mês' },
  { value: 'all', label: 'Todas' },
]

const LEVEL_PROGRESS: Record<string, number> = {
  'Júnior': 33,
  Pleno: 66,
  'Sênior': 100,
}

const AI_SQUAD = [
  {
    agent: 'Maestro',
    role: 'Orquestrador da jornada',
    icon: Bot,
    className: 'squad-maestro',
  },
  {
    agent: 'Scout',
    role: 'Radar de oportunidades',
    icon: Search,
    className: 'squad-scout',
  },
  {
    agent: 'Curator',
    role: 'Trilha de evolução',
    icon: GraduationCap,
    className: 'squad-curator',
  },
  {
    agent: 'Coach',
    role: 'Treino de entrevista',
    icon: UserRoundCheck,
    className: 'squad-coach',
  },
] satisfies Array<{
  agent: AgentName
  role: string
  icon: typeof Bot
  className: string
}>

const PRODUCT_NAV = [
  {
    key: 'dashboard',
    label: 'Painel',
    helper: 'visão geral',
    agent: 'Maestro',
    icon: LayoutDashboard,
    className: 'nav-maestro',
  },
  {
    key: 'opportunities',
    label: 'Oportunidades',
    helper: 'radar de vagas',
    agent: 'Scout',
    icon: Search,
    className: 'nav-scout',
  },
  {
    key: 'growth',
    label: 'Evolução',
    helper: 'lacunas e trilhas',
    agent: 'Curator',
    icon: GraduationCap,
    className: 'nav-curator',
  },
  {
    key: 'interview',
    label: 'Entrevista',
    helper: 'simulação guiada',
    agent: 'Coach',
    icon: UserRoundCheck,
    className: 'nav-coach',
  },
  {
    key: 'resume',
    label: 'Currículo',
    helper: 'análise de perfil',
    agent: 'Maestro',
    icon: FileText,
    className: 'nav-maestro',
  },
  {
    key: 'saved',
    label: 'Salvos',
    helper: 'em breve',
    agent: 'Maestro',
    icon: Bookmark,
    className: 'nav-disabled',
    disabled: true,
  },
] satisfies Array<{
  key: string
  label: string
  helper: string
  agent: AgentName
  icon: typeof Bot
  className: string
  disabled?: boolean
}>

function splitTags(value?: string): string[] {
  return value?.split(',').map(item => item.trim()).filter(Boolean) ?? []
}

function SkeletonLine({ width = '100%' }: { width?: string }) {
  return <div className="shimmer skeleton-line" style={{ width }} />
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Target
  label: string
  value?: string
}) {
  if (!value) return null

  return (
    <div className="profile-info-row">
      <Icon size={15} aria-hidden="true" />
      <span>
        <small>{label}</small>
        <strong>{value}</strong>
      </span>
    </div>
  )
}

function TagGroup({
  items,
  label,
  variant = 'default',
}: {
  items: string[]
  label: string
  variant?: 'default' | 'soft'
}) {
  if (items.length === 0) return null

  return (
    <section className="profile-section">
      <h3>{label}</h3>
      <div className="tag-list">
        {items.map((item, index) => (
          <motion.span
            key={`${label}-${item}`}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.025 }}
          >
            <SkillTag variant={variant === 'soft' ? 'partial' : 'safe'}>{item}</SkillTag>
          </motion.span>
        ))}
      </div>
    </section>
  )
}

function AISquad({ activeAgent }: { activeAgent: AgentName }) {
  return (
    <section className="profile-section ai-squad" aria-label="Agentes da jornada">
      <div className="squad-header">
        <h3>Squad de IA</h3>
        <span>missão ativa</span>
      </div>

      <div className="squad-list">
        {AI_SQUAD.map(item => {
          const Icon = item.icon
          const isActive = activeAgent === item.agent

          return (
            <div
              key={item.agent}
              className={`squad-agent ${item.className} ${isActive ? 'active' : ''}`}
              title={item.role}
              aria-current={isActive ? 'step' : undefined}
            >
              <span className="squad-agent-icon">
                <Icon size={15} aria-hidden="true" />
              </span>
              <span className="squad-agent-copy">
                <strong>{item.agent}</strong>
                <small>{isActive ? 'ativo' : 'standby'}</small>
              </span>
              <span className="squad-agent-status">
                <Radio size={12} aria-hidden="true" />
                {isActive ? 'ativo' : 'standby'}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function ProductNav({
  activeAgent,
  compact,
  onNavigate,
}: {
  activeAgent: AgentName
  compact: boolean
  onNavigate: (key: string, options?: { dateFilter?: DateFilter }) => void
}) {
  const [dateFilter, setDateFilter] = useState<DateFilter>('all')

  const activeKey = activeAgent === 'Scout'
    ? 'opportunities'
    : activeAgent === 'Curator'
      ? 'growth'
      : activeAgent === 'Coach'
        ? 'interview'
        : 'dashboard'

  const handleSelectPeriod = (value: DateFilter) => {
    setDateFilter(value)
    onNavigate('opportunities', { dateFilter: value })
  }

  return (
    <nav className="product-nav" aria-label="Navegação de carreira">
      <div className="product-nav-header">
        <span>Workspace</span>
        <small>Career Maze</small>
      </div>

      <div className="product-nav-list">
        {PRODUCT_NAV.map(item => {
          const Icon = item.icon
          const isActive = !item.disabled && activeKey === item.key

          if (item.disabled) {
            return (
              <span
                key={item.label}
                className={`product-nav-item ${item.className} ${isActive ? 'active' : ''} disabled`}
                aria-current={isActive ? 'page' : undefined}
                aria-disabled="true"
                title={compact ? item.label : undefined}
              >
                <Icon size={15} aria-hidden="true" />
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.helper}</small>
                </span>
              </span>
            )
          }

          return (
            <div key={item.label} className="product-nav-entry">
              <button
                type="button"
                className={`product-nav-item ${item.className} ${isActive ? 'active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
                aria-label={compact ? item.label : undefined}
                title={compact ? item.label : undefined}
                onClick={() => onNavigate(item.key)}
              >
                <Icon size={15} aria-hidden="true" />
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.helper}</small>
                </span>
              </button>

              {item.key === 'opportunities' && (
                <div className="nav-date-filter" role="group" aria-label="Período das vagas">
                  {DATE_FILTERS.map(filter => (
                    <button
                      type="button"
                      key={filter.value}
                      className={`date-filter-chip ${dateFilter === filter.value ? 'active' : ''}`}
                      aria-pressed={dateFilter === filter.value}
                      onClick={() => handleSelectPeriod(filter.value)}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </nav>
  )
}

export function ProfilePanel({
  activeAgent,
  compact = false,
  onStartProfile,
  onNavigate,
  onToggleCompact,
}: Props) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadProfile = useCallback(async (cancelled?: () => boolean) => {
    try {
      const response = await fetch('/api/profile/', {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        },
      })

      if (!response.ok) {
        throw new Error(`Falha HTTP ${response.status}`)
      }

      const data = await response.json() as {
        exists?: boolean
        data?: UserProfile
      }

      if (cancelled?.()) return
      setProfile(data.exists && data.data ? data.data : null)
    } catch (requestError) {
      console.error('Falha ao carregar perfil:', requestError)
      if (!cancelled?.()) {
        setError('Não foi possível carregar seu perfil agora.')
      }
    } finally {
      if (!cancelled?.()) setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const isCancelled = () => cancelled
    const handleProfileUpdated = () => {
      setLoading(true)
      setError('')
      void loadProfile()
    }

    const loadTimer = window.setTimeout(() => {
      void loadProfile(isCancelled)
    }, 0)
    window.addEventListener('profile-updated', handleProfileUpdated)

    return () => {
      cancelled = true
      window.clearTimeout(loadTimer)
      window.removeEventListener('profile-updated', handleProfileUpdated)
    }
  }, [loadProfile])

  const fields = useMemo(() => {
    const skills = splitTags(profile?.['Habilidades atuais'])
    const softSkills = splitTags(profile?.['Soft skills'])
    const targetRoles = splitTags(profile?.['Funções alvo'])
    const level = profile?.['Nível de experiência'] ?? ''

    return {
      area: profile?.['Área de interesse'],
      completed: profile?.['Concluído']?.toLowerCase() === 'true',
      location: profile?.['Localização'],
      objective: profile?.['Objetivo de carreira'],
      preference: profile?.['Preferências de trabalho'],
      level,
      progress: LEVEL_PROGRESS[level] ?? 0,
      skills,
      softSkills,
      targetRoles,
    }
  }, [profile])

  const hasProfileDraft = Boolean(profile)

  return (
    <aside className={`profile-panel ${compact ? 'compact' : ''}`} aria-label="Perfil profissional usado pela IA">
      <div className="sidebar-primary">
        <div className="profile-panel-header">
          <div>
            <p className="eyebrow">import vagas</p>
            <h2>Career Maze</h2>
          </div>
          {onToggleCompact && (
            <button
              type="button"
              className="sidebar-compact-toggle"
              onClick={onToggleCompact}
              aria-expanded={!compact}
              aria-label={compact ? 'Expandir menu' : 'Recolher menu'}
              title={compact ? 'Expandir menu' : 'Recolher menu'}
            >
              {compact
                ? <PanelLeftOpen size={17} aria-hidden="true" />
                : <PanelLeftClose size={17} aria-hidden="true" />}
            </button>
          )}
        </div>

        <ProductNav activeAgent={activeAgent} compact={compact} onNavigate={onNavigate} />
      </div>

      <div
        className="sidebar-secondary"
        tabIndex={0}
        aria-label="Resumo e detalhes do perfil profissional"
      >
        {compact && <AISquad activeAgent={activeAgent} />}
        {loading ? (
        <div className="profile-loading">
          <div className="shimmer profile-avatar-skeleton" />
          <SkeletonLine width="72%" />
          <SkeletonLine width="92%" />
          <SkeletonLine width="58%" />
        </div>
      ) : error && !hasProfileDraft ? (
        <div className="profile-empty">
          <FeedbackState
            tone="error"
            title={error}
            description="Confira se o backend está disponível e tente novamente."
          />
          <button
            type="button"
            className="primary-panel-button"
            onClick={() => {
              setLoading(true)
              setError('')
              void loadProfile()
            }}
          >
            Tentar novamente
          </button>
        </div>
      ) : !hasProfileDraft ? (
        <div className="profile-empty">
          <div className="empty-profile-icon" aria-hidden="true">
            <UserRound size={24} />
          </div>

          <h3>Seu diagnóstico ainda está incompleto</h3>
          <p>
            O diagnóstico cria a base que o Maestro usa para orientar vagas, evolução e entrevistas
            com mais contexto.
          </p>

          <button
            type="button"
            className="primary-panel-button"
            onClick={onStartProfile}
          >
            <Sparkles size={15} aria-hidden="true" />
            Iniciar diagnóstico
          </button>
        </div>
      ) : (
        <>
          {error && (
            <FeedbackState
              tone="error"
              title="O perfil salvo não pôde ser atualizado."
              description="Mantivemos os últimos dados carregados. Tente novamente quando a conexão voltar."
            />
          )}
          <section className="profile-summary">
            <div className="profile-avatar" aria-hidden="true">
              <BriefcaseBusiness size={24} />
            </div>

            <div>
              <p>{fields.area || 'Área a confirmar'}</p>
              <h3>{fields.level || 'Nível a confirmar'}</h3>
              <span>
                {fields.completed
                  ? [fields.location, fields.preference].filter(Boolean).join(' / ') || 'Local e modelo a confirmar'
                  : 'Rascunho do perfil'}
              </span>
            </div>
          </section>

          {!fields.completed && (
            <section className="profile-empty compact">
              <h3>Diagnóstico em rascunho</h3>
              <p>Confirme as informações para liberar recomendações mais precisas.</p>
              <button
                type="button"
                className="primary-panel-button"
                onClick={onStartProfile}
              >
                <Sparkles size={15} aria-hidden="true" />
                Continuar diagnóstico
              </button>
            </section>
          )}

          <section className="profile-progress" aria-label="Nível de experiência">
            <div>
              <span>Rota de carreira</span>
              <strong>{fields.progress}%</strong>
            </div>
            <div className="progress-track">
              <motion.div
                className="progress-fill"
                initial={{ width: 0 }}
                animate={{ width: `${fields.progress}%` }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
          </section>

          {!compact && <AISquad activeAgent={activeAgent} />}

          <details className="profile-details">
            <summary>
              <span>Detalhes do perfil</span>
              <ChevronDown size={15} aria-hidden="true" />
            </summary>

            <div className="profile-details-body">
              <section className="profile-info-card">
                <InfoRow icon={MapPin} label="Localização" value={fields.location} />
                <InfoRow icon={Compass} label="Objetivo" value={fields.objective} />
                <InfoRow icon={Zap} label="Modelo de trabalho" value={fields.preference} />
              </section>

              <TagGroup label="Habilidades técnicas" items={fields.skills} />
              <TagGroup label="Soft skills" items={fields.softSkills} variant="soft" />

              {fields.targetRoles.length > 0 && (
                <section className="profile-section">
                  <h3>Funções alvo</h3>
                  <div className="target-role-list">
                    {fields.targetRoles.map(role => (
                      <div key={role} className="target-role-item">
                        <Code2 size={14} aria-hidden="true" />
                        <span>{role}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </details>
        </>
        )}
      </div>
    </aside>
  )
}
