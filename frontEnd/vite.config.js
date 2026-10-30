import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // "@/..." apunta a src/. Ej.: import { Boton } from '@/components/ui/Boton'
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // En desarrollo, las llamadas a /api se reenvían al backend (FastAPI en el puerto 8000).
    // Así el navegador no bloquea las peticiones por CORS.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  // Pruebas (npm test): simulan un navegador con jsdom.
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
  },
})
