export type RunStatus = "running" | "success" | "failed" | "skipped";
export type TaskStatus = RunStatus | "upstream_failed";
export type PipelineSource = "airflow" | "azure_function" | "sdk";
export type AlertType = "failure" | "duration_exceeded" | "no_run";

export interface DagNode {
  id: string;
  label: string;
  type: string;
  status?: TaskStatus;
}

export interface DagEdge {
  source: string;
  target: string;
}

export interface DagDefinition {
  nodes: DagNode[] | null;
  edges: DagEdge[] | null;
}

export interface Pipeline {
  id: string;
  name: string;
  source: PipelineSource;
  dag_id?: string | null;
  last_run_status?: RunStatus | null;
  last_run_at?: string | null;
  created_at: string;
  dag_definition?: DagDefinition | null;
}

export interface PipelineRun {
  id: string;
  pipeline_id: string;
  run_id: string;
  status: RunStatus;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  error_message?: string | null;
  created_at: string;
}

export interface TaskInstance {
  id: string;
  run_id: string;
  task_id: string;
  status: TaskStatus;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  try_number: number;
  log_url?: string | null;
  error_message?: string | null;
}

export interface Alert {
  id: string;
  pipeline_id: string;
  run_id?: string | null;
  type: string;
  message: string;
  resolved: boolean;
  created_at: string;
}

export interface Metrics {
  runs_today: number;
  failed_today: number;
  active_pipelines: number;
  avg_duration_ms: number;
}
