'use client'
import { useEffect, useRef } from 'react'

export function CustomCursor() {
  const dot = useRef<HTMLDivElement>(null)
  const ring = useRef<HTMLDivElement>(null)
  const pos = useRef({ x: 0, y: 0 })
  const ringPos = useRef({ x: 0, y: 0 })
  const raf = useRef<number>()

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      pos.current = { x: e.clientX, y: e.clientY }
    }

    const onEnterClickable = () => {
      dot.current?.style.setProperty('transform', 'translate(-50%,-50%) scale(0)')
      ring.current?.style.setProperty('width', '36px')
      ring.current?.style.setProperty('height', '36px')
      ring.current?.style.setProperty('border-color', 'var(--accent)')
    }

    const onLeaveClickable = () => {
      dot.current?.style.setProperty('transform', 'translate(-50%,-50%) scale(1)')
      ring.current?.style.setProperty('width', '20px')
      ring.current?.style.setProperty('height', '20px')
      ring.current?.style.setProperty('border-color', 'rgba(255,255,255,0.5)')
    }

    const loop = () => {
      ringPos.current.x += (pos.current.x - ringPos.current.x) * 0.12
      ringPos.current.y += (pos.current.y - ringPos.current.y) * 0.12
      if (dot.current) {
        dot.current.style.left = pos.current.x + 'px'
        dot.current.style.top  = pos.current.y + 'px'
      }
      if (ring.current) {
        ring.current.style.left = ringPos.current.x + 'px'
        ring.current.style.top  = ringPos.current.y + 'px'
      }
      raf.current = requestAnimationFrame(loop)
    }

    const clickables = () => document.querySelectorAll(
      'a, button, [role="button"], input, select, textarea, [data-cursor="pointer"]'
    )

    document.addEventListener('mousemove', onMove)

    const observer = new MutationObserver(() => {
      clickables().forEach(el => {
        el.addEventListener('mouseenter', onEnterClickable)
        el.addEventListener('mouseleave', onLeaveClickable)
      })
    })
    observer.observe(document.body, { childList: true, subtree: true })
    clickables().forEach(el => {
      el.addEventListener('mouseenter', onEnterClickable)
      el.addEventListener('mouseleave', onLeaveClickable)
    })

    raf.current = requestAnimationFrame(loop)

    return () => {
      document.removeEventListener('mousemove', onMove)
      observer.disconnect()
      if (raf.current) cancelAnimationFrame(raf.current)
    }
  }, [])

  return (
    <>
      <div ref={dot} style={{
        position: 'fixed', pointerEvents: 'none', zIndex: 99999,
        width: 5, height: 5, borderRadius: '50%',
        background: 'var(--accent)',
        transform: 'translate(-50%,-50%)',
        transition: 'transform 150ms var(--ease)',
        mixBlendMode: 'difference',
      }} />
      <div ref={ring} style={{
        position: 'fixed', pointerEvents: 'none', zIndex: 99998,
        width: 20, height: 20, borderRadius: '50%',
        border: '1px solid rgba(255,255,255,0.5)',
        transform: 'translate(-50%,-50%)',
        transition: 'width 200ms var(--ease), height 200ms var(--ease), border-color 200ms var(--ease)',
      }} />
    </>
  )
}
