"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { resolveAlert } from "@/lib/api";
import type { Alert } from "@/lib/types";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function AlertList({ alerts, token }: { alerts: Alert[]; token?: string }) {
    const router = useRouter();
    const [pending, startTransition] = useTransition();

    const getBorderColor = (type: string) => {
        if (type === "failure") return "border-l-[4px] border-l-[var(--status-failed)]";
        if (type === "duration_exceeded") return "border-l-[4px] border-l-[var(--status-running)]";
        if (type === "no_run") return "border-l-[4px] border-l-[var(--status-skipped)]";
        return "border-l-[4px] border-l-[var(--border)]";
    };

    return (
        <div className="space-y-3">
            {alerts.map((alert) => (
                <Card key={alert.id} className={getBorderColor(alert.type)}>
                    <CardContent className="flex items-center justify-between gap-4 p-4">
                        <div>
                            <div className="font-medium font-sans text-[var(--text-primary)] capitalize">{alert.type.replace('_', ' ')}</div>
                            <div className="mt-1 text-sm text-[var(--text-muted)] font-sans">{alert.message}</div>
                        </div>
                        <Button
                            className="bg-transparent border border-[var(--border)] text-[var(--text-primary)] rounded-[10px] hover:bg-[var(--bg-surface)] hover:text-white transition"
                            disabled={pending}
                            onClick={() =>
                                startTransition(async () => {
                                    await resolveAlert(alert.id, token);
                                    router.refresh();
                                })
                            }
                        >
                            Resolver
                        </Button>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}