  import { AlertCircle, Check, Circle, LockKeyhole, Play } from 'lucide-react'
import type { PipelineStatus } from '../../types'

const STATUS_CONFIG = {
  completed: { label: 'Concluído', icon: Check },
  available: { label: 'Disponível', icon: Play },
  pending: { label: 'Pendente', icon: Circle },
  blocked: { label: 'Bloqueado', icon: LockKeyhole },
  error: { label: 'Atenção', icon: AlertCircle },
} satisfies Record<PipelineStatus, { label: string; icon: typeof Check }>

export function StatusBadge({ status }: { status: PipelineStatus }) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon

  return (
    <span className={`status-badge ${status}`}>
      <Icon size={12} aria-hidden="true" />
      {config.label}
    </span>
  )
}
