'use client'
import { ArbiterSymbol } from "./symbol"
import { useEffect, useState } from "react"

interface LogoProps {
  variant?: "symbol-only" | "symbol-name" | "full"
  size?: "sm" | "md" | "lg"
}

const sizes = {
  sm: { symbol: 16, text: 14, gap: 7 },
  md: { symbol: 20, text: 16, gap: 9 },
  lg: { symbol: 28, text: 22, gap: 12 },
}

export function ArbiterLogo({ variant = "symbol-name", size = "md" }: LogoProps) {
  const [theme, setTheme] = useState<"dark" | "light">("dark")

  useEffect(() => {
    const el = document.documentElement
    const update = () => {
      const t = el.getAttribute("data-theme") as "dark" | "light" | null
      setTheme(t ?? "dark")
    }
    update()
    const obs = new MutationObserver(update)
    obs.observe(el, { attributes: true, attributeFilter: ["data-theme"] })
    return () => obs.disconnect()
  }, [])

  const s = sizes[size]
  const color = theme === "dark" ? "#ffffff" : "#1a1a1a"

  return (
    <div style={{ display: "flex", alignItems: "center", gap: s.gap, userSelect: "none" }}>
      <ArbiterSymbol size={s.symbol} theme={theme} />
      {variant !== "symbol-only" && (
        <span style={{
          fontFamily: "'Pragmatica Extended', 'DM Sans', sans-serif",
          fontWeight: 700,
          fontSize: s.text,
          color,
          letterSpacing: "-0.3px",
          lineHeight: 1,
        }}>
          Arbiter
          <sup style={{
            fontSize: "0.44em",
            verticalAlign: "super",
            marginLeft: "2px",
            color: "#C7FF8F",
            lineHeight: 1,
          }}>●</sup>
        </span>
      )}
    </div>
  )
}
