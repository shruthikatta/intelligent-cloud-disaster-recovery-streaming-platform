/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx,css}"],
  theme: {
    extend: {
      colors: {
        /** Netflix-style streaming UI: near-black page, lifted cards, red accent */
        sv: {
          page: "#141414",
          card: "#181818",
          "card-hover": "#252525",
          line: "#2f2f2f",
          ink: "#ffffff",
          muted: "#b3b3b3",
          dim: "#757575",
          accent: "#e50914",
          "accent-hover": "#f40612",
        },
      },
      fontFamily: {
        display: ["Helvetica Neue", "Segoe UI", "system-ui", "sans-serif"],
        sans: ["Helvetica Neue", "Segoe UI", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 4px 24px rgba(0, 0, 0, 0.55)",
        "card-hover": "0 8px 32px rgba(0, 0, 0, 0.65)",
      },
    },
  },
  plugins: [],
};
