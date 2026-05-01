import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Welcome from '../views/Welcome.vue'
import Dashboard from '../views/Dashboard.vue'
import ServerView from '../views/ServerView.vue'
import Users from '../views/Users.vue'
import Admin from '../views/Admin.vue'
import Themes from '../views/Themes.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/welcome', component: Welcome, meta: { requiresAuth: true } },
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/themes', component: Themes, meta: { requiresAuth: true } },
  { path: '/server/:id', component: ServerView, meta: { requiresAuth: true } },
  { path: '/users', component: Users, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin', component: Admin, meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  if (!authStore.initialized) {
    await authStore.init()
  }

  if (to.meta.requiresAuth && !authStore.user) {
    next('/login')
  } else if (to.meta.requiresAdmin && !authStore.user?.is_admin) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
