'use client'
import { useState, ReactNode } from 'react'

export function Tooltip({ content, children }: { content: string; children: ReactNode }) {
  const [visible, setVisible] = useState(false)

  return (
    <div
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: '50%',
          transform: 'translateX(-50%)',
          background: 'var(--text)', color: 'var(--bg)',
          fontSize: 12, fontWeight: 500,
          padding: '5px 10px', borderRadius: 'var(--r-sm)',
          whiteSpace: 'nowrap', zIndex: 1000,
          pointerEvents: 'none',
          animation: 'scale-in 150ms var(--ease) both',
        }}>
          {content}
          <div style={{
            position: 'absolute', top: '100%', left: '50%',
            transform: 'translateX(-50%)',
            borderLeft: '4px solid transparent',
            borderRight: '4px solid transparent',
            borderTop: `4px solid var(--text)`,
          }} />
        </div>
      )}
    </div>
  )
}
