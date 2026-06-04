import { cn } from "@/components/ui/utils";
import type { ButtonHTMLAttributes } from "react";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
    return (
        <button
            className={cn(
                "inline-flex items-center justify-center rounded-[10px] border border-[var(--border)] bg-transparent px-4 py-2 text-sm font-semibold font-sans text-[var(--text-primary)] transition-all hover:bg-[var(--bg-card)] hover:border-[var(--border-hover)]",
                className,
            )}
            {...props}
        />
    );
}