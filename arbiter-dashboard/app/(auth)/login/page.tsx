"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { signIn } from "next-auth/react";
import { useState, useTransition } from "react";

export default function LoginPage() {
    const [organization, setOrganization] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [pending, startTransition] = useTransition();

    return (
        <main className="flex min-h-screen items-center justify-center p-6">
            <div className="w-full max-w-md">
                <Card>
                    <CardHeader>
                        <div className="text-2xl font-semibold">Arbiter</div>
                        <div className="mt-1 text-sm text-[var(--text-muted)]">Enter your organization and API key.</div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Input placeholder="Organization" value={organization} onChange={(event) => setOrganization(event.target.value)} />
                        <Input placeholder="API Key" type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
                        <Button
                            className="w-full"
                            disabled={pending}
                            onClick={() =>
                                startTransition(async () => {
                                    await signIn("credentials", {
                                        username: organization,
                                        password: apiKey,
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