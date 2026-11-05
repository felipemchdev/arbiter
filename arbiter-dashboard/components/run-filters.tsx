"use client";

import { Button } from "@/components/ui/button-arbiter";
import { RUN_FILTER_KEYS, RUN_STATUSES, runsHref, type RunFilterValues } from "@/lib/runs-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";

const fieldStyle = {
  height: 34,
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--r-md)",
  color: "var(--text)",
  fontFamily: "'DM Sans', sans-serif",
  fontSize: 13,
  padding: "0 10px",
} as const;

/**
 * Filter bar for the run browser.
 *
 * The fields are uncontrolled: applying a filter writes them into the URL, and the page
 * reads them back from the server. `key` on the form remounts the inputs when navigation
 * changes the URL, so the browser back button restores what the reader sees.
 */
export function RunFilters({
  values,
  pipelines,
}: {
  values: RunFilterValues;
  pipelines: Array<{ id: string; name: string }>;
}) {
  const router = useRouter();

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const next: RunFilterValues = {};
    for (const key of RUN_FILTER_KEYS) {
      const value = data.get(key);
      if (typeof value === "string" && value) {
        next[key] = value;
      }
    }
    router.push(runsHref(next));
  }

  return (
    <form
      key={runsHref(values)}
      onSubmit={onSubmit}
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: 8,
        padding: "12px 16px",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-lg)",
      }}
    >
      <input
        name="q"
        type="search"
        defaultValue={values.q ?? ""}
        placeholder="Search run id or error"
        aria-label="Search run id or error"
        style={{ ...fieldStyle, flex: "2 1 200px" }}
      />
      <select
        name="status"
        defaultValue={values.status ?? ""}
        aria-label="Filter by run status"
        style={{ ...fieldStyle, flex: "1 1 120px" }}
      >
        <option value="">Any status</option>
        {RUN_STATUSES.map((status) => (
          <option key={status} value={status}>
            {status}
          </option>
        ))}
      </select>
      <select
        name="pipeline"
        defaultValue={values.pipeline ?? ""}
        aria-label="Filter by pipeline"
        style={{ ...fieldStyle, flex: "1 1 160px" }}
      >
        <option value="">Any pipeline</option>
        {pipelines.map((pipeline) => (
          <option key={pipeline.id} value={pipeline.id}>
            {pipeline.name}
          </option>
        ))}
      </select>
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
        From
        <input
          name="from"
          type="date"
          defaultValue={values.from ?? ""}
          aria-label="Started on or after, UTC date"
          style={fieldStyle}
        />
      </label>
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
        To
        <input
          name="to"
          type="date"
          defaultValue={values.to ?? ""}
          aria-label="Started on or before, UTC date"
          style={fieldStyle}
        />
      </label>
      <Button type="submit" size="sm" variant="primary">
        Apply
      </Button>
      <Link href="/dashboard/runs">
        <Button type="button" size="sm">
          Clear
        </Button>
      </Link>
      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Dates match UTC days.</span>
    </form>
  );
}
