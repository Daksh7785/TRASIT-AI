/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          dark: '#0B1026',
          card: 'rgba(15, 22, 55, 0.7)',
          accent: '#00FF88',
          nebula: '#8B5CF6',
          cyan: '#06B6D4',
          gold: '#FFD700',
        }
      },
      backgroundImage: {
        'cosmic-gradient': 'linear-gradient(135deg, #0B1026 0%, #151D45 50%, #0B1026 100%)',
      }
    },
  },
  plugins: [],
}
