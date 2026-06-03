
import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
    interface Session {
        accessToken?: string;
        orgId?: string;
        user: DefaultSession["user"] & {
            orgId?: string;
        };
    }

    interface User {
        accessToken?: string;
        orgId?: string;
    }
}

declare module "next-auth/jwt" {
    interface JWT {
        accessToken?: string;
        orgId?: string;
    }
}
