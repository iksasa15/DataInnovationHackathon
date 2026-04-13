<script setup lang="ts">
import { RouterLink } from 'vue-router'
import HomeQualityChart from '../components/HomeQualityChart.vue'
import HomePageIcon from '../components/HomePageIcon.vue'
import type { HomeIconName } from '../components/HomePageIcon.vue'
import { LOGO_AIN_SRC } from '../constants/branding'

const summaryCards: {
  icon: HomeIconName
  title: string
  desc: string
  accent: string
}[] = [
  {
    icon: 'shield',
    title: 'كشف التناقضات',
    desc: 'تحليل دلالي للحقول مع قواعد LFS لاكتشاف التعارضات المعنوية والمنطقية.',
    accent: 'purple',
  },
  {
    icon: 'trending-up',
    title: 'الشفافية والاحترافية',
    desc: 'تقارير واضحة وتكامل آمن مع واجهة API للفرق التقنية.',
    accent: 'blue',
  },
  {
    icon: 'check-circle',
    title: 'جودة السجلات',
    desc: 'تنبيهات فورية ودرجات ثقة عند مخالفة قواعد الجودة.',
    accent: 'green',
  },
  {
    icon: 'clipboard-list',
    title: 'وضوح البيانات',
    desc: 'ميتاداتا الحقول والأسئلة لسياق أوضح أثناء المراجعة.',
    accent: 'teal',
  },
]

const services: {
  icon: HomeIconName
  title: string
  desc: string
  accent: string
}[] = [
  {
    icon: 'sparkles',
    title: 'التحليل الدلالي للحقول',
    desc: 'اكتشاف التناقضات المعنوية والمنطقية بين الحقول.',
    accent: 'purple',
  },
  {
    icon: 'table',
    title: 'معالجة البيانات الجدولية',
    desc: 'رفع Excel أو CSV وتحليل الصفوف مع تقارير واضحة.',
    accent: 'cyan',
  },
  {
    icon: 'plug',
    title: 'التكامل عبر API',
    desc: 'ربط الواجهة بخادم FastAPI لتبادل البيانات بكفاءة.',
    accent: 'green',
  },
  {
    icon: 'clipboard-check',
    title: 'فحص جودة الاستبيانات',
    desc: 'تحقق من اتساق الإجابات مع سياق الاستبيان.',
    accent: 'cyan',
  },
  {
    icon: 'search',
    title: 'كشف الأخطاء والتكرار',
    desc: 'تنبيهات ودرجات ثقة واقتراحات تصحيحية.',
    accent: 'purple',
  },
]

const steps = [
  { n: 1, title: 'رفع البيانات / الاستبيان', desc: 'استمارة حية أو ملف جدولي حسب احتياجك.', tone: 'purple' },
  {
    n: 2,
    title: 'التحليل الآلي',
    desc: 'قواعد أعمال و/أو نموذج لغوي مباشر حسب إعدادات الخادم.',
    tone: 'blue',
  },
  { n: 3, title: 'عرض النتائج والتوصيات', desc: 'ملخص، تفاصيل لكل صف، وتصفية حسب الشدة.', tone: 'green' },
]

const highlights: {
  icon: HomeIconName
  title: string
  desc: string
  accent: string
}[] = [
  { icon: 'zap', title: 'سرعة المعالجة', desc: 'معالجة دقيقة وتغذية راجعة سريعة في الاستمارة.', accent: 'purple' },
  { icon: 'target', title: 'دقة التحليل', desc: 'دمج قواعد LFS مع تحليل دلالي عند التفعيل.', accent: 'blue' },
  { icon: 'layout', title: 'سهولة الاستخدام', desc: 'واجهة عربية ومسارات واضحة للاستبيان والملفات.', accent: 'green' },
  { icon: 'settings', title: 'أتمتة كاملة', desc: 'تقليل المراجعة اليدوية المتكررة للبيانات المتشابهة.', accent: 'indigo' },
]

const flowNodes: { label: string; icon: HomeIconName; tone: string }[] = [
  { label: 'رفع', icon: 'upload', tone: 'purple' },
  { label: 'تحليل', icon: 'cpu', tone: 'blue' },
  { label: 'نتائج', icon: 'file-text', tone: 'green' },
  { label: 'تدقيق', icon: 'circle-check', tone: 'violet' },
]
</script>

<template>
  <div class="home">
    <!-- بطاقات ملخص علوية -->
    <section class="dash-summary" aria-label="ملخص المنصة">
      <article
        v-for="(c, i) in summaryCards"
        :key="i"
        class="summary-card"
        :class="'summary-card--' + c.accent"
      >
        <span class="summary-card-icon-wrap">
          <HomePageIcon :name="c.icon" :size="26" />
        </span>
        <h2 class="summary-card-title">{{ c.title }}</h2>
        <p class="summary-card-desc">{{ c.desc }}</p>
      </article>
    </section>

    <!-- بطل: رسم بياني + نص -->
    <section class="dash-hero" aria-labelledby="hero-heading">
      <div class="dash-hero-chart">
        <div class="dash-hero-chart-head">
          <div class="dash-hero-chart-titles">
            <h3 class="dash-hero-chart-title">مسار تحقق الجودة</h3>
          </div>
        </div>
        <div class="dash-hero-chart-inner">
          <HomeQualityChart />
        </div>
        <p class="dash-hero-chart-explainer">
          وضعنا هذا المنحنى لأن <strong>الجودة</strong> ليست رقماً لحظياً واحداً، بل
          <strong>مسار تحقق</strong> يمر بمراحل: إدخال، تحقق وقواعد، ثم استقرار السجل. المنحنى التصاعدي
          يعبّر عن هذه الفكرة بصرياً؛ القيم المعروضة تمثيلية ولا تعكس عيّنتك الفعلية بعد التحليل.
        </p>
        <ul class="dash-hero-chart-legend" aria-label="مفتاح الألوان">
          <li>
            <span class="chart-legend-dot chart-legend-dot--purple" aria-hidden="true" />
            بنفسجي — أساسي
          </li>
          <li>
            <span class="chart-legend-dot chart-legend-dot--cyan" aria-hidden="true" />
            سماوي — تمييز
          </li>
          <li>
            <span class="chart-legend-dot chart-legend-dot--green" aria-hidden="true" />
            أخضر — إيجابي
          </li>
        </ul>
      </div>
      <div class="dash-hero-copy">
        <h2 id="hero-heading" class="dash-hero-title">رفع جودة البيانات من المصدر</h2>
        <p class="dash-hero-text">
          منصة ذكية ترفع جودة البيانات من المصدر عبر كشف التناقضات أثناء الإدخال، باستخدام الذكاء الاصطناعي لتحليل فوري
          يعزز الدقة ويقلل الجهد ويدعم القرار.
        </p>
        <div class="dash-hero-actions">
          <RouterLink to="/survey" class="btn btn--primary">الحارس الدلالي</RouterLink>
          <RouterLink to="/analysis" class="btn btn--outline">تحليل الملف</RouterLink>
        </div>
      </div>
    </section>

    <!-- خدمات المنصة -->
    <section class="section section--surface" aria-labelledby="services-heading">
      <div class="section-inner">
        <h2 id="services-heading" class="section-title">خدمات المنصة</h2>
        <p class="section-sub">أدوات رئيسية لجودة البيانات في مسار واحد.</p>
        <div class="services-grid">
          <article
            v-for="(s, i) in services"
            :key="i"
            class="service-card"
            :class="'service-card--accent-' + s.accent"
          >
            <span class="service-icon-wrap">
              <HomePageIcon :name="s.icon" :size="22" />
            </span>
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
            <span class="step-num" :class="'step-num--' + st.tone">{{ st.n }}</span>
            <div class="step-body">
              <h3 class="step-title">{{ st.title }}</h3>
              <p class="step-desc">{{ st.desc }}</p>
            </div>
          </li>
        </ol>

        <div class="how-infographic" aria-hidden="true">
          <div class="how-flow">
            <template v-for="(node, idx) in flowNodes" :key="node.label">
              <div class="how-node" :class="'how-node--' + node.tone">
                <span class="how-node-icon-wrap">
                  <HomePageIcon :name="node.icon" :size="18" />
                </span>
                <span class="how-node-label">{{ node.label }}</span>
              </div>
              <div v-if="idx < flowNodes.length - 1" class="how-connector" />
            </template>
          </div>
        </div>
      </div>
    </section>

    <!-- ماذا يميز المنصة -->
    <section class="section section--surface" aria-labelledby="highlights-heading">
      <div class="section-inner">
        <h2 id="highlights-heading" class="section-title">ماذا يميز المنصة؟</h2>
        <div class="highlights-grid">
          <article
            v-for="(h, i) in highlights"
            :key="i"
            class="highlight-card"
            :class="'highlight-card--' + h.accent"
          >
            <span class="highlight-icon-wrap">
              <HomePageIcon :name="h.icon" :size="28" />
            </span>
            <h3 class="highlight-title">{{ h.title }}</h3>
            <p class="highlight-desc">{{ h.desc }}</p>
          </article>
        </div>
      </div>
    </section>

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
            <li><RouterLink to="/privacy">سياسة الخصوصية</RouterLink></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <div class="footer-mark" aria-hidden="true">
          <img :src="LOGO_AIN_SRC" alt="" width="22" height="22" decoding="async" />
        </div>
        <p>© {{ new Date().getFullYear() }} عين — لوحة التحقق من جودة البيانات والاستبيانات.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100%;
  padding: 1.25rem 1.25rem 2rem;
  font-family: var(--font-app);
  background: #f1f5f9;
}

@media (min-width: 1100px) {
  .home {
    padding: 1.5rem 2rem 2.5rem;
  }
}

/* ملخص علوي */
.dash-summary {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  margin-bottom: 1.35rem;
}

@media (min-width: 640px) {
  .dash-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1100px) {
  .dash-summary {
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }
}

.summary-card {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: #fff;
  border: 1px solid #e8e8ef;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
  border-top: 4px solid #cbd5e1;
  transition: box-shadow 0.2s, transform 0.2s;
}

.summary-card:hover {
  box-shadow: 0 8px 28px rgba(45, 31, 69, 0.1);
  transform: translateY(-2px);
}

.summary-card--purple {
  border-top-color: var(--ga-primary);
}
.summary-card--blue {
  border-top-color: var(--ga-cyan);
}
.summary-card--green {
  border-top-color: var(--ga-green);
}
.summary-card--teal {
  border-top-color: var(--ga-cyan);
}

.summary-card-icon-wrap {
  display: flex;
  margin-bottom: 0.45rem;
  color: var(--ga-primary);
}

.summary-card--blue .summary-card-icon-wrap {
  color: var(--ga-cyan);
}

.summary-card--green .summary-card-icon-wrap {
  color: var(--ga-green);
}

.summary-card--teal .summary-card-icon-wrap {
  color: #0d9488;
}

.summary-card-title {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
  font-weight: 800;
  color: #1e293b;
}

.summary-card-desc {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.55;
  color: #64748b;
}

/* بطل */
.dash-hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
  margin-bottom: 2rem;
  align-items: stretch;
}

@media (min-width: 960px) {
  .dash-hero {
    grid-template-columns: 1.05fr 1fr;
    gap: 1.5rem;
  }
}

.dash-hero-chart {
  background: #fff;
  border-radius: 1.25rem;
  border: 1px solid #e8e8ef;
  padding: 1.1rem 1.15rem 1rem;
  box-shadow: 0 10px 40px rgba(15, 23, 42, 0.08);
}

.dash-hero-chart-head {
  margin-bottom: 0.5rem;
}

.dash-hero-chart-titles {
  text-align: right;
}

.dash-hero-chart-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--ga-primary-dark);
  letter-spacing: 0.02em;
}

.dash-hero-chart-explainer {
  margin: 0.75rem 0 0;
  padding: 0.65rem 0.75rem;
  font-size: 0.78rem;
  line-height: 1.65;
  color: #475569;
  background: rgba(65, 55, 168, 0.04);
  border-radius: 0.5rem;
  border: 1px solid rgba(65, 55, 168, 0.1);
}

.dash-hero-chart-explainer strong {
  color: var(--ga-primary-dark);
  font-weight: 700;
}

.dash-hero-chart-inner {
  height: 240px;
}

.dash-hero-chart-legend {
  list-style: none;
  margin: 0.65rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.85rem 1.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #64748b;
}

.dash-hero-chart-legend li {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.chart-legend-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  flex-shrink: 0;
}

.chart-legend-dot--purple {
  background: var(--ga-primary-mid);
}

.chart-legend-dot--cyan {
  background: var(--ga-cyan);
}

.chart-legend-dot--green {
  background: var(--ga-green);
}

.dash-hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0.25rem 0;
}

.dash-hero-title {
  margin: 0 0 0.75rem;
  font-size: clamp(1.35rem, 3vw, 1.85rem);
  font-weight: 800;
  line-height: 1.35;
  color: #1e293b;
}

.dash-hero-text {
  margin: 0 0 1.25rem;
  font-size: 0.95rem;
  line-height: 1.75;
  color: #475569;
}

.dash-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.65rem 1.35rem;
  border-radius: 0.55rem;
  font-size: 0.92rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.btn--primary {
  background: linear-gradient(135deg, var(--ga-primary-dark), var(--ga-primary-mid));
  color: #fff;
  border: 1px solid transparent;
  box-shadow: 0 4px 14px rgba(65, 55, 168, 0.35);
}

.btn--primary:hover {
  filter: brightness(1.06);
}

.btn--outline {
  background: #fff;
  color: var(--ga-cyan);
  border: 2px solid var(--ga-cyan);
}

.btn--outline:hover {
  background: var(--ga-cyan-soft);
}

/* أقسام */
.section {
  padding: 2.25rem 0;
}

.section--surface {
  background: transparent;
  border-radius: 0;
  border: none;
  padding: 2rem 0;
  margin-bottom: 0;
  box-shadow: none;
}

.section-inner {
  max-width: 72rem;
  margin: 0 auto;
}

.section-title {
  margin: 0 0 0.5rem;
  font-size: 1.35rem;
  font-weight: 800;
  text-align: center;
  color: #1e293b;
}

.section-sub {
  margin: 0 0 1.75rem;
  text-align: center;
  font-size: 0.9rem;
  color: #64748b;
}

.section-sub--en {
  margin: -0.25rem 0 1.5rem;
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--ga-primary);
}

.services-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

@media (min-width: 640px) {
  .services-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1100px) {
  .services-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 0.85rem;
  }
}

.service-card {
  padding: 1.05rem 1rem 1.05rem 1.1rem;
  border-radius: 0.85rem;
  border: 1px solid #e8e8ef;
  border-right: 3px solid var(--service-accent, var(--ga-primary));
  background: #fff;
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.2s, transform 0.2s;
}

.service-card--accent-purple {
  --service-accent: var(--ga-primary);
}

.service-card--accent-cyan {
  --service-accent: var(--ga-cyan);
}

.service-card--accent-green {
  --service-accent: var(--ga-green);
}

.service-card:hover {
  box-shadow: 0 8px 28px rgba(45, 31, 69, 0.1);
  transform: translateY(-2px);
}

.service-icon-wrap {
  display: flex;
  margin-bottom: 0.4rem;
  color: var(--service-icon-c, var(--ga-primary));
}

.service-card--accent-cyan .service-icon-wrap {
  --service-icon-c: var(--ga-cyan);
}

.service-card--accent-green .service-icon-wrap {
  --service-icon-c: var(--ga-green);
}

.service-title {
  margin: 0 0 0.3rem;
  font-size: 0.9rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.35;
}

.service-desc {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.5;
  color: #64748b;
}

/* خطوات */
.steps-list {
  list-style: none;
  margin: 0 0 1.75rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

@media (min-width: 900px) {
  .steps-list {
    flex-direction: row;
    align-items: stretch;
  }
  .step-item {
    flex: 1;
  }
}

.step-item {
  display: flex;
  gap: 0.85rem;
  padding: 1.15rem 1.1rem;
  border-radius: 1rem;
  border: 1px solid #e8e8ef;
  background: #fff;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
}

.step-num {
  flex-shrink: 0;
  width: 2.35rem;
  height: 2.35rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 800;
  font-size: 0.95rem;
  color: #fff;
}

.step-num--purple {
  background: linear-gradient(145deg, var(--ga-primary-dark), var(--ga-primary-mid));
}
.step-num--blue {
  background: linear-gradient(145deg, #0095bc, var(--ga-cyan));
}
.step-num--green {
  background: linear-gradient(145deg, var(--ga-green-dark), var(--ga-green));
}

.step-title {
  margin: 0 0 0.2rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
}

.step-desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.55;
  color: #64748b;
}

.how-infographic {
  border: 2px dashed #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1.25rem 1rem;
}

.how-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.how-node {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1.1rem;
  min-width: auto;
  border-radius: 999px;
  border: 1px solid transparent;
  background: #fff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.how-node--purple {
  border-color: rgba(65, 55, 168, 0.25);
  background: linear-gradient(180deg, #fff 0%, rgba(65, 55, 168, 0.08) 100%);
}
.how-node--blue {
  border-color: rgba(0, 178, 223, 0.3);
  background: linear-gradient(180deg, #fff 0%, rgba(0, 178, 223, 0.1) 100%);
}
.how-node--green {
  border-color: rgba(83, 205, 63, 0.3);
  background: linear-gradient(180deg, #fff 0%, rgba(83, 205, 63, 0.1) 100%);
}
.how-node--violet {
  border-color: rgba(50, 42, 130, 0.35);
  background: linear-gradient(180deg, #fff 0%, rgba(65, 55, 168, 0.12) 100%);
}

.how-node-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ga-primary-dark);
}

.how-node-label {
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--ga-primary-dark);
}

.how-connector {
  width: 1.5rem;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--ga-primary-mid), var(--ga-cyan));
  opacity: 0.65;
  flex-shrink: 0;
}

@media (max-width: 520px) {
  .how-flow {
    flex-direction: column;
  }
  .how-connector {
    width: 3px;
    height: 1.25rem;
  }
}

/* تمييزات */
.highlights-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  direction: rtl;
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
  padding: 1.25rem 0.9rem;
  border-radius: 1rem;
  border: 1px solid #e8e8ef;
  background: #fff;
  border-top: 4px solid #cbd5e1;
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.highlight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(45, 31, 69, 0.1);
}

.highlight-card--blue {
  border-top-color: var(--ga-cyan);
}
.highlight-card--purple {
  border-top-color: var(--ga-primary-mid);
}
.highlight-card--amber {
  border-top-color: #f59e0b;
}
.highlight-card--green {
  border-top-color: var(--ga-green);
}
.highlight-card--indigo {
  border-top-color: var(--ga-primary-dark);
}

.highlight-icon-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 0.4rem;
  color: var(--ga-primary);
}

.highlight-card--purple .highlight-icon-wrap {
  color: var(--ga-primary-mid);
}

.highlight-card--blue .highlight-icon-wrap {
  color: var(--ga-cyan);
}

.highlight-card--green .highlight-icon-wrap {
  color: var(--ga-green);
}

.highlight-card--indigo .highlight-icon-wrap {
  color: var(--ga-primary-dark);
}

.highlight-title {
  margin: 0 0 0.35rem;
  font-size: 0.92rem;
  font-weight: 700;
  color: #1e293b;
}

.highlight-desc {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.5;
  color: #64748b;
}

/* تذييل */
.site-footer {
  position: relative;
  margin-top: 2rem;
  margin-inline: -1.25rem -1.25rem;
  margin-bottom: -2rem;
  padding: 2.5rem 1.25rem 0;
  background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 48%, #0c1222 100%);
  color: #e2e8f0;
}

.site-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--ga-green), var(--ga-cyan));
  border-radius: 0;
}

@media (min-width: 1100px) {
  .site-footer {
    margin-inline: -2rem -2rem;
    margin-bottom: -2.5rem;
    padding-inline: 2rem;
  }
}

.footer-inner {
  max-width: 56rem;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.75rem;
}

@media (min-width: 640px) {
  .footer-inner {
    grid-template-columns: 1.2fr 1fr;
  }
}

.footer-heading {
  margin: 0 0 0.55rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: #fff;
}

.footer-text {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.65;
  opacity: 0.85;
}

.footer-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.footer-links li {
  margin-bottom: 0.45rem;
}

.footer-links a {
  font-size: 0.88rem;
  color: #a5b4fc;
  text-decoration: none;
  font-weight: 500;
}

.footer-links a:hover {
  color: #fff;
  text-decoration: underline;
}

.footer-bottom {
  margin-top: 1.75rem;
  padding: 1.25rem 1rem 1.75rem;
  text-align: center;
  font-size: 0.75rem;
  color: rgba(226, 232, 240, 0.65);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-bottom p {
  margin: 0.5rem 0 0;
}

.footer-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  margin: 0 auto;
  border-radius: 50%;
  background: #fff;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}

.footer-mark img {
  width: 1.35rem;
  height: 1.35rem;
  object-fit: contain;
  display: block;
}
</style>
