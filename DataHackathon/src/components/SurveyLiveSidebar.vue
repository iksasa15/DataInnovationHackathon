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
  if (s >= 80) return '#53cd3f'
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
          <span class="live-stat-num live-stat-semantic">{{ semanticOnlyCount }}</span>
          <span class="live-stat-label">دلالية</span>
        </div>
        <div class="live-stat">
          <span class="live-stat-num live-stat-fields">{{ affectedFieldsCount }}</span>
          <span class="live-stat-label">حقول متأثرة</span>
        </div>
      </div>

      <div class="live-gauge">
        <svg viewBox="0 0 100 100" class="live-gauge-svg" aria-hidden="true">
          <circle cx="50" cy="50" r="40" fill="none" stroke="var(--live-ring)" stroke-width="8" />
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
      <p v-if="confirmedBlocks.length" class="live-jump">
        <a href="#survey-confirmed-violations" class="live-jump-link">تجاوزات القواعد المؤكدة</a>
      </p>

      <section
        v-if="confirmedBlocks.length"
        id="survey-confirmed-violations"
        class="live-section live-violations"
      >
        <h3 class="live-h3">تجاوزات القواعد المؤكدة</h3>
        <ul class="live-rule-list">
          <li v-for="(b, i) in confirmedBlocks" :key="i + b.code" class="live-rule-item">
            <div class="live-rule-banner">
              <span class="live-rule-badge">تنبيه قاعدة</span>
              <span class="live-code">{{ b.code }}</span>
            </div>
            <div class="live-rule-body">
              <span class="live-code-desc">{{ b.shortLabel }}</span>
              <p class="live-rule-msg">{{ b.message }}</p>
            </div>
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
  --live-purple: #322a82;
  --live-purple-mid: #4137a8;
  --live-purple-soft: #ebe8f7;
  --live-ring: #e8ecf1;

  background: #fff;
  border: 1px solid #e8e8ef;
  border-radius: 1rem;
  padding: 1.15rem 1.15rem 1.25rem;
  box-shadow: 0 6px 28px rgba(15, 23, 42, 0.07);
  font-family: var(--font-app);
}
.live-sidebar-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
  margin-bottom: 0.9rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid #eef0f4;
}
.live-sidebar-title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--live-purple);
  line-height: 1.35;
}
.mode-pill {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.22rem 0.5rem;
  border-radius: 999px;
  white-space: nowrap;
}
.mode-on {
  background: #e8f5e9;
  color: #1b5e20;
  border: 1px solid #81c784;
  font-weight: 800;
}
.mode-off {
  background: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}

.live-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.86rem;
  color: #475569;
  padding: 0.5rem 0;
}
.spinner {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid #e2e8f0;
  border-top-color: var(--live-purple);
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
  gap: 0.4rem;
  margin-bottom: 0.8rem;
}
.live-stat {
  text-align: center;
  padding: 0.55rem 0.25rem;
  background: #fff;
  border: 1px solid #e8e8ef;
  border-radius: 0.55rem;
}
.live-stat-num {
  display: block;
  font-size: 1.12rem;
  font-weight: 800;
  line-height: 1.2;
}
.live-stat-bad {
  color: #dc2626;
}
.live-stat-semantic {
  color: var(--live-purple-mid);
}
.live-stat-fields {
  color: #64748b;
}
.live-stat-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: #64748b;
}

.live-gauge {
  display: flex;
  justify-content: center;
  margin-bottom: 0.7rem;
}
.live-gauge-svg {
  width: 112px;
  height: 112px;
}
.live-gauge-pct {
  font-size: 1.05rem;
  font-weight: 800;
}
.live-gauge-sub {
  font-size: 0.62rem;
  fill: #64748b;
}

.live-summary-line {
  margin: 0 0 0.45rem;
  font-size: 0.8rem;
  line-height: 1.55;
  color: #475569;
}

.live-jump {
  margin: 0 0 0.85rem;
  font-size: 0.78rem;
}
.live-jump-link {
  color: #0288d1;
  font-weight: 700;
  text-decoration: none;
}
.live-jump-link:hover {
  text-decoration: underline;
}

.live-violations {
  scroll-margin-top: 5.5rem;
}

.live-section {
  margin-bottom: 0.85rem;
}
.live-h3 {
  margin: 0 0 0.5rem;
  font-size: 0.76rem;
  font-weight: 800;
  color: var(--live-purple);
}
.live-rule-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.live-rule-item {
  overflow: hidden;
  border-radius: 0.65rem;
  border: 1px solid #e0dcf0;
  background: #fff;
  box-shadow: 0 3px 12px rgba(45, 38, 117, 0.08);
}
.live-rule-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.65rem;
  background: linear-gradient(180deg, #f3f0fa 0%, var(--live-purple-soft) 100%);
  border-bottom: 1px solid #e0dcf0;
}
.live-rule-badge {
  font-size: 0.62rem;
  font-weight: 800;
  color: var(--live-purple);
  background: #ede9f7;
  padding: 0.18rem 0.45rem;
  border-radius: 0.35rem;
  border: 1px solid rgba(65, 55, 168, 0.18);
}
.live-code {
  font-size: 0.65rem;
  font-weight: 800;
  font-family: ui-monospace, monospace;
  color: var(--ga-primary);
  margin-inline-start: auto;
}
.live-rule-body {
  padding: 0.5rem 0.6rem 0.6rem;
}
.live-code-desc {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 0.25rem;
}
.live-rule-msg {
  margin: 0;
  font-size: 0.76rem;
  line-height: 1.45;
  color: #475569;
}

.live-sug-list {
  margin: 0;
  padding-right: 1rem;
  font-size: 0.76rem;
  line-height: 1.5;
  color: #475569;
}

.live-hybrid-note {
  font-size: 0.7rem;
  margin: 0.5rem 0 0;
  color: #64748b;
}

.live-empty {
  font-size: 0.82rem;
  line-height: 1.55;
  color: #64748b;
}
</style>
