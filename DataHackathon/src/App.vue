<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <header class="app-header">
      <RouterLink to="/" class="logo">
        <span class="logo-data">Data</span><span class="logo-hackathon">Hackathon</span>
      </RouterLink>
      <nav class="nav">
        <RouterLink to="/">الرئيسية</RouterLink>
        <RouterLink to="/survey" class="nav-highlight">🛡 الحارس الدلالي</RouterLink>
        <RouterLink to="/about">من نحن</RouterLink>
      </nav>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(8px);
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  text-decoration: none;
  letter-spacing: -0.02em;
}

.logo-data {
  color: var(--color-heading);
}

.logo-hackathon {
  color: #0e7490;
}

.logo:hover .logo-hackathon {
  text-decoration: underline;
}

.nav {
  display: flex;
  gap: 0.5rem;
}

.nav a {
  padding: 0.5rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  border-radius: 0.375rem;
  transition: background 0.2s, color 0.2s;
}

.nav a:hover {
  background: var(--color-background-soft);
  color: #0e7490;
}

.nav a.router-link-active {
  color: #0e7490;
  background: rgba(6, 182, 212, 0.1);
}

.nav-highlight {
  font-weight: 600;
  color: #0e7490 !important;
}

.app-main {
  flex: 1;
}

@media (prefers-color-scheme: dark) {
  .logo-hackathon {
    color: #22d3ee;
  }
  .nav a:hover,
  .nav a.router-link-active {
    color: #22d3ee;
  }
  .nav a.router-link-active {
    background: rgba(34, 211, 238, 0.12);
  }
}
</style>
