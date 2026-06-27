import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../lib/api'
import { ProfileSuggestionConfirm } from './ProfileSuggestionConfirm'
import type { ProfileSuggestion } from '../types'

vi.mock('../lib/api', () => ({
  apiRequest: vi.fn(),
  ApiError: class ApiError extends Error {},
}))

const apiRequestMock = vi.mocked(apiRequest)

const applicableSuggestion: ProfileSuggestion = {
  field: 'Área de interesse',
  source: 'curriculo',
  current_value: '',
  suggested_value: 'Ciência de Dados',
  applicable: true,
  conflict: false,
}

beforeEach(() => {
  apiRequestMock.mockReset()
})

describe('ProfileSuggestionConfirm', () => {
  it('mostra o aviso de não atualização automática, o campo e o valor sugerido', () => {
    render(<ProfileSuggestionConfirm suggestions={[applicableSuggestion]} />)

    expect(screen.getByText(/foi atualizado automaticamente a partir do currículo/i)).toBeTruthy()
    expect(screen.getByText('Área de interesse')).toBeTruthy()
    expect(screen.getByText(/Ciência de Dados/)).toBeTruthy()
  })

  it('chama a API com confirm=true e o campo selecionado ao aplicar', async () => {
    apiRequestMock.mockResolvedValue({
      success: true,
      updated_fields: ['Área de interesse'],
      profile: {},
    })

    render(<ProfileSuggestionConfirm suggestions={[applicableSuggestion]} />)

    fireEvent.click(screen.getByRole('button', { name: /Aplicar selecionados/i }))

    expect(await screen.findByText(/Perfil atualizado a partir do currículo/i)).toBeTruthy()

    expect(apiRequestMock).toHaveBeenCalledTimes(1)
    const call = apiRequestMock.mock.calls[0]
    expect(call[0]).toBe('/api/resume/apply-profile')

    const parsedBody = JSON.parse(call[1]?.body as string)
    expect(parsedBody.confirm).toBe(true)
    expect(parsedBody.fields).toContain('Área de interesse')
  })

  it('exibe mensagem de erro (role=alert) quando a confirmação falha', async () => {
    apiRequestMock.mockRejectedValue(new Error('falha'))

    render(<ProfileSuggestionConfirm suggestions={[applicableSuggestion]} />)

    fireEvent.click(screen.getByRole('button', { name: /Aplicar selecionados/i }))

    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.queryByText(/Perfil atualizado a partir do currículo/i)).toBeNull()
  })

  it('não renderiza nenhum card quando não há sugestões acionáveis', () => {
    const { container } = render(<ProfileSuggestionConfirm suggestions={[]} />)

    expect(container.firstChild).toBeNull()
  })

  it('ao ignorar as sugestões não chama a API e avisa que o perfil não foi alterado', () => {
    render(<ProfileSuggestionConfirm suggestions={[applicableSuggestion]} />)

    fireEvent.click(screen.getByRole('button', { name: /Ignorar sugestões/i }))

    expect(apiRequestMock).not.toHaveBeenCalled()
    expect(screen.getByText(/Seu perfil não foi alterado/i)).toBeTruthy()
  })
})
