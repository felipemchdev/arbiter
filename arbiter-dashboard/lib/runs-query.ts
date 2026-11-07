export const RUN_PAGE_SIZE = 20;
export const RUN_STATUSES = ["running", "success", "failed", "skipped"];

export const RUN_FILTER_KEYS = ["status", "pipeline", "q", "from", "to"] as const;
export type RunFilterKey = (typeof RUN_FILTER_KEYS)[number];
export type RunFilterValues = Partial<Record<RunFilterKey, string>>;

export function runsHref(values: RunFilterValues, page = 1): string {
  const query = new URLSearchParams();
  for (const key of RUN_FILTER_KEYS) {
    const value = values[key];
    if (value) {
      query.set(key, value);
    }
  }
  if (page > 1) {
    query.set("page", String(page));
  }
  const suffix = query.toString();
  return suffix ? `/dashboard/runs?${suffix}` : "/dashboard/runs";
}

export function toRunApiFilters(values: RunFilterValues) {
  return {
    status: RUN_STATUSES.includes(values.status ?? "") ? values.status : undefined,
    pipeline_id: values.pipeline,
    q: values.q,
    started_from: values.from ? `${values.from}T00:00:00.000000Z` : undefined,
    started_to: values.to ? `${values.to}T23:59:59.999999Z` : undefined,
  };
}
