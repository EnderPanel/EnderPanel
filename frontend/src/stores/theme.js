import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

export const useThemeStore = defineStore('theme', () => {
  const storedTheme = localStorage.getItem('theme')
  const storedDqsLayout = localStorage.getItem('dqs-layout')
  const defaultDqsLayout = storedTheme === 'dqs-hosting' ? 'top' : 'sidebar'
  const currentTheme = ref(
    storedTheme === 'light' || storedTheme === 'dark' || storedTheme === 'dqs-hosting'
      ? storedTheme
      : 'dark'
  )
  const currentDqsLayout = ref(
    storedDqsLayout === 'top' || storedDqsLayout === 'sidebar'
      ? storedDqsLayout
      : defaultDqsLayout
  )

  const isDark = computed(() => currentTheme.value === 'dark' || currentTheme.value === 'dqs-hosting')
  const isDqsSidebar = computed(() => currentTheme.value === 'dqs-hosting' && currentDqsLayout.value === 'sidebar')
  let syncTimeout = null

  function toggle() {
    currentTheme.value = currentTheme.value === 'light' ? 'dark' : 'light'
    apply()
  }

  function setTheme(theme) {
    currentTheme.value = theme
    if (theme === 'dqs-hosting' && (!currentDqsLayout.value || currentDqsLayout.value === 'sidebar') && !storedDqsLayout) {
      currentDqsLayout.value = 'top'
    }
    apply()
  }

  function setDqsLayout(layout) {
    currentDqsLayout.value = layout === 'top' ? 'top' : 'sidebar'
    apply()
  }

  function toggleDqsLayout() {
    currentDqsLayout.value = currentDqsLayout.value === 'sidebar' ? 'top' : 'sidebar'
    apply()
  }

  function apply() {
    localStorage.setItem('theme', currentTheme.value)
    localStorage.setItem('dqs-layout', currentDqsLayout.value)
    document.documentElement.classList.toggle('dark', isDark.value)
    document.documentElement.classList.toggle('theme-dqs', currentTheme.value === 'dqs-hosting')
    schedulePreferenceSync()
  }

  function init() {
    apply()
  }

  function applyUserPreferences(user) {
    if (user?.theme === 'light' || user?.theme === 'dark' || user?.theme === 'dqs-hosting') {
      currentTheme.value = user.theme
    }
    if (user?.dqs_layout === 'top' || user?.dqs_layout === 'sidebar') {
      currentDqsLayout.value = user.dqs_layout
    } else if (currentTheme.value === 'dqs-hosting') {
      currentDqsLayout.value = 'top'
    }
    localStorage.setItem('theme', currentTheme.value)
    localStorage.setItem('dqs-layout', currentDqsLayout.value)
    document.documentElement.classList.toggle('dark', isDark.value)
    document.documentElement.classList.toggle('theme-dqs', currentTheme.value === 'dqs-hosting')
  }

  function ensureUserPreferences(user) {
    if (!user) return
    if (user.theme && user.dqs_layout) return
    schedulePreferenceSync()
  }

  function schedulePreferenceSync() {
    const authStore = useAuthStore()
    if (!authStore.user) return
    if (syncTimeout) clearTimeout(syncTimeout)
    syncTimeout = setTimeout(() => {
      axios.post('/api/auth/preferences', {
        theme: currentTheme.value,
        dqs_layout: currentDqsLayout.value,
      }).catch(() => {})
    }, 150)
  }

  return { currentTheme, currentDqsLayout, isDark, isDqsSidebar, toggle, setTheme, setDqsLayout, toggleDqsLayout, init, applyUserPreferences, ensureUserPreferences }
})
