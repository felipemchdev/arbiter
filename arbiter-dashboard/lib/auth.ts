import { Buffer } from "buffer";
import CredentialsProvider from "next-auth/providers/credentials";
import type { NextAuthOptions } from "next-auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authOptions: NextAuthOptions = {
    session: { strategy: "jwt" },
    providers: [
        CredentialsProvider({
            name: "Arbiter",
            credentials: {
                username: { label: "Organization", type: "text" },
                password: { label: "API Key", type: "password" },
            },
            async authorize(credentials) {
                const response = await fetch(`${API_URL}/api/v1/auth/token`, {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: new URLSearchParams({
                        username: credentials?.username || "",
                        password: credentials?.password || "",
                    }),
                });
                if (!response.ok) {
                    return null;
                }
                const data = (await response.json()) as { access_token: string };
                return {
                    id: credentials?.username || "org",
                    name: credentials?.username || "Arbiter",
                    accessToken: data.access_token,
                    orgId: credentials?.username || "org",
                };
            },
        }),
    ],
    callbacks: {
        async jwt({ token, user }) {
            if (user) {
                token.accessToken = user.accessToken;
                token.orgId = user.orgId;
            }
            if (token.accessToken) { try { const payload = JSON.parse(Buffer.from((token.accessToken as string).split(".")[1], "base64").toString()) as { exp: number }; if (Date.now() >= payload.exp * 1000) { return { ...token, error: "TokenExpired" }; } } catch {} } return token;
        },
        async session({ session, token }) {
            if (token.error === "TokenExpired") { (session as any).error = "TokenExpired"; return session; } session.accessToken = token.accessToken;
            session.orgId = token.orgId;
            return session;
        },
    },
    pages: {
        signIn: "/login",
    },
    secret: process.env.NEXTAUTH_SECRET,
};