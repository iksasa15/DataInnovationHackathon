/**
 * بعد قراءة Excel/CSV: القيم الحرفية «NULL» أو الفارغة تُعرض كحقل فاضٍ في الجدول والتحليل.
 */
export function normalizeCellValue(value: unknown): unknown {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') {
    const t = value.trim()
    if (t === '' || t.toUpperCase() === 'NULL') return ''
    return value
  }
  return value
}

export function normalizeRowsNullLike<T extends Record<string, unknown>>(rawRows: T[]): T[] {
  return rawRows.map((row) => {
    const out = {} as Record<string, unknown>
    for (const [k, v] of Object.entries(row)) {
      out[k] = normalizeCellValue(v)
    }
    return out as T
  })
}
