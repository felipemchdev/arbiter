"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { signIn } from "next-auth/react";
import { useState, useTransition } from "react";

type Status = "idle" | "loading" | "success" | "error";

export default function LoginPage() {
  const [org, setOrg] = useState("");
  const [key, setKey] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [, startTransition] = useTransition();

  const handleLogin = () => {
    setStatus("loading");
    startTransition(async () => {
      const result = await signIn("credentials", { username: org, password: key, redirect: false });
      if (result?.error) { setStatus("error"); setTimeout(() => setStatus("idle"), 2000); }
      else { setStatus("success"); window.location.href = "/dashboard"; }
    });
  };

  const btnColor = status === "success" ? "bg-[var(--status-success)]" : status === "error" ? "bg-[var(--status-failed)]" : "bg-[var(--accent-blue)]";

  return (
    <main className="flex min-h-screen items-center justify-center p-6 relative">
      <div className="absolute top-6 left-6"><span className="font-harmond text-2xl tracking-wider text-[var(--accent-blue)]">Arbiter</span></div>
      <Card className={"w-full max-w-sm border-[var(--border)] bg-[var(--bg-card)] shadow-glow transition-all " + (status === "error" ? "border-[var(--status-failed)]" : "")}>
        <CardContent className="flex flex-col items-center gap-5 px-6 py-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--accent-blue)]/10 ring-1 ring-[var(--accent-blue)]/20"><span className="font-harmond text-2xl text-[var(--accent-blue)]">A</span></div>
          <Input placeholder="Organization" value={org} onChange={e => setOrg(e.target.value)} className="bg-[var(--bg-surface)] border-[var(--border)] text-sm h-10" onKeyDown={e => e.key === "Enter" && handleLogin()} />
          <Input type="password" placeholder="API Key" value={key} onChange={e => setKey(e.target.value)} className="bg-[var(--bg-surface)] border-[var(--border)] text-sm h-10" onKeyDown={e => e.key === "Enter" && handleLogin()} />
          <Button className={"w-full h-10 font-harmond text-sm transition-all duration-300 " + btnColor + (status === "error" ? " animate-[shake_0.4s_ease-in-out]" : "")} disabled={status === "loading" || status === "success"} onClick={handleLogin}>
            {status === "loading" ? <Spinner /> : status === "success" ? <Check /> : status === "error" ? <X /> : "Sign in"}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}

function Spinner() { return <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>; }
function Check() { return <svg className="animate-[pop-in_0.3s_ease-out] h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M5 13l4 4L19 7" /></svg>; }
function X() { return <svg className="animate-[pop-in_0.3s_ease-out] h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M18 6L6 18M6 6l12 12" /></svg>; }
