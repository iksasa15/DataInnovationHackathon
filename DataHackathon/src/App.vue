<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { LOGO_AIN_SRC as logoSrc } from './constants/branding'
import HomePageIcon from './components/HomePageIcon.vue'

const route = useRoute()
const sidebarOpen = ref(false)

watch(
  () => route.path,
  () => {
    sidebarOpen.value = false
  },
)

const hideChrome = computed(() => route.meta.presentation === true)

const pageTitle = computed(() => {
  const n = route.name
  if (n === 'home') return 'لوحة عين'
  if (n === 'survey') return 'الحارس الدلالي — الاستبيان'
  if (n === 'analysis') return 'تحليل الملف الجدولي'
  if (n === 'privacy') return 'سياسة الخصوصية'
  if (n === 'pitch' || n === 'pitch-present') return 'عن عين'
  return 'عين'
})

const navItems: { to: string; name: string; label: string }[] = [
  { to: '/', name: 'home', label: 'الرئيسية' },
  { to: '/pitch/present', name: 'pitch-present', label: 'عن عين' },
  { to: '/survey', name: 'survey', label: 'الحارس الدلالي' },
  { to: '/analysis', name: 'analysis', label: 'تحليل الملف' },
  { to: '/privacy', name: 'privacy', label: 'الخصوصية' },
]
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--present': hideChrome }">
    <div
      v-if="!hideChrome"
      class="sidebar-backdrop"
      :class="{ 'sidebar-backdrop--on': sidebarOpen }"
      aria-hidden="true"
      @click="sidebarOpen = false"
    />

    <aside
      v-if="!hideChrome"
      class="sidebar"
      :class="{ 'sidebar--open': sidebarOpen }"
      aria-label="القائمة الرئيسية"
    >
      <div class="sidebar-brand">
        <div class="sidebar-logo">
          <img :src="logoSrc" alt="عين" class="sidebar-logo-img" width="40" height="40" decoding="async" />
        </div>
        <div class="sidebar-brand-text">
          <span class="sidebar-title">عين</span>
          <span class="sidebar-tagline">التحقق من جودة البيانات</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{
            'sidebar-link--active':
              route.name === item.name ||
              (item.name === 'pitch-present' && route.name === 'pitch'),
          }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <div class="main-column">
      <header v-if="!hideChrome" class="topbar">
        <button
          type="button"
          class="menu-toggle"
          aria-label="فتح القائمة"
          @click="sidebarOpen = true"
        >
          <span class="menu-toggle-icon" aria-hidden="true">
            <HomePageIcon name="menu" :size="22" />
          </span>
        </button>
        <div class="topbar-brand">
          <div class="topbar-logo-chip" aria-hidden="true">
            <img :src="logoSrc" alt="" class="topbar-logo-img" width="36" height="36" decoding="async" />
          </div>
          <h1 class="topbar-title">{{ pageTitle }}</h1>
        </div>
      </header>

      <main class="app-main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: row;
  font-family: var(--font-app);
  background: var(--ga-surface);
}

.main-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--ga-sidebar-top) 0%, var(--ga-sidebar-mid) 48%, var(--ga-sidebar-bottom) 100%);
  color: #f1f5f9;
  padding: 1.35rem 0 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: -4px 0 24px rgba(15, 23, 42, 0.12);
  z-index: 60;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1.15rem;
}

.sidebar-logo {
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.65rem;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  overflow: hidden;
  padding: 0.2rem;
  box-sizing: border-box;
}

.sidebar-logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.sidebar-brand-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.sidebar-title {
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.sidebar-tagline {
  font-size: 0.72rem;
  opacity: 0.78;
  line-height: 1.3;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0 0.65rem;
}

.sidebar-link {
  display: block;
  padding: 0.65rem 0.85rem;
  border-radius: 0.55rem;
  color: rgba(241, 245, 249, 0.88);
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 600;
  transition: background 0.15s, color 0.15s;
}

.sidebar-link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.sidebar-link--active {
  background: linear-gradient(90deg, rgba(0, 178, 223, 0.28), rgba(65, 55, 168, 0.2));
  color: #fff;
  border-right: 3px solid var(--ga-cyan);
}

.menu-toggle-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.25rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
  flex: 1;
  direction: rtl;
}

.topbar-logo-chip {
  flex-shrink: 0;
  width: 2.35rem;
  height: 2.35rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  padding: 0.2rem;
  box-sizing: border-box;
}

.topbar-logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.topbar-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.25;
}

.menu-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  font-size: 1.25rem;
  cursor: pointer;
  color: #334155;
}

.sidebar-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .menu-toggle {
    display: flex;
  }

  .sidebar {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    transform: translateX(100%);
    transition: transform 0.25s ease;
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    z-index: 55;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
  }

  .sidebar-backdrop--on {
    opacity: 1;
    pointer-events: auto;
  }
}

.app-main {
  flex: 1;
  min-height: 0;
}

.app-shell--present .main-column {
  min-height: 100vh;
}

.app-shell--present .app-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
</style>

<style>
@media print {
  .app-shell .sidebar,
  .app-shell .topbar,
  .app-shell .sidebar-backdrop {
    display: none !important;
  }

  .app-shell .main-column {
    width: 100% !important;
    max-width: 100% !important;
  }

  .app-shell .menu-toggle {
    display: none !important;
  }
}
</style>
