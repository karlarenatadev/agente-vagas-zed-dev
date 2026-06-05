import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  BriefcaseBusiness,
  ChevronLeft,
  Code2,
  Compass,
  MapPin,
  Sparkles,
  Target,
  UserRound,
  Zap,
} from 'lucide-react'
import type { UserProfile } from '../types'

interface Props {
  onStartProfile?: () => void
  onToggleCollapse?: () => void
}

const LEVEL_PROGRESS: Record<string, number> = {
  'Júnior': 33,
  Pleno: 66,
  'Sênior': 100,
}

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

export function ProfilePanel({ onStartProfile, onToggleCollapse }: Props) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const loadProfile = useCallback((cancelled?: () => boolean) => {
    fetch('/api/profile/')
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
    const handleProfileUpdated = () => loadProfile()

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

  const hasUsableProfile = Boolean(profile && fields.completed)

  return (
    <aside className="profile-panel" aria-label="Perfil profissional usado pela IA">
      <div className="profile-panel-header">
        <div>
          <p className="eyebrow">Perfil profissional</p>
          <h2>Base usada pela IA</h2>
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

      {loading ? (
        <div className="profile-loading">
          <div className="shimmer profile-avatar-skeleton" />
          <SkeletonLine width="72%" />
          <SkeletonLine width="92%" />
          <SkeletonLine width="58%" />
        </div>
      ) : !hasUsableProfile ? (
        <div className="profile-empty">
          <div className="empty-profile-icon" aria-hidden="true">
            <UserRound size={24} />
          </div>

          <h3>Seu perfil ainda está incompleto</h3>
          <p>
            O quiz cria a base que o Maestro usa para orientar vagas, cursos e entrevistas
            com mais contexto.
          </p>

          <button
            type="button"
            className="primary-panel-button"
            onClick={onStartProfile}
          >
            <Sparkles size={15} aria-hidden="true" />
            Iniciar perfil
          </button>
        </div>
      ) : (
        <>
          <section className="profile-summary">
            <div className="profile-avatar" aria-hidden="true">
              <BriefcaseBusiness size={24} />
            </div>

            <div>
              <p>{fields.area}</p>
              <h3>{fields.level}</h3>
              <span>{fields.preference}</span>
            </div>
          </section>

          <section className="profile-progress" aria-label="Nível de experiência">
            <div>
              <span>Nível de experiência</span>
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
        </>
      )}
    </aside>
  )
}
