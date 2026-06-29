/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces
        bg: "var(--bg)",
        "bg-elev": "var(--bg-elev)",
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
        // Accent (Tron electric blue)
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
        lg: "10px",
        xl: "11px",
        "2xl": "14px",
      },
      boxShadow: {
        card: "var(--shadow)",
        glow: "0 0 0 1px var(--accent), 0 0 22px -6px var(--glow)",
        "glow-sm": "0 0 0 1px var(--accent), 0 0 14px -5px var(--glow)",
        "glow-soft": "0 0 18px -6px var(--glow)",
        focus: "0 0 0 1px var(--accent), 0 0 16px -6px var(--glow)",
        "inset-accent": "inset 0 0 0 1px var(--accent-soft)",
      },
    },
  },
  plugins: [],
};
