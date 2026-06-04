import { useSession } from "next-auth/react";

export function useRole() {
  const { data: session } = useSession();
  return (session as any)?.role ?? "viewer";
}

export function useIsOwner() {
  return useRole() === "owner";
}
