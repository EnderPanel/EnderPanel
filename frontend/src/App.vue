<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white transition-colors duration-300">
    <nav v-if="authStore.user" class="glass sticky top-0 z-40 px-6 py-3 animate-fade-in">
      <div class="max-w-7xl mx-auto flex justify-between items-center">
        <div class="flex items-center gap-8">
          <router-link to="/dashboard" class="flex items-center gap-2 group">
            <div class="w-8 h-8 bg-gradient-to-br from-purple-500 via-pink-500 to-purple-700 rounded-lg flex items-center justify-center 
                        group-hover:shadow-lg group-hover:shadow-purple-500/30 transition-all duration-300 group-hover:scale-110 relative overflow-hidden">
              <div class="absolute inset-1 bg-gradient-to-br from-pink-300 to-purple-400 rounded-md opacity-80"></div>
              <div class="absolute w-2 h-2 bg-white rounded-full top-1.5 left-1.5 opacity-90 shadow-lg shadow-white/50"></div>
            </div>
            <span class="text-xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">EnderPanel</span>
            <span class="hidden md:block text-xs text-gray-400 dark:text-gray-500 ml-2">With Love by <span class="text-mc-accent">ThatMacOSGuy</span> & <span class="text-mc-purple">carit1</span></span>
          </router-link>
          <div class="hidden sm:flex items-center gap-1">
            <router-link to="/dashboard" 
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
              :class="$route.path === '/dashboard' 
                ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' 
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
              Servers
            </router-link>
            <router-link to="/users" 
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
              :class="$route.path === '/users' 
                ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' 
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
              Users
            </router-link>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button @click="themeStore.toggle()" 
            class="p-2 rounded-xl text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white 
                   hover:bg-gray-200 dark:hover:bg-white/10 transition-all duration-200"
            :title="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'">
            <svg v-if="themeStore.isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
          </button>

          <div v-if="isAdmin" class="hidden sm:flex items-center gap-2 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 px-3 py-1.5 rounded-lg border border-yellow-500/20">
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
            </svg>
            <span class="text-xs font-medium">Admin</span>
          </div>

          <div class="relative group">
            <input type="file" ref="avatarInput" @change="uploadAvatar" accept="image/*" class="hidden" />
            <button @click="$refs.avatarInput.click()" 
              class="flex items-center gap-3 bg-gray-100 dark:bg-white/5 px-3 py-1.5 rounded-xl hover:bg-gray-200 dark:hover:bg-white/10 transition-all duration-200">
              <div class="w-7 h-7 rounded-lg overflow-hidden flex items-center justify-center">
                <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-gradient-to-br from-mc-accent to-mc-purple flex items-center justify-center text-xs font-bold text-white">
                  {{ authStore.user.username?.charAt(0).toUpperCase() }}
                </div>
              </div>
              <span class="text-sm text-gray-600 dark:text-gray-300 hidden sm:block">{{ authStore.user.username }}</span>
            </button>
            <div class="absolute top-full right-0 mt-2 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 whitespace-nowrap">
              <p class="text-xs text-gray-500 dark:text-gray-400 px-2 py-1">Click to change avatar</p>
            </div>
          </div>

          <button @click="logout" 
            class="p-2 rounded-xl text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-all duration-200">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </nav>
    <Toast ref="toastRef" />
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Toast from './components/Toast.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const router = useRouter()
const avatarInput = ref(null)
const toastRef = ref(null)

const toast = (options) => toastRef.value?.addToast(options)
const confirm = (options) => toastRef.value?.showConfirm(options)

provide('toast', toast)
provide('confirm', confirm)

onMounted(() => {
  themeStore.init()
  refreshUser()
})

const isAdmin = computed(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    return user.is_admin
  }
  return false
})

const userAvatar = computed(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    return user.avatar
  }
  return null
})

async function refreshUser() {
  try {
    const res = await axios.get('/api/auth/me')
    localStorage.setItem('user', JSON.stringify(res.data))
    authStore.user = res.data
  } catch (e) {}
}

async function uploadAvatar(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    await axios.post('/api/user/avatar', formData)
    await refreshUser()
  } catch (e) {
    toast({ title: 'Failed to upload avatar', message: e.response?.data?.detail || '', type: 'error' })
  }
  event.target.value = ''
}

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
