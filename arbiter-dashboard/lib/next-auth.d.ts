import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    orgId?: string;
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
