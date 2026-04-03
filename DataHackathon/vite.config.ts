import fs from 'node:fs'
import path from 'node:path'
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

/**
 * GitHub Pages لا يخدم مسارات SPA (/analysis إلخ). 404.html يعيد التوجيه إلى /REPO/#/…
 * مع VITE_GH_PAGES + createWebHashHistory في الراوتر.
 */
function ghPages404RedirectPlugin(publicBase: string): Plugin {
  return {
    name: 'gh-pages-404-redirect',
    closeBundle() {
      if (process.env.VITE_GH_PAGES !== 'true' || publicBase === '/') return
      const repo = publicBase.replace(/^\/+|\/+$/g, '')
      if (!repo) return
      const distDir = path.resolve(fileURLToPath(new URL('.', import.meta.url)), 'dist')
      const html = `<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>توجيه…</title><script>(function(){var r=${JSON.stringify(repo)};var p=location.pathname||"";var prefix="/"+r;if(p.indexOf(prefix)!==0){location.replace(location.origin+prefix+"/#/");return;}var rest=p.slice(prefix.length).replace(/^\\/+|\\/+$/g,"");location.replace(location.origin+prefix+"/#"+(rest?"/"+rest:"/")+location.search);})()<\/script></head><body style="font-family:system-ui,sans-serif;text-align:center;padding:2rem">جاري فتح الصفحة…</body></html>`
      fs.writeFileSync(path.join(distDir, '404.html'), html, 'utf8')
    },
  }
}

export default defineConfig({
  base,
  /** طلبات /api تُمرَّر إلى FastAPI محلياً — نفس المنشأ يتفادى CORS عند استخدام منافذ 5174/5175… */
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  plugins: [
    trailingSlashRedirectForBase(base),
    ghPages404RedirectPlugin(base),
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
