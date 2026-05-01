import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const storedTheme = localStorage.getItem('theme')
  const storedDqsLayout = localStorage.getItem('dqs-layout')
  const currentTheme = ref(
    storedTheme === 'light' || storedTheme === 'dark' || storedTheme === 'dqs-hosting'
      ? storedTheme
      : 'dark'
  )
  const currentDqsLayout = ref(
    storedDqsLayout === 'top' || storedDqsLayout === 'sidebar'
      ? storedDqsLayout
      : 'sidebar'
  )

  const isDark = computed(() => currentTheme.value === 'dark' || currentTheme.value === 'dqs-hosting')
  const isDqsSidebar = computed(() => currentTheme.value === 'dqs-hosting' && currentDqsLayout.value === 'sidebar')

  function toggle() {
    currentTheme.value = currentTheme.value === 'light' ? 'dark' : 'light'
    apply()
  }

  function setTheme(theme) {
    currentTheme.value = theme
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
  }

  function init() {
    apply()
  }

  return { currentTheme, currentDqsLayout, isDark, isDqsSidebar, toggle, setTheme, setDqsLayout, toggleDqsLayout, init }
})
