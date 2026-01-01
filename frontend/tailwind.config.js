/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#e50914',
                dark: {
                    100: '#f5f5f5',
                    200: '#e5e5e5',
                    300: '#b3b3b3',
                    400: '#808080',
                    500: '#565656',
                    600: '#404040',
                    700: '#2a2a2a',
                    800: '#1a1a1a',
                    900: '#0a0a0a',
                }
            },
            borderRadius: {
                'card': '8px',
                'modal': '12px',
            },
            transitionDuration: {
                '300': '300ms',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-in',
                'slide-in': 'slideIn 0.3s ease-out',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideIn: {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
            },
        },
    },
    plugins: [],
}
