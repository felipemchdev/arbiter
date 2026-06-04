import { Buffer } from "buffer";
import CredentialsProvider from "next-auth/providers/credentials";
import type { NextAuthOptions } from "next-auth";
import { jwtDecode } from "jwt-decode";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authOptions: NextAuthOptions = {
    session: { strategy: "jwt" },
    providers: [
        CredentialsProvider({
            name: "Arbiter",
            credentials: {
                username: { label: "Email", type: "text", placeholder: "user" },
                password: { label: "Password", type: "password", placeholder: "password" },
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
                const decoded = jwtDecode<{ exp: number; role: string }>(data.access_token);
                return {
                    id: credentials?.username || "user",
                    name: credentials?.username || "Arbiter",
                    accessToken: data.access_token,
                    accessTokenExpires: decoded.exp * 1000,
                    role: decoded.role,
                };
            },
        }),
    ],
    callbacks: {
        async jwt({ token, user }) {
            if (user) {
                token.accessToken = (user as any).accessToken;
                token.accessTokenExpires = (user as any).accessTokenExpires;
                token.role = (user as any).role;
            }
            if (Date.now() > (token.accessTokenExpires as number ?? 0)) {
                token.error = "AccessTokenExpired";
            }
            return token;
        },
        async session({ session, token }) {
            (session as any).accessToken = token.accessToken;
            (session as any).role = token.role;
            (session as any).error = token.error;
            return session;
        },
    },
    pages: {
        signIn: "/login",
    },
    secret: process.env.NEXTAUTH_SECRET,
};
