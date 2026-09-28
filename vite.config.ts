import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [preact()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  // NO_HMR=1: pages never reload themselves when a file changes (long
  // headless tool runs survive edits; the next page load gets the new code).
  server: { port: 5173, host: true, hmr: process.env.NO_HMR ? false : undefined },
  build: { target: 'es2022', chunkSizeWarningLimit: 4000, assetsInlineLimit: 0 },
  test: { environment: 'node', include: ['tests/**/*.test.ts'] },
});
