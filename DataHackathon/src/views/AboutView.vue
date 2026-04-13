<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import {
  getApiBaseUrl,
  runFullDiagnostics,
  checkGeminiStatus,
  setGeminiApiKey,
  checkHealth,
} from '../services/api'
import type { DiagnosticResult, HealthStatus } from '../services/api'
import HomePageIcon from '../components/HomePageIcon.vue'

const apiBase = computed(() => getApiBaseUrl())
const apiDocsUrl = computed(() => `${getApiBaseUrl()}/docs`)
const apiOpenApiUrl = computed(() => `${getApiBaseUrl()}/openapi.json`)

const diagLoading = ref(false)
const diagnosticResults = ref<DiagnosticResult[] | null>(null)

const allDiagnosticsOk = computed(() => {
  const r = diagnosticResults.value
  if (!r?.length) return null
  return r.every((x) => x.ok)
})

async function runDiagnostics() {
  diagLoading.value = true
  diagnosticResults.value = null
  try {
    diagnosticResults.value = await runFullDiagnostics()
  } catch (e) {
    diagnosticResults.value = [
      {
        id: 'fatal',
        label: 'خطأ غير متوقع',
        ok: false,
        message: e instanceof Error ? e.message : 'فشل التشخيص',
      },
    ]
  } finally {
    diagLoading.value = false
  }
}

const health = ref<HealthStatus | null>(null)

const showGeminiKeyInput = computed(() => {
  if (import.meta.env.VITE_HIDE_GEMINI_KEY_INPUT === 'true') return false
  const h = health.value
  if (h?.gemini_from_env) return false
  if (h?.supabase_settings_enabled) return false
  if (h?.client_can_set_gemini_key === false) return false
  return true
})

const geminiServerNote = computed(() => {
  const h = health.value
  if (h?.supabase_settings_enabled) {
    return 'مفتاح النموذج اللغوي يُدار من Supabase (جدول app_settings). عدّل config_value من Table Editor؛ التحديث يظهر خلال حوالي دقيقة أو بعد استدعاء مسح الكاش (انظر README).'
  }
  if (h?.gemini_from_env) {
    return 'النموذج اللغوي يعمل من مفتاح الخادم — غيّر GEMINI_API_KEY في الاستضافة دون إعادة بناء الواجهة.'
  }
  return ''
})

onMounted(async () => {
  try {
    health.value = await checkHealth()
  } catch {
    health.value = null
  }
})

const geminiChecking = ref(false)
const geminiStatus = ref<{ ok: boolean; message: string } | null>(null)
const geminiApiKey = ref('')
const geminiKeySaving = ref(false)
const geminiKeyMessage = ref<{ ok: boolean; message: string } | null>(null)

async function verifyGemini() {
  geminiStatus.value = null
  geminiKeyMessage.value = null
  geminiChecking.value = true
  try {
    geminiStatus.value = await checkGeminiStatus()
  } catch {
    geminiStatus.value = { ok: false, message: 'فشل الاتصال بالخادم. تأكد أن الـ backend يعمل.' }
  } finally {
    geminiChecking.value = false
  }
}

async function saveGeminiKey() {
  geminiKeyMessage.value = null
  geminiStatus.value = null
  geminiKeySaving.value = true
  try {
    const res = await setGeminiApiKey(geminiApiKey.value)
    geminiKeyMessage.value = res
    if (res.ok) geminiApiKey.value = ''
  } catch {
    geminiKeyMessage.value = { ok: false, message: 'فشل الاتصال بالخادم' }
  } finally {
    geminiKeySaving.value = false
  }
}
</script>

<template>
  <div class="tests-page">
    <header class="tests-header">
      <h1 class="tests-title">اختبارات</h1>
      <p class="tests-lead">
        عنوان الـ API، وثائق الواجهة، فحص شامل للخادم، واختبار اتصال النموذج اللغوي — لاستخدام المطوّرين والتشغيل.
      </p>
    </header>

    <section class="card" aria-labelledby="api-heading">
      <h2 id="api-heading" class="card-title">عنوان الـ API</h2>
      <p class="api-base-line">
        <code class="api-base-url">{{ apiBase }}</code>
      </p>
      <div class="links-row">
        <a :href="apiDocsUrl" class="btn btn-outline btn-sm" target="_blank" rel="noopener noreferrer">
          وثائق Swagger
        </a>
        <a :href="apiOpenApiUrl" class="btn btn-outline btn-sm" target="_blank" rel="noopener noreferrer">
          openapi.json
        </a>
      </div>
    </section>

    <section class="card" aria-labelledby="diag-heading">
      <h2 id="diag-heading" class="card-title">اختبار شامل</h2>
      <p class="card-desc">فحص الاتصال، قاعدة البيانات، والنموذج اللغوي (إن وُجد) من الواجهة.</p>
      <button
        type="button"
        class="btn btn-diagnostics btn-with-inline-icon"
        :disabled="diagLoading"
        @click="runDiagnostics"
      >
        <HomePageIcon v-if="!diagLoading" name="search" :size="18" class="btn-inline-icon" />
        {{ diagLoading ? 'جاري فحص الخادم…' : 'تشغيل الفحص (API + قاعدة + نموذج لغوي)' }}
      </button>
      <div
        v-if="diagnosticResults?.length"
        class="diagnostics-panel"
        :class="allDiagnosticsOk ? 'diagnostics-all-ok' : 'diagnostics-has-fail'"
        role="status"
      >
        <p class="diagnostics-summary">
          {{
            allDiagnosticsOk
              ? 'جميع فحوصات الخادم نجحت.'
              : 'بعض الفحوصات فشلت — راجع التفاصيل أدناه.'
          }}
        </p>
        <ul class="diagnostics-list">
          <li
            v-for="row in diagnosticResults"
            :key="row.id"
            class="diag-row"
            :class="row.ok ? 'diag-ok' : 'diag-fail'"
          >
            <div class="diag-row-head">
              <span class="diag-icon" aria-hidden="true">
                <HomePageIcon v-if="row.ok" name="circle-check" :size="18" />
                <HomePageIcon v-else name="x" :size="18" />
              </span>
              <strong class="diag-label">{{ row.label }}</strong>
              <span v-if="row.durationMs != null" class="diag-ms">{{ row.durationMs }} ms</span>
            </div>
            <p class="diag-msg">{{ row.message }}</p>
          </li>
        </ul>
      </div>
    </section>

    <section class="card" aria-labelledby="llm-connection-heading">
      <h2 id="llm-connection-heading" class="card-title">اتصال النموذج اللغوي</h2>
      <p v-if="geminiServerNote" class="gemini-server-hint">{{ geminiServerNote }}</p>
      <div v-if="showGeminiKeyInput" class="gemini-api-row">
        <input
          v-model="geminiApiKey"
          type="password"
          class="input-gemini-api"
          placeholder="مفتاح API للنموذج اللغوي (تطوير محلي)"
          autocomplete="off"
          @keydown.enter="saveGeminiKey"
        />
        <button
          type="button"
          class="btn-gemini-save"
          :disabled="geminiKeySaving || !geminiApiKey.trim()"
          @click="saveGeminiKey"
        >
          <span v-if="geminiKeySaving" class="btn-gemini-spinner"></span>
          {{ geminiKeySaving ? '…' : 'حفظ' }}
        </button>
      </div>
      <button
        type="button"
        class="btn-gemini btn-with-inline-icon"
        :disabled="geminiChecking"
        @click="verifyGemini"
      >
        <span v-if="geminiChecking" class="btn-gemini-spinner"></span>
        <HomePageIcon v-else name="link" :size="18" class="btn-inline-icon" />
        {{ geminiChecking ? 'جاري التحقق…' : 'التحقق من اتصال النموذج اللغوي' }}
      </button>
      <Transition name="gemini-msg">
        <div
          v-if="geminiKeyMessage ?? geminiStatus"
          class="gemini-status-inline"
          :class="(geminiKeyMessage ?? geminiStatus)?.ok ? 'gemini-ok' : 'gemini-fail'"
        >
          {{ (geminiKeyMessage ?? geminiStatus)?.message }}
        </div>
      </Transition>
    </section>
  </div>
</template>

<style scoped>
.tests-page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1.5rem 3rem;
  font-family: var(--font-app);
}

.tests-header {
  margin-bottom: 2rem;
  text-align: center;
}

.tests-title {
  margin: 0 0 0.5rem;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--color-heading);
}

.tests-lead {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--color-text);
  opacity: 0.9;
}

.card {
  margin-bottom: 1.5rem;
  padding: 1.35rem 1.25rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
}

.card-title {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-heading);
}

.card-desc {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  color: var(--color-text);
  opacity: 0.88;
  line-height: 1.5;
}

.api-base-line {
  margin: 0 0 1rem;
}

.api-base-url {
  display: block;
  padding: 0.5rem 0.65rem;
  border-radius: 0.35rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  font-size: 0.8rem;
  word-break: break-all;
  direction: ltr;
}

.links-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 0.5rem;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 2px solid transparent;
  font-family: inherit;
}

.btn-outline {
  color: #0e7490;
  border-color: #0e7490;
  background: transparent;
}

.btn-outline:hover {
  background: rgba(14, 116, 144, 0.08);
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
}

.btn-diagnostics {
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
  border: none;
}

.btn-diagnostics:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.btn-diagnostics:disabled {
  opacity: 0.75;
  cursor: wait;
}

.btn-with-inline-icon {
  gap: 0.45rem;
}

.btn-inline-icon {
  flex-shrink: 0;
}

.diagnostics-panel {
  margin-top: 1.25rem;
  padding: 1rem 1.15rem;
  border-radius: 0.65rem;
  text-align: right;
  border: 1px solid var(--color-border);
  background: var(--color-background);
}

.diagnostics-all-ok {
  border-color: rgba(62, 207, 142, 0.45);
  background: rgba(62, 207, 142, 0.08);
}

.diagnostics-has-fail {
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.06);
}

.diagnostics-summary {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-heading);
}

.diagnostics-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.diag-row {
  padding: 0.65rem 0;
  border-top: 1px solid var(--color-border);
  font-size: 0.85rem;
}

.diag-row:first-of-type {
  border-top: none;
  padding-top: 0;
}

.diag-row-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem 0.5rem;
  margin-bottom: 0.35rem;
}

.diag-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.35rem;
  flex-shrink: 0;
}

.diag-ok .diag-icon {
  color: #059669;
}

.diag-fail .diag-icon {
  color: #dc2626;
}

.diag-label {
  flex: 1;
  min-width: 0;
  font-size: 0.88rem;
}

.diag-ms {
  font-size: 0.75rem;
  opacity: 0.7;
  font-variant-numeric: tabular-nums;
}

.diag-msg {
  margin: 0;
  line-height: 1.45;
  color: var(--color-text);
  opacity: 0.92;
  font-size: 0.82rem;
}

.gemini-server-hint {
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.65rem;
  font-size: 0.78rem;
  line-height: 1.4;
  color: #0f766e;
  background: #ccfbf1;
  border-radius: 6px;
  border: 1px solid #5eead4;
}

.gemini-api-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.75rem;
}

.input-gemini-api {
  flex: 1;
  min-width: 160px;
  max-width: 280px;
  padding: 0.45rem 0.6rem;
  font-size: 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text);
  font-family: inherit;
}

.input-gemini-api:focus {
  outline: none;
  border-color: #0e7490;
  box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
}

.btn-gemini-save {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  padding: 0.45rem 0.65rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #fff;
  background: #0e7490;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
}

.btn-gemini-save:hover:not(:disabled) {
  background: #0c6380;
}

.btn-gemini-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-gemini {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.85rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.4);
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
}

.btn-gemini:hover:not(:disabled) {
  background: rgba(6, 182, 212, 0.2);
  border-color: #0e7490;
}

.btn-gemini:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-gemini-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(14, 116, 144, 0.3);
  border-top-color: #0e7490;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.gemini-status-inline {
  margin-top: 0.75rem;
  padding: 0.55rem 0.75rem;
  font-size: 0.82rem;
  border-radius: 0.375rem;
  line-height: 1.45;
}

.gemini-ok {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.gemini-fail {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}

.gemini-msg-enter-active,
.gemini-msg-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.gemini-msg-enter-from,
.gemini-msg-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

</style>
