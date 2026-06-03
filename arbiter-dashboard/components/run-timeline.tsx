import { Card, CardContent } from "@/components/ui/card";
import type { TaskInstance } from "@/lib/types";

export function RunTimeline({ tasks }: { tasks: TaskInstance[] }) {
    const first = tasks[0]?.started_at ? new Date(tasks[0].started_at).getTime() : Date.now();
    const last = tasks.at(-1)?.finished_at ? new Date(tasks.at(-1)?.finished_at || "").getTime() : Date.now();
    const total = Math.max(last - first, 1);

    return (
        <Card>
            <CardContent className="space-y-3">
                {tasks.map((task) => {
                    const start = new Date(task.started_at).getTime();
                    const finish = task.finished_at ? new Date(task.finished_at).getTime() : start + (task.duration_ms ?? 0);
                    const left = ((start - first) / total) * 100;
                    const width = Math.max(((finish - start) / total) * 100, 3);
                    return (
                        <div key={task.id} className="grid grid-cols-[160px_1fr_120px] items-center gap-3 text-sm">
                            <div className="text-[var(--text-primary)]">{task.task_id}</div>
                            <div className="relative h-4 rounded-full bg-[#111120]">
                                <div
                                    className="absolute h-4 rounded-full bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-purple)]"
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