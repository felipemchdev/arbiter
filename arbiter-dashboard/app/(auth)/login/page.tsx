"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { signIn } from "next-auth/react";
import { useState, useTransition } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [pending, startTransition] = useTransition();

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md">
        <Card>
          <CardHeader>
            <div className="text-2xl font-semibold">Arbiter</div>
            <div className="mt-1 text-sm text-[var(--text-muted)]">Enter your credentials.</div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input placeholder="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            <Input placeholder="Senha" type="password" value={senha} onChange={(event) => setSenha(event.target.value)} />
            <Button
              className="w-full"
              disabled={pending}
              onClick={() =>
                startTransition(async () => {
                  await signIn("credentials", {
                    username: email,
                    password: senha,
                    callbackUrl: "/dashboard",
                  });
                })
              }
            >
              Sign in
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
