import { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  padding?: number | string
  hoverable?: boolean
  accent?: boolean
}

export function Card({ children, padding = 20, hoverable = false, accent = false, style, ...props }: CardProps) {
  return (
    <div
      {...props}
      style={{
        background: 'var(--bg-card)',
        border: accent
          ? '1px solid var(--border-accent)'
          : '1px solid var(--border)',
        borderRadius: 'var(--r-lg)',
        padding: typeof padding === 'number' ? padding + 'px' : padding,
        transition: hoverable ? `all var(--duration-base) var(--ease)` : undefined,
        ...style,
      }}
      onMouseEnter={hoverable ? e => {
        (e.currentTarget as HTMLElement).style.background = 'var(--bg-card-hover)'
        ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border-hover)'
      } : undefined}
      onMouseLeave={hoverable ? e => {
        (e.currentTarget as HTMLElement).style.background = 'var(--bg-card)'
        ;(e.currentTarget as HTMLElement).style.borderColor = accent ? 'var(--border-accent)' : 'var(--border)'
      } : undefined}
    >
      {children}
    </div>
  )
}
