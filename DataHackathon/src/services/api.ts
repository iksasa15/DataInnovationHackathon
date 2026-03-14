const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'

export interface FormData {
  name?: string | null
  age?: number | null
  gender?: string | null
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
}

export async function checkGeminiStatus(): Promise<GeminiStatus> {
  const response = await fetch(`${API_BASE}/api/gemini-status`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
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
  provider?: 'gemini' | 'local'
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
  mode?: "fast" | "smart"
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
