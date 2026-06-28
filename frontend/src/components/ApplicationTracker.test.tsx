import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../lib/api'
import { applicationFixture } from '../test/fixtures'
import { ApplicationTracker } from './ApplicationTracker'

vi.mock('../lib/api', () => ({
  apiRequest: vi.fn(),
  ApiError: class ApiError extends Error {},
}))

const apiRequestMock = vi.mocked(apiRequest)

function renderTracker(payload: unknown) {
  apiRequestMock.mockResolvedValue(payload)
  render(<ApplicationTracker isOpen onClose={vi.fn()} />)
}

beforeEach(() => {
  apiRequestMock.mockReset()
})

describe('ApplicationTracker - dados externos e legados', () => {
  it.each([
    'https://jobs.example.com/vaga-1',
    'http://jobs.example.com/vaga-2',
  ])('renderiza link http(s) válido com proteção: %s', async link => {
    renderTracker([{ ...applicationFixture, link }])

    const anchor = await screen.findByRole('link', {
      name: /Abrir vaga Analista de Dados Junior em nova aba/i,
    }) as HTMLAnchorElement

    expect(anchor.getAttribute('href')).toBe(link)
    expect(anchor.getAttribute('target')).toBe('_blank')
    expect(anchor.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it.each([
    'javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'jobs.example.com/vaga-3',
  ])('não renderiza âncora para link inseguro legado: %s', async link => {
    renderTracker([{ ...applicationFixture, link }])

    expect(await screen.findByText('Link indisponível')).toBeTruthy()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('aceita link vazio sem renderizar âncora ou alerta', async () => {
    renderTracker([{ ...applicationFixture, link: '' }])

    expect(await screen.findByText(applicationFixture.titulo)).toBeTruthy()
    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.queryByText('Link indisponível')).toBeNull()
  })

  it('normaliza status e campos legados inválidos sem quebrar o painel', async () => {
    renderTracker([
      {
        ...applicationFixture,
        link: 'javascript:alert(1)',
        status: 'arquivada',
        data_salva: 'data-invalida',
        contagem_correspondencia: 123,
      },
    ])

    expect(await screen.findByText(applicationFixture.titulo)).toBeTruthy()
    expect(screen.getByText('Status inválido')).toBeTruthy()
    expect(screen.getByText('Link indisponível')).toBeTruthy()
    expect(screen.getByText('Data indisponível')).toBeTruthy()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('ignora itens legados que não são objetos e mantém registros utilizáveis', async () => {
    renderTracker([
      null,
      'registro-invalido',
      42,
      applicationFixture,
    ])

    expect(await screen.findByText(applicationFixture.titulo)).toBeTruthy()
    expect(screen.getByText('1 vaga salva')).toBeTruthy()
  })
})
