import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    host: true, // Listen on all local IPs
    allowedHosts: true, // Allow all hosts for tunneling
    proxy: {
      '/api': {
        target: 'http://localhost:5005',
        changeOrigin: true,
      },
    },
  },
})
