<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { checkSupabaseStatus } from '../services/api'
import type { SupabaseStatusResult } from '../services/api'

const supabaseLoading = ref(false)
const supabaseResult = ref<SupabaseStatusResult | null>(null)
const supabaseError = ref<string | null>(null)

async function testSupabase() {
  supabaseLoading.value = true
  supabaseError.value = null
  supabaseResult.value = null
  try {
    supabaseResult.value = await checkSupabaseStatus()
  } catch {
    supabaseError.value = 'تعذّر الاتصال بالخادم. تأكد أن الـ backend يعمل على المنفذ 8000.'
  } finally {
    supabaseLoading.value = false
  }
}
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
          <RouterLink to="/survey" class="btn btn-primary">جرّب الاستبيان الآن</RouterLink>
          <a href="#features" class="btn btn-outline">المميزات</a>
          <button
            type="button"
            class="btn btn-supabase"
            :disabled="supabaseLoading"
            @click="testSupabase"
          >
            {{ supabaseLoading ? 'جاري الاختبار…' : '🔗 اختبار اتصال Supabase' }}
          </button>
        </div>
        <div
          v-if="supabaseResult || supabaseError"
          class="supabase-status-box"
          :class="supabaseError || (supabaseResult && !supabaseResult.ok) ? 'supabase-bad' : 'supabase-ok'"
          role="status"
        >
          <template v-if="supabaseError">{{ supabaseError }}</template>
          <template v-else-if="supabaseResult">
            {{ supabaseResult.message }}
            <span v-if="supabaseResult.configured" class="supabase-meta">
              جدول: {{ supabaseResult.table_ok ? 'موجود' : '—' }} · مفتاح Gemini في DB:
              {{ supabaseResult.gemini_row_filled ? 'موجود' : 'فارغ' }}
            </span>
          </template>
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

.btn-supabase {
  color: #fff;
  background: linear-gradient(135deg, #3ecf8e 0%, #1e8a5a 100%);
  border: none;
}

.btn-supabase:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.btn-supabase:disabled {
  opacity: 0.75;
  cursor: wait;
}

.supabase-status-box {
  margin-top: 1.25rem;
  padding: 0.85rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  line-height: 1.5;
  text-align: center;
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
}

.supabase-ok {
  background: rgba(62, 207, 142, 0.12);
  border: 1px solid rgba(62, 207, 142, 0.45);
  color: #0f5132;
}

.supabase-bad {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #991b1b;
}

.supabase-meta {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  opacity: 0.9;
}

.btn-lg {
  padding: 0.9rem 1.75rem;
  font-size: 1.05rem;
}

/* Features */
.features {
  padding: 4rem 1.5rem;
  max-width: 80rem;
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
  .btn-supabase {
    background: linear-gradient(135deg, #2dd4bf 0%, #0d9488 100%);
  }
  .supabase-ok {
    background: rgba(45, 212, 191, 0.12);
    border-color: rgba(45, 212, 191, 0.4);
    color: #6ee7b7;
  }
  .supabase-bad {
    background: rgba(248, 113, 113, 0.12);
    border-color: rgba(248, 113, 113, 0.35);
    color: #fca5a5;
  }
}
</style>
