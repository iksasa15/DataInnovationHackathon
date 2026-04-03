<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import iconv from 'iconv-lite'
import FieldRuleDetailModal from '../components/FieldRuleDetailModal.vue'
import { fetchBatchInsightsReport, fetchLfsBusinessRulesCatalog, validateBatchDynamic } from '../services/api'
import { normalizeRowsNullLike } from '../utils/spreadsheetNull'
import { loadLfsMetadataMap } from '../utils/lfsMetadata'
import { resolveLfsTableColumnHeader } from '../utils/lfsTableColumnHeader'
import type { BatchInsightsResponse, BatchResult, LfsBusinessRuleRow, ValidationError } from '../services/api'

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
const insightsReport = ref<BatchInsightsResponse | null>(null)
const insightsLoading = ref(false)
const insightsError = ref<string | null>(null)
const filter = ref<'all' | 'error' | 'warning' | 'valid'>('all')
const uploadError = ref('')
const detailsModalRow = ref<number | null>(null)
const lfsMeta = ref<Record<string, string>>({})
const lfsRulesById = ref<Record<number, LfsBusinessRuleRow>>({})
const fieldDetailTarget = ref<{ rowIndex: number; col: string } | null>(null)

const filteredRows = computed(() => {
  if (filter.value === 'all') return rows.value
  return rows.value.filter((r) => r.validation?.status === filter.value)
})

const stats = computed(() => batchResult.value?.stats ?? null)

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

/** خريطة تفاصيل كل صف (ملخص مشاكل + اقتراحات) */
const rowDetailsMap = computed(() => {
  const m = new Map<number, ReturnType<typeof getRowDetails>>()
  rows.value.forEach((r) => m.set(r.row_index, getRowDetails(r)))
  return m
})

function columnHeaderLabel(tag: string): string {
  const r = resolveLfsTableColumnHeader(tag, lfsMeta.value)
  return r.shortLabel !== r.technicalId ? r.shortLabel : tag
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

onMounted(async () => {
  lfsMeta.value = await loadLfsMetadataMap(import.meta.env.BASE_URL)
  loadLfsRulesCatalog()
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
  // BOM UTF-8: نزيله ونفك بـ UTF-8 (الأصلي في المتصفح)
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    return utf8Decoder.decode(bytes.subarray(3))
  }
  // نجرب UTF-8 أولاً (الأسرع والأدق في المتصفح)
  const utf8Decoded = utf8Decoder.decode(bytes)
  if (/[\u0600-\u06FF]/.test(utf8Decoded) && !/\uFFFD/.test(utf8Decoded)) return utf8Decoded
  // إذا فشل UTF-8 نجرب ترميزات عربية قديمة عبر iconv
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
      /* تجاهل ترميز غير مدعوم */
    }
  }
  return best
}

function processFile(file: File) {
  uploadError.value = ''
  if (!file.name.toLowerCase().endsWith('.csv')) {
    uploadError.value = 'يرجى اختيار ملف CSV فقط (.csv)'
    return
  }
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    const result = e.target?.result
    if (!result) return
    try {
      const decoded = decodeCsvBuffer(result as ArrayBuffer)
      const wb = XLSX.read(decoded, { type: 'string' })
      const firstSheetName = wb.SheetNames[0]
      if (!firstSheetName) {
        uploadError.value = 'الملف لا يحتوي على بيانات'
        return
      }
      const ws = wb.Sheets[firstSheetName]
      if (!ws) return
      const rawRows: Record<string, any>[] = normalizeRowsNullLike(
        XLSX.utils.sheet_to_json(ws, { defval: '' }) as Record<string, any>[],
      )
      if (!rawRows.length || !rawRows[0]) {
        uploadError.value = 'الملف فارغ أو لا يحتوي على أعمدة'
        return
      }
      columns.value = Object.keys(rawRows[0])
      rows.value = rawRows.map((row, i) => ({
        row_index: i,
        originalData: row,
        editableData: { ...row },
        validation: null,
      }))
      batchResult.value = null
      insightsReport.value = null
      insightsError.value = null
      fieldDetailTarget.value = null
      filter.value = 'all'
    } catch (err) {
      uploadError.value = 'تعذر قراءة الملف. تأكد أنه ملف CSV صالح.'
    }
  }
  reader.readAsArrayBuffer(file)
}

async function analyzeAll() {
  if (!rows.value.length || !columns.value.length) return
  isProcessing.value = true
  insightsReport.value = null
  insightsError.value = null
  try {
    const payload = {
      columns: columns.value,
      records: rows.value.map((r) => ({ row_index: r.row_index, ...(r.editableData ?? r.originalData) })),
      mode: 'smart' as const,
    }
    batchResult.value = await validateBatchDynamic(payload)
    const resultMap = new Map(batchResult.value.results.map((r) => [r.row_index, r]))
    rows.value = rows.value.map((r) => ({
      ...r,
      editableData: r.editableData ?? { ...r.originalData },
      validation: resultMap.get(r.row_index) ?? null,
    }))
    await loadInsightsReport()
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
  fieldDetailTarget.value = null
  filter.value = 'all'
  uploadError.value = ''
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
  const baseName = fileName.value.replace(/\.[^.]+$/, '') || 'export'
  const dataRows = rows.value.map((r) => r.editableData ?? r.originalData)
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
  <div class="csv-page">
    <div class="page-head">
      <h1 class="page-title">تحليل ملف CSV</h1>
      <p class="page-desc">
        ارفع ملف CSV (مثل استبيانات أو جداول بيانات) وسيكتشف <strong>الحارس الدلالي</strong> الأخطاء المنطقية ويدعم العربية تلقائياً.
      </p>
    </div>

    <!-- Upload zone -->
    <div v-if="!rows.length" class="upload-zone"
      :class="{ 'dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @drop.prevent="onDrop"
      @dragleave="isDragging = false">
      <div class="upload-icon">📋</div>
      <p class="upload-title">اسحب ملف CSV هنا</p>
      <p class="upload-sub">أو</p>
      <label class="btn btn-primary upload-btn">
        اختر ملف CSV
        <input type="file" accept=".csv" hidden @change="onFileInput" />
      </label>
      <p class="upload-note">يدعم: UTF-8 · Windows-1256 · ISO-8859-6 (عربي)</p>
      <p v-if="uploadError" class="upload-error">{{ uploadError }}</p>
    </div>

    <!-- File loaded: preview + actions -->
    <template v-else>
      <div class="toolbar">
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
            {{ isProcessing ? 'جارٍ التحليل…' : '🔍 تحليل بـ Gemini' }}
          </button>
          <button class="btn btn-download btn-sm" @click="exportFileOnly" title="تحميل الملف المعدّل فقط">
            📥 تحميل الملف
          </button>
          <button class="btn btn-export btn-sm" @click="exportFileAndReport" title="تصدير الملف المعدّل مع التقرير">
            💾 حفظ وتصدير + التقرير
          </button>
        </div>
      </div>

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

      <section v-if="batchResult" class="batch-insights-section" aria-label="تقرير نهاية التحليل">
        <div v-if="insightsLoading" class="batch-insights-loading">
          <span class="btn-spinner batch-insights-spinner" aria-hidden="true"></span>
          جارٍ إعداد تقرير نهاية التحليل…
        </div>
        <div v-else-if="insightsError" class="batch-insights-error" role="alert">
          {{ insightsError }}
        </div>
        <article v-else-if="insightsReport?.report" class="batch-insights-card">
          <header class="batch-insights-head">
            <h3 class="batch-insights-title">تقرير نهاية التحليل</h3>
            <span v-if="insightsReport.provider === 'gemini'" class="tag-gemini">Gemini</span>
            <span v-else class="tag-insights-fallback">تحليل إحصائي</span>
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
            <span v-for="(pf, i) in insightsReport.report.priority_fields_ar" :key="'pf' + i" class="batch-insights-chip">{{
              pf
            }}</span>
          </div>
          <ul v-if="insightsReport.report.recommendations_ar?.length" class="batch-insights-recs">
            <li v-for="(rec, ri) in insightsReport.report.recommendations_ar" :key="'rec' + ri">
              {{ rec }}
            </li>
          </ul>
          <div v-if="insightsReport.aggregates?.most_repeated?.length" class="batch-insights-table-wrap">
            <span class="batch-insights-table-caption">أعلى الأنواع تكراراً</span>
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
                  <td>{{ row.field }}</td>
                  <td>{{ row.count }}</td>
                  <td class="batch-insights-msg-cell">{{ row.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <div v-if="batchResult?.provider" class="provider-notice" :class="batchResult.provider === 'gemini' ? 'provider-ok' : 'provider-local'">
        <span v-if="batchResult.provider === 'gemini'">✓ تم التحليل بـ Gemini</span>
        <span v-else-if="batchResult.provider === 'local'">
          التحليل تم محلياً. لتفعيل التحليل بـ Gemini: أضف <code>GEMINI_API_KEY</code> في ملف <code>.env</code> داخل مجلد <code>backend</code> ثم أعد تشغيل السيرفر.
        </span>
      </div>

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

      <div v-if="batchResult" class="legend">
        <span class="legend-item"><span class="legend-dot dot-high"></span> خطأ حرج</span>
        <span class="legend-item"><span class="legend-dot dot-medium"></span> تحذير متوسط</span>
        <span class="legend-item"><span class="legend-dot dot-low"></span> ملاحظة خفيفة</span>
        <span class="legend-tip"
          >«تفاصيل» للصف؛ للخلية الملوّنة: ⓘ أو نقرتان لعرض القاعدة والمقترحات التصحيحية</span
        >
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="th-num">#</th>
              <th v-for="col in columns" :key="col">{{ col }}</th>
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
.csv-page {
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
.upload-error {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #dc2626;
  font-weight: 500;
}

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

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.6rem;
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

.batch-insights-section { margin-bottom: 1rem; }
.batch-insights-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--color-background-soft);
  border: 1px dashed var(--color-border);
  border-radius: 0.5rem;
  font-size: 0.9rem;
}
.batch-insights-spinner { width: 1rem; height: 1rem; border-width: 2px; }
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
.batch-insights-title { margin: 0; font-size: 1.05rem; font-weight: 700; color: var(--color-heading); }
.tag-insights-fallback {
  font-size: 0.72rem;
  padding: 0.15rem 0.45rem;
  border-radius: 0.35rem;
  background: rgba(100, 116, 139, 0.15);
}
.tag-gemini {
  font-size: 0.72rem;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.2);
  color: #047857;
}
.batch-insights-note { margin: 0 0 0.5rem; font-size: 0.78rem; opacity: 0.85; }
.batch-insights-summary { margin: 0 0 0.85rem; font-size: 0.92rem; line-height: 1.55; }
.batch-insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}
.batch-insights-h4 { margin: 0 0 0.35rem; font-size: 0.82rem; font-weight: 700; color: var(--color-heading); }
.batch-insights-body { margin: 0; font-size: 0.82rem; line-height: 1.5; opacity: 0.92; }
.batch-insights-priority {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.65rem;
  font-size: 0.82rem;
}
.batch-insights-priority-label { font-weight: 600; color: var(--color-heading); }
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
.batch-insights-table-caption {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
  color: var(--color-heading);
}
.batch-insights-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.batch-insights-table th,
.batch-insights-table td {
  border: 1px solid var(--color-border);
  padding: 0.35rem 0.5rem;
  text-align: right;
  vertical-align: top;
}
.batch-insights-table th { background: var(--color-background-soft); font-weight: 600; }
.batch-insights-msg-cell { max-width: 28rem; word-break: break-word; }

.provider-notice {
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}
.provider-notice code { font-family: ui-monospace, monospace; padding: 0.1rem 0.35rem; border-radius: 0.25rem; }
.provider-ok { background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; color: #047857; }
.provider-local { background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; color: #b45309; }

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
}
.data-table thead {
  background: var(--color-background-mute);
  position: sticky;
  top: 0;
  z-index: 2;
}
.data-table th {
  padding: 0.7rem 0.85rem;
  text-align: right;
  font-weight: 600;
  color: var(--color-heading);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  font-size: 0.82rem;
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

.row-error { background: rgba(239,68,68,0.03); }
.row-warning { background: rgba(245,158,11,0.03); }

.data-cell { padding: 0; max-width: 200px; }
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
