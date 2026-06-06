'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface RunsPerDay {
  date: string
  label: string
  count: number
  failed: number
}

export function RunsChart({ data }: { data: RunsPerDay[] }) {
  if (!data?.length) return (
    <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>No runs in the last 7 days</span>
    </div>
  )

  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data} barGap={2} barCategoryGap="30%">
        <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" />
        <XAxis
          dataKey="label"
          tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'DM Sans' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'DM Sans' }}
          axisLine={false}
          tickLine={false}
          width={28}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-overlay)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            fontSize: 12,
            fontFamily: 'DM Sans',
            color: 'var(--text)',
          }}
          cursor={{ fill: 'var(--bg-surface)' }}
          formatter={(value: number, name: string) => [value, name === 'count' ? 'Runs' : 'Failed']}
        />
        <Bar dataKey="count" fill="var(--accent)" radius={[4,4,0,0]} opacity={0.85} />
        <Bar dataKey="failed" fill="var(--failed)" radius={[4,4,0,0]} opacity={0.55} />
      </BarChart>
    </ResponsiveContainer>
  )
}
