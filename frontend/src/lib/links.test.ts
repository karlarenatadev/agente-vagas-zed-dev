import { describe, expect, it } from 'vitest'
import { normalizeHttpLink } from './links'

describe('normalizeHttpLink', () => {
  it('aceita URL https valida e devolve a forma normalizada', () => {
    const result = normalizeHttpLink('https://x.com/a')
    expect(result).toContain('https://x.com')
    expect(result).toContain('/a')
  })

  it('aceita URL http (nao apenas https)', () => {
    const result = normalizeHttpLink('http://x.com')
    expect(result).not.toBeNull()
    expect(result!.startsWith('http://')).toBe(true)
  })

  it('retorna null para valores vazios/ausentes', () => {
    expect(normalizeHttpLink('')).toBeNull()
    expect(normalizeHttpLink('   ')).toBeNull()
    expect(normalizeHttpLink(undefined)).toBeNull()
    expect(normalizeHttpLink(null)).toBeNull()
  })

  it('bloqueia esquemas inseguros e nao http(s)', () => {
    expect(normalizeHttpLink('ftp://x')).toBeNull()
    expect(normalizeHttpLink('javascript:alert(1)')).toBeNull()
    expect(normalizeHttpLink('data:text/html,x')).toBeNull()
    expect(normalizeHttpLink('mailto:a@b.com')).toBeNull()
    expect(normalizeHttpLink('file:///etc')).toBeNull()
  })

  it('bloqueia strings sem esquema (caminho relativo / texto livre)', () => {
    expect(normalizeHttpLink('udemy.com/curso')).toBeNull()
  })
})
