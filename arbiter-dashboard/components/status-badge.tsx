import type { RunStatus, TaskStatus } from "@/lib/types";

const statusColors: Record<string, { color: string; bg: string }> = {
  success:          { color: "#22C55E", bg: "rgba(34,197,94,0.12)" },
  failed:           { color: "#EF4444", bg: "rgba(239,68,68,0.12)" },
  running:          { color: "#F59E0B", bg: "rgba(245,158,11,0.12)" },
  skipped:          { color: "#64748B", bg: "rgba(100,116,139,0.12)" },
  upstream_failed:  { color: "#F97316", bg: "rgba(249,115,22,0.12)" },
  airflow:          { color: "#38BDF8", bg: "rgba(56,189,248,0.12)" },
  azure_function:   { color: "#818CF8", bg: "rgba(129,140,248,0.12)" },
  sdk:              { color: "#94A3B8", bg: "rgba(148,163,184,0.12)" },
};

export function StatusBadge({ status }: { status: RunStatus | TaskStatus | string | null | undefined }) {
  const val = (status || "skipped") as string;
  const c = statusColors[val] || statusColors["skipped"];
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
