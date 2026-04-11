<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PitchSvgIcon from '../components/PitchSvgIcon.vue'
import { LOGO_AIN_SRC } from '../constants/branding'

const TAGLINE =
  'منصة ذكية ترفع جودة البيانات من المصدر عبر كشف التناقضات المنطقية والدلالية باستخدام الذكاء الاصطناعي، سواء في الاستمارة الحية أو عند تحليل الملفات الجدولية. ويربط الحل بين نماذج اللغة الكبيرة وقواعد الأعمال ومسار جمع البيانات، لتحويل التحقق من مرحلة لاحقة إلى جزء مباشر من دورة العمل، بما يعزز الدقة ويقلل الجهد في المراجعة اللاحقة.'
</script>

<template>
  <div class="pitch-page">
    <!-- الشريحة ١ — تعريف وجملة -->
    <section class="slide slide--cover" aria-labelledby="s1">
      <div class="slide-body slide-body--cover">
        <span class="pitch-hero-badge">
          <span class="pitch-hero-badge-chip" aria-hidden="true">
            <img :src="LOGO_AIN_SRC" alt="" width="28" height="28" decoding="async" />
          </span>
          عن عين
        </span>
        <p id="s1" class="pitch-tagline">{{ TAGLINE }}</p>

        <div class="cover-goals-wrap">
          <h3 class="cover-goals-title">الأهداف</h3>
          <ul class="goals-grid goals-grid--cover" role="list">
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="target" size="lg" /></span>
              <span>رفع جودة البيانات من المصدر</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="cog" size="lg" /></span>
              <span>تقليل الأخطاء البشرية والجهد اليدوي</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="clock" size="lg" /></span>
              <span>تسريع جمع ومعالجة البيانات</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="check-circle" size="lg" /></span>
              <span>دعم القرار ببيانات أكثر موثوقية</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="chat" size="lg" /></span>
              <span>تعزيز التغذية الراجعة الفورية</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- الشريحة 2 — المشكلة + أثرها (نفس الشريحة) -->
    <section class="slide slide--problem" aria-labelledby="s2">
      <div class="slide-body">
        <h2 id="s2">المشكلة</h2>
        <p class="slide-lead slide-lead--problem">
          في الأعمال الميدانية وجمع الاستبيانات والملفات بكميات كبيرة، يصبح التحقق اليدوي من صحة البيانات واتساقها
          <strong>تحدّيًا كبيرًا</strong>، خاصة مع وجود حقول مترابطة وتناقضات دلالية ومنطقية لا تكشفها القواعد التقليدية
          بسهولة، مما يؤدي إلى اكتشافها في مراحل متأخرة.
        </p>

        <div class="slide-grid-2 slide-grid-2--problem">
          <div class="card-mini">
            <h3 class="problem-split-heading">لماذا المراجعة اليدوية صعبة؟</h3>
            <ul class="card-mini-list">
              <li>كثرة السجلات وتعدد الحقول المترابطة.</li>
              <li>صعوبة اكتشاف التناقضات الدلالية يدويًا.</li>
              <li>الاكتشاف المتأخر يرفع تكلفة التصحيح والمعالجة.</li>
            </ul>
          </div>
          <div class="card-mini card-mini--accent">
            <h3 class="problem-split-heading">أثر المشكلة على جودة البيانات</h3>
            <ul class="icon-list icon-list--impact" role="list">
              <li>
                <span class="icon-cell"><PitchSvgIcon name="chart" /></span>
                <span>ارتفاع احتمال الأخطاء في التقارير والمؤشرات.</span>
              </li>
              <li>
                <span class="icon-cell"><PitchSvgIcon name="trend-down" /></span>
                <span>تراجع الثقة في المخرجات.</span>
              </li>
              <li>
                <span class="icon-cell"><PitchSvgIcon name="cost" /></span>
                <span>زيادة الوقت والجهد في المعالجة اللاحقة.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- الشريحة 3 -->
    <section class="slide slide--flow" aria-labelledby="s3">
      <div class="slide-body">
        <h2 id="s3">كيف تعمل المنصة</h2>
        <p class="slide-lead">
          تربط المنصة طبقة تحقق ذكية بمسار البيانات، بحيث تنتقل من الإدخال أو الرفع إلى النتيجة في مسار واضح وسريع.
        </p>
        <h3 class="subsection-title flow-path-heading">المسار</h3>
        <ul class="flow-steps">
          <li>
            <div>
              <strong>الاستمارة الحية</strong>
              <span>أثناء تعبئة الحقول، يتم تحليل البيانات، ثم تعرض النتيجة بشكل فوري مع درجة ثقة وتنبيهات واضحة.</span>
            </div>
          </li>
          <li>
            <div>
              <strong>تحليل الملفات</strong>
              <span>يمكن رفع ملفات Excel وCSV لتحليل السجلات دفعة واحدة واكتشاف التناقضات داخل البيانات المجمّعة.</span>
            </div>
          </li>
          <li>
            <div>
              <strong>تحليل ذكي</strong>
              <span>تعتمد المنصة على نماذج لغوية وقواعد أعمال لاكتشاف التناقضات المنطقية والدلالية بشكل أكثر دقة.</span>
            </div>
          </li>
          <li>
            <div>
              <strong>عرض النتائج</strong>
              <span>تعرض النتائج في صورة حالة، ودرجة ثقة، وتنبيهات، وحقول متأثرة، واقتراحات تساعد على المراجعة والتصحيح.</span>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <!-- الشريحة 4 -->
    <section class="slide slide--usage" aria-labelledby="s4">
      <div class="slide-body">
        <h2 id="s4">المنصة في الاستخدام</h2>
        <p class="slide-lead">
          توفر المنصة تجربة موحدة تجمع بين الاستبيان الحي وتحليل الملفات، بما يساعد على فهم التناقضات واتخاذ الإجراء
          المناسب بسرعة.
        </p>
        <div class="usage-blocks">
          <div class="usage-blocks__panel">
            <h3>خطوات الاستخدام</h3>
            <ul class="slide-list">
              <li>اختيار مسار الاستمارة الحية أو رفع ملف Excel أو CSV.</li>
              <li>تنفيذ التحليل باستخدام قواعد الأعمال أو النموذج اللغوي أو الاثنين معًا.</li>
              <li>عرض النتائج حسب مستوى الشدة والحالة.</li>
              <li>تحديد الحقول المتأثرة داخل السجل أو الملف.</li>
              <li>مراجعة الاقتراحات واتخاذ إجراء التصحيح أو التصدير.</li>
            </ul>
          </div>
          <div class="usage-blocks__panel">
            <h3>قراءة النتائج</h3>
            <ul class="slide-list">
              <li><strong>درجة ثقة</strong> تعكس مدى اتساق السجل.</li>
              <li>قائمة بالتناقضات والملاحظات.</li>
              <li>تمييز الحقول المتأثرة.</li>
              <li>اقتراحات للمراجعة أو التصحيح.</li>
              <li>إمكانية فرز الحالات حسب الأولوية.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- الشريحة 5 — ما يميز عين، الخلاصة -->
    <section class="slide slide--outro" aria-labelledby="s5">
      <div class="slide-body">
        <h2 id="s5">ما الذي يميز عين؟</h2>
        <p class="slide-lead slide-lead--outro">
          يتميّز حلّنا بأنه لا يتعامل مع جودة البيانات كمرحلة لاحقة بعد اكتمال الجمع، بل يدمج التحقق الذكي داخل مسار
          العمل نفسه، سواء في الاستمارة الحية أو في تحليل الملفات، مما يرفع جودة البيانات مبكرًا ويقلل تكاليف المعالجة
          اللاحقة.
        </p>

        <h3 class="subsection-title">ما يميز المنصة</h3>
        <ul class="slide-list slide-list--spaced">
          <li>الجمع بين الاستمارة الحية وتحليل الملفات في تجربة موحدة.</li>
          <li>كشف دلالي ومنطقي وليس تحققًا شكليًا فقط.</li>
          <li>عرض درجة ثقة وتنبيهات واضحة واقتراحات عملية.</li>
          <li>دعم قواعد الأعمال والنموذج اللغوي ضمن تجربة موحدة.</li>
          <li>تمكين المستخدم من الوصول السريع إلى موضع الإشكال.</li>
        </ul>

        <div class="pitch-summary">
          <strong>الخلاصة</strong>
          <p>
            تحوّل المنصة التحقق من جودة البيانات من خطوة لاحقة ومكلفة إلى عملية فورية ومندمجة ضمن دورة العمل، بما يعزز
            موثوقية البيانات ويرفع كفاءة المعالجة ويدعم اتخاذ القرار.
          </p>
        </div>
        <div class="pitch-cta">
          <RouterLink to="/survey" class="pitch-btn pitch-btn--primary">جرب الاستبيان</RouterLink>
          <RouterLink to="/analysis" class="pitch-btn pitch-btn--outline">تحليل ملف</RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.pitch-page {
  --pitch-surface-grad: linear-gradient(
    165deg,
    var(--ga-primary-soft, #ebe8f7) 0%,
    #fff 52%,
    var(--ga-cyan-soft, #dff6fc) 100%
  );
  --pitch-border: 1px solid rgba(65, 55, 168, 0.14);
  --pitch-rail: 3px solid rgba(82, 71, 184, 0.42);

  min-height: 100%;
  max-width: 920px;
  margin: 0 auto;
  padding: 1.25rem 1.25rem 2.5rem;
  font-family: var(--font-app);
  background: linear-gradient(180deg, #e8eaf5 0%, #f0f4fa 38%, #f4f2fb 100%);
  color: var(--ga-primary-darker, #1a1530);
}

@media (min-width: 1100px) {
  .pitch-page {
    padding: 1.5rem 2rem 3rem;
  }
}

.pitch-hero-badge {
  display: inline-flex;
  align-items: center;
  align-self: center;
  gap: 0.45rem;
  padding: 0.2rem 0.65rem 0.2rem 0.2rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  background: var(--ga-primary-soft);
  color: var(--ga-primary-dark);
  margin-bottom: 0.65rem;
}

.pitch-hero-badge-chip {
  flex-shrink: 0;
  width: 1.85rem;
  height: 1.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 0.12rem;
  box-sizing: border-box;
}

.pitch-hero-badge-chip img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.slide-body--cover {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.cover-goals-wrap {
  margin-top: 1.75rem;
  padding-top: 1.5rem;
  border-top: 1px dashed rgba(65, 55, 168, 0.2);
  width: 100%;
  max-width: 100%;
  text-align: right;
}

.cover-goals-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--ga-primary, #4137a8);
  margin: 0 0 0.85rem;
  text-align: center;
}

.goals-grid--cover {
  margin-top: 0;
}

.pitch-tagline {
  font-size: 1rem;
  line-height: 1.8;
  max-width: 40rem;
  margin: 0 auto;
  color: #334155;
}

.slide {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1.35rem;
  padding: 1.5rem 1.35rem 1.6rem;
  border-radius: 1rem;
  background: var(--pitch-surface-grad);
  border: var(--pitch-border);
  border-right: var(--pitch-rail);
  box-shadow: 0 4px 22px rgba(65, 55, 168, 0.08);
  transition: box-shadow 0.22s ease;
}

.slide:hover {
  box-shadow: 0 8px 32px rgba(65, 55, 168, 0.11);
}

.slide--cover {
  padding: 1.85rem 1.5rem 2rem;
}

.slide-body {
  flex: 1;
  min-width: 0;
}

.slide-body h2 {
  font-size: 1.28rem;
  font-weight: 800;
  color: var(--ga-primary-dark, #322a82);
  margin: 0 0 0.85rem;
  letter-spacing: -0.02em;
}

.slide-body:not(.slide-body--cover) h2 {
  padding-bottom: 0.65rem;
  border-bottom: 1px solid rgba(65, 55, 168, 0.12);
  margin-bottom: 1rem;
}

.slide-body h3 {
  font-size: 0.98rem;
  font-weight: 800;
  color: var(--ga-primary-dark, #322a82);
  margin: 0 0 0.55rem;
}

.slide-lead {
  font-size: 0.98rem;
  line-height: 1.8;
  margin: 0 0 1rem;
  color: #334155;
}

.slide-lead--problem {
  margin-bottom: 1.35rem;
}

.slide-lead--outro {
  margin-bottom: 1rem;
}

.problem-split-heading {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--ga-primary-dark, #322a82);
  margin: 0 0 0.65rem;
}

.slide-grid-2--problem {
  margin-top: 0.5rem;
  align-items: stretch;
  gap: 1.1rem;
}

.icon-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.icon-list--impact li {
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
  padding: 0.85rem 1rem;
  background: linear-gradient(180deg, var(--ga-primary-soft, #ebe8f7) 0%, #fff 100%);
  border: 1px solid rgba(65, 55, 168, 0.18);
  border-radius: 0.65rem;
  font-size: 0.92rem;
  line-height: 1.7;
  color: #334155;
}

.icon-cell {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 0.5rem;
  border: 1px solid rgba(65, 55, 168, 0.15);
  line-height: 0;
}

.icon-cell :deep(.pitch-svg-icon) {
  width: 1.35rem;
  height: 1.35rem;
}

.subsection-title {
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--ga-primary, #4137a8);
  margin: 1.15rem 0 0.75rem;
}

.subsection-title:first-of-type {
  margin-top: 0.35rem;
}

.flow-path-heading {
  margin-top: 0.85rem;
}

.slide-list--spaced li {
  margin-bottom: 0.65rem;
}

.goals-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.65rem;
}

@media (max-width: 640px) {
  .goals-grid {
    grid-template-columns: 1fr;
  }
}

.goal-card {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.75rem 0.85rem;
  background: var(--ga-primary-soft, #ebe8f7);
  border: 1px solid rgba(65, 55, 168, 0.15);
  border-radius: 0.55rem;
  font-size: 0.88rem;
  line-height: 1.55;
  color: #1e293b;
}

.goal-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.goal-icon :deep(.pitch-svg-icon--lg) {
  width: 1.75rem;
  height: 1.75rem;
}

.slide-list {
  margin: 0;
  padding: 0 1.15rem 0 0;
  font-size: 0.95rem;
  line-height: 1.75;
  color: #334155;
}

.usage-blocks__panel .slide-list {
  padding-right: 1.1rem;
}

.slide-list li {
  margin-bottom: 0.45rem;
}

.slide-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 720px) {
  .slide-grid-2 {
    grid-template-columns: 1fr;
  }
}

.card-mini {
  padding: 1.05rem 1.15rem;
  background: rgba(255, 255, 255, 0.72);
  border-radius: 0.75rem;
  border: 1px solid rgba(65, 55, 168, 0.12);
  box-shadow: 0 2px 12px rgba(65, 55, 168, 0.06);
}

.card-mini--accent {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, var(--ga-primary-soft, #ebe8f7) 100%);
  border-color: rgba(65, 55, 168, 0.14);
}

.card-mini ul {
  margin: 0.5rem 0 0;
  padding: 0 1rem 0 0;
  font-size: 0.9rem;
  line-height: 1.65;
  color: #475569;
}

.flow-steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.flow-steps li {
  padding: 1rem 1.15rem;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.92) 0%, var(--ga-primary-soft, #ebe8f7) 100%);
  border-radius: 0.75rem;
  border: 1px solid rgba(65, 55, 168, 0.12);
  box-shadow: 0 2px 10px rgba(65, 55, 168, 0.05);
}

.flow-steps strong {
  display: block;
  font-size: 1rem;
  color: var(--ga-primary-dark, #322a82);
  margin-bottom: 0.25rem;
}

.flow-steps li span {
  font-size: 0.92rem;
  line-height: 1.65;
  color: #475569;
}

.usage-blocks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.35rem;
  align-items: stretch;
}

.usage-blocks__panel {
  padding: 1.1rem 1.15rem 1.15rem;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(65, 55, 168, 0.11);
  border-radius: 0.75rem;
  box-shadow: 0 2px 14px rgba(65, 55, 168, 0.06);
}

.usage-blocks__panel h3 {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--ga-primary, #4137a8);
}

@media (max-width: 720px) {
  .usage-blocks {
    grid-template-columns: 1fr;
  }
}

.pitch-summary {
  margin-top: 1.65rem;
  padding: 1.15rem 1.2rem;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.9) 0%, var(--ga-primary-soft, #ebe8f7) 100%);
  border-radius: 0.75rem;
  border: 1px solid rgba(65, 55, 168, 0.12);
  border-right: 4px solid var(--ga-primary-mid, #5247b8);
  font-size: 0.98rem;
  line-height: 1.8;
  color: #1e293b;
  box-shadow: 0 2px 14px rgba(65, 55, 168, 0.06);
}

.pitch-summary strong {
  display: block;
  font-size: 1.05rem;
  margin-bottom: 0.5rem;
  color: var(--ga-primary-dark, #322a82);
}

.pitch-summary p {
  margin: 0;
  line-height: 1.85;
}

.pitch-cta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.65rem;
  justify-content: center;
}

.pitch-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.65rem 1.35rem;
  border-radius: 0.55rem;
  font-size: 0.92rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s, color 0.2s, border-color 0.2s, filter 0.2s;
}

.pitch-btn--primary {
  background: linear-gradient(135deg, var(--ga-primary-dark), var(--ga-primary-mid));
  color: #fff;
  border: 1px solid transparent;
  box-shadow: 0 4px 14px rgba(65, 55, 168, 0.35);
}

.pitch-btn--primary:hover {
  filter: brightness(1.06);
}

.pitch-btn--outline {
  background: #fff;
  color: var(--ga-cyan);
  border: 2px solid var(--ga-cyan);
}

.pitch-btn--outline:hover {
  background: var(--ga-cyan-soft);
}
</style>
