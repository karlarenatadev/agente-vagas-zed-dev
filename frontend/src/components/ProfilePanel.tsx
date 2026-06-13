import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Bookmark,
  Bot,
  BriefcaseBusiness,
  ChevronDown,
  ChevronLeft,
  Code2,
  Compass,
  FileText,
  GraduationCap,
  LayoutDashboard,
  MapPin,
  Radio,
  Search,
  Sparkles,
  Target,
  UserRound,
  UserRoundCheck,
  Zap,
} from 'lucide-react'
import type { AgentName, UserProfile } from '../types'

interface Props {
  activeAgent: AgentName
  onStartProfile?: () => void
  onToggleCollapse?: () => void
}

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
            className={`profile-tag ${variant}`}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.025 }}
          >
            {item}
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

function ProductNav({ activeAgent }: { activeAgent: AgentName }) {
  const activeKey = activeAgent === 'Scout'
    ? 'opportunities'
    : activeAgent === 'Curator'
      ? 'growth'
      : activeAgent === 'Coach'
        ? 'interview'
        : 'dashboard'

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

          return (
            <span
              key={item.label}
              className={`product-nav-item ${item.className} ${isActive ? 'active' : ''} ${item.disabled ? 'disabled' : ''}`}
              aria-current={isActive ? 'page' : undefined}
              aria-disabled={item.disabled ? 'true' : undefined}
            >
              <Icon size={15} aria-hidden="true" />
              <span>
                <strong>{item.label}</strong>
                <small>{item.helper}</small>
              </span>
            </span>
          )
        })}
      </div>
    </nav>
  )
}

export function ProfilePanel({ activeAgent, onStartProfile, onToggleCollapse }: Props) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const loadProfile = useCallback((cancelled?: () => boolean) => {
    fetch('/api/profile/', {
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache',
      },
    })
      .then(response => response.json())
      .then(data => {
        if (cancelled?.()) return
        setProfile(data.exists ? data.data : null)
      })
      .catch(error => {
        console.error('Falha ao carregar perfil:', error)
      })
      .finally(() => {
        if (!cancelled?.()) setLoading(false)
      })
  }, [])

  useEffect(() => {
    let cancelled = false
    const isCancelled = () => cancelled
    const handleProfileUpdated = () => {
      setLoading(true)
      loadProfile()
    }

    loadProfile(isCancelled)
    window.addEventListener('profile-updated', handleProfileUpdated)

    return () => {
      cancelled = true
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
    <aside className="profile-panel" aria-label="Perfil profissional usado pela IA">
      <div className="sidebar-primary">
        <div className="profile-panel-header">
          <div>
            <p className="eyebrow">import vagas</p>
            <h2>Career Maze</h2>
          </div>

          <button
            className="icon-button"
            type="button"
            aria-label="Recolher painel de perfil"
            onClick={onToggleCollapse}
          >
            <ChevronLeft size={17} />
          </button>
        </div>

        <ProductNav activeAgent={activeAgent} />
      </div>

      <div className="sidebar-secondary">
        {loading ? (
        <div className="profile-loading">
          <div className="shimmer profile-avatar-skeleton" />
          <SkeletonLine width="72%" />
          <SkeletonLine width="92%" />
          <SkeletonLine width="58%" />
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

          <AISquad activeAgent={activeAgent} />

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
