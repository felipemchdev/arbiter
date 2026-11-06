"use client";

import { Button } from "@/components/ui/button-arbiter";
import { updatePipelineBudget } from "@/lib/api";
import { useIsOwner } from "@/lib/useRole";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

/**
 * Budget a run may take, in milliseconds. Without one the API compares each run
 * against the p95 of the pipeline's own history.
 */
export function DurationBudget({
  pipelineId,
  thresholdMs,
  token,
}: {
  pipelineId: string;
  thresholdMs?: number | null;
  token?: string;
}) {
  const isOwner = useIsOwner();
  const router = useRouter();
  const [value, setValue] = useState(thresholdMs == null ? "" : String(thresholdMs));
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  if (!isOwner) {
    return null;
  }

  const submit = (next: number | null) => {
    if (!token) {
      setError("Sign in again to change this budget.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const updated = await updatePipelineBudget(pipelineId, next, token);
        setValue(updated.slow_threshold_ms == null ? "" : String(updated.slow_threshold_ms));
        router.refresh();
      } catch {
        setError("The API refused that value. Use a whole number above zero.");
      }
    });
  };

  const save = () => {
    const parsed = Number(value.trim());
    if (!Number.isInteger(parsed) || parsed <= 0) {
      setError("Enter a whole number of milliseconds above zero.");
      return;
    }
    submit(parsed);
  };

  return (
    <div style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: "var(--r-lg)",
      padding: 20,
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>
        Duration budget
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          inputMode="numeric"
          placeholder="p95 of history"
          aria-label="Duration budget in milliseconds"
          style={{
            width: 160, padding: "8px 10px", fontSize: 13,
            color: "var(--text)", background: "var(--bg-surface)",
            border: "1px solid var(--border)", borderRadius: "var(--r-md)",
            fontFamily: "'JetBrains Mono', monospace",
          }}
        />
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>ms</span>
        <Button variant="secondary" size="sm" onClick={save} disabled={pending}>
          Save
        </Button>
        {thresholdMs != null && (
          <Button variant="ghost" size="sm" onClick={() => submit(null)} disabled={pending}>
            Use history
          </Button>
        )}
      </div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 10 }}>
        A run longer than this budget raises a duration alert. Leave it empty to compare against the
        slowest 5 percent of recent successful runs.
      </div>
      {error && (
        <div style={{ fontSize: 12, color: "var(--failed)", marginTop: 8 }}>{error}</div>
      )}
    </div>
  );
}
