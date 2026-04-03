<script setup lang="ts">
import { RouterLink } from 'vue-router'

const services = [
  { icon: '🧠', title: 'التحليل الدلالي للحقول', desc: 'اكتشاف التناقضات المعنوية والمنطقية بين الحقول.' },
  { icon: '📊', title: 'معالجة البيانات الجدولية', desc: 'رفع Excel أو CSV وتحليل الصفوف مع تقارير واضحة.' },
  { icon: '🔌', title: 'التكامل عبر API', desc: 'ربط الواجهة بخادم FastAPI لتبادل البيانات بكفاءة.' },
  { icon: '✅', title: 'فحص جودة الاستبيانات', desc: 'تحقق من اتساق الإجابات مع سياق الاستبيان.' },
  { icon: '🔍', title: 'كشف الأخطاء والتكرار', desc: 'تنبيهات ودرجات ثقة واقتراحات تصحيحية.' },
]

const steps = [
  { n: 1, title: 'رفع البيانات / الاستبيان', desc: 'استمارة حية أو ملف جدولي حسب احتياجك.' },
  { n: 2, title: 'التحليل الآلي', desc: 'قواعد أعمال و/أو نموذج لغوي حسب الإعدادات.' },
  { n: 3, title: 'عرض النتائج والتوصيات', desc: 'ملخص، تفاصيل لكل صف، وتصفية حسب الشدة.' },
]

const highlights = [
  { icon: '⚡', title: 'سرعة المعالجة', desc: 'معالجة دقيقة وتغذية راجعة سريعة في الاستمارة.' },
  { icon: '🎯', title: 'دقة التحليل', desc: 'دمج قواعد LFS مع تحليل دلالي عند التفعيل.' },
  { icon: '👆', title: 'سهولة الاستخدام', desc: 'واجهة عربية ومسارات واضحة للاستبيان والملفات.' },
  { icon: '⚙️', title: 'أتمتة كاملة', desc: 'تقليل المراجعة اليدوية المتكررة للبيانات المتشابهة.' },
]
</script>

<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg" />
      <div class="hero-inner">
        <p class="hero-brand">عين</p>
        <h1 class="hero-title">منصة ذكية للتحقق من جودة البيانات والاستبيانات.</h1>
        <p class="hero-desc">
          منصة متكاملة لضمان جودة البيانات والاستبيانات، تعتمد على التحليل الدلالي للحقول، وتدعم معالجة
          البيانات الجدولية، إضافة إلى التكامل مع خادم API لتمكين الربط وتبادل المعلومات بكفاءة.
        </p>
        <p class="hero-cta-label">ابدأ الآن</p>
        <div class="hero-cards">
          <RouterLink to="/survey" class="hero-card hero-card--primary">
            <span class="hero-card-icon" aria-hidden="true">🛡</span>
            <span class="hero-card-title">جرّب الاستبيان</span>
            <span class="hero-card-text">استمارة LFS مع التحقق اللحظي والحارس الدلالي.</span>
            <span class="hero-card-arrow">←</span>
          </RouterLink>
          <RouterLink to="/analysis" class="hero-card hero-card--secondary">
            <span class="hero-card-icon" aria-hidden="true">📂</span>
            <span class="hero-card-title">تحليل الملف</span>
            <span class="hero-card-text">Excel أو CSV مع تحليل بالقواعد أو Gemini أو الاثنين.</span>
            <span class="hero-card-arrow">←</span>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- خدمات -->
    <section class="section section--muted" aria-labelledby="services-heading">
      <div class="section-inner">
        <h2 id="services-heading" class="section-title">خدمات المنصة</h2>
        <p class="section-sub">أدوات رئيسية لجودة البيانات في مسار واحد.</p>
        <div class="services-grid">
          <article v-for="(s, i) in services" :key="i" class="service-card">
            <span class="service-icon" aria-hidden="true">{{ s.icon }}</span>
            <h3 class="service-title">{{ s.title }}</h3>
            <p class="service-desc">{{ s.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- كيف تعمل -->
    <section class="section" aria-labelledby="how-heading">
      <div class="section-inner">
        <h2 id="how-heading" class="section-title">كيف تعمل المنصة؟</h2>
        <p class="section-sub section-sub--en" dir="ltr">How it works</p>

        <ol class="steps-list">
          <li v-for="st in steps" :key="st.n" class="step-item">
            <span class="step-num">{{ st.n }}</span>
            <div class="step-body">
              <h3 class="step-title">{{ st.title }}</h3>
              <p class="step-desc">{{ st.desc }}</p>
            </div>
          </li>
        </ol>

        <!-- إنفوجرافيك بسيط -->
        <div class="how-infographic" aria-hidden="true">
          <div class="how-flow">
            <div class="how-node">
              <span class="how-node-icon">📤</span>
              <span class="how-node-label">رفع</span>
            </div>
            <div class="how-connector" />
            <div class="how-node how-node--mid">
              <span class="how-node-icon">🤖</span>
              <span class="how-node-label">تحليل</span>
            </div>
            <div class="how-connector" />
            <div class="how-node">
              <span class="how-node-icon">📋</span>
              <span class="how-node-label">نتائج</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ماذا يميز المنصة -->
    <section class="section section--muted" aria-labelledby="highlights-heading">
      <div class="section-inner">
        <h2 id="highlights-heading" class="section-title">ماذا يميز المنصة؟</h2>
        <div class="highlights-grid">
          <article v-for="(h, i) in highlights" :key="i" class="highlight-card">
            <span class="highlight-icon" aria-hidden="true">{{ h.icon }}</span>
            <h3 class="highlight-title">{{ h.title }}</h3>
            <p class="highlight-desc">{{ h.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- تذييل معلومات -->
    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-col">
          <h3 class="footer-heading">معلومات التواصل</h3>
          <p class="footer-text">
            للاستفسارات التقنية والشراكة: راجع مستودع المشروع على GitHub أو تواصل مع فريق العمل المختص
            لدى جهتك.
          </p>
        </div>
        <div class="footer-col">
          <h3 class="footer-heading">روابط سريعة</h3>
          <ul class="footer-links">
            <li><RouterLink to="/survey">الحارس الدلالي — الاستبيان</RouterLink></li>
            <li><RouterLink to="/analysis">تحليل الملفات الجدولية</RouterLink></li>
            <li><RouterLink to="/tests">اختبارات واتصال API</RouterLink></li>
            <li><RouterLink to="/privacy">سياسة الخصوصية</RouterLink></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© {{ new Date().getFullYear() }} عين — منصة التحقق من جودة البيانات والاستبيانات.</p>
      </div>
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
  padding: 2.5rem 1.25rem 3.5rem;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 90% 50% at 50% -10%, rgba(14, 165, 233, 0.18) 0%, transparent 55%),
    radial-gradient(ellipse 50% 35% at 90% 40%, rgba(6, 182, 212, 0.1) 0%, transparent 50%),
    var(--color-background);
}

.hero-inner {
  position: relative;
  max-width: 52rem;
  margin: 0 auto;
  text-align: center;
}

.hero-brand {
  margin: 0 0 0.75rem;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #0e7490;
}

.hero-title {
  margin: 0 0 1.25rem;
  font-size: clamp(1.35rem, 4vw, 1.85rem);
  font-weight: 800;
  line-height: 1.45;
  color: var(--color-heading);
}

.hero-desc {
  margin: 0 auto 1.75rem;
  max-width: 44rem;
  font-size: 1.02rem;
  line-height: 1.85;
  color: var(--color-text);
  opacity: 0.92;
}

.hero-cta-label {
  margin: 0 0 1rem;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(1.65rem, 4.5vw, 2.15rem);
  font-weight: 700;
  font-style: italic;
  letter-spacing: 0.02em;
  color: #0e7490;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.4);
}

.hero-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  max-width: 40rem;
  margin: 0 auto;
}

@media (min-width: 640px) {
  .hero-cards {
    grid-template-columns: 1fr 1fr;
    max-width: 44rem;
  }
}

.hero-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: right;
  padding: 1.35rem 1.25rem 1.5rem;
  border-radius: 0.85rem;
  text-decoration: none;
  border: 1.5px solid var(--color-border);
  background: var(--color-background-soft);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  color: inherit;
}

.hero-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(14, 116, 144, 0.12);
  border-color: rgba(14, 165, 233, 0.35);
}

.hero-card--primary {
  border-color: rgba(14, 165, 233, 0.45);
  background: linear-gradient(165deg, rgba(6, 182, 212, 0.09) 0%, var(--color-background-soft) 55%);
}

.hero-card--secondary {
  background: var(--color-background-soft);
}

.hero-card-icon {
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}

.hero-card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.35rem;
}

.hero-card-text {
  font-size: 0.88rem;
  line-height: 1.55;
  color: var(--color-text);
  opacity: 0.88;
}

.hero-card-arrow {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  font-size: 1.25rem;
  color: #0e7490;
  opacity: 0.85;
}

/* Sections */
.section {
  padding: 3rem 1.25rem;
}

.section--muted {
  background: linear-gradient(180deg, rgba(6, 182, 212, 0.05) 0%, transparent 100%);
}

.section-inner {
  max-width: 56rem;
  margin: 0 auto;
}

.section-title {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  font-weight: 800;
  text-align: center;
  color: var(--color-heading);
}

.section-sub {
  margin: 0 0 2rem;
  text-align: center;
  font-size: 0.95rem;
  color: var(--color-text);
  opacity: 0.82;
}

.section-sub--en {
  margin: -0.25rem 0 1.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #0e7490;
  opacity: 0.9;
}

/* Services */
.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.service-card {
  padding: 1.15rem 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.service-card:hover {
  border-color: rgba(14, 165, 233, 0.3);
  box-shadow: 0 8px 24px rgba(14, 116, 144, 0.08);
}

.service-icon {
  display: block;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.service-title {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-heading);
  line-height: 1.35;
}

.service-desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text);
  opacity: 0.85;
}

/* Steps */
.steps-list {
  list-style: none;
  margin: 0 0 2.5rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (min-width: 768px) {
  .steps-list {
    flex-direction: row;
    align-items: stretch;
    gap: 1.25rem;
  }
  .step-item {
    flex: 1;
  }
}

.step-item {
  display: flex;
  gap: 0.85rem;
  padding: 1rem 1.1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.step-num {
  flex-shrink: 0;
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 800;
  font-size: 1rem;
  background: linear-gradient(145deg, #0e7490, #0891b2);
  color: #fff;
}

.step-title {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-heading);
}

.step-desc {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.55;
  color: var(--color-text);
  opacity: 0.88;
}

/* Infographic */
.how-infographic {
  padding: 1.5rem 0 0;
}

.how-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.how-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 0.85rem 1.1rem;
  min-width: 5.5rem;
  border-radius: 0.75rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
}

.how-node--mid {
  background: linear-gradient(180deg, rgba(6, 182, 212, 0.12) 0%, var(--color-background-soft) 100%);
  border-color: rgba(14, 165, 233, 0.35);
}

.how-node-icon {
  font-size: 1.75rem;
}

.how-node-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: #0e7490;
}

.how-connector {
  width: 2rem;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, #0e7490, #22d3ee);
  opacity: 0.65;
}

@media (max-width: 520px) {
  .how-connector {
    width: 80%;
    height: 3px;
    margin: 0.25rem 0;
  }
  .how-flow {
    flex-direction: column;
  }
}

/* Highlights */
.highlights-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 560px) {
  .highlights-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 960px) {
  .highlights-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.highlight-card {
  text-align: center;
  padding: 1.35rem 1rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  transition: transform 0.2s, box-shadow 0.2s;
}

.highlight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(14, 116, 144, 0.1);
}

.highlight-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.highlight-title {
  margin: 0 0 0.4rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-heading);
}

.highlight-desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text);
  opacity: 0.85;
}

/* Footer */
.site-footer {
  border-top: 1px solid var(--color-border);
  background: var(--color-background-soft);
  padding: 2.5rem 1.25rem 0;
  margin-top: 1rem;
}

.footer-inner {
  max-width: 56rem;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 640px) {
  .footer-inner {
    grid-template-columns: 1.2fr 1fr;
  }
}

.footer-heading {
  margin: 0 0 0.65rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-heading);
}

.footer-text {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.65;
  color: var(--color-text);
  opacity: 0.88;
}

.footer-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.footer-links li {
  margin-bottom: 0.5rem;
}

.footer-links a {
  font-size: 0.9rem;
  color: #0e7490;
  text-decoration: none;
  font-weight: 500;
}

.footer-links a:hover {
  text-decoration: underline;
}

.footer-bottom {
  margin-top: 2rem;
  padding: 1.25rem 1rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text);
  opacity: 0.65;
  border-top: 1px solid var(--color-border);
}

</style>
