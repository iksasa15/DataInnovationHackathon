<script setup lang="ts">
import { computed } from 'vue'
import type { ValidationResult } from '../services/api'

const props = defineProps<{
  result: ValidationResult | null
  isLoading: boolean
  mode: 'live' | 'demo' | 'unknown'
  /** عناوين عربية لأسماء الحقول كما في ميتاداتا LFS (مفتاح = اسم الحقل في رد الـ API) */
  fieldLabels?: Record<string, string>
}>()

const CIRCUMFERENCE = 2 * Math.PI * 45

const dashOffset = computed(() =>
  props.result ? CIRCUMFERENCE * (1 - props.result.confidence_score / 100) : CIRCUMFERENCE,
)

const scoreColor = computed(() => {
  const s = props.result?.confidence_score ?? 0
  if (s >= 80) return '#10b981'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
})

const statusMeta = computed(() => {
  switch (props.result?.status) {
    case 'valid':
      return { label: 'بيانات سليمة', cls: 'badge-valid', icon: '✓' }
    case 'warning':
      return { label: 'تحذيرات', cls: 'badge-warning', icon: '⚠' }
    case 'error':
      return { label: 'أخطاء مكتشفة', cls: 'badge-error', icon: '✕' }
    default:
      return null
  }
})

const severityMeta = (s: string) => {
  if (s === 'high') return { label: 'حرج', cls: 'sev-high', dot: '#ef4444' }
  if (s === 'medium') return { label: 'متوسط', cls: 'sev-medium', dot: '#f59e0b' }
  return { label: 'منخفض', cls: 'sev-low', dot: '#6b7280' }
}
</script>

<template>
  <aside class="panel">
    <!-- Header -->
    <div class="panel-header">
      <span class="panel-icon">🛡</span>
      <div>
        <h2 class="panel-title">الحارس الدلالي</h2>
        <span :class="['mode-badge', mode === 'live' ? 'mode-live' : 'mode-demo']">
          {{ mode === 'live' ? '● تحليل بنموذج لغوي' : '● وضع تجريبي' }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>جارٍ التحليل…</p>
    </div>

    <!-- Empty -->
    <div v-else-if="!result" class="empty-state">
      <div class="empty-icon">📋</div>
      <p>ابدأ بملء الاستمارة<br /><small>سيبدأ التحقق تلقائياً</small></p>
    </div>

    <!-- Results -->
    <template v-else>
      <!-- Gauge -->
      <div class="gauge-wrap">
        <svg viewBox="0 0 120 120" class="gauge-svg" aria-label="درجة الثقة">
          <circle cx="60" cy="60" r="45" fill="none" stroke="var(--color-border)" stroke-width="9" />
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            :stroke="scoreColor"
            stroke-width="9"
            stroke-linecap="round"
            :stroke-dasharray="CIRCUMFERENCE"
            :stroke-dashoffset="dashOffset"
            transform="rotate(-90 60 60)"
            class="gauge-arc"
          />
          <text x="60" y="54" text-anchor="middle" class="gauge-num" :fill="scoreColor">
            {{ result.confidence_score }}
          </text>
          <text x="60" y="70" text-anchor="middle" class="gauge-sub" fill="var(--color-text)">
            درجة الثقة
          </text>
        </svg>

        <span v-if="statusMeta" :class="['status-badge', statusMeta.cls]">
          {{ statusMeta.icon }} {{ statusMeta.label }}
        </span>
      </div>

      <!-- Summary -->
      <p class="summary">{{ result.summary }}</p>

      <!-- Errors -->
      <div v-if="result.errors.length" class="section">
        <h3 class="section-title">
          <span>🔍</span> التناقضات المكتشفة
          <span class="count-badge">{{ result.errors.length }}</span>
        </h3>
        <ul class="error-list">
          <li v-for="(err, i) in result.errors" :key="i" class="error-item">
            <span class="sev-dot" :style="{ background: severityMeta(err.severity).dot }"></span>
            <div class="error-body">
              <div class="error-field">{{ props.fieldLabels?.[err.field] ?? err.field }}</div>
              <div class="error-msg">{{ err.message }}</div>
            </div>
            <span :class="['sev-label', severityMeta(err.severity).cls]">
              {{ severityMeta(err.severity).label }}
            </span>
          </li>
        </ul>
      </div>

      <!-- No errors -->
      <div v-else class="no-errors">
        <span>✓</span> لا توجد تناقضات مرصودة
      </div>

      <!-- Suggestions -->
      <div v-if="result.suggestions.length" class="section">
        <h3 class="section-title"><span>💡</span> اقتراحات</h3>
        <ul class="suggestion-list">
          <li v-for="(s, i) in result.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.panel {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.875rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  position: sticky;
  top: 5rem;
  max-height: calc(100vh - 7rem);
  overflow-y: auto;
}

/* Header */
.panel-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}
.panel-icon {
  font-size: 1.5rem;
  margin-top: 2px;
}
.panel-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.25rem;
}
.mode-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
}
.mode-live {
  color: #10b981;
  background: rgba(16, 185, 129, 0.12);
}
.mode-demo {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem 0;
  color: var(--color-text);
  opacity: 0.7;
  font-size: 0.9rem;
}
.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid var(--color-border);
  border-top-color: #0e7490;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 0;
  text-align: center;
  color: var(--color-text);
  opacity: 0.6;
}
.empty-icon {
  font-size: 2.5rem;
}
.empty-state p {
  font-size: 0.9rem;
  line-height: 1.6;
}

/* Gauge */
.gauge-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.gauge-svg {
  width: 140px;
  height: 140px;
}
.gauge-arc {
  transition: stroke-dashoffset 0.7s ease, stroke 0.4s ease;
}
.gauge-num {
  font-size: 1.6rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.gauge-sub {
  font-size: 0.58rem;
  opacity: 0.7;
}

/* Status badges */
.status-badge {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.3rem 0.8rem;
  border-radius: 9999px;
}
.badge-valid   { color: #10b981; background: rgba(16,185,129,0.12); }
.badge-warning { color: #f59e0b; background: rgba(245,158,11,0.12); }
.badge-error   { color: #ef4444; background: rgba(239,68,68,0.12);  }

/* Summary */
.summary {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--color-text);
  padding: 0.75rem;
  background: var(--color-background-mute);
  border-radius: 0.5rem;
  border-right: 3px solid #0e7490;
}

/* Section */
.section { display: flex; flex-direction: column; gap: 0.6rem; }
.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-heading);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.count-badge {
  margin-right: auto;
  background: rgba(239,68,68,0.12);
  color: #ef4444;
  border-radius: 9999px;
  font-size: 0.72rem;
  padding: 0.1rem 0.5rem;
  font-weight: 700;
}

/* Error list */
.error-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.error-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.7rem 0.8rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}
.sev-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
}
.error-body { flex: 1; min-width: 0; }
.error-field {
  font-size: 0.72rem;
  font-weight: 700;
  color: #0e7490;
  margin-bottom: 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.error-msg {
  font-size: 0.82rem;
  color: var(--color-text);
  line-height: 1.5;
}
.sev-label {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 9999px;
  white-space: nowrap;
  flex-shrink: 0;
}
.sev-high   { color: #ef4444; background: rgba(239,68,68,0.1);  }
.sev-medium { color: #f59e0b; background: rgba(245,158,11,0.1); }
.sev-low    { color: #6b7280; background: rgba(107,114,128,0.1);}

/* No errors */
.no-errors {
  font-size: 0.875rem;
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(16,185,129,0.08);
  border-radius: 0.5rem;
}

/* Suggestions */
.suggestion-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.suggestion-list li {
  font-size: 0.83rem;
  color: var(--color-text);
  padding: 0.5rem 0.75rem;
  background: rgba(245,158,11,0.06);
  border-radius: 0.375rem;
  border-right: 2px solid #f59e0b;
  line-height: 1.5;
}
.suggestion-list li::before {
  content: '→ ';
  color: #f59e0b;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .summary { border-right-color: #22d3ee; }
  .error-field { color: #22d3ee; }
}
</style>
