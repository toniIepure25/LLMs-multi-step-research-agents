import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary brand = teal/mint ("Obsidian Aurora").  Used for the
        // hero word accent, focus rings, the Run button left stop,
        // pipeline-active glow, citation chips, and chip-hover borders.
        brand: {
          50:  "#ECFEFF",
          100: "#CFFAFE",
          200: "#99F6E4",   // soft mint (hero accent)
          300: "#5EEAD4",   // mint (chip border / inline citation text)
          400: "#2DD4BF",   // teal (icon accents / active rings)
          500: "#14B8A6",   // primary teal (button left stop)
          600: "#0D9488",
          700: "#0F766E",
          800: "#115E59",
          900: "#134E4A",
        },
        // Slate ramp for foreground text on dark obsidian.
        // 50 white headlines → 300 body → 400 muted labels → 500 placeholders.
        ink: {
          50:  "#F8FAFC",   // pure (headings / primary text)
          100: "#F1F5F9",
          200: "#E2E8F0",   // strong body
          300: "#CBD5E1",   // body
          400: "#94A3B8",   // muted labels
          500: "#64748B",   // placeholders / fine print
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
        },
        // Obsidian / near-black graphite surfaces.
        surface: {
          base:   "#030712",   // body bg (deep obsidian)
          raised: "#0F172A",   // primary card (slate-900)
          inset:  "#070A12",   // inset / inputs
          hover:  "#1E293B",   // hover for rows (slate-800)
        },
        accent: {
          green:  "#10B981",   // safety + supported (emerald)
          amber:  "#F59E0B",   // (kept for ResultSummary tone variant)
          red:    "#F87171",   // muted red, used sparingly
          // Aurora highlights.  "cyan" -> ice blue.  "violet" -> soft violet.
          cyan:   "#38BDF8",   // ice blue (button right stop, comet)
          violet: "#A78BFA",   // soft violet (atmosphere)
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Inter", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        glow:       "0 0 40px -10px rgba(94,234,212,0.55)",
        glowSoft:   "0 0 28px -14px rgba(94,234,212,0.45)",
        glowGreen:  "0 0 28px -10px rgba(16,185,129,0.55)",
        glowAmber:  "0 0 28px -10px rgba(245,158,11,0.55)",
        glowCyan:   "0 0 28px -10px rgba(56,189,248,0.6)",
        glowViolet: "0 0 28px -10px rgba(167,139,250,0.5)",
        soft:       "0 16px 50px -28px rgba(0,0,0,0.85)",
        ring:       "inset 0 0 0 1px rgba(148,163,184,0.10)",
      },
      backgroundImage: {
        "grid-dark":
          "linear-gradient(rgba(148,163,184,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.05) 1px, transparent 1px)",
        "panel-gradient":
          "linear-gradient(180deg, rgba(248,250,252,0.04) 0%, rgba(248,250,252,0.01) 100%)",
        "hero-gradient":
          "radial-gradient(120% 100% at 0% 0%, rgba(45,212,191,0.14) 0%, transparent 55%), radial-gradient(120% 100% at 100% 100%, rgba(167,139,250,0.10) 0%, transparent 55%)",
        "pipeline-track":
          "linear-gradient(90deg, rgba(20,184,166,0.0) 0%, rgba(45,212,191,0.6) 30%, rgba(56,189,248,0.6) 70%, rgba(167,139,250,0.0) 100%)",
      },
      keyframes: {
        "soft-pulse": {
          "0%, 100%": { opacity: "0.4" },
          "50%":      { opacity: "1" },
        },
        "ambient-drift": {
          "0%":   { transform: "translate3d(0,0,0)" },
          "50%":  { transform: "translate3d(0,-12px,0)" },
          "100%": { transform: "translate3d(0,0,0)" },
        },
      },
      animation: {
        "soft-pulse":   "soft-pulse 2.4s ease-in-out infinite",
        "ambient-drift":"ambient-drift 12s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;

