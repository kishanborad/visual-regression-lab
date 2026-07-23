import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'system-ui', 'sans-serif'],
      },
      colors: {
        vr: {
          bg: '#050816',
          deep: '#0a0a1a',
          surface: 'rgba(20, 20, 30, 0.7)',
          surfaceSolid: '#0d0d1a',
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.15)',
          text: '#f4f4f6',
          secondary: '#aaa6c3',
          muted: '#64648a',
          accent: '#818cf8',
          accentDim: '#6366f1',
          accentDark: '#4f46e5',
          pass: '#22c55e',
          fail: '#ef4444',
          diffDefault: '#ff00ff',
          glowAccent: 'rgba(99, 102, 241, 0.15)',
          glowPass: 'rgba(34, 197, 94, 0.2)',
          glowFail: 'rgba(239, 68, 68, 0.2)',
        },
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.3)',
        glow: '0 0 20px rgba(99, 102, 241, 0.15)',
        'glow-pass': '0 0 20px rgba(34, 197, 94, 0.2)',
        'glow-fail': '0 0 20px rgba(239, 68, 68, 0.2)',
        'glow-lg': '0 0 40px rgba(99, 102, 241, 0.2)',
      },
      backdropBlur: {
        glass: '12px',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(99, 102, 241, 0.1)' },
          '50%': { boxShadow: '0 0 30px rgba(99, 102, 241, 0.3)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
