import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
    interface Session {
        accessToken?: string;
        refreshToken?: string;
        error?: string;
        orgId?: string;
        user: DefaultSession["user"] & {
            orgId?: string;
        };
    }

    interface User {
        accessToken?: string;
        refreshToken?: string;
        accessTokenExpires?: number;
        role?: string;
        orgId?: string;
    }
}

declare module "next-auth/jwt" {
    interface JWT {
        accessToken?: string;
        refreshToken?: string;
        accessTokenExpires?: number;
        role?: string;
        orgId?: string;
        error?: string;
    }
}
