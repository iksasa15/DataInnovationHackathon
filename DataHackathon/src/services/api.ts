const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'

export function getApiBaseUrl(): string {
  return API_BASE
}

export interface FormData {
  /** يُعرَض كـ `f_m_id` في استمارة LFS */
  name?: string | null
  age?: number | null
  gender?: string | null
  nationality?: string | null
  education?: string | null
  job_title?: string | null
  years_experience?: number | null
  monthly_salary?: number | null
  sector?: string | null
  marital_status?: string | null
  children_count?: number | null
}

export interface ValidationError {
  field: string
  message: string
  severity: 'low' | 'medium' | 'high'
  /** رقم القاعدة من LFS_Business_Rules.xlsx عند التحقق البرمجي */
  rule_id?: number
  message_en?: string
  rule_type?: string
}

export interface ValidationResult {
  confidence_score: number
  status: 'valid' | 'warning' | 'error'
  errors: ValidationError[]
  suggestions: string[]
  summary: string
}

export interface HealthStatus {
  status: string
  llm_configured: boolean
  provider: string
  mode: 'live' | 'demo'
  /** مفعّل من متغير البيئة على الخادم — لا حاجة لمفتاح من المستخدم */
  gemini_from_env?: boolean
  /** تم ضبط Supabase URL + service role — المفتاح يُقرأ من جدول app_settings */
  supabase_settings_enabled?: boolean
  /** يوجد مفتاح غير فارغ في Supabase */
  gemini_from_supabase?: boolean
  /** هل يُسمح بإرسال المفتاح من المتصفح */
  client_can_set_gemini_key?: boolean
}

export async function validateForm(data: FormData): Promise<ValidationResult> {
  const response = await fetch(`${API_BASE}/api/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/api/health`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export interface GeminiStatus {
  ok: boolean
  message: string
  cached?: boolean
}

export async function checkGeminiStatus(): Promise<GeminiStatus> {
  const response = await fetch(`${API_BASE}/api/gemini-status`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

/** نتيجة خطوة واحدة من تشخيص الخادم */
export interface DiagnosticResult {
  id: string
  label: string
  ok: boolean
  message: string
  durationMs?: number
}

/**
 * يجري بالتتابع: صحة الخادم، OpenAPI، Gemini، Supabase.
 * يتوقف عن طلبات إضافية إن فشل الاتصال الأساسي بـ /api/health.
 */
export async function runFullDiagnostics(): Promise<DiagnosticResult[]> {
  const results: DiagnosticResult[] = []

  const tHealth = performance.now()
  try {
    const h = await checkHealth()
    results.push({
      id: 'health',
      label: 'صحة الخادم (/api/health)',
      ok: h.status === 'ok',
      message: `الوضع: ${h.mode} · المزوّد: ${h.provider} · LLM جاهز: ${h.llm_configured ? 'نعم' : 'لا'} · Gemini من البيئة: ${h.gemini_from_env ? 'نعم' : 'لا'} · Supabase مفعّل: ${h.supabase_settings_enabled ? 'نعم' : 'لا'} · مفتاح من Supabase: ${h.gemini_from_supabase ? 'نعم' : 'لا'}`,
      durationMs: Math.round(performance.now() - tHealth),
    })
  } catch {
    results.push({
      id: 'health',
      label: 'صحة الخادم (/api/health)',
      ok: false,
      message: `تعذّر الاتصال بـ ${API_BASE}. تأكد من تشغيل الـ backend أو ضبط VITE_API_URL عند البناء.`,
      durationMs: Math.round(performance.now() - tHealth),
    })
    results.push({
      id: 'openapi',
      label: 'توثيق API (openapi.json)',
      ok: false,
      message: 'تُخطى — لا يوجد اتصال بالخادم.',
    })
    results.push({
      id: 'gemini',
      label: 'اتصال Gemini',
      ok: false,
      message: 'تُخطى.',
    })
    results.push({
      id: 'supabase',
      label: 'قاعدة Supabase',
      ok: false,
      message: 'تُخطى.',
    })
    return results
  }

  const tOpen = performance.now()
  try {
    const r = await fetch(`${API_BASE}/openapi.json`)
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const j = (await r.json()) as { paths?: Record<string, unknown> }
    const n = j.paths ? Object.keys(j.paths).length : 0
    results.push({
      id: 'openapi',
      label: 'توثيق API (openapi.json)',
      ok: true,
      message: `تم الجلب بنجاح — عدد المسارات في المخطط: ${n}`,
      durationMs: Math.round(performance.now() - tOpen),
    })
  } catch (e) {
    results.push({
      id: 'openapi',
      label: 'توثيق API (openapi.json)',
      ok: false,
      message: e instanceof Error ? e.message : 'فشل جلب المخطط',
      durationMs: Math.round(performance.now() - tOpen),
    })
  }

  const tGem = performance.now()
  try {
    const g = await checkGeminiStatus()
    results.push({
      id: 'gemini',
      label: 'اتصال Gemini (/api/gemini-status)',
      ok: g.ok,
      message: `${g.message}${g.cached ? ' · (نتيجة من الكاش)' : ''}`,
      durationMs: Math.round(performance.now() - tGem),
    })
  } catch (e) {
    results.push({
      id: 'gemini',
      label: 'اتصال Gemini (/api/gemini-status)',
      ok: false,
      message: e instanceof Error ? e.message : 'فشل الطلب',
      durationMs: Math.round(performance.now() - tGem),
    })
  }

  const tSb = performance.now()
  try {
    const s = await checkSupabaseStatus()
    results.push({
      id: 'supabase',
      label: 'قاعدة Supabase (/api/supabase-status)',
      ok: s.ok,
      message: `${s.message} · الجدول: ${s.table_ok ? 'موجود' : 'لا'} · صف المفتاح: ${s.gemini_row_filled ? 'مملوء' : 'فارغ/غير جاهز'}`,
      durationMs: Math.round(performance.now() - tSb),
    })
  } catch (e) {
    results.push({
      id: 'supabase',
      label: 'قاعدة Supabase (/api/supabase-status)',
      ok: false,
      message: e instanceof Error ? e.message : 'فشل الطلب',
      durationMs: Math.round(performance.now() - tSb),
    })
  }

  return results
}

export interface SupabaseStatusResult {
  ok: boolean
  message: string
  configured: boolean
  table_ok: boolean
  gemini_row_filled: boolean
}

export async function checkSupabaseStatus(): Promise<SupabaseStatusResult> {
  const response = await fetch(`${API_BASE}/api/supabase-status`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export async function setGeminiApiKey(apiKey: string): Promise<{ ok: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/gemini-api-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  })
  let data: { ok?: boolean; message?: string } = {}
  try {
    data = await response.json()
  } catch {
    /* ignore */
  }
  if (!response.ok) {
    return {
      ok: false,
      message: data.message || `فشل الطلب (${response.status})`,
    }
  }
  return { ok: data.ok ?? true, message: data.message || 'تم الحفظ' }
}

export interface BatchRecord extends FormData {
  row_index: number
}

export interface BatchStats {
  total: number
  errors: number
  warnings: number
  valid: number
  avg_confidence: number
}

export interface BatchResult {
  results: (ValidationResult & { row_index: number })[]
  stats: BatchStats
  provider?: 'gemini' | 'local' | 'rules'
  gemini_unavailable?: boolean
}

export async function validateBatch(records: BatchRecord[]): Promise<BatchResult> {
  const response = await fetch(`${API_BASE}/api/validate-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(records),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export interface DynamicBatchPayload {
  columns: string[]
  records: Record<string, any>[]
  mode?: 'fast' | 'smart'
  /** تسميات عربية اختيارية للأعمدة (تُدمج مع ملف الميتاداتا الافتراضي في الخادم) */
  column_labels?: Record<string, string>
  /** دمج backend/data/lfs_column_labels.json تلقائياً */
  embed_metadata?: boolean
  /** تقليص الأعمدة الطويلة (LFS) قبل الإرسال للنموذج */
  column_subset?: boolean
  max_columns?: number
  /** دمج قواعد الأعمال الصريحة مع مخرجات النموذج */
  apply_hybrid_rules?: boolean
  /** إذا false: لا يُستدعَ النموذج اللغوي — قواعد الأعمال فقط */
  use_llm?: boolean
}

export async function validateBatchDynamic(payload: DynamicBatchPayload): Promise<BatchResult> {
  const response = await fetch(`${API_BASE}/api/validate-batch-dynamic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}
