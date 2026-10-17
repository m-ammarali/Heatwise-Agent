/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#0f1b3d", 2: "#475467", 3: "#7a869a" },
        brand: { DEFAULT: "#1d4ba0", dark: "#153a80", soft: "#eaf0fb" },
        accent: "#ef8a1f",
        line: { DEFAULT: "#e4e9f0", strong: "#cfd7e3" },
        soft: "#f5f7fb",
        navy: "#0f1d44",
      },
      fontFamily: {
        sans: ["'Inter Variable'", "Inter", "system-ui", "-apple-system", "'Segoe UI'", "sans-serif"],
        mono: ["ui-monospace", "'SF Mono'", "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,27,61,0.04), 0 8px 24px -12px rgba(15,27,61,0.10)",
      },
    },
  },
  plugins: [],
};
