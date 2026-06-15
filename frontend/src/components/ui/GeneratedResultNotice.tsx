import { CheckCircle2 } from 'lucide-react'

export function GeneratedResultNotice({
  title,
  nextStep,
}: {
  title: string
  nextStep: string
}) {
  return (
    <div className="generated-result-notice" role="status" aria-live="polite">
      <span className="generated-now-badge">
        <CheckCircle2 size={14} aria-hidden="true" />
        Gerado agora
      </span>
      <span>
        <strong>{title}</strong>
        <small>{nextStep}</small>
      </span>
    </div>
  )
}
