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
