import { StatusBadge } from "@/components/status-badge";
import { SourceBadge } from "@/components/source-badge";
import { Button } from "@/components/ui/button-arbiter";
import { authOptions } from "@/lib/auth";
import { getPipelines } from "@/lib/api";
import { getServerSession } from "next-auth";
import Link from "next/link";

export default async function PipelinesPage() {
  const session = await getServerSession(authOptions);
  const pipelines = await getPipelines(session?.accessToken);

  return (
    <div className="space-y-6">
      <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{
            fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
            fontWeight: 700, fontSize: 22,
            color: 'var(--text)', letterSpacing: '-0.3px',
            marginBottom: 4,
          }}>Pipelines</h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            {pipelines.length} pipelines monitored
          </p>
        </div>
      </div>

      <div className="animate-fade-in" style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-lg)',
        overflow: 'hidden',
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr 1fr 1fr 80px',
          padding: '10px 20px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border)',
          fontSize: 11, fontWeight: 600,
          color: 'var(--text-muted)',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}>
          <span>Pipeline</span>
          <span>Source</span>
          <span>Status</span>
          <span>Last run</span>
          <span></span>
        </div>

        {pipelines.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            No pipelines found.
          </div>
        ) : (
          pipelines.map(p => (
            <div key={p.id} style={{
              display: 'grid',
              gridTemplateColumns: '2fr 1fr 1fr 1fr 80px',
              padding: '14px 20px',
              borderBottom: '1px solid var(--border)',
              alignItems: 'center',
              transition: 'background var(--duration-fast) var(--ease)',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-surface)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text)', marginBottom: 2 }}>
                  {p.name}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
                  {p.id.slice(0, 8)}...
                </div>
              </div>
              <SourceBadge source={p.source} />
              <StatusBadge status={p.last_run_status} />
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {p.last_run_at ? new Date(p.last_run_at).toLocaleString() : '—'}
              </div>
              <Link href={`/dashboard/pipelines/${p.id}`}>
                <Button>View</Button>
              </Link>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
