import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CuratorReport, type CuratorData } from './CuratorReport'

// Cria um CuratorData minimo com 1 bucket / 1 skill / 1 resource, permitindo
// sobrescrever o `link` do recurso por cenario de normalizacao de link.
function dataWithLink(link?: string): CuratorData {
  return {
    resumo: 'Trilha priorizada.',
    buckets: [
      {
        label: 'Fundamentos',
        skills: [
          {
            habilidade: 'Python',
            resources: [
              { kind: 'free', label: 'Curso', name: 'Python Básico', link },
            ],
          },
        ],
      },
    ],
  }
}

describe('CuratorReport - normalizacao de links', () => {
  it('URL https valida produz link clicavel com noopener noreferrer', () => {
    render(<CuratorReport data={dataWithLink('https://curso.example.com/python')} />)

    const link = screen.getByRole('link', { name: /Abrir/i }) as HTMLAnchorElement
    expect(link.getAttribute('href')).toBe('https://curso.example.com/python')
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it('aceita URL http (nao apenas https)', () => {
    render(<CuratorReport data={dataWithLink('http://curso.example.com/python')} />)

    const link = screen.getByRole('link', { name: /Abrir/i }) as HTMLAnchorElement
    expect(link.getAttribute('href')).toBe('http://curso.example.com/python')
  })

  it('link com esquema inseguro (javascript:) nao vira link e mostra aviso', () => {
    render(<CuratorReport data={dataWithLink('javascript:alert(1)')} />)

    expect(screen.queryByRole('link', { name: /Abrir/i })).toBeNull()
    expect(screen.getByText(/Link não disponível/i)).toBeTruthy()
  })

  it('link sem esquema http(s) nao vira link clicavel e mostra aviso', () => {
    render(<CuratorReport data={dataWithLink('udemy.com/python')} />)

    expect(screen.queryByRole('link', { name: /Abrir/i })).toBeNull()
    expect(screen.getByText(/Link não disponível/i)).toBeTruthy()
  })

  it('link vazio ou "Não informado" nao vira link nem mostra aviso', () => {
    render(<CuratorReport data={dataWithLink('')} />)
    expect(screen.queryByRole('link', { name: /Abrir/i })).toBeNull()
    expect(screen.queryByText(/Link não disponível/i)).toBeNull()

    render(<CuratorReport data={dataWithLink('Não informado')} />)
    expect(screen.queryByRole('link', { name: /Abrir/i })).toBeNull()
    expect(screen.queryByText(/Link não disponível/i)).toBeNull()
  })
})
