'use client'

import { useEffect } from 'react'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('dashboard_error', error.digest ?? error.message)
  }, [error])

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '64px 24px' }}>
      <div
        style={{
          maxWidth: 460,
          width: '100%',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)',
          padding: 28,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            margin: '0 auto 16px',
            borderRadius: 'var(--r-pill)',
            background: 'var(--failed-bg)',
            color: 'var(--failed)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 20,
            fontWeight: 700,
          }}
        >
          !
        </div>
        <h2
          style={{
            fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
            fontWeight: 700,
            fontSize: 18,
            color: 'var(--text)',
            marginBottom: 8,
          }}
        >
          Something went wrong
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20, lineHeight: 1.6 }}>
          We could not load this part of the dashboard. Try again, and if it keeps happening check
          that the API is reachable.
        </p>
        <button
          type="button"
          onClick={reset}
          style={{
            background: 'var(--accent)',
            color: 'var(--accent-text)',
            border: 'none',
            borderRadius: 'var(--r-md)',
            padding: '10px 20px',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Try again
        </button>
      </div>
    </div>
  )
}
