<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <span class="hero-badge">هاكاثون الابتكار في البيانات</span>
        <h1 class="hero-title">
          <span class="hero-title-main">Data</span><span class="hero-title-accent">Hackathon</span>
        </h1>
        <p class="hero-desc">
          منصة تجمع المبتكرين والمطورين لبناء حلول ذكية تعتمد على البيانات.
          انضم إلينا واصنع الفرق.
        </p>
        <div class="hero-actions">
          <RouterLink to="/about" class="btn btn-primary">اعرف المزيد</RouterLink>
          <a href="#features" class="btn btn-outline">المميزات</a>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="features">
      <h2 class="section-title">لماذا DataHackathon؟</h2>
      <div class="features-grid">
        <article class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>تحليل البيانات</h3>
          <p>أدوات وبيانات مفتوحة لتحويل الأفكار إلى رؤى قابلة للتطبيق.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🤝</div>
          <h3>فريق وشركاء</h3>
          <p>تعاون مع خبراء من قطاعات مختلفة وابنِ مشروعك خلال أيام.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🏆</div>
          <h3>جوائز ودعم</h3>
          <p>فرصة للفوز بدعم مادي وتقدير ودعم لتحويل المشروع إلى واقع.</p>
        </article>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta">
      <div class="cta-content">
        <h2>جاهز للمشاركة؟</h2>
        <p>سجّل الآن وكن جزءاً من مجتمع الابتكار في البيانات.</p>
        <RouterLink to="/about" class="btn btn-primary btn-lg">سجّل الآن</RouterLink>
      </div>
    </section>

    <footer class="home-footer">
      <p>© {{ new Date().getFullYear() }} DataHackathon — هاكاثون الابتكار في البيانات</p>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif;
}

/* Hero */
.hero {
  position: relative;
  min-height: 85vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
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

.hero-badge {
  display: inline-block;
  padding: 0.35rem 0.9rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
  border-radius: 9999px;
  margin-bottom: 1.25rem;
  letter-spacing: 0.02em;
}

.hero-title {
  font-size: clamp(2.5rem, 8vw, 4rem);
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 1rem;
  letter-spacing: -0.03em;
}

.hero-title-main {
  color: var(--color-heading);
}

.hero-title-accent {
  color: #0e7490;
}

.hero-desc {
  font-size: 1.125rem;
  color: var(--color-text);
  opacity: 0.9;
  line-height: 1.65;
  margin-bottom: 2rem;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Buttons */
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

.btn-lg {
  padding: 0.9rem 1.75rem;
  font-size: 1.05rem;
}

/* Features */
.features {
  padding: 4rem 1.5rem;
  max-width: 64rem;
  margin: 0 auto;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 2.5rem;
  color: var(--color-heading);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  padding: 1.75rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  border-color: rgba(14, 165, 233, 0.3);
  box-shadow: 0 8px 24px rgba(14, 165, 233, 0.08);
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-heading);
}

.feature-card p {
  font-size: 0.95rem;
  color: var(--color-text);
  opacity: 0.85;
  line-height: 1.55;
}

/* CTA */
.cta {
  padding: 4rem 1.5rem;
  background: linear-gradient(180deg, rgba(6, 182, 212, 0.06) 0%, transparent 100%);
}

.cta-content {
  max-width: 36rem;
  margin: 0 auto;
  text-align: center;
}

.cta h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--color-heading);
}

.cta p {
  margin-bottom: 1.5rem;
  color: var(--color-text);
  opacity: 0.9;
}

/* Footer */
.home-footer {
  padding: 1.5rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text);
  opacity: 0.7;
  border-top: 1px solid var(--color-border);
}

@media (prefers-color-scheme: dark) {
  .hero-title-accent {
    color: #22d3ee;
  }
  .hero-badge {
    color: #67e8f9;
    background: rgba(34, 211, 238, 0.15);
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
