import type { Alert, Pipeline, PipelineRun, TaskInstance } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T | null> {
    if (!response.ok) {
        return null;
    }
    return (await response.json()) as T;
}

export async function apiFetch<T>(path: string, token?: string, init: RequestInit = {}): Promise<T | null> {
    const response = await fetch(`${API_URL}${path}`, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(init.headers || {}),
        },
        cache: "no-store",
    });
    return parseResponse<T>(response);
}

export async function getPipelines(token?: string) {
    return (await apiFetch<Pipeline[]>("/api/v1/pipelines", token)) ?? [];
}

export async function getPipeline(id: string, token?: string) {
    return await apiFetch<Pipeline>(`/api/v1/pipelines/${id}`, token);
}

export async function getPipelineRuns(id: string, token?: string) {
    return (await apiFetch<PipelineRun[]>(`/api/v1/pipelines/${id}/runs`, token)) ?? [];
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