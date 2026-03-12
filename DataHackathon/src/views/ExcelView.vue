<script setup lang="ts">
import { ref, computed } from 'vue'
import * as XLSX from 'xlsx'
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
  validation: (ValidationResult & { row_index: number }) | null
}

const isDragging = ref(false)
const isProcessing = ref(false)
const fileName = ref('')
const columns = ref<string[]>([])
const rows = ref<RowData[]>([])
const batchResult = ref<BatchResult | null>(null)
const filter = ref<'all' | 'error' | 'warning' | 'valid'>('all')
const analysisMode = ref<'smart' | 'fast'>('smart')

const filteredRows = computed(() => {
  if (filter.value === 'all') return rows.value
  return rows.value.filter((r) => r.validation?.status === filter.value)
})

const stats = computed(() => batchResult.value?.stats ?? null)

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
  const arabicMatches = text.match(/[\u0600-\u06FF]/g)?.length ?? 0
  const mojibakeMatches = text.match(/[ØÙÃÂ]/g)?.length ?? 0
  return arabicMatches - mojibakeMatches * 3
}

function decodeCsvBuffer(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  const candidates = ['utf-8', 'windows-1256', 'iso-8859-6']
  let best = ''
  let bestScore = Number.NEGATIVE_INFINITY

  for (const encoding of candidates) {
    try {
      const decoded = new TextDecoder(encoding).decode(bytes)
      const score = scoreArabicQuality(decoded)
      if (score > bestScore) {
        best = decoded
        bestScore = score
      }
    } catch {
      // Skip unsupported encodings in some browsers.
    }
  }

  if (best) return best
  return new TextDecoder('utf-8').decode(bytes)
}

function parseWorkbook(data: ArrayBuffer, isCsv: boolean) {
  if (isCsv) {
    const decodedCsv = decodeCsvBuffer(data)
    return XLSX.read(decodedCsv, { type: 'string' })
  }
  return XLSX.read(new Uint8Array(data), { type: 'array' })
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

    columns.value = Object.keys(rawRows[0])
    rows.value = rawRows.map((row, i) => ({
      row_index: i,
      originalData: row,
      validation: null,
    }))

    batchResult.value = null
    filter.value = 'all'
  }

  reader.readAsArrayBuffer(file)
}

async function analyzeAll() {
  if (!rows.value.length || !columns.value.length) return
  isProcessing.value = true
  try {
    const payload = {
      columns: columns.value,
      records: rows.value.map((r) => ({ row_index: r.row_index, ...r.originalData })),
      mode: analysisMode.value,
    }

    batchResult.value = await validateBatchDynamic(payload)

    const resultMap = new Map(batchResult.value.results.map((r) => [r.row_index, r]))
    rows.value = rows.value.map((r) => ({
      ...r,
      validation: resultMap.get(r.row_index) ?? null,
    }))
  } finally {
    isProcessing.value = false
  }
}

function resetFile() {
  fileName.value = ''
  columns.value = []
  rows.value = []
  batchResult.value = null
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
</script>

<template>
  <div class="excel-page">
    <div class="page-head">
      <h1 class="page-title">تحليل ملف Excel</h1>
      <p class="page-desc">
        ارفع ملف استبيان وسيكتشف <strong>الحارس الدلالي</strong> الأخطاء المنطقية ويلوّن الخلايا المشبوهة تلقائياً.
      </p>
    </div>

    <!-- Upload zone -->
    <div v-if="!rows.length" class="upload-zone"
      :class="{ 'dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop">
      <div class="upload-icon">📂</div>
      <p class="upload-title">اسحب ملف Excel هنا</p>
      <p class="upload-sub">أو</p>
      <label class="btn btn-primary upload-btn">
        اختر ملفاً
        <input type="file" accept=".xlsx,.xls,.csv" hidden @change="onFileInput" />
      </label>
      <p class="upload-note">يدعم: xlsx · xls · csv</p>
    </div>

    <!-- File loaded: preview + actions -->
    <template v-else>
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="file-info">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ fileName }}</span>
          <span class="file-rows">{{ rows.length }} سجل</span>
        </div>
        <div class="toolbar-actions">
          <div class="mode-switch" role="group" aria-label="وضع التحليل">
            <button
              class="mode-btn"
              :class="analysisMode === 'smart' && 'mode-btn-active'"
              type="button"
              @click="analysisMode = 'smart'"
            >🧠 ذكي (Gemini)</button>
            <button
              class="mode-btn"
              :class="analysisMode === 'fast' && 'mode-btn-active'"
              type="button"
              @click="analysisMode = 'fast'"
            >⚡ سريع (محلي)</button>
          </div>
          <button class="btn btn-ghost btn-sm" @click="resetFile">تغيير الملف</button>
          <button
            class="btn btn-primary btn-sm"
            :disabled="isProcessing"
            @click="analyzeAll">
            <span v-if="isProcessing" class="btn-spinner"></span>
            {{ isProcessing ? 'جارٍ التحليل…' : analysisMode === 'smart' ? '🔍 تحليل ذكي' : '🔍 تحليل سريع' }}
          </button>
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
        <span class="legend-tip">🖱 مرّر على الخلية الملوّنة لمعرفة السبب</span>
      </div>

      <!-- Table -->
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="th-num">#</th>
              <th v-for="col in columns" :key="col">{{ col }}</th>
              <th v-if="batchResult" class="th-score">درجة الثقة</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.row_index" :class="rowClass(row)">
              <td class="td-num">{{ row.row_index + 1 }}</td>

              <td v-for="col in columns" :key="col"
                :class="['data-cell', getCellClass(row, col)]">
                <div class="cell-inner">
                  <span class="cell-val">{{ row.originalData[col] }}</span>
                  <!-- Tooltip -->
                  <span v-if="getFieldError(row, col)" class="error-badge">!</span>
                  <div v-if="getFieldError(row, col)" class="tooltip-box">
                    <div class="tooltip-sev" :class="`sev-${getFieldError(row, col)!.severity}`">
                      {{ getFieldError(row, col)!.severity === 'high' ? 'حرج' : getFieldError(row, col)!.severity === 'medium' ? 'متوسط' : 'خفيف' }}
                    </div>
                    {{ getFieldError(row, col)!.message }}
                  </div>
                </div>
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

.mode-switch {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-background);
}

.mode-btn {
  border: none;
  background: transparent;
  color: var(--color-text);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.45rem 0.7rem;
  cursor: pointer;
  font-family: inherit;
}

.mode-btn + .mode-btn {
  border-right: 1px solid var(--color-border);
}

.mode-btn:hover {
  background: var(--color-background-mute);
}

.mode-btn-active {
  color: #0e7490;
  background: rgba(6, 182, 212, 0.1);
}

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
.th-score, .td-score { text-align: center; width: 90px; }

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
  max-width: 200px;
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
