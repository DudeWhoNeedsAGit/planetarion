/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'space-dark': '#0a0a0a',
        'space-blue': '#1e3a8a',
        'metal': '#64748b',
        'crystal': '#06b6d4',
        'deuterium': '#8b5cf6',
      },
    },
  },
  plugins: [],
}
