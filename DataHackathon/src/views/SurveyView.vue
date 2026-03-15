<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import ValidationPanel from '../components/ValidationPanel.vue'
import { validateForm, checkHealth } from '../services/api'
import type { FormData, ValidationResult, HealthStatus } from '../services/api'

const form = ref<FormData>({
  name: '',
  age: null,
  gender: '',
  education: '',
  job_title: '',
  years_experience: null,
  monthly_salary: null,
  sector: '',
  marital_status: '',
  children_count: null,
})

const validationResult = ref<ValidationResult | null>(null)
const isValidating = ref(false)
const isSubmitting = ref(false)
const health = ref<HealthStatus | null>(null)
const apiError = ref(false)
const showSuccess = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const EDUCATION_OPTIONS = [
  'ابتدائي', 'متوسط', 'ثانوي', 'دبلوم',
  'بكالوريوس', 'ماجستير', 'دكتوراه',
]
const SECTOR_OPTIONS = ['حكومي', 'خاص', 'أهلي / غير ربحي', 'لا ينطبق']
const MARITAL_OPTIONS = ['أعزب', 'متزوج', 'مطلق', 'أرمل', 'عزباء', 'متزوجة', 'مطلقة', 'أرملة']
const GENDER_OPTIONS = ['ذكر', 'أنثى']

const RANDOM_NAMES = ['أحمد محمد', 'سارة علي', 'خالد عبدالله', 'نورة سعد', 'فهد حسن', 'مريم إبراهيم', 'عمر يوسف', 'هند عبدالرحمن', 'تركي فيصل', 'لمى ناصر']
const RANDOM_JOBS = ['مهندس برمجيات', 'مدير مالي', 'طبيب عام', 'معلم', 'محاسب', 'مدير تسويق', 'ممرض', 'موظف إداري', 'فني مختبر', 'باحث']

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function generateRandomData() {
  const gender = pick(GENDER_OPTIONS)
  form.value = {
    name: pick(RANDOM_NAMES),
    age: 22 + Math.floor(Math.random() * 35),
    gender,
    education: pick(EDUCATION_OPTIONS),
    job_title: pick(RANDOM_JOBS),
    years_experience: Math.floor(Math.random() * 20),
    monthly_salary: 5000 + Math.floor(Math.random() * 25000),
    sector: pick(SECTOR_OPTIONS),
    marital_status: pick(MARITAL_OPTIONS),
    children_count: Math.floor(Math.random() * 5),
  }
  validationResult.value = null
}

onMounted(async () => {
  try {
    health.value = await checkHealth()
  } catch {
    apiError.value = true
  }
})

function triggerValidation() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    const filled = Object.entries(form.value).filter(
      ([k, v]) => v !== null && v !== '' && v !== 0 && k !== 'name',
    ).length
    if (filled < 2) {
      validationResult.value = null
      return
    }
    isValidating.value = true
    try {
      validationResult.value = await validateForm(form.value)
      apiError.value = false
    } catch {
      apiError.value = true
    } finally {
      isValidating.value = false
    }
  }, 2500)
}

watch(form, triggerValidation, { deep: true })

async function handleSubmit() {
  if (debounceTimer) clearTimeout(debounceTimer)
  isSubmitting.value = true
  try {
    validationResult.value = await validateForm(form.value)
    apiError.value = false
    if (validationResult.value.status === 'valid' || validationResult.value.confidence_score >= 70) {
      showSuccess.value = true
      setTimeout(() => (showSuccess.value = false), 4000)
    }
  } catch {
    apiError.value = true
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  form.value = {
    name: '', age: null, gender: '', education: '',
    job_title: '', years_experience: null, monthly_salary: null,
    sector: '', marital_status: '', children_count: null,
  }
  validationResult.value = null
}

const mode = ref<'live' | 'demo' | 'unknown'>('unknown')
watch(health, (h) => {
  if (h) mode.value = h.mode as 'live' | 'demo'
})
</script>

<template>
  <div class="survey-page">
    <!-- Page header -->
    <div class="page-head">
      <h1 class="page-title">استمارة الاستبيان</h1>
      <p class="page-desc">
        أدخل البيانات وسيقوم <strong>الحارس الدلالي</strong> بالتحقق منها لحظياً باستخدام الذكاء الاصطناعي.
      </p>

      <!-- API status banner -->
      <div v-if="apiError" class="banner banner-error">
        <strong>⚠ تعذّر الاتصال بالخادم</strong> — الـ backend غير مشغّل على المنفذ 8000.<br>
        من جذر المشروع: <code>./run.sh</code> أو من مجلد backend: <code>uvicorn main:app --reload --port 8000</code>
      </div>
      <div v-else-if="health && health.mode === 'demo'" class="banner banner-warning">
        🔧 وضع تجريبي — أضف <code>OPENAI_API_KEY</code> أو <code>GROQ_API_KEY</code> في ملف <code>backend/.env</code> لتفعيل النموذج اللغوي
      </div>
      <div v-else-if="health && health.mode === 'live'" class="banner banner-success">
        ✓ متصل — يعمل بنموذج
        {{ health.provider === 'gemini' ? 'Google Gemini' : health.provider === 'groq' ? 'Groq LLaMA' : 'OpenAI GPT' }}
        مباشرةً
      </div>
    </div>

    <div class="survey-layout">
      <!-- Form -->
      <form class="survey-form" @submit.prevent="handleSubmit" novalidate>

        <!-- Section: Personal -->
        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">01</span> المعلومات الشخصية
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="name">الاسم (اختياري)</label>
              <input id="name" v-model="form.name" type="text" placeholder="محمد أحمد…" />
            </div>
            <div class="field">
              <label for="age">العمر <span class="req">*</span></label>
              <input
                id="age"
                v-model.number="form.age"
                type="number"
                min="15"
                max="100"
                placeholder="مثال: 35"
              />
            </div>
            <div class="field">
              <label for="gender">الجنس</label>
              <select id="gender" v-model="form.gender">
                <option value="">— اختر —</option>
                <option v-for="g in GENDER_OPTIONS" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Section: Education -->
        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">02</span> المعلومات التعليمية
          </h2>
          <div class="fields-grid">
            <div class="field field-full">
              <label for="education">المستوى التعليمي <span class="req">*</span></label>
              <select id="education" v-model="form.education">
                <option value="">— اختر المؤهل العلمي —</option>
                <option v-for="e in EDUCATION_OPTIONS" :key="e" :value="e">{{ e }}</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Section: Professional -->
        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">03</span> المعلومات الوظيفية
          </h2>
          <div class="fields-grid">
            <div class="field field-full">
              <label for="job_title">المسمى الوظيفي <span class="req">*</span></label>
              <input
                id="job_title"
                v-model="form.job_title"
                type="text"
                placeholder="مثال: مدير مالي، مهندس برمجيات، طبيب…"
              />
            </div>
            <div class="field">
              <label for="years_experience">سنوات الخبرة <span class="req">*</span></label>
              <input
                id="years_experience"
                v-model.number="form.years_experience"
                type="number"
                min="0"
                max="60"
                placeholder="مثال: 8"
              />
            </div>
            <div class="field">
              <label for="monthly_salary">الراتب الشهري (ر.س)</label>
              <input
                id="monthly_salary"
                v-model.number="form.monthly_salary"
                type="number"
                min="0"
                placeholder="مثال: 12000"
              />
            </div>
            <div class="field">
              <label for="sector">القطاع</label>
              <select id="sector" v-model="form.sector">
                <option value="">— اختر —</option>
                <option v-for="s in SECTOR_OPTIONS" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Section: Family -->
        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">04</span> المعلومات الأسرية
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="marital_status">الحالة الاجتماعية</label>
              <select id="marital_status" v-model="form.marital_status">
                <option value="">— اختر —</option>
                <option v-for="m in MARITAL_OPTIONS" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
            <div class="field">
              <label for="children_count">عدد الأبناء</label>
              <input
                id="children_count"
                v-model.number="form.children_count"
                type="number"
                min="0"
                max="20"
                placeholder="مثال: 2"
              />
            </div>
          </div>
        </section>

        <!-- Actions -->
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="btn-spinner"></span>
            <span>{{ isSubmitting ? 'جارٍ التحقق…' : 'تحقق نهائي من الاستمارة' }}</span>
          </button>
          <button type="button" class="btn btn-ghost" @click="generateRandomData">🎲 توليد بيانات عشوائية</button>
          <button type="button" class="btn btn-ghost" @click="resetForm">إعادة تعيين</button>
        </div>

        <!-- Success toast -->
        <Transition name="fade">
          <div v-if="showSuccess" class="toast toast-success">
            ✓ البيانات مقبولة — درجة الثقة مرتفعة
          </div>
        </Transition>
      </form>

      <!-- Validation Panel -->
      <div class="panel-col">
        <ValidationPanel
          :result="validationResult"
          :is-loading="isValidating"
          :mode="mode"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.survey-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem 2rem 4rem;
}

/* Page header */
.page-head {
  margin-bottom: 2rem;
}
.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.5rem;
}
.page-desc {
  color: var(--color-text);
  opacity: 0.85;
  font-size: 1rem;
  margin-bottom: 1rem;
}

/* Banners */
.banner {
  margin-top: 0.75rem;
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  line-height: 1.5;
}
.banner code {
  background: rgba(0,0,0,0.08);
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  font-size: 0.82rem;
}
.banner-error   { background: rgba(239,68,68,0.1);   color: #b91c1c; border: 1px solid rgba(239,68,68,0.25); }
.banner-warning { background: rgba(245,158,11,0.1);  color: #92400e; border: 1px solid rgba(245,158,11,0.25); }
.banner-success { background: rgba(16,185,129,0.1);  color: #065f46; border: 1px solid rgba(16,185,129,0.25); }

/* Layout */
.survey-layout {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 2rem;
  align-items: start;
}
@media (max-width: 1100px) {
  .survey-layout {
    grid-template-columns: 1fr 360px;
  }
}
@media (max-width: 820px) {
  .survey-layout {
    grid-template-columns: 1fr;
  }
  .panel-col {
    order: -1;
  }
}

/* Form */
.survey-form {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

/* Section */
.form-section {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  padding: 1.5rem;
}
.form-section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.sec-num {
  font-size: 0.7rem;
  font-weight: 800;
  color: #0e7490;
  background: rgba(6,182,212,0.12);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  letter-spacing: 0.05em;
}

/* Fields grid */
.fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 560px) {
  .fields-grid { grid-template-columns: 1fr; }
}
.field-full {
  grid-column: 1 / -1;
}

/* Field */
.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}
.req {
  color: #ef4444;
}
.field input,
.field select {
  padding: 0.6rem 0.8rem;
  border: 1.5px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.9rem;
  transition: border-color 0.2s;
  width: 100%;
  font-family: inherit;
}
.field input:focus,
.field select:focus {
  outline: none;
  border-color: #0e7490;
}

/* Actions */
.form-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 0.5rem;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s ease;
  font-family: inherit;
}
.btn-primary {
  background: #0e7490;
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: #0c6380;
  transform: translateY(-1px);
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-ghost {
  background: transparent;
  color: var(--color-text);
  border-color: var(--color-border);
}
.btn-ghost:hover {
  background: var(--color-background-mute);
}
.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}
.toast-success {
  background: rgba(16,185,129,0.12);
  color: #065f46;
  border: 1px solid rgba(16,185,129,0.3);
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (prefers-color-scheme: dark) {
  .sec-num { color: #22d3ee; background: rgba(34,211,238,0.12); }
  .field input:focus, .field select:focus { border-color: #22d3ee; }
  .btn-primary { background: #0891b2; }
  .btn-primary:hover:not(:disabled) { background: #0e7490; }
  .banner-warning { color: #fef3c7; }
  .banner-success { color: #d1fae5; }
  .banner-error   { color: #fecaca; }
}
</style>
