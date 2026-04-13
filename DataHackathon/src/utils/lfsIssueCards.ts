import type { ValidationError } from '../services/api'
import {
  classifyValidationErrorKind,
  issueKindLabelAr,
  severityLabelAr,
  validationErrorMatchesKind,
  type IssueKindClass,
} from './lfsIssueKind'

export type SeverityFilterBtn = 'all' | 'high' | 'medium' | 'low'
export type IssueKindFilterBtn = 'all' | IssueKindClass

/** صف نتيجة تحقق — الحد الأدنى للحقول المطلوبة لبناء البطاقات */
export interface RowWithValidationLike {
  row_index: number
  validation: {
    confidence_score: number
    errors: ValidationError[]
  } | null
}

export interface FlatIssueCard {
  rowDisplay: number
  /** معرّف الحقل التقني لعناصر المفتاح */
  fieldKey: string
  severityKey: 'high' | 'medium' | 'low'
  severityLabel: string
  fieldLabel: string
  confidence: number | null
  kindLabel: string
  /** عنوان موجز مستخرج من الرسالة */
  title: string
  /** نص التفاصيل الكامل */
  body: string
}

/** يستخرج عنواناً قصيراً وبقية النص للعرض في البطاقة */
export function splitMessageForCard(message: string): { title: string; body: string } {
  const t = message.replace(/\r\n/g, '\n').trim()
  if (!t) return { title: '', body: '' }
  const lines = t
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
  if (lines.length >= 2) {
    return { title: lines[0]!, body: lines.slice(1).join('\n\n') }
  }
  const one = lines[0] || t
  const punct = one.search(/[.!?؟]\s/)
  if (punct >= 20 && punct <= 240) {
    return { title: one.slice(0, punct + 1).trim(), body: one.slice(punct + 1).trim() }
  }
  if (one.length > 100) {
    return { title: one.slice(0, 96).trim() + '…', body: one }
  }
  return { title: one, body: '' }
}

/**
 * قائمة مسطّحة من بطاقات التنبيهات المطابقة لفلتر الشدة ونوع التنبيه الحاليين.
 */
export function buildFilteredIssueCards(
  rows: RowWithValidationLike[],
  severityFilter: SeverityFilterBtn,
  kindFilter: IssueKindFilterBtn,
  columnLabel: (field: string) => string,
): FlatIssueCard[] {
  const out: FlatIssueCard[] = []
  for (const r of rows) {
    const v = r.validation
    if (!v?.errors?.length) continue
    const conf = typeof v.confidence_score === 'number' ? v.confidence_score : null
    for (const e of v.errors) {
      const sevRaw = String(e.severity ?? 'medium').toLowerCase()
      const sevNorm = sevRaw === 'high' ? 'high' : sevRaw === 'low' ? 'low' : 'medium'
      if (severityFilter !== 'all' && sevNorm !== severityFilter) continue
      if (kindFilter !== 'all' && !validationErrorMatchesKind(e, kindFilter)) continue

      const kind = classifyValidationErrorKind(e)
      const msg = String(e.message ?? '')
      const { title, body } = splitMessageForCard(msg)
      const titleUse = title || msg.slice(0, 72) + (msg.length > 72 ? '…' : '')
      const bodyUse = body.trim() ? body.trim() : msg

      out.push({
        rowDisplay: r.row_index + 1,
        fieldKey: String(e.field ?? ''),
        severityKey: sevNorm,
        severityLabel: severityLabelAr(sevNorm),
        fieldLabel: columnLabel(e.field),
        confidence: conf,
        kindLabel: issueKindLabelAr(kind),
        title: titleUse,
        body: bodyUse,
      })
    }
  }

  const severityOrder: Record<FlatIssueCard['severityKey'], number> = { high: 0, medium: 1, low: 2 }
  out.sort((a, b) => {
    const bySev = severityOrder[a.severityKey] - severityOrder[b.severityKey]
    if (bySev !== 0) return bySev
    return a.rowDisplay - b.rowDisplay
  })

  return out
}
