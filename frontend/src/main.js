import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './style.css'

axios.defaults.withCredentials = true

const pinia = createPinia()
const app = createApp(App)
app.use(pinia)
app.use(router)

import { useAuthStore } from './stores/auth'

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore()
      authStore.clearSession()
      
      if (router.currentRoute.value.path !== '/login') {
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
