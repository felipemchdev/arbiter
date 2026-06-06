import { Card, CardContent } from "@/components/ui/card";
import type { TaskInstance } from "@/lib/types";

export function RunTimeline({ tasks }: { tasks: TaskInstance[] }) {
  const first = tasks[0]?.started_at ? new Date(tasks[0].started_at).getTime() : Date.now();
  const last = tasks.at(-1)?.finished_at ? new Date(tasks.at(-1)?.finished_at || "").getTime() : Date.now();
  const total = Math.max(last - first, 1);

  const getStatusColor = (status: string) => {
    if (status === "success") return "var(--success)";
    if (status === "failed") return "var(--failed)";
    if (status === "running") return "var(--running)";
    return "var(--skipped)";
  };

  return (
    <div className="animate-slide-up" style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)',
      padding: '20px 20px 16px',
      marginBottom: 24,
      overflowX: 'auto',
    }}>
      <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16 }}>
        Task timeline
      </div>
      <div className="space-y-3">
        {tasks.map((task) => {
          const start = new Date(task.started_at).getTime();
          const finish = task.finished_at ? new Date(task.finished_at).getTime() : start + (task.duration_ms ?? 0);
          const left = ((start - first) / total) * 100;
          const width = Math.max(((finish - start) / total) * 100, 1);
          return (
            <div key={task.id} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 0 }}>
              <div style={{ width: 120, fontSize: 11, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace", flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {task.task_id}
              </div>
              <div style={{ flex: 1, height: 8, background: 'var(--bg-surface)', borderRadius: 4, position: 'relative', minWidth: 200 }}>
                <div style={{
                  position: 'absolute', left: `${left}%`, width: `${Math.max(width, 1)}%`,
                  height: '100%', borderRadius: 4,
                  background: getStatusColor(task.status),
                  opacity: 0.85,
                  transition: 'width var(--duration-slow) var(--ease)',
                }} />
              </div>
              <div style={{ width: 48, fontSize: 11, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace", flexShrink: 0, textAlign: 'right' }}>
                {task.duration_ms ? `${(task.duration_ms / 1000).toFixed(1)}s` : '—'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
