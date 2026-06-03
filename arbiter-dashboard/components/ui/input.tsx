import { cn } from "@/components/ui/utils";
import type { InputHTMLAttributes } from "react";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
    return <input className={cn("w-full rounded-md border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm outline-none placeholder:text-[var(--text-muted)]", className)} {...props} />;
}