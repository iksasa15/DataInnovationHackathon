<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { RouterLink } from 'vue-router'

const CompareCharts = defineAsyncComponent(() => import('../components/CompareCharts.vue'))
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
        <h2 id="details-heading" class="section-title section-title--in-details">
          تفاصيل تقنية ومقارنة سريعة
        </h2>
        <p class="details-intro">
          ملخص للّغات والمكتبات، ثم فرق عملي بين الاعتماد على مراجعة يدوية أو جداول فقط وبين استخدام المنصة.
        </p>

        <h3 class="details-subheading">اللغات والأدوات المستخدمة</h3>
        <div class="tech-blocks">
          <div class="tech-block">
            <h4 class="tech-block-title">الواجهة (متصفّح)</h4>
            <ul class="tech-tags" aria-label="تقنيات الواجهة">
              <li>TypeScript</li>
              <li>Vue 3</li>
              <li>Vue Router</li>
              <li>Pinia</li>
              <li>Vite</li>
              <li>SheetJS (<span class="tech-note">xlsx</span>)</li>
              <li>iconv-lite</li>
            </ul>
            <p class="tech-block-desc">
              بناء SPA مع فحص أنواع عند البناء (<code class="inline-code">vue-tsc</code>)، اختبارات اختيارية
              (Vitest / Playwright)، ونشر ثابت عبر GitHub Actions إلى مجلد <code class="inline-code">docs/</code>
              لصفحات GitHub مع دعم المسار الأساسي (<code class="inline-code">VITE_BASE_PATH</code>).
            </p>
          </div>
          <div class="tech-block">
            <h4 class="tech-block-title">الخادم والـ API</h4>
            <ul class="tech-tags" aria-label="تقنيات الخادم">
              <li>Python</li>
              <li>FastAPI</li>
              <li>Uvicorn</li>
              <li>Pydantic</li>
              <li>httpx</li>
              <li>Google Generative AI</li>
              <li>OpenAI SDK</li>
            </ul>
            <p class="tech-block-desc">
              نقاط للتحقق من النموذج، دفعات ديناميكية، وثائق Swagger تلقائية، وفحص صحة يشمل الاتصال بقاعدة البيانات
              وخدمة Gemini عند التفعيل. يمكن ربط الإعدادات بـ Supabase (<code class="inline-code">app_settings</code>)
              أو بمتغيرات البيئة على الاستضافة (مثل Render).
            </p>
          </div>
        </div>

        <p class="details-footnote">
          عنوان واجهة الـ API للواجهة الأمامية يُضبط عند البناء عبر
          <code class="inline-code">VITE_API_URL</code> دون تعديل الكود. صفحة
          <RouterLink to="/tests" class="inline-link">اختبارات</RouterLink>
          تعرض العنوان الفعلي وروابط <strong>Swagger</strong> و<strong>openapi.json</strong> والفحص الشامل.
        </p>

        <h3 class="details-subheading">قبل عين وبعدها</h3>
        <p class="compare-lead">
          ليست مقارنة منتجات خارجية، بل مسار عمل شائع مقابل ما توحّده المنصة في مكان واحد.
        </p>
        <p class="compare-disclaimer" role="note">
          <strong>تنبيه:</strong> النِّسَب والأرقام في الرسوم التالية
          <strong>تقديرية توضيحية</strong> لإظهار الفرق النسبي بين المسارين، وليست قياساً ميدانياً على بياناتك أو مشروعك.
        </p>

        <Suspense>
          <CompareCharts />
          <template #fallback>
            <p class="charts-fallback">جاري تحميل الرسوم…</p>
          </template>
        </Suspense>

        <div class="compare-stats" role="group" aria-label="ملخص تقديري بالأرقام">
          <div class="stat-card">
            <span class="stat-card-kicker">تقديري</span>
            <span class="stat-card-value" dir="ltr">~62٪</span>
            <span class="stat-card-label">انخفاض نسبي في جهد الوقت لمراجعة دفعة متوسطة*</span>
            <span class="stat-card-spark stat-card-spark--down" aria-hidden="true"></span>
          </div>
          <div class="stat-card stat-card--accent">
            <span class="stat-card-kicker">تقديري</span>
            <span class="stat-card-value" dir="ltr">~2.1×</span>
            <span class="stat-card-label">توسّع تقريبي في تغطية الالتقاط المبكر للتناقضات*</span>
            <span class="stat-card-spark stat-card-spark--up" aria-hidden="true"></span>
          </div>
        </div>
        <p class="compare-footnote">* مقارنة نسبية مبسّطة بين سيناريو يدوي/جداول فقط وسيناريو يستخدم المنصة.</p>

        <div class="compare-table-wrap" role="region" aria-label="مقارنة نصية قبل وبعد استخدام عين">
          <table class="compare-table">
            <thead>
              <tr>
                <th scope="col">بدون عين (تقليدي)</th>
                <th scope="col">مع عين</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>مراجعة يدوية لكل صف أو حقل في Excel، أو اعتماد على «عين بشرية» فقط.</td>
                <td>إرسال دفعة للخادم مع تقسيم حسب الحالة (صالح / تحذير / خطأ) وملخص لكل صف.</td>
              </tr>
              <tr>
                <td>قواعد ثابتة في الجدول (مثل التنسيق الشرطي) بلا سياق لغوي موحّد.</td>
                <td>تحقق عبر API مع نماذج Pydantic وطبقة تحليل (بما فيها Gemini عند توفر المفتاح).</td>
              </tr>
              <tr>
                <td>الاستبيان: حفظ ثم مراجعة لاحقة؛ صعوبة ملاحظة التناقضات أثناء الإدخال.</td>
                <td>الحارس الدلالي: تحقق أثناء التعديل مع اقتراحات دون إعادة تحميل الصفحة.</td>
              </tr>
              <tr>
                <td>تشخيص مشاكل الاتصال أو المفتاح يتطلب سجلات الخادم أو أدوات خارجية.</td>
                <td>صفحة اختبارات تجمع عنوان الـ API، الوثائق، الفحص الشامل، واختبار Gemini في واجهة واحدة.</td>
              </tr>
            </tbody>
          </table>
        </div>
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
  max-width: 52rem;
  margin: 0 auto;
}

.section-title--in-details {
  margin-bottom: 0.5rem;
}

.details-intro {
  margin: 0 0 1.75rem;
  text-align: center;
  max-width: 38rem;
  margin-left: auto;
  margin-right: auto;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--color-text);
  opacity: 0.88;
}

.details-subheading {
  margin: 2rem 0 0.85rem;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-heading);
  text-align: right;
}

.details-subheading:first-of-type {
  margin-top: 0;
}

.tech-blocks {
  display: grid;
  gap: 1.25rem;
}

@media (min-width: 768px) {
  .tech-blocks {
    grid-template-columns: 1fr 1fr;
  }
}

.tech-block {
  padding: 1.1rem 1.15rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.65rem;
}

.tech-block-title {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-heading);
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0 0 0.75rem;
  padding: 0;
  list-style: none;
}

.tech-tags li {
  padding: 0.2rem 0.55rem;
  font-size: 0.78rem;
  font-weight: 500;
  border-radius: 9999px;
  background: rgba(14, 165, 233, 0.1);
  color: #0e7490;
  border: 1px solid rgba(14, 165, 233, 0.25);
}

.tech-block-desc {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--color-text);
  opacity: 0.9;
}

.tech-note {
  font-family: ui-monospace, monospace;
  font-size: 0.9em;
}

.details-footnote {
  margin: 1.25rem 0 0;
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--color-text);
  opacity: 0.88;
}

.compare-lead {
  margin: 0 0 0.85rem;
  font-size: 0.9rem;
  color: var(--color-text);
  opacity: 0.85;
  line-height: 1.55;
}

.charts-fallback {
  margin: 0 0 1.25rem;
  padding: 1.5rem 1rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text);
  opacity: 0.75;
  border: 1px dashed var(--color-border);
  border-radius: 0.65rem;
}

.compare-disclaimer {
  margin: 0 0 1.25rem;
  padding: 0.65rem 0.85rem;
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--color-text);
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 0.5rem;
}

.compare-stats {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  margin: 0 0 0.65rem;
}

@media (min-width: 560px) {
  .compare-stats {
    grid-template-columns: 1fr 1fr;
  }
}

.stat-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1rem 1.1rem 2.35rem;
  border-radius: 0.65rem;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  overflow: hidden;
}

.stat-card--accent {
  border-color: rgba(14, 165, 233, 0.4);
  background: rgba(6, 182, 212, 0.07);
}

.stat-card-kicker {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #0e7490;
  opacity: 0.9;
}

.stat-card-value {
  font-size: 2rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  color: var(--color-heading);
}

.stat-card-label {
  font-size: 0.82rem;
  line-height: 1.45;
  color: var(--color-text);
  opacity: 0.88;
}

.stat-card-spark {
  position: absolute;
  left: 0.85rem;
  right: 0.85rem;
  bottom: 0.65rem;
  height: 5px;
  border-radius: 9999px;
  opacity: 0.85;
}

.stat-card-spark--down {
  background: linear-gradient(90deg, #f97316 0%, #fb923c 40%, #fed7aa 100%);
}

.stat-card-spark--up {
  background: linear-gradient(90deg, #0e7490 0%, #22d3ee 55%, #a5f3fc 100%);
}

.compare-footnote {
  margin: 0 0 1.5rem;
  font-size: 0.75rem;
  line-height: 1.45;
  color: var(--color-text);
  opacity: 0.72;
}

.compare-table-wrap {
  margin-top: 0.25rem;
  overflow-x: auto;
  border-radius: 0.65rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  line-height: 1.55;
  text-align: right;
}

.compare-table th,
.compare-table td {
  padding: 0.75rem 0.9rem;
  vertical-align: top;
  border-bottom: 1px solid var(--color-border);
}

.compare-table thead th {
  font-weight: 700;
  color: var(--color-heading);
  background: var(--color-background-soft);
  border-bottom-width: 2px;
}

.compare-table tbody tr:last-child td {
  border-bottom: none;
}

.compare-table td:first-child {
  width: 48%;
  color: var(--color-text);
  opacity: 0.88;
}

.compare-table td + td {
  border-inline-start: 1px solid var(--color-border);
}

.compare-table td:last-child {
  background: rgba(6, 182, 212, 0.04);
  color: var(--color-text);
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
  .tech-tags li {
    background: rgba(34, 211, 238, 0.12);
    color: #67e8f9;
    border-color: rgba(34, 211, 238, 0.3);
  }
  .compare-table td:last-child {
    background: rgba(34, 211, 238, 0.06);
  }
  .compare-disclaimer {
    background: rgba(251, 191, 36, 0.08);
    border-color: rgba(251, 191, 36, 0.28);
  }
  .stat-card-kicker {
    color: #67e8f9;
  }
}
</style>
