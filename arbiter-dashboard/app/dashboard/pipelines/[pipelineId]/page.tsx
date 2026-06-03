import PipelineDetailClient from "./pipeline-detail-client";
import { authOptions } from "@/lib/auth";
import { getPipeline, getPipelineRuns, getAlerts, getRunTasks } from "@/lib/api";
import { getServerSession } from "next-auth";
import { notFound } from "next/navigation";

export default async function PipelineDetailPage({ params }: { params: { pipelineId: string } }) {
  const { pipelineId } = params;
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;
  const pipeline = await getPipeline(pipelineId, token);
  if (!pipeline) {
    notFound();
  }
  const runs = await getPipelineRuns(pipelineId, token);
  const allAlerts = await getAlerts(token);
  const alerts = allAlerts.filter((a) => a.pipeline_id === pipelineId);
  const latestRun = runs[0];
  const tasks = latestRun ? await getRunTasks(latestRun.id, token) : [];

  return (
    <PipelineDetailClient
      pipeline={pipeline}
      runs={runs}
      alerts={alerts}
      tasks={tasks}
      token={token}
    />
  );
}
