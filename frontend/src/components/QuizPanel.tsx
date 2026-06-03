/**
 * Painel de quiz — exibe a pergunta atual de forma isolada e limpa.
 * Substitui o fluxo de perguntas no chat quando mode === 'quiz'.
 */

import { type KeyboardEvent, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight } from 'lucide-react'

interface Props {
  step: number          // 0-indexed, 0..6
  question: string      // texto da pergunta atual
  onAnswer: (answer: string) => void
  disabled: boolean
}

const STEP_LABELS = [
  'Área de interesse',
  'Nível de experiência',
  'Preferência de trabalho',
  'Localização',
  'Soft skills',
  'Objetivo de carreira',
  'Habilidades técnicas',
]

const TOTAL = 7

// Opções rápidas por passo
const QUICK_OPTIONS: Record<number, string[]> = {
  0: ['Frontend', 'Backend', 'Ciência de Dados', 'Full Stack', 'DevOps', 'Mobile', 'Design UX', 'Design UI', 'Gestão de Produtos', 'Cibersegurança', 'Liderança', 'RH', 'Growth Marketing'],
  1: ['Júnior', 'Pleno', 'Sênior'],
  2: ['Remoto', 'Híbrido', 'Presencial'],
  5: ['Crescimento técnico', 'Transição de carreira', 'Primeiro emprego', 'Trilha de liderança'],
}

export function QuizPanel({ step, question, onAnswer, disabled }: Props) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Foca o input quando a pergunta muda
  useEffect(() => {
    setValue('')
    setTimeout(() => inputRef.current?.focus(), 100)
  }, [step])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onAnswer(trimmed)
    setValue('')
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  const handleInput = () => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 100)}px`
  }

  const quickOpts = QUICK_OPTIONS[step] ?? []
  const hasValue = value.trim().length > 0

  return (
    <motion.div
      key={step}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      style={{
        display: 'flex', flexDirection: 'column',
        flex: 1, overflow: 'hidden',
        background: 'var(--bg-base)',
      }}
    >
      {/* Barra de progresso */}
      <div style={{ padding: '24px 32px 0', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--violet-light)', fontFamily: 'var(--font-sans)' }}>
            Criando seu perfil
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {step + 1} / {TOTAL}
          </span>
        </div>

        {/* Steps visuais */}
        <div style={{ display: 'flex', gap: '4px' }}>
          {Array.from({ length: TOTAL }).map((_, i) => (
            <div
              key={i}
              style={{
                flex: 1, height: '3px', borderRadius: '99px',
                background: i < step
                  ? 'var(--violet)'
                  : i === step
                  ? 'linear-gradient(90deg, var(--violet), var(--cyan))'
                  : 'var(--bg-overlay)',
                transition: 'background 0.3s',
              }}
            />
          ))}
        </div>

        {/* Label do passo atual */}
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
          {STEP_LABELS[step] ?? ''}
        </p>
      </div>

      {/* Área central — pergunta */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        justifyContent: 'center', padding: '32px',
        overflowY: 'auto',
      }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={`q-${step}`}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Pergunta */}
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 'clamp(18px, 2.5vw, 24px)',
              color: 'var(--text-primary)',
              lineHeight: 1.4,
              letterSpacing: '-0.02em',
              marginBottom: '28px',
              maxWidth: '560px',
            }}>
              {question}
            </h2>

            {/* Opções rápidas */}
            {quickOpts.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '24px' }}>
                {quickOpts.map(opt => (
                  <motion.button
                    key={opt}
                    whileHover={{ scale: 1.03, y: -1 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => { setValue(opt); setTimeout(handleSubmit, 50) }}
                    disabled={disabled}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-md)',
                      background: value === opt ? 'rgba(124,58,237,0.2)' : 'var(--bg-elevated)',
                      border: `1px solid ${value === opt ? 'rgba(124,58,237,0.5)' : 'var(--border-default)'}`,
                      color: value === opt ? 'var(--violet-light)' : 'var(--text-secondary)',
                      fontSize: '13px', fontWeight: 500,
                      fontFamily: 'var(--font-sans)',
                      cursor: disabled ? 'not-allowed' : 'pointer',
                      transition: 'all 0.15s',
                    }}
                  >
                    {opt}
                  </motion.button>
                ))}
              </div>
            )}

            {/* Input de texto livre */}
            <div style={{
              display: 'flex', alignItems: 'flex-end', gap: '10px',
              padding: '12px 14px',
              borderRadius: 'var(--radius-lg)',
              background: 'var(--bg-elevated)',
              border: `1px solid ${hasValue ? 'var(--border-focus)' : 'var(--border-default)'}`,
              boxShadow: hasValue ? '0 0 0 3px rgba(124,58,237,0.08)' : 'none',
              transition: 'border-color 0.2s, box-shadow 0.2s',
              maxWidth: '560px',
            }}>
              <textarea
                ref={inputRef}
                value={value}
                onChange={e => setValue(e.target.value)}
                onKeyDown={handleKey}
                onInput={handleInput}
                disabled={disabled}
                placeholder={quickOpts.length > 0 ? 'Ou escreva sua resposta...' : 'Escreva sua resposta...'}
                rows={1}
                style={{
                  flex: 1, resize: 'none',
                  background: 'transparent', border: 'none', outline: 'none',
                  fontSize: '14px', color: 'var(--text-primary)',
                  fontFamily: 'var(--font-sans)', lineHeight: '1.55',
                  caretColor: 'var(--violet-light)',
                }}
              />
              <motion.button
                whileHover={hasValue && !disabled ? { scale: 1.08 } : {}}
                whileTap={hasValue && !disabled ? { scale: 0.92 } : {}}
                onClick={handleSubmit}
                disabled={disabled || !hasValue}
                style={{
                  width: '32px', height: '32px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: hasValue && !disabled
                    ? 'linear-gradient(135deg, var(--violet) 0%, #5b21b6 100%)'
                    : 'var(--bg-overlay)',
                  border: 'none',
                  cursor: hasValue && !disabled ? 'pointer' : 'not-allowed',
                  flexShrink: 0,
                  boxShadow: hasValue && !disabled ? '0 0 12px rgba(124,58,237,0.35)' : 'none',
                  transition: 'all 0.2s',
                }}
              >
                <ArrowRight size={15} color={hasValue && !disabled ? 'white' : 'var(--text-ghost)'} strokeWidth={2.5} />
              </motion.button>
            </div>

            <p style={{ fontSize: '11px', color: 'var(--text-ghost)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
              Enter para continuar
            </p>
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
