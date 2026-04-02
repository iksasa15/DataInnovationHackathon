import { fileURLToPath, URL } from 'node:url'

import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

// https://vite.dev/config/
// لـ GitHub Pages (مشروع تحت مسار فرعي): عيّن عند البناء VITE_BASE_PATH=/اسم-المستودع/
const base =
  process.env.VITE_BASE_PATH?.replace(/\/?$/, '/') ||
  '/'

/** يوجّه .../Repo إلى .../Repo/ حتى تُحمَّل الأصول والراوتر على GitHub Pages */
function trailingSlashRedirectForBase(publicBase: string): Plugin {
  return {
    name: 'trailing-slash-for-base',
    transformIndexHtml(html) {
      if (publicBase === '/') return html
      const withSlash = publicBase.endsWith('/') ? publicBase : `${publicBase}/`
      const noTrailing = withSlash.slice(0, -1)
      const script = `<script>(function(){var p=location.pathname;if(p===${JSON.stringify(noTrailing)})location.replace(${JSON.stringify(withSlash)}+location.search+location.hash)})()<\/script>`
      return html.replace('<head>', `<head>${script}`)
    },
  }
}

export default defineConfig({
  base,
  plugins: [
    trailingSlashRedirectForBase(base),
    nodePolyfills({
      globals: {
        Buffer: true,
        global: true,
      },
    }),
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
