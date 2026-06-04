import { StatusBadge } from "@/components/status-badge";
import { SourceBadge } from "@/components/source-badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { authOptions } from "@/lib/auth";
import { getPipelines } from "@/lib/api";
import { getServerSession } from "next-auth";
import Link from "next/link";

export default async function PipelinesPage() {
  const session = await getServerSession(authOptions);
  const pipelines = await getPipelines(session?.accessToken);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold font-display text-[var(--text-primary)]">Pipelines</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">{pipelines.length} pipelines found</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Name</TableHeader>
                <TableHeader>Source</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Last Run</TableHeader>
                <TableHeader>Action</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {pipelines.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-[var(--text-muted)] py-8">
                    No pipelines found.
                  </TableCell>
                </TableRow>
              ) : (
                pipelines.map((pipeline) => (
                  <TableRow key={pipeline.id}>
                    <TableCell className="font-medium">{pipeline.name}</TableCell>
                    <TableCell>
                      <SourceBadge source={pipeline.source} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={pipeline.last_run_status} />
                    </TableCell>
                    <TableCell className="text-[var(--text-muted)]">
                      {pipeline.last_run_at
                        ? new Date(pipeline.last_run_at).toLocaleString()
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Link href={`/dashboard/pipelines/${pipeline.id}`}>
                        <Button>Ver</Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
