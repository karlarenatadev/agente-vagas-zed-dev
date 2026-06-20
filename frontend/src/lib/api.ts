const DEFAULT_TIMEOUT_MS = 25000

type ApiRequestInit = RequestInit & {
  timeoutMs?: number
}

export class ApiError extends Error {
  status?: number
  payload?: unknown

  constructor(message: string, status?: number, payload?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function stringifyDetail(value: unknown): string | null {
  if (typeof value === 'string') return value.trim() || null
  if (Array.isArray(value)) {
    const messages = value
      .map(item => {
        if (typeof item === 'string') return item
        if (isRecord(item)) {
          const message = item.msg ?? item.message ?? item.detail
          return typeof message === 'string' ? message : null
        }
        return null
      })
      .filter((message): message is string => Boolean(message?.trim()))

    return messages.length ? [...new Set(messages)].slice(0, 3).join(' ') : null
  }
  if (isRecord(value)) {
    const message = value.message ?? value.error ?? value.detail ?? value.msg
    if (typeof message === 'string') return message.trim() || null
    return JSON.stringify(value)
  }
  return null
}

function extractErrorMessage(payload: unknown): string | null {
  if (!isRecord(payload)) return stringifyDetail(payload)

  const detail = stringifyDetail(payload.detail)
  if (detail) return detail

  const message = stringifyDetail(payload.message)
  if (message) return message

  return stringifyDetail(payload.error)
}

function looksLikeTechnicalValidationMessage(message: string): boolean {
  const normalized = message.toLowerCase()
  return [
    'field required',
    'input should',
    'value is not',
    'missing',
    'string should',
    'list should',
    'type=',
  ].some(marker => normalized.includes(marker))
}

function statusMessage(status: number, payload: unknown): string {
  const extracted = extractErrorMessage(payload)

  if (status === 400) {
    return extracted || 'Nao foi possivel processar esta solicitacao. Revise os dados e tente novamente.'
  }

  if (status === 413) {
    return extracted || 'O arquivo enviado e maior que o limite permitido. Reduza o tamanho e tente novamente.'
  }

  if (status === 422) {
    if (extracted && !looksLikeTechnicalValidationMessage(extracted)) return extracted
    return 'Alguns dados enviados nao passaram na validacao. Revise as informacoes e tente novamente.'
  }

  if (status >= 500) {
    return 'O backend encontrou uma falha ao processar esta etapa. Tente novamente em alguns instantes.'
  }

  return extracted || 'Nao foi possivel completar esta solicitacao. Tente novamente em alguns instantes.'
}

function parseJson(text: string, status: number, ok: boolean): unknown {
  const trimmed = text.trim()
  if (!trimmed) {
    if (ok) {
      throw new ApiError('Recebi uma resposta vazia do backend. Tente novamente em alguns instantes.', status)
    }
    return null
  }

  try {
    return JSON.parse(trimmed) as unknown
  } catch {
    if (ok) {
      throw new ApiError('Recebi uma resposta inesperada do backend. Tente novamente em alguns instantes.', status)
    }
    return trimmed
  }
}

export function isApiErrorStatus(error: unknown, status: number): boolean {
  return error instanceof ApiError && error.status === status
}

export async function apiRequest<T>(url: string, init: ApiRequestInit = {}): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...requestInit } = init
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, {
      ...requestInit,
      signal: controller.signal,
    })
    const text = await response.text()
    const payload = parseJson(text, response.status, response.ok)

    if (!response.ok) {
      throw new ApiError(statusMessage(response.status, payload), response.status, payload)
    }

    return payload as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('A solicitacao demorou mais que o esperado. Tente novamente em alguns instantes.')
    }
    throw new ApiError('Nao consegui falar com o backend agora. Confira se o servidor esta rodando e tente novamente.')
  } finally {
    window.clearTimeout(timeoutId)
  }
}
