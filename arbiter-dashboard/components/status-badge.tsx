import { Badge } from "@/components/ui/badge";
import type { RunStatus, TaskStatus } from "@/lib/types";
import { cn } from "@/components/ui/utils";

export function StatusBadge({ status }: { status?: RunStatus | TaskStatus | string | null }) {
    const value = (status || "skipped") as string;
    const color =
        value === "success"
            ? "text-[var(--status-success)] border-[rgba(34,197,94,0.18)]"
            : value === "failed"
                ? "text-[var(--status-failed)] border-[rgba(239,68,68,0.18)]"
                : value === "running"
                    ? "text-[var(--status-running)] border-[rgba(245,158,11,0.18)]"
                    : "text-[var(--status-skipped)] border-[rgba(100,116,139,0.18)]";

    return <Badge className={cn("capitalize", color)}>{value}</Badge>;
}