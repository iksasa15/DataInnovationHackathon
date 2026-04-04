<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import SurveyLiveSidebar from '../components/SurveyLiveSidebar.vue'
import { validateForm, checkHealth } from '../services/api'
import type { FormData, HealthStatus, ValidationError, ValidationResult } from '../services/api'
import { loadLfsMetadataMap } from '../utils/lfsMetadata'
import { resolveLfsTableColumnHeader } from '../utils/lfsTableColumnHeader'
import { LOGO_AIN_SRC } from '../constants/branding'

/**
 * حقول بأسماء أعمدة LFS كما في `MetaData_LFS_Training_Dataset.xlsx` وملفات Excel/CSV للمسح.
 * تُحوَّل داخلياً إلى `FormData` لمسار `/api/validate`.
 */
interface LfsLiveSurveyFields {
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

/** قواعد فقط | نموذج لغوي فقط | الاثنان — مطابق لـ ExcelView */
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
      return 'نموذج لغوي (حسب المزوّد في الخادم) + قواعد الأعمال.'
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

/** أعلى عتبة مؤهل لكل قاعدة عمر↔مؤهل (2011 ثانوي+ … 2016 دكتوراه) */
function effectiveRuleTier(e: ValidationError): number | null {
  if (e.rule_code === 'BR_4008' || e.rule_id === 2013) return 4
  switch (e.rule_id) {
    case 2011:
      return 2
    case 2012:
      return 3
    case 2015:
      return 5
    case 2016:
      return 6
    default:
      return null
  }
}

function isAgeEducationRuleError(e: ValidationError): boolean {
  const id = e.rule_id
  if (id === 2011 || id === 2012 || id === 2013 || id === 2015 || id === 2016) return true
  if (e.rule_code === 'BR_4008') return true
  const m = (e.message || '').toLowerCase()
  return (
    (m.includes('عمر') &&
      (m.includes('مؤهل') ||
        m.includes('ثانوي') ||
        m.includes('دبلوم') ||
        m.includes('بكالور') ||
        m.includes('ماجستير') ||
        m.includes('دكتور'))) ||
    (m.includes('الحد الأدنى') && m.includes('مؤهل')) ||
    (m.includes('بكالوريوس فأعلى') && m.includes('عمر'))
  )
}

const EDUC_RANK_ORDER = ['ابتدائي', 'متوسط', 'ثانوي', 'دبلوم', 'بكالوريوس', 'ماجستير', 'دكتوراه'] as const

function userEducationRank(q301: string): number | null {
  const i = EDUC_RANK_ORDER.indexOf(q301.trim() as (typeof EDUC_RANK_ORDER)[number])
  return i >= 0 ? i : null
}

/**
 * عند تعدّد قواعد العمر↔المؤهل (مثلاً 15 سنة وبكالوريوس يُطلق 2011 و2012 و2013)،
 * نعرض رسالة واحدة: أشد قاعدة لا تتجاوز مستوى المؤهل المختار (مثلاً بكالوريوس → 2013 فقط لا 2015/2016).
 */
function pickSingleAgeEducationError(candidates: ValidationError[], q301: string): ValidationError | null {
  if (!candidates.length) return null
  const u = userEducationRank(q301)
  const withTier: { e: ValidationError; t: number }[] = []
  for (const e of candidates) {
    const t = effectiveRuleTier(e)
    if (t != null) withTier.push({ e, t })
  }
  if (withTier.length && u != null) {
    const relevant = withTier.filter((x) => x.t <= u)
    if (relevant.length) {
      const maxT = Math.max(...relevant.map((x) => x.t))
      const best = relevant.filter((x) => x.t === maxT)
      return best[0]!.e
    }
  }
  if (withTier.length) {
    const maxT = Math.max(...withTier.map((x) => x.t))
    const best = withTier.filter((x) => x.t === maxT)
    return best[0]?.e ?? candidates[0]!
  }
  const q = q301.trim()
  if (q) {
    const keywords = [q]
    if (q === 'دكتوراه') keywords.push('دكتور', 'PhD', 'doctorate')
    const found = candidates.find((e) => {
      const msg = e.message || ''
      return keywords.some((k) => k.length > 1 && msg.includes(k))
    })
    if (found) return found
  }
  const sevOrder: Record<string, number> = { high: 0, medium: 1, low: 2 }
  return [...candidates].sort((a, b) => {
    const sa = sevOrder[String(a.severity || 'medium')] ?? 1
    const sb = sevOrder[String(b.severity || 'medium')] ?? 1
    return sa - sb
  })[0]!
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

const surveyDisplayErrors = computed(() => {
  const vr = validationResult.value
  const raw = vr?.errors ?? []
  const ageEdu = raw.filter(
    (e) =>
      isAgeEducationRuleError(e) &&
      fieldKeysForError(e).some((k) => k === 'age' || k === 'q_301'),
  )
  const rest = raw.filter((e) => !ageEdu.includes(e))
  const picked = pickSingleAgeEducationError(ageEdu, form.value.q_301)
  return picked ? [...rest, picked] : rest
})

const validationDisplayResult = computed(() => {
  const r = validationResult.value
  if (!r) return null
  return { ...r, errors: surveyDisplayErrors.value }
})

function inlineErrorsForFormField(fieldKey: string): ValidationError[] {
  const list = surveyDisplayErrors.value.filter((e) => fieldKeysForError(e).includes(fieldKey))
  /* رسالة العمر↔المؤهل الموحّدة تظهر تحت «العمر» فقط لتجنب التكرار */
  if (fieldKey === 'q_301') return list.filter((e) => !isAgeEducationRuleError(e))
  return list
}

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
    <header class="page-hero">
      <div class="page-kicker-row">
        <span class="page-kicker-logo-chip" aria-hidden="true">
          <img :src="LOGO_AIN_SRC" alt="" width="28" height="28" decoding="async" />
        </span>
        <span class="page-kicker">منصة عين — الحارس الدلالي</span>
      </div>
      <h1 class="page-title">استمارة LFS (الحارس الدلالي)</h1>
      <p class="page-desc">
        أسماء الحقول مطابقة لـ <strong>MetaData_LFS_Training_Dataset</strong>؛ تُطبَّق قواعد الأعمال تلقائياً أثناء
        الإدخال بعد حقلين على الأقل. تظهر التنبيهات تحت الحقول المعنية وفي لوحة «تجاوزات القواعد المؤكدة».
      </p>

      <div v-if="apiError" class="banner banner-error">
        <strong>تعذّر الاتصال بالـ API</strong> — تأكد أن خادم FastAPI يعمل على
        <code>http://127.0.0.1:8000</code> (الواجهة تمرّر <code>/api</code> عبر Vite). من الجذر:
        <code>./run.sh</code>
      </div>
      <div v-else-if="health && health.mode === 'demo'" class="banner banner-warning">
        وضع تجريبي — أضف مفتاح API في <code>backend/.env</code> لتفعيل النموذج اللغوي الكامل.
      </div>
      <div v-else-if="health && health.mode === 'live'" class="banner banner-success">
        <span class="banner-success-icon" aria-hidden="true">✓</span>
        متصل — يعمل بنموذج لغوي مباشر
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
            نموذج لغوي
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
    </header>

    <form id="survey-live-form" class="survey-form" @submit.prevent="handleSubmit" novalidate>
        <section class="form-section">
          <div class="form-section-head">
            <span class="sec-num">01</span>
            <h2 class="form-section-title">البيانات الشخصية الديموغرافية</h2>
          </div>
          <div class="form-section-body">
          <div class="fields-grid">
            <div class="field">
              <label for="age">{{ labelFor('age', 'العمر') }} <span class="req">*</span></label>
              <input id="age" v-model.number="form.age" type="number" min="15" max="100" placeholder="مثال: 35" />
              <div
                v-for="(err, ei) in inlineErrorsForFormField('age')"
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
                v-for="(err, ei) in inlineErrorsForFormField('gender')"
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
                v-for="(err, ei) in inlineErrorsForFormField('nationality')"
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
                v-for="(err, ei) in inlineErrorsForFormField('marage_status')"
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
                v-for="(err, ei) in inlineErrorsForFormField('family_relation')"
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
                v-for="(err, ei) in inlineErrorsForFormField('children_count')"
                :key="'ch-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
          </div>
          </div>
        </section>

        <section class="form-section">
          <div class="form-section-head">
            <span class="sec-num">02</span>
            <h2 class="form-section-title">البيانات التعليمية</h2>
          </div>
          <div class="form-section-body">
          <div class="fields-grid">
            <div class="field field-full">
              <label for="q_301">{{ labelFor('q_301', 'أعلى مؤهل تعليمي') }} <span class="req">*</span></label>
              <select id="q_301" v-model="form.q_301">
                <option value="">— اختر —</option>
                <option v-for="e in EDUCATION_OPTIONS" :key="e" :value="e">{{ e }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsForFormField('q_301')"
                :key="'q301-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
            </div>
          </div>
          </div>
        </section>

        <section class="form-section">
          <div class="form-section-head">
            <span class="sec-num">03</span>
            <h2 class="form-section-title">البيانات العملية والاقتصادية</h2>
          </div>
          <div class="form-section-body">
          <div class="fields-grid">
            <div class="field">
              <label for="q_534">{{ labelFor('q_534', 'نوع القطاع المؤسسي') }}</label>
              <select id="q_534" v-model="form.q_534">
                <option value="">— اختر —</option>
                <option v-for="s in SECTOR_OPTIONS" :key="s" :value="s">{{ s }}</option>
              </select>
              <div
                v-for="(err, ei) in inlineErrorsForFormField('q_534')"
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
                v-for="(err, ei) in inlineErrorsForFormField('economic_activity_text')"
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
                v-for="(err, ei) in inlineErrorsForFormField('q_537_e_job')"
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
                v-for="(err, ei) in inlineErrorsForFormField('q_602_val')"
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
                v-for="(err, ei) in inlineErrorsForFormField('weekly_hours_usual')"
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
                v-for="(err, ei) in inlineErrorsForFormField('weekly_hours_actual')"
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
                v-for="(err, ei) in inlineErrorsForFormField('ilo_employment_status')"
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
                v-for="(err, ei) in inlineErrorsForFormField('d_ystartwk')"
                :key="'ystart-e-' + ei + err.message.slice(0, 24)"
                class="field-inline-msg"
                :class="'field-inline-' + (err.severity || 'medium')"
                role="status"
              >
                {{ err.message }}
              </div>
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

        <div class="panel-col">
          <SurveyLiveSidebar :result="validationDisplayResult" :is-loading="isValidating" :mode="mode" />
        </div>
      </form>
  </div>
</template>

<style scoped>
/* هوية الحارس الدلالي — مطابقة مرجع الواجهة (بطاقات بيضاء، بنفسجي عميق، سطح رمادي فاتح) */
.survey-page {
  --sv-purple: #4137a8;
  --sv-purple-mid: #5247b8;
  --sv-purple-deep: #2d2669;
  --sv-purple-soft: #ebe8f7;
  --sv-surface: #f1f5f9;
  --sv-card: #ffffff;
  --sv-warn-bg: #fff8e6;
  --sv-warn-border: #ffb74d;
  --sv-warn-text: #bf360c;
  --sv-err-bg: #ffebee;
  --sv-err-border: #e57373;
  --sv-err-text: #b71c1c;

  max-width: 1200px;
  margin: 0 auto;
  padding: 1.25rem 1rem 4rem;
  font-family: var(--font-app);
  background: var(--sv-surface);
  border-radius: 0;
}

@media (min-width: 900px) {
  .survey-page {
    padding: 1.5rem 1.25rem 5.5rem;
  }
}

.page-hero {
  position: relative;
  background: var(--sv-card);
  border: 1px solid #e8e8ef;
  border-radius: 1rem;
  padding: 1.35rem 1.35rem 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.page-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--ga-green), var(--ga-cyan));
  border-radius: 1rem 1rem 0 0;
}

.page-kicker-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.65rem;
}

.page-kicker-logo-chip {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.45rem;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  padding: 0.15rem;
  box-sizing: border-box;
}

.page-kicker-logo-chip img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.page-kicker {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--sv-purple);
  background: var(--sv-purple-soft);
}

.page-title {
  font-size: clamp(1.35rem, 2.5vw, 1.75rem);
  font-weight: 800;
  color: var(--sv-purple-deep);
  margin: 0 0 0.55rem;
  line-height: 1.35;
}

.page-desc {
  margin: 0 0 1rem;
  color: #475569;
  font-size: 0.92rem;
  line-height: 1.7;
  max-width: 52rem;
}

.survey-engine {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e8e8ef;
}
.engine-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--sv-purple);
  margin-bottom: 0.5rem;
  opacity: 0.95;
}
.engine-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}
.engine-btn {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  font-family: inherit;
  font-weight: 600;
  border: 1.5px solid #d8d4e8;
  border-radius: 0.55rem;
  background: #faf9fc;
  color: #4338ca;
  cursor: pointer;
  transition:
    background 0.15s,
    border-color 0.15s,
    color 0.15s,
    box-shadow 0.15s;
}
.engine-btn:hover:not(:disabled) {
  background: #fff;
  border-color: var(--sv-purple-mid);
}
.engine-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.engine-btn-active {
  background: linear-gradient(180deg, var(--sv-purple-deep) 0%, var(--sv-purple) 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 4px 16px rgba(45, 38, 117, 0.4);
}
.engine-hint {
  margin: 0.65rem 0 0;
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.5;
}

.hint {
  font-size: 0.72rem;
  font-weight: 500;
  color: #94a3b8;
}

.banner {
  margin-top: 0.65rem;
  padding: 0.7rem 1rem;
  border-radius: 0.65rem;
  font-size: 0.86rem;
  line-height: 1.55;
}
.banner code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.12rem 0.4rem;
  border-radius: 0.3rem;
  font-size: 0.8rem;
}
.banner-error {
  background: var(--sv-err-bg);
  color: #b71c1c;
  border: 1px solid var(--sv-err-border);
}
.banner-warning {
  background: var(--sv-warn-bg);
  color: #e65100;
  border: 1px solid var(--sv-warn-border);
}
.banner-success {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
  background: #e8f5e9;
  color: #1b5e20;
  border: 1px solid #c8e6c9;
  font-weight: 700;
  border-radius: 0.65rem;
}
.banner-success-icon {
  display: inline-flex;
  width: 1.35rem;
  height: 1.35rem;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #c8e6c9;
  font-size: 0.75rem;
}

.survey-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-section {
  background: var(--sv-card);
  border: 1px solid #e8e8ef;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 4px 22px rgba(15, 23, 42, 0.06);
}

.form-section-head {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 1rem 1.2rem;
  background: #fff;
  border-bottom: 1px solid #eef0f4;
}

.form-section-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  flex: 1;
  line-height: 1.4;
  color: var(--sv-purple-deep);
}

.sec-num {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  padding: 0;
  background: linear-gradient(145deg, var(--sv-purple-deep) 0%, var(--sv-purple) 55%, var(--sv-purple-mid) 100%);
  color: #fff;
  border: none;
  box-shadow: 0 4px 14px rgba(40, 33, 87, 0.38);
}

.form-section-body {
  padding: 1.35rem 1.2rem 1.4rem;
  background: #fff;
}

.fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem 1.1rem;
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
  gap: 0.42rem;
}
.field label {
  font-size: 0.84rem;
  font-weight: 600;
  color: #334155;
}
.req {
  color: #dc2626;
}
.field input,
.field select {
  padding: 0.65rem 0.9rem;
  border: 1px solid #d8dee6;
  border-radius: 0.5rem;
  background: #fff;
  color: #0f172a;
  font-size: 0.9rem;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  width: 100%;
  font-family: inherit;
}
.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--sv-purple-mid);
  box-shadow: 0 0 0 3px rgba(65, 55, 168, 0.12);
  background: #fff;
}

.field-inline-msg {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.55;
  padding: 0.5rem 0.7rem;
  border-radius: 0.5rem;
  border: 1px solid transparent;
}
.field-inline-high {
  color: var(--sv-err-text);
  background: var(--sv-err-bg);
  border-color: var(--sv-err-border);
  font-weight: 600;
}
.field-inline-medium {
  color: var(--sv-warn-text);
  background: var(--sv-warn-bg);
  border-color: var(--sv-warn-border);
  font-weight: 600;
}
.field-inline-low {
  color: #475569;
  background: #f8fafc;
  border-color: #e2e8f0;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
  justify-content: flex-start;
  padding: 1.15rem 1.2rem;
  margin-top: 0.15rem;
  background: var(--sv-card);
  border: 1px solid #e8e8ef;
  border-radius: 1rem;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.72rem 1.35rem;
  font-size: 0.9rem;
  font-weight: 700;
  border-radius: 0.55rem;
  cursor: pointer;
  border: 2px solid transparent;
  transition:
    transform 0.15s,
    box-shadow 0.15s,
    background 0.15s;
  font-family: inherit;
}
.btn-primary {
  background: linear-gradient(180deg, var(--sv-purple-deep) 0%, var(--sv-purple) 100%);
  color: #fff;
  box-shadow: 0 4px 18px rgba(45, 38, 117, 0.38);
  border: none;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.05);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.btn-ghost {
  background: #fff;
  color: var(--ga-cyan);
  border: 2px solid var(--ga-cyan);
}
.btn-ghost:hover {
  background: var(--ga-cyan-soft);
  border-color: var(--ga-cyan);
  color: #006b8a;
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
  border-radius: 0.55rem;
  font-size: 0.86rem;
  font-weight: 600;
}
.toast-success {
  background: #e8f5e9;
  color: #1b5e20;
  border: 1px solid #a5d6a7;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.panel-col {
  min-width: 0;
  margin-top: 1.15rem;
}
</style>
