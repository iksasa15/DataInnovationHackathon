<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { checkGeminiStatus, getGeminiApiKey, setGeminiApiKey } from './services/api'

const geminiChecking = ref(false)
const geminiStatus = ref<{ ok: boolean; message: string } | null>(null)
const apiKeyInput = ref('')
const apiKeySaved = ref(false)
const showKeyPanel = ref(false)


function saveApiKey() {
  const key = apiKeyInput.value?.trim() || ''
  setGeminiApiKey(key)
  apiKeySaved.value = true
  setTimeout(() => { apiKeySaved.value = false }, 2000)
  if (!key) showKeyPanel.value = false
}

async function verifyGemini() {
  geminiStatus.value = null
  geminiChecking.value = true
  try {
    geminiStatus.value = await checkGeminiStatus()
  } catch (e) {
    geminiStatus.value = { ok: false, message: 'فشل الاتصال بالخادم. تأكد أن الـ backend يعمل.' }
  } finally {
    geminiChecking.value = false
  }
}
</script>

<template>
  <div class="app">
    <header class="app-header">
      <RouterLink to="/" class="logo">
        <span class="logo-data">Data</span><span class="logo-hackathon">Hackathon</span>
      </RouterLink>
      <nav class="nav">
        <RouterLink to="/">الرئيسية</RouterLink>
        <RouterLink to="/survey" class="nav-highlight">🛡 الحارس الدلالي</RouterLink>
        <RouterLink to="/excel" class="nav-highlight">📊 تحليل Excel</RouterLink>
        <RouterLink to="/csv" class="nav-highlight">📋 تحليل CSV</RouterLink>
        <RouterLink to="/about">من نحن</RouterLink>
        <div class="nav-gemini">
          <div class="gemini-key-wrap">
            <button
              type="button"
              class="btn-gemini btn-gemini-key"
              @click="showKeyPanel = !showKeyPanel"
            >
              {{ getGeminiApiKey() ? '🔑 مفتاح محفوظ' : '➕ مفتاح API' }}
            </button>
            <Transition name="key-panel">
              <div v-if="showKeyPanel" class="gemini-key-panel">
                <input
                  v-model="apiKeyInput"
                  type="password"
                  class="gemini-key-input"
                  placeholder="أدخل مفتاح Gemini API"
                  autocomplete="off"
                />
                <div class="gemini-key-actions">
                  <button type="button" class="btn-gemini-save" @click="saveApiKey">
                    {{ apiKeySaved ? '✓ تم الحفظ' : 'حفظ' }}
                  </button>
                </div>
              </div>
            </Transition>
          </div>
          <button
            type="button"
            class="btn-gemini"
            :disabled="geminiChecking"
            @click="verifyGemini"
          >
            <span v-if="geminiChecking" class="btn-gemini-spinner"></span>
            {{ geminiChecking ? 'جاري التحقق…' : '🔗 اتصال Gemini' }}
          </button>
          <Transition name="gemini-msg">
            <div v-if="geminiStatus" class="gemini-status" :class="geminiStatus.ok ? 'gemini-ok' : 'gemini-fail'">
              {{ geminiStatus.message }}
            </div>
          </Transition>
        </div>
      </nav>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 2rem;
  background: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(8px);
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  text-decoration: none;
  letter-spacing: -0.02em;
}

.logo-data {
  color: var(--color-heading);
}

.logo-hackathon {
  color: #0e7490;
}

.logo:hover .logo-hackathon {
  text-decoration: underline;
}

.nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nav-gemini {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.gemini-key-wrap {
  position: relative;
}

.btn-gemini-key {
  font-size: 0.8rem;
  padding: 0.35rem 0.6rem;
}

.gemini-key-panel {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.35rem;
  padding: 0.6rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 101;
  min-width: 220px;
}

.gemini-key-input {
  width: 100%;
  padding: 0.45rem 0.6rem;
  font-size: 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text);
  margin-bottom: 0.5rem;
  font-family: ui-monospace, monospace;
}

.gemini-key-input::placeholder {
  opacity: 0.7;
}

.gemini-key-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-gemini-save {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #fff;
  background: #0e7490;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
}

.btn-gemini-save:hover {
  background: #0c6380;
}

.btn-gemini {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.4);
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s, border-color 0.2s;
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
  to { transform: rotate(360deg); }
}

.gemini-status {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.35rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.8rem;
  border-radius: 0.375rem;
  white-space: nowrap;
  max-width: 280px;
  white-space: normal;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 100;
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

.key-panel-enter-active,
.key-panel-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.key-panel-enter-from,
.key-panel-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.nav a {
  padding: 0.5rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  border-radius: 0.375rem;
  transition: background 0.2s, color 0.2s;
}

.nav a:hover {
  background: var(--color-background-soft);
  color: #0e7490;
}

.nav a.router-link-active {
  color: #0e7490;
  background: rgba(6, 182, 212, 0.1);
}

.nav-highlight {
  font-weight: 600;
  color: #0e7490 !important;
}

.app-main {
  flex: 1;
}

@media (prefers-color-scheme: dark) {
  .logo-hackathon {
    color: #22d3ee;
  }
  .nav a:hover,
  .nav a.router-link-active {
    color: #22d3ee;
  }
  .nav a.router-link-active {
    background: rgba(34, 211, 238, 0.12);
  }
  .btn-gemini {
    color: #22d3ee;
    background: rgba(34, 211, 238, 0.12);
    border-color: rgba(34, 211, 238, 0.4);
  }
  .btn-gemini:hover:not(:disabled) {
    background: rgba(34, 211, 238, 0.2);
    border-color: #22d3ee;
  }
  .btn-gemini-spinner { border-top-color: #22d3ee; }
  .gemini-ok { background: #064e3b; color: #6ee7b7; border-color: #10b981; }
  .gemini-fail { background: #7f1d1d; color: #fca5a5; border-color: #ef4444; }
}
</style>
