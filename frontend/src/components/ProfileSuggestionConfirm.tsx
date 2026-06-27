import { useState } from 'react'
import { apiRequest } from '../lib/api'
import { getFriendlyErrorMessage } from '../lib/errorMessages'
import type { ApplyProfileResponse, ProfileSuggestion } from '../types'

interface Props {
  suggestions: ProfileSuggestion[]
}

type ConfirmStatus = 'idle' | 'applying' | 'success' | 'error'

export function ProfileSuggestionConfirm({ suggestions }: Props) {
  const actionable = suggestions.filter(s => s.applicable || s.conflict)

  // Inicia com os campos aplicáveis marcados; conflitos ficam DESmarcados por
  // padrão para não substituir um valor existente sem opt-in explícito.
  const [selected, setSelected] = useState<Set<string>>(() => {
    const initial = new Set<string>()
    for (const suggestion of actionable) {
      if (suggestion.applicable) initial.add(suggestion.field)
    }
    return initial
  })
  const [status, setStatus] = useState<ConfirmStatus>('idle')
  const [message, setMessage] = useState('')
  const [updatedFields, setUpdatedFields] = useState<string[]>([])
  const [dismissed, setDismissed] = useState(false)

  if (actionable.length === 0) return null

  const toggleField = (field: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(field)) next.delete(field)
      else next.add(field)
      return next
    })
  }

  const applySelected = async () => {
    setStatus('applying')
    const fields = [...selected]
    try {
      const res = await apiRequest<ApplyProfileResponse>('/api/resume/apply-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true, fields }),
      })
      if (!res.success) throw new Error('Falha ao aplicar.')
      setUpdatedFields(res.updated_fields)
      setStatus('success')
      window.dispatchEvent(new Event('profile-updated'))
      window.dispatchEvent(new Event('pipeline-updated'))
    } catch (error) {
      setStatus('error')
      setMessage(getFriendlyErrorMessage(
        error,
        'Não foi possível atualizar o perfil. Tente novamente.',
      ))
    }
  }

  const dismiss = () => setDismissed(true)

  if (dismissed) {
    return (
      <div className="profile-confirm-card">
        <p role="status">Sugestões ignoradas. Seu perfil não foi alterado.</p>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="profile-confirm-card">
        <p role="status">Perfil atualizado a partir do currículo.</p>
        {updatedFields.length > 0 ? (
          <ul className="profile-confirm-updated">
            {updatedFields.map(field => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        ) : (
          <p>Nenhum campo precisou ser alterado.</p>
        )}
      </div>
    )
  }

  return (
    <div className="profile-confirm-card">
      <p className="profile-confirm-warning">
        Seu perfil <strong>não</strong> foi atualizado automaticamente a partir do currículo.
        Revise as sugestões e confirme o que deseja aplicar.
      </p>

      <ul className="profile-confirm-list">
        {actionable.map((suggestion, index) => {
          const checkboxId = `profile-suggestion-${index}`
          return (
            <li key={suggestion.field} className="profile-confirm-row">
              <input
                type="checkbox"
                id={checkboxId}
                checked={selected.has(suggestion.field)}
                onChange={() => toggleField(suggestion.field)}
              />
              <label htmlFor={checkboxId}>
                <span className="profile-confirm-field">{suggestion.field}</span>
                {suggestion.conflict && (
                  <span
                    className="profile-confirm-badge"
                    title="O valor atual do perfil será substituído pelo valor sugerido."
                  >
                    conflito
                  </span>
                )}
                <span className="profile-confirm-values">
                  atual: {suggestion.current_value || '(vazio)'} → sugerido: {suggestion.suggested_value}
                </span>
              </label>
            </li>
          )
        })}
      </ul>

      {status === 'error' && (
        <p className="profile-confirm-error" role="alert">
          {message}
        </p>
      )}

      <div className="profile-confirm-actions">
        <button
          type="button"
          className="primary-action-button"
          onClick={applySelected}
          disabled={selected.size === 0 || status === 'applying'}
        >
          {status === 'applying' ? 'Aplicando...' : 'Aplicar selecionados'}
        </button>
        <button
          type="button"
          className="secondary-action-button"
          onClick={dismiss}
        >
          Ignorar sugestões
        </button>
      </div>
    </div>
  )
}

export default ProfileSuggestionConfirm
