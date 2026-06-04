"use client";

export function RoleBadge({ role }: { role: string }) {
  if (role === "owner") return null;

  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.1em",
        color: "rgba(245,158,11,0.80)",
        background: "rgba(245,158,11,0.10)",
        border: "1px solid rgba(245,158,11,0.20)",
        borderRadius: 4,
        padding: "3px 8px",
        marginRight: 12,
        textTransform: "uppercase",
      }}
    >
      View Only
    </span>
  );
}
