import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import type { UserProfile } from '../types'

const LEVEL_XP: Record<string, number> = { 'Júnior': 33, 'Pleno': 66, 'Sênior': 100 }

const AREA_ICONS: Record<string, string> = {
  'Ciência de Dados': '📊',
  'Frontend': '🎨',
  'Backend': '⚙️',
  'Full Stack': '🔧',
  'DevOps': '🚀',
  'Mobile': '📱',
  'Design UX': '✏️',
  'Design UI': '🖼️',
  'Cibersegurança': '🔒',
  'Gestão de Produtos': '📋',
}

function SkeletonLine({ width = '100%' }: { width?: string }) {
  return (
    <div
      className="shimmer rounded"
      style={{ height: '12px', width, borderRadius: '4px' }}
    />
  )
}

export function ProfilePanel() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/profile/')
      .then(r => r.json())
      .then(data => { if (data.exists) setProfile(data.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const xp = LEVEL_XP[profile?.['Nível de experiência'] ?? ''] ?? 0
  const skills = profile?.['Habilidades atuais']?.split(',').map(s => s.trim()).filter(Boolean) ?? []
  const roles = profile?.['Funções alvo']?.split(',').map(s => s.trim()).filter(Boolean) ?? []
  const area = profile?.['Área de interesse'] ?? ''
  const areaIcon = AREA_ICONS[area] ?? '💼'
  const level = profile?.['Nível de experiência'] ?? ''

  return (
    <aside
      className="flex flex-col h-full overflow-y-auto"
      style={{
        width: '272px',
        minWidth: '272px',
        backgroundColor: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)',
      }}
    >
      {/* ── Header do perfil ── */}
      <div style={{ padding: '24px 20px 20px' }}>
        <p style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '16px' }}>
          Perfil do Agente
        </p>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <div className="shimmer" style={{ width: 52, height: 52, borderRadius: 'var(--radius-lg)', flexShrink: 0 }} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <SkeletonLine width="60%" />
                <SkeletonLine width="80%" />
              </div>
            </div>
            <SkeletonLine />
          </div>
        ) : !profile ? (
          /* Estado vazio */
          <div
            style={{
              padding: '20px',
              borderRadius: 'var(--radius-lg)',
              background: 'var(--bg-elevated)',
              border: '1px dashed var(--border-default)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '28px', marginBottom: '8px' }}>🎯</div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Complete o quiz para criar seu perfil profissional
            </p>
          </div>
        ) : (
          /* Perfil preenchido */
          <>
            {/* Avatar + nome */}
            <div style={{ display: 'flex', gap: '14px', alignItems: 'center', marginBottom: '16px' }}>
              <div
                style={{
                  width: '52px', height: '52px',
                  borderRadius: 'var(--radius-lg)',
                  background: 'linear-gradient(135deg, rgba(124,58,237,0.3) 0%, rgba(34,211,238,0.15) 100%)',
                  border: '1px solid rgba(124,58,237,0.35)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '22px', flexShrink: 0,
                  boxShadow: '0 0 20px rgba(124,58,237,0.2)',
                }}
              >
                {areaIcon}
              </div>
              <div style={{ minWidth: 0 }}>
                <p style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '2px' }}>
                  {area || 'Agente'}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span
                    style={{
                      fontSize: '11px', fontWeight: 600,
                      padding: '1px 8px',
                      borderRadius: 'var(--radius-full)',
                      background: 'rgba(124,58,237,0.15)',
                      border: '1px solid rgba(124,58,237,0.3)',
                      color: 'var(--violet-light)',
                    }}
                  >
                    {level}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {profile['Preferências de trabalho']}
                  </span>
                </div>
              </div>
            </div>

            {/* Barra de XP */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>Nível de experiência</span>
                <span style={{ fontSize: '11px', color: 'var(--violet-light)', fontFamily: 'var(--font-mono)' }}>{xp}%</span>
              </div>
              <div style={{ height: '4px', borderRadius: '99px', background: 'var(--bg-overlay)', overflow: 'hidden' }}>
                <motion.div
                  style={{ height: '100%', borderRadius: '99px', background: 'linear-gradient(90deg, var(--violet), var(--cyan))' }}
                  initial={{ width: 0 }}
                  animate={{ width: `${xp}%` }}
                  transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
            </div>
          </>
        )}
      </div>

      {/* ── Localização e objetivo ── */}
      {profile && (
        <div style={{ padding: '0 20px 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {[
            { icon: '📍', label: profile['Localização'] },
            { icon: '🎯', label: profile['Objetivo de carreira'] },
          ].map(({ icon, label }) => label && (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', flexShrink: 0 }}>{icon}</span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{label}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Divider ── */}
      {profile && <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '0 20px' }} />}

      {/* ── Funções alvo ── */}
      {roles.length > 0 && (
        <div style={{ padding: '20px' }}>
          <p style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
            Funções Alvo
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {roles.map((role, i) => (
              <motion.div
                key={role}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--cyan)', flexShrink: 0 }} />
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>{role}</span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── Divider ── */}
      {skills.length > 0 && <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '0 20px' }} />}

      {/* ── Skills ── */}
      {skills.length > 0 && (
        <div style={{ padding: '20px' }}>
          <p style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
            Habilidades
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {skills.map((skill, i) => (
              <motion.span
                key={skill}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.04 }}
                style={{
                  fontSize: '11px', fontWeight: 500,
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-full)',
                  background: 'rgba(124,58,237,0.1)',
                  border: '1px solid rgba(124,58,237,0.2)',
                  color: 'var(--violet-light)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {skill}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* ── Soft skills ── */}
      {profile?.['Soft skills'] && (
        <>
          <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '0 20px' }} />
          <div style={{ padding: '20px' }}>
            <p style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
              Soft Skills
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {profile['Soft skills']}
            </p>
          </div>
        </>
      )}

      {/* Espaço no final */}
      <div style={{ flexGrow: 1 }} />
    </aside>
  )
}
