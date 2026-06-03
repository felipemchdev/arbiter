import { AlertList } from "@/components/alert-list";
import { MetricsCard } from "@/components/metrics-card";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { authOptions } from "@/lib/auth";
import { getAlerts, getMetrics } from "@/lib/api";
import { getServerSession } from "next-auth";
import { RunsChart } from "@/components/runs-chart";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;
  const metrics = (await getMetrics(token)) ?? { runs_today: 0, failed_today: 0, active_pipelines: 0, avg_duration_ms: 0 };
  const alerts = await getAlerts(token);

  return (
    <div className="space-y-8">
      <div className="grid gap-4 md:grid-cols-4">
        <MetricsCard label="Runs Hoje" value={metrics.runs_today} />
        <MetricsCard label="Falhas Hoje" value={metrics.failed_today} />
        <MetricsCard label="Pipelines Ativos" value={metrics.active_pipelines} />
        <MetricsCard label="Tempo Médio" value={`${Math.round(metrics.avg_duration_ms)} ms`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.35fr_0.9fr]">
        <Card>
          <CardHeader>
            <div className="text-lg font-semibold">Runs por dia</div>
          </CardHeader>
          <CardContent>
            <RunsChart runsToday={metrics.runs_today} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div className="text-lg font-semibold">Active Alerts</div>
          </CardHeader>
          <CardContent>
            <AlertList alerts={alerts} token={token} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
