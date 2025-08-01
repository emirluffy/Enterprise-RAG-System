import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: 'localhost',
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/ws': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        ws: true
      }
    }
  }
})
