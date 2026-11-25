import { defineConfig } from 'vite';
// base './' so the same build works at /popup-atlas/three/ on GitHub Pages and from a Capacitor www/ folder.
export default defineConfig({
  base: './',
  build: { target: 'safari15', assetsInlineLimit: 0, chunkSizeWarningLimit: 900 },
});
