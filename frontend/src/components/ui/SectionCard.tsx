import type { ReactNode } from 'react'

export function SectionCard({
  title,
  description,
  action,
  children,
  variant = 'default',
  className = '',
}: {
  title: string
  description?: string
  action?: ReactNode
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  className?: string
}) {
  return (
    <section className={`section-card ${variant} ${className}`.trim()}>
      <header className="section-card-header">
        <div>
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </div>
        {action}
      </header>
      <div className="section-card-body">{children}</div>
    </section>
  )
}
