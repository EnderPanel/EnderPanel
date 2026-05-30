import { defineStore } from 'pinia'
import axios from 'axios'

axios.defaults.withCredentials = true

let initPromise = null

function getWelcomeStorageKey(user) {
  const username = user?.username || 'guest'
  return `welcome_shown_${username}`
}

function hasCompletedWelcome(user) {
  const userSpecific = localStorage.getItem(getWelcomeStorageKey(user)) === 'true'
  const legacy = localStorage.getItem('welcome_shown') === 'true'
  return Boolean(user?.welcome_completed) || userSpecific || (!userSpecific && legacy)
}

function loadStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    localStorage.removeItem('user')
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: loadStoredUser(),
    initialized: false,
  }),
  actions: {
    async login(username, password, totp_code = null) {
      const { useThemeStore } = await import('./theme')
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)
      if (totp_code) {
        formData.append('totp_code', totp_code)
      }

      const res = await axios.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      this.user = res.data.user
      localStorage.setItem('token', res.data.access_token || '')
      localStorage.setItem('user', JSON.stringify(this.user))
      const themeStore = useThemeStore()
      themeStore.applyUserPreferences(this.user)
      themeStore.ensureUserPreferences(this.user)
      if (hasCompletedWelcome(this.user) && !this.user.welcome_completed) {
        try {
          this.user = await this.updatePreferences({ welcome_completed: true })
        } catch {}
      }
      this.initialized = true
    },
    async register(username, email, password) {
      const { useThemeStore } = await import('./theme')
      const res = await axios.post('/api/auth/register', { username, email, password })
      this.user = res.data.user
      localStorage.setItem('token', res.data.access_token || '')
      localStorage.setItem('user', JSON.stringify(this.user))
      const themeStore = useThemeStore()
      themeStore.applyUserPreferences(this.user)
      themeStore.ensureUserPreferences(this.user)
      this.initialized = true
    },
    logout() {
      axios.post('/api/auth/logout').catch(() => {})
      this.clearSession()
    },
    clearSession() {
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.initialized = true
    },
    async init(force = false) {
      if (this.initialized && !force) {
        return this.user
      }

      if (initPromise && !force) {
        return initPromise
      }

      initPromise = (async () => {
        try {
          const { useThemeStore } = await import('./theme')
          const res = await axios.get('/api/auth/me')
          const sessionToken = res.headers?.['x-enderpanel-token']
          if (sessionToken) {
            localStorage.setItem('token', sessionToken)
          }
          this.user = res.data
          localStorage.setItem('user', JSON.stringify(this.user))
          const themeStore = useThemeStore()
          themeStore.applyUserPreferences(this.user)
          themeStore.ensureUserPreferences(this.user)
          if (hasCompletedWelcome(this.user) && !this.user.welcome_completed) {
            try {
              this.user = await this.updatePreferences({ welcome_completed: true })
            } catch {}
          }
          return this.user
        } catch {
          this.user = null
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          return null
        } finally {
          this.initialized = true
          initPromise = null
        }
      })()

      return initPromise
    },
    async updatePreferences(preferences) {
      const res = await axios.post('/api/auth/preferences', preferences)
      this.user = res.data
      localStorage.setItem('user', JSON.stringify(this.user))
      if (this.user.welcome_completed) {
        localStorage.setItem('welcome_shown', 'true')
        localStorage.setItem(getWelcomeStorageKey(this.user), 'true')
      }
      return this.user
    },
    hasCompletedWelcome() {
      return hasCompletedWelcome(this.user)
    },
  }
})
