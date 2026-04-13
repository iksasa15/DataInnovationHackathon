<script setup lang="ts">
/**
 * أيقونات خطية بسيطة بألوان الهوية (currentColor) — بديل عن الإيموجي في الصفحة الرئيسية.
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
