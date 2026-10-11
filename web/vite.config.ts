import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `npm run api` serves the FastAPI app on :8000; the dev server forwards /api to it.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
