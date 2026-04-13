<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
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
import BatchInsightsPanel from '../components/BatchInsightsPanel.vue'
import { fetchBatchInsightsReport, fetchLfsBusinessRulesCatalog, validateBatchDynamic } from '../services/api'
import type {
  BatchInsightsResponse,
  BatchResult,
  LfsBusinessRuleRow,
  ValidationError,
} from '../services/api'
import { LOGO_AIN_SRC } from '../constants/branding'
import {
  buildAnalysisExportReportHtml,
  type AnalysisExportInsightsFull,
} from '../utils/analysisExportReportHtml'
import HomePageIcon from '../components/HomePageIcon.vue'
import type { HomeIconName } from '../components/HomePageIcon.vue'

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
/** تقرير نهاية التحليل (تكرار الأخطاء + نموذج لغوي أو احتياطي إحصائي) */
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

/** قواعد فقط | نموذج لغوي فقط | الاثنان معاً */
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

const ISSUE_CARDS_INITIAL = 5
const issueCardsExpanded = ref(false)
const displayedIssueCards = computed(() => {
  const all = filteredIssueCards.value
  if (issueCardsExpanded.value || all.length <= ISSUE_CARDS_INITIAL) return all
  return all.slice(0, ISSUE_CARDS_INITIAL)
})

watch([severityFilterBtn, issueKindFilterBtn], () => {
  issueCardsExpanded.value = false
})

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
  if (batchResult.value) return 'إعادة التحليل'
  if (analysisEngine.value === 'rules') return 'تحليل بالقواعد'
  if (analysisEngine.value === 'gemini') return 'تحليل بنموذج لغوي'
  return 'تحليل (نموذج لغوي + قواعد)'
})

const analyzeButtonIcon = computed((): HomeIconName | null => {
  if (isProcessing.value) return null
  if (batchResult.value) return 'refresh-cw'
  if (analysisEngine.value === 'rules') return 'settings'
  if (analysisEngine.value === 'gemini') return 'bot'
  return 'search'
})

/** اقتراحات على مستوى الدفعة (فوق الجدول) — بدون قائمة تنبيهات ولا أعداد تحذيرات */
const analysisNotice = computed(() => {
  if (!batchResult.value || isProcessing.value) return null
  const br = batchResult.value
  const st = br.stats
  if (!st) return null

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
  return { suggestions, allClear }
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

const sampleLoading = ref(false)
const SAMPLE_CSV_URL = `${import.meta.env.BASE_URL}lfs-sample-violations.csv`

async function loadSampleFile() {
  sampleLoading.value = true
  analysisError.value = null
  try {
    const res = await fetch(SAMPLE_CSV_URL)
    if (!res.ok) throw new Error('fetch failed')
    const buf = await res.arrayBuffer()
    const file = new File([buf], 'lfs-sample-violations.csv', { type: 'text/csv' })
    processFile(file)
  } catch {
    analysisError.value = 'تعذّر تحميل الملف التجريبي. تأكد من وجود الملف في المشروع.'
  } finally {
    sampleLoading.value = false
  }
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
  if (score >= 80) return '#53cd3f'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}

function buildInsightsFullExport(): AnalysisExportInsightsFull | null {
  const ir = insightsReport.value
  if (!ir?.report) return null
  const agg = ir.aggregates
  const mostRepeatedRows = (agg?.most_repeated ?? []).slice(0, 40).map((r) => ({
    fieldLabel: columnHeaderLabel(r.field),
    count: r.count,
    message: r.message,
  }))
  const topFieldsRows = (agg?.fields_by_errors_desc ?? []).slice(0, 20).map((r) => ({
    fieldLabel: columnHeaderLabel(r.field),
    error_mentions: r.error_mentions,
  }))
  return {
    provider: ir.provider,
    message: ir.message,
    summaryAr: ir.report.summary_ar,
    mostRepeatedInsightsAr: ir.report.most_repeated_insights_ar,
    rareAndIsolatedAr: ir.report.rare_and_isolated_ar,
    leastProblematicFieldsAr: ir.report.least_problematic_fields_ar?.trim() || undefined,
    priorityFieldLabels: (ir.report.priority_fields_ar ?? []).map((f) => columnHeaderLabel(f)),
    total_error_occurrences: agg?.total_error_occurrences,
    unique_error_types: agg?.unique_error_types,
    singleton_count: agg?.singleton_count,
    mostRepeatedRows,
    topFieldsRows,
  }
}

function buildReportHtml(): string {
  const baseName = fileName.value.replace(/\.[^.]+$/, '') || 'export'
  const issueSections: {
    rowNum: number
    statusAr: string
    summary: string
    problems: string[]
  }[] = []
  const noIssuesMessage = 'لا توجد أخطاء أو تحذيرات مرصودة.'
  for (const row of rows.value) {
    if (!row.validation || (row.validation.status === 'valid' && !row.validation.errors?.length)) continue
    const d = getRowDetails(row)
    issueSections.push({
      rowNum: row.row_index + 1,
      statusAr: row.validation.status === 'error' ? 'خطأ' : 'تحذير',
      summary: d.summary ?? row.validation.summary ?? '',
      problems: d.problems,
    })
  }
  return buildAnalysisExportReportHtml({
    documentTitle: `تقرير التحليل — ${baseName}`,
    sourceFileLabel: fileName.value || baseName,
    stats: batchResult.value?.stats ?? null,
    insightsFull: buildInsightsFullExport(),
    issueSections,
    noIssuesMessage,
  })
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
  downloadBlob(new Blob([buildReportHtml()], { type: 'text/html;charset=utf-8' }), `${baseName}_تقرير.html`)
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
    <header class="page-hero">
      <div class="page-kicker-row">
        <span class="page-kicker-logo-chip" aria-hidden="true">
          <img :src="LOGO_AIN_SRC" alt="" width="28" height="28" decoding="async" />
        </span>
        <span class="page-kicker">منصة عين — تحليل الملف الجدولي</span>
      </div>
      <h1 class="page-title">تحليل الملف</h1>
      <p class="page-desc">
        ارفع ملف Excel أو CSV، ثم اختر <strong>نوع التحليل</strong> (قواعد الأعمال، نموذج لغوي، أو الاثنين معاً) واضغط
        <strong>تحليل</strong>. يُلوّن الخلايا ويُظهر التنبيهات. الملاحظات بالعربية حتى لو كانت البيانات بالإنجليزية.
      </p>
    </header>

    <!-- Upload zone: خانة واحدة لـ Excel و CSV -->
    <div v-if="!rows.length" class="upload-zone"
      :class="{ 'dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop">
      <div class="upload-icon" aria-hidden="true">
        <HomePageIcon name="folder" :size="44" />
      </div>
      <p class="upload-title">اسحب ملف Excel أو CSV هنا</p>
      <p class="upload-sub">أو</p>
      <div class="upload-actions">
        <label class="btn btn-primary upload-btn">
          اختر ملفاً
          <input type="file" accept=".xlsx,.xls,.csv" hidden @change="onFileInput" />
        </label>
        <button
          type="button"
          class="btn btn-outline upload-sample"
          :disabled="sampleLoading"
          @click="loadSampleFile"
        >
          <span v-if="sampleLoading" class="btn-spinner btn-spinner--muted" />
          <HomePageIcon v-if="!sampleLoading" name="file-text" :size="16" class="btn-inline-icon" />
          {{ sampleLoading ? 'جارٍ التحميل…' : 'ملف تجريبي جاهز (تعارضات LFS)' }}
        </button>
      </div>
      <p class="upload-note">يقبل: (xlsx · xls) Excel و CSV — البيانات بالإنجليزي أو العربي</p>
    </div>

    <!-- File loaded: preview + actions -->
    <template v-else>
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-main">
          <div class="file-info">
            <span class="file-icon" aria-hidden="true">
              <HomePageIcon name="file-text" :size="18" />
            </span>
            <span class="file-name">{{ fileName }}</span>
            <span class="file-rows">{{ rows.length }} سجل</span>
          </div>
          <div class="toolbar-actions">
            <button class="btn btn-ghost btn-sm" @click="resetFile">تغيير الملف</button>
            <button
              class="btn btn-primary btn-sm"
              :disabled="isProcessing"
              @click="analyzeAll"
            >
              <span v-if="isProcessing" class="btn-spinner"></span>
              <HomePageIcon
                v-else-if="analyzeButtonIcon"
                :name="analyzeButtonIcon"
                :size="16"
                class="btn-inline-icon"
              />
              {{ analyzeButtonLabel }}
            </button>
            <button class="btn btn-download btn-sm" @click="exportFileOnly" title="تحميل الملف المعدّل فقط">
              <HomePageIcon name="download" :size="16" class="btn-inline-icon" />
              تحميل الملف
            </button>
            <button
              class="btn btn-export btn-sm"
              @click="exportFileAndReport"
              title="تصدير الملف المعدّل مع تقرير HTML بنفس هوية المنصة"
            >
              <HomePageIcon name="save" :size="16" class="btn-inline-icon" />
              حفظ وتصدير + التقرير
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
              نموذج لغوي
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
          <span class="severity-card-label">حرجة</span>
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

      <BatchInsightsPanel
        v-if="batchResult"
        :insights-loading="insightsLoading"
        :insights-error="insightsError"
        :insights-report="insightsReport"
        :batch-stats="batchResult.stats"
        :column-label="columnHeaderLabel"
      />

      <div
        v-if="batchResult?.provider"
        class="provider-notice"
        :class="{
          'provider-ok': batchResult.provider === 'gemini',
          'provider-rules': batchResult.provider === 'rules',
          'provider-local': batchResult.provider === 'local',
        }"
      >
        <span v-if="batchResult.provider === 'gemini'" class="provider-line">
          <HomePageIcon name="circle-check" :size="16" class="provider-line-icon" />
          تم التحليل بنموذج لغوي
        </span>
        <span v-else-if="batchResult.provider === 'rules'" class="provider-line">
          <HomePageIcon name="circle-check" :size="16" class="provider-line-icon" />
          تم التحليل بـ <strong>قواعد الأعمال</strong> فقط (LFS Business Rules) — دون استدعاء النموذج اللغوي.
        </span>
        <span v-else-if="batchResult.provider === 'local'">
          التحليل تم محلياً. لتفعيل النموذج اللغوي: أضف <code>GEMINI_API_KEY</code> (أو مفتاح المزوّد المفعّل) في ملف
          <code>.env</code> داخل مجلد <code>backend</code> ثم أعد تشغيل السيرفر.
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
        <template v-else>
          <div class="issue-cards-layout">
            <ul class="issue-cards-list">
              <li
                v-for="(c, ci) in displayedIssueCards"
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
            <button
              v-if="filteredIssueCards.length > ISSUE_CARDS_INITIAL"
              type="button"
              class="issue-cards-more-btn"
              :aria-expanded="issueCardsExpanded"
              @click="issueCardsExpanded = !issueCardsExpanded"
            >
              {{ issueCardsExpanded ? 'عرض أقل' : 'المزيد' }}
            </button>
          </div>
        </template>
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

      <!-- اقتراحات (فوق الجدول) -->
      <div
        v-if="analysisNotice && analysisNotice.suggestions.length > 0"
        class="analysis-notice-card analysis-notice-card--suggestions-only"
        role="status"
      >
        <div class="analysis-notice-head">
          <span class="analysis-notice-icon" aria-hidden="true">
            <HomePageIcon name="lightbulb" :size="22" />
          </span>
          <div>
            <h3 class="analysis-notice-title">اقتراحات</h3>
            <p v-if="batchResult?.provider" class="analysis-notice-meta">
              <span v-if="batchResult.provider === 'gemini'" class="tag-gemini">نموذج لغوي</span>
              <span v-else-if="batchResult.provider === 'rules'" class="tag-rules">قواعد فقط</span>
              <span v-else-if="batchResult.provider === 'local'" class="tag-local">تحقق محلي + قواعد</span>
            </p>
          </div>
        </div>
        <ul class="analysis-notice-suggestions">
          <li
            v-for="(sg, sgi) in analysisNotice.suggestions"
            :key="'sg' + sgi"
            class="suggestion-li"
          >
            {{ sg }}
          </li>
        </ul>
      </div>

      <div v-else-if="analysisNotice && analysisNotice.allClear" class="analysis-notice-ok" role="status">
        <span class="ok-icon" aria-hidden="true">
          <HomePageIcon name="circle-check" :size="22" />
        </span>
        <div>
          <strong>لم يُرصد خطأ أو تحذير في الدفعة</strong>
          <p class="ok-sub">يمكنك مراجعة الجدول أو تصدير التقرير إن رغبت.</p>
        </div>
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
  --ex-purple: var(--ga-primary);
  --ex-purple-mid: var(--ga-primary-mid);
  --ex-purple-soft: var(--ga-primary-soft);
  --ex-surface: var(--ga-surface);
  --ex-card: #ffffff;

  max-width: 1320px;
  margin: 0 auto;
  padding: 1.25rem 1rem 4rem;
  font-family: var(--font-app);
  background: var(--ex-surface);
}

@media (min-width: 900px) {
  .excel-page {
    padding: 1.5rem 1.25rem 4.5rem;
  }
}

.page-hero {
  position: relative;
  background: var(--ex-card);
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1.35rem 1.35rem 1.25rem;
  margin-bottom: 1.35rem;
  box-shadow: 0 8px 32px rgba(45, 38, 117, 0.08);
  overflow: hidden;
}
.page-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--ex-purple), var(--ga-green));
  border-radius: 1rem 1rem 0 0;
}

.page-kicker-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.65rem;
}

.page-kicker-logo-chip {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.45rem;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  padding: 0.15rem;
  box-sizing: border-box;
}

.page-kicker-logo-chip img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.page-kicker {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ex-purple);
  background: var(--ex-purple-soft);
}

.page-title {
  font-size: clamp(1.35rem, 2.5vw, 1.85rem);
  font-weight: 800;
  color: var(--ex-purple);
  margin: 0 0 0.5rem;
  line-height: 1.35;
}

.page-desc {
  margin: 0;
  color: #475569;
  font-size: 0.92rem;
  line-height: 1.7;
  max-width: 52rem;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed #c4b8e0;
  border-radius: 1rem;
  padding: 3.25rem 1.5rem;
  text-align: center;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  cursor: default;
  background: #faf9fc;
}
.upload-zone.dragging {
  border-color: var(--ex-purple-mid);
  background: rgba(63, 61, 145, 0.06);
  box-shadow: inset 0 0 0 1px rgba(63, 61, 145, 0.12);
}
.upload-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.85rem;
  color: var(--ex-purple-mid);
  opacity: 0.9;
}
.btn-inline-icon {
  display: inline-flex;
  flex-shrink: 0;
  vertical-align: middle;
}
.provider-line {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.provider-line-icon {
  flex-shrink: 0;
  color: currentColor;
}
.upload-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.35rem;
}
.upload-sub {
  color: #94a3b8;
  margin-bottom: 0.85rem;
  font-size: 0.9rem;
}
.upload-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
  justify-content: center;
}
.upload-btn {
  cursor: pointer;
}
.upload-note {
  margin-top: 1rem;
  font-size: 0.78rem;
  color: #94a3b8;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.7rem 1.35rem;
  font-size: 0.9rem;
  font-weight: 700;
  border-radius: 0.55rem;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  font-family: inherit;
  text-decoration: none;
}
.btn-primary {
  background: linear-gradient(135deg, var(--ex-purple) 0%, var(--ex-purple-mid) 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(45, 38, 117, 0.3);
}
.btn-primary:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.btn-outline {
  background: #fff;
  color: var(--ex-purple-mid);
  border-color: #c4b8e0;
}
.btn-outline:hover:not(:disabled) {
  border-color: var(--ex-purple-mid);
  background: #faf9fc;
}
.btn-outline:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn-ghost {
  background: #fff;
  color: #334155;
  border-color: #d1d5db;
}
.btn-ghost:hover {
  background: #f8fafc;
  border-color: var(--ex-purple-mid);
  color: var(--ex-purple);
}
.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.82rem;
}
.btn-spinner {
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.btn-spinner--muted {
  border-color: #e2e8f0;
  border-top-color: var(--ex-purple-mid);
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Toolbar */
.toolbar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.15rem;
  padding: 1rem 1.15rem;
  background: var(--ex-card);
  border: 1px solid #e8e8ef;
  border-radius: 0.9rem;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
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
  font-weight: 700;
  color: var(--ex-purple);
}
.engine-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}
.engine-btn {
  padding: 0.45rem 0.95rem;
  font-size: 0.78rem;
  font-weight: 600;
  font-family: inherit;
  border: 1.5px solid #d8d4e8;
  border-radius: 0.5rem;
  background: #faf9fc;
  color: #4338ca;
  cursor: pointer;
  transition:
    background 0.15s,
    border-color 0.15s,
    color 0.15s,
    box-shadow 0.15s;
}
.engine-btn:hover:not(:disabled) {
  background: #fff;
  border-color: var(--ex-purple-mid);
}
.engine-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.engine-btn-active {
  background: linear-gradient(135deg, var(--ex-purple) 0%, var(--ex-purple-mid) 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 3px 12px rgba(45, 38, 117, 0.3);
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
.analysis-notice-card--suggestions-only {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.07), rgba(139, 92, 246, 0.05));
  border-color: rgba(99, 102, 241, 0.32);
}
.analysis-notice-head {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}
.analysis-notice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #6366f1;
}
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
  background: rgba(91, 33, 182, 0.12);
  color: #5b21b6;
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
  margin: 0.35rem 0 0;
  padding-right: 1rem;
  list-style: none;
  font-size: 0.82rem;
  color: #5b21b6;
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
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #059669;
}
.ok-sub {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  font-weight: 400;
  color: var(--color-text);
  opacity: 0.85;
}
.file-info { display: flex; align-items: center; gap: 0.5rem; }
.file-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ex-purple-mid);
}
.file-name { font-weight: 600; color: var(--color-heading); font-size: 0.95rem; }
.file-rows {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ex-purple);
  background: var(--ex-purple-soft);
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  border: 1px solid rgba(63, 61, 145, 0.15);
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
  background: var(--ex-card);
  border: 1px solid #e8e8ef;
  border-radius: 0.75rem;
  padding: 0.9rem 1rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
  border-top: 3px solid #cbd5e1;
}
.stat-total {
  border-top-color: var(--ex-purple-mid);
}
.stat-num {
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  font-size: 0.74rem;
  font-weight: 600;
  color: #64748b;
}
.stat-total .stat-num {
  color: var(--ex-purple);
}
.stat-error {
  border-top-color: #ef4444;
}
.stat-error .stat-num {
  color: #ef4444;
}
.stat-warning {
  border-top-color: #f59e0b;
}
.stat-warning .stat-num {
  color: #f59e0b;
}
.stat-valid {
  border-top-color: #10b981;
}
.stat-valid .stat-num {
  color: var(--ga-green);
}
.stat-avg {
  border-top-color: var(--ga-cyan);
}

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
  border-color: rgba(37, 99, 235, 0.35);
  background: linear-gradient(180deg, rgba(219, 234, 254, 0.55), #fafbfc);
}
.severity-card--low .severity-card-num {
  color: #2563eb;
}

/* Provider notice (نموذج لغوي vs محلي) */
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
.tab-active {
  background: var(--ex-purple-soft);
  border-color: var(--ex-purple-mid);
  color: var(--ex-purple);
  font-weight: 700;
}
.tab-error.tab-active { border-color: #ef4444; color: #ef4444; }
.tab-warning.tab-active { border-color: #f59e0b; color: #f59e0b; }
.tab-valid.tab-active { border-color: #10b981; color: #10b981; }

.filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-bottom: 0.85rem;
  padding: 0.85rem 1rem;
  background: #eef2ff;
  border: 1px solid #e0e7ff;
  border-radius: 0.75rem;
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
  border-color: var(--ex-purple-mid);
  background: var(--ex-purple-soft);
  color: var(--ex-purple);
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
.issue-cards-layout {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0.65rem;
  border-radius: 0.65rem;
  border: 1px solid rgba(99, 102, 241, 0.12);
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.04), transparent 48%);
}
.issue-cards-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.65rem;
  align-items: stretch;
}
@media (max-width: 1100px) {
  .issue-cards-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 720px) {
  .issue-cards-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 420px) {
  .issue-cards-list {
    grid-template-columns: 1fr;
  }
}
.issue-cards-more-btn {
  display: block;
  width: 100%;
  margin-top: 0;
  padding: 0.45rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: inherit;
  color: var(--ga-primary-dark);
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 0.45rem;
  cursor: pointer;
  text-align: center;
}
.issue-cards-more-btn:hover {
  background: rgba(99, 102, 241, 0.14);
}
.issue-card {
  margin: 0;
  padding: 0.75rem 0.85rem;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 0.55rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  border-right: 4px solid var(--color-border);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.07);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.issue-card:hover {
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.1);
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
  font-size: 0.86rem;
  font-weight: 700;
  line-height: 1.4;
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
  color: #2563eb;
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
.dot-low {
  background: rgba(99, 102, 241, 0.2);
  border: 1.5px solid #6366f1;
}
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
  background: linear-gradient(90deg, var(--ex-purple) 0%, var(--ex-purple-mid) 100%);
  position: sticky;
  top: 0;
  z-index: 2;
}
.data-table th {
  padding: 0.75rem 0.8rem;
  text-align: right;
  font-weight: 700;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 0.8rem;
  vertical-align: top;
  background: transparent;
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
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  margin-bottom: 0.2rem;
  line-height: 1.25;
}
.th-col-short {
  display: block;
  font-size: 0.78rem;
  font-weight: 800;
  color: #fff;
}
.th-num,
.td-num {
  text-align: center;
  width: 44px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.76rem;
}
.data-table tbody .td-num {
  color: var(--color-text);
  opacity: 0.45;
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
  font-weight: 600;
  color: var(--ex-purple);
  background: var(--ex-purple-soft);
  border: 1px solid rgba(63, 61, 145, 0.35);
  border-radius: 0.4rem;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s, border-color 0.2s;
}
.btn-details:hover {
  background: rgba(91, 33, 182, 0.14);
  border-color: var(--ex-purple-mid);
}
.btn-details.has-issues { color: #b45309; background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.4); }
.btn-details.has-issues:hover { background: rgba(245, 158, 11, 0.2); }
.details-ok { color: #047857; font-weight: 500; margin: 0 0 0.5rem 0; }
.details-summary { margin: 0 0 0.5rem 0; color: var(--color-text); opacity: 0.9; line-height: 1.5; }
.details-block { margin-top: 0.75rem; }
.details-block:first-of-type { margin-top: 0; }
.details-label { display: block; font-size: 0.75rem; color: var(--color-heading); margin-bottom: 0.25rem; }
.details-list { margin: 0; padding-right: 1.25rem; list-style: disc; }
.details-list li { margin-bottom: 0.25rem; }
.details-suggestions {
  color: #047857;
}
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
  border-bottom: 1px solid #e8e8ef;
  background: linear-gradient(90deg, var(--ex-purple) 0%, var(--ex-purple-mid) 100%);
}
.details-modal-head h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  color: #fff;
}
.details-modal-close {
  width: 28px;
  height: 28px;
  padding: 0;
  font-size: 1.25rem;
  line-height: 1;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.details-modal-close:hover {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}
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
  border-color: var(--ex-purple-mid);
  background: var(--color-background);
  box-shadow: 0 0 0 2px rgba(63, 61, 145, 0.12);
}
.btn-download {
  background: var(--color-background-mute);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
.btn-download:hover { background: var(--color-background-soft); }
.btn-export {
  background: var(--ga-green-dark);
  color: #fff;
  border: none;
}
.btn-export:hover {
  background: #35962a;
}
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
