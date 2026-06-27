/**
 * Validação e normalização de URLs para uso seguro em atributos `href`.
 *
 * Esta é a mesma proteção aplicada no Scout e no Curator: um link só é
 * considerado "clicável" quando é uma URL http(s) bem formada. Isso bloqueia
 * esquemas perigosos (`javascript:`, `data:`, `file:`, `ftp:` ...) e strings
 * que não são URLs (caminhos relativos, texto livre, "Não informado" etc.).
 */

/**
 * Normaliza uma URL http(s) ou retorna `null` quando o valor não é seguro.
 *
 * Retorna `null` se o valor for vazio/ausente, não começar com `http://` ou
 * `https://`, não for parseável por `new URL()`, ou se o protocolo final não
 * for http/https. Caso contrário, devolve a URL normalizada (`URL.toString()`).
 */
export function normalizeHttpLink(value?: string | null): string | null {
  if (!value) return null
  const trimmed = value.trim()
  if (!trimmed) return null
  if (!/^https?:\/\//i.test(trimmed)) return null
  try {
    const url = new URL(trimmed)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : null
  } catch {
    return null
  }
}
