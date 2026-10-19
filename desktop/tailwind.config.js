/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces
        bg: "var(--bg)",
        "bg-elev": "var(--bg-elev)",
        side: "var(--side)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        "surface-3": "var(--surface-3)",
        // Lines / borders
        line: "var(--line)",
        hair: "var(--border)",
        "hair-strong": "var(--border-strong)",
        // Text
        ink: "var(--text)",
        "ink-2": "var(--text-2)",
        "ink-3": "var(--text-3)",
        "ink-inv": "var(--text-inv)",
        // Accent
        accent: "var(--accent)",
        "accent-2": "var(--accent-2)",
        "accent-press": "var(--accent-press)",
        "accent-soft": "var(--accent-soft)",
        // Status
        success: "var(--success)",
        "success-soft": "var(--success-soft)",
        warning: "var(--warning)",
        "warning-soft": "var(--warning-soft)",
        manual: "var(--manual)",
        "manual-soft": "var(--manual-soft)",
        neutral: "var(--neutral)",
        "neutral-soft": "var(--neutral-soft)",
        danger: "var(--danger)",
        "danger-soft": "var(--danger-soft)",
      },
      fontFamily: {
        sans: [
          "Geist Variable",
          "Geist",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          "Geist Mono Variable",
          "Geist Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      borderRadius: {
        lg: "8px",
        xl: "9px",
        "2xl": "14px",
      },
      // The old neon "glow" names are kept so existing classes still work,
      // but they now render as quiet depth instead of a glowing outline.
      boxShadow: {
        card: "var(--shadow)",
        raise: "var(--raise)",
        glow: "inset 0 1px 0 rgba(255,255,255,0.18), 0 1px 2px rgba(0,0,0,0.15), 0 6px 16px -8px var(--glow)",
        "glow-sm": "var(--raise)",
        "glow-soft": "var(--shadow)",
        focus: "0 0 0 1.5px var(--accent), 0 0 0 4px var(--accent-soft)",
        "inset-accent": "none",
      },
    },
  },
  plugins: [],
};
