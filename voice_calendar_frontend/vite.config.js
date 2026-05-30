import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true
      }
    }
  }
})
