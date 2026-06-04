"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bell, ClipboardList } from "lucide-react";

export function SidebarNav() {
    const pathname = usePathname();

    const nav = [
        { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
        { href: "/dashboard/pipelines", label: "Pipelines", icon: ClipboardList },
        { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
    ];

    return (
        <nav className="space-y-2">
            {nav.map(({ href, label, icon: Icon }) => {
                const isActive = pathname === href || (href !== "/dashboard" && pathname?.startsWith(href));
                return (
                    <Link 
                        key={href} 
                        href={href} 
                        className={`flex items-center gap-3 px-3 py-2 text-sm transition font-sans ${
                            isActive 
                                ? "bg-[rgba(74,144,217,0.15)] border-l-2 border-[var(--accent-blue)] text-[var(--text-primary)]" 
                                : "text-[var(--text-muted)] border-l-2 border-transparent hover:border-[var(--border)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)] rounded-xl"
                        }`}
                        style={isActive ? { borderRadius: "0 12px 12px 0" } : {}}
                    >
                        <Icon size={16} />
                        {label}
                    </Link>
                );
            })}
        </nav>
    );
}
