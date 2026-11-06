"use client";

import { useSession } from "next-auth/react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import {
  createNotificationChannel,
  deleteNotificationChannel,
  getDeliveries,
  listNotificationChannels,
  testNotificationChannel,
  updateNotificationChannel,
} from "@/lib/api";
import type { AlertDelivery, NotificationChannel, TestSendResult } from "@/lib/types";

const DELIVERY_STATUSES = ["", "pending", "delivered", "failed"] as const;

const th: CSSProperties = {
  padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600,
  color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em',
};
const td: CSSProperties = {
  padding: '12px 16px', fontSize: 12, color: 'var(--text-muted)',
  fontFamily: "'DM Sans', sans-serif",
};

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "delivered" || status === "active"
      ? { fg: 'var(--success)', bg: 'var(--success-bg)' }
      : status === "failed"
        ? { fg: 'var(--failed)', bg: 'var(--failed-bg)' }
        : status === "muted"
          ? { fg: 'var(--skipped)', bg: 'var(--skipped-bg)' }
          : { fg: 'var(--running)', bg: 'var(--running-bg)' };
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
      letterSpacing: '0.04em', padding: '2px 8px', borderRadius: 'var(--r-pill)',
      background: tone.bg, color: tone.fg, border: '1px solid transparent',
    }}>
      {status}
    </span>
  );
}

export default function NotificationsPage() {
  const { data: session } = useSession();
  const role = (session as { role?: string } | null)?.role ?? "viewer";
  const token = (session as { accessToken?: string } | null)?.accessToken ?? "";
  const isOwner = role === "owner";

  const [channels, setChannels] = useState<NotificationChannel[]>([]);
  const [deliveries, setDeliveries] = useState<AlertDelivery[] | null>(null);
  const [status, setStatus] = useState<string>("pending");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [probe, setProbe] = useState<TestSendResult | null>(null);
  const loadSeq = useRef(0);

  const load = useCallback(async () => {
    if (!token) return;
    const seq = ++loadSeq.current;
    setLoading(true);
    setError(null);
    try {
      const [rows, page] = await Promise.all([
        listNotificationChannels(token),
        getDeliveries(token, status ? { status, limit: 20 } : { limit: 20 }),
      ]);
      if (seq !== loadSeq.current) return;
      setChannels(rows);
      setDeliveries(page?.items ?? null);
    } catch (e) {
      if (seq !== loadSeq.current) return;
      console.error("Failed to load notification channels", e);
      setError(e instanceof Error ? e.message : "Failed to load notification channels");
    } finally {
      if (seq === loadSeq.current) setLoading(false);
    }
  }, [token, status]);

  useEffect(() => { load(); }, [load]);

  const channelName = (id: string) => channels.find(c => c.id === id)?.name ?? id.slice(0, 8);

  const handleCreate = async () => {
    if (!token || !name.trim() || !url.trim() || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      const created = await createNotificationChannel(
        { name: name.trim(), url: url.trim(), enabled },
        token,
      );
      setSecret(created.signing_secret);
      setName("");
      setUrl("");
      setCreating(false);
      await load();
    } catch (e) {
      console.error("Failed to create channel", e);
      setError(e instanceof Error ? e.message : "Failed to create channel");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (channel: NotificationChannel) => {
    if (!token) return;
    setError(null);
    try {
      await updateNotificationChannel(channel.id, { enabled: !channel.enabled }, token);
      await load();
    } catch (e) {
      console.error("Failed to update channel", e);
      setError(e instanceof Error ? e.message : "Failed to update channel");
    }
  };

  const handleDelete = async (channel: NotificationChannel) => {
    if (!token) return;
    if (!window.confirm(`Remove "${channel.name}"? Alert deliveries stop immediately.`)) return;
    setError(null);
    try {
      await deleteNotificationChannel(channel.id, token);
      await load();
    } catch (e) {
      console.error("Failed to delete channel", e);
      setError(e instanceof Error ? e.message : "Failed to delete channel");
    }
  };

  const handleTest = async (channel: NotificationChannel) => {
    if (!token) return;
    setError(null);
    setProbe(null);
    try {
      setProbe(await testNotificationChannel(channel.id, token));
    } catch (e) {
      console.error("Failed to test channel", e);
      setError(e instanceof Error ? e.message : "Failed to test channel");
    }
  };

  const copySecret = async () => {
    if (!secret) return;
    await navigator.clipboard.writeText(secret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const linkButton: CSSProperties = {
    padding: '4px 12px', borderRadius: 'var(--r-sm)', fontSize: 11, fontWeight: 500,
    fontFamily: "'DM Sans', sans-serif", background: 'transparent',
    border: '1px solid var(--border)', color: 'var(--text-muted)', cursor: 'pointer',
  };

  return (
    <div className="space-y-6">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700, fontSize: 22, color: 'var(--text)',
          letterSpacing: '-0.3px', marginBottom: 4,
        }}>
          Notifications
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>
          Arbiter posts each new alert to every active channel. The worker retries a
          failed send and stops after five attempts.
        </p>
      </div>

      {secret && (
        <div className="animate-slide-up" style={{
          padding: 24, borderRadius: 'var(--r-lg)',
          border: '1px solid var(--accent)', background: 'var(--accent-muted)',
          marginBottom: 24,
        }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)', marginBottom: 4 }}>
            Channel created
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
            Copy the signing secret now. The API shows it only once. Put it in your
            receiver to verify the{" "}
            <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
              X-Arbiter-Signature
            </code>{" "}
            header.
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
            borderRadius: 'var(--r-md)', background: 'var(--bg)',
            border: '1px solid var(--border)',
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontSize: 12, color: 'var(--text)', wordBreak: 'break-all',
          }}>
            <span style={{ flex: 1 }}>{secret}</span>
            <button onClick={copySecret} style={{ ...linkButton, flexShrink: 0 }}>
              {copied ? "Copied" : "Copy"}
            </button>
            <button onClick={() => setSecret(null)} style={{ ...linkButton, flexShrink: 0 }}>
              Close
            </button>
          </div>
        </div>
      )}

      {probe && (
        <div style={{
          padding: '12px 16px', borderRadius: 'var(--r-md)', marginBottom: 24,
          fontSize: 12, fontFamily: "'DM Sans', sans-serif",
          border: `1px solid ${probe.delivered ? 'var(--success)' : 'var(--failed)'}`,
          background: probe.delivered ? 'var(--success-bg)' : 'var(--failed-bg)',
          color: probe.delivered ? 'var(--success)' : 'var(--failed)',
        }}>
          {probe.delivered
            ? `Test delivered. The endpoint answered ${probe.status_code}.`
            : `Test failed. ${probe.error ?? `The endpoint answered ${probe.status_code}.`}`}
        </div>
      )}

      {error && (
        <div role="alert" style={{
          padding: '8px 12px', borderRadius: 'var(--r-md)', fontSize: 12, fontWeight: 500,
          color: 'var(--failed)', background: 'var(--failed-bg)', marginBottom: 24,
        }}>
          {error}
        </div>
      )}

      {isOwner && (
        <div style={{
          padding: 24, borderRadius: 'var(--r-lg)',
          border: '1px solid var(--border)', background: 'var(--bg-surface)',
          marginBottom: 24,
        }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)', marginBottom: 16 }}>
            {creating ? "New channel" : "Add a webhook channel"}
          </div>

          {creating ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <label style={{ display: 'block' }}>
                <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                  Name
                </span>
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. on-call slack bridge"
                  style={{
                    width: '100%', padding: '8px 12px', borderRadius: 'var(--r-md)',
                    border: '1px solid var(--border)', background: 'var(--bg)',
                    color: 'var(--text)', fontSize: 13,
                    fontFamily: "'DM Sans', sans-serif", outline: 'none',
                  }}
                />
              </label>
              <label style={{ display: 'block' }}>
                <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                  Endpoint URL
                </span>
                <input
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  placeholder="https://example.com/arbiter/hooks"
                  style={{
                    width: '100%', padding: '8px 12px', borderRadius: 'var(--r-md)',
                    border: '1px solid var(--border)', background: 'var(--bg)',
                    color: 'var(--text)', fontSize: 13,
                    fontFamily: "'DM Sans', sans-serif", outline: 'none',
                  }}
                  onKeyDown={e => e.key === "Enter" && handleCreate()}
                />
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} />
                Start sending immediately
              </label>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={handleCreate}
                  disabled={!name.trim() || !url.trim() || submitting}
                  style={{
                    padding: '6px 16px', borderRadius: 'var(--r-md)', fontSize: 12, fontWeight: 600,
                    fontFamily: "'DM Sans', sans-serif",
                    background: name.trim() && url.trim() && !submitting ? 'var(--accent)' : 'var(--bg-surface)',
                    border: `1px solid ${name.trim() && url.trim() && !submitting ? 'var(--accent)' : 'var(--border)'}`,
                    color: name.trim() && url.trim() && !submitting ? 'white' : 'var(--text-muted)',
                    cursor: name.trim() && url.trim() && !submitting ? 'pointer' : 'default',
                  }}
                >
                  {submitting ? "Creating..." : "Create channel"}
                </button>
                <button
                  onClick={() => { setCreating(false); setName(""); setUrl(""); setError(null); }}
                  style={{ padding: '6px 16px', borderRadius: 'var(--r-md)', fontSize: 12, ...linkButton }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setCreating(true)}
              style={{
                padding: '6px 16px', borderRadius: 'var(--r-md)', fontSize: 12, fontWeight: 600,
                fontFamily: "'DM Sans', sans-serif", background: 'var(--accent)',
                border: '1px solid var(--accent)', color: 'white', cursor: 'pointer',
              }}
            >
              + New channel
            </button>
          )}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{
            width: 20, height: 20, border: '2px solid var(--border)',
            borderTopColor: 'var(--accent)', borderRadius: '50%',
            animation: 'spin 0.7s linear infinite',
          }} />
        </div>
      ) : channels.length === 0 ? (
        <div style={{ padding: '32px 0', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
          No channels yet. Alerts stay unread until you add one.
        </div>
      ) : (
        <div className="animate-slide-up" style={{
          borderRadius: 'var(--r-lg)', border: '1px solid var(--border)', overflow: 'hidden',
          marginBottom: 24,
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={th}>Channel</th>
                <th style={th}>Endpoint</th>
                <th style={th}>State</th>
                <th style={th}>Last delivery</th>
                <th style={{ ...th, textAlign: 'right' }}></th>
              </tr>
            </thead>
            <tbody>
              {channels.map(channel => (
                <tr key={channel.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ ...td, color: 'var(--text)', fontSize: 13 }}>{channel.name}</td>
                  <td style={{ ...td, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
                    {channel.url}
                  </td>
                  <td style={td}>
                    <StatusBadge status={channel.enabled ? "active" : "muted"} />
                  </td>
                  <td style={td}>
                    {channel.last_delivery ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <StatusBadge status={channel.last_delivery.status} />
                        <span>
                          {channel.last_delivery.attempts} attempt
                          {channel.last_delivery.attempts === 1 ? "" : "s"}
                          {channel.last_delivery.response_status_code
                            ? ` · HTTP ${channel.last_delivery.response_status_code}`
                            : ""}
                        </span>
                        {channel.last_delivery.last_error && (
                          <span style={{ color: 'var(--failed)', fontSize: 11 }}>
                            {channel.last_delivery.last_error}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span>Nothing sent yet.</span>
                    )}
                  </td>
                  <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {isOwner && (
                      <>
                        <button onClick={() => handleTest(channel)} style={{ ...linkButton, marginRight: 6 }}>
                          Test
                        </button>
                        <button onClick={() => handleToggle(channel)} style={{ ...linkButton, marginRight: 6 }}>
                          {channel.enabled ? "Mute" : "Unmute"}
                        </button>
                        <button
                          onClick={() => handleDelete(channel)}
                          style={{
                            ...linkButton,
                            borderColor: 'var(--failed-bg)', color: 'var(--failed)',
                          }}
                        >
                          Remove
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {channels.length > 0 && (
        <div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap',
          }}>
            <span style={{
              fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
              fontWeight: 600, fontSize: 14, color: 'var(--text)',
            }}>
              Deliveries
            </span>
            {DELIVERY_STATUSES.map(value => (
              <button
                key={value || "all"}
                onClick={() => setStatus(value)}
                style={{
                  padding: '3px 10px', borderRadius: 'var(--r-pill)', fontSize: 11, fontWeight: 500,
                  fontFamily: "'DM Sans', sans-serif",
                  background: status === value ? 'var(--accent-muted)' : 'transparent',
                  border: `1px solid ${status === value ? 'var(--accent)' : 'var(--border)'}`,
                  color: status === value ? 'var(--accent)' : 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                {value || "all"}
              </button>
            ))}
          </div>

          {deliveries === null ? (
            <div style={{ padding: '24px 0', fontSize: 13, color: 'var(--text-muted)' }}>
              The delivery list did not load. Check that the API is reachable.
            </div>
          ) : deliveries.length === 0 ? (
            <div style={{ padding: '24px 0', fontSize: 13, color: 'var(--text-muted)' }}>
              No delivery matches this state.
            </div>
          ) : (
            <div style={{
              borderRadius: 'var(--r-lg)', border: '1px solid var(--border)', overflow: 'hidden',
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={th}>Channel</th>
                    <th style={th}>State</th>
                    <th style={th}>Attempts</th>
                    <th style={th}>Code</th>
                    <th style={th}>Detail</th>
                    <th style={th}>Queued</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.map(row => (
                    <tr key={row.id}>
                      <td style={{ ...td, color: 'var(--text)' }}>{channelName(row.channel_id)}</td>
                      <td style={td}><StatusBadge status={row.status} /></td>
                      <td style={td}>{row.attempts}</td>
                      <td style={td}>{row.response_status_code ?? "—"}</td>
                      <td style={{ ...td, maxWidth: 320 }}>
                        {row.last_error ?? (row.delivered_at ? "Delivered." : "Waiting for the worker.")}
                      </td>
                      <td style={td}>{new Date(row.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
