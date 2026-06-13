import type { ReactNode } from 'react'

export type SkillTagVariant =
  | 'strong'
  | 'partial'
  | 'missing'
  | 'safe'
  | 'warning'
  | 'danger'
  | 'neutral'

export function SkillTag({
  children,
  variant = 'neutral',
}: {
  children: ReactNode
  variant?: SkillTagVariant
}) {
  return <span className={`skill-tag ${variant}`}>{children}</span>
}
