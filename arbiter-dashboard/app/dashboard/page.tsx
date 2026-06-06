import { AlertList } from "@/components/alert-list";
import { MetricsCard } from "@/components/metrics-card";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { authOptions } from "@/lib/auth";
import { getAlerts, getMetrics } from "@/lib/api";
import { getServerSession } from "next-auth";
import { RunsChart } from "@/components/runs-chart";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;
  const metrics = (await getMetrics(token)) ?? { runs_today: 0, failed_today: 0, active_pipelines: 0, avg_duration_ms: 0 };
  const alerts = await getAlerts(token);

  return (
    <div className="space-y-8">
      <div className="animate-fade-in" style={{ marginBottom: 32 }}>
        <h1 style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700, fontSize: 22,
          color: 'var(--text)', letterSpacing: '-0.3px',
          marginBottom: 4,
        }}>Overview</h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Pipeline health at a glance
        </p>
      </div>

      <div className="animate-slide-up delay-1" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 12, marginBottom: 28,
      }}>
        {([
          { label: 'Runs Today', value: metrics.runs_today },
          { label: 'Failures Today', value: metrics.failed_today },
          { label: 'Active Pipelines', value: metrics.active_pipelines },
          { label: 'Avg Duration', value: `${Math.round(metrics.avg_duration_ms)} ms` },
        ]).map(({ label, value }) => (
          <div key={label} style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r-lg)',
            padding: '18px 20px',
            transition: 'all var(--duration-base) var(--ease)',
          }}
          onMouseEnter={e => {
            ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-card-hover)'
            ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border-hover)'
          }}
          onMouseLeave={e => {
            ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-card)'
            ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'
          }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 10 }}>
              {label}
            </div>
            <div style={{
              fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
              fontWeight: 700, fontSize: 32,
              color: 'var(--text)', letterSpacing: '-0.5px', lineHeight: 1,
              marginBottom: 6,
            }}>
              {value}
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.35fr_0.9fr]">
        <div className="animate-slide-up delay-2" style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)',
          padding: '20px 20px 12px',
          marginBottom: 28,
        }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16 }}>
            Runs / 7 days
          </div>
          <RunsChart runsToday={metrics.runs_today} />
        </div>

        <div className="animate-slide-up delay-3" style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)',
          padding: 20,
          marginBottom: 28,
        }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16 }}>
            Active alerts
          </div>
          <AlertList alerts={alerts} token={token} />
        </div>
      </div>
    </div>
  );
}
