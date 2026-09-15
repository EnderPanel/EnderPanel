import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './style.css'

axios.defaults.withCredentials = true

function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`
  const match = document.cookie.split('; ').find(value => value.startsWith(prefix))
  return match ? decodeURIComponent(match.slice(prefix.length)) : null
}

axios.interceptors.request.use((config) => {
  const requestUrl = String(config.url || '')
  const method = String(config.method || 'get').toLowerCase()
  if (requestUrl.startsWith('/api') && !['get', 'head', 'options'].includes(method)) {
    const csrfToken = readCookie('csrf_token')
    config.headers = config.headers || {}
    if (csrfToken) config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

const pinia = createPinia()
const app = createApp(App)
app.use(pinia)
app.use(router)

import { useAuthStore } from './stores/auth'

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      const requestUrl = String(error.config?.url || '')
      const authStore = useAuthStore()
      authStore.clearSession()

      if (!requestUrl.includes('/api/auth/me') && router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

async function bootstrap() {
  const authStore = useAuthStore()
  await authStore.init()
  app.mount('#app')
}

bootstrap()
