'use client'
import { usePathname } from 'next/navigation'
import { useEffect, useState, ReactNode } from 'react'

export function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const [show, setShow] = useState(false)

  useEffect(() => {
    setShow(false)
    const t = setTimeout(() => setShow(true), 20)
    return () => clearTimeout(t)
  }, [pathname])

  return (
    <div style={{
      opacity: show ? 1 : 0,
      transform: show ? 'translateY(0)' : 'translateY(8px)',
      transition: `opacity ${show ? '350ms' : '0ms'} var(--ease),
                   transform ${show ? '350ms' : '0ms'} var(--ease)`,
    }}>
      {children}
    </div>
  )
}
