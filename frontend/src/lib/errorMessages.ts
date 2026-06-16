export function getFriendlyErrorMessage(error: unknown, fallback: string): string {
  const message = error instanceof Error ? error.message.trim() : ''
  if (!message) return fallback

  const normalized = message.toLowerCase()
  const isNetworkFailure = [
    'failed to fetch',
    'networkerror',
    'load failed',
    'fetch failed',
  ].some(marker => normalized.includes(marker))

  if (isNetworkFailure) {
    return 'Não consegui falar com o backend agora. Confira se o servidor está rodando e tente novamente.'
  }

  const isServerFailure = [
    'internal server error',
    'erro interno',
    'falha http 500',
    'http 500',
  ].some(marker => normalized.includes(marker))

  if (isServerFailure) {
    return 'O backend encontrou uma falha ao processar esta etapa. Tente novamente em alguns instantes.'
  }

  const isInvalidPayload = [
    'unexpected token',
    'invalid json',
    'json',
  ].some(marker => normalized.includes(marker))

  if (isInvalidPayload) {
    return 'Recebi uma resposta inesperada do backend. Tente novamente em alguns instantes.'
  }

  return message
}
