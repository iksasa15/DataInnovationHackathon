<script setup lang="ts">
/**
 * أيقونات خطية (currentColor) — بديل عن الإيموجي في الواجهة.
 */
export type HomeIconName =
  | 'shield'
  | 'trending-up'
  | 'check-circle'
  | 'clipboard-list'
  | 'sparkles'
  | 'table'
  | 'plug'
  | 'clipboard-check'
  | 'search'
  | 'zap'
  | 'target'
  | 'layout'
  | 'settings'
  | 'upload'
  | 'cpu'
  | 'file-text'
  | 'circle-check'
  | 'bar-chart'
  | 'folder'
  | 'lock'
  | 'download'
  | 'save'
  | 'refresh-cw'
  | 'lightbulb'
  | 'bot'
  | 'x'
  | 'alert-triangle'
  | 'dice'
  | 'link'
  | 'menu'
  | 'line-chart'

withDefaults(
  defineProps<{
    name: HomeIconName
    /** حجم مربع الـ viewBox بالبكسل */
    size?: number
    strokeWidth?: number
  }>(),
  { size: 24, strokeWidth: 2 },
)
</script>

<template>
  <span class="home-page-icon" aria-hidden="true">
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- shield -->
      <g v-if="name === 'shield'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </g>
      <!-- trending-up -->
      <g v-else-if="name === 'trending-up'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
      </g>
      <!-- check-circle -->
      <g v-else-if="name === 'check-circle'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </g>
      <!-- clipboard-list -->
      <g v-else-if="name === 'clipboard-list'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <line x1="12" y1="11" x2="12" y2="11.01" />
        <line x1="12" y1="16" x2="12" y2="16.01" />
        <line x1="12" y1="6" x2="12" y2="6.01" />
        <line x1="16" y1="11" x2="8" y2="11" />
        <line x1="16" y1="16" x2="8" y2="16" />
      </g>
      <!-- sparkles -->
      <g v-else-if="name === 'sparkles'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
        <path d="M20 3v4M22 5h-4M4 17v2M5 18H3" />
      </g>
      <!-- table -->
      <g v-else-if="name === 'table'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <line x1="3" y1="9" x2="21" y2="9" />
        <line x1="3" y1="15" x2="21" y2="15" />
        <line x1="12" y1="3" x2="12" y2="21" />
      </g>
      <!-- plug -->
      <g v-else-if="name === 'plug'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22v-5" />
        <path d="M9 8V2" />
        <path d="M15 8V2" />
        <path d="M18 8v5a6 6 0 0 1-12 0V8" />
        <rect x="6" y="8" width="12" height="5" rx="1" />
      </g>
      <!-- clipboard-check -->
      <g v-else-if="name === 'clipboard-check'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <path d="m9 14 2 2 4-4" />
      </g>
      <!-- search -->
      <g v-else-if="name === 'search'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </g>
      <!-- zap -->
      <g v-else-if="name === 'zap'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </g>
      <!-- target -->
      <g v-else-if="name === 'target'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="6" />
        <circle cx="12" cy="12" r="2" />
      </g>
      <!-- layout -->
      <g v-else-if="name === 'layout'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <line x1="3" y1="9" x2="21" y2="9" />
        <line x1="9" y1="21" x2="9" y2="9" />
      </g>
      <!-- settings -->
      <g v-else-if="name === 'settings'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
      </g>
      <!-- upload -->
      <g v-else-if="name === 'upload'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </g>
      <!-- cpu -->
      <g v-else-if="name === 'cpu'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
        <rect x="9" y="9" width="6" height="6" />
        <line x1="9" y1="1" x2="9" y2="4" />
        <line x1="15" y1="1" x2="15" y2="4" />
        <line x1="9" y1="20" x2="9" y2="23" />
        <line x1="15" y1="20" x2="15" y2="23" />
        <line x1="20" y1="9" x2="23" y2="9" />
        <line x1="20" y1="14" x2="23" y2="14" />
        <line x1="1" y1="9" x2="4" y2="9" />
        <line x1="1" y1="14" x2="4" y2="14" />
      </g>
      <!-- file-text -->
      <g v-else-if="name === 'file-text'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <line x1="10" y1="9" x2="8" y2="9" />
      </g>
      <!-- circle-check -->
      <g v-else-if="name === 'circle-check'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="m9 12 2 2 4-4" />
      </g>
      <!-- bar-chart -->
      <g v-else-if="name === 'bar-chart'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </g>
      <!-- folder -->
      <g v-else-if="name === 'folder'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </g>
      <!-- lock -->
      <g v-else-if="name === 'lock'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </g>
      <!-- download -->
      <g v-else-if="name === 'download'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </g>
      <!-- save (floppy) -->
      <g v-else-if="name === 'save'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
        <polyline points="17 21 17 13 7 13 7 21" />
        <polyline points="7 3 7 8 15 8" />
      </g>
      <!-- refresh-cw -->
      <g v-else-if="name === 'refresh-cw'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M23 4v6h-6" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
      </g>
      <!-- lightbulb -->
      <g v-else-if="name === 'lightbulb'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 18h6M10 22h4M12 3v1m0 0a6 6 0 0 1 6 6c0 1.5-.5 2.8-1.4 3.9-.5.6-.6 1.4-.6 2.1H8c0-.7-.1-1.5-.6-2.1A6 6 0 0 1 12 4z" />
      </g>
      <!-- bot -->
      <g v-else-if="name === 'bot'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="5" y="8" width="14" height="12" rx="2" />
        <path d="M9 8V6a3 3 0 0 1 6 0v2" />
        <line x1="9" y1="14" x2="9.01" y2="14" />
        <line x1="15" y1="14" x2="15.01" y2="14" />
        <path d="M9 18h6" />
      </g>
      <!-- x -->
      <g v-else-if="name === 'x'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </g>
      <!-- alert-triangle -->
      <g v-else-if="name === 'alert-triangle'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </g>
      <!-- dice -->
      <g v-else-if="name === 'dice'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.25" fill="currentColor" />
        <circle cx="15.5" cy="15.5" r="1.25" fill="currentColor" />
        <circle cx="15.5" cy="8.5" r="1.25" fill="currentColor" />
        <circle cx="8.5" cy="15.5" r="1.25" fill="currentColor" />
      </g>
      <!-- link -->
      <g v-else-if="name === 'link'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 13a5 5 0 0 1 0-7l1-1a5 5 0 0 1 7 7l-1 1" />
        <path d="M14 11a5 5 0 0 1 0 7l-1 1a5 5 0 0 1-7-7l1-1" />
      </g>
      <!-- menu -->
      <g v-else-if="name === 'menu'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="6" x2="21" y2="6" />
        <line x1="3" y1="12" x2="21" y2="12" />
        <line x1="3" y1="18" x2="21" y2="18" />
      </g>
      <!-- line-chart (مسار/ملخص) -->
      <g v-else-if="name === 'line-chart'" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </g>
    </svg>
  </span>
</template>

<style scoped>
.home-page-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  line-height: 0;
}
.home-page-icon svg {
  display: block;
}
</style>
