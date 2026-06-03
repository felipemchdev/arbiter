import { RunTimeline } from "@/components/run-timeline";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { authOptions } from "@/lib/auth";
import { getRun, getRunTasks } from "@/lib/api";
import { getServerSession } from "next-auth";
import { notFound } from "next/navigation";

export default async function RunDetailPage({ params }: { params: { id: string } }) {
    const { id } = params;
    const session = await getServerSession(authOptions);
    const run = await getRun(id, session?.accessToken);
    if (!run) {
        notFound();
    }
    const tasks = await getRunTasks(id, session?.accessToken);

    return (
        <div className="space-y-6">
            <div className="text-3xl font-semibold">{run.run_id}</div>
            <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
                <StatusBadge status={run.status} />
                <span>{run.duration_ms ? `${run.duration_ms} ms` : "—"}</span>
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
                                    <TableCell>{task.error_message || "—"}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}