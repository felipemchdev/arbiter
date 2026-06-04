import { cn } from "@/components/ui/utils";
import type { HTMLAttributes } from "react";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
    return <span className={cn("inline-flex items-center rounded-[6px] border px-[8px] py-[2px] text-[12px] font-medium font-sans", className)} {...props} />;
}