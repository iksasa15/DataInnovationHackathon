<script setup lang="ts">
import { computed } from 'vue'
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
import type { BatchInsightsResponse, BatchStats } from '../services/api'

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

const leastRowsAsc = computed(() => agg.value?.fields_by_errors_asc?.slice(0, 12) ?? [])

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

const leastFieldsBarData = computed<ChartData<'bar'>>(() => {
  const rows = leastRowsAsc.value
  return {
    labels: rows.map((r) => abbrevLabel(props.columnLabel(r.field), 42)),
    datasets: [
      {
        label: 'عدد الإشارات (الأقل)',
        data: rows.map((r) => r.error_mentions),
        backgroundColor: '#8b7fd4',
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
      ticks: { font: { size: 10 } },
      grid: { display: false },
    },
  },
}))

const leastBarOptions = computed<ChartOptions<'bar'>>(() => {
  const rows = leastRowsAsc.value
  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        rtl: true,
        bodyAlign: 'right',
        titleAlign: 'right',
        callbacks: {
          title: (items) => {
            const i = items[0]?.dataIndex ?? 0
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
        ticks: { font: { size: 10 } },
        grid: { display: false },
      },
    },
  }
})

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

const showLeastFieldsChart = computed(() => (agg.value?.fields_by_errors_asc?.length ?? 0) > 0)
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

      <!-- رسوم بيانية -->
      <div v-if="batchStats && (showStatusChart || showFieldCharts)" class="insights-charts-wrap">
        <div v-if="showStatusChart" class="insights-chart-card insights-chart-card--donut">
          <h4 class="insights-chart-h4">توزيع حالة الصفوف</h4>
          <div class="insights-chart-inner insights-chart-inner--donut">
            <Doughnut :data="statusDonutData" :options="statusDonutOptions" />
          </div>
          <p class="insights-chart-caption">سليمة / تحذير / خطأ — حسب نتيجة التحقق لكل سجل</p>
        </div>

        <div v-if="showFieldCharts" class="insights-chart-card">
          <h4 class="insights-chart-h4">أكثر الحقول إشارات للخطأ</h4>
          <div class="insights-chart-inner insights-chart-inner--bar">
            <Bar :data="topFieldsBarData" :options="barOptions" />
          </div>
        </div>

        <div v-if="showLeastFieldsChart" class="insights-chart-card">
          <h4 class="insights-chart-h4">أقل الحقول تكراراً للمشاكل</h4>
          <p class="insights-chart-sub">ضمن الحقول التي وُجد لها خطأ على الأقل — الأقل إشارة أولاً</p>
          <div class="insights-chart-inner insights-chart-inner--bar">
            <Bar :data="leastFieldsBarData" :options="leastBarOptions" />
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
        <div class="batch-insights-block">
          <h4 class="batch-insights-h4">حقول بأقل تكرار للمشاكل</h4>
          <p class="batch-insights-body">{{ insightsReport.report.least_problematic_fields_ar }}</p>
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

      <div v-if="insightsReport.aggregates?.most_repeated?.length" class="batch-insights-table-wrap">
        <span class="batch-insights-table-caption">تفاصيل أعلى التكرار (حقل + رسالة)</span>
        <table class="batch-insights-table">
          <thead>
            <tr>
              <th>الحقل</th>
              <th>التكرار</th>
              <th>الرسالة</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ti) in insightsReport.aggregates.most_repeated.slice(0, 14)" :key="'fr' + ti">
              <td>{{ columnLabel(row.field) }}</td>
              <td>{{ row.count }}</td>
              <td class="batch-insights-msg-cell">{{ row.message }}</td>
            </tr>
          </tbody>
        </table>
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
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-bottom: 1rem;
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

.insights-chart-sub {
  margin: -0.25rem 0 0.5rem;
  font-size: 0.72rem;
  color: var(--color-text);
  opacity: 0.8;
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
