/**
 * Identidade de sessão anônima.
 *
 * Cada navegador gera um ID único (guardado em localStorage) que isola seus
 * dados no backend (data/sessions/{id}/). O ID viaja em todo request REST pelo
 * header X-Session-Id e na conexão WebSocket pela query string.
 */

const STORAGE_KEY = 'import-vagas:session-id'

/** Retorna o ID da sessão, criando e persistindo um novo na primeira vez. */
export function getSessionId(): string {
  let id = localStorage.getItem(STORAGE_KEY)
  if (!id) {
    id =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `s-${Date.now()}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem(STORAGE_KEY, id)
  }
  return id
}

/**
 * Instala um wrapper sobre window.fetch que injeta o header X-Session-Id em
 * todas as chamadas para /api/. Centraliza o envio do ID sem precisar alterar
 * cada componente que faz fetch. Chamar uma vez, no boot do app.
 */
export function installSessionFetch(): void {
  const original = window.fetch.bind(window)

  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.pathname
          : input.url

    if (url.includes('/api/')) {
      const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined))
      headers.set('X-Session-Id', getSessionId())
      return original(input, { ...init, headers })
    }

    return original(input, init)
  }
}
