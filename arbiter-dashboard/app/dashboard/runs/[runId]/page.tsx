import { RunTimeline } from "@/components/run-timeline";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { authOptions } from "@/lib/auth";
import { getRun, getRunTasks, getPipeline } from "@/lib/api";
import { getServerSession } from "next-auth";
import { notFound } from "next/navigation";
import Link from "next/link";

export default async function RunDetailPage({ params }: { params: { runId: string } }) {
  const { runId } = params;
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;
  const run = await getRun(runId, token);
  if (!run) {
    notFound();
  }
  const pipeline = await getPipeline(run.pipeline_id, token);
  const tasks = await getRunTasks(runId, token);

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 500, fontSize: 18,
          color: 'var(--text)',
          marginBottom: 8,
        }}>{run.run_id}</h1>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 12, fontSize: 13, color: 'var(--text-muted)' }}>
          <StatusBadge status={run.status} />
          <span>{run.duration_ms ? `${run.duration_ms} ms` : '—'}</span>
          {pipeline && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              Pipeline:{' '}
              <Link href={`/dashboard/pipelines/${pipeline.id}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}
                onMouseEnter={e => (e.currentTarget.style.textDecoration = 'underline')}
                onMouseLeave={e => (e.currentTarget.style.textDecoration = 'none')}>
                {pipeline.name}
              </Link>
            </span>
          )}
        </div>
      </div>

      <RunTimeline tasks={tasks} />

      <div className="animate-slide-up" style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-lg)',
        overflow: 'hidden',
      }}>
        <div style={{
          padding: '10px 20px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border)',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr 80px 60px 40px',
            fontSize: 11, fontWeight: 600,
            color: 'var(--text-muted)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>
            <span>Task ID</span>
            <span>Status</span>
            <span>Duration</span>
            <span>Try #</span>
            <span></span>
          </div>
        </div>

        {tasks.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            No task instances.
          </div>
        ) : (
          tasks.map((task) => (
            <div key={task.id}>
              <div style={{
                display: 'grid', gridTemplateColumns: '2fr 1fr 80px 60px 40px',
                padding: '12px 20px', borderBottom: '1px solid var(--border)',
                alignItems: 'center',
                transition: 'background var(--duration-fast) var(--ease)',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-surface)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                <div style={{ fontSize: 13, fontWeight: 500, fontFamily: "'JetBrains Mono', monospace", color: 'var(--text)' }}>
                  {task.task_id}
                </div>
                <StatusBadge status={task.status} size="sm" />
                <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
                  {task.duration_ms ? `${(task.duration_ms/1000).toFixed(1)}s` : '—'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{`×${task.try_number}`}</div>
                {task.error_message ? (
                  <details style={{ cursor: 'pointer' }}>
                    <summary style={{ color: 'var(--failed)', fontSize: 11, fontWeight: 500, fontFamily: "'DM Sans', sans-serif", listStyle: 'none' }}>
                      {String.fromCharCode(9660)}
                    </summary>
                  </details>
                ) : (
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{'—'}</span>
                )}
              </div>
              {task.error_message && (
                <div style={{
                  padding: '12px 20px',
                  background: 'rgba(239,68,68,0.04)',
                  borderBottom: '1px solid var(--border)',
                  borderLeft: '3px solid var(--failed)',
                }}>
                  <pre style={{
                    fontSize: 11, color: 'rgba(239,68,68,0.80)',
                    fontFamily: "'JetBrains Mono', monospace",
                    lineHeight: 1.7, whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0,
                  }}>{task.error_message}</pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
