type StatusType =
  | 'success' | 'failed' | 'running' | 'skipped' | 'upstream_failed'
  | 'airflow' | 'azure_function' | 'sdk'
  | 'owner' | 'viewer'

const STATUS_MAP: Record<StatusType, { label: string; color: string; bg: string; pulse?: boolean }> = {
  success:         { label: 'Success',         color: '#22C55E', bg: 'rgba(34,197,94,0.10)'    },
  failed:          { label: 'Failed',          color: '#EF4444', bg: 'rgba(239,68,68,0.10)'    },
  running:         { label: 'Running',         color: '#F59E0B', bg: 'rgba(245,158,11,0.10)', pulse: true },
  skipped:         { label: 'Skipped',         color: '#64748B', bg: 'rgba(100,116,139,0.10)' },
  upstream_failed: { label: 'Upstream Failed', color: '#F97316', bg: 'rgba(249,115,22,0.10)'  },
  airflow:         { label: 'Airflow',         color: '#38BDF8', bg: 'rgba(56,189,248,0.10)'  },
  azure_function:  { label: 'Azure Function',  color: '#818CF8', bg: 'rgba(129,140,248,0.10)' },
  sdk:             { label: 'SDK',             color: '#94A3B8', bg: 'rgba(148,163,184,0.10)' },
  owner:           { label: 'Owner',           color: '#C7FF8F', bg: 'rgba(199,255,143,0.10)' },
  viewer:          { label: 'View Only',       color: '#94A3B8', bg: 'rgba(148,163,184,0.10)' },
}

export function StatusBadge({ status, size = 'md' }: { status: string | null | undefined; size?: 'sm' | 'md' }) {
  const s = STATUS_MAP[(status || 'skipped') as StatusType] ?? {
    label: status, color: '#94A3B8', bg: 'rgba(148,163,184,0.10)',
  }
  const fontSize = size === 'sm' ? 11 : 12
  const padding  = size === 'sm' ? '2px 7px' : '3px 9px'

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding, borderRadius: 'var(--r-sm)',
      fontSize, fontWeight: 500,
      fontFamily: "'DM Sans', sans-serif",
      color: s.color, background: s.bg,
      border: `1px solid ${s.color}1A`,
      whiteSpace: 'nowrap',
      letterSpacing: '0.01em',
    }}>
      <span style={{
        position: 'relative',
        width: 5, height: 5, borderRadius: '50%',
        background: s.color, flexShrink: 0,
      }}>
        {s.pulse && (
          <span style={{
            position: 'absolute', inset: -2,
            borderRadius: '50%', background: s.color,
            animation: 'ping 1.4s cubic-bezier(0,0,0.2,1) infinite',
            opacity: 0.4,
          }} />
        )}
      </span>
      {s.label}
    </span>
  )
}
