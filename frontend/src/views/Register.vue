<template>
  <div class="enderpanel-auth-page min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute bottom-1/4 left-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse-slow" style="animation-delay: 1.5s"></div>
    </div>

    <div class="w-full max-w-md animate-fade-up relative z-10">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 via-pink-500 to-purple-700 rounded-2xl mb-4
                    shadow-lg shadow-purple-500/30 animate-float relative overflow-hidden">
          <div class="absolute inset-2 bg-gradient-to-br from-pink-300 to-purple-400 rounded-xl opacity-80"></div>
          <div class="absolute w-4 h-4 bg-white rounded-full top-3 left-3 opacity-90 shadow-lg shadow-white/50"></div>
        </div>
        <h1 class="text-3xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent mb-2">EnderPanel</h1>
        <p class="text-gray-500 dark:text-gray-400">Create your account</p>
      </div>

      <div class="glass rounded-2xl p-8 shadow-2xl shadow-gray-200/50 dark:shadow-black/50">
        <transition name="shake">
          <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl mb-6 text-sm flex items-center gap-2">
            <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            {{ error }}
          </div>
        </transition>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <div class="animate-slide-up" style="animation-delay: 100ms">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Username</label>
            <div class="relative">
              <div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
              </div>
              <input v-model="username" type="text" required placeholder="Choose a username"
                class="input-field pl-12" />
            </div>
          </div>

          <div class="animate-slide-up" style="animation-delay: 150ms">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Email</label>
            <div class="relative">
              <div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
              </div>
              <input v-model="email" type="email" required placeholder="Enter your email"
                class="input-field pl-12" />
            </div>
          </div>

          <div class="animate-slide-up" style="animation-delay: 200ms">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Password</label>
            <div class="relative">
              <div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </div>
              <input v-model="password" type="password" required placeholder="Create a password"
                class="input-field pl-12" />
            </div>
          </div>

          <button type="submit" :disabled="loading" class="btn-primary w-full animate-slide-up" style="animation-delay: 300ms">
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creating account...
            </span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <div class="mt-6 text-center animate-fade-in" style="animation-delay: 400ms">
          <p class="text-gray-500 dark:text-gray-500 text-sm">
            Already have an account?
            <router-link to="/login" class="text-purple-500 hover:text-purple-400 font-medium transition-colors">Sign in</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await authStore.register(username.value, email.value, password.value)
    router.push('/welcome')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.shake-enter-active {
  animation: shake 0.5s ease;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-10px); }
  40% { transform: translateX(10px); }
  60% { transform: translateX(-10px); }
  80% { transform: translateX(10px); }
}
</style>
