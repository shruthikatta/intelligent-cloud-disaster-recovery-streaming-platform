/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        obsidian: { 950: "#020617", 900: "#0b1224", 800: "#111827" },
        neon: { cyan: "#22d3ee", rose: "#fb7185" },
      },
    },
  },
  plugins: [],
};
