import { defineStore } from 'pinia'
import axios from 'axios'

axios.defaults.withCredentials = true

let initPromise = null

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
      this.initialized = true
    },
    async register(username, email, password) {
      const res = await axios.post('/api/auth/register', { username, email, password })
      this.user = res.data.user
      localStorage.setItem('token', res.data.access_token || '')
      localStorage.setItem('user', JSON.stringify(this.user))
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
          const res = await axios.get('/api/auth/me')
          this.user = res.data
          localStorage.setItem('user', JSON.stringify(this.user))
          return this.user
        } catch {
          this.user = null
          localStorage.removeItem('user')
          return null
        } finally {
          localStorage.removeItem('token')
          this.initialized = true
          initPromise = null
        }
      })()

      return initPromise
    }
  }
})
