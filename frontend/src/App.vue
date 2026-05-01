<template>
  <div v-if="!loading" :class="['min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white transition-colors duration-300', { 'dqs-app-shell': isDqsTheme }]">
    <nav
      v-if="authStore.user && $route.path !== '/login' && $route.path !== '/register' && (!isDqsTheme || !isDqsSidebarLayout)"
      class="glass sticky top-0 z-40 px-4 sm:px-6 py-3 animate-fade-in"
    >
      <div class="max-w-7xl mx-auto flex justify-between items-center">
        <div class="flex items-center gap-4 sm:gap-8">
          <router-link to="/dashboard" class="flex items-center gap-2 group">
            <img
              :src="brandIconSrc"
              :alt="brandName"
              :class="isDqsTheme ? 'h-8 w-auto object-contain mr-4 transition-transform duration-300 group-hover:scale-105' : 'w-8 h-8 rounded-xl object-cover border border-white/10 shadow-lg transition-transform duration-300 group-hover:scale-110'"
            />
            <span
              v-if="!isDqsTheme"
              class="text-lg sm:text-xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent"
            >
              {{ brandName }}
            </span>
            <button
              v-if="isDqsTheme"
              type="button"
              @click.stop="openDqsHosting"
              class="hidden md:block text-xs text-white ml-3 underline decoration-white/40 underline-offset-4 hover:decoration-white transition-colors"
            >
              Buy a Cheap Server at https://www.dqshosting.online/
            </button>
            <span v-else class="hidden md:block text-xs text-gray-400 dark:text-gray-500 ml-2">With Love by <span class="text-mc-accent">ThatMacOSGuy</span> & <span class="text-mc-purple">carit1</span></span>
          </router-link>
          <div class="hidden sm:flex items-center gap-1">
            <router-link to="/dashboard"
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
              :class="$route.path === '/dashboard' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
              Servers
            </router-link>
            <router-link to="/themes"
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
              :class="$route.path === '/themes' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
              Themes
            </router-link>
            <router-link v-if="isAdmin" to="/users"
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
              :class="$route.path === '/users' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
              Users
            </router-link>
            <router-link v-if="isAdmin" to="/admin"
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
              :class="$route.path === '/admin' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
              Admin
            </router-link>
          </div>
        </div>
        <div class="flex items-center gap-2 sm:gap-3">
          <button @click="themeStore.toggle()"
            class="p-2 rounded-xl text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-white/10 transition-all duration-200">
            <svg v-if="themeStore.isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
          </button>

          <button
            v-if="isDqsTheme"
            @click="themeStore.toggleDqsLayout()"
            class="px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 border"
            :class="isDqsSidebarLayout
              ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10 border-gray-200 dark:border-white/10 hover:bg-gray-300 dark:hover:bg-white/15'
              : 'text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:bg-gray-200 dark:hover:bg-white/10'"
          >
            {{ isDqsSidebarLayout ? 'Top View' : 'Side View' }}
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
              class="flex items-center gap-2 bg-gray-100 dark:bg-white/5 px-2 sm:px-3 py-1.5 rounded-xl hover:bg-gray-200 dark:hover:bg-white/10 transition-all duration-200">
              <div class="w-7 h-7 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0">
                <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-gradient-to-br from-mc-accent to-mc-purple flex items-center justify-center text-xs font-bold text-white">
                  {{ authStore.user.username?.charAt(0).toUpperCase() }}
                </div>
              </div>
              <span class="text-sm text-gray-600 dark:text-gray-300 hidden sm:block">{{ authStore.user.username }}</span>
            </button>
          </div>

          <button @click="openSecurity"
            class="relative p-2 rounded-xl text-gray-500 hover:text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-500/10 transition-all duration-200"
            title="Security Settings">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
            <div v-if="!authStore.user?.totp_enabled" class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-gray-950"></div>
          </button>

          <button @click="logout"
            class="p-2 rounded-xl text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-all duration-200">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>

          <!-- Mobile hamburger -->
          <button @click="mobileMenuOpen = !mobileMenuOpen"
            class="sm:hidden p-2 rounded-xl text-gray-500 hover:bg-gray-200 dark:hover:bg-white/10 transition-all duration-200">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile menu -->
      <transition name="mobile-menu">
        <div v-if="mobileMenuOpen" class="sm:hidden border-t border-gray-200 dark:border-white/10 mt-3 pt-3 pb-1 flex flex-col gap-1">
          <router-link to="/dashboard" @click="mobileMenuOpen = false"
            class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
            :class="$route.path === '/dashboard' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-600 dark:text-gray-300'">
            Servers
          </router-link>
          <router-link to="/themes" @click="mobileMenuOpen = false"
            class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
            :class="$route.path === '/themes' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-600 dark:text-gray-300'">
            Themes
          </router-link>
          <router-link v-if="isAdmin" to="/users" @click="mobileMenuOpen = false"
            class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
            :class="$route.path === '/users' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-600 dark:text-gray-300'">
            Users
          </router-link>
          <router-link v-if="isAdmin" to="/admin" @click="mobileMenuOpen = false"
            class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
            :class="$route.path === '/admin' ? 'text-gray-900 dark:text-white bg-gray-200 dark:bg-white/10' : 'text-gray-600 dark:text-gray-300'">
            Admin
          </router-link>
        </div>
      </transition>
    </nav>
    <aside
      v-if="authStore.user && $route.path !== '/login' && $route.path !== '/register' && isDqsSidebarLayout"
      class="hidden md:flex dqs-sidebar glass flex-col animate-fade-in"
    >
      <router-link to="/dashboard" class="flex items-center gap-3 pb-6 mb-6 border-b border-white/10">
        <img
          :src="brandIconSrc"
          alt="dqs hosting"
          class="h-8 w-auto object-contain"
        />
      </router-link>

      <div class="flex flex-col gap-2">
        <router-link
          to="/dashboard"
          class="dqs-nav-link"
          :class="{ active: $route.path === '/dashboard' }"
        >
          Servers
        </router-link>
        <router-link
          to="/themes"
          class="dqs-nav-link"
          :class="{ active: $route.path === '/themes' }"
        >
          Themes
        </router-link>
        <router-link
          v-if="isAdmin"
          to="/users"
          class="dqs-nav-link"
          :class="{ active: $route.path === '/users' }"
        >
          Users
        </router-link>
        <router-link
          v-if="isAdmin"
          to="/admin"
          class="dqs-nav-link"
          :class="{ active: $route.path === '/admin' }"
        >
          Admin
        </router-link>
      </div>

      <div class="mt-auto space-y-4 pt-6 border-t border-white/10">
        <button
          type="button"
          @click="openDqsHosting"
          class="w-full text-left text-sm text-white underline decoration-white/40 underline-offset-4 hover:decoration-white transition-colors"
        >
          Buy a Cheap Server at https://www.dqshosting.online/
        </button>

        <button
          type="button"
          @click="themeStore.toggleDqsLayout()"
          class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-gray-200 transition-all duration-200 hover:bg-white/10"
        >
          Switch to Top View
        </button>

        <div class="flex items-center gap-2">
          <button @click="themeStore.toggle()"
            class="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all duration-200">
            <svg v-if="themeStore.isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
          </button>

          <button @click="openSecurity"
            class="relative p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all duration-200"
            title="Security Settings">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
            <div v-if="!authStore.user?.totp_enabled" class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-[#0f0f0f]"></div>
          </button>

          <button @click="$refs.avatarInput.click()"
            class="flex items-center gap-2 bg-white/5 px-2 py-1.5 rounded-xl hover:bg-white/10 transition-all duration-200 min-w-0 flex-1">
            <div class="w-7 h-7 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0">
              <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-[#151515] border border-[#222] flex items-center justify-center text-xs font-bold text-white">
                {{ authStore.user.username?.charAt(0).toUpperCase() }}
              </div>
            </div>
            <span class="text-sm text-gray-300 truncate">{{ authStore.user.username }}</span>
          </button>
        </div>

        <button @click="logout"
          class="w-full flex items-center justify-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm font-medium text-red-300 transition-all duration-200 hover:bg-red-500/15 hover:text-red-200">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
          Logout
        </button>
      </div>
    </aside>
    <SecurityModal :show="showSecurityModal" @close="showSecurityModal = false" ref="securityModalRef" />
    <Toast ref="toastRef" />
    <div :class="{ 'md:ml-[260px]': isDqsSidebarLayout && authStore.user && $route.path !== '/login' && $route.path !== '/register' }">
      <router-view :key="$route.fullPath" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide, watch } from 'vue'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Toast from './components/Toast.vue'
import SecurityModal from './components/SecurityModal.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const router = useRouter()
const avatarInput = ref(null)
const toastRef = ref(null)
const securityModalRef = ref(null)
const showSecurityModal = ref(false)
const loading = ref(true)
const mobileMenuOpen = ref(false)
watch(() => router.currentRoute.value.path, () => { mobileMenuOpen.value = false })

const openSecurity = () => {
  showSecurityModal.value = true
  // setTimeout to allow the ref to bind after v-if evaluation
  setTimeout(() => {
    if (securityModalRef.value) {
      securityModalRef.value.fetchSetup()
    }
  }, 50)
}

const toast = (options) => toastRef.value?.addToast(options)
const confirm = (options) => toastRef.value?.showConfirm(options)

provide('toast', toast)
provide('confirm', confirm)

onMounted(() => {
  themeStore.init()
  authStore.init()
  refreshUser()
})

const isAdmin = computed(() => Boolean(authStore.user?.is_admin))
const isDqsTheme = computed(() => themeStore.currentTheme === 'dqs-hosting')
const isDqsSidebarLayout = computed(() => themeStore.isDqsSidebar)
const brandName = computed(() => (isDqsTheme.value ? 'dqs hosting' : 'EnderPanel'))
const brandIconSrc = computed(() => (isDqsTheme.value ? `${window.location.origin}/branding/dqs-hosting-logo.png` : `${window.location.origin}/branding/favicon.svg`))

const userAvatar = computed(() => authStore.user?.avatar || null)

async function refreshUser() {
  const hadToken = !!authStore.token
  try {
    const res = await axios.get('/api/auth/me')
    localStorage.setItem('user', JSON.stringify(res.data))
    authStore.user = res.data
  } catch (e) {
    if (e.response?.status === 401 && hadToken) {
      authStore.logout()
      router.push('/login')
    }
  } finally {
    loading.value = false
  }
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

function openDqsHosting() {
  window.open('https://www.dqshosting.online/', '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.page-enter-active, .page-leave-active { transition: all 0.3s ease; }
.page-enter-from { opacity: 0; transform: translateY(10px); }
.page-leave-to { opacity: 0; transform: translateY(-10px); }

.mobile-menu-enter-active, .mobile-menu-leave-active { transition: all 0.2s ease; }
.mobile-menu-enter-from, .mobile-menu-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
