import type { Alert, ApiKey, ApiKeyCreated, Pipeline, PipelineRun, TaskInstance } from "@/lib/types";

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

export async function getPipeline(id: string, token?: string) {
  return await apiFetch<Pipeline>(`/api/v1/pipelines/${id}`, token);
}

export async function getPipelineRuns(id: string, token?: string) {
  return (await apiFetch<PipelineRun[]>(`/api/v1/pipelines/${id}/runs`, token)) ?? [];
}

export async function getPipelineAlerts(id: string, token?: string) {
  return (await apiFetch<Alert[]>(`/api/v1/pipelines/${id}/alerts`, token)) ?? [];
}

export async function getRun(id: string, token?: string) {
  return await apiFetch<PipelineRun>(`/api/v1/runs/${id}`, token);
}

export async function getRunTasks(id: string, token?: string) {
  return (await apiFetch<TaskInstance[]>(`/api/v1/runs/${id}/tasks`, token)) ?? [];
}

export async function getAlerts(token?: string) {
  return (await apiFetch<Alert[]>("/api/v1/alerts", token)) ?? [];
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

export async function getPipelines(token?: string) {
  return (await apiFetch<Pipeline[]>("/api/v1/pipelines", token)) ?? [];
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
