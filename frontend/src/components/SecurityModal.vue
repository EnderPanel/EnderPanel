<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-xl max-w-md w-full p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Security Settings</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="space-y-4">
        <div>
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Two-Factor Authentication</h4>
          <div v-if="totpEnabled" class="flex items-center gap-2 text-green-600 dark:text-green-400">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <span>2FA is enabled</span>
          </div>
          <div v-else class="space-y-3">
            <div v-if="!setupMode">
              <button @click="startSetup" type="button" class="px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">Enable 2FA</button>
            </div>
            <div v-else class="space-y-3">
              <img v-if="qrCode" :src="qrCode" alt="2FA QR Code" class="mx-auto" />
              <div v-else class="flex items-center justify-center h-48">
                <svg class="animate-spin w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke-width="4" class="opacity-25"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12a8 8 0 018-8"/>
                </svg>
              </div>
              <p v-if="secret" class="text-xs text-gray-500 text-center">Secret: {{ secret }}</p>
              <div class="flex gap-2">
                <input v-model="code" type="text" placeholder="Enter 2FA code" class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800" />
                <button @click="enable2FA" :disabled="enabling" class="px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors disabled:opacity-50">{{ enabling ? 'Enabling...' : 'Confirm' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

defineProps({ show: Boolean })
defineEmits(['close'])

const totpEnabled = ref(false)
const setupMode = ref(false)
const qrCode = ref('')
const secret = ref('')
const code = ref('')
const enabling = ref(false)

async function fetchSetup() {
  try {
    const res = await axios.get('/api/auth/me')
    totpEnabled.value = !!res.data.totp_enabled
  } catch (e) {}
}

async function startSetup() {
  try {
    const res = await axios.get('/api/auth/2fa/generate')
    qrCode.value = res.data.qr_code
    secret.value = res.data.secret
    setupMode.value = true
  } catch (e) {}
}

async function enable2FA() {
  if (!secret.value || !code.value) return
  enabling.value = true
  try {
    await axios.post('/api/auth/2fa/enable', { secret: secret.value, code: code.value })
    totpEnabled.value = true
    setupMode.value = false
    code.value = ''
    secret.value = ''
    qrCode.value = ''
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to enable 2FA')
  } finally {
    enabling.value = false
  }
}
</script>