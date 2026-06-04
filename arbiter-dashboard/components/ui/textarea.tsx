import { cn } from "@/components/ui/utils";
import type { TextareaHTMLAttributes } from "react";

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
    return <textarea className={cn("w-full rounded-[10px] border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm focus:border-[var(--accent-blue)] focus:shadow-[0_0_0_3px_rgba(74,144,217,0.15)] outline-none placeholder:text-[var(--text-muted)]", className)} {...props} />;
}