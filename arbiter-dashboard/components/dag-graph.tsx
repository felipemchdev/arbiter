"use client";

import dagre from "dagre";
import { useMemo } from "react";
import ReactFlow, { Background, Controls, Handle, Position, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";

import type { TaskStatus } from "@/lib/types";

const nodeWidth = 180;
const nodeHeight = 72;

function buildLayout(nodes: Array<{ id: string; label: string; status?: TaskStatus }>, edges: Array<{ source: string; target: string }>) {
    const graph = new dagre.graphlib.Graph();
    graph.setGraph({ rankdir: "LR", nodesep: 40, ranksep: 60 });
    graph.setDefaultEdgeLabel(() => ({}));

    nodes.forEach((node) => graph.setNode(node.id, { width: nodeWidth, height: nodeHeight }));
    edges.forEach((edge) => graph.setEdge(edge.source, edge.target));
    dagre.layout(graph);

    const layoutNodes: Node[] = nodes.map((node) => {
        const position = graph.node(node.id) ?? { x: 0, y: 0 };
        return {
            id: node.id,
            data: { label: node.label, status: node.status },
            position: { x: position.x - nodeWidth / 2, y: position.y - nodeHeight / 2 },
            type: "dagNode",
        };
    });

    const layoutEdges: Edge[] = edges.map((edge) => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: true,
        style: { stroke: "rgba(56,189,248,0.35)" },
    }));

    return { layoutNodes, layoutEdges };
}

function DagNode({ data }: { data: { label?: string; status?: TaskStatus } }) {
    const status = (data.status || "skipped") as TaskStatus;
    const color =
        status === "success"
            ? "border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.08)]"
            : status === "failed"
                ? "border-[rgba(239,68,68,0.3)] bg-[rgba(239,68,68,0.08)]"
                : status === "running"
                    ? "border-[rgba(245,158,11,0.3)] bg-[rgba(245,158,11,0.08)]"
                    : "border-[rgba(100,116,139,0.3)] bg-[rgba(100,116,139,0.08)]";
    return (
        <div className={`rounded-2xl border px-4 py-3 text-left shadow-glow ${color}`}>
            <Handle type="target" position={Position.Left} className="!bg-[var(--accent-blue)]" />
            <div className="text-sm font-medium">{data.label}</div>
            <div className="mt-1 text-xs text-[var(--text-muted)]">{status}</div>
            <Handle type="source" position={Position.Right} className="!bg-[var(--accent-blue)]" />
        </div>
    );
}

const nodeTypes = { dagNode: DagNode };

export function DagGraph({ nodes, edges }: { nodes: Array<{ id: string; label: string; status?: TaskStatus }>; edges: Array<{ source: string; target: string }> }) {
    const { layoutNodes, layoutEdges } = useMemo(() => buildLayout(nodes, edges), [nodes, edges]);

    return (
        <div className="h-[560px] rounded-3xl border border-[var(--border)] bg-[var(--bg-surface)]">
            <ReactFlow nodes={layoutNodes} edges={layoutEdges} nodeTypes={nodeTypes} fitView>
                <Background color="rgba(56,189,248,0.12)" gap={24} />
                <Controls />
            </ReactFlow>
        </div>
    );
}