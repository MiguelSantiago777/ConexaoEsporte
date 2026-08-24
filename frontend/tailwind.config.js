/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#1e6f3c",   // verde esporte
          dark: "#154f2b",
          light: "#eaf5ee",
        },
      },
    },
  },
  plugins: [],
};
