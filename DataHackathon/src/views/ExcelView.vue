<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import iconv from 'iconv-lite'
import { validateBatchDynamic } from '../services/api'
import type { BatchResult, ValidationError } from '../services/api'

interface ValidationResult {
  confidence_score: number
  status: 'valid' | 'warning' | 'error'
  errors: ValidationError[]
  suggestions: string[]
  summary: string
}

interface RowData {
  row_index: number
  originalData: Record<string, any>
  editableData: Record<string, any>
  validation: (ValidationResult & { row_index: number }) | null
}

const isDragging = ref(false)
const isProcessing = ref(false)
const fileName = ref('')
const columns = ref<string[]>([])
const rows = ref<RowData[]>([])
const batchResult = ref<BatchResult | null>(null)
/** رسالة عند فشل الطلب للخادم (بعد الرفع التلقائي أو اليدوي) */
const analysisError = ref<string | null>(null)
const filter = ref<'all' | 'error' | 'warning' | 'valid'>('all')
const detailsModalRow = ref<number | null>(null)

/** قواعد فقط | Gemini فقط | الاثنان معاً */
type AnalysisEngine = 'rules' | 'gemini' | 'both'
const analysisEngine = ref<AnalysisEngine>('both')

/** معرف العمود (tag) → نص السؤال من MetaData_LFS_Training_Dataset */
const lfsColumnQuestionByName = ref<Record<string, string>>({})

/**
 * إزالة عناصر الاستبيان النائبة [#token#] و #field# حتى لا تُعرض للمستخدم،
 * وإزالة جمل «الفترة المرجعية» التي تصبح فارغة بعد الحذف.
 */
function sanitizeLfsQuestionForDisplay(text: string): string {
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
 * يدعم أسماء رؤوس `Column_Name` / `Question` أو أي ترتيب عمودين إن تغيّر الملف.
 */
function buildLfsMetadataMapFromSheet(ws: XLSX.WorkSheet): Record<string, string> {
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

async function loadLfsColumnMetadata() {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}MetaData_LFS_Training_Dataset.xlsx`)
    if (!res.ok) return
    const buf = await res.arrayBuffer()
    const wb = XLSX.read(new Uint8Array(buf), { type: 'array' })
    const name = wb.SheetNames[0]
    if (!name) return
    const ws = wb.Sheets[name]
    if (!ws) return
    lfsColumnQuestionByName.value = buildLfsMetadataMapFromSheet(ws)
  } catch {
    /* ملف الميتاداتا اختياري */
  }
}

/** عنوان العرض في الجدول: نص السؤال من الميتاداتا إن وُجد (مع مطابقة غير حساسة لحالة الأحرف)، وإلا المعرّف كما في الملف */
function columnHeaderLabel(tag: string): string {
  const m = lfsColumnQuestionByName.value
  let raw: string | undefined = m[tag]
  if (!raw) {
    const lower = tag.toLowerCase()
    for (const k of Object.keys(m)) {
      if (k.toLowerCase() === lower) {
        raw = m[k]
        break
      }
    }
  }
  if (raw) {
    const cleaned = sanitizeLfsQuestionForDisplay(raw)
    return cleaned || tag
  }
  return tag
}

onMounted(() => {
  loadLfsColumnMetadata()
})

const filteredRows = computed(() => {
  if (filter.value === 'all') return rows.value
  return rows.value.filter((r) => r.validation?.status === filter.value)
})

const stats = computed(() => batchResult.value?.stats ?? null)

const analyzeButtonLabel = computed(() => {
  if (isProcessing.value) return 'جارٍ التحليل…'
  if (batchResult.value) return '🔄 إعادة التحليل'
  if (analysisEngine.value === 'rules') return '⚙️ تحليل بالقواعد'
  if (analysisEngine.value === 'gemini') return '🤖 تحليل بـ Gemini'
  return '🔍 تحليل (Gemini + قواعد)'
})

/** ملخص تنبيهات بأسباب (مثل تجربة التحليل بـ Gemini) — يظهر بعد كل تحليل ناجح */
const analysisNotice = computed(() => {
  if (!batchResult.value || isProcessing.value) return null
  const br = batchResult.value
  const st = br.stats
  if (!st) return null

  type Item = {
    field: string
    fieldLabel: string
    message: string
    severity?: string
    rule_id?: number
    message_en?: string
  }
  const items: Item[] = []
  const seen = new Set<string>()
  for (const r of br.results) {
    const errs = r.errors || []
    for (const e of errs) {
      const msg = typeof e.message === 'string' ? e.message : String(e.message ?? '')
      const key = `${e.field}|${msg}`
      if (seen.has(key)) continue
      seen.add(key)
      const ex = e as ValidationError & { rule_id?: number; message_en?: string }
      items.push({
        field: e.field,
        fieldLabel: columnHeaderLabel(e.field),
        message: msg,
        severity: e.severity,
        rule_id: ex.rule_id,
        message_en: ex.message_en,
      })
      if (items.length >= 18) break
    }
    if (items.length >= 18) break
  }

  const suggestions: string[] = []
  const sugSeen = new Set<string>()
  for (const r of br.results) {
    for (const s of r.suggestions || []) {
      const t = typeof s === 'string' ? s : String(s)
      if (!t.trim() || sugSeen.has(t)) continue
      sugSeen.add(t)
      suggestions.push(t)
      if (suggestions.length >= 6) break
    }
    if (suggestions.length >= 6) break
  }

  const allClear = st.errors === 0 && st.warnings === 0
  return {
    items,
    suggestions,
    totalErrors: st.errors,
    totalWarnings: st.warnings,
    allClear,
    hasRowLevelIssues: items.length > 0,
  }
})

/** خريطة تفاصيل كل صف (ملخص مشاكل + اقتراحات) لتجنب إعادة الحساب في القالب */
const rowDetailsMap = computed(() => {
  const m = new Map<number, ReturnType<typeof getRowDetails>>()
  rows.value.forEach((r) => m.set(r.row_index, getRowDetails(r)))
  return m
})

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) processFile(file)
}

function onFileInput(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) processFile(file)
}

function scoreArabicQuality(text: string): number {
  const arabicMatches = text.match(/[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/g)?.length ?? 0
  const mojibakeMatches = text.match(/[ØÙÃÂÃ¡Ã¢Ã£Ã¤Ã¥Ã¦Ã§Ã¨Ã©]/g)?.length ?? 0
  const replacementCount = (text.match(/\uFFFD/g) ?? []).length
  return arabicMatches - mojibakeMatches * 3 - replacementCount * 5
}

const LEGACY_ARABIC_ENCODINGS = ['win1256', 'iso-8859-6'] as const
const utf8Decoder = new TextDecoder('utf-8', { fatal: false })

function decodeCsvBuffer(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    return utf8Decoder.decode(bytes.subarray(3))
  }
  const utf8Decoded = utf8Decoder.decode(bytes)
  if (/[\u0600-\u06FF]/.test(utf8Decoded) && !/\uFFFD/.test(utf8Decoded)) return utf8Decoded
  let best = utf8Decoded
  let bestScore = scoreArabicQuality(utf8Decoded)
  for (const enc of LEGACY_ARABIC_ENCODINGS) {
    try {
      const decoded = iconv.decode(bytes as unknown as Buffer, enc)
      const score = scoreArabicQuality(decoded)
      if (score > bestScore) {
        best = decoded
        bestScore = score
      }
    } catch {
      /* unsupported encoding */
    }
  }
  return best
}

function parseWorkbook(data: ArrayBuffer, isCsv: boolean) {
  if (isCsv) {
    const decodedCsv = decodeCsvBuffer(data)
    return XLSX.read(decodedCsv, { type: 'string' })
  }
  return XLSX.read(new Uint8Array(data), { type: 'array' })
}

/** أعمدة الوصف المرافقة للرمز (*_desc) — للترميز التقني ولا تُعرض للمستخدم النهائي */
function isTechnicalDescColumn(key: string): boolean {
  return key.trim().toLowerCase().endsWith('_desc')
}

function stripTechnicalDescColumns(rawRows: Record<string, any>[]): {
  columns: string[]
  rows: Record<string, any>[]
} {
  if (!rawRows.length) return { columns: [], rows: [] }
  const allKeys = new Set<string>()
  for (const row of rawRows) {
    for (const k of Object.keys(row)) allKeys.add(k)
  }
  const keep = [...allKeys].filter((k) => !isTechnicalDescColumn(k))
  if (!keep.length) return { columns: [], rows: [] }

  const rows = rawRows.map((row) => {
    const next: Record<string, any> = {}
    for (const c of keep) {
      next[c] = row[c]
    }
    return next
  })
  return { columns: keep, rows }
}

function processFile(file: File) {
  fileName.value = file.name
  const isCsv = file.name.toLowerCase().endsWith('.csv')
  const reader = new FileReader()

  reader.onload = (e) => {
    const result = e.target?.result
    if (!result) return

    const wb = parseWorkbook(result as ArrayBuffer, isCsv)
    const firstSheetName = wb.SheetNames[0]
    if (!firstSheetName) return

    const ws = wb.Sheets[firstSheetName]
    if (!ws) return

    const rawRows: Record<string, any>[] = XLSX.utils.sheet_to_json(ws, { defval: '' })
    if (!rawRows.length || !rawRows[0]) return

    const { columns: visibleCols, rows: dataRows } = stripTechnicalDescColumns(rawRows)
    if (!visibleCols.length) return

    columns.value = visibleCols
    rows.value = dataRows.map((row, i) => ({
      row_index: i,
      originalData: row,
      editableData: { ...row },
      validation: null,
    }))

    batchResult.value = null
    analysisError.value = null
    filter.value = 'all'
  }

  reader.readAsArrayBuffer(file)
}

async function analyzeAll() {
  if (!rows.value.length || !columns.value.length) return
  isProcessing.value = true
  analysisError.value = null
  try {
    const engine = analysisEngine.value
    const useLlm = engine !== 'rules'
    const applyHybrid = engine !== 'gemini'

    const payload = {
      columns: columns.value,
      records: rows.value.map((r) => ({ row_index: r.row_index, ...(r.editableData ?? r.originalData) })),
      mode: 'smart' as const,
      use_llm: useLlm,
      apply_hybrid_rules: applyHybrid,
    }

    batchResult.value = await validateBatchDynamic(payload)

    const resultMap = new Map(batchResult.value.results.map((r) => [r.row_index, r]))
    rows.value = rows.value.map((r) => ({
      ...r,
      editableData: r.editableData ?? { ...r.originalData },
      validation: resultMap.get(r.row_index) ?? null,
    }))
  } catch (e) {
    batchResult.value = null
    analysisError.value =
      e instanceof Error ? e.message : 'تعذّر الاتصال بالخادم أو إكمال التحليل. تحقق من تشغيل الـ API.'
  } finally {
    isProcessing.value = false
  }
}

function resetFile() {
  fileName.value = ''
  columns.value = []
  rows.value = []
  batchResult.value = null
  analysisError.value = null
  filter.value = 'all'
}

function norm(value: string) {
  return value.trim().toLowerCase().replace(/[_\-\s]+/g, ' ')
}

function getFieldError(row: RowData, col: string): ValidationError | null {
  if (!row.validation) return null
  const target = norm(col)
  return (
    row.validation.errors.find((e) => norm(e.field) === target) ||
    row.validation.errors.find((e) => target.includes(norm(e.field)) || norm(e.field).includes(target)) ||
    null
  )
}

function getCellClass(row: RowData, col: string) {
  const err = getFieldError(row, col)
  if (!err) return ''
  if (err.severity === 'high') return 'cell-error-high'
  if (err.severity === 'medium') return 'cell-error-medium'
  return 'cell-error-low'
}

function rowClass(row: RowData) {
  if (!row.validation) return ''
  if (row.validation.status === 'error') return 'row-error'
  if (row.validation.status === 'warning') return 'row-warning'
  return ''
}

function scoreColor(score: number) {
  if (score >= 80) return '#10b981'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}

/** قائمة التعديلات (صف، عمود، قديم، جديد) */
const modifications = computed(() => {
  const out: { row_index: number; col: string; oldVal: string; newVal: string }[] = []
  for (const row of rows.value) {
    const orig = row.originalData
    const edit = row.editableData ?? orig
    for (const col of columns.value) {
      const o = orig[col] != null ? String(orig[col]) : ''
      const n = edit[col] != null ? String(edit[col]) : ''
      if (o !== n) out.push({ row_index: row.row_index, col, oldVal: o, newVal: n })
    }
  }
  return out
})

function buildReportText(): string {
  const lines: string[] = []
  lines.push('=== تقرير التحليل والتعديلات ===')
  lines.push('')
  if (batchResult.value?.stats) {
    const s = batchResult.value.stats
    lines.push('--- ملخص التحليل ---')
    lines.push(`إجمالي السجلات: ${s.total}`)
    lines.push(`بها أخطاء: ${s.errors}`)
    lines.push(`تحذيرات: ${s.warnings}`)
    lines.push(`سليمة: ${s.valid}`)
    lines.push(`متوسط الثقة: ${s.avg_confidence}%`)
    lines.push('')
  }
  lines.push('--- الأخطاء والتحذيرات المرصودة (حسب الصف) ---')
  let hasIssues = false
  for (const row of rows.value) {
    if (!row.validation || (row.validation.status === 'valid' && !row.validation.errors?.length)) continue
    hasIssues = true
    const d = getRowDetails(row)
    lines.push(`صف ${row.row_index + 1}: ${row.validation.status === 'error' ? 'خطأ' : 'تحذير'} — ${d.summary ?? row.validation.summary ?? ''}`)
    for (const p of d.problems) lines.push(`  • ${p}`)
  }
  if (!hasIssues) lines.push('لا توجد أخطاء أو تحذيرات مرصودة.')
  lines.push('')
  lines.push('--- التعديلات التي أجراها المستخدم ---')
  if (modifications.value.length === 0) {
    lines.push('لم يتم تعديل أي خلية.')
  } else {
    for (const m of modifications.value) {
      lines.push(`صف ${m.row_index + 1}، العمود «${m.col}»: من «${m.oldVal}» إلى «${m.newVal}»`)
    }
  }
  return lines.join('\n')
}

function downloadBlob(blob: Blob, name: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  a.click()
  URL.revokeObjectURL(a.href)
}

function exportFileOnly() {
  const isCsv = fileName.value.toLowerCase().endsWith('.csv')
  const baseName = fileName.value.replace(/\.[^.]+$/, '') || 'export'
  const dataRows = rows.value.map((r) => r.editableData ?? r.originalData)
  if (isCsv) {
    const header = columns.value.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')
    const csvLines = [header]
    for (const row of dataRows) {
      const cells = columns.value.map((c) => {
        const v = row[c]
        const s = v != null ? String(v) : ''
        return `"${s.replace(/"/g, '""')}"`
      })
      csvLines.push(cells.join(','))
    }
    const csv = '\uFEFF' + csvLines.join('\r\n')
    downloadBlob(new Blob([csv], { type: 'text/csv;charset=utf-8' }), `${baseName}_معدل.csv`)
  } else {
    const ws = XLSX.utils.json_to_sheet(dataRows, { header: columns.value })
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
    const xlsxBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
    downloadBlob(new Blob([xlsxBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }), `${baseName}_معدل.xlsx`)
  }
}

function exportFileAndReport() {
  const baseName = fileName.value.replace(/\.[^.]+$/, '') || 'export'
  exportFileOnly()
  downloadBlob(new Blob([buildReportText()], { type: 'text/plain;charset=utf-8' }), `${baseName}_تقرير.txt`)
}

/** ملخص المشاكل والاقتراحات للصف (لعمود التفاصيل) */
function getRowDetails(row: RowData): { isOk: boolean; summary?: string; problems: string[]; suggestions: string[] } {
  const v = row.validation
  if (!v) return { isOk: true, problems: [], suggestions: [] }
  if (v.status === 'valid' && (!v.errors?.length && !v.suggestions?.length)) {
    return { isOk: true, summary: v.summary || undefined, problems: [], suggestions: v.suggestions || [] }
  }
  const problems = (v.errors || []).map((e) => `${e.field}: ${e.message}`)
  const suggestions = v.suggestions || []
  return {
    isOk: false,
    summary: v.summary || undefined,
    problems,
    suggestions,
  }
}
</script>

<template>
  <div class="excel-page">
    <div class="page-head">
      <h1 class="page-title">تحليل الملف</h1>
      <p class="page-desc">
        ارفع ملف Excel أو CSV، ثم اختر <strong>نوع التحليل</strong> (قواعد الأعمال، Gemini، أو الاثنين معاً) واضغط <strong>تحليل</strong>. يُلوّن الخلايا ويُظهر التنبيهات. الملاحظات بالعربية حتى لو كانت البيانات بالإنجليزية.
      </p>
    </div>

    <!-- Upload zone: خانة واحدة لـ Excel و CSV -->
    <div v-if="!rows.length" class="upload-zone"
      :class="{ 'dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop">
      <div class="upload-icon">📂</div>
      <p class="upload-title">اسحب ملف Excel أو CSV هنا</p>
      <p class="upload-sub">أو</p>
      <label class="btn btn-primary upload-btn">
        اختر ملفاً
        <input type="file" accept=".xlsx,.xls,.csv" hidden @change="onFileInput" />
      </label>
      <p class="upload-note">يقبل: Excel (xlsx · xls) و CSV — البيانات بالإنجليزي أو العربي</p>
    </div>

    <!-- File loaded: preview + actions -->
    <template v-else>
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-main">
          <div class="file-info">
            <span class="file-icon">📄</span>
            <span class="file-name">{{ fileName }}</span>
            <span class="file-rows">{{ rows.length }} سجل</span>
          </div>
          <div class="toolbar-actions">
            <button class="btn btn-ghost btn-sm" @click="resetFile">تغيير الملف</button>
            <button
              class="btn btn-primary btn-sm"
              :disabled="isProcessing"
              @click="analyzeAll">
              <span v-if="isProcessing" class="btn-spinner"></span>
              {{ analyzeButtonLabel }}
            </button>
            <button class="btn btn-download btn-sm" @click="exportFileOnly" title="تحميل الملف المعدّل فقط">
              📥 تحميل الملف
            </button>
            <button class="btn btn-export btn-sm" @click="exportFileAndReport" title="تصدير الملف المعدّل مع التقرير">
              💾 حفظ وتصدير + التقرير
            </button>
          </div>
        </div>
        <div class="toolbar-engine" role="group" aria-label="نوع التحليل">
          <span class="engine-label">نوع التحليل</span>
          <div class="engine-btns">
            <button
              type="button"
              class="engine-btn"
              :class="{ 'engine-btn-active': analysisEngine === 'rules' }"
              :disabled="isProcessing"
              @click="analysisEngine = 'rules'"
            >
              قواعد الأعمال
            </button>
            <button
              type="button"
              class="engine-btn"
              :class="{ 'engine-btn-active': analysisEngine === 'gemini' }"
              :disabled="isProcessing"
              @click="analysisEngine = 'gemini'"
            >
              Gemini
            </button>
            <button
              type="button"
              class="engine-btn"
              :class="{ 'engine-btn-active': analysisEngine === 'both' }"
              :disabled="isProcessing"
              @click="analysisEngine = 'both'"
            >
              الكل
            </button>
          </div>
        </div>
      </div>

      <div v-if="analysisError" class="analysis-error-banner" role="alert">
        {{ analysisError }}
      </div>

      <!-- تنبيه بأسباب (نفس منطق التحليل بـ Gemini + القواعد) -->
      <div
        v-if="analysisNotice && !analysisNotice.allClear"
        class="analysis-notice-card"
        role="status"
      >
        <div class="analysis-notice-head">
          <span class="analysis-notice-icon">⚠️</span>
          <div>
            <h3 class="analysis-notice-title">نتيجة التحليل — تنبيهات</h3>
            <p class="analysis-notice-meta">
              {{ analysisNotice.totalErrors }} صف بحالة خطأ · {{ analysisNotice.totalWarnings }} تحذير
              <span v-if="batchResult?.provider === 'gemini'" class="tag-gemini">Gemini</span>
              <span v-else-if="batchResult?.provider === 'rules'" class="tag-rules">قواعد فقط</span>
              <span v-else-if="batchResult?.provider === 'local'" class="tag-local">تحقق محلي + قواعد</span>
            </p>
          </div>
        </div>
        <ul v-if="analysisNotice.items.length" class="analysis-notice-list">
          <li v-for="(it, idx) in analysisNotice.items" :key="idx" class="analysis-notice-li">
            <span class="notice-field">{{ it.fieldLabel }}</span>
            <span class="notice-msg">{{ it.message }}</span>
            <span v-if="it.rule_id != null" class="notice-rule">قاعدة {{ it.rule_id }}</span>
            <span v-if="it.message_en" class="notice-en" dir="ltr">{{ it.message_en }}</span>
          </li>
        </ul>
        <p
          v-else-if="analysisNotice.totalErrors + analysisNotice.totalWarnings > 0"
          class="analysis-notice-fallback"
        >
          وُجدت مشاكل في الصفوف — راجع ألوان الخلايا أو عمود «تفاصيل» والتبويبات أعلاه.
        </p>
        <ul v-if="analysisNotice.suggestions.length" class="analysis-notice-suggestions">
          <li
            v-for="(sg, sgi) in analysisNotice.suggestions"
            :key="'sg' + sgi"
            class="suggestion-li"
          >
            💡 {{ sg }}
          </li>
        </ul>
      </div>

      <div v-else-if="analysisNotice && analysisNotice.allClear" class="analysis-notice-ok" role="status">
        <span class="ok-icon">✓</span>
        <div>
          <strong>لم يُرصد خطأ أو تحذير في الدفعة</strong>
          <p class="ok-sub">يمكنك مراجعة الجدول أو تصدير التقرير إن رغبت.</p>
        </div>
      </div>

      <!-- Stats bar (after analysis) -->
      <div v-if="stats" class="stats-bar">
        <div class="stat-card stat-total">
          <span class="stat-num">{{ stats.total }}</span>
          <span class="stat-label">إجمالي السجلات</span>
        </div>
        <div class="stat-card stat-error">
          <span class="stat-num">{{ stats.errors }}</span>
          <span class="stat-label">بها أخطاء</span>
        </div>
        <div class="stat-card stat-warning">
          <span class="stat-num">{{ stats.warnings }}</span>
          <span class="stat-label">تحذيرات</span>
        </div>
        <div class="stat-card stat-valid">
          <span class="stat-num">{{ stats.valid }}</span>
          <span class="stat-label">سليمة</span>
        </div>
        <div class="stat-card stat-avg">
          <span class="stat-num" :style="{ color: scoreColor(stats.avg_confidence) }">
            {{ stats.avg_confidence }}%
          </span>
          <span class="stat-label">متوسط الثقة</span>
        </div>
      </div>

      <div
        v-if="batchResult?.provider"
        class="provider-notice"
        :class="{
          'provider-ok': batchResult.provider === 'gemini',
          'provider-rules': batchResult.provider === 'rules',
          'provider-local': batchResult.provider === 'local',
        }"
      >
        <span v-if="batchResult.provider === 'gemini'">✓ تم التحليل بـ Gemini</span>
        <span v-else-if="batchResult.provider === 'rules'">
          ✓ تم التحليل بـ <strong>قواعد الأعمال</strong> فقط (LFS Business Rules) — دون استدعاء النموذج اللغوي.
        </span>
        <span v-else-if="batchResult.provider === 'local'">
          التحليل تم محلياً. لتفعيل التحليل بـ Gemini: أضف <code>GEMINI_API_KEY</code> في ملف <code>.env</code> داخل مجلد <code>backend</code> ثم أعد تشغيل السيرفر.
        </span>
      </div>

      <!-- Filter tabs (after analysis) -->
      <div v-if="batchResult" class="filter-tabs">
        <button :class="['tab', filter === 'all' && 'tab-active']" @click="filter = 'all'">
          الكل ({{ rows.length }})
        </button>
        <button :class="['tab', 'tab-error', filter === 'error' && 'tab-active']" @click="filter = 'error'">
          أخطاء ({{ stats?.errors }})
        </button>
        <button :class="['tab', 'tab-warning', filter === 'warning' && 'tab-active']" @click="filter = 'warning'">
          تحذيرات ({{ stats?.warnings }})
        </button>
        <button :class="['tab', 'tab-valid', filter === 'valid' && 'tab-active']" @click="filter = 'valid'">
          سليمة ({{ stats?.valid }})
        </button>
      </div>

      <!-- Legend -->
      <div v-if="batchResult" class="legend">
        <span class="legend-item"><span class="legend-dot dot-high"></span> خطأ حرج</span>
        <span class="legend-item"><span class="legend-dot dot-medium"></span> تحذير متوسط</span>
        <span class="legend-item"><span class="legend-dot dot-low"></span> ملاحظة خفيفة</span>
        <span class="legend-tip">تفاصيل الأخطاء والاقتراحات في عمود «تفاصيل»</span>
      </div>

      <!-- Table -->
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="th-num">#</th>
              <th v-for="col in columns" :key="col" class="th-col" :title="columnHeaderLabel(col) !== col ? col : undefined">
                {{ columnHeaderLabel(col) }}
              </th>
              <th v-if="batchResult" class="th-details">تفاصيل</th>
              <th v-if="batchResult" class="th-score">درجة الثقة</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.row_index" :class="rowClass(row)">
              <td class="td-num">{{ row.row_index + 1 }}</td>

              <td v-for="col in columns" :key="col"
                :class="['data-cell', getCellClass(row, col)]">
                <div class="cell-inner">
                  <input
                    v-model="row.editableData[col]"
                    type="text"
                    class="cell-input"
                  />
                </div>
              </td>

              <!-- تفاصيل: زر يفتح نافذة -->
              <td v-if="batchResult" class="td-details">
                <template v-if="!row.validation">
                  <span class="details-na">—</span>
                </template>
                <template v-else>
                  <button
                    type="button"
                    class="btn-details"
                    :class="{ 'has-issues': rowDetailsMap.get(row.row_index)?.problems?.length }"
                    @click="detailsModalRow = row.row_index"
                  >
                    تفاصيل
                  </button>
                </template>
              </td>

              <!-- Score -->
              <td v-if="batchResult" class="td-score">
                <span v-if="row.validation" class="score-badge"
                  :style="{ color: scoreColor(row.validation.confidence_score), borderColor: scoreColor(row.validation.confidence_score) }">
                  {{ row.validation.confidence_score }}
                </span>
                <span v-else class="score-na">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- نافذة تفاصيل المشكلة -->
      <Teleport to="body">
        <div v-if="detailsModalRow !== null" class="details-overlay" @click.self="detailsModalRow = null">
          <div class="details-modal">
            <div class="details-modal-head">
              <h3>تفاصيل الصف {{ detailsModalRow !== null ? detailsModalRow + 1 : '' }}</h3>
              <button type="button" class="details-modal-close" aria-label="إغلاق" @click="detailsModalRow = null">×</button>
            </div>
            <div class="details-modal-body">
              <template v-if="rowDetailsMap.get(detailsModalRow!)">
                <template v-if="rowDetailsMap.get(detailsModalRow!)?.isOk && !rowDetailsMap.get(detailsModalRow!)?.problems?.length">
                  <p class="details-ok">لا توجد مشاكل</p>
                  <p v-if="rowDetailsMap.get(detailsModalRow!)?.summary" class="details-summary">{{ rowDetailsMap.get(detailsModalRow!)?.summary }}</p>
                </template>
                <template v-else>
                  <p v-if="rowDetailsMap.get(detailsModalRow!)?.summary" class="details-summary">{{ rowDetailsMap.get(detailsModalRow!)?.summary }}</p>
                  <div v-if="rowDetailsMap.get(detailsModalRow!)?.problems?.length" class="details-block">
                    <strong class="details-label">المشاكل:</strong>
                    <ul class="details-list">
                      <li v-for="(p, i) in rowDetailsMap.get(detailsModalRow!)?.problems" :key="i">{{ p }}</li>
                    </ul>
                  </div>
                  <div v-if="rowDetailsMap.get(detailsModalRow!)?.suggestions?.length" class="details-block">
                    <strong class="details-label">اقتراحات للتعديل:</strong>
                    <ul class="details-list details-suggestions">
                      <li v-for="(s, i) in rowDetailsMap.get(detailsModalRow!)?.suggestions" :key="i">{{ s }}</li>
                    </ul>
                  </div>
                </template>
              </template>
            </div>
          </div>
        </div>
      </Teleport>
    </template>
  </div>
</template>

<style scoped>
.excel-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem 2rem 4rem;
}

.page-head { margin-bottom: 1.5rem; }
.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.4rem;
}
.page-desc {
  color: var(--color-text);
  opacity: 0.85;
  font-size: 1rem;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed var(--color-border);
  border-radius: 1rem;
  padding: 4rem 2rem;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
}
.upload-zone.dragging {
  border-color: #0e7490;
  background: rgba(6, 182, 212, 0.04);
}
.upload-icon { font-size: 3rem; margin-bottom: 1rem; }
.upload-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-heading);
  margin-bottom: 0.5rem;
}
.upload-sub { color: var(--color-text); opacity: 0.5; margin-bottom: 0.75rem; }
.upload-btn { cursor: pointer; }
.upload-note {
  margin-top: 0.75rem;
  font-size: 0.8rem;
  color: var(--color-text);
  opacity: 0.5;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.7rem 1.4rem;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 0.5rem;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  font-family: inherit;
  text-decoration: none;
}
.btn-primary { background: #0e7490; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #0c6380; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost { background: transparent; color: var(--color-text); border-color: var(--color-border); }
.btn-ghost:hover { background: var(--color-background-mute); }
.btn-sm { padding: 0.5rem 1rem; font-size: 0.875rem; }
.btn-spinner {
  width: 13px; height: 13px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Toolbar */
.toolbar {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.6rem;
}
.toolbar-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.toolbar-engine {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
}
.engine-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-heading);
  opacity: 0.9;
}
.engine-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.engine-btn {
  padding: 0.35rem 0.75rem;
  font-size: 0.78rem;
  font-family: inherit;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.engine-btn:hover:not(:disabled) {
  background: var(--color-background-mute);
}
.engine-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.engine-btn-active {
  background: rgba(14, 116, 144, 0.14);
  border-color: #0e7490;
  color: #0e7490;
  font-weight: 600;
}
.analysis-error-banner {
  margin: -0.25rem 0 1rem;
  padding: 0.65rem 1rem;
  font-size: 0.875rem;
  color: #991b1b;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.35);
  border-radius: 0.5rem;
}

.analysis-notice-card {
  margin-bottom: 1rem;
  padding: 1rem 1.1rem;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(239, 68, 68, 0.06));
  border: 1px solid rgba(245, 158, 11, 0.45);
  border-radius: 0.65rem;
}
.analysis-notice-head {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}
.analysis-notice-icon { font-size: 1.35rem; line-height: 1; }
.analysis-notice-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-heading);
}
.analysis-notice-meta {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--color-text);
  opacity: 0.88;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}
.tag-gemini, .tag-local, .tag-rules {
  font-size: 0.72rem;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-weight: 600;
}
.tag-gemini { background: rgba(16, 185, 129, 0.2); color: #047857; }
.tag-rules { background: rgba(59, 130, 246, 0.18); color: #1d4ed8; }
.tag-local { background: rgba(107, 114, 128, 0.2); color: #374151; }

.analysis-notice-list {
  margin: 0;
  padding-right: 1.1rem;
  list-style: disc;
  font-size: 0.875rem;
  line-height: 1.45;
  color: var(--color-text);
}
.analysis-notice-li {
  margin-bottom: 0.5rem;
}
.notice-field {
  display: inline-block;
  font-weight: 600;
  color: var(--color-heading);
  margin-left: 0.35rem;
}
.notice-msg { display: inline; }
.notice-rule {
  display: inline-block;
  margin-right: 0.35rem;
  font-size: 0.72rem;
  padding: 0.08rem 0.4rem;
  border-radius: 0.25rem;
  background: rgba(14, 116, 144, 0.15);
  color: #0e7490;
  vertical-align: middle;
}
.notice-en {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.78rem;
  opacity: 0.85;
  color: var(--color-text);
}
.analysis-notice-fallback {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text);
  opacity: 0.9;
}
.analysis-notice-suggestions {
  margin: 0.65rem 0 0;
  padding-right: 1rem;
  list-style: none;
  font-size: 0.82rem;
  color: #0e7490;
}
.suggestion-li { margin-bottom: 0.35rem; }

.analysis-notice-ok {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.35);
  border-radius: 0.65rem;
  font-size: 0.9rem;
  color: var(--color-heading);
}
.analysis-notice-ok .ok-icon {
  font-size: 1.25rem;
  color: #059669;
  line-height: 1.2;
}
.ok-sub {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  font-weight: 400;
  color: var(--color-text);
  opacity: 0.85;
}
.file-info { display: flex; align-items: center; gap: 0.5rem; }
.file-icon { font-size: 1.1rem; }
.file-name { font-weight: 600; color: var(--color-heading); font-size: 0.95rem; }
.file-rows {
  font-size: 0.78rem;
  color: #0e7490;
  background: rgba(6,182,212,0.1);
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
}
.toolbar-actions { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }

/* Stats */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (max-width: 700px) {
  .stats-bar { grid-template-columns: repeat(3, 1fr); }
}
.stat-card {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.6rem;
  padding: 0.9rem 1rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.stat-num { font-size: 1.5rem; font-weight: 700; line-height: 1; }
.stat-label { font-size: 0.78rem; color: var(--color-text); opacity: 0.7; }
.stat-total .stat-num { color: var(--color-heading); }
.stat-error .stat-num { color: #ef4444; }
.stat-warning .stat-num { color: #f59e0b; }
.stat-valid .stat-num { color: #10b981; }

/* Provider notice (Gemini vs local) */
.provider-notice {
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}
.provider-notice code { font-family: ui-monospace, monospace; padding: 0.1rem 0.35rem; border-radius: 0.25rem; }
.provider-ok { background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; color: #047857; }
.provider-rules { background: rgba(59, 130, 246, 0.1); border: 1px solid #3b82f6; color: #1d4ed8; }
.provider-local { background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; color: #b45309; }

/* Filter tabs */
.filter-tabs {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}
.tab {
  padding: 0.4rem 0.9rem;
  font-size: 0.85rem;
  font-weight: 500;
  border-radius: 9999px;
  border: 1.5px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.tab:hover { background: var(--color-background-mute); }
.tab-active { background: var(--color-background-mute); border-color: #0e7490; color: #0e7490; font-weight: 700; }
.tab-error.tab-active { border-color: #ef4444; color: #ef4444; }
.tab-warning.tab-active { border-color: #f59e0b; color: #f59e0b; }
.tab-valid.tab-active { border-color: #10b981; color: #10b981; }

/* Legend */
.legend {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
  color: var(--color-text);
  opacity: 0.8;
}
.legend-item { display: flex; align-items: center; gap: 0.35rem; }
.legend-dot {
  width: 10px; height: 10px;
  border-radius: 2px;
  display: inline-block;
}
.dot-high   { background: rgba(239,68,68,0.3); border: 1.5px solid #ef4444; }
.dot-medium { background: rgba(245,158,11,0.3); border: 1.5px solid #f59e0b; }
.dot-low    { background: rgba(107,114,128,0.2); border: 1.5px solid #6b7280; }
.legend-tip { margin-right: auto; font-style: italic; opacity: 0.6; }

/* Table */
.table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  min-width: 600px;
  table-layout: auto;
}
.data-table thead {
  background: var(--color-background-mute);
  position: sticky;
  top: 0;
  z-index: 2;
}
.data-table th {
  padding: 0.7rem 0.75rem;
  text-align: right;
  font-weight: 600;
  color: var(--color-heading);
  border-bottom: 1px solid var(--color-border);
  font-size: 0.82rem;
  vertical-align: top;
  /* خلفية لكل خلية حتى لا يختلط النص مع الصفوف عند sticky */
  background: var(--color-background-mute);
  box-sizing: border-box;
}
/* nowrap فقط للأعمدة الضيقة — لا تُفرض على رؤوس الحقول الطويلة */
.data-table th.th-num,
.data-table th.th-details,
.data-table th.th-score {
  white-space: nowrap;
}
.data-table th.th-col {
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
  min-width: 8rem;
  max-width: 13rem;
  line-height: 1.35;
}
.th-num, .td-num {
  text-align: center;
  width: 44px;
  color: var(--color-text);
  opacity: 0.45;
  font-size: 0.78rem;
}
.th-details, .td-details {
  text-align: center;
  padding: 0.6rem 0.85rem;
  width: 1%;
  white-space: nowrap;
}
.details-na { color: var(--color-text); opacity: 0.4; font-size: 0.875rem; }
.btn-details {
  padding: 0.35rem 0.65rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.4);
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s, border-color 0.2s;
}
.btn-details:hover { background: rgba(6, 182, 212, 0.2); border-color: #0e7490; }
.btn-details.has-issues { color: #b45309; background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.4); }
.btn-details.has-issues:hover { background: rgba(245, 158, 11, 0.2); }
.details-ok { color: #047857; font-weight: 500; margin: 0 0 0.5rem 0; }
.details-summary { margin: 0 0 0.5rem 0; color: var(--color-text); opacity: 0.9; line-height: 1.5; }
.details-block { margin-top: 0.75rem; }
.details-block:first-of-type { margin-top: 0; }
.details-label { display: block; font-size: 0.75rem; color: var(--color-heading); margin-bottom: 0.25rem; }
.details-list { margin: 0; padding-right: 1.25rem; list-style: disc; }
.details-list li { margin-bottom: 0.25rem; }
.details-suggestions { color: #0e7490; }
.th-score, .td-score { text-align: center; width: 90px; }

/* نافذة التفاصيل */
.details-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}
.details-modal {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  max-width: 420px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}
.details-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}
.details-modal-head h3 { margin: 0; font-size: 1rem; font-weight: 600; color: var(--color-heading); }
.details-modal-close {
  width: 28px;
  height: 28px;
  padding: 0;
  font-size: 1.25rem;
  line-height: 1;
  color: var(--color-text);
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.details-modal-close:hover { background: var(--color-background-soft); color: var(--color-heading); }
.details-modal-body {
  padding: 1rem;
  overflow-y: auto;
  font-size: 0.875rem;
}

.data-table tbody tr {
  border-bottom: 1px solid var(--color-border);
  transition: background 0.15s;
}
.data-table tbody tr:hover { background: var(--color-background-mute); }
.data-table tbody tr:last-child { border-bottom: none; }

/* Row level classes */
.row-error { background: rgba(239,68,68,0.03); }
.row-warning { background: rgba(245,158,11,0.03); }

/* Data cells */
.data-cell {
  padding: 0;
  min-width: 8rem;
  max-width: 14rem;
  vertical-align: top;
}
.cell-inner {
  position: relative;
  padding: 0.6rem 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.cell-val {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
  display: inline-block;
}
.cell-input {
  width: 100%;
  min-width: 0;
  padding: 0.4rem 0.5rem;
  font-size: inherit;
  font-family: inherit;
  color: var(--color-text);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.25rem;
  text-align: inherit;
}
.cell-input:hover { border-color: var(--color-border); }
.cell-input:focus {
  outline: none;
  border-color: #0e7490;
  background: var(--color-background);
}
.btn-download {
  background: var(--color-background-mute);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
.btn-download:hover { background: var(--color-background-soft); }
.btn-export {
  background: #047857;
  color: #fff;
  border: none;
}
.btn-export:hover { background: #065f46; }
/* Error cell colors */
.cell-error-high {
  background: rgba(239, 68, 68, 0.12) !important;
  border-right: 3px solid #ef4444;
}
.cell-error-medium {
  background: rgba(245, 158, 11, 0.12) !important;
  border-right: 3px solid #f59e0b;
}
.cell-error-low {
  background: rgba(107, 114, 128, 0.1) !important;
  border-right: 3px solid #6b7280;
}

/* Error badge */
.error-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #ef4444;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 800;
  flex-shrink: 0;
  cursor: help;
}

/* Tooltip */
.tooltip-box {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  z-index: 100;
  bottom: calc(100% + 6px);
  right: 0;
  min-width: 220px;
  max-width: 280px;
  background: #1f2937;
  color: #f9fafb;
  padding: 0.65rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.8rem;
  line-height: 1.5;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
  transition: opacity 0.15s, visibility 0.15s;
  pointer-events: none;
  white-space: normal;
}
.tooltip-box::after {
  content: '';
  position: absolute;
  top: 100%;
  right: 18px;
  border: 5px solid transparent;
  border-top-color: #1f2937;
}
.cell-inner:hover .tooltip-box {
  visibility: visible;
  opacity: 1;
}
.tooltip-sev {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 9999px;
  display: inline-block;
  margin-bottom: 0.35rem;
}
.sev-high   { background: rgba(239,68,68,0.2); color: #fca5a5; }
.sev-medium { background: rgba(245,158,11,0.2); color: #fcd34d; }
.sev-low    { background: rgba(107,114,128,0.2); color: #d1d5db; }

/* Score */
.score-badge {
  display: inline-block;
  font-size: 0.82rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  border: 1.5px solid;
}
.score-na { color: var(--color-text); opacity: 0.3; font-size: 0.85rem; }

@media (prefers-color-scheme: dark) {
  .upload-zone:hover { border-color: #22d3ee; }
  .tab-active { border-color: #22d3ee; color: #22d3ee; }
  .file-rows { color: #22d3ee; background: rgba(34,211,238,0.1); }
  .tooltip-box { background: #111827; }
  .tooltip-box::after { border-top-color: #111827; }
}
</style>
