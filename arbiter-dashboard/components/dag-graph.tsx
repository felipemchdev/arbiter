"use client";

import dagre from "dagre";
import { useMemo, useState } from "react";
import ReactFlow, { Background, Controls, Handle, Position, MarkerType, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";

import type { TaskStatus } from "@/lib/types";
import { StatusBadge } from "@/components/status-badge";

const nodeWidth = 200;
const nodeHeight = 80;

function buildLayout(
  nodes: Array<{ id: string; label: string; status?: TaskStatus }>,
  edges: Array<{ source: string; target: string }>,
) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  nodes.forEach((node) => g.setNode(node.id, { width: nodeWidth, height: nodeHeight }));
  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  dagre.layout(g);

  const layoutNodes: Node[] = nodes.map((node) => {
    const pos = g.node(node.id) ?? { x: 0, y: 0 };
    return {
      id: node.id,
      data: { label: node.label, status: node.status },
      position: { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 },
      type: "dagNode",
    };
  });

  const layoutEdges: Edge[] = edges.map((edge) => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    animated: true,
  }));

  return { layoutNodes, layoutEdges };
}

function DagNode({ data }: { data: { label?: string; status?: TaskStatus } }) {
  const status = (data.status || "skipped") as TaskStatus;
  const statusColor =
    status === "success"
      ? "var(--status-success)"
      : status === "failed"
        ? "var(--status-failed)"
        : status === "running"
          ? "var(--status-running)"
          : "var(--status-skipped)";
          
  return (
    <div
      style={{
        background: 'rgba(25, 42, 78, 0.70)',
        border: `1px solid ${statusColor}`,
        borderRadius: '10px',
        backdropFilter: 'blur(8px)',
        color: '#FFFFFF',
        fontFamily: 'DM Sans, sans-serif',
        fontSize: '13px',
        padding: '8px 14px',
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-[var(--accent-blue)]" />
      <div className="font-medium">{data.label}</div>
      <div className="mt-1">
        <StatusBadge status={status} />
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-[var(--accent-blue)]" />
    </div>
  );
}

const nodeTypes = { dagNode: DagNode };

interface DagNodeSpec {
  id: string;
  label: string;
  status?: TaskStatus;
}

interface TaskDetail {
  task_id: string;
  status: TaskStatus;
  duration_ms?: number | null;
  try_number: number;
  error_message?: string | null;
}

export function DagGraph({
  nodes,
  edges,
  tasks,
}: {
  nodes: DagNodeSpec[];
  edges: Array<{ source: string; target: string }>;
  tasks: TaskDetail[];
}) {
  const { layoutNodes, layoutEdges } = useMemo(() => buildLayout(nodes, edges), [nodes, edges]);
  const [selectedTask, setSelectedTask] = useState<TaskDetail | null>(null);

  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    const task = tasks.find((t) => t.task_id === node.id);
    setSelectedTask(task ?? null);
  };

  const taskMap = useMemo(() => {
    const map = new Map<string, TaskDetail>();
    tasks.forEach((t) => map.set(t.task_id, t));
    return map;
  }, [tasks]);

  const enrichedNodes = useMemo(
    () =>
      layoutNodes.map((n) => ({
        ...n,
        data: { ...n.data, status: taskMap.get(n.id)?.status ?? ("skipped" as TaskStatus) },
      })),
    [layoutNodes, taskMap],
  );

  return (
    <div className="relative flex h-[600px] rounded-[var(--card-radius)] border border-[var(--border)] bg-[#000000] overflow-hidden">
      <div className="flex-1">
        <ReactFlow
          nodes={enrichedNodes}
          edges={layoutEdges}
          nodeTypes={nodeTypes}
          fitView
          onNodeClick={handleNodeClick}
          proOptions={{ hideAttribution: true }}
          style={{ background: 'transparent' }}
          defaultEdgeOptions={{
            style: { stroke: 'rgba(100, 140, 220, 0.40)', strokeWidth: 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(100, 140, 220, 0.40)' }
          }}
        >
          <Background color="rgba(100, 140, 220, 0.06)" gap={20} />
          <Controls />
        </ReactFlow>
      </div>

      {selectedTask && (
        <div className="w-[320px] shrink-0 border-l border-[var(--border)] bg-[rgba(10,18,40,0.90)] backdrop-blur-[20px] p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="text-sm font-semibold text-[var(--text-primary)]">Task Details</div>
            <button
              onClick={() => setSelectedTask(null)}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
            >
              ✕
            </button>
          </div>
          <div className="space-y-4 text-sm font-sans">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Task ID</div>
              <div className="mt-1 font-medium text-[var(--text-primary)]">{selectedTask.task_id}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Status</div>
              <div className="mt-1">
                <StatusBadge status={selectedTask.status} />
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Duration</div>
              <div className="mt-1 text-[var(--text-primary)]">{selectedTask.duration_ms ? `${selectedTask.duration_ms} ms` : "—"}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Try Number</div>
              <div className="mt-1 text-[var(--text-primary)]">{selectedTask.try_number}</div>
            </div>
            {selectedTask.error_message && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Error</div>
                <div className="mt-1 rounded-[10px] border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.06)] p-3 text-xs text-[var(--status-failed)] font-mono overflow-auto max-h-[150px]">
                  {selectedTask.error_message}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
