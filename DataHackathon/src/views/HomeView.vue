<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getApiBaseUrl, runFullDiagnostics } from '../services/api'
import type { DiagnosticResult } from '../services/api'

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
</script>

<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <h1 class="hero-title">عين</h1>
        <div class="hero-actions">
          <RouterLink to="/survey" class="btn btn-primary">جرّب الاستبيان الآن</RouterLink>
          <button
            type="button"
            class="btn btn-diagnostics"
            :disabled="diagLoading"
            @click="runDiagnostics"
          >
            {{ diagLoading ? 'جاري فحص الخادم…' : '🔍 اختبار شامل (API + قاعدة + Gemini)' }}
          </button>
        </div>
        <p class="api-base-line">
          <span class="api-base-label">عنوان الـ API الحالي:</span>
          <code class="api-base-url">{{ apiBase }}</code>
        </p>
        <div class="diagnostics-links">
          <a :href="apiDocsUrl" class="btn btn-outline btn-sm" target="_blank" rel="noopener noreferrer">
            وثائق Swagger
          </a>
          <a :href="apiOpenApiUrl" class="btn btn-outline btn-sm" target="_blank" rel="noopener noreferrer">
            openapi.json
          </a>
        </div>
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
                <span class="diag-icon">{{ row.ok ? '✓' : '✕' }}</span>
                <strong class="diag-label">{{ row.label }}</strong>
                <span v-if="row.durationMs != null" class="diag-ms">{{ row.durationMs }} ms</span>
              </div>
              <p class="diag-msg">{{ row.message }}</p>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <footer class="home-footer">
      <p>© {{ new Date().getFullYear() }} عين</p>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif;
}

/* Hero */
.hero {
  position: relative;
  min-height: 85vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(14, 165, 233, 0.15) 0%, transparent 55%),
    radial-gradient(ellipse 60% 40% at 80% 60%, rgba(6, 182, 212, 0.08) 0%, transparent 50%),
    var(--color-background);
}

.hero-content {
  position: relative;
  text-align: center;
  max-width: 42rem;
}

.hero-title {
  font-size: clamp(3rem, 12vw, 5rem);
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 2rem;
  letter-spacing: 0.02em;
  color: #0e7490;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Buttons */
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
}

.btn-primary {
  background: #0e7490;
  color: #fff;
}

.btn-primary:hover {
  background: #0c6380;
  transform: translateY(-1px);
}

.btn-outline {
  color: #0e7490;
  border-color: #0e7490;
  background: transparent;
}

.btn-outline:hover {
  background: rgba(14, 116, 144, 0.08);
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

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
}

.api-base-line {
  margin: 1rem auto 0;
  max-width: 42rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text);
  opacity: 0.85;
  line-height: 1.5;
}

.api-base-label {
  display: block;
  margin-bottom: 0.25rem;
}

.api-base-url {
  display: inline-block;
  padding: 0.2rem 0.45rem;
  border-radius: 0.35rem;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  font-size: 0.78rem;
  word-break: break-all;
  direction: ltr;
}

.diagnostics-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.75rem;
}

.diagnostics-panel {
  margin: 1.25rem auto 0;
  max-width: 40rem;
  padding: 1rem 1.15rem;
  border-radius: 0.65rem;
  text-align: right;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
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
  font-weight: 700;
  width: 1.25rem;
  text-align: center;
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

/* Footer */
.home-footer {
  padding: 1.5rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text);
  opacity: 0.7;
  border-top: 1px solid var(--color-border);
}

@media (prefers-color-scheme: dark) {
  .hero-title {
    color: #22d3ee;
  }
  .btn-primary {
    background: #0891b2;
  }
  .btn-primary:hover {
    background: #0e7490;
  }
  .btn-outline {
    color: #22d3ee;
    border-color: #22d3ee;
  }
  .btn-outline:hover {
    background: rgba(34, 211, 238, 0.1);
  }
  .btn-diagnostics {
    background: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
  }
  .diagnostics-all-ok {
    border-color: rgba(45, 212, 191, 0.4);
    background: rgba(45, 212, 191, 0.08);
  }
  .diagnostics-has-fail {
    border-color: rgba(248, 113, 113, 0.35);
    background: rgba(248, 113, 113, 0.08);
  }
  .diag-ok .diag-icon {
    color: #34d399;
  }
  .diag-fail .diag-icon {
    color: #f87171;
  }
}
</style>
