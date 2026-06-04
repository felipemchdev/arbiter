"use client";

import { useState } from "react";
import { DagGraph } from "@/components/dag-graph";
import { StatusBadge } from "@/components/status-badge";
import { SourceBadge } from "@/components/source-badge";
import { AlertList } from "@/components/alert-list";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import type { Pipeline, PipelineRun, Alert, TaskInstance } from "@/lib/types";

function Tabs({ active, onTab, tabs }: { active: string; onTab: (v: string) => void; tabs: string[] }) {
  return (
    <div className="flex gap-6 border-b border-[var(--border)]">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTab(tab)}
          className={`px-1 py-3 text-sm font-medium transition font-sans ${
            active === tab
              ? "border-b-2 border-[var(--accent-blue)] text-[var(--accent-blue)]"
              : "border-b-2 border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)]"
          }`}
        >
          {tab}
        </button>
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
  const [tab, setTab] = useState("Grafo");

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
      <div>
        <div className="text-3xl font-semibold">{pipeline.name}</div>
        <div className="mt-2 flex items-center gap-3">
          <StatusBadge status={pipeline.last_run_status} />
          <SourceBadge source={pipeline.source} />
        </div>
      </div>

      <Tabs active={tab} onTab={setTab} tabs={["Grafo", "Histórico", "Alertas"]} />

      {tab === "Grafo" && (
        <Card>
          <CardContent className="p-0">
            {hasDag ? (
              <DagGraph nodes={nodes as any} edges={edges as any} tasks={taskDetails as any} />
            ) : (
              <div className="flex h-[400px] items-center justify-center text-sm text-[var(--text-muted)]">
                No DAG definition yet.
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "Histórico" && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Run</TableHeader>
                  <TableHeader>Status</TableHeader>
                  <TableHeader>Started</TableHeader>
                  <TableHeader>Duration</TableHeader>
                  <TableHeader>Action</TableHeader>
                </TableRow>
              </TableHead>
              <TableBody>
                {runs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-[var(--text-muted)] py-8">
                      No runs yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell className="font-mono text-xs">{run.run_id.substring(0, 12)}...</TableCell>
                      <TableCell>
                        <StatusBadge status={run.status} />
                      </TableCell>
                      <TableCell className="text-[var(--text-muted)]">
                        {new Date(run.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-[var(--text-muted)]">
                        {run.duration_ms ? `${run.duration_ms} ms` : "—"}
                      </TableCell>
                      <TableCell>
                        <Link href={`/dashboard/runs/${run.id}`}>
                          <Button>Ver run</Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === "Alertas" && (
        <Card>
          <CardHeader>
            <div className="text-lg font-semibold">Pipeline Alerts</div>
          </CardHeader>
          <CardContent>
            <AlertList alerts={alerts} token={token} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
