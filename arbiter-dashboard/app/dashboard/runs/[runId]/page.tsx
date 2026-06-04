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
      <div>
        <div className="text-3xl font-semibold font-display text-[var(--text-primary)]">{run.run_id}</div>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)] font-sans">
          <StatusBadge status={run.status} />
          <span>{run.duration_ms ? `${run.duration_ms} ms` : "—"}</span>
          {pipeline && (
            <span className="flex items-center gap-2">
              Pipeline:{" "}
              <Link href={`/dashboard/pipelines/${pipeline.id}`} className="text-[var(--accent-blue)] hover:underline">
                {pipeline.name}
              </Link>
            </span>
          )}
        </div>
      </div>

      <RunTimeline tasks={tasks} />

      <Card>
        <CardHeader>
          <div className="text-lg font-semibold font-display text-[var(--text-primary)]">Task Instances</div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Task ID</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Duration</TableHeader>
                <TableHeader>Try #</TableHeader>
                <TableHeader>Error</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-[var(--text-muted)] py-8 font-sans">
                    No task instances.
                  </TableCell>
                </TableRow>
              ) : (
                tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium font-sans">{task.task_id}</TableCell>
                    <TableCell>
                      <StatusBadge status={task.status} />
                    </TableCell>
                    <TableCell className="text-[var(--text-muted)] font-sans">
                      {task.duration_ms ? `${task.duration_ms} ms` : "—"}
                    </TableCell>
                    <TableCell className="text-[var(--text-muted)] font-sans">{task.try_number}</TableCell>
                    <TableCell className="max-w-[300px]">
                      {task.error_message ? (
                        <details className="cursor-pointer">
                          <summary className="truncate text-[var(--status-failed)] font-medium font-sans">Error details</summary>
                          <div className="mt-2 whitespace-pre-wrap rounded-[10px] border border-[var(--status-failed)] bg-[rgba(239,68,68,0.08)] p-4 text-xs text-[var(--status-failed)] font-mono">
                            {task.error_message}
                          </div>
                        </details>
                      ) : (
                        <span className="text-[var(--text-muted)] font-sans">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
