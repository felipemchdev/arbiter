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
    const run = await getRun(runId, session?.accessToken);
    if (!run) {
        notFound();
    }
    const pipeline = await getPipeline(run.pipeline_id, session?.accessToken);
    const tasks = await getRunTasks(runId, session?.accessToken);

    return (
        <div className="space-y-6">
            <div>
                <div className="text-3xl font-semibold">{run.run_id}</div>
                <div className="mt-2 flex items-center gap-3 text-sm text-[var(--text-muted)]">
                    <StatusBadge status={run.status} />
                    <span>{run.duration_ms ? `${run.duration_ms} ms` : "—"}</span>
                    {pipeline && (
                        <span className="flex items-center gap-2">
                            Pipeline: <Link href={`/dashboard/pipelines/${pipeline.id}`} className="hover:underline text-[var(--primary)]">{pipeline.name}</Link>
                        </span>
                    )}
                </div>
            </div>

            <RunTimeline tasks={tasks} />

            <Card>
                <CardHeader>
                    <div className="text-lg font-semibold">Tasks</div>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeader>Task</TableHeader>
                                <TableHeader>Status</TableHeader>
                                <TableHeader>Duration</TableHeader>
                                <TableHeader>Try</TableHeader>
                                <TableHeader>Error</TableHeader>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {tasks.map((task) => (
                                <TableRow key={task.id}>
                                    <TableCell>{task.task_id}</TableCell>
                                    <TableCell><StatusBadge status={task.status} /></TableCell>
                                    <TableCell>{task.duration_ms ? `${task.duration_ms} ms` : "—"}</TableCell>
                                    <TableCell>{task.try_number}</TableCell>
                                    <TableCell className="max-w-[300px]">
                                        {task.error_message ? (
                                            <details className="cursor-pointer group">
                                                <summary className="truncate text-red-500 font-medium">Error details</summary>
                                                <div className="mt-2 text-xs text-red-400 whitespace-pre-wrap p-2 bg-red-500/10 rounded border border-red-500/20">{task.error_message}</div>
                                            </details>
                                        ) : "—"}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
