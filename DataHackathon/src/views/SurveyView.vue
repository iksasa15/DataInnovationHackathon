<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import ValidationPanel from '../components/ValidationPanel.vue'
import { validateForm, checkHealth } from '../services/api'
import type { FormData, ValidationResult, HealthStatus } from '../services/api'
import { columnQuestionLabel, loadLfsMetadataMap } from '../utils/lfsMetadata'

/**
 * حقول بأسماء أعمدة LFS كما في `MetaData_LFS_Training_Dataset.xlsx` وملفات Excel/CSV للمسح.
 * تُحوَّل داخلياً إلى `FormData` لمسار `/api/validate`.
 */
interface LfsLiveSurveyFields {
  f_m_id: string
  gender: string
  age: number | null
  nationality: string
  q_301: string
  marage_status: string
  q_537_e_job: string
  /** سنة بداية العمل — تُستَخدَم لتقدير سنوات الخبرة للحارس الدلالي */
  d_ystartwk: number | null
  q_602_val: number | null
  q_534: string
  children_count: number | null
}

function emptyLfsSurvey(): LfsLiveSurveyFields {
  return {
    f_m_id: '',
    gender: '',
    age: null,
    nationality: '',
    q_301: '',
    marage_status: '',
    q_537_e_job: '',
    d_ystartwk: null,
    q_602_val: null,
    q_534: '',
    children_count: null,
  }
}

const form = ref<LfsLiveSurveyFields>(emptyLfsSurvey())
const lfsMeta = ref<Record<string, string>>({})

/** قواعد فقط | Gemini فقط | الاثنان — مطابق لـ ExcelView */
type AnalysisEngine = 'rules' | 'gemini' | 'both'
const analysisEngine = ref<AnalysisEngine>('both')

function lfsSurveyToApiPayload(s: LfsLiveSurveyFields): FormData {
  const y = s.d_ystartwk
  const cy = new Date().getFullYear()
  let years_experience: number | undefined
  if (typeof y === 'number' && y > 1950 && y <= cy) {
    years_experience = Math.max(0, cy - y)
  }
  return {
    name: s.f_m_id?.trim() || undefined,
    age: s.age ?? undefined,
    gender: s.gender || undefined,
    nationality: s.nationality?.trim() || undefined,
    education: s.q_301 || undefined,
    job_title: s.q_537_e_job?.trim() || undefined,
    years_experience,
    monthly_salary: s.q_602_val ?? undefined,
    sector: s.q_534 || undefined,
    marital_status: s.marage_status || undefined,
    children_count: s.children_count ?? undefined,
  }
}

function buildValidatePayload(): FormData {
  const base = lfsSurveyToApiPayload(form.value)
  const useLlm = analysisEngine.value !== 'rules'
  const applyHybrid = analysisEngine.value !== 'gemini'
  return { ...base, use_llm: useLlm, apply_hybrid_rules: applyHybrid }
}

const analyzeModeHint = computed(() => {
  switch (analysisEngine.value) {
    case 'rules':
      return 'قواعد الأعمال فقط — دون استدعاء النموذج اللغوي.'
    case 'gemini':
      return 'تحليل دلالي فقط — بدون دمج قواعد LFS الصريحة.'
    default:
      return 'Gemini (أو المزوّد المتاح) + قواعد الأعمال.'
  }
})

function meaningfulFieldCount(s: LfsLiveSurveyFields): number {
  const p = lfsSurveyToApiPayload(s)
  let n = 0
  for (const [k, v] of Object.entries(p)) {
    if (k === 'name') continue
    if (v === null || v === undefined || v === '' || v === 0) continue
    n++
  }
  return n
}

const validationFieldLabels = computed(() => {
  const m = lfsMeta.value
  const L = (tag: string, fallback: string) => {
    const q = columnQuestionLabel(tag, m)
    return q === tag ? fallback : q
  }
  const q301 = L('q_301', 'أعلى مؤهل')
  const q534 = L('q_534', 'القطاع المؤسسي')
  return {
    name: L('f_m_id', 'معرّف الفرد'),
    age: L('age', 'العمر'),
    gender: L('gender', 'جنس الفرد'),
    nationality: L('nationality', 'جنسية الفرد'),
    education: q301,
    q_301: q301,
    q_301_desc: q301,
    job_title: L('q_537_e_job', 'المسمى الوظيفي'),
    years_experience: 'سنوات الخبرة (تقدير من سنة بداية العمل)',
    monthly_salary: L('q_602_val', 'الأجر الشهري'),
    sector: q534,
    q_534: q534,
    q_534_desc: q534,
    q_302_e_txt: L('q_302_e_txt', 'مجال الدراسة / التخصص'),
    marital_status: L('marage_status', 'الحالة الاجتماعية'),
    children_count: 'عدد الأبناء',
  }
})

function labelFor(tag: string, fallback: string): string {
  const q = columnQuestionLabel(tag, lfsMeta.value)
  return q === tag ? fallback : q
}

const validationResult = ref<ValidationResult | null>(null)
const isValidating = ref(false)
const isSubmitting = ref(false)
const health = ref<HealthStatus | null>(null)
const apiError = ref(false)
const showSuccess = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const EDUCATION_OPTIONS = [
  'ابتدائي',
  'متوسط',
  'ثانوي',
  'دبلوم',
  'بكالوريوس',
  'ماجستير',
  'دكتوراه',
]
const SECTOR_OPTIONS = ['حكومي', 'خاص', 'أهلي / غير ربحي', 'لا ينطبق']
const MARITAL_OPTIONS = ['أعزب', 'متزوج', 'مطلق', 'أرمل', 'عزباء', 'متزوجة', 'مطلقة', 'أرملة']
const GENDER_OPTIONS = ['ذكر', 'أنثى']

const RANDOM_NAMES = [
  'أحمد محمد',
  'سارة علي',
  'خالد عبدالله',
  'نورة سعد',
  'فهد حسن',
  'مريم إبراهيم',
  'عمر يوسف',
  'هند عبدالرحمن',
  'تركي فيصل',
  'لمى ناصر',
]
const RANDOM_JOBS = [
  'مهندس برمجيات',
  'مدير مالي',
  'طبيب عام',
  'معلم',
  'محاسب',
  'مدير تسويق',
  'ممرض',
  'موظف إداري',
  'فني مختبر',
  'باحث',
]

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!
}

function generateRandomData() {
  const gender = pick(GENDER_OPTIONS)
  const cy = new Date().getFullYear()
  form.value = {
    f_m_id: `DEMO-${1000 + Math.floor(Math.random() * 9000)}`,
    age: 22 + Math.floor(Math.random() * 35),
    gender,
    nationality: 'سعودي / سعودية',
    q_301: pick(EDUCATION_OPTIONS),
    marage_status: pick(MARITAL_OPTIONS),
    q_537_e_job: pick(RANDOM_JOBS),
    d_ystartwk: cy - Math.floor(Math.random() * 22) - 1,
    q_602_val: 5000 + Math.floor(Math.random() * 25000),
    q_534: pick(SECTOR_OPTIONS),
    children_count: Math.floor(Math.random() * 5),
  }
  validationResult.value = null
}

onMounted(async () => {
  lfsMeta.value = await loadLfsMetadataMap(import.meta.env.BASE_URL)
  try {
    health.value = await checkHealth()
  } catch {
    apiError.value = true
  }
})

function triggerValidation() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    if (meaningfulFieldCount(form.value) < 2) {
      validationResult.value = null
      return
    }
    isValidating.value = true
    try {
      validationResult.value = await validateForm(buildValidatePayload())
      apiError.value = false
    } catch {
      apiError.value = true
    } finally {
      isValidating.value = false
    }
  }, 2500)
}

watch(form, triggerValidation, { deep: true })

watch(analysisEngine, async () => {
  validationResult.value = null
  if (meaningfulFieldCount(form.value) < 2) return
  isValidating.value = true
  try {
    validationResult.value = await validateForm(buildValidatePayload())
    apiError.value = false
  } catch {
    apiError.value = true
  } finally {
    isValidating.value = false
  }
})

async function handleSubmit() {
  if (debounceTimer) clearTimeout(debounceTimer)
  isSubmitting.value = true
  try {
    validationResult.value = await validateForm(buildValidatePayload())
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
  form.value = emptyLfsSurvey()
  validationResult.value = null
}

const mode = ref<'live' | 'demo' | 'unknown'>('unknown')
watch(health, (h) => {
  if (h) mode.value = h.mode as 'live' | 'demo'
})

const currentYear = new Date().getFullYear()
</script>

<template>
  <div class="survey-page">
    <div class="page-head">
      <h1 class="page-title">استمارة LFS (الحارس الدلالي)</h1>
      <p class="page-desc">
        حقول بأسماء الأعمدة كما في <strong>MetaData_LFS_Training_Dataset</strong> وملفات Excel؛ يُحوَّل الإدخال
        تلقائياً لصيغة التحقق. التحقق اللحظي يبدأ بعد ملء حقلين على الأقل (غير المعرّف) والتوقف عن الكتابة قليلاً.
      </p>

      <div v-if="apiError" class="banner banner-error">
        <strong>⚠ تعذّر الاتصال بالخادم</strong> — الـ backend غير مشغّل على المنفذ 8000.<br />
        من جذر المشروع: <code>./run.sh</code> أو من مجلد backend: <code>uvicorn main:app --reload --port 8000</code>
      </div>
      <div v-else-if="health && health.mode === 'demo'" class="banner banner-warning">
        🔧 وضع تجريبي — أضف <code>OPENAI_API_KEY</code> أو <code>GROQ_API_KEY</code> في ملف
        <code>backend/.env</code> لتفعيل النموذج اللغوي
      </div>
      <div v-else-if="health && health.mode === 'live'" class="banner banner-success">
        ✓ متصل — يعمل بنموذج
        {{ health.provider === 'gemini' ? 'Google Gemini' : health.provider === 'groq' ? 'Groq LLaMA' : 'OpenAI GPT' }}
        مباشرةً
      </div>

      <div class="survey-engine" role="group" aria-label="نوع التحليل">
        <span class="engine-label">نوع التحليل</span>
        <div class="engine-btns">
          <button
            type="button"
            class="engine-btn"
            :class="{ 'engine-btn-active': analysisEngine === 'rules' }"
            :disabled="isSubmitting || isValidating"
            @click="analysisEngine = 'rules'"
          >
            قواعد الأعمال
          </button>
          <button
            type="button"
            class="engine-btn"
            :class="{ 'engine-btn-active': analysisEngine === 'gemini' }"
            :disabled="isSubmitting || isValidating"
            @click="analysisEngine = 'gemini'"
          >
            Gemini
          </button>
          <button
            type="button"
            class="engine-btn"
            :class="{ 'engine-btn-active': analysisEngine === 'both' }"
            :disabled="isSubmitting || isValidating"
            @click="analysisEngine = 'both'"
          >
            الكل
          </button>
        </div>
        <p class="engine-hint">{{ analyzeModeHint }}</p>
      </div>
    </div>

    <div class="survey-layout">
      <form class="survey-form" @submit.prevent="handleSubmit" novalidate>
        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">01</span>
            معرّفات
          </h2>
          <div class="fields-grid">
            <div class="field field-full">
              <label for="f_m_id">{{ labelFor('f_m_id', 'معرّف الفرد') }} <span class="hint">(f_m_id)</span></label>
              <input id="f_m_id" v-model="form.f_m_id" type="text" placeholder="اختياري — يُرسَل كاسم للخادم" />
            </div>
          </div>
        </section>

        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">02</span>
            الخصائص الديموغرافية
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="age">{{ labelFor('age', 'العمر') }} <span class="req">*</span></label>
              <input id="age" v-model.number="form.age" type="number" min="15" max="100" placeholder="مثال: 35" />
            </div>
            <div class="field">
              <label for="gender">{{ labelFor('gender', 'جنس الفرد') }}</label>
              <select id="gender" v-model="form.gender">
                <option value="">— اختر —</option>
                <option v-for="g in GENDER_OPTIONS" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
            <div class="field field-full">
              <label for="nationality">{{ labelFor('nationality', 'جنسية الفرد') }}</label>
              <input id="nationality" v-model="form.nationality" type="text" placeholder="مثال: سعودي" />
            </div>
          </div>
        </section>

        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">03</span>
            التعليم والمهنة
          </h2>
          <div class="fields-grid">
            <div class="field field-full">
              <label for="q_301">{{ labelFor('q_301', 'أعلى مؤهل') }} <span class="req">*</span></label>
              <select id="q_301" v-model="form.q_301">
                <option value="">— اختر —</option>
                <option v-for="e in EDUCATION_OPTIONS" :key="e" :value="e">{{ e }}</option>
              </select>
            </div>
            <div class="field field-full">
              <label for="q_537_e_job">{{ labelFor('q_537_e_job', 'المسمى الوظيفي') }} <span class="req">*</span></label>
              <input
                id="q_537_e_job"
                v-model="form.q_537_e_job"
                type="text"
                placeholder="نص حر كما في الاستمارة"
              />
            </div>
            <div class="field">
              <label for="d_ystartwk">{{ labelFor('d_ystartwk', 'سنة بداية العمل') }}</label>
              <input
                id="d_ystartwk"
                v-model.number="form.d_ystartwk"
                type="number"
                :min="1970"
                :max="currentYear"
                placeholder="يُحسب منها تقدير سنوات الخبرة"
              />
            </div>
          </div>
        </section>

        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">04</span>
            العمل والأجر
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="q_602_val">{{ labelFor('q_602_val', 'الأجر الشهري') }}</label>
              <input
                id="q_602_val"
                v-model.number="form.q_602_val"
                type="number"
                min="0"
                placeholder="ر.س"
              />
            </div>
            <div class="field">
              <label for="q_534">{{ labelFor('q_534', 'القطاع') }}</label>
              <select id="q_534" v-model="form.q_534">
                <option value="">— اختر —</option>
                <option v-for="s in SECTOR_OPTIONS" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>
        </section>

        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">05</span>
            الأسرة
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="marage_status">{{ labelFor('marage_status', 'الحالة الاجتماعية') }}</label>
              <select id="marage_status" v-model="form.marage_status">
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
                placeholder="مكمّل للتحقق من التناقضات"
              />
            </div>
          </div>
        </section>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="btn-spinner"></span>
            <span>{{ isSubmitting ? 'جارٍ التحقق…' : 'تحقق نهائي من الاستمارة' }}</span>
          </button>
          <button type="button" class="btn btn-ghost" @click="generateRandomData">🎲 توليد بيانات عشوائية</button>
          <button type="button" class="btn btn-ghost" @click="resetForm">إعادة تعيين</button>
        </div>

        <Transition name="fade">
          <div v-if="showSuccess" class="toast toast-success">✓ البيانات مقبولة — درجة الثقة مرتفعة</div>
        </Transition>
      </form>

      <div class="panel-col">
        <ValidationPanel
          :result="validationResult"
          :is-loading="isValidating"
          :mode="mode"
          :field-labels="validationFieldLabels"
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

.survey-engine {
  margin-top: 1rem;
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-background-soft);
}
.engine-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-heading);
  margin-bottom: 0.45rem;
  opacity: 0.9;
}
.engine-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.engine-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.78rem;
  font-family: inherit;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.engine-btn:hover:not(:disabled) {
  background: var(--color-background-mute);
}
.engine-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.engine-btn-active {
  background: rgba(14, 116, 144, 0.14);
  border-color: #0e7490;
  color: #0e7490;
  font-weight: 600;
}
.engine-hint {
  margin: 0.55rem 0 0;
  font-size: 0.78rem;
  color: var(--color-text);
  opacity: 0.82;
  line-height: 1.45;
}

.hint {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text);
  opacity: 0.65;
}

.banner {
  margin-top: 0.75rem;
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  line-height: 1.5;
}
.banner code {
  background: rgba(0, 0, 0, 0.08);
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  font-size: 0.82rem;
}
.banner-error {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.25);
}
.banner-warning {
  background: rgba(245, 158, 11, 0.1);
  color: #92400e;
  border: 1px solid rgba(245, 158, 11, 0.25);
}
.banner-success {
  background: rgba(16, 185, 129, 0.1);
  color: #065f46;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

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

.survey-form {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

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
  background: rgba(6, 182, 212, 0.12);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  letter-spacing: 0.05em;
}

.fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 560px) {
  .fields-grid {
    grid-template-columns: 1fr;
  }
}
.field-full {
  grid-column: 1 / -1;
}

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
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.toast {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}
.toast-success {
  background: rgba(16, 185, 129, 0.12);
  color: #065f46;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (prefers-color-scheme: dark) {
  .sec-num {
    color: #22d3ee;
    background: rgba(34, 211, 238, 0.12);
  }
  .field input:focus,
  .field select:focus {
    border-color: #22d3ee;
  }
  .btn-primary {
    background: #0891b2;
  }
  .btn-primary:hover:not(:disabled) {
    background: #0e7490;
  }
  .banner-warning {
    color: #fef3c7;
  }
  .banner-success {
    color: #d1fae5;
  }
  .banner-error {
    color: #fecaca;
  }
}
</style>
