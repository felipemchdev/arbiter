interface SkeletonProps {
  width?: string | number
  height?: string | number
  borderRadius?: string
  className?: string
}

export function Skeleton({ width = '100%', height = 16, borderRadius = 'var(--r-md)', className }: SkeletonProps) {
  return (
    <div className={`skeleton ${className ?? ''}`} style={{
      width, height: typeof height === 'number' ? height + 'px' : height,
      borderRadius,
    }} />
  )
}

export function SkeletonCard() {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)', padding: 20,
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <Skeleton height={12} width="40%" />
      <Skeleton height={28} width="60%" />
      <Skeleton height={10} width="30%" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16,
      padding: '14px 20px', borderBottom: '1px solid var(--border)',
    }}>
      <Skeleton height={10} width="20%" />
      <Skeleton height={10} width="15%" />
      <Skeleton height={10} width="25%" />
      <Skeleton height={10} width="12%" />
    </div>
  )
}
