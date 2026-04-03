<script setup lang="ts">
import { computed } from 'vue'
import type { LfsBusinessRuleRow, ValidationError } from '../services/api'

const props = defineProps<{
  modelValue: boolean
  error: ValidationError | null
  /** عنوان الحقل من الميتاداتا */
  fieldLabel: string
  /** عمود الجدول الذي نُقر عليه */
  columnKey: string
  /** رقم الصف للعرض (يبدأ من 1) */
  rowDisplayIndex: number
  /** من جدول LFS_Business_Rules عبر /api/lfs-business-rules */
  rulesById: Record<number, LfsBusinessRuleRow>
  /** اقتراحات عامة على مستوى الصف من التحليل */
  rowSuggestions: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function close() {
  emit('update:modelValue', false)
}

const ruleMeta = computed(() => {
  const id = props.error?.rule_id
  if (id == null || id === undefined) return null
  return props.rulesById[id] ?? null
})

const severityLabel = computed(() => {
  const s = props.error?.severity
  if (s === 'high') return 'حرج'
  if (s === 'medium') return 'متوسط'
  if (s === 'low') return 'منخفض'
  return s || '—'
})

const correctiveLines = computed(() => {
  const lines: string[] = []
  const seen = new Set<string>()
  const push = (t: string) => {
    const x = t.trim()
    if (!x || seen.has(x)) return
    seen.add(x)
    lines.push(x)
  }
  const act = ruleMeta.value?.action?.trim()
  if (act) push(act)
  for (const s of props.rowSuggestions) push(typeof s === 'string' ? s : String(s))
  return lines
})

const isConfirmedRule = computed(() => props.error?.rule_id != null && props.error.rule_id !== undefined)

const showColumnNote = computed(
  () =>
    props.error &&
    props.columnKey.trim().toLowerCase() !== String(props.error.field || '').trim().toLowerCase(),
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue && error"
      class="field-rule-overlay"
      role="presentation"
      @click.self="close"
    >
      <div class="field-rule-modal" role="dialog" aria-modal="true" aria-labelledby="field-rule-title">
        <div class="field-rule-head">
          <h3 id="field-rule-title">تفاصيل الخطأ — صف {{ rowDisplayIndex }}</h3>
          <button type="button" class="field-rule-close" aria-label="إغلاق" @click="close">×</button>
        </div>
        <div class="field-rule-body">
          <div
            class="field-rule-badge"
            :class="isConfirmedRule ? 'field-rule-badge--rule' : 'field-rule-badge--soft'"
          >
            {{ isConfirmedRule ? 'قاعدة مؤكدة' : 'تحليل ذكي / عام' }}
          </div>

          <div class="field-rule-grid">
            <div class="field-rule-k">المجال</div>
            <div class="field-rule-v">{{ fieldLabel }}</div>

            <div class="field-rule-k">المعرّف التقني</div>
            <div class="field-rule-v"><code class="field-rule-code">{{ error.field }}</code></div>

            <template v-if="showColumnNote">
              <div class="field-rule-k">عمود الجدول</div>
              <div class="field-rule-v"><code class="field-rule-code">{{ columnKey }}</code></div>
            </template>

            <template v-if="error.rule_id != null && error.rule_id !== undefined">
              <div class="field-rule-k">رقم القاعدة</div>
              <div class="field-rule-v">{{ error.rule_id }}</div>
            </template>

            <template v-if="error.rule_type">
              <div class="field-rule-k">نوع الخطأ</div>
              <div class="field-rule-v">{{ error.rule_type }}</div>
            </template>

            <div class="field-rule-k">الشدة</div>
            <div class="field-rule-v">{{ severityLabel }}</div>
          </div>

          <section class="field-rule-section">
            <h4 class="field-rule-h4">الرسالة</h4>
            <p class="field-rule-p">{{ error.message }}</p>
          </section>

          <section v-if="error.message_en" class="field-rule-section field-rule-en">
            <h4 class="field-rule-h4">مرجع إنجليزي</h4>
            <p class="field-rule-p" dir="ltr">{{ error.message_en }}</p>
          </section>

          <section v-if="ruleMeta?.rule_summary" class="field-rule-section">
            <h4 class="field-rule-h4">ملخص القاعدة</h4>
            <p class="field-rule-p">{{ ruleMeta.rule_summary }}</p>
          </section>

          <section v-if="correctiveLines.length" class="field-rule-section field-rule-corrective">
            <h4 class="field-rule-h4">مقترحات تصحيحية</h4>
            <ul class="field-rule-ul">
              <li v-for="(line, i) in correctiveLines" :key="i">{{ line }}</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.field-rule-overlay {
  position: fixed;
  inset: 0;
  z-index: 12000;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.field-rule-modal {
  background: var(--color-background, #fff);
  color: var(--color-text, #1e293b);
  border-radius: 0.65rem;
  max-width: 34rem;
  width: 100%;
  max-height: min(88vh, 640px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid var(--color-border, #e2e8f0);
}
.field-rule-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}
.field-rule-head h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-heading, #0f172a);
}
.field-rule-close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--color-text);
  opacity: 0.7;
  padding: 0 0.25rem;
}
.field-rule-close:hover {
  opacity: 1;
}
.field-rule-body {
  padding: 1rem 1.1rem 1.15rem;
  overflow-y: auto;
}
.field-rule-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.55rem;
  border-radius: 0.35rem;
  margin-bottom: 0.75rem;
}
.field-rule-badge--rule {
  background: rgba(59, 130, 246, 0.15);
  color: #1d4ed8;
  border: 1px solid rgba(59, 130, 246, 0.35);
}
.field-rule-badge--soft {
  background: rgba(100, 116, 139, 0.12);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
.field-rule-grid {
  display: grid;
  grid-template-columns: 7.5rem 1fr;
  gap: 0.35rem 0.75rem;
  font-size: 0.82rem;
  margin-bottom: 0.85rem;
}
.field-rule-k {
  color: var(--color-text);
  opacity: 0.75;
  font-weight: 600;
}
.field-rule-v {
  word-break: break-word;
}
.field-rule-code {
  font-size: 0.78rem;
  background: var(--color-background-soft, #f1f5f9);
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
}
.field-rule-section {
  margin-top: 0.75rem;
}
.field-rule-h4 {
  margin: 0 0 0.35rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-heading);
}
.field-rule-p {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.55;
}
.field-rule-en .field-rule-p {
  font-size: 0.82rem;
  opacity: 0.92;
}
.field-rule-ul {
  margin: 0;
  padding-right: 1.1rem;
  font-size: 0.86rem;
  line-height: 1.5;
}
.field-rule-corrective .field-rule-h4 {
  color: #047857;
}
</style>
