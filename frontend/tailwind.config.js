/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Custom colors for legal document analysis
      colors: {
        // Primary brand colors
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        // Risk flag colors
        risk: {
          green: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
          },
          yellow: {
            50: '#fefce8',
            100: '#fef3c7',
            200: '#fde68a',
            300: '#fcd34d',
            400: '#fbbf24',
            500: '#f59e0b',
            600: '#d97706',
            700: '#b45309',
            800: '#92400e',
            900: '#78350f',
          },
          red: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
          },
        },
        // Neutral colors for UI
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
          950: '#030712',
        },
        // Ring colors for focus states
        ring: '#0284c7'
      },
      // Typography for legal documents
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          '"Noto Sans"',
          'sans-serif'
        ],
        mono: [
          'Fira Code',
          'ui-monospace',
          'SFMono-Regular',
          '"Menlo"',
          '"Monaco"',
          '"Cascadia Code"',
          '"Roboto Mono"',
          '"Oxygen Mono"',
          '"Ubuntu Monospace"',
          '"Source Code Pro"',
          'monospace'
        ],
      },
      // Custom spacing for legal document layouts
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      // Animation for smooth transitions
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounceSubtle 2s infinite',
        'highlight': 'highlight 0.8s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        highlight: {
          '0%, 100%': { backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgb(255, 247, 133)' }, // yellow-200
        },
      },
      // Custom shadows for depth
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 30px -5px rgba(0, 0, 0, 0.05)',
        'strong': '0 10px 40px -10px rgba(0, 0, 0, 0.15), 0 20px 50px -10px rgba(0, 0, 0, 0.1)',
      },
      // Border radius for modern UI
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      // Grid templates for layouts
      gridTemplateColumns: {
        'contract': '1fr 400px',
        'contract-lg': '1fr 500px',
        'analysis': '300px 1fr 400px',
      },
      // Max width for content
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
      // Z-index utilities
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    // Custom plugin for risk flag utilities
    function({ addUtilities }) {
      const newUtilities = {
        '.risk-flag-green': {
          backgroundColor: '#22c55e',
          color: 'white',
          borderRadius: '0.375rem',
          padding: '0.25rem 0.75rem',
          fontSize: '0.875rem',
          fontWeight: '500',
        },
        '.risk-flag-yellow': {
          backgroundColor: '#f59e0b',
          color: 'white',
          borderRadius: '0.375rem',
          padding: '0.25rem 0.75rem',
          fontSize: '0.875rem',
          fontWeight: '500',
        },
        '.risk-flag-red': {
          backgroundColor: '#ef4444',
          color: 'white',
          borderRadius: '0.375rem',
          padding: '0.25rem 0.75rem',
          fontSize: '0.875rem',
          fontWeight: '500',
        },
        '.clause-highlight': {
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderLeft: '3px solid rgb(59, 130, 246)',
          transition: 'all 0.2s ease-in-out',
        },
        '.clause-highlight-active': {
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          borderLeft: '4px solid rgb(59, 130, 246)',
          transform: 'translateX(2px)',
        }
      }
      addUtilities(newUtilities)
    }
  ],
  // Dark mode configuration
  darkMode: 'class',
}