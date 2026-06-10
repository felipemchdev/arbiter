"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { createApiKey, listApiKeys, revokeApiKey } from "@/lib/api";
import type { ApiKey, ApiKeyCreated } from "@/lib/types";

export default function ApiKeysPage() {
  const { data: session } = useSession();
  const token = session?.accessToken;
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [environment, setEnvironment] = useState("test");
  const [newKey, setNewKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchKeys = () => {
    if (!token) return;
    setLoading(true);
    listApiKeys(token).then(setKeys).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { fetchKeys(); }, [token]);

  const handleCreate = async () => {
    if (!token || !name.trim() || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      const created = await createApiKey(name.trim(), environment, token);
      setNewKey(created);
      setName("");
      fetchKeys();
    } catch (e) {
      console.error("Failed to create API key", e);
      setError(e instanceof Error ? e.message : "Failed to create API key");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (id: string) => {
    if (!token) return;
    try {
      await revokeApiKey(id, token);
      fetchKeys();
    } catch (e) {
      console.error("Failed to revoke API key", e);
    }
  };

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700, fontSize: 22,
          color: 'var(--text)', letterSpacing: '-0.3px',
          marginBottom: 4,
        }}>API Keys</h1>
      </div>

      {newKey ? (
        <div style={{
          padding: 24, borderRadius: 'var(--r-lg)',
          border: '1px solid var(--accent)',
          background: 'var(--accent-muted)',
          marginBottom: 24,
        }} className="animate-slide-up">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)', marginBottom: 4 }}>
                Key created
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                Copy this key now. You won&apos;t see it again.
              </div>
            </div>
            <button onClick={() => setNewKey(null)} style={{
              background: 'transparent', border: 'none',
              color: 'var(--text-muted)', fontSize: 16,
              cursor: 'pointer', padding: '0 4px',
            }}>
              ×
            </button>
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '10px 14px',
            borderRadius: 'var(--r-md)',
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontSize: 12, color: 'var(--text)',
            wordBreak: 'break-all',
          }}>
            <span style={{ flex: 1 }}>{newKey.api_key}</span>
            <button onClick={() => copyToClipboard(newKey.api_key)} style={{
              flexShrink: 0,
              padding: '4px 12px',
              borderRadius: 'var(--r-sm)',
              fontSize: 11, fontWeight: 500,
              fontFamily: "'DM Sans', sans-serif",
              border: `1px solid ${copied ? 'var(--accent)' : 'var(--border)'}`,
              background: copied ? 'var(--accent)' : 'var(--bg-surface)',
              color: copied ? 'white' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all var(--duration-fast) var(--ease)',
            }}>
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>
      ) : (
        <div style={{
          padding: 24, borderRadius: 'var(--r-lg)',
          border: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          marginBottom: 24,
        }}>
          <div style={{
            fontWeight: 600, fontSize: 13, color: 'var(--text)',
            marginBottom: 16,
          }}>
            {creating ? "New API key" : "Create an API key"}
          </div>

          {creating ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                  Name
                </label>
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. CI/CD pipeline"
                  style={{
                    width: '100%', padding: '8px 12px',
                    borderRadius: 'var(--r-md)',
                    border: '1px solid var(--border)',
                    background: 'var(--bg)',
                    color: 'var(--text)',
                    fontSize: 13,
                    fontFamily: "'DM Sans', sans-serif",
                    outline: 'none',
                  }}
                  onKeyDown={e => e.key === "Enter" && handleCreate()}
                />
              </div>
              <div>
                <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                  Environment
                </label>
                <div style={{ display: 'flex', gap: 6 }}>
                  {["test", "production"].map(env => (
                    <button key={env} onClick={() => setEnvironment(env)} style={{
                      padding: '5px 14px', borderRadius: 'var(--r-pill)',
                      fontSize: 12, fontWeight: 500,
                      fontFamily: "'DM Sans', sans-serif",
                      background: environment === env ? 'var(--accent-muted)' : 'var(--bg)',
                      border: `1px solid ${environment === env ? 'var(--border-accent)' : 'var(--border)'}`,
                      color: environment === env ? 'var(--accent)' : 'var(--text-muted)',
                      cursor: 'pointer', textTransform: 'capitalize',
                      transition: 'all var(--duration-fast) var(--ease)',
                    }}>
                      {env}
                    </button>
                  ))}
                </div>
              </div>
              {error && (
                <div style={{
                  padding: '8px 12px', borderRadius: 'var(--r-md)',
                  fontSize: 12, fontWeight: 500,
                  fontFamily: "'DM Sans', sans-serif",
                  color: 'var(--danger)',
                  background: 'var(--danger-muted)',
                  border: '1px solid var(--danger-muted)',
                }}>
                  {error}
                </div>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={handleCreate} disabled={!name.trim() || submitting} style={{
                  padding: '6px 16px', borderRadius: 'var(--r-md)',
                  fontSize: 12, fontWeight: 600,
                  fontFamily: "'DM Sans', sans-serif",
                  background: name.trim() && !submitting ? 'var(--accent)' : 'var(--bg-surface)',
                  border: `1px solid ${name.trim() && !submitting ? 'var(--accent)' : 'var(--border)'}`,
                  color: name.trim() && !submitting ? 'white' : 'var(--text-muted)',
                  cursor: name.trim() && !submitting ? 'pointer' : 'default',
                  transition: 'all var(--duration-fast) var(--ease)',
                }}>
                  {submitting ? "Creating..." : "Create key"}
                </button>
                <button onClick={() => { setCreating(false); setName(""); setError(null); }} style={{
                  padding: '6px 16px', borderRadius: 'var(--r-md)',
                  fontSize: 12, fontWeight: 500,
                  fontFamily: "'DM Sans', sans-serif",
                  background: 'transparent', border: '1px solid var(--border)',
                  color: 'var(--text-muted)', cursor: 'pointer',
                  transition: 'all var(--duration-fast) var(--ease)',
                }}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button onClick={() => setCreating(true)} style={{
              padding: '6px 16px', borderRadius: 'var(--r-md)',
              fontSize: 12, fontWeight: 600,
              fontFamily: "'DM Sans', sans-serif",
              background: 'var(--accent)', border: '1px solid var(--accent)',
              color: 'white', cursor: 'pointer',
              transition: 'all var(--duration-fast) var(--ease)',
            }}>
              + New API key
            </button>
          )}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: 20, height: 20, border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
        </div>
      ) : keys.length === 0 ? (
        <div style={{ padding: '32px 0', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
          No API keys yet.
        </div>
      ) : (
        <div className="animate-slide-up" style={{
          borderRadius: 'var(--r-lg)',
          border: '1px solid var(--border)',
          overflow: 'hidden',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Name</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Environment</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Prefix</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Created</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last used</th>
                <th style={{ padding: '10px 16px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}></th>
              </tr>
            </thead>
            <tbody>
              {keys.map(key => (
                <tr key={key.id} style={{
                  borderBottom: '1px solid var(--border)',
                  background: key.revoked ? 'var(--bg-surface)' : 'transparent',
                }}>
                  <td style={{
                    padding: '12px 16px', fontSize: 13, color: 'var(--text)',
                    fontFamily: "'DM Sans', sans-serif",
                    textDecoration: key.revoked ? 'line-through' : 'none',
                  }}>
                    {key.name}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontSize: 11, fontWeight: 600,
                      fontFamily: "'DM Sans', sans-serif",
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      padding: '2px 8px',
                      borderRadius: 'var(--r-pill)',
                      background: key.environment === 'production' ? 'var(--danger-muted)' : 'var(--bg-surface)',
                      color: key.environment === 'production' ? 'var(--danger)' : 'var(--text-muted)',
                      border: `1px solid ${key.environment === 'production' ? 'var(--danger-muted)' : 'var(--border)'}`,
                    }}>
                      {key.environment === 'production' ? 'live' : key.environment}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: "'JetBrains Mono', 'Fira Code', monospace", fontSize: 12, color: 'var(--text-muted)' }}>
                    {key.prefix}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-muted)', fontFamily: "'DM Sans', sans-serif" }}>
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-muted)', fontFamily: "'DM Sans', sans-serif" }}>
                    {key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : "—"}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    {key.revoked ? (
                      <span style={{
                        fontSize: 11, fontWeight: 500,
                        fontFamily: "'DM Sans', sans-serif",
                        color: 'var(--text-muted)',
                        padding: '3px 10px',
                        borderRadius: 'var(--r-pill)',
                        background: 'var(--bg-surface)',
                      }}>Revoked</span>
                    ) : (
                      <button onClick={() => handleRevoke(key.id)} style={{
                        padding: '4px 12px', borderRadius: 'var(--r-sm)',
                        fontSize: 11, fontWeight: 500,
                        fontFamily: "'DM Sans', sans-serif",
                        background: 'transparent',
                        border: '1px solid var(--danger-muted)',
                        color: 'var(--danger)',
                        cursor: 'pointer',
                        transition: 'all var(--duration-fast) var(--ease)',
                      }}>
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
