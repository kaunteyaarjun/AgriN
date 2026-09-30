/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agri: {
          bg: '#080F0B',
          surface: '#111D16',
          elevated: '#17291F',
          border: '#1F382B',
          glow: '#34D399',
          primary: '#10B981',
          healthy: '#22C55E',
          watch: '#F59E0B',
          hazard: '#EF4444',
          unknown: '#6B7280',
          text: '#F3F4F6',
          muted: '#9CA3AF',
        }
      }
    },
  },
  plugins: [],
}
