import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { authOptions } from "@/lib/auth";
import { getPipelines } from "@/lib/api";
import { getServerSession } from "next-auth";
import Link from "next/link";

export default async function PipelinesPage() {
    const session = await getServerSession(authOptions);
    const pipelines = await getPipelines(session?.accessToken);

    return (
        <Card>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableHeader>Name</TableHeader>
                        <TableHeader>Source</TableHeader>
                        <TableHeader>Status</TableHeader>
                        <TableHeader>Last Run</TableHeader>
                        <TableHeader>Actions</TableHeader>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {pipelines.map((pipeline) => (
                        <TableRow key={pipeline.id}>
                            <TableCell>{pipeline.name}</TableCell>
                            <TableCell><StatusBadge status={pipeline.source} /></TableCell>
                            <TableCell><StatusBadge status={pipeline.last_run_status} /></TableCell>
                            <TableCell>{pipeline.last_run_at ? new Date(pipeline.last_run_at).toLocaleString() : "—"}</TableCell>
                            <TableCell>
                                <Link className="inline-flex items-center justify-center rounded-md border border-[var(--border)] bg-[var(--bg-card)] px-4 py-2 text-sm font-medium" href={`/dashboard/pipelines/${pipeline.id}`}>
                                    View
                                </Link>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </Card>
    );
}