<script setup lang="ts">
import { computed } from 'vue'
import type { ValidationResult, ValidationError } from '../services/api'

const props = defineProps<{
  result: ValidationResult | null
  isLoading: boolean
  mode: 'live' | 'demo' | 'unknown'
}>()

const RULE_TAG_LABELS: Record<string, string> = {
  LFS_SALARY_HIGH: 'الأجر 50,000 فأكثر',
  LFS_HOURS_HIGH: 'ساعات العمل الاعتيادية 84+',
  BR_4008: 'العمر لا يناسب المؤهل',
}

function displayCode(e: ValidationError): string {
  if (e.rule_code) return e.rule_code
  if (e.rule_id != null) return `BR_${e.rule_id}`
  return e.rule_type || 'تنبيه'
}

function tagLabel(e: ValidationError): string {
  const c = e.rule_code || (e.rule_id != null ? `BR_${e.rule_id}` : '')
  const mapped = c !== '' ? RULE_TAG_LABELS[c] : undefined
  if (mapped !== undefined) return mapped
  return e.rule_type || 'قاعدة'
}

const confirmedBlocks = computed(() => {
  const errs = props.result?.errors ?? []
  return errs.map((e) => ({
    code: displayCode(e),
    shortLabel: tagLabel(e),
    message: e.message,
    severity: e.severity,
  }))
})

const errorCount = computed(() => props.result?.errors?.length ?? 0)

/** تنبيهات لا تحمل رمز قاعدة مؤكدة (غالباً من النموذج اللغوي فقط) */
const semanticOnlyCount = computed(() => {
  const errs = props.result?.errors ?? []
  return errs.filter((e) => !e.rule_id && !e.rule_code).length
})

const affectedFieldsCount = computed(() => {
  const errs = props.result?.errors ?? []
  return new Set(errs.map((e) => e.field)).size
})

const confidence = computed(() => props.result?.confidence_score ?? 0)

const CIRCUMFERENCE = 2 * Math.PI * 40
const dashOffset = computed(() =>
  props.result ? CIRCUMFERENCE * (1 - confidence.value / 100) : CIRCUMFERENCE,
)

const scoreColor = computed(() => {
  const s = confidence.value
  if (s >= 80) return '#10b981'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
})
</script>

<template>
  <aside class="live-sidebar">
    <div class="live-sidebar-head">
      <h2 class="live-sidebar-title">نتيجة التحقق اللحظي</h2>
      <span :class="['mode-pill', mode === 'live' ? 'mode-on' : 'mode-off']">
        {{ mode === 'live' ? 'نموذج لغوي' : 'وضع تجريبي' }}
      </span>
    </div>

    <div v-if="isLoading" class="live-loading">
      <div class="spinner" />
      <span>جارٍ التحقق…</span>
    </div>

    <template v-else-if="result">
      <div class="live-stat-grid" role="group" aria-label="ملخص سريع">
        <div class="live-stat">
          <span class="live-stat-num live-stat-bad">{{ errorCount }}</span>
          <span class="live-stat-label">أخطاء</span>
        </div>
        <div class="live-stat">
          <span class="live-stat-num">{{ semanticOnlyCount }}</span>
          <span class="live-stat-label">دلالية</span>
        </div>
        <div class="live-stat">
          <span class="live-stat-num">{{ affectedFieldsCount }}</span>
          <span class="live-stat-label">حقول متأثرة</span>
        </div>
      </div>

      <div class="live-gauge">
        <svg viewBox="0 0 100 100" class="live-gauge-svg" aria-hidden="true">
          <circle cx="50" cy="50" r="40" fill="none" stroke="var(--color-border)" stroke-width="8" />
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            :stroke="scoreColor"
            stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="CIRCUMFERENCE"
            :stroke-dashoffset="dashOffset"
            transform="rotate(-90 50 50)"
          />
          <text x="50" y="48" text-anchor="middle" class="live-gauge-pct" :fill="scoreColor">
            {{ confidence }}%
          </text>
          <text x="50" y="62" text-anchor="middle" class="live-gauge-sub">الثقة</text>
        </svg>
      </div>

      <p class="live-summary-line">{{ result.summary }}</p>

      <section v-if="confirmedBlocks.length" class="live-section">
        <h3 class="live-h3">تجاوزات القواعد المؤكدة</h3>
        <ul class="live-rule-list">
          <li v-for="(b, i) in confirmedBlocks" :key="i + b.code" class="live-rule-item">
            <div class="live-rule-tags">
              <span class="live-code">{{ b.code }}</span>
              <span class="live-code-desc">{{ b.shortLabel }}</span>
            </div>
            <p class="live-rule-msg">{{ b.message }}</p>
          </li>
        </ul>
      </section>

      <section v-if="result.suggestions?.length" class="live-section">
        <h3 class="live-h3">المقترحات التصحيحية</h3>
        <ul class="live-sug-list">
          <li v-for="(s, si) in result.suggestions" :key="si">{{ s }}</li>
        </ul>
      </section>

      <p v-if="result.hybrid_rules_applied" class="live-hybrid-note">
        ⚙️ دُمجت <strong>قواعد أعمال LFS</strong> مع نتيجة التحليل.
      </p>
    </template>

    <div v-else class="live-empty">
      <p>أدخل حقلين على الأقل لتظهر <strong>نتيجة التحقق اللحظي</strong> هنا وتحت الحقول.</p>
    </div>
  </aside>
</template>

<style scoped>
.live-sidebar {
  background: linear-gradient(180deg, var(--color-background-soft) 0%, var(--color-background) 100%);
  border: 1px solid var(--color-border);
  border-radius: 0.85rem;
  padding: 1.1rem 1.15rem 1.25rem;
  position: sticky;
  top: 5rem;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
}
.live-sidebar-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--color-border);
}
.live-sidebar-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--color-heading);
}
.mode-pill {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.45rem;
  border-radius: 999px;
}
.mode-on {
  background: rgba(16, 185, 129, 0.15);
  color: #047857;
}
.mode-off {
  background: rgba(245, 158, 11, 0.15);
  color: #92400e;
}

.live-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
  color: var(--color-text);
  opacity: 0.85;
  padding: 0.5rem 0;
}
.spinner {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid var(--color-border);
  border-top-color: #0e7490;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.live-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
  margin-bottom: 0.75rem;
}
.live-stat {
  text-align: center;
  padding: 0.45rem 0.25rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.45rem;
}
.live-stat-num {
  display: block;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--color-heading);
  line-height: 1.2;
}
.live-stat-bad {
  color: #dc2626;
}
.live-stat-label {
  font-size: 0.68rem;
  color: var(--color-text);
  opacity: 0.8;
}

.live-gauge {
  display: flex;
  justify-content: center;
  margin-bottom: 0.65rem;
}
.live-gauge-svg {
  width: 112px;
  height: 112px;
}
.live-gauge-pct {
  font-size: 1.1rem;
  font-weight: 800;
}
.live-gauge-sub {
  font-size: 0.65rem;
  fill: var(--color-text);
  opacity: 0.75;
}

.live-summary-line {
  margin: 0 0 0.85rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text);
}

.live-section {
  margin-bottom: 0.85rem;
}
.live-h3 {
  margin: 0 0 0.45rem;
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--color-heading);
  text-transform: none;
}
.live-rule-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.live-rule-item {
  padding: 0.5rem 0.55rem;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 0.45rem;
}
.live-rule-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.25rem;
}
.live-code {
  font-size: 0.68rem;
  font-weight: 800;
  font-family: ui-monospace, monospace;
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.12);
  padding: 0.12rem 0.35rem;
  border-radius: 0.25rem;
}
.live-code-desc {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-heading);
}
.live-rule-msg {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.45;
  color: var(--color-text);
}

.live-sug-list {
  margin: 0;
  padding-right: 1rem;
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--color-text);
}

.live-hybrid-note {
  font-size: 0.72rem;
  margin: 0.5rem 0 0;
  opacity: 0.9;
}

.live-empty {
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--color-text);
  opacity: 0.85;
}
</style>
