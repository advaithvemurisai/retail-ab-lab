import { defineConfig } from 'vitest/config'

// Separate from vite.config.ts: the tests are pure TypeScript, so they need no React plugin.
export default defineConfig({ test: { environment: 'node', include: ['src/**/*.test.ts'] } })
