"use client";
import { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
  loading?: boolean
}

export function Button({
  variant = 'secondary', size = 'md', children, loading, style, ...props
}: ButtonProps) {
  const sizes = {
    sm: { height: 30, padding: '0 12px', fontSize: 12 },
    md: { height: 36, padding: '0 16px', fontSize: 13 },
    lg: { height: 42, padding: '0 20px', fontSize: 14 },
  }
  const s = sizes[size]

  const variants = {
    primary:   { background: 'var(--accent)', color: 'var(--accent-text)', border: 'none' },
    secondary: { background: 'transparent',  color: 'var(--text-secondary)', border: '1px solid var(--border)' },
    ghost:     { background: 'transparent',  color: 'var(--text-muted)',     border: 'none' },
    danger:    { background: 'transparent',  color: 'var(--failed)',         border: '1px solid rgba(239,68,68,0.20)' },
  }
  const v = variants[variant]

  return (
    <button
      {...props}
      style={{
        height: s.height,
        padding: s.padding,
        fontSize: s.fontSize,
        fontWeight: 500,
        fontFamily: "'DM Sans', sans-serif",
        borderRadius: 'var(--r-md)',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        transition: `all var(--duration-base) var(--ease)`,
        opacity: props.disabled ? 0.45 : 1,
        letterSpacing: '0.01em',
        ...v,
        ...style,
      }}
      onMouseEnter={e => {
        if (props.disabled) return
        if (variant === 'primary') {
          (e.currentTarget as HTMLElement).style.background = 'var(--accent-hover)'
        } else {
          (e.currentTarget as HTMLElement).style.background = 'var(--bg-surface-hover)'
        }
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.background = v.background
      }}
    >
      {loading ? <span style={{ width: 14, height: 14, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} /> : children}
    </button>
  )
}
