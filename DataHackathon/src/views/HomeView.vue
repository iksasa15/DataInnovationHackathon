<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="home">
    <!-- Hero -->
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
          <a href="#features" class="btn btn-outline">المميزات</a>
        </div>
      </div>
    </section>

    <section id="features" class="features">
      <h2 class="section-title">مميزات عين</h2>
      <p class="section-lead">
        أدوات متكاملة للتحقق من الاتساق والمعنى قبل الاعتماد على البيانات في التقارير أو القرارات.
      </p>
      <div class="features-grid">
        <article class="feature-card">
          <div class="feature-icon" aria-hidden="true">🛡</div>
          <h3>الحارس الدلالي للاستبيان</h3>
          <p>
            استمارة جاهزة مع حقول ديموغرافية ومهنية؛ يُرسل كل تغيير للخادم فيتحقق من المنطق
            والصياغة ويُرجع ملخصاً واقتراحات دون إعادة تحميل الصفحة.
          </p>
          <RouterLink to="/survey" class="feature-link">فتح الاستبيان ←</RouterLink>
        </article>
        <article class="feature-card">
          <div class="feature-icon" aria-hidden="true">📂</div>
          <h3>تحليل الملفات الجدولية</h3>
          <p>
            اسحب ملف Excel أو CSV؛ يُعرض الجدول مع أعمدة ديناميكية، ثم تُرسل الدفعة للتحقق الديناميكي
            مع إحصاءات (صالح / تحذير / خطأ) وتصفية وعرض تفصيلي لكل صف.
          </p>
          <RouterLink to="/analysis" class="feature-link">رفع ملف ←</RouterLink>
        </article>
      </div>
    </section>

    <section class="details" aria-labelledby="details-heading">
      <div class="details-inner">
        <h2 id="details-heading" class="section-title">تفاصيل تقنية سريعة</h2>
        <ul class="details-list">
          <li>
            <strong>واجهة أمامية:</strong> Vue 3 مع توجيه للصفحات؛ مناسبة للنشر على GitHub Pages
            (مسار أساسي قابل للضبط).
          </li>
          <li>
            <strong>خادم الخلفية:</strong> FastAPI؛ نقاط للتحقق من النموذج، الدفعات الديناميكية،
            وفحص الصحة بما في ذلك إعدادات Gemini وSupabase عند الاستخدام.
          </li>
          <li>
            <strong>عنوان الـ API:</strong> يُحدَّد عبر متغير البيئة عند البناء (<code class="inline-code">VITE_API_URL</code>)
            ليتوافق مع الاستضافة (مثلاً Render) دون تعديل الكود. صفحة
            <RouterLink to="/tests" class="inline-link">اختبارات</RouterLink>
            تعرض العنوان الحالي وروابط الوثائق والفحوص.
          </li>
        </ul>
      </div>
    </section>

    <section class="cta">
      <div class="cta-content">
        <h2>ابدأ من أي مسار يناسبك</h2>
        <p>
          جرّب استمارة واحدة للتحقق السريع، أو حمّل جدولاً كاملاً إذا كنت تعمل على بيانات مجمّعة.
        </p>
        <div class="cta-actions">
          <RouterLink to="/survey" class="btn btn-primary btn-lg">الاستبيان</RouterLink>
          <RouterLink to="/analysis" class="btn btn-outline btn-lg">تحليل الملف</RouterLink>
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
  padding: 3.5rem 1.5rem 4rem;
  max-width: 80rem;
  margin: 0 auto;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  text-align: center;
  margin: 0 0 0.75rem;
  color: var(--color-heading);
}

.section-lead {
  max-width: 40rem;
  margin: 0 auto 2.25rem;
  text-align: center;
  font-size: 1rem;
  line-height: 1.65;
  color: var(--color-text);
  opacity: 0.88;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  display: flex;
  flex-direction: column;
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
  margin: 0 0 0.5rem;
  color: var(--color-heading);
}

.feature-card p {
  flex: 1;
  margin: 0 0 1rem;
  font-size: 0.95rem;
  color: var(--color-text);
  opacity: 0.88;
  line-height: 1.6;
}

.feature-link {
  align-self: flex-start;
  font-size: 0.9rem;
  font-weight: 600;
  color: #0e7490;
  text-decoration: none;
}

.feature-link:hover {
  text-decoration: underline;
}

/* Details */
.details {
  padding: 0 1.5rem 4rem;
  background: linear-gradient(180deg, transparent 0%, rgba(6, 182, 212, 0.04) 40%, transparent 100%);
}

.details-inner {
  max-width: 44rem;
  margin: 0 auto;
}

.details-list {
  margin: 0;
  padding: 0 1.25rem 0 0;
  list-style: disc;
  color: var(--color-text);
  line-height: 1.75;
  font-size: 0.95rem;
}

.details-list li {
  margin-bottom: 0.85rem;
}

.details-list strong {
  color: var(--color-heading);
}

.inline-code {
  padding: 0.12rem 0.35rem;
  font-size: 0.85em;
  border-radius: 0.3rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  font-family: ui-monospace, monospace;
  direction: ltr;
  display: inline-block;
}

.inline-link {
  font-weight: 600;
  color: #0e7490;
  text-decoration: none;
}

.inline-link:hover {
  text-decoration: underline;
}

/* CTA */
.cta {
  padding: 3.5rem 1.5rem 4rem;
  border-top: 1px solid var(--color-border);
}

.cta-content {
  max-width: 36rem;
  margin: 0 auto;
  text-align: center;
}

.cta h2 {
  font-size: 1.45rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  color: var(--color-heading);
}

.cta p {
  margin: 0 0 1.5rem;
  color: var(--color-text);
  opacity: 0.9;
  line-height: 1.6;
}

.cta-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
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
  .feature-link {
    color: #22d3ee;
  }
  .inline-link {
    color: #22d3ee;
  }
}
</style>
