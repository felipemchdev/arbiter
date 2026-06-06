interface LettermarkProps {
  size?: number
  theme?: "dark" | "light"
  showDot?: boolean
}

export function ArbiterLettermark({ size = 40, theme = "dark", showDot = true }: LettermarkProps) {
  const stroke = theme === "dark" ? "#ffffff" : "#1a1a1a"
  const sw = size / 22

  return (
    <svg width={size} height={size} viewBox="0 0 52 52" fill="none" aria-hidden="true">
      <path
        d="M26 10 L40 46 H34 L26 25 L18 46 H12 Z"
        stroke={stroke}
        strokeWidth={sw * 1.8}
        strokeLinejoin="round"
        fill="none"
      />
      <line
        x1="16" y1="34" x2="36" y2="34"
        stroke={stroke}
        strokeWidth={sw * 1.8}
        strokeLinecap="round"
      />
      {showDot && <circle cx="26" cy="6" r="3.5" fill="#C7FF8F" />}
    </svg>
  )
}
