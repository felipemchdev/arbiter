import { cn } from "@/components/ui/utils";
import type { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("rounded-[var(--card-radius)] border border-[var(--border)] bg-[var(--bg-card)] backdrop-blur-[var(--card-blur)] transition-all duration-200 ease-in-out hover:bg-[var(--bg-card-hover)] hover:border-[var(--border-hover)]", className)} {...props} />;
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("border-b border-[var(--border)] p-4", className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("p-4", className)} {...props} />;
}