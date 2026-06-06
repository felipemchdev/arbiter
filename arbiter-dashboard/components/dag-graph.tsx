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

const statusColor = (status: string) =>
  status === "success"
    ? "var(--success)"
    : status === "failed"
      ? "var(--failed)"
      : status === "running"
        ? "var(--running)"
        : "var(--skipped)";

function DagNode({ data }: { data: { label?: string; status?: TaskStatus } }) {
  const status = (data.status || "skipped") as TaskStatus;
  const color = statusColor(status);

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${color}`,
        borderRadius: 10,
        padding: '8px 16px',
        color: 'var(--text)',
        fontFamily: "'DM Sans', sans-serif",
        fontSize: 13, fontWeight: 500,
        minWidth: 130,
        textAlign: 'center' as const,
        backdropFilter: 'blur(8px)',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: 'var(--accent)' }} />
      <div style={{ fontWeight: 500 }}>{data.label}</div>
      <div style={{ marginTop: 4 }}>
        <StatusBadge status={status} size="sm" />
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent)' }} />
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
    <div style={{ position: 'relative', display: 'flex', height: 420, borderRadius: 'var(--r-lg)', border: '1px solid var(--border)', background: 'transparent', overflow: 'hidden' }}>
      <div style={{ flex: 1 }}>
        <ReactFlow
          nodes={enrichedNodes}
          edges={layoutEdges}
          nodeTypes={nodeTypes}
          fitView
          onNodeClick={handleNodeClick}
          proOptions={{ hideAttribution: true }}
          style={{ background: 'transparent' }}
          defaultEdgeOptions={{
            style: { stroke: 'var(--border-hover)', strokeWidth: 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(255,255,255,0.20)' },
          }}
        >
          <Background color="var(--border)" gap={24} size={1} />
          <Controls style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)' }} />
        </ReactFlow>
      </div>

      {selectedTask && (
        <div className="animate-slide-right" style={{
          width: 340, flexShrink: 0,
          borderLeft: '1px solid var(--border)',
          background: 'var(--bg-overlay)',
          backdropFilter: 'blur(24px)',
          padding: 28,
          overflowY: 'auto',
          display: 'flex', flexDirection: 'column', gap: 20,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>Task</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', fontFamily: "'JetBrains Mono', monospace" }}>
                {selectedTask.task_id}
              </div>
            </div>
            <button onClick={() => setSelectedTask(null)} style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--r-md)', width: 32, height: 32,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-muted)',
            }}>{String.fromCharCode(10005)}</button>
          </div>

          <StatusBadge status={selectedTask.status} />

          {[
            { label: 'Duration',    value: selectedTask.duration_ms ? `${(selectedTask.duration_ms / 1000).toFixed(1)}s` : '—', mono: true },
            { label: 'Try number',  value: selectedTask.try_number, mono: true },
            { label: 'Started at',  value: '—', mono: false },
          ].map(({ label, value, mono }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</span>
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)', fontFamily: mono ? "'JetBrains Mono', monospace" : "'DM Sans', sans-serif" }}>{value}</span>
            </div>
          ))}

          {selectedTask.error_message && (
            <div style={{
              background: 'rgba(239,68,68,0.06)',
              border: '1px solid rgba(239,68,68,0.18)',
              borderRadius: 'var(--r-md)',
              padding: '12px 14px',
            }}>
              <div style={{ fontSize: 10, color: 'var(--failed)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>Error</div>
              <pre style={{
                fontSize: 11, color: 'rgba(239,68,68,0.85)',
                fontFamily: "'JetBrains Mono', monospace",
                lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                margin: 0,
              }}>{selectedTask.error_message}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
