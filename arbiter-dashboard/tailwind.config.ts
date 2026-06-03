import type { Config } from "tailwindcss";

export default {
    darkMode: ["class"],
    content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                base: "#06060F",
                surface: "#09090F",
                card: "#0D0D18",
                border: "rgba(56, 189, 248, 0.07)",
                accentBlue: "#38BDF8",
                accentPurple: "#818CF8",
                textPrimary: "#F1F5F9",
                textMuted: "#475569",
                statusSuccess: "#22C55E",
                statusFailed: "#EF4444",
                statusRunning: "#F59E0B",
                statusSkipped: "#64748B",
            },
            boxShadow: {
                glow: "0 0 0 1px rgba(56, 189, 248, 0.08), 0 20px 60px rgba(0, 0, 0, 0.35)",
            },
        },
    },
    plugins: [],
} satisfies Config;