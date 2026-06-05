import { type KeyboardEvent, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, CheckCircle2 } from 'lucide-react'

interface Props {
  step: number
  question: string
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

const FALLBACK_QUESTIONS = [
  'Qual área mais te anima?',
  'Como você descreveria seu nível de experiência atual?',
  'Como você prefere trabalhar?',
  'Onde você está localizado?',
  'Quais são suas soft skills mais fortes?',
  'Onde você se vê em sua carreira?',
  'Quais habilidades técnicas você já tem?',
]

const TOTAL = 7

const QUICK_OPTIONS: Record<number, string[]> = {
  0: [
    'Frontend',
    'Backend',
    'Ciência de Dados',
    'Full Stack',
    'DevOps',
    'Mobile',
    'Design UX',
    'Design UI',
    'Gestão de Produtos',
    'Cibersegurança',
  ],
  1: ['Júnior', 'Pleno', 'Sênior'],
  2: ['Remoto', 'Híbrido', 'Presencial'],
  5: ['Crescimento técnico', 'Transição de carreira', 'Primeiro emprego', 'Trilha de liderança'],
}

export function QuizPanel({ step, question, onAnswer, disabled }: Props) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const quickOptions = QUICK_OPTIONS[step] ?? []
  const hasValue = value.trim().length > 0
  const safeStep = Math.min(Math.max(step, 0), TOTAL - 1)
  const currentQuestion = question || FALLBACK_QUESTIONS[safeStep]

  useEffect(() => {
    window.setTimeout(() => inputRef.current?.focus(), 80)
  }, [step])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return

    onAnswer(trimmed)
    setValue('')
  }

  const handleQuickAnswer = (answer: string) => {
    if (disabled) return
    onAnswer(answer)
  }

  const handleKey = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = () => {
    const element = inputRef.current
    if (!element) return

    element.style.height = 'auto'
    element.style.height = `${Math.min(element.scrollHeight, 112)}px`
  }

  return (
    <section className="quiz-panel" aria-label="Quiz de perfil profissional">
      <div className="quiz-progress">
        <div className="quiz-progress-top">
          <span>Criando seu perfil</span>
          <strong>{safeStep + 1} de {TOTAL}</strong>
        </div>

        <div className="quiz-step-track" aria-hidden="true">
          {Array.from({ length: TOTAL }).map((_, index) => (
            <span
              key={index}
              className={index < safeStep ? 'done' : index === safeStep ? 'active' : ''}
            />
          ))}
        </div>

        <p>{STEP_LABELS[safeStep]}</p>
      </div>

      <div className="quiz-body">
        <AnimatePresence mode="wait">
          <motion.div
            key={`question-${safeStep}`}
            className="quiz-card"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.22 }}
          >
            <span className="quiz-step-chip">
              <CheckCircle2 size={15} aria-hidden="true" />
              Responda para avançar
            </span>

            <h2>{currentQuestion}</h2>

            {quickOptions.length > 0 && (
              <div className="quick-options" aria-label="Opções rápidas">
                {quickOptions.map(option => (
                  <motion.button
                    key={option}
                    type="button"
                    className="quick-option"
                    disabled={disabled}
                    onClick={() => handleQuickAnswer(option)}
                    whileHover={disabled ? undefined : { y: -1 }}
                    whileTap={disabled ? undefined : { scale: 0.97 }}
                  >
                    {option}
                  </motion.button>
                ))}
              </div>
            )}

            <div className={`composer quiz-composer ${hasValue ? 'has-value' : ''}`}>
              <textarea
                ref={inputRef}
                value={value}
                onChange={event => setValue(event.target.value)}
                onKeyDown={handleKey}
                onInput={handleInput}
                disabled={disabled}
                placeholder={quickOptions.length > 0 ? 'Ou escreva sua resposta...' : 'Escreva sua resposta...'}
                rows={1}
                aria-label="Resposta do quiz"
              />

              <motion.button
                className="send-button"
                type="button"
                whileHover={hasValue && !disabled ? { scale: 1.05 } : undefined}
                whileTap={hasValue && !disabled ? { scale: 0.94 } : undefined}
                onClick={handleSubmit}
                disabled={disabled || !hasValue}
                aria-label="Enviar resposta do quiz"
              >
                <ArrowRight size={17} strokeWidth={2.5} aria-hidden="true" />
              </motion.button>
            </div>

            <p className="composer-hint left">Enter para continuar. Você pode editar antes de enviar.</p>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}

export default QuizPanel
