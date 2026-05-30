import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './style.css'

axios.defaults.withCredentials = true

axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const requestUrl = String(config.url || '')
  if (token && requestUrl.startsWith('/api') && !config.headers?.Authorization) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
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
