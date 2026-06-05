import { Buffer } from "buffer";
import CredentialsProvider from "next-auth/providers/credentials";
import type { NextAuthOptions } from "next-auth";
import { jwtDecode } from "jwt-decode";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fetchToken = async (username: string, password: string) => {
  const res = await fetch(API_URL + "/api/v1/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access_token: string };
  const decoded = jwtDecode<{ exp: number; role: string }>(data.access_token);
  return { accessToken: data.access_token, expires: decoded.exp * 1000, role: decoded.role };
};

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
        const result = await fetchToken(credentials.username, credentials.password);
        if (!result) return null;
        return {
          id: credentials.username,
          name: credentials.username,
          accessToken: result.accessToken,
          accessTokenExpires: result.expires,
          role: result.role,
          password: credentials.password,
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
        token.username = user.name;
        token.password = (user as any).password;
      }
      const expiry = token.accessTokenExpires as number | undefined;
      if (expiry && Date.now() > expiry) {
        const u = token.username as string;
        const p = token.password as string;
        if (u && p) {
          const r = await fetchToken(u, p);
          if (r) {
            token.accessToken = r.accessToken;
            token.accessTokenExpires = r.expires;
            token.role = r.role;
            token.error = undefined;
            return token;
          }
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
