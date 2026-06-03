import { cn } from "@/components/ui/utils";
import type { HTMLAttributes } from "react";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
    return <span className={cn("inline-flex items-center rounded-full border border-[var(--border)] px-2.5 py-1 text-xs font-medium", className)} {...props} />;
}