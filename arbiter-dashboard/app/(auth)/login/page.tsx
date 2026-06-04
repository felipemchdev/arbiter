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

  const btnColor = status === "success" ? "bg-[var(--status-success)] text-white" : status === "error" ? "bg-[var(--status-failed)] text-white" : "bg-white text-black";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 relative">
      <div className="absolute top-8 left-8">
        <span className="font-display font-semibold text-2xl">
          Arbiter
          <span className="align-super text-[0.52em] leading-none ml-[2px]">✳</span>
        </span>
      </div>
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-display font-semibold mb-2">
          Arbiter
          <span className="align-super text-[0.52em] leading-none ml-[2px]">✳</span>
        </h1>
        <p className="text-[var(--text-secondary)] text-sm">Welcome to your new best friend in pipelines observability</p>
      </div>
      <Card className={"w-full max-w-sm border-[var(--border)] bg-[var(--bg-card)] backdrop-blur-[var(--card-blur)] shadow-xl transition-all " + (status === "error" ? "border-[var(--status-failed)]" : "hover:border-[var(--border-hover)] hover:bg-[var(--bg-card-hover)]")}>
        <CardContent className="flex flex-col gap-5 px-6 py-8">
          <Input placeholder="user" value={org} onChange={e => setOrg(e.target.value)} className="bg-[rgba(15,25,50,0.6)] border-[var(--border)] rounded-[10px] text-sm h-11 text-white focus:border-[var(--accent-blue)] focus:ring-[3px] focus:ring-[rgba(74,144,217,0.15)] focus:outline-none" onKeyDown={e => e.key === "Enter" && handleLogin()} />
          <Input type="password" placeholder="password" value={key} onChange={e => setKey(e.target.value)} className="bg-[rgba(15,25,50,0.6)] border-[var(--border)] rounded-[10px] text-sm h-11 text-white focus:border-[var(--accent-blue)] focus:ring-[3px] focus:ring-[rgba(74,144,217,0.15)] focus:outline-none" onKeyDown={e => e.key === "Enter" && handleLogin()} />
          <Button className={"w-full h-11 rounded-[10px] font-sans font-semibold transition-all duration-200 " + btnColor + (status === "error" ? " animate-[shake_0.4s_ease-in-out]" : "")} disabled={status === "loading" || status === "success"} onClick={handleLogin}>
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

