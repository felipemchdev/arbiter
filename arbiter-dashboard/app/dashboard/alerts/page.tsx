"use client";

import { AlertList } from "@/components/alert-list";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { getAlerts } from "@/lib/api";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const { data: session } = useSession();
  const token = session?.accessToken;
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      getAlerts(token).then((data) => {
        setAlerts(data);
        setLoading(false);
      });
    }
  }, [token]);

  const filtered = filter === "All" ? alerts : alerts.filter((a) => a.type === filter);

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700, fontSize: 22,
          color: 'var(--text)', letterSpacing: '-0.3px',
          marginBottom: 4,
        }}>Alerts</h1>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        {['All', 'failure', 'no_run', 'duration_exceeded'].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '5px 14px', borderRadius: 'var(--r-pill)',
            fontSize: 12, fontWeight: 500,
            fontFamily: "'DM Sans', sans-serif",
            background: filter === f ? 'var(--accent-muted)' : 'var(--bg-surface)',
            border: `1px solid ${filter === f ? 'var(--border-accent)' : 'var(--border)'}`,
            color: filter === f ? 'var(--accent)' : 'var(--text-muted)',
            transition: 'all var(--duration-fast) var(--ease)',
            cursor: 'pointer',
          }}>{f === 'All' ? 'All' : f.replace('_', ' ')}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: 20, height: 20, border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ padding: '32px 0', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
          No alerts found.
        </div>
      ) : (
        <div className="animate-slide-up">
          <AlertList alerts={filtered} token={token} />
        </div>
      )}
    </div>
  );
}
