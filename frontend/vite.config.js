import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// Dev: Vite serves from '/' on its own port and proxies /api to Django, so
// the browser only ever talks to one origin (no CORS/cookie complications).
// Build: assets are emitted under /static/app/ so Django's existing
// staticfiles app can serve them without any extra configuration.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/app/' : '/',
  plugins: [
    svelte(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'SikaTrack',
        short_name: 'SikaTrack',
        description: 'Track your Ghana Stock Exchange portfolio.',
        start_url: '/app/',
        scope: '/app/',
        display: 'standalone',
        background_color: '#f9fafb',
        theme_color: '#059669',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Never cache API responses opaquely — the app always wants fresh
        // portfolio data when online. The service worker exists to make the
        // app shell installable and load instantly, not to serve stale
        // financial figures.
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
  ],
  build: {
    outDir: '../static/app',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: false,
      },
    },
  },
}))
