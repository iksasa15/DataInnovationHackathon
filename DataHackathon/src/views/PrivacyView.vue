<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="privacy-page">
    <RouterLink to="/" class="back">← العودة للرئيسية</RouterLink>
    <h1>سياسة الخصوصية</h1>
    <p class="lead">
      تهدف منصة عين إلى معالجة بيانات الاستبيان والملفات الجدولية لأغراض التحقق من الجودة فقط، وفق ما
      يتيحه إعداد الخادم لديك.
    </p>
    <section>
      <h2>البيانات المرسلة</h2>
      <p>
        عند استخدام الاستبارة أو رفع ملف، تُرسل المحتويات إلى واجهة برمجة التطبيقات (API) على الخادم الذي
        تضبطه. لا تُخزَّن هذه البيانات في الواجهة الأمامية بعد إغلاق الجلسة ما لم يُنفَّذ ذلك صراحة في
        الخادم.
      </p>
    </section>
    <section>
      <h2>مفاتيح الخدمات</h2>
      <p>
        مفاتيح مثل Gemini أو غيرها يجب أن تُضبط على الخادم أو عبر القنوات الآمنة المعتمدة لديك، ولا يُنصح
        بمشاركتها في الواجهة العامة.
      </p>
    </section>
    <section>
      <h2>تحديثات</h2>
      <p>قد تُحدَّث هذه الصفحة عند تغيّر ممارسات المعالجة. آخر مراجعة: {{ new Date().getFullYear() }}.</p>
    </section>
  </div>
</template>

<style scoped>
.privacy-page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}
.back {
  display: inline-block;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
  color: #0e7490;
  text-decoration: none;
}
.back:hover {
  text-decoration: underline;
}
h1 {
  font-size: 1.75rem;
  color: var(--color-heading);
  margin: 0 0 1rem;
}
.lead {
  line-height: 1.7;
  color: var(--color-text);
  opacity: 0.9;
  margin-bottom: 2rem;
}
section {
  margin-bottom: 1.5rem;
}
h2 {
  font-size: 1.1rem;
  color: var(--color-heading);
  margin: 0 0 0.5rem;
}
p {
  margin: 0;
  line-height: 1.65;
  color: var(--color-text);
  opacity: 0.88;
  font-size: 0.95rem;
}
</style>
