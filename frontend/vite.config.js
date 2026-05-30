import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            if (err.code !== 'EPIPE') {
              console.error('Proxy error:', err)
            }
          })
        }
      },
      '/playit-api': {
        target: 'http://localhost:8010',
        changeOrigin: true
      },
      '/branding': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
