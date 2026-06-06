"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useMemo } from "react";

export function RunsChart({ runsToday }: { runsToday: number }) {
  const data = useMemo(
    () =>
      Array.from({ length: 7 }).map((_, index) => ({
        day: `D-${6 - index}`,
        runs: Math.max(runsToday - index * Math.ceil(runsToday / 7 || 1), 0),
      })),
    [runsToday],
  );

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="day" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "var(--r-lg)",
            color: "var(--text)",
          }}
        />
        <Bar dataKey="runs" fill="var(--accent)" radius={[6, 6, 0, 0]} barSize={32} />
      </BarChart>
    </ResponsiveContainer>
  );
}
