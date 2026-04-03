<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <h1 class="hero-title">عين</h1>
        <p class="hero-tagline">
          منصة للتحقق من جودة البيانات والاستبيانات: تحليل دلالي للحقول، معالجة ملفات جدولية،
          وربط بخادم API.
        </p>
        <div class="hero-actions">
          <RouterLink to="/survey" class="btn btn-primary">جرّب الاستبيان الآن</RouterLink>
          <RouterLink to="/analysis" class="btn btn-outline">تحليل ملف Excel / CSV</RouterLink>
        </div>
      </div>
    </section>

    <footer class="home-footer">
      <p>© {{ new Date().getFullYear() }} عين</p>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
}

.hero {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem 3rem;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(14, 165, 233, 0.15) 0%, transparent 55%),
    radial-gradient(ellipse 60% 40% at 80% 60%, rgba(6, 182, 212, 0.08) 0%, transparent 50%),
    var(--color-background);
}

.hero-content {
  position: relative;
  text-align: center;
  max-width: 42rem;
}

.hero-title {
  font-size: clamp(3rem, 12vw, 5rem);
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 1rem;
  letter-spacing: 0.02em;
  color: #0e7490;
}

.hero-tagline {
  max-width: 36rem;
  margin: 0 auto 2rem;
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--color-text);
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 0.5rem;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.btn-primary {
  background: #0e7490;
  color: #fff;
}

.btn-primary:hover {
  background: #0c6380;
  transform: translateY(-1px);
}

.btn-outline {
  color: #0e7490;
  border-color: #0e7490;
  background: transparent;
}

.btn-outline:hover {
  background: rgba(14, 116, 144, 0.08);
}

.home-footer {
  padding: 1.5rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text);
  opacity: 0.7;
  border-top: 1px solid var(--color-border);
}

@media (prefers-color-scheme: dark) {
  .hero-title {
    color: #22d3ee;
  }
  .btn-primary {
    background: #0891b2;
  }
  .btn-primary:hover {
    background: #0e7490;
  }
  .btn-outline {
    color: #22d3ee;
    border-color: #22d3ee;
  }
  .btn-outline:hover {
    background: rgba(34, 211, 238, 0.1);
  }
}
</style>
