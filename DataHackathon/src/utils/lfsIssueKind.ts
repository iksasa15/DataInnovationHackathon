import type { ValidationError } from '../services/api'

export type IssueKindClass = 'semantic' | 'logical' | 'input'

/**
 * تصنيف نوع التنبيه للفلترة: تناقض دلالي / تعارض منطقي / احتمال خطأ إدخال.
 * يعتمد على rule_type من LFS_Business_Rules ثم الرسالة ثم rule_id.
 */
export function classifyValidationErrorKind(e: ValidationError): IssueKindClass {
  const rt = `${e.rule_type ?? ''}`.toLowerCase()
  const msg = `${e.message ?? ''}`

  if (/semantic|meaning|دلالي|معنوي|contextual/i.test(rt)) return 'semantic'
  if (/logical|منطق|reasoning/i.test(rt)) return 'logical'
  if (/input|entry|إدخال|data\s*quality|typo|format/i.test(rt)) return 'input'

  if (/تناقض\s*دلالي|تناقض\s+دلالي|دلالي|معنوي|دلالة\s*مع|semantic/i.test(msg)) return 'semantic'
  if (/خطأ\s*إدخال|احتمال\s*خطأ\s*إدخال|إدخال|فاصلة|وحدات|تنسيق|typo|input\s*error/i.test(msg))
    return 'input'
  if (/تعارض\s*منطقي|منطق|تعارض|تناقض|logical|contradiction/i.test(msg)) return 'logical'

  if (e.rule_id != null) return 'logical'

  return 'semantic'
}

export function validationErrorMatchesKind(e: ValidationError, kind: IssueKindClass): boolean {
  return classifyValidationErrorKind(e) === kind
}

export function severityLabelAr(sev: string): string {
  const s = String(sev ?? 'medium').toLowerCase()
  if (s === 'high') return 'عالية'
  if (s === 'low') return 'منخفضة'
  return 'متوسطة'
}

export function issueKindLabelAr(kind: IssueKindClass): string {
  switch (kind) {
    case 'semantic':
      return 'تناقض دلالي'
    case 'logical':
      return 'تعارض منطقي'
    case 'input':
      return 'احتمال خطأ إدخال'
  }
}
