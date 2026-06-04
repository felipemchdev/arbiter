import type { PipelineSource } from "@/lib/types";

const sourceColors: Record<string, { color: string; bg: string }> = {
  airflow:          { color: "#38BDF8", bg: "rgba(56,189,248,0.12)" },
  azure_function:   { color: "#818CF8", bg: "rgba(129,140,248,0.12)" },
  sdk:              { color: "#94A3B8", bg: "rgba(148,163,184,0.12)" },
};

export function SourceBadge({ source }: { source: PipelineSource | string | null }) {
  const val = source || "sdk";
  const c = sourceColors[val] || sourceColors["sdk"];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "3px 9px", borderRadius: 6, fontSize: 12,
      fontWeight: 500, fontFamily: "'DM Sans', sans-serif",
      color: c.color, background: c.bg,
      border: `1px solid ${c.color}22`, whiteSpace: "nowrap",
    }}>{val}</span>
  );
}