/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0a0a0f',
          surface: '#151520',
          border: '#2a2a3a',
          hover: '#1f1f2e',
        },
        accent: {
          primary: '#6366f1',
          secondary: '#8b5cf6',
          glow: '#818cf8',
        },
      },
    },
  },
  plugins: [],
}

