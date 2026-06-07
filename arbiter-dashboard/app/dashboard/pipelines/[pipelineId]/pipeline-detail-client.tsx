"use client";

import { useRouter } from 'next/navigation';
import { useState } from "react";
import { DagGraph } from "@/components/dag-graph";
import { StatusBadge } from "@/components/status-badge";
import { SourceBadge } from "@/components/source-badge";
import { AlertList } from "@/components/alert-list";
import Link from "next/link";
import { Button } from "@/components/ui/button-arbiter";
import type { Pipeline, PipelineRun, Alert, TaskInstance } from "@/lib/types";

function Tabs({ active, onTab, tabs }: { active: string; onTab: (v: string) => void; tabs: string[] }) {
  return (
    <div style={{
      display: 'flex', gap: 0,
      borderBottom: '1px solid var(--border)',
      marginBottom: 24,
    }}>
      {tabs.map(t => (
        <button key={t} onClick={() => onTab(t)} style={{
          padding: '10px 18px',
          fontSize: 13, fontWeight: active === t ? 600 : 400,
          color: active === t ? 'var(--text)' : 'var(--text-muted)',
          background: 'transparent', border: 'none',
          borderBottom: active === t ? '2px solid var(--accent)' : '2px solid transparent',
          marginBottom: -1,
          transition: 'all var(--duration-fast) var(--ease)',
          letterSpacing: '0.01em',
          fontFamily: "'DM Sans', sans-serif",
        }}>{t}</button>
      ))}
    </div>
  );
}

export default function PipelineDetailClient({
  pipeline,
  runs,
  alerts,
  tasks,
  token,
}: {
  pipeline: Pipeline;
  runs: PipelineRun[];
  alerts: Alert[];
  tasks: TaskInstance[];
  token?: string;
}) {
  const [tab, setTab] = useState("Graph");

  const nodes = (pipeline.dag_definition?.nodes ?? []).map((n) => ({ ...n, status: tasks.find((t) => t.task_id === n.id)?.status ?? undefined }));
  const edges = pipeline.dag_definition?.edges ?? [];
  const hasDag = pipeline.dag_definition != null && (pipeline.dag_definition.nodes?.length ?? 0) > 0;
  const taskDetails = tasks.map((t) => ({
    task_id: t.task_id,
    status: t.status,
    duration_ms: t.duration_ms,
    try_number: t.try_number,
    error_message: t.error_message,
  }));

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700, fontSize: 22,
          color: 'var(--text)', letterSpacing: '-0.3px',
          marginBottom: 8,
        }}>{pipeline.name}</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
          <StatusBadge status={pipeline.last_run_status} />
          <SourceBadge source={pipeline.source} />
        </div>
      </div>

      <Tabs active={tab} onTab={setTab} tabs={["Graph", "History", "Alerts"]} />

      {tab === "Graph" && (
        <div className="animate-slide-up" style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)',
          overflow: 'hidden',
        }}>
          {hasDag ? (
            <DagGraph nodes={nodes as any} edges={edges as any} tasks={taskDetails as any} />
          ) : (
            <div style={{ display: 'flex', height: 400, alignItems: 'center', justifyContent: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
              No DAG definition yet.
            </div>
          )}
        </div>
      )}

      {tab === "History" && (
        <div className="animate-slide-up" style={{
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
            <span>Run</span>
            <span>Status</span>
            <span>Started</span>
            <span>Duration</span>
            <span></span>
          </div>
          {runs.length === 0 ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No runs yet.
            </div>
          ) : (
            runs.map((run) => (
              <div key={run.id} style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr 1fr 1fr 80px',
                padding: '14px 20px',
                borderBottom: '1px solid var(--border)',
                alignItems: 'center',
                transition: 'background var(--duration-fast) var(--ease)',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-surface)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                <div style={{ fontSize: 13, fontFamily: "'JetBrains Mono', monospace", color: 'var(--text)' }}>
                  {run.run_id.substring(0, 12)}...
                </div>
                <StatusBadge status={run.status} />
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {new Date(run.started_at).toLocaleString()}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {run.duration_ms ? `${run.duration_ms} ms` : '—'}
                </div>
                <Link href={`/dashboard/runs/${run.id}`}>
                  <Button>View run</Button>
                </Link>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "Alerts" && (
        <div className="animate-slide-up" style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)',
          padding: 20,
        }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16 }}>
            Pipeline Alerts
          </div>
          <AlertList alerts={alerts} token={token} />
        </div>
      )}
    </div>
  );
}
