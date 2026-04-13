<script setup lang="ts">
import { computed, ref } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
} from 'chart.js'
import type { ChartData, ChartOptions } from 'chart.js'
import type { BatchErrorFrequencyItem, BatchInsightsResponse, BatchStats } from '../services/api'

interface MostRepeatedFieldGroup {
  field: string
  fieldLabel: string
  rows: BatchErrorFrequencyItem[]
  totalCount: number
}

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale, LinearScale, BarElement)
ChartJS.defaults.font.family = "'Frutiger LT Arabic', 'Segoe UI', system-ui, sans-serif"

const props = defineProps<{
  insightsLoading: boolean
  insightsError: string | null
  /** يبقى null حتى يكتمل الطلب */
  insightsReport: BatchInsightsResponse | null
  batchStats: BatchStats | null
  columnLabel: (field: string) => string
}>()

const agg = computed(() => props.insightsReport?.aggregates)

const statusDonutData = computed<ChartData<'doughnut'>>(() => {
  const s = props.batchStats
  const v = s?.valid ?? 0
  const w = s?.warnings ?? 0
  const e = s?.errors ?? 0
  return {
    labels: ['سليمة', 'تحذير', 'خطأ'],
    datasets: [
      {
        data: [v, w, e],
        backgroundColor: ['#53cd3f', '#f59e0b', '#ef4444'],
        borderWidth: 0,
        hoverOffset: 4,
      },
    ],
  }
})

const statusDonutOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      rtl: true,
      labels: { boxWidth: 12, padding: 12, font: { size: 11 } },
    },
    tooltip: {
      rtl: true,
      callbacks: {
        label: (ctx) => ` ${ctx.label}: ${ctx.raw} سجل`,
      },
    },
  },
}))

const topFieldsBarData = computed<ChartData<'bar'>>(() => {
  const rows = agg.value?.fields_by_errors_desc?.slice(0, 12) ?? []
  return {
    labels: rows.map((r) => abbrevLabel(props.columnLabel(r.field), 42)),
    datasets: [
      {
        label: 'عدد إشارات الخطأ',
        data: rows.map((r) => r.error_mentions),
        backgroundColor: '#4137a8',
        borderRadius: 6,
        maxBarThickness: 22,
      },
    ],
  }
})

const barOptions = computed<ChartOptions<'bar'>>(() => ({
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  layout: {
    padding: { left: 2, right: 6, top: 4, bottom: 4 },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      rtl: true,
      bodyAlign: 'right',
      titleAlign: 'right',
      callbacks: {
        title: (items) => {
          const i = items[0]?.dataIndex ?? 0
          const rows = agg.value?.fields_by_errors_desc?.slice(0, 12) ?? []
          const r = rows[i]
          return r ? props.columnLabel(r.field) : ''
        },
        label: (ctx) => ` ${ctx.parsed.x} إشارة`,
      },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: { stepSize: 1, font: { size: 10 } },
      grid: { color: 'rgba(15, 23, 42, 0.06)' },
    },
    y: {
      ticks: { font: { size: 10 }, maxWidth: 140 },
      grid: { display: false },
    },
  },
}))

function abbrevLabel(s: string, max: number): string {
  const t = s.replace(/\s+/g, ' ').trim()
  if (t.length <= max) return t
  return t.slice(0, max - 1) + '…'
}

const showStatusChart = computed(() => {
  const s = props.batchStats
  if (!s) return false
  return (s.valid ?? 0) + (s.warnings ?? 0) + (s.errors ?? 0) > 0
})

const showFieldCharts = computed(() => {
  const a = agg.value
  return (a?.fields_by_errors_desc?.length ?? 0) > 0
})

const showAnyChart = computed(() => showStatusChart.value || showFieldCharts.value)
const chartsSideBySide = computed(() => showStatusChart.value && showFieldCharts.value)

/** تجميع أعلى التكرار حسب الحقل (نفس الصفوف الـ14) — الحقل الواحد مع رسائله معاً */
const mostRepeatedFieldGroups = computed((): MostRepeatedFieldGroup[] => {
  const raw = agg.value?.most_repeated?.slice(0, 14) ?? []
  if (!raw.length) return []
  const map = new Map<string, BatchErrorFrequencyItem[]>()
  for (const item of raw) {
    const list = map.get(item.field) ?? []
    list.push(item)
    map.set(item.field, list)
  }
  const groups: MostRepeatedFieldGroup[] = []
  for (const [field, rows] of map) {
    rows.sort((a, b) => b.count - a.count || a.message.localeCompare(b.message, 'ar'))
    const totalCount = rows.reduce((s, r) => s + r.count, 0)
    groups.push({
      field,
      fieldLabel: props.columnLabel(field),
      rows,
      totalCount,
    })
  }
  groups.sort((a, b) => b.totalCount - a.totalCount || a.field.localeCompare(b.field, 'ar'))
  return groups
})

/** صفوف الجدول المفتوحة (حقل → تفاصيل الرسائل) */
const freqRowOpen = ref<Record<string, boolean>>({})

function toggleFreqField(field: string) {
  freqRowOpen.value = { ...freqRowOpen.value, [field]: !freqRowOpen.value[field] }
}

function isFreqOpen(field: string): boolean {
  return !!freqRowOpen.value[field]
}
</script>

<template>
  <section class="batch-insights-section" aria-label="تقرير نهاية التحليل">
    <div v-if="insightsLoading" class="batch-insights-loading">
      <span class="batch-insights-spinner" aria-hidden="true"></span>
      جارٍ إعداد تقرير نهاية التحليل (ملخص، رسوم، وتوصيات)…
    </div>
    <div v-else-if="insightsError" class="batch-insights-error" role="alert">
      {{ insightsError }}
    </div>
    <article v-else-if="insightsReport?.report" class="batch-insights-article">
      <header class="batch-insights-head">
        <h3 class="batch-insights-title">تقرير نهاية التحليل</h3>
        <div class="batch-insights-badges">
          <span v-if="insightsReport.provider === 'gemini'" class="tag-gemini">نموذج لغوي</span>
          <span v-else class="tag-insights-fallback">تحليل إحصائي</span>
        </div>
      </header>

      <p v-if="insightsReport.message" class="batch-insights-note">{{ insightsReport.message }}</p>

      <!-- ملخص تنفيذي -->
      <div class="summary-callout">
        <span class="summary-callout-icon" aria-hidden="true">📊</span>
        <div class="summary-callout-body">
          <p class="summary-callout-text">{{ insightsReport.report.summary_ar }}</p>
          <div v-if="agg || batchStats" class="summary-metrics">
            <span v-if="batchStats != null" class="summary-metric">
              متوسط الثقة: <strong>{{ Math.round(batchStats.avg_confidence) }}٪</strong>
            </span>
            <span v-if="agg?.total_error_occurrences != null" class="summary-metric">
              إجمالي إشارات الخطأ: <strong>{{ agg.total_error_occurrences }}</strong>
            </span>
            <span v-if="agg?.unique_error_types != null" class="summary-metric">
              أنواع مميزة (حقل+رسالة): <strong>{{ agg.unique_error_types }}</strong>
            </span>
            <span v-if="agg?.singleton_count != null" class="summary-metric">
              أخطاء «مرة واحدة»: <strong>{{ agg.singleton_count }}</strong>
            </span>
          </div>
        </div>
      </div>

      <!-- الرسمان معاً في إطار واحد بلا فراغ يفصلهما -->
      <div v-if="batchStats && showAnyChart" class="insights-charts-wrap">
        <div v-if="chartsSideBySide" class="insights-charts-pair">
          <div class="insights-chart-segment insights-chart-segment--bar">
            <h4 class="insights-chart-h4">أكثر الحقول تكراراً للخطأ</h4>
            <div class="insights-chart-inner insights-chart-inner--bar">
              <Bar :data="topFieldsBarData" :options="barOptions" />
            </div>
          </div>
          <div class="insights-charts-divider" aria-hidden="true" />
          <div class="insights-chart-segment insights-chart-segment--donut">
            <h4 class="insights-chart-h4">توزيع حالة الصفوف</h4>
            <div class="insights-chart-inner insights-chart-inner--donut">
              <Doughnut :data="statusDonutData" :options="statusDonutOptions" />
            </div>
            <p class="insights-chart-caption">سليمة / تحذير / خطأ — حسب نتيجة التحقق لكل سجل</p>
          </div>
        </div>
        <div v-else class="insights-charts-row">
          <div v-if="showFieldCharts" class="insights-chart-card">
            <h4 class="insights-chart-h4">أكثر الحقول تكراراً للخطأ</h4>
            <div class="insights-chart-inner insights-chart-inner--bar">
              <Bar :data="topFieldsBarData" :options="barOptions" />
            </div>
          </div>
          <div v-if="showStatusChart" class="insights-chart-card insights-chart-card--donut">
            <h4 class="insights-chart-h4">توزيع حالة الصفوف</h4>
            <div class="insights-chart-inner insights-chart-inner--donut">
              <Doughnut :data="statusDonutData" :options="statusDonutOptions" />
            </div>
            <p class="insights-chart-caption">سليمة / تحذير / خطأ — حسب نتيجة التحقق لكل سجل</p>
          </div>
        </div>
      </div>

      <!-- نصوص تحليلية -->
      <div class="batch-insights-grid">
        <div class="batch-insights-block">
          <h4 class="batch-insights-h4">الأخطاء الأكثر تكراراً</h4>
          <p class="batch-insights-body">{{ insightsReport.report.most_repeated_insights_ar }}</p>
        </div>
        <div class="batch-insights-block">
          <h4 class="batch-insights-h4">أخطاء نادرة أو معزولة</h4>
          <p class="batch-insights-body">{{ insightsReport.report.rare_and_isolated_ar }}</p>
        </div>
      </div>

      <div v-if="insightsReport.report.priority_fields_ar?.length" class="batch-insights-priority">
        <span class="batch-insights-priority-label">أولوية المراجعة</span>
        <span
          v-for="(pf, i) in insightsReport.report.priority_fields_ar"
          :key="'pf' + i"
          class="batch-insights-chip"
        >
          {{ columnLabel(pf) }}
        </span>
      </div>

      <!-- توصيات -->
      <div v-if="insightsReport.report.recommendations_ar?.length" class="insights-recs-section">
        <h4 class="insights-recs-title">اقتراحات عملية</h4>
        <ul class="insights-recs-grid">
          <li v-for="(rec, ri) in insightsReport.report.recommendations_ar" :key="'rec' + ri" class="insights-rec-card">
            <span class="insights-rec-icon" aria-hidden="true">✓</span>
            <span class="insights-rec-text">{{ rec }}</span>
          </li>
        </ul>
      </div>

      <div v-if="mostRepeatedFieldGroups.length" class="batch-insights-table-wrap batch-insights-freq-wrap">
        <span class="batch-insights-table-caption">تفاصيل أعلى التكرار (حقل + رسالة)</span>
        <p class="batch-insights-freq-hint">
          جدول ملخّص لكل حقل؛ اضغط على الصف لعرض جدول الرسائل والتكرار لكل رسالة.
        </p>
        <div class="freq-table-scroll">
          <table class="batch-insights-table batch-insights-table--freq-main">
            <thead>
              <tr>
                <th class="freq-col-expand" scope="col" aria-hidden="true"></th>
                <th scope="col">الحقل</th>
                <th scope="col" class="freq-col-num">إجمالي التكرار</th>
                <th scope="col" class="freq-col-num">عدد الرسائل</th>
              </tr>
            </thead>
            <template v-for="g in mostRepeatedFieldGroups" :key="g.field">
              <tbody class="freq-tbody-group">
                <tr
                  class="freq-main-row"
                  :class="{ 'freq-main-row--open': isFreqOpen(g.field) }"
                  tabindex="0"
                  role="button"
                  :aria-expanded="isFreqOpen(g.field)"
                  :aria-controls="'freq-detail-' + g.field"
                  @click="toggleFreqField(g.field)"
                  @keydown.enter.prevent="toggleFreqField(g.field)"
                  @keydown.space.prevent="toggleFreqField(g.field)"
                >
                  <td class="freq-col-expand">
                    <span class="freq-chevron" aria-hidden="true">{{ isFreqOpen(g.field) ? '▼' : '◀' }}</span>
                  </td>
                  <td class="freq-cell-field" :title="'معرّف تقني: ' + g.field">{{ g.fieldLabel }}</td>
                  <td class="freq-cell-num">{{ g.totalCount }}</td>
                  <td class="freq-cell-num">{{ g.rows.length }}</td>
                </tr>
                <tr v-show="isFreqOpen(g.field)" class="freq-detail-row">
                  <td :id="'freq-detail-' + g.field" class="freq-detail-cell" colspan="4" role="region">
                    <table class="batch-insights-table batch-insights-table--nested">
                      <thead>
                        <tr>
                          <th class="freq-th-count" scope="col">التكرار</th>
                          <th scope="col">الرسالة</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, ri) in g.rows" :key="'r' + ri + row.message.slice(0, 48)">
                          <td class="freq-count-cell">{{ row.count }}</td>
                          <td class="batch-insights-msg-cell">{{ row.message }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </td>
                </tr>
              </tbody>
            </template>
          </table>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.batch-insights-section {
  margin-bottom: 1rem;
}

.batch-insights-loading {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.85rem 1rem;
  background: var(--color-background-soft);
  border: 1px dashed var(--color-border);
  border-radius: 0.55rem;
  font-size: 0.9rem;
  color: var(--color-text);
}

.batch-insights-spinner {
  width: 1.1rem;
  height: 1.1rem;
  border: 2px solid var(--color-border);
  border-top-color: var(--ga-primary);
  border-radius: 50%;
  animation: bi-spin 0.7s linear infinite;
}

@keyframes bi-spin {
  to {
    transform: rotate(360deg);
  }
}

.batch-insights-error {
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.35);
  font-size: 0.875rem;
}

.batch-insights-article {
  padding: 1.1rem 1.2rem;
  background: linear-gradient(145deg, rgba(63, 61, 145, 0.08), rgba(99, 102, 241, 0.06));
  border: 1px solid rgba(63, 61, 145, 0.2);
  border-radius: 0.75rem;
}

.batch-insights-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.batch-insights-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--color-heading);
}

.batch-insights-badges {
  display: flex;
  gap: 0.35rem;
}

.tag-gemini {
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.35rem;
  background: rgba(16, 185, 129, 0.15);
  color: #047857;
  font-weight: 600;
}

.tag-insights-fallback {
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.35rem;
  background: rgba(100, 116, 139, 0.15);
  color: var(--color-text);
}

.batch-insights-note {
  margin: 0 0 0.75rem;
  font-size: 0.82rem;
  opacity: 0.88;
}

.summary-callout {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.1rem;
  margin-bottom: 1rem;
  border-radius: 0.65rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-right: 4px solid var(--ga-primary);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.summary-callout-icon {
  font-size: 1.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.summary-callout-body {
  flex: 1;
  min-width: 0;
}

.summary-callout-text {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--color-heading);
  font-weight: 500;
}

.summary-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  font-size: 0.78rem;
  color: var(--color-text);
  opacity: 0.9;
}

.summary-metric strong {
  color: var(--ga-primary);
  font-weight: 700;
}

.insights-charts-wrap {
  margin-bottom: 1rem;
}

.insights-charts-pair {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: stretch;
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: 0.65rem;
  background: var(--color-background);
  overflow: hidden;
}

.insights-chart-segment {
  padding: 0.75rem 0.85rem;
  min-width: 0;
  box-sizing: border-box;
}

.insights-chart-segment--bar {
  flex: 1 1 0;
}

.insights-chart-segment--donut {
  flex: 0 0 clamp(13rem, 26vw, 19rem);
}

.insights-charts-divider {
  flex: 0 0 1px;
  align-self: stretch;
  background: var(--color-border);
  margin: 0.65rem 0;
}

@media (max-width: 36rem) {
  .insights-charts-pair {
    flex-direction: column;
    flex-wrap: wrap;
  }

  .insights-charts-divider {
    width: 100%;
    height: 1px;
    flex: 0 0 auto;
    margin: 0;
  }

  .insights-chart-segment--donut {
    flex: 1 1 auto;
    max-width: none;
  }
}

.insights-charts-row {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.insights-chart-card {
  padding: 0.75rem 0.85rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.6rem;
}

.insights-chart-card--donut {
  max-width: 22rem;
  margin-inline: auto;
  width: 100%;
}

.insights-chart-h4 {
  margin: 0 0 0.5rem;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--color-heading);
}

.insights-chart-caption {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  color: var(--color-text);
  opacity: 0.75;
  text-align: center;
}

.insights-chart-inner {
  position: relative;
}

.insights-chart-inner--donut {
  height: 220px;
}

.insights-chart-inner--bar {
  height: 280px;
}

.batch-insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.batch-insights-block {
  padding: 0.75rem 0.85rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.batch-insights-h4 {
  margin: 0 0 0.4rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ga-primary-dark);
}

.batch-insights-body {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--color-text);
  opacity: 0.92;
}

.batch-insights-priority {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.85rem;
}

.batch-insights-priority-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-heading);
}

.batch-insights-chip {
  font-size: 0.74rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.28);
  color: #4338ca;
}

.insights-recs-section {
  margin-bottom: 1rem;
}

.insights-recs-title {
  margin: 0 0 0.55rem;
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--color-heading);
}

.insights-recs-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 0.5rem;
}

.insights-rec-card {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  padding: 0.65rem 0.75rem;
  border-radius: 0.5rem;
  background: rgba(16, 185, 129, 0.06);
  border: 1px solid rgba(16, 185, 129, 0.22);
  font-size: 0.82rem;
  line-height: 1.45;
  color: var(--color-text);
}

.insights-rec-icon {
  flex-shrink: 0;
  width: 1.25rem;
  height: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.2);
  color: #047857;
  font-size: 0.7rem;
  font-weight: 800;
}

.insights-rec-text {
  flex: 1;
  min-width: 0;
}

.batch-insights-table-wrap {
  margin-top: 0.25rem;
}

.batch-insights-table-caption {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
  color: var(--color-heading);
}

.batch-insights-freq-wrap .batch-insights-table-caption {
  margin-bottom: 0.35rem;
}

.batch-insights-freq-hint {
  margin: 0 0 0.65rem;
  font-size: 0.72rem;
  line-height: 1.45;
  color: var(--color-text);
  opacity: 0.82;
}

.freq-table-scroll {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: 0.55rem;
  background: var(--color-background);
}

.batch-insights-table--freq-main {
  margin: 0;
  min-width: min(100%, 36rem);
}

.freq-tbody-group {
  border-bottom: 1px solid var(--color-border);
}

.freq-tbody-group:last-child {
  border-bottom: none;
}

.freq-main-row {
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}

.freq-main-row:hover {
  background: rgba(99, 102, 241, 0.06);
}

.freq-main-row:focus-visible {
  outline: 2px solid var(--ga-primary);
  outline-offset: -2px;
}

.freq-main-row--open {
  background: rgba(99, 102, 241, 0.08);
}

.freq-col-expand {
  width: 2.25rem;
  text-align: center;
  vertical-align: middle;
  padding-inline: 0.25rem !important;
}

.freq-chevron {
  display: inline-block;
  font-size: 0.65rem;
  opacity: 0.85;
  color: var(--ga-primary-dark);
}

.freq-cell-field {
  font-weight: 700;
  color: var(--color-heading);
}

.freq-col-num {
  width: 6.5rem;
  white-space: nowrap;
  text-align: center;
}

.freq-cell-num {
  font-variant-numeric: tabular-nums;
  text-align: center;
  font-weight: 600;
}

.freq-detail-row .freq-detail-cell {
  padding: 0.5rem 0.65rem 0.65rem !important;
  background: var(--color-background-soft);
  border-top: 1px dashed rgba(99, 102, 241, 0.25);
  vertical-align: top;
}

.batch-insights-table--nested {
  width: 100%;
  font-size: 0.76rem;
  margin: 0;
}

.freq-th-count {
  width: 4.5rem;
  white-space: nowrap;
}

.freq-count-cell {
  font-variant-numeric: tabular-nums;
  text-align: center;
  vertical-align: top;
}

.batch-insights-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.batch-insights-table th,
.batch-insights-table td {
  border: 1px solid var(--color-border);
  padding: 0.4rem 0.55rem;
  text-align: right;
  vertical-align: top;
}

.batch-insights-table th {
  background: var(--color-background-soft);
  font-weight: 600;
}

.batch-insights-msg-cell {
  max-width: 24rem;
  word-break: break-word;
}
</style>
