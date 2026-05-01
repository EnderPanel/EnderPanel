<template>
  <transition name="modal">
    <div v-if="show" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="close">
      <div class="glass rounded-2xl p-8 w-full max-w-md scale-in dqs-modal-card">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold flex items-center gap-2">
            <svg class="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
            Security Settings
          </h2>
          <button @click="close" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div v-if="loading" class="flex justify-center py-10">
          <svg class="animate-spin w-8 h-8 text-purple-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>

        <div v-else>
          <!-- ENABLE 2FA FLOW -->
          <div v-if="!totpEnabled">
            <p class="text-gray-600 dark:text-gray-300 text-sm mb-4">
              Two-Factor Authentication adds an extra layer of security to your account.
              Scan the QR code below using an authenticator app (like Authy or Google Authenticator).
            </p>
            
            <div v-if="setupData" class="flex flex-col items-center mb-6">
              <div class="bg-white p-4 rounded-xl shadow-inner mb-4 w-48 h-48 flex items-center justify-center">
                <img :src="setupData.qr_code" class="w-full h-full object-contain" alt="2FA QR Code"/>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Or enter manual key:</p>
              <code class="bg-gray-100 dark:bg-white/10 px-3 py-1.5 rounded-lg text-sm tracking-widest font-mono text-purple-500 dark:text-purple-400 select-all">{{ setupData.secret }}</code>
            </div>

            <form @submit.prevent="enable2FA" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Verify Code</label>
                <div class="relative">
                  <input v-model="verifyCode" type="text" required placeholder="000 000" maxlength="7"
                    class="input-field text-center text-lg tracking-widest" />
                </div>
              </div>
              <button type="submit" :disabled="enabling" class="btn-success w-full mt-2">
                {{ enabling ? 'Verifying...' : 'Enable 2FA' }}
              </button>
            </form>
          </div>

          <!-- DISABLE 2FA FLOW -->
          <div v-else>
            <div class="bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 rounded-xl p-4 flex items-start gap-3 mb-6">
              <svg class="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 class="font-bold text-emerald-700 dark:text-emerald-400">2FA is Enabled</h3>
                <p class="text-sm text-emerald-600 dark:text-emerald-500">Your account is secured with two-factor authentication.</p>
              </div>
            </div>

            <form @submit.prevent="disable2FA" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Current Password</label>
                <input v-model="disablePassword" type="password" required placeholder="Enter password to disable"
                  class="input-field" />
              </div>
              <button type="submit" :disabled="disabling" class="btn-danger w-full mt-2">
                {{ disabling ? 'Disabling...' : 'Disable 2FA' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close', 'updated'])
const authStore = useAuthStore()
const toast = inject('toast')

const loading = ref(false)
const enabling = ref(false)
const disabling = ref(false)

const setupData = ref(null)
const verifyCode = ref('')
const disablePassword = ref('')

const totpEnabled = computed(() => {
  return authStore.user?.totp_enabled || false
})

async function fetchSetup() {
  if (totpEnabled.value) return
  loading.value = true
  setupData.value = null
  try {
    const res = await axios.get('/api/auth/2fa/generate')
    setupData.value = res.data
  } catch (e) {
    toast({ title: 'Error', message: 'Failed to generate 2FA setup', type: 'error' })
  } finally {
    loading.value = false
  }
}

async function enable2FA() {
  if (!verifyCode.value) return
  enabling.value = true
  const code = verifyCode.value.replace(/\s/g, '')
  try {
    await axios.post('/api/auth/2fa/enable', {
      secret: setupData.value.secret,
      code: code
    })
    toast({ title: 'Success', message: 'Two-Factor Authentication enabled', type: 'success' })
    if (authStore.user) {
      const updatedUser = { ...authStore.user, totp_enabled: true }
      authStore.user = updatedUser
      localStorage.setItem('user', JSON.stringify(updatedUser))
    }
    emit('updated')
    close()
  } catch (e) {
    toast({ title: 'Invalid Code', message: e.response?.data?.detail || 'Please check your authenticator app', type: 'error' })
  } finally {
    enabling.value = false
  }
}

async function disable2FA() {
  if (!disablePassword.value) return
  disabling.value = true
  try {
    await axios.post('/api/auth/2fa/disable', {
      password: disablePassword.value
    })
    toast({ title: 'Success', message: 'Two-Factor Authentication disabled', type: 'success' })
    if (authStore.user) {
      const updatedUser = { ...authStore.user, totp_enabled: false }
      authStore.user = updatedUser
      localStorage.setItem('user', JSON.stringify(updatedUser))
    }
    emit('updated')
    close()
  } catch (e) {
    toast({ title: 'Error', message: e.response?.data?.detail || 'Failed to disable 2FA', type: 'error' })
  } finally {
    disabling.value = false
  }
}

function close() {
  verifyCode.value = ''
  disablePassword.value = ''
  emit('close')
}

// Expose fetchSetup so parent can call it when modal opens
defineExpose({ fetchSetup })
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .glass,
.modal-leave-to .glass {
  transform: scale(0.95);
}
</style>
