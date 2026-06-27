import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ScoutReport, type ScoutData } from './ScoutReport'

// Cria um ScoutData minimo com uma unica vaga, permitindo sobrescrever os
// campos relevantes (source, link) para cada cenario de normalizacao de link.
function dataWithJob(job: Partial<ScoutData['vagas'][number]>): ScoutData {
  return {
    resumo: 'Analisei 1 vaga encontrada.',
    requisitos: [],
    vagas: [
      {
        titulo: 'Analista de Dados',
        empresa: 'Acme',
        ...job,
      },
    ],
  }
}

describe('ScoutReport - normalizacao de links', () => {
  it('vaga real com URL http(s) valida produz link clicavel com noopener noreferrer', () => {
    render(
      <ScoutReport
        data={dataWithJob({ source: 'real', link: 'https://jobs.example.com/vaga-123' })}
      />,
    )

    const link = screen.getByRole('link', { name: /Ver vaga/i }) as HTMLAnchorElement
    expect(link.getAttribute('href')).toBe('https://jobs.example.com/vaga-123')
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it('aceita URL http (nao apenas https) para vaga real', () => {
    render(
      <ScoutReport data={dataWithJob({ source: 'real', link: 'http://jobs.example.com/vaga-9' })} />,
    )

    const link = screen.getByRole('link', { name: /Ver vaga/i }) as HTMLAnchorElement
    expect(link.getAttribute('href')).toBe('http://jobs.example.com/vaga-9')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it('vaga simulated nao produz link clicavel mesmo com URL valida', () => {
    render(
      <ScoutReport
        data={dataWithJob({ source: 'simulated', link: 'https://jobs.example.com/vaga-123' })}
      />,
    )

    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()
  })

  it('vaga llm nao produz link clicavel mesmo com URL valida', () => {
    render(
      <ScoutReport
        data={dataWithJob({ source: 'llm', link: 'https://jobs.example.com/vaga-123' })}
      />,
    )

    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()
  })

  it('vaga real com link sem esquema http(s) valido nao produz link clicavel', () => {
    render(
      <ScoutReport data={dataWithJob({ source: 'real', link: 'jobs.example.com/vaga-123' })} />,
    )

    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()
  })

  it('vaga real com esquema nao http (ftp/javascript) nao produz link clicavel', () => {
    render(
      <ScoutReport data={dataWithJob({ source: 'real', link: 'ftp://files.example.com/vaga' })} />,
    )
    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()

    render(
      <ScoutReport
        data={dataWithJob({ source: 'real', link: 'javascript:alert(1)' })}
      />,
    )
    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()
  })

  it('vaga real sem link (vazio/nao informado) nao produz link clicavel', () => {
    render(<ScoutReport data={dataWithJob({ source: 'real', link: 'Nao informado' })} />)
    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()

    render(<ScoutReport data={dataWithJob({ source: 'real', link: '' })} />)
    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()
  })
})
