<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PitchSvgIcon from '../components/PitchSvgIcon.vue'
import { LOGO_AIN_SRC } from '../constants/branding'

const TAGLINE =
  'منصة ذكية ترفع جودة البيانات من المصدر عبر كشف التناقضات أثناء الإدخال، باستخدام الذكاء الاصطناعي لتحليل فوري يعزز الدقة ويقلل الجهد ويدعم القرار.'
</script>

<template>
  <div class="pitch-page">
    <!-- الشريحة ١ — تعريف وجملة -->
    <section class="slide slide--cover" aria-labelledby="s1">
      <div class="slide-num">١</div>
      <div class="slide-body slide-body--cover">
        <span class="pitch-hero-badge">
          <span class="pitch-hero-badge-chip" aria-hidden="true">
            <img :src="LOGO_AIN_SRC" alt="" width="28" height="28" decoding="async" />
          </span>
          عن عين
        </span>
        <p id="s1" class="pitch-tagline">{{ TAGLINE }}</p>
        <p class="slide-lead slide-lead--tight">
          حلّنا يربط نماذج لغوية كبيرة (LLM) بمسار جمع البيانات لاكتشاف التناقضات المنطقية والدلالية
          <strong>أثناء الإدخال</strong> — ضمن تحدّي «الحارس الدلالي» لجودة البيانات الإحصائية.
        </p>

        <div class="cover-goals-wrap">
          <h3 class="cover-goals-title">الأهداف</h3>
          <ul class="goals-grid goals-grid--cover" role="list">
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="target" size="lg" /></span>
              <span>رفع جودة البيانات من المصدر</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="cog" size="lg" /></span>
              <span>أتمتة التحقق وتقليل الأخطاء البشرية</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="clock" size="lg" /></span>
              <span>تسريع دورة جمع ومعالجة البيانات</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="chat" size="lg" /></span>
              <span>تعزيز الشفافية والتغذية الراجعة الفورية</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="check-circle" size="lg" /></span>
              <span>تمكين اتخاذ القرار المبني على بيانات موثوقة</span>
            </li>
            <li class="goal-card">
              <span class="goal-icon"><PitchSvgIcon name="link" size="lg" /></span>
              <span>تكامل مرن مع الأنظمة والمنصات المختلفة</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- الشريحة 2 — المشكلة + أثرها (نفس الشريحة) -->
    <section class="slide slide--problem" aria-labelledby="s2">
      <div class="slide-num">٢</div>
      <div class="slide-body">
        <h2 id="s2">المشكلة</h2>
        <p class="slide-lead slide-lead--problem">
          في سياق العمل الميداني الذي يتطلب جمع آلاف الاستبيانات، تُعد عملية التحقق اليدوي من صحة وتناسق البيانات
          (مثل: العمر، المستوى التعليمي، المهنة، الحالة الاجتماعية، مدة البحث عن عمل، وغيرها)
          <strong>تحديًا جوهريًا</strong>. إذ أن هذه العملية غالبًا ما تكون غير عملية عند هذا الحجم، كما أنها تستنزف وقتًا
          وجهدًا كبيرين بعد مرحلة جمع البيانات.
        </p>

        <div class="slide-grid-2 slide-grid-2--problem">
          <div class="card-mini">
            <h3 class="problem-split-heading">لماذا المراجعة اليدوية صعبة؟</h3>
            <ul class="card-mini-list">
              <li>حجم البيانات الكبير وعدد الحقول المتقاطعة (مئات الأعمدة في ملفات مثل LFS).</li>
              <li>التناقضات «الدلالية» لا تُمسكها قواعد جامدة فقط (مثل تعارض المسمى الوظيفي مع المؤهل).</li>
              <li>الاكتشاف المتأخر يعني إعادة اتصال أو تصحيح مكلف.</li>
            </ul>
          </div>
          <div class="card-mini card-mini--accent">
            <h3 class="problem-split-heading">أثر المشكلة على جودة البيانات</h3>
            <ul class="icon-list icon-list--impact" role="list">
              <li>
                <span class="icon-cell"><PitchSvgIcon name="chart" /></span>
                <span>زيادة احتمالية وقوع أخطاء في التقارير الإحصائية والمؤشرات المستخلصة من البيانات.</span>
              </li>
              <li>
                <span class="icon-cell"><PitchSvgIcon name="trend-down" /></span>
                <span>تراجع مستوى الثقة لدى المستخدمين وصناع القرار في مخرجات البيانات المنشورة.</span>
              </li>
              <li>
                <span class="icon-cell"><PitchSvgIcon name="cost" /></span>
                <span>ارتفاع تكاليف المعالجة اللاحقة، مثل تنظيف البيانات أو إعادة إجراء المقابلات للتحقق من صحتها.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- الشريحة 3 -->
    <section class="slide slide--flow" aria-labelledby="s3">
      <div class="slide-num">٣</div>
      <div class="slide-body">
        <h2 id="s3">كيف تعمل المنصة — المسار المختصر</h2>
        <p class="slide-lead">
          منصتنا تربط طبقة تحقق ذكية بالاستمارة أو الملف: من الإدخال إلى النتيجة في مسار واحد واضح.
        </p>
        <ol class="flow-steps">
          <li>
            <span class="flow-icon" aria-hidden="true">①</span>
            <div>
              <strong>تحليل حي</strong>
              <span>أثناء ملء الاستمارة يُرسل الحقل إلى الـ API ويُعاد تقييم درجة الثقة والتنبيهات دون انتظار الإرسال النهائي.</span>
            </div>
          </li>
          <li>
            <span class="flow-icon" aria-hidden="true">②</span>
            <div>
              <strong>رفع مستندات</strong>
              <span>استيراد Excel/CSV (استبيانات مجمّعة أو عينات تدريب) لتحليل دفعي صفاً بصف.</span>
            </div>
          </li>
          <li>
            <span class="flow-icon" aria-hidden="true">③</span>
            <div>
              <strong>تحليل ذكي</strong>
              <span>استخدام LLM مع إرشادات وسياق أعمدة (وميتاداتا LFS عند تفعيل القالب) لاكتشاف التناقضات المعقّدة.</span>
            </div>
          </li>
          <li>
            <span class="flow-icon" aria-hidden="true">④</span>
            <div>
              <strong>عرض النتائج</strong>
              <span>درجة ثقة، ملخص، أخطاء مرتبطة بالحقول، واقتراحات تصحيح — جاهزة للقراءة والتصدير.</span>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <!-- الشريحة 4 -->
    <section class="slide slide--usage" aria-labelledby="s4">
      <div class="slide-num">٤</div>
      <div class="slide-body">
        <h2 id="s4">المنصة في الاستخدام</h2>
        <p class="slide-lead">
          تجربة موحّدة: من الاستبيان المباشر إلى الجداول الكبيرة.
        </p>
        <div class="usage-blocks">
          <div>
            <h3>خطوات الاستخدام</h3>
            <ol class="slide-list ordered">
              <li>تشغيل الواجهة والخادم، التأكد من تفعيل مفتاح النموذج اللغوي (أو المودل المحلي).</li>
              <li>
                <strong>الاستبيان:</strong> فتح «الحارس الدلالي»، ملء الحقول — يظهر لوح التحقق تلقائياً بعد ثوانٍ.
              </li>
              <li>
                <strong>الملفات:</strong> فتح «تحليل الملف»، رفع Excel/CSV، تفعيل «قالب LFS» عند الحاجة، ثم «تحليل».
              </li>
              <li>مراجعة الألوان على الخلايا (حرج / متوسط / خفيف) وفتح عمود التفاصيل لكل صف.</li>
              <li>تعديل القيم في الجدول إن لزم، ثم تصدير الملف المعدّل أو التقرير النصي.</li>
            </ol>
          </div>
          <div>
            <h3>قراءة النتائج والتناقضات</h3>
            <ul class="slide-list">
              <li><strong>درجة الثقة:</strong> مقياس 0–100 يعكس اتساق الصف ككل.</li>
              <li><strong>التناقضات:</strong> قائمة بأسماء الحقول المتأثرة مع شرح عربي ودرجة الخطورة.</li>
              <li><strong>الاقتراحات:</strong> خطوات عملية لتصحيح الإدخال أو استكمال الحقول الناقصة.</li>
              <li>يمكن تصفية الصفوف (أخطاء / تحذيرات / سليمة) لتسريع المراجعة.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- الشريحة 5 — ما يميزنا، الأهداف، الخلاصة -->
    <section class="slide slide--outro" aria-labelledby="s5">
      <div class="slide-num">٥</div>
      <div class="slide-body">
        <h2 id="s5">الفائدة وما يميز حلنا</h2>

        <h3 class="subsection-title">ما يميز منصتنا</h3>
        <ul class="slide-list slide-list--spaced">
          <li>
            <strong>تكامل فعّال مع مسار جمع البيانات،</strong> من خلال واجهة تفاعلية حية مدعومة بواجهات برمجية (API)
            ومعالجة فورية.
          </li>
          <li>
            <strong>دعم متقدم لقوالب المسوح</strong> (مثل LFS)، مع إمكانية تخصيص أعمدة الوصف، وربط ميتاداتا الأسئلة،
            وتطبيق قواعد تحقق ذكية.
          </li>
          <li>
            <strong>مرونة عالية في اختيار مزودات الذكاء الاصطناعي،</strong> بما يتوافق مع مختلف البيئات التقنية
            (مثل النماذج المتوافقة مع OpenAI أو غيرها، بما في ذلك الحلول المحلية).
          </li>
        </ul>

        <div class="pitch-summary">
          <strong>الخلاصة</strong>
          <p>
            تُحوّل المنصة عملية التحقق من جودة البيانات من مرحلة لاحقة إلى جزء متكامل من عملية الإدخال نفسها؛ مما يؤدي
            إلى تسريع سير العمل، وتحسين موثوقية البيانات، ورفع كفاءة فرق العمل، مع تحقيق توافق أكبر مع متطلبات التحديات
            الحديثة في جودة البيانات.
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
  min-height: 100%;
  max-width: 920px;
  margin: 0 auto;
  padding: 1.25rem 1.25rem 2.5rem;
  font-family: var(--font-app);
  background: #f1f5f9;
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
  margin-top: 1.5rem;
  padding-top: 1.35rem;
  border-top: 1px dashed var(--ga-neutral-light, #dde2e8);
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

.slide-lead--tight {
  text-align: right;
  margin-top: 1.25rem;
  max-width: 40rem;
  margin-left: auto;
  margin-right: auto;
}

.pitch-tagline {
  font-size: 1rem;
  line-height: 1.75;
  max-width: 42rem;
  margin: 0 auto;
  color: #334155;
}

.slide {
  --slide-accent: var(--ga-primary);
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
  margin-bottom: 2.5rem;
  padding: 1.75rem 1.5rem;
  background: #fff;
  border-radius: 0.85rem;
  border: 1px solid #e8e8ef;
  border-right: 3px solid var(--slide-accent);
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.2s, transform 0.2s;
}

.slide:hover {
  box-shadow: 0 8px 28px rgba(45, 31, 69, 0.1);
}

.slide--cover {
  --slide-accent: var(--ga-primary);
  background: linear-gradient(165deg, var(--ga-primary-soft, #ebe8f7) 0%, #fff 55%, var(--ga-cyan-soft, #dff6fc) 100%);
}

.slide--problem {
  --slide-accent: var(--ga-primary-mid);
}

.slide--flow {
  --slide-accent: var(--ga-cyan);
}

.slide--usage {
  --slide-accent: var(--ga-green);
}

.slide--outro {
  --slide-accent: var(--ga-primary);
}

.slide-num {
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, var(--ga-primary, #4137a8), var(--ga-primary-dark, #322a82));
  border-radius: 0.75rem;
  line-height: 1;
}

.slide-body {
  flex: 1;
  min-width: 0;
}

.slide-body h2 {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--ga-primary-dark, #322a82);
  margin: 0 0 0.75rem;
}

.slide-body h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--ga-primary, #4137a8);
  margin: 0 0 0.5rem;
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

.problem-split-heading {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--ga-primary-dark, #322a82);
  margin: 0 0 0.65rem;
}

.slide-grid-2--problem {
  margin-top: 0.25rem;
  align-items: stretch;
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
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--ga-primary, #4137a8);
  margin: 1.35rem 0 0.65rem;
}

.subsection-title:first-of-type {
  margin-top: 0.25rem;
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

.slide-list li {
  margin-bottom: 0.45rem;
}

.slide-list.ordered {
  list-style: decimal;
  padding-right: 1.25rem;
}

.slide--problem .slide-num {
  background: linear-gradient(145deg, var(--ga-primary-mid, #5247b8), var(--ga-primary-dark, #322a82));
}

.slide--flow .slide-num {
  background: linear-gradient(145deg, var(--ga-cyan, #00b2df), #0284c7);
}

.slide--usage .slide-num {
  background: linear-gradient(145deg, var(--ga-green-dark, #3daf2e), var(--ga-green, #53cd3f));
}

.slide--outro .slide-num {
  background: linear-gradient(145deg, var(--ga-primary-mid, #5247b8), var(--ga-primary, #4137a8));
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
  padding: 1rem 1.1rem;
  background: var(--ga-surface, #f4f6f9);
  border-radius: 0.65rem;
  border: 1px solid var(--ga-neutral-light, #dde2e8);
}

.card-mini--accent {
  background: linear-gradient(180deg, var(--ga-primary-soft, #ebe8f7) 0%, #fff 100%);
  border-color: rgba(65, 55, 168, 0.18);
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
  gap: 1rem;
}

.flow-steps li {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  padding: 1rem 1.1rem;
  background: linear-gradient(90deg, var(--ga-cyan-soft, #dff6fc) 0%, #fff 40%);
  border-radius: 0.65rem;
  border: 1px solid #bae6fd;
}

.flow-icon {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--ga-cyan, #00b2df);
  line-height: 1;
}

.flow-steps strong {
  display: block;
  font-size: 1rem;
  color: var(--ga-primary-dark, #322a82);
  margin-bottom: 0.25rem;
}

.flow-steps span:not(.flow-icon) {
  font-size: 0.92rem;
  line-height: 1.65;
  color: #475569;
}

.usage-blocks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

@media (max-width: 720px) {
  .usage-blocks {
    grid-template-columns: 1fr;
  }
}

.pitch-summary {
  margin-top: 1.5rem;
  padding: 1rem 1.15rem;
  background: var(--ga-primary-soft, #ebe8f7);
  border-radius: 0.65rem;
  border-right: 4px solid var(--ga-primary, #4137a8);
  font-size: 0.98rem;
  line-height: 1.8;
  color: #1e293b;
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
  margin-top: 1.5rem;
  justify-content: flex-start;
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
