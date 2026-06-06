import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        proxyTimeout: 600000,   // 10 minuta — za batch od 1000+ fajlova
        timeout:      600000,   // isto za socket timeout
      }
    }
  }
})
