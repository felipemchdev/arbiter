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

    return (
        <div className="space-y-3">
            {alerts.map((alert) => (
                <Card key={alert.id}>
                    <CardContent className="flex items-start justify-between gap-4">
                        <div>
                            <div className="font-medium">{alert.type}</div>
                            <div className="mt-1 text-sm text-[var(--text-muted)]">{alert.message}</div>
                        </div>
                        <Button
                            disabled={pending}
                            onClick={() =>
                                startTransition(async () => {
                                    await resolveAlert(alert.id, token);
                                    router.refresh();
                                })
                            }
                        >
                            Resolve
                        </Button>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}