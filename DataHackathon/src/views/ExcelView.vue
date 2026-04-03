<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import iconv from 'iconv-lite'
import { loadLfsMetadataMap } from '../utils/lfsMetadata'
import { normalizeRowsNullLike } from '../utils/spreadsheetNull'
import { mergeLfsDescIntoCodeRows } from '../utils/lfsCodeDescMerge'
import {
  formatLfsColumnHeaderTooltip,
  resolveLfsTableColumnHeader,
} from '../utils/lfsTableColumnHeader'
import { validationErrorMatchesKind } from '../utils/lfsIssueKind'
import type { IssueKindClass } from '../utils/lfsIssueKind'
import { buildFilteredIssueCards } from '../utils/lfsIssueCards'
import FieldRuleDetailModal from '../components/FieldRuleDetailModal.vue'
import { fetchBatchInsightsReport, fetchLfsBusinessRulesCatalog, validateBatchDynamic } from '../services/api'
import type {
  BatchInsightsResponse,
  BatchResult,
  LfsBusinessRuleRow,
  ValidationError,
} from '../services/api'

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
/** تقرير نهاية التحليل (تكرار الأخطاء + Gemini أو احتياطي إحصائي) */
const insightsReport = ref<BatchInsightsResponse | null>(null)
const insightsLoading = ref(false)
const insightsError = ref<string | null>(null)
/** جدول قواعد الأعمال (مقترحات تصحيحية وملخصات) مفهرس بـ rule_id */
const lfsRulesById = ref<Record<number, LfsBusinessRuleRow>>({})
/** خلية مفتوحة لنافذة «قاعدة مؤكدة» */
const fieldDetailTarget = ref<{ rowIndex: number; col: string } | null>(null)
/** رسالة عند فشل الطلب للخادم (بعد الرفع التلقائي أو اليدوي) */
const analysisError = ref<string | null>(null)
type SeverityFilterBtn = 'all' | 'high' | 'medium' | 'low'
type IssueKindFilterBtn = 'all' | IssueKindClass

const severityFilterBtn = ref<SeverityFilterBtn>('all')
const issueKindFilterBtn = ref<IssueKindFilterBtn>('all')
const detailsModalRow = ref<number | null>(null)

/** قواعد فقط | Gemini فقط | الاثنان معاً */
type AnalysisEngine = 'rules' | 'gemini' | 'both'
const analysisEngine = ref<AnalysisEngine>('both')

/** معرف العمود (tag) → نص السؤال من MetaData_LFS_Training_Dataset */
const lfsColumnQuestionByName = ref<Record<string, string>>({})

async function loadLfsColumnMetadata() {
  lfsColumnQuestionByName.value = await loadLfsMetadataMap(import.meta.env.BASE_URL)
}

/** خريطة رؤوس الأعمدة (تصنيف + مختصر) — تُحدَّث مع الأعمدة والميتاداتا */
const columnHeaderByCol = computed(() => {
  const meta = lfsColumnQuestionByName.value
  const map: Record<string, ReturnType<typeof resolveLfsTableColumnHeader>> = {}
  for (const c of columns.value) {
    map[c] = resolveLfsTableColumnHeader(c, meta)
  }
  return map
})

/** للحقول خارج الجدول (تنبيهات، تفاصيل) */
function columnHeaderLabel(tag: string): string {
  return resolveLfsTableColumnHeader(tag, lfsColumnQuestionByName.value).shortLabel
}
function columnHeaderTooltipFromCol(col: string): string {
  const r = columnHeaderByCol.value[col]
  return r ? formatLfsColumnHeaderTooltip(r) : formatLfsColumnHeaderTooltip(resolveLfsTableColumnHeader(col, lfsColumnQuestionByName.value))
}

async function loadLfsRulesCatalog() {
  try {
    const data = await fetchLfsBusinessRulesCatalog()
    const m: Record<number, LfsBusinessRuleRow> = {}
    for (const r of data.rules) {
      m[r.rule_id] = r
    }
    lfsRulesById.value = m
  } catch {
    lfsRulesById.value = {}
  }
}

onMounted(() => {
  loadLfsColumnMetadata()
  loadLfsRulesCatalog()
})

function rowMatchesSeverityBtn(r: RowData, f: SeverityFilterBtn): boolean {
  if (f === 'all') return true
  return (r.validation?.errors ?? []).some((e) => String(e.severity ?? 'medium').toLowerCase() === f)
}

function rowMatchesIssueKindBtn(r: RowData, f: IssueKindFilterBtn): boolean {
  if (f === 'all') return true
  return (r.validation?.errors ?? []).some((e) => validationErrorMatchesKind(e, f))
}

const filteredRows = computed(() =>
  rows.value.filter(
    (r) => rowMatchesSeverityBtn(r, severityFilterBtn.value) && rowMatchesIssueKindBtn(r, issueKindFilterBtn.value),
  ),
)

const severityFilterCounts = computed(() => {
  const list = rows.value
  const n = (pred: (r: RowData) => boolean) => list.filter(pred).length
  return {
    all: list.length,
    high: n((r) => (r.validation?.errors ?? []).some((e) => e.severity === 'high')),
    medium: n((r) =>
      (r.validation?.errors ?? []).some((e) => String(e.severity ?? 'medium').toLowerCase() === 'medium'),
    ),
    low: n((r) => (r.validation?.errors ?? []).some((e) => e.severity === 'low')),
  }
})

const issueKindFilterCounts = computed(() => {
  const list = rows.value
  const n = (kind: IssueKindClass) =>
    list.filter((r) => (r.validation?.errors ?? []).some((e) => validationErrorMatchesKind(e, kind))).length
  return {
    all: list.length,
    semantic: n('semantic'),
    logical: n('logical'),
    input: n('input'),
  }
})

const filterToolbarActive = computed(
  () => severityFilterBtn.value !== 'all' || issueKindFilterBtn.value !== 'all',
)

/** بطاقات التنبيهات المطابقة للفلتر (نفس منطق جدول الصفوف المصفّى) */
const filteredIssueCards = computed(() =>
  buildFilteredIssueCards(
    rows.value,
    severityFilterBtn.value,
    issueKindFilterBtn.value,
    columnHeaderLabel,
  ),
)

const stats = computed(() => batchResult.value?.stats ?? null)

/** إجمالي عدد تنبيهات الخلايا حسب الشدة (جميع الصفوف) */
const severityIssueTotals = computed(() => {
  let high = 0
  let medium = 0
  let low = 0
  for (const r of rows.value) {
    for (const e of r.validation?.errors ?? []) {
      const s = String(e.severity ?? 'medium').toLowerCase()
      if (s === 'high') high++
      else if (s === 'low') low++
      else medium++
    }
  }
  return { high, medium, low }
})

async function loadInsightsReport() {
  const br = batchResult.value
  if (!br?.stats || !br.results?.length) {
    insightsLoading.value = false
    return
  }
  insightsLoading.value = true
  insightsError.value = null
  try {
    insightsReport.value = await fetchBatchInsightsReport({ stats: br.stats, results: br.results })
  } catch (e) {
    insightsError.value =
      e instanceof Error ? e.message : 'تعذّر جلب تقرير نهاية التحليل. تحقق من الاتصال بالخادم.'
    insightsReport.value = null
  } finally {
    insightsLoading.value = false
  }
}

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

/**
 * أعمدة *_desc المتبقية (بعد دمج lfsCodeDescMerge) — تُخفى إن وُجدت دون قاعدة مطابقة.
 */
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

    const rawRows: Record<string, any>[] = normalizeRowsNullLike(
      XLSX.utils.sheet_to_json(ws, { defval: '' }) as Record<string, any>[],
    )
    if (!rawRows.length || !rawRows[0]) return

    const merged = mergeLfsDescIntoCodeRows(rawRows) as Record<string, any>[]
    const { columns: visibleCols, rows: dataRows } = stripTechnicalDescColumns(merged)
    if (!visibleCols.length) return

    columns.value = visibleCols
    rows.value = dataRows.map((row, i) => ({
      row_index: i,
      originalData: row,
      editableData: { ...row },
      validation: null,
    }))

    batchResult.value = null
    insightsReport.value = null
    insightsError.value = null
    fieldDetailTarget.value = null
    analysisError.value = null
    severityFilterBtn.value = 'all'
    issueKindFilterBtn.value = 'all'
  }

  reader.readAsArrayBuffer(file)
}

async function analyzeAll() {
  if (!rows.value.length || !columns.value.length) return
  isProcessing.value = true
  analysisError.value = null
  insightsReport.value = null
  insightsError.value = null
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
    await loadInsightsReport()
  } catch (e) {
    batchResult.value = null
    insightsReport.value = null
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
  insightsReport.value = null
  insightsError.value = null
  analysisError.value = null
  fieldDetailTarget.value = null
  severityFilterBtn.value = 'all'
  issueKindFilterBtn.value = 'all'
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

const fieldDetailContext = computed(() => {
  const t = fieldDetailTarget.value
  if (t === null) return null
  const row = rows.value.find((r) => r.row_index === t.rowIndex)
  if (!row?.validation) return null
  const err = getFieldError(row, t.col)
  if (!err) return null
  return {
    row,
    col: t.col,
    err,
    fieldLabel: columnHeaderLabel(err.field),
    rowSuggestions: row.validation.suggestions ?? [],
  }
})

function openFieldDetail(row: RowData, col: string) {
  if (!getFieldError(row, col)) return
  fieldDetailTarget.value = { rowIndex: row.row_index, col }
}

function closeFieldDetail() {
  fieldDetailTarget.value = null
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
  const problems = (v.errors || []).map(
    (e) => `${columnHeaderLabel(e.field)} (${e.field}): ${e.message}`,
  )
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
        v-if="batchResult"
        class="severity-cards"
        role="group"
        aria-label="عدد التحذيرات حسب شدة الخلية"
      >
        <div class="severity-card severity-card--high">
          <span class="severity-card-num">{{ severityIssueTotals.high }}</span>
          <span class="severity-card-label">تحذيرات حرجة</span>
        </div>
        <div class="severity-card severity-card--medium">
          <span class="severity-card-num">{{ severityIssueTotals.medium }}</span>
          <span class="severity-card-label">متوسطة</span>
        </div>
        <div class="severity-card severity-card--low">
          <span class="severity-card-num">{{ severityIssueTotals.low }}</span>
          <span class="severity-card-label">منخفضة</span>
        </div>
      </div>

      <!-- تقرير نهاية التحليل: أكثر التكرار / الأقل / توصيات (Gemini أو احتياطي) -->
      <section v-if="batchResult" class="batch-insights-section" aria-label="تقرير نهاية التحليل">
        <div v-if="insightsLoading" class="batch-insights-loading">
          <span class="btn-spinner batch-insights-spinner" aria-hidden="true"></span>
          جارٍ إعداد تقرير نهاية التحليل (تكرار الأخطاء والتحليل)…
        </div>
        <div v-else-if="insightsError" class="batch-insights-error" role="alert">
          {{ insightsError }}
        </div>
        <article v-else-if="insightsReport?.report" class="batch-insights-card">
          <header class="batch-insights-head">
            <h3 class="batch-insights-title">تقرير نهاية التحليل</h3>
            <div class="batch-insights-badges">
              <span
                v-if="insightsReport.provider === 'gemini'"
                class="tag-gemini"
                title="نص التحليل من Gemini"
                >Gemini</span
              >
              <span v-else class="tag-insights-fallback" title="بدون مفتاح أو عند فشل النموذج"
                >تحليل إحصائي</span
              >
            </div>
          </header>
          <p v-if="insightsReport.message" class="batch-insights-note">{{ insightsReport.message }}</p>
          <p class="batch-insights-summary">{{ insightsReport.report.summary_ar }}</p>
          <div class="batch-insights-grid">
            <div class="batch-insights-block">
              <h4 class="batch-insights-h4">الأخطاء الأكثر تكراراً</h4>
              <p class="batch-insights-body">{{ insightsReport.report.most_repeated_insights_ar }}</p>
            </div>
            <div class="batch-insights-block">
              <h4 class="batch-insights-h4">أخطاء نادرة أو معزولة</h4>
              <p class="batch-insights-body">{{ insightsReport.report.rare_and_isolated_ar }}</p>
            </div>
            <div class="batch-insights-block">
              <h4 class="batch-insights-h4">حقول بأقل تكرار للمشاكل</h4>
              <p class="batch-insights-body">{{ insightsReport.report.least_problematic_fields_ar }}</p>
            </div>
          </div>
          <div v-if="insightsReport.report.priority_fields_ar?.length" class="batch-insights-priority">
            <span class="batch-insights-priority-label">أولوية المراجعة:</span>
            <span
              v-for="(pf, i) in insightsReport.report.priority_fields_ar"
              :key="'pf' + i"
              class="batch-insights-chip"
              >{{ columnHeaderLabel(pf) }}</span
            >
          </div>
          <ul v-if="insightsReport.report.recommendations_ar?.length" class="batch-insights-recs">
            <li v-for="(rec, ri) in insightsReport.report.recommendations_ar" :key="'rec' + ri">
              {{ rec }}
            </li>
          </ul>
          <div
            v-if="insightsReport.aggregates?.most_repeated?.length"
            class="batch-insights-table-wrap"
          >
            <span class="batch-insights-table-caption">أعلى الأنواع تكراراً (حقل + رسالة)</span>
            <table class="batch-insights-table">
              <thead>
                <tr>
                  <th>الحقل</th>
                  <th>التكرار</th>
                  <th>الرسالة</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, ti) in insightsReport.aggregates.most_repeated.slice(0, 12)" :key="'fr' + ti">
                  <td>{{ columnHeaderLabel(row.field) }}</td>
                  <td>{{ row.count }}</td>
                  <td class="batch-insights-msg-cell">{{ row.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>

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

      <!-- فلترة: شدة الخلية + نوع التنبيه -->
      <div v-if="batchResult" class="filter-toolbar" aria-label="فلترة الصفوف">
        <div class="filter-toolbar-row">
          <span class="filter-toolbar-label">الشدة</span>
          <div class="filter-btn-group" role="group">
            <button
              type="button"
              class="filter-chip"
              :class="{ 'filter-chip--on': severityFilterBtn === 'all' }"
              @click="severityFilterBtn = 'all'"
            >
              الكل <span class="filter-chip-n">{{ severityFilterCounts.all }}</span>
            </button>
            <button
              type="button"
              class="filter-chip filter-chip--sev-high"
              :class="{ 'filter-chip--on': severityFilterBtn === 'high' }"
              @click="severityFilterBtn = 'high'"
            >
              عالية <span class="filter-chip-n">{{ severityFilterCounts.high }}</span>
            </button>
            <button
              type="button"
              class="filter-chip filter-chip--sev-med"
              :class="{ 'filter-chip--on': severityFilterBtn === 'medium' }"
              @click="severityFilterBtn = 'medium'"
            >
              متوسطة <span class="filter-chip-n">{{ severityFilterCounts.medium }}</span>
            </button>
            <button
              type="button"
              class="filter-chip filter-chip--sev-low"
              :class="{ 'filter-chip--on': severityFilterBtn === 'low' }"
              @click="severityFilterBtn = 'low'"
            >
              منخفضة <span class="filter-chip-n">{{ severityFilterCounts.low }}</span>
            </button>
          </div>
        </div>
        <div class="filter-toolbar-row">
          <span class="filter-toolbar-label">نوع التنبيه</span>
          <div class="filter-btn-group filter-btn-group--kind" role="group">
            <button
              type="button"
              class="filter-chip"
              :class="{ 'filter-chip--on': issueKindFilterBtn === 'all' }"
              @click="issueKindFilterBtn = 'all'"
            >
              الكل <span class="filter-chip-n">{{ issueKindFilterCounts.all }}</span>
            </button>
            <button
              type="button"
              class="filter-chip"
              :class="{ 'filter-chip--on': issueKindFilterBtn === 'semantic' }"
              @click="issueKindFilterBtn = 'semantic'"
            >
              تناقض دلالي <span class="filter-chip-n">{{ issueKindFilterCounts.semantic }}</span>
            </button>
            <button
              type="button"
              class="filter-chip"
              :class="{ 'filter-chip--on': issueKindFilterBtn === 'logical' }"
              @click="issueKindFilterBtn = 'logical'"
            >
              تعارض منطقي <span class="filter-chip-n">{{ issueKindFilterCounts.logical }}</span>
            </button>
            <button
              type="button"
              class="filter-chip"
              :class="{ 'filter-chip--on': issueKindFilterBtn === 'input' }"
              @click="issueKindFilterBtn = 'input'"
            >
              احتمال خطأ إدخال <span class="filter-chip-n">{{ issueKindFilterCounts.input }}</span>
            </button>
          </div>
        </div>
        <p v-if="filterToolbarActive" class="filter-toolbar-hint">
          يعرض {{ filteredRows.length }} من {{ rows.length }} صفاً
        </p>
      </div>

      <!-- بطاقات التنبيهات حسب الفلتر -->
      <section v-if="batchResult" class="issue-cards-section" aria-label="قائمة التنبيهات">
        <h3 class="issue-cards-title">التنبيهات ({{ filteredIssueCards.length }})</h3>
        <p v-if="!filteredIssueCards.length" class="issue-cards-empty">لا توجد تنبيهات تطابق الفلتر الحالي.</p>
        <ul v-else class="issue-cards-list">
          <li
            v-for="(c, ci) in filteredIssueCards"
            :key="'ic' + ci + '-' + c.rowDisplay + '-' + c.fieldKey"
            class="issue-card"
            :class="'issue-card--' + c.severityKey"
          >
            <div class="issue-card-head">
              <span class="issue-card-sev-badge">{{ c.severityLabel }}</span>
              <span class="issue-card-row-num">الصف {{ c.rowDisplay }}</span>
            </div>
            <h4 class="issue-card-headline">{{ c.title }}</h4>
            <p class="issue-card-field-line">العمود الرئيسي: {{ c.fieldLabel }}</p>
            <p v-if="c.confidence != null" class="issue-card-confidence">
              الثقة: {{ Math.round(c.confidence) }}٪
            </p>
            <span class="issue-card-kind-pill">{{ c.kindLabel }}</span>
            <p v-if="c.body && c.body.trim() !== c.title.trim()" class="issue-card-detail">{{ c.body }}</p>
          </li>
        </ul>
      </section>

      <!-- Legend -->
      <div v-if="batchResult" class="legend">
        <span class="legend-item"><span class="legend-dot dot-high"></span> خطأ حرج</span>
        <span class="legend-item"><span class="legend-dot dot-medium"></span> تحذير متوسط</span>
        <span class="legend-item"><span class="legend-dot dot-low"></span> ملاحظة خفيفة</span>
        <span class="legend-tip"
          >تفاصيل الصف من «تفاصيل»؛ للخلية الملوّنة: ⓘ أو نقرتان على الحقل لعرض القاعدة والمقترحات</span
        >
      </div>

      <!-- Table -->
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="th-num">#</th>
              <th
                v-for="col in columns"
                :key="col"
                class="th-col"
                :title="columnHeaderTooltipFromCol(col)"
              >
                <span v-if="columnHeaderByCol[col]?.category" class="th-col-cat">{{
                  columnHeaderByCol[col]!.category
                }}</span>
                <span class="th-col-short">{{ columnHeaderByCol[col]?.shortLabel ?? col }}</span>
              </th>
              <th v-if="batchResult" class="th-details">تفاصيل</th>
              <th v-if="batchResult" class="th-score">درجة الثقة</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.row_index" :class="rowClass(row)">
              <td class="td-num">{{ row.row_index + 1 }}</td>

              <td
                v-for="col in columns"
                :key="col"
                :class="['data-cell', getCellClass(row, col)]"
              >
                <div
                  class="cell-inner"
                  @dblclick="
                    batchResult && getFieldError(row, col) ? openFieldDetail(row, col) : undefined
                  "
                >
                  <button
                    v-if="batchResult && getFieldError(row, col)"
                    type="button"
                    class="cell-rule-trigger"
                    title="تفاصيل القاعدة والمقترحات التصحيحية"
                    aria-label="تفاصيل القاعدة"
                    @click.stop="openFieldDetail(row, col)"
                  >
                    ⓘ
                  </button>
                  <input
                    v-model="row.editableData[col]"
                    type="text"
                    class="cell-input"
                    @dblclick.stop="
                      batchResult && getFieldError(row, col) ? openFieldDetail(row, col) : undefined
                    "
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
      <FieldRuleDetailModal
        :model-value="fieldDetailContext !== null"
        :error="fieldDetailContext?.err ?? null"
        :field-label="fieldDetailContext?.fieldLabel ?? ''"
        :column-key="fieldDetailContext?.col ?? ''"
        :row-display-index="fieldDetailContext ? fieldDetailContext.row.row_index + 1 : 1"
        :rules-by-id="lfsRulesById"
        :row-suggestions="fieldDetailContext?.rowSuggestions ?? []"
        @update:model-value="(v) => !v && closeFieldDetail()"
      />

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

.severity-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (max-width: 520px) {
  .severity-cards {
    grid-template-columns: 1fr;
  }
}
.severity-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 0.85rem 1rem;
  border-radius: 0.65rem;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
}
.severity-card-num {
  font-size: 1.65rem;
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.severity-card-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text);
  opacity: 0.88;
}
.severity-card--high {
  border-color: rgba(239, 68, 68, 0.42);
  background: linear-gradient(180deg, rgba(239, 68, 68, 0.09), var(--color-background-soft));
}
.severity-card--high .severity-card-num {
  color: #ef4444;
}
.severity-card--medium {
  border-color: rgba(245, 158, 11, 0.42);
  background: linear-gradient(180deg, rgba(245, 158, 11, 0.09), var(--color-background-soft));
}
.severity-card--medium .severity-card-num {
  color: #d97706;
}
.severity-card--low {
  border-color: rgba(107, 114, 128, 0.4);
  background: linear-gradient(180deg, rgba(107, 114, 128, 0.1), var(--color-background-soft));
}
.severity-card--low .severity-card-num {
  color: #4b5563;
}

/* تقرير نهاية التحليل */
.batch-insights-section {
  margin-bottom: 1rem;
}
.batch-insights-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--color-background-soft);
  border: 1px dashed var(--color-border);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  color: var(--color-text);
}
.batch-insights-spinner {
  width: 1rem;
  height: 1rem;
  border-width: 2px;
}
.batch-insights-error {
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.35);
  font-size: 0.875rem;
}
.batch-insights-card {
  padding: 1rem 1.15rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.06), rgba(16, 185, 129, 0.05));
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 0.65rem;
}
.batch-insights-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.65rem;
}
.batch-insights-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-heading);
}
.batch-insights-badges {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.tag-insights-fallback {
  font-size: 0.72rem;
  padding: 0.15rem 0.45rem;
  border-radius: 0.35rem;
  background: rgba(100, 116, 139, 0.15);
  color: var(--color-text);
}
.batch-insights-note {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  opacity: 0.85;
}
.batch-insights-summary {
  margin: 0 0 0.85rem;
  font-size: 0.92rem;
  line-height: 1.55;
}
.batch-insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}
.batch-insights-h4 {
  margin: 0 0 0.35rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--color-heading);
}
.batch-insights-body {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
  opacity: 0.92;
}
.batch-insights-priority {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.65rem;
  font-size: 0.82rem;
}
.batch-insights-priority-label {
  font-weight: 600;
  color: var(--color-heading);
}
.batch-insights-chip {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
}
.batch-insights-recs {
  margin: 0 0 0.85rem;
  padding-right: 1.1rem;
  font-size: 0.82rem;
  line-height: 1.55;
}
.batch-insights-table-wrap {
  margin-top: 0.25rem;
}
.batch-insights-table-caption {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
  color: var(--color-heading);
}
.batch-insights-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}
.batch-insights-table th,
.batch-insights-table td {
  border: 1px solid var(--color-border);
  padding: 0.35rem 0.5rem;
  text-align: right;
  vertical-align: top;
}
.batch-insights-table th {
  background: var(--color-background-soft);
  font-weight: 600;
}
.batch-insights-msg-cell {
  max-width: 28rem;
  word-break: break-word;
}

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

.filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-bottom: 0.85rem;
  padding: 0.65rem 0.9rem;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);
  border-radius: 0.55rem;
}
.filter-toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.5rem 0.75rem;
}
.filter-toolbar-label {
  flex: 0 0 auto;
  min-width: 5.5rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--color-heading);
  padding-top: 0.35rem;
}
.filter-btn-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  flex: 1 1 12rem;
}
.filter-btn-group--kind .filter-chip {
  font-size: 0.78rem;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.38rem 0.65rem;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  border-radius: 999px;
  border: 1.5px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.filter-chip:hover {
  background: var(--color-background-soft);
}
.filter-chip--on {
  border-color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
  color: #0e7490;
}
.filter-chip--sev-high.filter-chip--on {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
}
.filter-chip--sev-med.filter-chip--on {
  border-color: #d97706;
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}
.filter-chip--sev-low.filter-chip--on {
  border-color: #6b7280;
  background: rgba(107, 114, 128, 0.12);
  color: #374151;
}
.filter-chip-n {
  font-size: 0.72rem;
  font-weight: 700;
  opacity: 0.85;
  font-variant-numeric: tabular-nums;
}
.filter-toolbar-hint {
  margin: 0;
  font-size: 0.78rem;
  color: var(--color-text);
  opacity: 0.85;
}

/* بطاقات التنبيهات */
.issue-cards-section {
  margin-bottom: 1rem;
}
.issue-cards-title {
  margin: 0 0 0.65rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-heading);
}
.issue-cards-empty {
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: 0.88rem;
  color: var(--color-text);
  opacity: 0.75;
  background: var(--color-background-soft);
  border: 1px dashed var(--color-border);
  border-radius: 0.5rem;
}
.issue-cards-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.issue-card {
  margin: 0;
  padding: 1rem 1.1rem;
  border-radius: 0.65rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  border-right: 4px solid var(--color-border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}
.issue-card--high {
  border-right-color: #ef4444;
  background: linear-gradient(135deg, rgba(254, 242, 242, 0.65), var(--color-background));
}
.issue-card--medium {
  border-right-color: #f59e0b;
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.7), var(--color-background));
}
.issue-card--low {
  border-right-color: #6b7280;
  background: linear-gradient(135deg, rgba(249, 250, 251, 0.9), var(--color-background));
}
.issue-card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
}
.issue-card-sev-badge {
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: none;
  padding: 0.2rem 0.55rem;
  border-radius: 0.35rem;
  background: rgba(15, 23, 42, 0.06);
  color: var(--color-heading);
}
.issue-card--high .issue-card-sev-badge {
  background: rgba(239, 68, 68, 0.14);
  color: #b91c1c;
}
.issue-card--medium .issue-card-sev-badge {
  background: rgba(245, 158, 11, 0.18);
  color: #b45309;
}
.issue-card--low .issue-card-sev-badge {
  background: rgba(107, 114, 128, 0.15);
  color: #374151;
}
.issue-card-row-num {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
  opacity: 0.85;
}
.issue-card-headline {
  margin: 0 0 0.45rem;
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.35;
  color: var(--color-heading);
}
.issue-card-field-line {
  margin: 0 0 0.35rem;
  font-size: 0.82rem;
  color: var(--color-text);
  opacity: 0.88;
}
.issue-card-confidence {
  margin: 0 0 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #0e7490;
}
.issue-card-kind-pill {
  display: inline-block;
  margin-bottom: 0.55rem;
  padding: 0.2rem 0.55rem;
  font-size: 0.74rem;
  font-weight: 600;
  border-radius: 0.35rem;
  background: rgba(99, 102, 241, 0.12);
  color: #4338ca;
  border: 1px solid rgba(99, 102, 241, 0.25);
}
.issue-card-detail {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.55;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}

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
  min-width: 7.5rem;
  max-width: 11rem;
  line-height: 1.3;
}
.th-col-cat {
  display: block;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--color-text);
  opacity: 0.72;
  margin-bottom: 0.2rem;
  line-height: 1.25;
}
.th-col-short {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-heading);
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
.cell-inner:has(.cell-rule-trigger) .cell-input {
  padding-inline-start: 1.5rem;
}
.cell-rule-trigger {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  inset-inline-start: 0.35rem;
  z-index: 2;
  width: 1.35rem;
  height: 1.35rem;
  padding: 0;
  border: none;
  border-radius: 0.25rem;
  background: rgba(59, 130, 246, 0.22);
  color: #1d4ed8;
  font-size: 0.72rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.cell-rule-trigger:hover {
  background: rgba(59, 130, 246, 0.38);
}
.data-cell.cell-error-high .cell-rule-trigger,
.data-cell.cell-error-medium .cell-rule-trigger,
.data-cell.cell-error-low .cell-rule-trigger {
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.06);
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

</style>
