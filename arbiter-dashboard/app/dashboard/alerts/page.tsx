"use client";

import { AlertList } from "@/components/alert-list";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { getAlerts } from "@/lib/api";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const { data: session } = useSession();
  const token = session?.accessToken;
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      getAlerts(token).then((data) => {
        setAlerts(data);
        setLoading(false);
      });
    }
  }, [token]);

  const filtered = filter === "all" ? alerts : alerts.filter((a) => a.type === filter);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Alerts</h1>
      </div>

      <div className="flex gap-1 rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-1 w-fit">
        {["all", "failure", "duration_exceeded", "no_run"].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition ${
              filter === type
                ? "bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            {type === "all" ? "All" : type.replace("_", " ")}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="text-lg font-semibold">{filtered.length} alerts</div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12 text-[var(--text-muted)]">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--accent-blue)]" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-8 text-center text-sm text-[var(--text-muted)]">No alerts found.</div>
          ) : (
            <AlertList alerts={filtered} token={token} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
