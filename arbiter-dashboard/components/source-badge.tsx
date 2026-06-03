"use client";

import { Badge } from "@/components/ui/badge";
import type { PipelineSource } from "@/lib/types";

export function SourceBadge({ source }: { source?: PipelineSource | string | null }) {
  const value = (source || "sdk") as string;
  const color =
    value === "airflow"
      ? "text-[#00C7D3] border-[rgba(0,199,211,0.18)]"
      : value === "azure_function"
        ? "text-[#9B59B6] border-[rgba(155,89,182,0.18)]"
        : "text-[var(--accent-blue)] border-[rgba(56,189,248,0.18)]";

  const label =
    value === "airflow"
      ? "Airflow"
      : value === "azure_function"
        ? "Azure Function"
        : "SDK";

  return <Badge className={color}>{label}</Badge>;
}
