import { useState } from 'react'
import { Check, Clipboard } from 'lucide-react'

async function copyText(value: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value)
      return
    } catch {
      // Restricted browser contexts can expose Clipboard API but reject writes.
    }
  }

  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  textarea.remove()
}

export function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await copyText(value)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <button
      type="button"
      className="copy-button"
      onClick={copy}
      aria-label={`Copiar ${label}`}
    >
      {copied
        ? <Check size={13} aria-hidden="true" />
        : <Clipboard size={13} aria-hidden="true" />}
      {copied ? 'Copiado' : 'Copiar'}
    </button>
  )
}
