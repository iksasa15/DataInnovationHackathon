<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import SurveyLiveSidebar from '../components/SurveyLiveSidebar.vue'
import { validateForm, checkHealth } from '../services/api'
import type { FormData, HealthStatus, ValidationError, ValidationResult } from '../services/api'
import { loadLfsMetadataMap } from '../utils/lfsMetadata'
import { resolveLfsTableColumnHeader } from '../utils/lfsTableColumnHeader'

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
  /** صلة القرابة برئيس الأسرة */
  family_relation: string
  q_537_e_job: string
  /** سنة بداية العمل — تُستَخدَم لتقدير سنوات الخبرة للحارس الدلالي */
  d_ystartwk: number | null
  q_602_val: number | null
  q_534: string
  /** عنوان النشاط الاقتصادي (نص حر) */
  economic_activity_text: string
  weekly_hours_usual: number | null
  weekly_hours_actual: number | null
  ilo_employment_status: string
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
    family_relation: '',
    q_537_e_job: '',
    d_ystartwk: null,
    q_602_val: null,
    q_534: '',
    economic_activity_text: '',
    weekly_hours_usual: null,
    weekly_hours_actual: null,
    ilo_employment_status: '',
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
    family_relation: s.family_relation?.trim() || undefined,
    economic_activity_text: s.economic_activity_text?.trim() || undefined,
    weekly_hours_usual: s.weekly_hours_usual ?? undefined,
    weekly_hours_actual: s.weekly_hours_actual ?? undefined,
    ilo_employment_status: s.ilo_employment_status?.trim() || undefined,
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

function normField(s: string): string {
  return s.trim().toLowerCase().replace(/[_\-\s]+/g, '')
}

/**
 * أي أخطاء تُعرض تحت حقل محدد في الاستمارة (يربط أسماء الـ API بحقول النموذج،
 * ويُكرّر تنبيهات العمر↔المؤهل تحت العمر والمؤهل معاً).
 */
function fieldKeysForError(e: ValidationError): string[] {
  const f = normField(String(e.field || ''))
  const out = new Set<string>()
  const add = (k: string) => out.add(k)

  if (!f || f === '?') {
    /* ignore */
  } else if (f === 'age') {
    add('age')
  } else if (f.includes('q301') || f.includes('301') || f === 'education') {
    add('q_301')
  } else if (f.includes('q537') || f.includes('job') || f === 'jobtitle') {
    add('q_537_e_job')
  } else if (f.includes('q534') || f.includes('534') || f === 'sector') {
    add('q_534')
  } else if (f.includes('marage') || f.includes('marital')) {
    add('marage_status')
  } else if (f.includes('602') || f.includes('salary')) {
    add('q_602_val')
  } else if (f.includes('weeklyhoursusual') || f === 'weeklyhoursusual' || f.includes('q501') || f === 'weekly_hours_usual') {
    add('weekly_hours_usual')
  } else if (f.includes('weeklyhoursactual') || f === 'weekly_hours_actual') {
    add('weekly_hours_actual')
  } else if (f.includes('economic') || f.includes('q536') || f.includes('536')) {
    add('economic_activity_text')
  } else if (f.includes('familyrelation') || f.includes('family_relation')) {
    add('family_relation')
  } else if (f.includes('ilostat') || f.includes('ilo') || f.includes('employmentstatus')) {
    add('ilo_employment_status')
  } else if (f.includes('children')) {
    add('children_count')
  } else if (f.includes('ystartwk') || f.includes('experience')) {
    add('d_ystartwk')
  } else if (f.includes('nationality')) {
    add('nationality')
  } else if (f.includes('gender')) {
    add('gender')
  } else if (f.includes('fmid') || f === 'name') {
    add('f_m_id')
  }

  const msg = (e.message || '').toLowerCase()
  const rid = e.rule_id
  if (
    rid === 2011 ||
    rid === 2012 ||
    rid === 2013 ||
    rid === 2015 ||
    rid === 2016 ||
    rid === 2017 ||
    (msg.includes('عمر') && (msg.includes('مؤهل') || msg.includes('ثانوي') || msg.includes('دبلوم') || msg.includes('بكالوريوس') || msg.includes('ماجستير') || msg.includes('دكتور')))
  ) {
    add('age')
    add('q_301')
  }
  if (rid === 2017 || (msg.includes('q_301') && msg.includes('302'))) {
    add('q_301')
  }

  const rc = e.rule_code
  if (rc === 'LFS_SALARY_HIGH') add('q_602_val')
  if (rc === 'LFS_HOURS_HIGH') add('weekly_hours_usual')
  if (rc === 'BR_4008') {
    add('age')
    add('q_301')
  }

  return [...out]
}

function inlineErrorsFor(fieldKey: string): ValidationError[] {
  const vr = validationResult.value
  if (!vr?.errors?.length) return []
  return vr.errors.filter((e) => fieldKeysForError(e).includes(fieldKey))
}

function labelFor(tag: string, fallback: string): string {
  const r = resolveLfsTableColumnHeader(tag, lfsMeta.value)
  const main = r.shortLabel !== r.technicalId ? r.shortLabel : fallback
  return r.category ? `${r.category} — ${main}` : main
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
const FAMILY_RELATION_OPTIONS = [
  'رب الأسرة',
  'زوج / زوجة',
  'ابن / ابنة',
  'أب / أم',
  'آخر',
]
const ILO_STATUS_OPTIONS = [
  'موظف',
  'عامل لحسابه الخاص',
  'عاطل عن العمل',
  'طالب',
  'متقاعد',
  'رب منزل',
  'أخرى',
]

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

/** مؤهلات تُفعّل تعارض العمر مع قاعدة البكالوريوس+ عند العمر الأقل من 21 */
const BACHELOR_PLUS: readonly string[] = ['بكالوريوس', 'ماجستير', 'دكتوراه']

/**
 * يولّد بيانات فيها 1–3 مخالفات عمداً (قواعد هجينة: عمر/مؤهل، أجر مرتفع، ساعات أسبوعية عالية).
 */
function generateRandomData() {
  const gender = pick(GENDER_OPTIONS)
  const cy = new Date().getFullYear()

  const kinds = ['age_edu', 'salary', 'hours'] as const
  const nViolations = 1 + Math.floor(Math.random() * 3)
  const shuffled = [...kinds].sort(() => Math.random() - 0.5)
  const active = new Set(shuffled.slice(0, nViolations))

  let age = 24 + Math.floor(Math.random() * 28)
  let q_301 = pick(EDUCATION_OPTIONS)
  let q_602_val = 4000 + Math.floor(Math.random() * 18000)
  let weekly_hours_usual = 32 + Math.floor(Math.random() * 14)
  let weekly_hours_actual = weekly_hours_usual + Math.floor(Math.random() * 8)

  if (active.has('age_edu')) {
    age = 15 + Math.floor(Math.random() * 5)
    q_301 = pick(BACHELOR_PLUS)
  }
  if (active.has('salary')) {
    q_602_val = 50000 + Math.floor(Math.random() * 120000)
  }
  if (active.has('hours')) {
    weekly_hours_usual = 85 + Math.floor(Math.random() * 20)
    weekly_hours_actual = weekly_hours_usual + Math.floor(Math.random() * 12)
  }

  form.value = {
    f_m_id: `DEMO-${1000 + Math.floor(Math.random() * 9000)}`,
    age,
    gender,
    nationality: 'سعودي / سعودية',
    q_301,
    marage_status: pick(MARITAL_OPTIONS),
    family_relation: pick(FAMILY_RELATION_OPTIONS),
    q_537_e_job: pick(RANDOM_JOBS),
    d_ystartwk: cy - Math.floor(Math.random() * 22) - 1,
    q_602_val,
    q_534: pick(SECTOR_OPTIONS),
    economic_activity_text: pick(['تجارة تجزئة', 'خدمات تقنية', 'مقاولات بناء', 'صحة خاصة']),
    weekly_hours_usual,
    weekly_hours_actual,
    ilo_employment_status: pick(ILO_STATUS_OPTIONS),
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
  }, 420)
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
        حقول بأسماء الأعمدة كما في <strong>MetaData_LFS_Training_Dataset</strong>؛ يُحوَّل الإدخال لصيغة التحقق.
        بعد حقلين على الأقل (غير المعرّف)، تُطبَّق قواعد الأعمال تلقائياً أثناء الكتابة — تظهر ملاحظات التعارض تحت
        الحقل (مثل العمر والمؤهل) دون الضغط على «تحقق نهائي».
      </p>

      <div v-if="apiError" class="banner banner-error">
        <strong>⚠ تعذّر الاتصال بالـ API</strong> — تأكد أن خادم FastAPI يعمل على
        <code>http://127.0.0.1:8000</code> (الواجهة في التطوير تمرّر <code>/api</code> عبر Vite).<br />
        من جذر المشروع: <code>./run.sh</code> أو: <code>cd backend &amp;&amp; uvicorn main:app --reload --host 127.0.0.1 --port 8000</code>
        — إن كان المنفذ 8000 مستخدماً أوقف العملية القديمة أولاً (<code>lsof -i :8000</code>).
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
            البيانات الشخصية الديموغرافية
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="age">{{ labelFor('age', 'العمر') }} <span class="req">*</span></label>
              <input id="age" v-model.number="form.age" type="number" min="15" max="100" placeholder="مثال: 35" />
              <div
                v-for="(err, ei) in inlineErrorsFor('age')"
                :key="'age-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="gender">{{ labelFor('gender', 'الجنس') }} <span class="req">*</span></label>
              <select id="gender" v-model="form.gender">
                <option value="">— اختر —</option>
                <option v-for="g in GENDER_OPTIONS" :key="g" :value="g">{{ g }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsFor('gender')"
                :key="'g-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field field-full">
              <label for="nationality">{{ labelFor('nationality', 'الجنسية') }} <span class="req">*</span></label>
              <input id="nationality" v-model="form.nationality" type="text" placeholder="مثال: سعودي" />
              <div
                v-for="(err, ei) in inlineErrorsFor('nationality')"
                :key="'nat-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="marage_status">{{ labelFor('marage_status', 'الحالة الاجتماعية') }}</label>
              <select id="marage_status" v-model="form.marage_status">
                <option value="">— اختر —</option>
                <option v-for="m in MARITAL_OPTIONS" :key="m" :value="m">{{ m }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsFor('marage_status')"
                :key="'mar-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="family_relation">صلة القرابة برئيس الأسرة</label>
              <select id="family_relation" v-model="form.family_relation">
                <option value="">— اختر —</option>
                <option v-for="fr in FAMILY_RELATION_OPTIONS" :key="fr" :value="fr">{{ fr }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsFor('family_relation')"
                :key="'fr-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="children_count">عدد الأبناء</label>
              <input
                id="children_count"
                v-model.number="form.children_count"
                type="number"
                min="0"
                max="20"
                placeholder="اختياري"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('children_count')"
                :key="'ch-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
          </div>
        </section>

        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">03</span>
            البيانات التعليمية
          </h2>
          <div class="fields-grid">
            <div class="field field-full">
              <label for="q_301">{{ labelFor('q_301', 'أعلى مؤهل تعليمي') }} <span class="req">*</span></label>
              <select id="q_301" v-model="form.q_301">
                <option value="">— اختر —</option>
                <option v-for="e in EDUCATION_OPTIONS" :key="e" :value="e">{{ e }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsFor('q_301')"
                :key="'q301-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
          </div>
        </section>

        <section class="form-section">
          <h2 class="form-section-title">
            <span class="sec-num">04</span>
            البيانات العملية والاقتصادية
          </h2>
          <div class="fields-grid">
            <div class="field">
              <label for="q_534">{{ labelFor('q_534', 'نوع القطاع المؤسسي') }}</label>
              <select id="q_534" v-model="form.q_534">
                <option value="">— اختر —</option>
                <option v-for="s in SECTOR_OPTIONS" :key="s" :value="s">{{ s }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsFor('q_534')"
                :key="'534-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field field-full">
              <label for="economic_activity_text">عنوان النشاط الاقتصادي</label>
              <input
                id="economic_activity_text"
                v-model="form.economic_activity_text"
                type="text"
                placeholder="نص حر — يُرسَل للتحقق الهجين"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('economic_activity_text')"
                :key="'eat-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field field-full">
              <label for="q_537_e_job">{{ labelFor('q_537_e_job', 'المسمى الوظيفي أو المهنة') }} <span class="req">*</span></label>
              <input
                id="q_537_e_job"
                v-model="form.q_537_e_job"
                type="text"
                placeholder="نص حر كما في الاستمارة"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('q_537_e_job')"
                :key="'job-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="q_602_val">الأجر الشهري (ريال)</label>
              <input
                id="q_602_val"
                v-model.number="form.q_602_val"
                type="number"
                min="0"
                placeholder="مثال: 8000"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('q_602_val')"
                :key="'602-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="weekly_hours_usual">ساعات العمل الاعتيادية الأسبوعية</label>
              <input
                id="weekly_hours_usual"
                v-model.number="form.weekly_hours_usual"
                type="number"
                min="0"
                max="168"
                placeholder="مثال: 40"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('weekly_hours_usual')"
                :key="'whu-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="weekly_hours_actual">ساعات العمل الفعلية الأسبوعية</label>
              <input
                id="weekly_hours_actual"
                v-model.number="form.weekly_hours_actual"
                type="number"
                min="0"
                max="168"
                placeholder="مثال: 42"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('weekly_hours_actual')"
                :key="'wha-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="ilo_employment_status">الحالة الوظيفية (ILO)</label>
              <select id="ilo_employment_status" v-model="form.ilo_employment_status">
                <option value="">— اختر —</option>
                <option v-for="ilo in ILO_STATUS_OPTIONS" :key="ilo" :value="ilo">{{ ilo }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsFor('ilo_employment_status')"
                :key="'ilo-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
            <div class="field">
              <label for="d_ystartwk">{{ labelFor('d_ystartwk', 'سنة بداية العمل') }}</label>
              <input
                id="d_ystartwk"
                v-model.number="form.d_ystartwk"
                type="number"
                :min="1970"
                :max="currentYear"
                placeholder="لتقدير سنوات الخبرة"
              />
              <div
                v-for="(err, ei) in inlineErrorsFor('d_ystartwk')"
                :key="'ystart-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
          </div>
        </section>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="btn-spinner"></span>
            <span>{{ isSubmitting ? 'جارٍ التحقق…' : 'تحقق نهائي من الاستمارة' }}</span>
          </button>
          <button type="button" class="btn btn-ghost" @click="generateRandomData">🎲 توليد بيانات مخالفة للقواعد</button>
          <button type="button" class="btn btn-ghost" @click="resetForm">إعادة تعيين</button>
        </div>

        <Transition name="fade">
          <div v-if="showSuccess" class="toast toast-success">✓ البيانات مقبولة — درجة الثقة مرتفعة</div>
        </Transition>
      </form>

      <div class="panel-col">
        <SurveyLiveSidebar :result="validationResult" :is-loading="isValidating" :mode="mode" />
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

.field-inline-msg {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  padding: 0.4rem 0.55rem;
  border-radius: 0.35rem;
  border: 1px solid transparent;
}
.field-inline-high {
  color: #991b1b;
  background: rgba(239, 68, 68, 0.09);
  border-color: rgba(239, 68, 68, 0.25);
}
.field-inline-medium {
  color: #92400e;
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.28);
}
.field-inline-low {
  color: #475569;
  background: rgba(100, 116, 139, 0.1);
  border-color: rgba(100, 116, 139, 0.22);
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

</style>
