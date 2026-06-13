import { AlertCircle, CheckCircle2, CircleDot, Loader2 } from 'lucide-react'

export function FeedbackState({
  tone,
  title,
  description,
}: {
  tone: 'loading' | 'empty' | 'error' | 'success'
  title: string
  description?: string
}) {
  const Icon = tone === 'loading'
    ? Loader2
    : tone === 'error'
      ? AlertCircle
      : tone === 'success'
        ? CheckCircle2
        : CircleDot

  return (
    <div className={`feedback-state ${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <span className="feedback-state-icon">
        <Icon size={16} className={tone === 'loading' ? 'spin' : undefined} aria-hidden="true" />
      </span>
      <span>
        <strong>{title}</strong>
        {description && <small>{description}</small>}
      </span>
    </div>
  )
}
