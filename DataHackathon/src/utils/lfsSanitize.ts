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
