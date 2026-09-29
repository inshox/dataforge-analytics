import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        forge: {
          bg: "var(--forge-bg)",
          surface: "var(--forge-surface)",
          card: "var(--forge-card)",
          border: "var(--forge-border)",
          accent: "var(--forge-accent)",
          muted: "var(--forge-muted)",
          text: "var(--forge-text)",
          hover: "var(--forge-hover)",
          "accent-soft": "var(--forge-accent-soft)",
          "primary-bg": "var(--forge-primary-bg)",
          "primary-fg": "var(--forge-primary-fg)",
          "success-bg": "var(--forge-success-bg)",
          "success-fg": "var(--forge-success-fg)",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
