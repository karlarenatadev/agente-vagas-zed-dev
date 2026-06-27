import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

// Reaproveita os plugins (react, tailwind) e o server do vite.config base,
// adicionando a configuracao de teste com ambiente jsdom e o setup do
// @testing-library/react.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      globals: false,
      setupFiles: './src/test/setup.ts',
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
    },
  }),
)
