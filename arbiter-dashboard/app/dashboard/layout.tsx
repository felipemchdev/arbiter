import { Card } from "@/components/ui/card";
import { authOptions } from "@/lib/auth";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, LineChart, Bell, ClipboardList } from "lucide-react";

export default async function DashboardLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    const session = await getServerSession(authOptions);
    if (!session?.accessToken) {
        redirect("/login");
    }

    const nav = [
        { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
        { href: "/dashboard/pipelines", label: "Pipelines", icon: ClipboardList },
        { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
    ];

    return (
        <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)]">
            <div className="grid min-h-screen grid-cols-[260px_1fr]">
                <aside className="border-r border-[var(--border)] bg-[var(--bg-surface)] p-6">
                    <div className="mb-8">
                        <div className="text-xs uppercase tracking-[0.35em] text-[var(--text-muted)]">Arbiter</div>
                        <div className="mt-2 text-2xl font-semibold">Observability</div>
                    </div>
                    <nav className="space-y-2">
                        {nav.map(({ href, label, icon: Icon }) => (
                            <Link key={href} href={href} className="flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 text-sm text-[var(--text-muted)] transition hover:border-[var(--border)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)]">
                                <Icon size={16} />
                                {label}
                            </Link>
                        ))}
                    </nav>
                </aside>
                <main className="p-8">
                    <Card className="mb-8 border-[var(--border)] bg-[linear-gradient(135deg,rgba(56,189,248,0.08),rgba(129,140,248,0.04))] p-5">
                        <div className="text-sm text-[var(--text-muted)]">Signed in</div>
                        <div className="mt-1 text-lg font-medium">{session.user?.name || "Arbiter organization"}</div>
                    </Card>
                    {children}
                </main>
            </div>
        </div>
    );
}
