import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, style, ...props }, ref
) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label style={{
          fontSize: 12, fontWeight: 500,
          color: 'var(--text-muted)',
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
        }}>
          {label}
        </label>
      )}
      <input
        ref={ref}
        {...props}
        style={{
          height: 40,
          background: 'var(--bg-surface)',
          border: `1px solid ${error ? 'var(--failed)' : 'var(--border)'}`,
          borderRadius: 'var(--r-md)',
          color: 'var(--text)',
          fontFamily: "'DM Sans', sans-serif",
          fontSize: 14,
          padding: '0 14px',
          width: '100%',
          outline: 'none',
          transition: `border-color var(--duration-fast) var(--ease)`,
          ...style,
        }}
        onFocus={e => {
          e.target.style.borderColor = error ? 'var(--failed)' : 'var(--border-focus)'
          e.target.style.boxShadow = error
            ? '0 0 0 3px rgba(239,68,68,0.10)'
            : '0 0 0 3px var(--accent-muted)'
        }}
        onBlur={e => {
          e.target.style.borderColor = error ? 'var(--failed)' : 'var(--border)'
          e.target.style.boxShadow = 'none'
        }}
      />
      {error && (
        <span style={{ fontSize: 12, color: 'var(--failed)' }}>{error}</span>
      )}
    </div>
  )
})
