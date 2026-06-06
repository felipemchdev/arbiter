'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useSession, signOut } from 'next-auth/react'
import { ReactNode, useEffect, useState } from 'react'
import { ArbiterLogo } from '@/components/logo/logo'
import { PageTransition } from '@/components/page-transition'
import { ThemeToggle } from '@/components/theme-toggle'

const NAV_ITEMS = [
  { href: '/dashboard',            label: 'Overview'  },
  { href: '/dashboard/pipelines',  label: 'Pipelines' },
  { href: '/dashboard/alerts',     label: 'Alerts'    },
]

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const { data: session } = useSession()
  const role = (session as any)?.role ?? 'viewer'
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>

      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        height: 52,
        background: scrolled ? 'var(--bg-overlay)' : 'transparent',
        backdropFilter: scrolled ? 'blur(16px)' : 'none',
        borderBottom: `1px solid ${scrolled ? 'var(--border)' : 'transparent'}`,
        transition: 'all var(--duration-base) var(--ease)',
        display: 'flex', alignItems: 'center',
        padding: '0 24px',
        gap: 32,
      }}>

        <Link href="/dashboard" style={{ textDecoration: 'none', flexShrink: 0 }}>
          <ArbiterLogo size="md" />
        </Link>

        <nav style={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
          {NAV_ITEMS.map(({ href, label }) => {
            const active = href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname.startsWith(href)
            return (
              <Link key={href} href={href} style={{ textDecoration: 'none' }}>
                <div style={{
                  padding: '5px 12px',
                  borderRadius: 'var(--r-md)',
                  fontSize: 13, fontWeight: active ? 600 : 400,
                  color: active ? 'var(--text)' : 'var(--text-muted)',
                  background: active ? 'var(--bg-surface-hover)' : 'transparent',
                  border: active ? '1px solid var(--border)' : '1px solid transparent',
                  transition: 'all var(--duration-fast) var(--ease)',
                  letterSpacing: '0.01em',
                }}
                onMouseEnter={e => {
                  if (!active) {
                    ;(e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)'
                    ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-surface)'
                  }
                }}
                onMouseLeave={e => {
                  if (!active) {
                    ;(e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'
                    ;(e.currentTarget as HTMLElement).style.background = 'transparent'
                  }
                }}>
                  {label}
                </div>
              </Link>
            )
          })}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>

          {role === 'viewer' && (
            <span style={{
              fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              padding: '3px 8px',
            }}>
              View only
            </span>
          )}

          <ThemeToggle />

          <button
            onClick={() => signOut({ callbackUrl: '/login' })}
            style={{
              background: 'transparent', border: 'none',
              color: 'var(--text-muted)', fontSize: 12,
              fontFamily: "'DM Sans', sans-serif",
              padding: '5px 10px', borderRadius: 'var(--r-md)',
              transition: 'color var(--duration-fast) var(--ease)',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            sign out
          </button>
        </div>
      </header>

      <main style={{ padding: '32px 24px', maxWidth: 1280, margin: '0 auto' }}>
        <PageTransition>{children}</PageTransition>
      </main>

    </div>
  )
}
