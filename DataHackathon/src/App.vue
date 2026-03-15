<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { checkGeminiStatus, setGeminiApiKey } from './services/api'

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
  } catch (e) {
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
  } catch (e) {
    geminiKeyMessage.value = { ok: false, message: 'فشل الاتصال بالخادم' }
  } finally {
    geminiKeySaving.value = false
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
        <RouterLink to="/analysis" class="nav-highlight">📂 تحليل الملف</RouterLink>
        <RouterLink to="/about">من نحن</RouterLink>
        <div class="nav-gemini">
          <div class="gemini-api-row">
            <input
              v-model="geminiApiKey"
              type="password"
              class="input-gemini-api"
              placeholder="مفتاح Gemini API"
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
            class="btn-gemini"
            :disabled="geminiChecking"
            @click="verifyGemini"
          >
            <span v-if="geminiChecking" class="btn-gemini-spinner"></span>
            {{ geminiChecking ? 'جاري التحقق…' : '🔗 اتصال Gemini' }}
          </button>
          <Transition name="gemini-msg">
            <div v-if="geminiKeyMessage ?? geminiStatus" class="gemini-status" :class="(geminiKeyMessage ?? geminiStatus)?.ok ? 'gemini-ok' : 'gemini-fail'">
              {{ (geminiKeyMessage ?? geminiStatus)?.message }}
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
  gap: 0.5rem;
  flex-wrap: wrap;
}

.gemini-api-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.input-gemini-api {
  width: 180px;
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text);
  font-family: inherit;
}

.input-gemini-api::placeholder {
  color: var(--color-text);
  opacity: 0.6;
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
  padding: 0.4rem 0.65rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #fff;
  background: #0e7490;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s;
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

/* تحليل — قائمة منسدلة */
.nav-dropdown {
  position: relative;
}

.nav-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #0e7490;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s, color 0.2s;
}

.nav-dropdown-trigger:hover {
  background: rgba(6, 182, 212, 0.1);
}

.nav-dropdown.nav-active .nav-dropdown-trigger {
  background: rgba(6, 182, 212, 0.1);
}

.nav-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.15rem;
  min-width: 180px;
  padding: 0.35rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 60;
}

.nav-dropdown-item {
  display: block;
  padding: 0.5rem 0.85rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  border-radius: 0.375rem;
  transition: background 0.2s, color 0.2s;
}

.nav-dropdown-item:hover {
  background: var(--color-background-soft);
  color: #0e7490;
}

.nav-dropdown-item.router-link-active {
  background: rgba(6, 182, 212, 0.12);
  color: #0e7490;
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
  .nav-dropdown-trigger { color: #22d3ee; }
  .nav-dropdown-trigger:hover { background: rgba(34, 211, 238, 0.12); }
  .nav-dropdown.nav-active .nav-dropdown-trigger { background: rgba(34, 211, 238, 0.12); }
  .nav-dropdown-item:hover,
  .nav-dropdown-item.router-link-active { color: #22d3ee; }
  .nav-dropdown-item.router-link-active { background: rgba(34, 211, 238, 0.12); }
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
  .input-gemini-api:focus { border-color: #22d3ee; box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.2); }
  .btn-gemini-save { background: #0891b2; }
  .btn-gemini-save:hover:not(:disabled) { background: #0e7490; }
  .gemini-ok { background: #064e3b; color: #6ee7b7; border-color: #10b981; }
  .gemini-fail { background: #7f1d1d; color: #fca5a5; border-color: #ef4444; }
}
</style>
