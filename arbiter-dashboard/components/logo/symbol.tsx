interface SymbolProps {
  size?: number
  theme?: "dark" | "light"
  className?: string
}

export function ArbiterSymbol({ size = 24, theme = "dark", className }: SymbolProps) {
  const primary = theme === "dark" ? "#C7FF8F" : "#1a1a1a"
  const secondary = theme === "dark" ? "rgba(199,255,143,0.38)" : "rgba(26,26,26,0.30)"
  const fill = theme === "dark" ? "#C7FF8F" : "#1a1a1a"

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 52 52"
      fill="none"
      className={className}
      aria-label="Arbiter symbol"
    >
      <circle cx="26" cy="27" r="6.5" fill={fill} />
      <circle cx="9"  cy="13" r="4.5" stroke={primary}   strokeWidth="1.5" fill="none" />
      <circle cx="43" cy="13" r="4.5" stroke={primary}   strokeWidth="1.5" fill="none" />
      <circle cx="26" cy="45" r="3.5" stroke={secondary} strokeWidth="1.5" fill="none" />
      <line x1="13"   y1="16.5" x2="21.5" y2="23" stroke={primary}   strokeWidth="1.3" strokeLinecap="round" />
      <line x1="39"   y1="16.5" x2="30.5" y2="23" stroke={primary}   strokeWidth="1.3" strokeLinecap="round" />
      <line x1="26"   y1="33.5" x2="26"   y2="41.5" stroke={secondary} strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  )
}
