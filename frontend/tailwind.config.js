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
        // Verde de quadra — usado nos estados de presença/sucesso no lugar do
        // verde genérico do Tailwind, e como segundo acento do sistema.
        court: {
          DEFAULT: "#1c7a4b",
          dark: "#155c39",
          light: "#e7f5ed",
        },
        // Neutro quente para superfícies "de documento" (cabeçalhos de
        // relatório, recibos) — usado com moderação, nunca como fundo padrão.
        paper: "#f7f3ea",
        ink: "#10233a",
      },
      fontFamily: {
        // Serif de exibição — títulos, marca, telas de entrada. Uso restrito
        // a esses pontos; o corpo do sistema (formulários, tabelas) continua
        // em Inter por legibilidade em densidade alta.
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        // Números de indicadores, contadores e colunas numéricas de tabela —
        // reforça a sensação de registro/planilha oficial.
        mono: ["\"IBM Plex Mono\"", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
