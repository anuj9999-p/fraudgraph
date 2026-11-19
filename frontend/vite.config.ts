import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({ plugins: [react(), tailwindcss()],
  test: { environment: 'jsdom', setupFiles: ['./src/setupTests.ts'] },
  server: { proxy: { '/api': process.env.VITE_API_PROXY ?? 'http://localhost:8000', '/health': process.env.VITE_API_PROXY ?? 'http://localhost:8000' } } })
