import type { Config } from "tailwindcss";

export default {
    darkMode: ["class"],
    content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
    theme: {
        extend: {
            fontFamily: {
                sans: ['DM Sans', 'sans-serif'],
                display: ['Pragmatica Extended', 'Inter', 'sans-serif'],
            },
            colors: {
                base: "var(--bg-base)",
                surface: "var(--bg-surface)",
                card: "var(--bg-card)",
                border: "var(--border)",
                borderHover: "var(--border-hover)",
                accentBlue: "var(--accent-blue)",
                accentBlueLight: "var(--accent-blue-light)",
                textPrimary: "var(--text-primary)",
                textSecondary: "var(--text-secondary)",
                textMuted: "var(--text-muted)",
                statusSuccess: "var(--status-success)",
                statusFailed: "var(--status-failed)",
                statusRunning: "var(--status-running)",
                statusSkipped: "var(--status-skipped)",
            },
            boxShadow: {
                glow: "0 0 0 1px rgba(56, 189, 248, 0.08), 0 20px 60px rgba(0, 0, 0, 0.35)",
            },
        },
    },
    plugins: [],
} satisfies Config;