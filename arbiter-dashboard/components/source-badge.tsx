"use client";

import { Badge } from "@/components/ui/badge";
import type { PipelineSource } from "@/lib/types";

export function SourceBadge({ source }: { source?: PipelineSource | string | null }) {
  const value = (source || "sdk") as string;
  const color =
    value === "airflow"
      ? "text-[var(--accent-blue)] border-[rgba(74,144,217,0.18)] bg-[rgba(74,144,217,0.08)]"
      : value === "azure_function"
        ? "text-[#9B59B6] border-[rgba(155,89,182,0.18)] bg-[rgba(155,89,182,0.08)]"
        : "text-[var(--text-muted)] border-[rgba(255,255,255,0.18)] bg-[rgba(255,255,255,0.05)]";

  const label =
    value === "airflow"
      ? "Airflow"
      : value === "azure_function"
        ? "Azure Function"
        : "SDK";

  return <Badge className={color}>{label}</Badge>;
}
