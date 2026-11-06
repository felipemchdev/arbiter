import { RunFilters } from "@/components/run-filters";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button-arbiter";
import { authOptions } from "@/lib/auth";
import { getPipelines, getRuns } from "@/lib/api";
import { RUN_FILTER_KEYS, RUN_PAGE_SIZE, runsHref, toRunApiFilters, type RunFilterValues } from "@/lib/runs-query";
import { getServerSession } from "next-auth";
import Link from "next/link";

const COLUMNS = "1.3fr 1.5fr 90px 150px 80px 64px";

export default async function RunsPage({ searchParams }: { searchParams: Record<string, string | string[] | undefined> }) {
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;

  const values: RunFilterValues = {};
  for (const key of RUN_FILTER_KEYS) {
    const value = searchParams[key];
    if (typeof value === "string") {
      values[key] = value;
    }
  }

  const requested = Number.parseInt(String(searchParams.page ?? "1"), 10);
  const page = Number.isNaN(requested) || requested < 1 ? 1 : requested;

  const [runPage, pipelines] = await Promise.all([
    getRuns(token, { ...toRunApiFilters(values), limit: RUN_PAGE_SIZE, offset: (page - 1) * RUN_PAGE_SIZE }),
    getPipelines(token, { limit: 200 }),
  ]);

  const total = runPage?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / RUN_PAGE_SIZE));
  const runs = runPage?.items ?? [];
  const firstShown = runs.length === 0 ? 0 : (page - 1) * RUN_PAGE_SIZE + 1;

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1
          style={{
            fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
            fontWeight: 700,
            fontSize: 22,
            color: "var(--text)",
            letterSpacing: "-0.3px",
            marginBottom: 4,
          }}
        >
          Runs
        </h1>
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
          {runPage === null ? "The run list did not load." : `${total} runs match the filters`}
        </p>
      </div>

      <div className="animate-fade-in">
        <RunFilters values={values} pipelines={pipelines.map((p) => ({ id: p.id, name: p.name }))} />
      </div>

      <div
        className="animate-fade-in"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--r-lg)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: COLUMNS,
            padding: "10px 20px",
            background: "var(--bg-surface)",
            borderBottom: "1px solid var(--border)",
            fontSize: 11,
            fontWeight: 600,
            color: "var(--text-muted)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          <span>Pipeline</span>
          <span>Run</span>
          <span>Status</span>
          <span>Started</span>
          <span>Duration</span>
          <span></span>
        </div>

        {runs.length === 0 ? (
          <div style={{ padding: "32px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            {runPage === null
              ? "Check that the API is reachable, or clear the filters."
              : "No runs match these filters."}
          </div>
        ) : (
          runs.map((run) => (
            <div
              key={run.id}
              style={{
                display: "grid",
                gridTemplateColumns: COLUMNS,
                padding: "14px 20px",
                borderBottom: "1px solid var(--border)",
                alignItems: "center",
                transition: "background var(--duration-fast) var(--ease)",
              }}
            >
              <Link
                href={`/dashboard/pipelines/${run.pipeline_id}`}
                style={{ fontSize: 14, fontWeight: 500, color: "var(--text)", textDecoration: "none" }}
              >
                {run.pipeline_name}
              </Link>
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    fontFamily: "'JetBrains Mono', monospace",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {run.run_id}
                </div>
                {run.error_message && (
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--failed)",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {run.error_message}
                  </div>
                )}
              </div>
              <StatusBadge status={run.status} />
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{new Date(run.started_at).toLocaleString()}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
                {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : "—"}
              </div>
              <Link href={`/dashboard/runs/${run.id}`}>
                <Button size="sm">View</Button>
              </Link>
            </div>
          ))
        )}

        {total > RUN_PAGE_SIZE && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 20px",
              fontSize: 12,
              color: "var(--text-muted)",
            }}
          >
            <span>
              {firstShown}–{Math.min(total, (page - 1) * RUN_PAGE_SIZE + runs.length)} of {total}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              {page > 1 && (
                <Link href={runsHref(values, page - 1)}>
                  <Button size="sm">Prev</Button>
                </Link>
              )}
              {page < lastPage && (
                <Link href={runsHref(values, page + 1)}>
                  <Button size="sm">Next</Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
