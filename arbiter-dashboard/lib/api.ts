import type {
  Alert,
  AlertDelivery,
  ApiKey,
  ApiKeyCreated,
  NotificationChannel,
  NotificationChannelCreated,
  Page,
  Pipeline,
  PipelineRun,
  RunListItem,
  TaskInstance,
  TestSendResult,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiGet<T>(path: string, token: string): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`GET ${path} failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  } catch (e) {
    if (e instanceof TypeError && e.message === "Failed to fetch") {
      throw new Error(`Cannot reach API at ${API_URL}. Is the API running?`);
    }
    throw e;
  }
}

export async function apiPost<T>(path: string, body: unknown, token: string): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`POST ${path} failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  } catch (e) {
    if (e instanceof TypeError && e.message === "Failed to fetch") {
      throw new Error(`Cannot reach API at ${API_URL}. Is the API running?`);
    }
    throw e;
  }
}

export async function apiPut<T>(path: string, body: unknown, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`PUT ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function apiFetch<T>(path: string, token?: string, init: RequestInit = {}): Promise<T | null> {
  try {
    const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  return response.json() as Promise<T>;
  } catch {
    return null;
  }
}

export async function apiPatch<T>(path: string, body: unknown, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`PATCH ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function updatePipelineBudget(pipelineId: string, slowThresholdMs: number | null, token: string) {
  return apiPatch<Pipeline>(`/api/v1/pipelines/${pipelineId}`, { slow_threshold_ms: slowThresholdMs }, token);
}

export async function getPipeline(id: string, token?: string) {
  return await apiFetch<Pipeline>(`/api/v1/pipelines/${id}`, token);
}

export async function getPipelineRuns(id: string, token?: string) {
  const page = await apiFetch<Page<PipelineRun>>(`/api/v1/pipelines/${id}/runs`, token);
  return page?.items ?? [];
}

export async function getRun(id: string, token?: string) {
  return await apiFetch<PipelineRun>(`/api/v1/runs/${id}`, token);
}

export async function getRuns(
  token?: string,
  filters: Partial<Record<string, string | number>> = {},
) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return await apiFetch<Page<RunListItem>>(`/api/v1/runs${suffix}`, token);
}

export async function getRunTasks(id: string, token?: string) {
  return (await apiFetch<TaskInstance[]>(`/api/v1/runs/${id}/tasks`, token)) ?? [];
}

export async function getAlerts(token?: string) {
  const page = await apiFetch<Page<Alert>>("/api/v1/alerts", token);
  return page?.items ?? [];
}

export async function getMetrics(token?: string) {
  return await apiFetch<{ runs_today: number; failed_today: number; active_pipelines: number; avg_duration_ms: number }>(
    "/api/v1/metrics",
    token,
  );
}

export async function resolveAlert(id: string, token?: string) {
  return await apiFetch(`/api/v1/alerts/${id}/resolve`, token, { method: "PUT" });
}

export async function getPipelines(token?: string, params?: { limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (params?.limit !== undefined) query.set("limit", String(params.limit));
  if (params?.offset !== undefined) query.set("offset", String(params.offset));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const page = await apiFetch<Page<Pipeline>>(`/api/v1/pipelines${suffix}`, token);
  return page?.items ?? [];
}

export async function createApiKey(name: string, environment: string, token: string): Promise<ApiKeyCreated> {
  return apiPost<ApiKeyCreated>("/api/v1/api-keys", { name, environment }, token);
}

export async function listApiKeys(token: string): Promise<ApiKey[]> {
  return apiGet<ApiKey[]>("/api/v1/api-keys", token);
}

export async function revokeApiKey(id: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/api-keys/${id}/revoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Revoke ${id} failed: ${response.status}`);
  }
}

export async function listNotificationChannels(token: string): Promise<NotificationChannel[]> {
  return apiGet<NotificationChannel[]>("/api/v1/notification-channels", token);
}

export async function createNotificationChannel(
  payload: { name: string; url: string; enabled: boolean },
  token: string,
): Promise<NotificationChannelCreated> {
  return apiPost<NotificationChannelCreated>("/api/v1/notification-channels", payload, token);
}

export async function updateNotificationChannel(
  id: string,
  payload: { name?: string; url?: string; enabled?: boolean },
  token: string,
): Promise<NotificationChannel> {
  return apiPatch<NotificationChannel>(`/api/v1/notification-channels/${id}`, payload, token);
}

export async function testNotificationChannel(id: string, token: string): Promise<TestSendResult> {
  return apiPost<TestSendResult>(`/api/v1/notification-channels/${id}/test`, {}, token);
}

export async function deleteNotificationChannel(id: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/notification-channels/${id}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Delete channel ${id} failed: ${response.status}`);
  }
}

export async function getDeliveries(
  token?: string,
  filters: Partial<Record<string, string | number>> = {},
) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return await apiFetch<Page<AlertDelivery>>(`/api/v1/notification-channels/deliveries${suffix}`, token);
}
