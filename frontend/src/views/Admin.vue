<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 min-h-screen dqs-page-shell dqs-admin-page">
    <!-- Header Area -->
    <div class="flex items-center justify-between mb-8 dqs-page-header">
      <div>
        <p class="dqs-overline">Control Center</p>
        <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-mc-accent to-mc-purple">
          Admin Dashboard
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">System overview & metrics</p>
      </div>
      <div v-if="stats.system?.uptime_seconds !== undefined" class="text-sm font-medium px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
        <span class="text-gray-400 mr-2">Uptime:</span>
        <span class="text-mc-accent">{{ formatUptime(stats.system.uptime_seconds) }}</span>
      </div>
    </div>

    <!-- Update Banner -->
    <div v-if="updateInfo.update_available" 
         class="glass-panel group mb-8 p-6 flex flex-col sm:flex-row items-center justify-between border-mc-accent/40 bg-mc-accent/5 overflow-hidden relative">
      <div class="absolute inset-0 bg-gradient-to-r from-mc-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      <div class="relative z-10 flex items-center gap-4 mb-4 sm:mb-0">
        <div class="p-3 bg-mc-accent/20 rounded-full">
          <svg class="w-6 h-6 text-mc-accent animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
        </div>
        <div>
          <h3 class="font-bold text-lg">Update Available</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">Version {{ updateInfo.current }} <span class="mx-2">&rarr;</span> Version {{ updateInfo.latest }}</p>
        </div>
      </div>
      <button @click="installUpdate" :disabled="updating"
        class="relative z-10 px-6 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-mc-accent to-mc-purple hover:scale-105 active:scale-95 shadow-lg shadow-mc-accent/20 transition-all disabled:opacity-50 disabled:scale-100">
        {{ updating ? 'Updating...' : 'Update Panel Now' }}
      </button>
    </div>

    <div v-if="!dockerAvailable" class="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-400/20 text-rose-700 dark:text-rose-200 backdrop-blur-md">
      <div class="flex items-start gap-3">
        <div class="mt-0.5">
          <svg class="w-5 h-5 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M10.29 3.86l-7.4 2.7a1 1 0 00-.64 1.28l2.2 7.52a1 1 0 001.28.64l7.4-2.7a1 1 0 00.64-1.28l-2.2-7.52a1 1 0 00-1.28-.64z"></path></svg>
        </div>
        <div>
          <h2 class="font-semibold text-lg">Docker is not running</h2>
          <p class="text-sm text-rose-600 dark:text-rose-200/90">The admin panel cannot access the Docker daemon. Start Docker to restore server management and container visibility.</p>
        </div>
      </div>
    </div>

    <!-- Top Bento Grid: Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      
      <!-- Servers Card -->
      <div class="glass-panel p-6 flex items-center justify-between hover-card dqs-stat-card">
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Servers Operated</p>
          <p class="text-3xl font-bold">{{ stats.counts?.servers || 0 }}</p>
        </div>
        <div class="p-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/5 text-blue-500">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"></path></svg>
        </div>
      </div>

      <!-- Users Card -->
      <div class="glass-panel p-6 flex items-center justify-between hover-card dqs-stat-card">
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Users</p>
          <p class="text-3xl font-bold">{{ stats.counts?.users || 0 }}</p>
        </div>
        <div class="p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/5 text-purple-500">
           <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        </div>
      </div>

      <!-- Docker Containers Card -->
      <div class="glass-panel p-6 flex items-center justify-between hover-card dqs-stat-card">
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Docker Nodes</p>
          <div class="flex items-baseline gap-1">
            <p class="text-3xl font-bold">{{ stats.docker?.running || 0 }}</p>
            <p class="text-lg text-gray-500">/ {{ stats.docker?.total || 0 }}</p>
          </div>
        </div>
        <div class="p-4 rounded-xl bg-gradient-to-br from-mc-accent/20 to-mc-accent/5 text-mc-accent">
           <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
      </div>

      <!-- CPU Percent Card -->
      <div class="glass-panel p-6 flex flex-col justify-between hover-card relative overflow-hidden dqs-stat-card">
        <div class="absolute bottom-0 inset-x-0 h-1 bg-gray-200 dark:bg-white/5">
          <div class="h-full bg-gradient-to-r from-red-500 to-orange-400 transition-all duration-500" :style="{width: (stats.system?.cpu_percent || 0) + '%'}"></div>
        </div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">CPU Usage</p>
          <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <p class="text-4xl font-black mb-2">{{ stats.system?.cpu_percent || 0 }}<span class="text-2xl text-gray-500 font-medium">%</span></p>
      </div>

    </div>

    <!-- Usage Graphs Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- CPU Graph -->
      <div class="glass-panel p-6 hover-card flex flex-col">
        <div class="flex justify-between items-center mb-6">
          <div class="flex items-center gap-3">
             <div class="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.7)]"></div>
             <h3 class="font-bold text-lg">CPU History</h3>
          </div>
          <span class="text-sm font-medium bg-purple-500/10 text-purple-400 px-3 py-1 rounded-full border border-purple-500/20">
            {{ stats.system?.cpu_percent || 0 }}% Load
          </span>
        </div>
        <div class="flex-1 w-full relative">
          <canvas ref="cpuCanvas" class="w-full h-[180px] rounded-lg"></canvas>
        </div>
      </div>

      <!-- Memory Graph -->
      <div class="glass-panel p-6 hover-card flex flex-col">
        <div class="flex justify-between items-center mb-6">
          <div class="flex items-center gap-3">
             <div class="w-3 h-3 rounded-full bg-pink-500 shadow-[0_0_10px_rgba(236,72,153,0.7)]"></div>
             <h3 class="font-bold text-lg">Memory History</h3>
          </div>
          <span class="text-sm font-medium bg-pink-500/10 text-pink-400 px-3 py-1 rounded-full border border-pink-500/20">
            {{ stats.system?.memory_percent || 0 }}% Load
          </span>
        </div>
        <div class="flex-1 w-full relative">
          <canvas ref="memCanvas" class="w-full h-[180px] rounded-lg"></canvas>
        </div>
      </div>
    </div>

    <!-- Storage & Network Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- Memory Bar -->
      <div class="glass-panel p-6 hover-card flex flex-col justify-center">
        <div class="flex justify-between items-center mb-4">
          <div class="flex items-center gap-2 text-gray-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
            <span class="font-medium">RAM Allocation</span>
          </div>
          <span class="text-sm font-bold">{{ formatBytes(stats.system?.memory_used) }} / {{ formatBytes(stats.system?.memory_total) }}</span>
        </div>
        <div class="h-3 w-full bg-gray-200 dark:bg-black/40 rounded-full overflow-hidden border border-white/5 shadow-inner">
          <div class="h-full bg-gradient-to-r from-pink-500 to-rose-400 rounded-full transition-all duration-1000 ease-out" 
               :style="{width: (stats.system?.memory_percent || 0) + '%'}"></div>
        </div>
      </div>

      <!-- Disk Bar -->
      <div class="glass-panel p-6 hover-card flex flex-col justify-center">
        <div class="flex justify-between items-center mb-4">
          <div class="flex items-center gap-2 text-gray-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
            <span class="font-medium">Disk Storage</span>
          </div>
          <span class="text-sm font-bold">{{ formatBytes(stats.system?.disk_used) }} / {{ formatBytes(stats.system?.disk_total) }}</span>
        </div>
        <div class="h-3 w-full bg-gray-200 dark:bg-black/40 rounded-full overflow-hidden border border-white/5 shadow-inner">
          <div class="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-1000 ease-out" 
               :style="{width: (stats.system?.disk_percent || 0) + '%'}"></div>
        </div>
      </div>

      <!-- Network I/O -->
      <div class="glass-panel p-6 hover-card flex flex-row items-center justify-between">
        <div class="flex-1 border-r border-gray-200 dark:border-white/10 pr-4">
          <div class="flex items-center gap-2 text-green-500 mb-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12"></path></svg>
            <span class="text-xs font-bold uppercase tracking-wider">Sent (TX)</span>
          </div>
          <span class="text-xl font-bold truncate">{{ formatBytes(stats.system?.net_sent) }}</span>
        </div>
        <div class="flex-1 pl-4">
          <div class="flex items-center gap-2 text-blue-500 mb-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6"></path></svg>
            <span class="text-xs font-bold uppercase tracking-wider">Recv (RX)</span>
          </div>
          <span class="text-xl font-bold truncate">{{ formatBytes(stats.system?.net_recv) }}</span>
        </div>
      </div>
    </div>

    <!-- Active Deployments (Servers) -->
    <div class="glass-panel overflow-hidden hover-card">
      <div class="p-6 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
        <h3 class="font-bold text-lg flex items-center gap-2">
          <svg class="w-5 h-5 text-mc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
          Active Deployments
        </h3>
        <span class="text-sm bg-black/20 px-3 py-1 rounded-full text-gray-400 shadow-inner">Total: {{ stats.servers?.length || 0 }}</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left dqs-data-table">
          <thead>
            <tr class="bg-gray-50 dark:bg-white/[0.02] text-gray-500 dark:text-gray-400 text-xs uppercase tracking-wider">
              <th class="py-3 px-6 font-medium">Server Name</th>
              <th class="py-3 px-6 font-medium">Architecture</th>
              <th class="py-3 px-6 font-medium">Version</th>
              <th class="py-3 px-6 font-medium">Port Assignment</th>
              <th class="py-3 px-6 font-medium text-right">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/5">
            <tr v-for="server in stats.servers" :key="server.id" class="transition-colors hover:bg-gray-50 dark:hover:bg-white/5">
              <td class="py-4 px-6 font-bold text-gray-900 dark:text-white flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-mc-accent/20 to-transparent flex items-center justify-center border border-mc-accent/20">
                  <span class="text-mc-accent font-bold text-sm">{{ server.name.charAt(0).toUpperCase() }}</span>
                </div>
                {{ server.name }}
              </td>
              <td class="py-4 px-6 text-sm">
                <span class="px-2 py-1 rounded-md bg-white/10 border border-white/5 text-xs text-gray-300">{{ server.type }}</span>
              </td>
              <td class="py-4 px-6 text-sm text-gray-600 dark:text-gray-300">{{ server.version }}</td>
              <td class="py-4 px-6">
                <span class="font-mono text-xs px-2 py-1 bg-black/20 rounded text-gray-400 shadow-inner">TCP:{{ server.port }}</span>
              </td>
              <td class="py-4 px-6 text-right">
                <span :class="statusClass(server.status)" class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider relative flex items-center gap-1.5 display-inline-flex justify-end w-max ml-auto shadow-sm">
                  <span v-if="server.status === 'running'" class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                  {{ server.status }}
                </span>
              </td>
            </tr>
            <tr v-if="!stats.servers?.length">
              <td colspan="5" class="py-8 text-center text-gray-500">
                <div class="flex flex-col items-center justify-center gap-2">
                  <svg class="w-10 h-10 text-gray-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
                  <p>No active deployments found.</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, nextTick } from 'vue'
import axios from 'axios'

const toast = inject('toast')

const stats = ref({})
const updateInfo = ref({})
const updating = ref(false)
const dockerAvailable = computed(() => stats.value.docker?.available !== false)
const cpuCanvas = ref(null)
const memCanvas = ref(null)
let interval

function drawBezierGraph(canvas, data, hexColor) {
  if (!canvas || !data || data.length < 2) return
  const ctx = canvas.getContext('2d')
  
  // High DPI canvas scaling
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)
  
  const w = rect.width
  const h = rect.height
  ctx.clearRect(0, 0, w, h)

  // Subtle grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.03)'
  ctx.lineWidth = 1
  for (let i = 0; i <= 4; i++) {
    const y = (h / 4) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }

  const step = w / (data.length - 1)
  const points = data.map((v, i) => ({
    x: i * step,
    y: h - (v / 100) * h * 0.9 - (h * 0.05) // Leave 5% padding top and bottom
  }))

  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)

  // Draw Bezier Curve
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i]
    const p1 = points[i + 1]
    const midX = (p0.x + p1.x) / 2
    ctx.bezierCurveTo(midX, p0.y, midX, p1.y, p1.x, p1.y)
  }

  // Neon line styling
  ctx.strokeStyle = hexColor
  ctx.lineWidth = 3
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  ctx.shadowColor = hexColor
  ctx.shadowBlur = 10
  ctx.shadowOffsetX = 0
  ctx.shadowOffsetY = 0
  ctx.stroke()

  // Reset shadow for fill
  ctx.shadowBlur = 0
  
  // Fill gradient
  ctx.lineTo(w, h)
  ctx.lineTo(0, h)
  ctx.closePath()

  const [_, r, g, b] = hexColor.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i) || [0, 168, 85, 247]
  const rgb = r && g && b ? `${parseInt(r, 16)}, ${parseInt(g, 16)}, ${parseInt(b, 16)}` : '168, 85, 247'
  
  const grad = ctx.createLinearGradient(0, 0, 0, h)
  grad.addColorStop(0, `rgba(${rgb}, 0.35)`)
  grad.addColorStop(1, `rgba(${rgb}, 0.0)`)
  
  ctx.fillStyle = grad
  ctx.fill()
}

async function fetchStats() {
  try {
    const res = await axios.get('/api/admin/stats')
    stats.value = res.data
    await nextTick()
    if (res.data.history) {
      // #A855F7 is purple, #EC4899 is pink
      drawBezierGraph(cpuCanvas.value, res.data.history.cpu, '#A855F7')
      drawBezierGraph(memCanvas.value, res.data.history.memory, '#EC4899')
    }
  } catch (e) {
    console.warn("Failed to fetch admin stats")
  }
}

async function checkUpdate() {
  try {
    const res = await axios.get('/api/update/check')
    updateInfo.value = res.data
  } catch (e) {}
}

async function installUpdate() {
  updating.value = true
  try {
    await axios.post('/api/update/install')
    toast({ title: 'Update complete!', message: 'Restarting panel...', type: 'success' })
    setTimeout(() => location.reload(), 1500)
  } catch (e) {
    toast({ title: 'Update failed', message: e.response?.data?.detail || 'Unknown error', type: 'error' })
  } finally {
    updating.value = false
  }
}

function formatBytes(bytes) {
  if (bytes === undefined || bytes === null || isNaN(bytes)) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { 
    size /= 1024
    i++ 
  }
  return size.toFixed(2) + ' ' + units[i]
}

function formatUptime(seconds) {
  if (seconds === undefined) return "Unknown"
  const d = Math.floor(seconds / (3600*24))
  const h = Math.floor(seconds % (3600*24) / 3600)
  const m = Math.floor(seconds % 3600 / 60)
  if (d > 0) return `${d}d ${h}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function statusClass(status) {
  if (status === 'running') return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
  if (status === 'exited' || status === 'stopped') return 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
  return 'bg-gray-500/10 text-gray-400 border border-gray-500/20'
}

let resizeHandler

onMounted(() => {
  fetchStats()
  checkUpdate()
  interval = setInterval(fetchStats, 5000)

  resizeHandler = () => {
    if (stats.value.history) {
      drawBezierGraph(cpuCanvas.value, stats.value.history.cpu, '#A855F7')
      drawBezierGraph(memCanvas.value, stats.value.history.memory, '#EC4899')
    }
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  clearInterval(interval)
  window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
.glass-panel {
  @apply bg-white dark:bg-[#111111]/80 backdrop-blur-xl border border-gray-200 dark:border-white/[0.08] shadow-xl shadow-black/5 rounded-2xl;
}

.hover-card {
  @apply transition-transform duration-300 transform-gpu hover:-translate-y-1 hover:shadow-2xl hover:shadow-mc-accent/10 hover:border-mc-accent/30;
}

canvas {
  image-rendering: auto;
}
</style>
