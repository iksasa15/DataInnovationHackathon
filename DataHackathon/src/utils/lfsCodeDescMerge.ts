/**
 * أزواج LFS (رمز + وصف) كما في بيانات التدريب: العمود الأساسي قد يحمل رقماً
 * والعمود *_desc يحمل النص المرجعي (مثل "1 - ذكر"). عند استيراد الجدول ندمج
 * الوصف في الحقل الأساسي ونحذف عمود *_desc حتى يظهر للمستخدم النص وليس الرمز فقط.
 */

function nonempty(v: unknown): boolean {
  if (v === null || v === undefined) return false
  if (typeof v === 'number' && v !== v) return false
  const t = String(v).trim()
  return t !== '' && t.toLowerCase() !== 'nan'
}

/** يزيل بادئة الرمز من تسميات LFS الشائعة: "1 - ذكر" → "ذكر" */
export function normalizeLfsDescLabel(value: unknown): string {
  const s = value == null ? '' : String(value).trim()
  if (!s) return ''
  const m = s.match(/^\d+\s*[-–]\s*(.+)$/u)
  if (m?.[1]) return m[1].trim()
  return s
}

/**
 * لكل مفتاح ينتهي بـ `_desc` وله قاعدة موجودة في الصف: يُستبدل قيمة القاعدة
 * بالنص المعروض من الوصف (مع تطبيع التسمية)، ثم يُحذف عمود الوصف.
 */
export function mergeLfsDescIntoCodeRows(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  if (!rows.length) return rows
  return rows.map((row) => {
    const next: Record<string, unknown> = { ...row }
    const keys = Object.keys(next)
    for (const k of keys) {
      if (!k.endsWith('_desc')) continue
      const base = k.slice(0, -5)
      if (!base || !(base in next)) continue
      const descRaw = next[k]
      const codeRaw = next[base]
      if (nonempty(descRaw)) {
        next[base] = normalizeLfsDescLabel(descRaw)
      } else if (nonempty(codeRaw)) {
        next[base] = typeof codeRaw === 'number' ? codeRaw : String(codeRaw).trim()
      }
      delete next[k]
    }
    return next
  })
}
