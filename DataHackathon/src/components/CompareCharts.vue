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

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale, LinearScale, BarElement)

ChartJS.defaults.font.family = "'Frutiger LT Arabic', 'Segoe UI', system-ui, sans-serif"

const donutBefore = computed<ChartData<'doughnut'>>(() => ({
  labels: ['تغطية', 'متبقي'],
  datasets: [
    {
      data: [42, 58],
      backgroundColor: ['#8492a2', '#dde2e8'],
      borderWidth: 0,
      hoverOffset: 6,
    },
  ],
}))

const donutAfter = computed<ChartData<'doughnut'>>(() => ({
  labels: ['تغطية', 'متبقي'],
  datasets: [
    {
      data: [88, 12],
      backgroundColor: ['#4137a8', 'rgba(0, 178, 223, 0.28)'],
      borderWidth: 0,
      hoverOffset: 6,
    },
  ],
}))

const doughnutOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 1,
  cutout: '68%',
  plugins: {
    legend: { display: false },
    tooltip: {
      rtl: true,
      bodyAlign: 'right',
      titleAlign: 'right',
      callbacks: {
        label: (ctx) => {
          const v = ctx.raw as number
          return ` ${v}٪`
        },
      },
    },
  },
}))

const barData = computed<ChartData<'bar'>>(() => ({
  labels: [
    'جهد الوقت (دفعة ~100 صف)',
    'ملاحظة تناقض أثناء الاستبيان',
    'تكامل التشخيص (API / مفتاح / وثائق)',
  ],
  datasets: [
    {
      label: 'تقليدي',
      data: [100, 32, 28],
      backgroundColor: '#8492a2',
      borderRadius: 6,
      maxBarThickness: 22,
    },
    {
      label: 'مع عين',
      data: [36, 94, 100],
      backgroundColor: '#4137a8',
      borderRadius: 6,
      maxBarThickness: 22,
    },
  ],
}))

const barOptions = computed<ChartOptions<'bar'>>(() => ({
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      beginAtZero: true,
      max: 100,
      grid: { color: 'rgba(15, 23, 42, 0.08)' },
      ticks: {
        callback: (value) => `${value}٪`,
        font: { size: 11 },
      },
    },
    y: {
      grid: { display: false },
      ticks: { font: { size: 11 } },
    },
  },
  plugins: {
    legend: {
      display: true,
      position: 'top',
      rtl: true,
      labels: {
        boxWidth: 14,
        boxHeight: 14,
        padding: 16,
        font: { size: 12 },
      },
    },
    tooltip: {
      rtl: true,
      bodyAlign: 'right',
      titleAlign: 'right',
      callbacks: {
        label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw}٪`,
      },
    },
  },
}))
</script>

<template>
  <div class="compare-charts" dir="rtl">
    <div class="compare-charts-donuts">
      <p class="compare-charts-title">نظرة سريعة (نسب مُقارَنة)</p>
      <div class="donuts-row">
        <figure class="donut-item">
          <div class="donut-chart-wrap">
            <Doughnut :data="donutBefore" :options="doughnutOptions" />
          </div>
          <figcaption class="donut-caption">
            <span class="donut-pct">42٪</span>
            <span class="donut-label">تغطية تحقق منظّمة<br /><small>مسار تقليدي</small></span>
          </figcaption>
        </figure>
        <div class="donut-arrow" aria-hidden="true"></div>
        <figure class="donut-item donut-item--highlight">
          <div class="donut-chart-wrap">
            <Doughnut :data="donutAfter" :options="doughnutOptions" />
          </div>
          <figcaption class="donut-caption">
            <span class="donut-pct">88٪</span>
            <span class="donut-label">تغطية تحقق منظّمة<br /><small>مع عين</small></span>
          </figcaption>
        </figure>
      </div>
    </div>

    <p class="compare-charts-title compare-charts-title--bars">مقارنة بالأشرطة (مقياس ٠–١٠٠٪)</p>
    <div class="bar-chart-card" role="img" aria-label="مخطط أشرطة أفقي يقارن تقليدي مع عين">
      <div class="bar-chart-inner">
        <Bar :data="barData" :options="barOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.compare-charts {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.compare-charts-donuts {
  margin: 0 0 1.5rem;
  padding: 1.25rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
}

.compare-charts-title {
  margin: 0 0 1rem;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-heading);
}

.compare-charts-title--bars {
  margin-top: 0.25rem;
}

.donuts-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: center;
  gap: 0.5rem 1rem;
}

.donut-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  margin: 0;
  padding: 0.5rem 0.75rem;
  border-radius: 0.65rem;
  border: 1px solid transparent;
}

.donut-item--highlight {
  border-color: rgba(0, 178, 223, 0.35);
  background: rgba(0, 178, 223, 0.08);
}

.donut-chart-wrap {
  width: 132px;
  height: 132px;
  position: relative;
}

.donut-caption {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  text-align: center;
}

.donut-pct {
  font-size: 1.25rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--color-heading);
}

.donut-label {
  font-size: 0.78rem;
  line-height: 1.35;
  color: var(--color-text);
  opacity: 0.88;
}

.donut-label small {
  font-size: 0.7rem;
  opacity: 0.75;
}

.donut-arrow {
  align-self: center;
  padding: 0.25rem 0;
  font-size: 1.35rem;
  color: var(--ga-primary);
  opacity: 0.55;
  line-height: 1;
}

.donut-arrow::after {
  content: '↓';
}

@media (min-width: 640px) {
  .donut-arrow {
    padding: 0 0.35rem;
    margin-bottom: 2.5rem;
  }

  .donut-arrow::after {
    content: '⇄';
  }
}

.bar-chart-card {
  margin: 0 0 1.75rem;
  padding: 1rem 0.75rem 0.5rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.bar-chart-inner {
  height: 240px;
  position: relative;
}

@media (min-width: 640px) {
  .bar-chart-inner {
    height: 220px;
  }
}
</style>
