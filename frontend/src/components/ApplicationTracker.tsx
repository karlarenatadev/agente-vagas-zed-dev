/**
 * Painel de rastreamento de candidaturas.
 * Exibe vagas salvas, permite mudar status e adicionar notas.
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ExternalLink, ChevronDown } from 'lucide-react'
import type { JobApplication, ApplicationStatus } from '../types'

const STATUS_CONFIG: Record<ApplicationStatus, { label: string; color: string; bg: string }> = {
  salva:        { label: 'Salva',        color: '#64748b', bg: 'rgba(100,116,139,0.12)' },
  aplicada:     { label: 'Aplicada',     color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  em_processo:  { label: 'Em processo',  color: '#22d3ee', bg: 'rgba(34,211,238,0.12)'  },
  entrevista:   { label: 'Entrevista',   color: '#fbbf24', bg: 'rgba(251,191,36,0.12)'  },
  oferta:       { label: 'Oferta',       color: '#34d399', bg: 'rgba(52,211,153,0.12)'  },
  recusada:     { label: 'Recusada',     color: '#fb7185', bg: 'rgba(251,113,133,0.12)' },
  desistiu:     { label: 'Desistiu',     color: '#475569', bg: 'rgba(71,85,105,0.12)'   },
}

const STATUS_ORDER: ApplicationStatus[] = [
  'salva', 'aplicada', 'em_processo', 'entrevista', 'oferta', 'recusada', 'desistiu',
]

function StatusBadge({ status, onClick }: { status: ApplicationStatus; onClick?: () => void }) {
  const cfg = STATUS_CONFIG[status]
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={onClick ? `Alterar status da candidatura. Status atual: ${cfg.label}` : cfg.label}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '4px',
        padding: '3px 10px',
        borderRadius: 'var(--radius-full)',
        background: cfg.bg,
        border: `1px solid ${cfg.color}40`,
        color: cfg.color,
        fontSize: '11px', fontWeight: 600,
        fontFamily: 'var(--font-sans)',
        cursor: onClick ? 'pointer' : 'default',
        whiteSpace: 'nowrap',
      }}
    >
      {cfg.label}
      {onClick && <ChevronDown size={10} />}
    </button>
  )
}

function StatusDropdown({
  current,
  onSelect,
  onClose,
}: {
  current: ApplicationStatus
  onSelect: (s: ApplicationStatus) => void
  onClose: () => void
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -4, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -4, scale: 0.96 }}
      transition={{ duration: 0.12 }}
      style={{
        position: 'absolute', top: '100%', left: 0, zIndex: 50,
        marginTop: '4px',
        background: 'var(--bg-overlay)',
        border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-md)',
        padding: '4px',
        minWidth: '140px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
      }}
    >
      {STATUS_ORDER.map(s => {
        const cfg = STATUS_CONFIG[s]
        return (
          <button
            type="button"
            key={s}
            onClick={() => { onSelect(s); onClose() }}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              width: '100%', padding: '7px 10px',
              borderRadius: 'var(--radius-sm)',
              background: s === current ? cfg.bg : 'transparent',
              border: 'none',
              color: s === current ? cfg.color : 'var(--text-secondary)',
              fontSize: '12px', fontWeight: s === current ? 600 : 400,
              fontFamily: 'var(--font-sans)',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
            {cfg.label}
          </button>
        )
      })}
    </motion.div>
  )
}

function ApplicationCard({
  app,
  onStatusChange,
  onDelete,
}: {
  app: JobApplication
  onStatusChange: (id: string, status: ApplicationStatus) => void
  onDelete: (id: string) => void
}) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [notes, setNotes] = useState(app.notas ?? '')
  const [editingNotes, setEditingNotes] = useState(false)

  const matchParts = app.contagem_correspondencia?.match(/(\d+)\s*de\s*(\d+)/)
  const matchNum = matchParts ? parseInt(matchParts[1]) : 0
  const matchTotal = matchParts ? parseInt(matchParts[2]) : 0
  const matchPct = matchTotal > 0 ? Math.round((matchNum / matchTotal) * 100) : 0

  const saveNotes = async () => {
    await fetch(`/api/applications/${app.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notas: notes }),
    })
    setEditingNotes(false)
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px',
        position: 'relative',
      }}
    >
      {/* Header do card */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '10px' }}>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px', lineHeight: 1.3 }}>
            {app.titulo}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {app.empresa} · {app.localizacao}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
          {/* Link externo */}
          {app.link && (
            <a
              href={app.link}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Abrir vaga ${app.titulo} em nova aba`}
              style={{
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <ExternalLink size={13} />
            </a>
          )}
          {/* Deletar */}
          <button
            type="button"
            onClick={() => onDelete(app.id)}
            aria-label={`Remover candidatura ${app.titulo}`}
            style={{
              color: 'var(--text-ghost)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '40px',
              height: '40px',
              padding: 0,
            }}
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Match bar */}
      {matchTotal > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Match de habilidades</span>
            <span style={{ fontSize: '11px', color: matchPct >= 60 ? 'var(--emerald)' : 'var(--amber)', fontFamily: 'var(--font-mono)' }}>
              {matchNum}/{matchTotal} ({matchPct}%)
            </span>
          </div>
          <div style={{ height: '3px', borderRadius: '99px', background: 'var(--bg-overlay)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '99px',
              width: `${matchPct}%`,
              background: matchPct >= 60
                ? 'linear-gradient(90deg, var(--emerald), #6ee7b7)'
                : 'linear-gradient(90deg, var(--amber), #fde68a)',
              transition: 'width 0.6s ease',
            }} />
          </div>
        </div>
      )}

      {/* Footer: status + data */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
        <div style={{ position: 'relative' }}>
          <StatusBadge status={app.status as ApplicationStatus} onClick={() => setShowDropdown(v => !v)} />
          <AnimatePresence>
            {showDropdown && (
              <StatusDropdown
                current={app.status as ApplicationStatus}
                onSelect={s => onStatusChange(app.id, s)}
                onClose={() => setShowDropdown(false)}
              />
            )}
          </AnimatePresence>
        </div>

        <span style={{ fontSize: '11px', color: 'var(--text-ghost)', fontFamily: 'var(--font-mono)' }}>
          {new Date(app.data_salva).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
        </span>
      </div>

      {/* Notas */}
      <div style={{ marginTop: '10px' }}>
        {editingNotes ? (
          <div>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Adicione notas sobre esta vaga..."
              aria-label={`Notas sobre ${app.titulo}`}
              rows={2}
              style={{
                width: '100%', resize: 'none',
                background: 'var(--bg-overlay)',
                border: '1px solid var(--border-focus)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 8px',
                fontSize: '12px', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
              }}
            />
            <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
              <button type="button" onClick={saveNotes} style={{ fontSize: '11px', color: 'var(--emerald)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Salvar
              </button>
              <button type="button" onClick={() => { setNotes(app.notas ?? ''); setEditingNotes(false) }} style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setEditingNotes(true)}
            aria-label={notes ? `Editar notas sobre ${app.titulo}` : `Adicionar nota sobre ${app.titulo}`}
            style={{
              fontSize: '11px',
              color: notes ? 'var(--text-secondary)' : 'var(--text-ghost)',
              background: 'none', border: 'none', cursor: 'pointer',
              fontFamily: 'var(--font-sans)', textAlign: 'left',
              padding: 0, lineHeight: 1.5,
            }}
          >
            {notes || '+ Adicionar nota'}
          </button>
        )}
      </div>
    </motion.div>
  )
}

// ── Painel principal ──────────────────────────────────────────────────────────

interface Props {
  isOpen: boolean
  onClose: () => void
}

export function ApplicationTracker({ isOpen, onClose }: Props) {
  const [applications, setApplications] = useState<JobApplication[]>([])
  const [filter, setFilter] = useState<ApplicationStatus | 'todas'>('todas')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isOpen) return

    const load = async () => {
      try {
        const res = await fetch('/api/applications/')
        const data = await res.json()
        setApplications(data)
      } catch {
        setApplications([])
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const handleStatusChange = async (id: string, status: ApplicationStatus) => {
    await fetch(`/api/applications/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    setApplications(prev => prev.map(a => a.id === id ? { ...a, status } : a))
  }

  const handleDelete = async (id: string) => {
    await fetch(`/api/applications/${id}`, { method: 'DELETE' })
    setApplications(prev => prev.filter(a => a.id !== id))
  }

  const filtered = filter === 'todas'
    ? applications
    : applications.filter(a => a.status === filter)

  // Contagens por status
  const counts = applications.reduce<Record<string, number>>((acc, a) => {
    acc[a.status] = (acc[a.status] ?? 0) + 1
    return acc
  }, {})

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.button
            type="button"
            aria-label="Fechar painel de candidaturas"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed', inset: 0, zIndex: 40,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(4px)',
              border: 0,
              padding: 0,
              cursor: 'pointer',
            }}
          />

          {/* Painel lateral direito */}
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-labelledby="applications-title"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            style={{
              position: 'fixed', top: 0, right: 0, bottom: 0, zIndex: 50,
              width: '420px', maxWidth: '95vw',
              background: 'var(--bg-surface)',
              borderLeft: '1px solid var(--border-default)',
              display: 'flex', flexDirection: 'column',
              boxShadow: '-8px 0 32px rgba(0,0,0,0.4)',
            }}
          >
            {/* Header */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '20px 20px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              flexShrink: 0,
            }}>
              <div>
                <h2 id="applications-title" style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '16px', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                  Candidaturas
                </h2>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {applications.length} vaga{applications.length !== 1 ? 's' : ''} salva{applications.length !== 1 ? 's' : ''}
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Fechar painel de candidaturas"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Filtros de status */}
            <div style={{
              display: 'flex', gap: '6px', flexWrap: 'wrap',
              padding: '12px 20px',
              borderBottom: '1px solid var(--border-subtle)',
              flexShrink: 0,
            }}>
              <button
                type="button"
                onClick={() => setFilter('todas')}
                aria-pressed={filter === 'todas'}
                style={{
                  padding: '4px 12px', borderRadius: 'var(--radius-full)',
                  background: filter === 'todas' ? 'rgba(124,58,237,0.15)' : 'transparent',
                  border: `1px solid ${filter === 'todas' ? 'rgba(124,58,237,0.4)' : 'var(--border-default)'}`,
                  color: filter === 'todas' ? 'var(--violet-light)' : 'var(--text-muted)',
                  fontSize: '11px', fontWeight: 600, cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                Todas ({applications.length})
              </button>
              {STATUS_ORDER.filter(s => counts[s]).map(s => {
                const cfg = STATUS_CONFIG[s]
                return (
                  <button
                    type="button"
                    key={s}
                    onClick={() => setFilter(s)}
                    aria-pressed={filter === s}
                    style={{
                      padding: '4px 12px', borderRadius: 'var(--radius-full)',
                      background: filter === s ? cfg.bg : 'transparent',
                      border: `1px solid ${filter === s ? cfg.color + '60' : 'var(--border-default)'}`,
                      color: filter === s ? cfg.color : 'var(--text-muted)',
                      fontSize: '11px', fontWeight: 600, cursor: 'pointer',
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    {cfg.label} ({counts[s]})
                  </button>
                )
              })}
            </div>

            {/* Lista */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {loading ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', paddingTop: '40px', fontSize: '13px' }}>
                  Carregando...
                </div>
              ) : filtered.length === 0 ? (
                <div style={{ textAlign: 'center', paddingTop: '40px' }}>
                  <div style={{ fontSize: '28px', marginBottom: '8px' }}>📋</div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    {filter === 'todas'
                      ? 'Nenhuma candidatura salva ainda.\nBusque vagas e salve as que te interessam.'
                      : `Nenhuma candidatura com status "${STATUS_CONFIG[filter].label}".`}
                  </p>
                </div>
              ) : (
                <AnimatePresence mode="popLayout">
                  {filtered.map(app => (
                    <ApplicationCard
                      key={app.id}
                      app={app}
                      onStatusChange={handleStatusChange}
                      onDelete={handleDelete}
                    />
                  ))}
                </AnimatePresence>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
export default ApplicationTracker
