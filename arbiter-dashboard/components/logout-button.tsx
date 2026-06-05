"use client";
import { signOut } from "next-auth/react";
import { LogOut } from "lucide-react";
export function LogoutButton() {
  return (
    <button onClick={() => signOut({ callbackUrl: "https://arbiter.felipe-machado.dev/login" })} className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)] rounded-xl transition font-sans"><LogOut size={16} />Sign out</button>
  );
}
