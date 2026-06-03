import { DagGraph } from "@/components/dag-graph";
import { RunTimeline } from "@/components/run-timeline";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { authOptions } from "@/lib/auth";
import { getPipeline, getPipelineRuns, getRunTasks } from "@/lib/api";
import { getServerSession } from "next-auth";
import { notFound } from "next/navigation";

export default async function PipelineDetailPage({ params }: { params: { pipelineId: string } }) {
    const { pipelineId } = params;
    const session = await getServerSession(authOptions);
    const pipeline = await getPipeline(pipelineId, session?.accessToken);
    if (!pipeline) {
        notFound();
    }
    const runs = await getPipelineRuns(pipelineId, session?.accessToken);
    const latestRun = runs[0];
    const runTasks = latestRun ? await getRunTasks(latestRun.id, session?.accessToken) : [];
    const nodes = pipeline.dag_definition?.nodes.map((node) => ({
        ...node,
        status: (runTasks.find((task) => task.task_id === node.id)?.status || "skipped") as any,
    })) || [];

    return (
        <div className="space-y-6">
            <div>
                <div className="text-3xl font-semibold">{pipeline.name}</div>
                <div className="mt-2 flex items-center gap-3 text-sm text-[var(--text-muted)]">
                    <StatusBadge status={pipeline.last_run_status} />
                    <StatusBadge status={pipeline.source} />
                </div>
            </div>

            <Card>
                <CardHeader>
                    <div className="text-lg font-semibold">Grafo</div>
                </CardHeader>
                <CardContent>{pipeline.dag_definition ? <DagGraph nodes={nodes} edges={pipeline.dag_definition.edges} /> : <div className="text-sm text-[var(--text-muted)]">No DAG definition yet.</div>}</CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <div className="text-lg font-semibold">Histórico</div>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeader>Run</TableHeader>
                                <TableHeader>Status</TableHeader>
                                <TableHeader>Duration</TableHeader>
                                <TableHeader>Timestamp</TableHeader>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {runs.map((run) => (
                                <TableRow key={run.id}>
                                    <TableCell>{run.run_id}</TableCell>
                                    <TableCell><StatusBadge status={run.status} /></TableCell>
                                    <TableCell>{run.duration_ms ? `${run.duration_ms} ms` : "—"}</TableCell>
                                    <TableCell>{new Date(run.started_at).toLocaleString()}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
