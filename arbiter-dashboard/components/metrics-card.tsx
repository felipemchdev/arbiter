import { Card, CardContent } from "@/components/ui/card";

export function MetricsCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
    return (
        <Card>
            <CardContent>
                <div className="text-sm text-[var(--text-muted)]">{label}</div>
                <div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
                {hint ? <div className="mt-2 text-xs text-[var(--text-muted)]">{hint}</div> : null}
            </CardContent>
        </Card>
    );
}