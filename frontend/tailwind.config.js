/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#00417d",
          dark: "#00325f",
          light: "#e8f1f9",
        },
        accent: {
          DEFAULT: "#fcba27",
          dark: "#8a6008",
          light: "#fef6e2",
        },
      },
    },
  },
  plugins: [],
};
