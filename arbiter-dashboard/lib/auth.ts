import CredentialsProvider from "next-auth/providers/credentials";
import type { NextAuthOptions } from "next-auth";
import { jwtDecode } from "jwt-decode";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt", maxAge: 30 * 24 * 60 * 60 },
  providers: [
    CredentialsProvider({
      name: "Arbiter",
      credentials: {
        username: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null;
        const res = await fetch(API_URL + "/api/v1/auth/token", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ username: credentials.username, password: credentials.password }),
        });
        if (!res.ok) return null;
        const data = await res.json() as { access_token: string; refresh_token: string };
        const decoded = jwtDecode<{ exp: number; role: string }>(data.access_token);
        return {
          id: credentials.username,
          name: credentials.username,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
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
        token.refreshToken = (user as any).refreshToken;
        token.accessTokenExpires = (user as any).accessTokenExpires;
        token.role = (user as any).role;
        token.username = user.name;
      }
      const expiry = token.accessTokenExpires as number | undefined;
      if (expiry && Date.now() > expiry) {
        const refresh = token.refreshToken as string | undefined;
        if (refresh) {
          try {
            const res = await fetch(API_URL + "/api/v1/auth/refresh", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh_token: refresh }),
            });
            if (res.ok) {
              const data = await res.json() as { access_token: string; refresh_token: string };
              const decoded = jwtDecode<{ exp: number; role: string }>(data.access_token);
              token.accessToken = data.access_token;
              token.refreshToken = data.refresh_token;
              token.accessTokenExpires = decoded.exp * 1000;
              token.role = decoded.role;
              token.error = undefined;
              return token;
            }
          } catch {}
        }
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
  pages: { signIn: "/login" },
  secret: process.env.NEXTAUTH_SECRET,
};
