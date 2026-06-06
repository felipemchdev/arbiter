"use client";

import { Button } from "@/components/ui/button-arbiter";
import { resolveAlert } from "@/lib/api";
import type { Alert } from "@/lib/types";
import { useIsOwner } from "@/lib/useRole";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

const alertTypeColor = (type: string) => {
  if (type === "failure") return "var(--failed)";
  if (type === "duration_exceeded") return "var(--running)";
  if (type === "no_run") return "var(--skipped)";
  return "var(--border)";
};

export function AlertList({ alerts, token }: { alerts: Alert[]; token?: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const isOwner = useIsOwner();

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <div key={alert.id} style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderLeft: `3px solid ${alertTypeColor(alert.type)}`,
          borderRadius: 'var(--r-lg)',
          padding: '16px 20px',
          marginBottom: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          transition: 'all var(--duration-fast) var(--ease)',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg-card)')}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)', marginBottom: 4 }}>
              {alert.message}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace", display: 'flex', gap: 12 }}>
              <span>{alert.pipeline_id.slice(0, 8)}...</span>
              <span>{String.fromCharCode(183)}</span>
              <span>{new Date(alert.created_at).toLocaleString()}</span>
            </div>
          </div>
          {isOwner && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                startTransition(async () => {
                  await resolveAlert(alert.id, token);
                  router.refresh();
                })
              }
              disabled={pending}
            >
              Resolve
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}
