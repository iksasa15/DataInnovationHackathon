<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js'
import type { ChartData, ChartOptions } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)
ChartJS.defaults.font.family = "'Frutiger LT Arabic', 'Segoe UI', system-ui, sans-serif"

const labels = ['', '', '', '', '', '']

const data = computed<ChartData<'line'>>(() => ({
  labels,
  datasets: [
    {
      label: 'مسار تحقق الجودة (توضيحي)',
      data: [14, 22, 18, 28, 24, 36],
      borderColor: '#00b2df',
      borderWidth: 2.5,
      fill: true,
      tension: 0.45,
      pointRadius: (ctx) => (ctx.dataIndex === 5 ? 8 : 0),
      pointHoverRadius: (ctx) => (ctx.dataIndex === 5 ? 9 : 0),
      pointBackgroundColor: (ctx) => (ctx.dataIndex === 5 ? '#53cd3f' : 'transparent'),
      pointBorderColor: (ctx) => (ctx.dataIndex === 5 ? '#ffffff' : 'transparent'),
      pointBorderWidth: (ctx) => (ctx.dataIndex === 5 ? 3 : 0),
      backgroundColor: (context) => {
        const chart = context.chart
        const { ctx: c, chartArea } = chart
        if (!chartArea) return 'rgba(65, 55, 168, 0.2)'
        const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
        g.addColorStop(0, 'rgba(82, 71, 184, 0.38)')
        g.addColorStop(0.45, 'rgba(139, 120, 220, 0.14)')
        g.addColorStop(1, 'rgba(255, 255, 255, 0)')
        return g
      },
    },
  ],
}))

const options = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      rtl: true,
      bodyAlign: 'right',
      titleAlign: 'right',
      callbacks: {
        title: () => '',
        label: (items) => ` ${items.formattedValue}٪ — قيمة تمثيلية على مسار الجودة`,
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { display: false },
      border: {
        display: true,
        color: 'rgba(148, 163, 184, 0.45)',
      },
    },
    y: {
      display: false,
      min: 0,
    },
  },
}))
</script>

<template>
  <div class="quality-chart" dir="rtl">
    <Line :data="data" :options="options" />
  </div>
</template>

<style scoped>
.quality-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
