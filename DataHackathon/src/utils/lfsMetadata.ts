import * as XLSX from 'xlsx'

/**
 * إزالة عناصر الاستبيان النائبة [#token#] و #field# حتى لا تُعرض للمستخدم،
 * وإزالة جمل «الفترة المرجعية» التي تصبح فارغة بعد الحذف.
 */
export function sanitizeLfsQuestionForDisplay(text: string): string {
  let s = text
  s = s.replace(/\[\#[^\]]+\#\]/g, '')
  s = s.replace(/\#[a-zA-Z0-9_]+\#/g, '…')
  s = s.replace(
    /\s*ملاحظة(?:\s*للباحث)?\s*:\s*الفترة المرجعية هي\s+(?:الى|إلى)\s+الموافق للتاريخ الميلادي\s+(?:الى|إلى)\s*/gi,
    ' ',
  )
  s = s.replace(/\s*الفترة المرجعية هي\s+(?:الى|إلى)\s+الموافق للتاريخ الميلادي\s+(?:الى|إلى)\s*/gi, ' ')
  s = s.replace(/\(\s*\)/g, '')
  s = s.replace(/\[\s*\]/g, '')
  s = s.replace(/\s{2,}/g, ' ')
  s = s.replace(/\s*([\u060C،])\s*/g, '$1 ')
  s = s.trim()
  s = s.replace(/^،\s*/u, '')
  s = s.replace(/\s+،\s*$/u, '،')
  return s
}

/**
 * بناء فهرس tag → نص السؤال من ورقة الميتاداتا.
 * يتوافق مع `regenerate_lfs_column_labels.py`: العمود الأول = المعرف، الثاني = السؤال.
 */
export function buildLfsMetadataMapFromSheet(ws: XLSX.WorkSheet): Record<string, string> {
  const map: Record<string, string> = {}

  const asRows = XLSX.utils.sheet_to_json(ws, { defval: '' }) as Record<string, unknown>[]
  if (asRows.length) {
    const firstKeys = Object.keys(asRows[0] ?? {})
    const colKey =
      firstKeys.find((k) => k.trim().toLowerCase() === 'column_name') ?? firstKeys[0]
    const qKey = firstKeys.find((k) => k.trim().toLowerCase() === 'question') ?? firstKeys[1]
    if (colKey && qKey) {
      for (const r of asRows) {
        const key = r[colKey] != null ? String(r[colKey]).trim() : ''
        const q = r[qKey] != null ? String(r[qKey]).trim() : ''
        if (!key || !q) continue
        if (key.toLowerCase() === 'column_name') continue
        map[key] = q
      }
      if (Object.keys(map).length) return map
    }
  }

  const aoa = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' }) as unknown[][]
  for (let i = 1; i < aoa.length; i++) {
    const row = aoa[i]
    if (!Array.isArray(row)) continue
    const key = String(row[0] ?? '').trim()
    const q = String(row[1] ?? '').trim()
    if (!key || !q) continue
    if (key.toLowerCase() === 'column_name') continue
    map[key] = q
  }
  return map
}

/** تحميل `MetaData_LFS_Training_Dataset.xlsx` من أصول الموقع (مجلد `public`). */
export async function loadLfsMetadataMap(baseUrl: string): Promise<Record<string, string>> {
  try {
    const res = await fetch(`${baseUrl}MetaData_LFS_Training_Dataset.xlsx`)
    if (!res.ok) return {}
    const buf = await res.arrayBuffer()
    const wb = XLSX.read(new Uint8Array(buf), { type: 'array' })
    const name = wb.SheetNames[0]
    if (!name) return {}
    const ws = wb.Sheets[name]
    if (!ws) return {}
    return buildLfsMetadataMapFromSheet(ws)
  } catch {
    return {}
  }
}

export function columnQuestionLabel(
  tag: string,
  meta: Record<string, string>,
  sanitize: (s: string) => string = sanitizeLfsQuestionForDisplay,
): string {
  let raw: string | undefined = meta[tag]
  if (!raw) {
    const lower = tag.toLowerCase()
    for (const k of Object.keys(meta)) {
      if (k.toLowerCase() === lower) {
        raw = meta[k]
        break
      }
    }
  }
  if (raw) {
    const cleaned = sanitize(raw)
    return cleaned || tag
  }
  return tag
}
