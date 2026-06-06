'use client'
import { ArbiterSymbol } from '@/components/logo/symbol'
import { ArbiterLettermark } from '@/components/logo/lettermark'
import { signIn } from 'next-auth/react'
import { useState, useEffect } from 'react'

type Status = 'idle' | 'loading' | 'error' | 'success'

export default function LoginPage() {
  const [user, setUser]         = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw]     = useState(false)
  const [status, setStatus]     = useState<Status>('idle')
  const [date, setDate]         = useState('')

  useEffect(() => {
    setDate(new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }))
  }, [])

  const handleLogin = async () => {
    if (!user || !password || status === 'loading') return
    setStatus('loading')
    const res = await signIn('credentials', { username: user, password, redirect: false })
    if (res?.error) {
      setStatus('error')
      setTimeout(() => setStatus('idle'), 2200)
    } else {
      setStatus('success')
      window.location.href = '/dashboard'
    }
  }

  const isError   = status === 'error'
  const isLoading = status === 'loading'

  return (
    <main style={{
      minHeight: '100vh',
      background: 'var(--bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        background: `
          radial-gradient(ellipse 55% 45% at 75% 15%, rgba(199,255,143,0.06) 0%, transparent 65%),
          radial-gradient(ellipse 40% 60% at 25% 85%, rgba(199,255,143,0.03) 0%, transparent 60%)
        `,
      }} />

      <div style={{ position: 'absolute', top: 24, left: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
        <ArbiterSymbol size={18} />
        <span style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700, fontSize: 14,
          color: 'var(--text)', letterSpacing: '-0.3px',
        }}>
          Arbiter<sup style={{ fontSize: '0.44em', verticalAlign: 'super', marginLeft: 1, color: 'var(--accent)' }}>●</sup>
        </span>
      </div>

      <div style={{
        position: 'absolute', top: 20, right: 20,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-pill)',
        padding: '6px 16px',
        fontSize: 12, color: 'var(--text-secondary)',
        fontWeight: 500,
      }}>
        {date}
      </div>

      <div className="animate-fade-in" style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0,
        width: '100%', maxWidth: 380, padding: '0 20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
          <ArbiterLettermark size={44} />
          <span style={{
            fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
            fontWeight: 700, fontSize: 30,
            color: 'var(--text)', letterSpacing: '-0.5px', lineHeight: 1,
          }}>
            Arbiter<sup style={{ fontSize: '0.42em', verticalAlign: 'super', marginLeft: 2, color: 'var(--accent)' }}>●</sup>
          </span>
        </div>

        <p style={{
          fontSize: 13, color: 'var(--text-muted)',
          marginBottom: 28, textAlign: 'center', lineHeight: 1.5,
        }}>
          Pipeline observability
        </p>

        <div style={{
          width: '100%',
          background: 'var(--bg-card)',
          border: `1px solid ${isError ? 'rgba(239,68,68,0.30)' : 'var(--border)'}`,
          borderRadius: 'var(--r-xl)',
          padding: '28px 28px 24px',
          transition: 'border-color var(--duration-base) var(--ease)',
          backdropFilter: 'blur(20px)',
        }}>
          <div style={{ marginBottom: 12 }}>
            <input
              type="text"
              placeholder="user"
              value={user}
              onChange={e => setUser(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              autoComplete="username"
              style={{
                width: '100%', height: 42,
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--r-md)',
                color: 'var(--text)',
                fontFamily: "'DM Sans', sans-serif",
                fontSize: 14, padding: '0 14px',
                outline: 'none',
                transition: 'border-color var(--duration-fast) var(--ease)',
              }}
              onFocus={e => {
                e.target.style.borderColor = 'var(--border-focus)'
                e.target.style.boxShadow = '0 0 0 3px var(--accent-muted)'
              }}
              onBlur={e => {
                e.target.style.borderColor = 'var(--border)'
                e.target.style.boxShadow = 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: 16, position: 'relative' }}>
            <input
              type={showPw ? 'text' : 'password'}
              placeholder="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              autoComplete="current-password"
              style={{
                width: '100%', height: 42,
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--r-md)',
                color: 'var(--text)',
                fontFamily: "'DM Sans', sans-serif",
                fontSize: 14, padding: '0 42px 0 14px',
                outline: 'none',
                transition: 'border-color var(--duration-fast) var(--ease)',
              }}
              onFocus={e => {
                e.target.style.borderColor = 'var(--border-focus)'
                e.target.style.boxShadow = '0 0 0 3px var(--accent-muted)'
              }}
              onBlur={e => {
                e.target.style.borderColor = 'var(--border)'
                e.target.style.boxShadow = 'none'
              }}
            />
            <button
              type="button"
              onClick={() => setShowPw(v => !v)}
              style={{
                position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none',
                color: 'var(--text-muted)', padding: 4, lineHeight: 0,
                transition: 'color var(--duration-fast) var(--ease)',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
              aria-label={showPw ? 'Hide password' : 'Show password'}
            >
              {showPw ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
                  <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              )}
            </button>
          </div>

          <button
            onClick={handleLogin}
            disabled={isLoading || status === 'success'}
            style={{
              width: '100%', height: 42,
              background: isError ? 'rgba(239,68,68,0.15)' : 'var(--accent)',
              border: isError ? '1px solid rgba(239,68,68,0.30)' : 'none',
              borderRadius: 'var(--r-md)',
              color: isError ? 'var(--failed)' : 'var(--accent-text)',
              fontFamily: "'DM Sans', sans-serif",
              fontSize: 13, fontWeight: 700,
              letterSpacing: '0.02em',
              transition: 'all var(--duration-base) var(--ease)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              opacity: isLoading ? 0.7 : 1,
            }}
            onMouseEnter={e => {
              if (isError || isLoading) return
              ;(e.currentTarget as HTMLElement).style.background = 'var(--accent-hover)'
            }}
            onMouseLeave={e => {
              if (isError) return
              ;(e.currentTarget as HTMLElement).style.background = 'var(--accent)'
            }}
          >
            {isLoading ? (
              <span style={{
                width: 14, height: 14,
                border: '2px solid var(--accent-text)',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 0.7s linear infinite',
                display: 'inline-block',
              }} />
            ) : isError ? (
              'Invalid credentials'
            ) : (
              'sign-in'
            )}
          </button>
        </div>

        <p style={{
          fontSize: 12, color: 'var(--text-muted)',
          marginTop: 16, textAlign: 'center', lineHeight: 1.6,
        }}>
          Welcome to your new best friend in pipelines observability
        </p>
      </div>
    </main>
  )
}
