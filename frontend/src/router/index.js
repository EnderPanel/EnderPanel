import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const Welcome = () => import('../views/Welcome.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const ServerView = () => import('../views/ServerView.vue')
const Users = () => import('../views/Users.vue')
const Admin = () => import('../views/Admin.vue')
const Themes = () => import('../views/Themes.vue')

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
  } else if (to.path === '/welcome' && authStore.hasCompletedWelcome()) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
