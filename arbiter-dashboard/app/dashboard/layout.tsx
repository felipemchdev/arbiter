import { authOptions } from "@/lib/auth";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { SidebarNav } from "@/components/sidebar-nav";

export default async function DashboardLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    const session = await getServerSession(authOptions);
    if (!session?.accessToken) {
        redirect("/login");
    }

    return (
        <div className="min-h-screen text-[var(--text-primary)] font-sans">
            <div className="grid min-h-screen grid-cols-[260px_1fr]">
                <aside className="border-r border-[var(--border)] bg-[rgba(10,18,35,0.70)] backdrop-blur-[16px] p-6">
                    <div className="mb-8">
                        <div className="text-2xl font-display font-semibold">
                            Arbiter<span className="align-super text-[0.52em] leading-none ml-[2px]">✳</span>
                        </div>
                    </div>
                    <SidebarNav />
                </aside>
                <div className="flex flex-col min-h-screen">
                    <header className="flex items-center px-8 py-4 bg-[rgba(0,0,0,0.40)] backdrop-blur-[12px] border-b border-[var(--border)]">
                        <div>
                            <div className="text-xs uppercase tracking-wider text-[var(--text-muted)] font-display">Signed in as</div>
                            <div className="mt-1 text-sm font-medium">{session.user?.name || "Arbiter organization"}</div>
                        </div>
                    </header>
                    <main className="p-8 flex-1">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}
