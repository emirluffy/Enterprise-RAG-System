/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce': 'bounce 1s infinite',
        'ping': 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
        '2xl': '40px',
        '3xl': '64px',
      },
      backgroundColor: {
        'white/5': 'rgba(255, 255, 255, 0.05)',
        'white/10': 'rgba(255, 255, 255, 0.1)',
        'white/20': 'rgba(255, 255, 255, 0.2)',
      },
      borderColor: {
        'white/10': 'rgba(255, 255, 255, 0.1)',
        'white/20': 'rgba(255, 255, 255, 0.2)',
      }
    },
  },
  plugins: [],
} 