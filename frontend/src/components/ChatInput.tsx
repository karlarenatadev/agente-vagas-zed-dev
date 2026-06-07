import { type KeyboardEvent, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowUp } from 'lucide-react'
import type { SessionMode } from '../types'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
  mode: SessionMode
}

export function ChatInput({ onSend, disabled, mode }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isMenu = mode === 'menu'
  const hasValue = value.trim().length > 0

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return

    onSend(trimmed)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const element = textareaRef.current
    if (!element) return

    element.style.height = 'auto'
    element.style.height = `${Math.min(element.scrollHeight, 128)}px`
  }

  return (
    <footer className="chat-input-shell">
      {isMenu && (
        <p className="input-mode-hint">
          Esteira visual pronta acima. Você também pode digitar A, B, C ou D.
        </p>
      )}

      <div className={`composer ${hasValue ? 'has-value' : ''}`}>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={event => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder={disabled ? 'Aguardando resposta...' : 'Escreva sua mensagem para o Maestro...'}
          rows={1}
          aria-label="Mensagem para o Maestro"
        />

        <motion.button
          className="send-button"
          type="button"
          whileHover={hasValue && !disabled ? { scale: 1.05 } : undefined}
          whileTap={hasValue && !disabled ? { scale: 0.94 } : undefined}
          onClick={handleSend}
          disabled={disabled || !hasValue}
          aria-label="Enviar mensagem"
        >
          <ArrowUp size={17} strokeWidth={2.5} aria-hidden="true" />
        </motion.button>
      </div>

      <p className="composer-hint">Enter envia. Shift+Enter cria uma nova linha.</p>
    </footer>
  )
}
