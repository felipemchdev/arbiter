import { Card, CardContent } from "@/components/ui/card";
import type { TaskInstance } from "@/lib/types";

export function RunTimeline({ tasks }: { tasks: TaskInstance[] }) {
    const first = tasks[0]?.started_at ? new Date(tasks[0].started_at).getTime() : Date.now();
    const last = tasks.at(-1)?.finished_at ? new Date(tasks.at(-1)?.finished_at || "").getTime() : Date.now();
    const total = Math.max(last - first, 1);

    const getStatusColor = (status: string) => {
        if (status === "success") return "bg-[var(--status-success)]";
        if (status === "failed") return "bg-[var(--status-failed)]";
        if (status === "running") return "bg-[var(--status-running)]";
        return "bg-[var(--status-skipped)]";
    };

    return (
        <Card>
            <CardContent className="space-y-4 p-6">
                {tasks.map((task) => {
                    const start = new Date(task.started_at).getTime();
                    const finish = task.finished_at ? new Date(task.finished_at).getTime() : start + (task.duration_ms ?? 0);
                    const left = ((start - first) / total) * 100;
                    const width = Math.max(((finish - start) / total) * 100, 1);
                    return (
                        <div key={task.id} className="grid grid-cols-[160px_1fr_120px] items-center gap-4 text-sm font-sans">
                            <div className="text-[var(--text-primary)] font-medium truncate" title={task.task_id}>{task.task_id}</div>
                            <div className="relative h-[20px] rounded-[6px] bg-[rgba(10,18,40,0.40)]">
                                <div
                                    className={`absolute h-full rounded-[6px] ${getStatusColor(task.status)} opacity-80 hover:opacity-100 transition-opacity`}
                                    style={{ left: `${left}%`, width: `${width}%` }}
                                />
                            </div>
                            <div className="text-right text-[var(--text-muted)]">
                                {task.duration_ms ? `${task.duration_ms} ms` : new Date(task.started_at).toLocaleTimeString()}
                            </div>
                        </div>
                    );
                })}
            </CardContent>
        </Card>
    );
}