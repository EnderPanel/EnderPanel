<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold mb-6">Admin Dashboard</h1>

    <!-- Update -->
    <div v-if="updateInfo.update_available" class="card mb-8 flex items-center justify-between" style="border-color: rgba(168,85,247,0.3); background: rgba(168,85,247,0.05);">
      <div>
        <p class="font-semibold">Update Available</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">v{{ updateInfo.current }} → v{{ updateInfo.latest }}</p>
      </div>
      <button @click="installUpdate" :disabled="updating"
        class="px-4 py-2 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-mc-accent to-mc-purple hover:opacity-90 transition disabled:opacity-50">
        {{ updating ? 'Updating...' : 'Update Now' }}
      </button>
    </div>

    <!-- Update Server Config -->
    <div class="card mb-8">
      <h3 class="font-semibold mb-3">Update Server</h3>
      <div class="flex gap-2">
        <input v-model="updateServerUrl" type="text" placeholder="https://enderpanel.space"
          class="flex-1 px-3 py-2 rounded-lg bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-sm outline-none focus:border-mc-accent" />
        <button @click="saveUpdateServer"
          class="px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 transition">
          Save
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
      <div class="card">
        <p class="text-sm text-gray-500 dark:text-gray-400">Servers</p>
        <p class="text-2xl font-bold">{{ stats.counts?.servers || 0 }}</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-500 dark:text-gray-400">Users</p>
        <p class="text-2xl font-bold">{{ stats.counts?.users || 0 }}</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-500 dark:text-gray-400">Docker</p>
        <p class="text-2xl font-bold">{{ stats.docker?.running || 0 }}/{{ stats.docker?.total || 0 }}</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-500 dark:text-gray-400">CPU</p>
        <p class="text-2xl font-bold">{{ stats.system?.cpu_percent || 0 }}%</p>
      </div>
    </div>

    <!-- Usage Graphs -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
      <div class="card">
        <div class="flex justify-between items-center mb-3">
          <h3 class="font-semibold">CPU Usage</h3>
          <span class="text-sm text-gray-500">{{ stats.system?.cpu_percent || 0 }}%</span>
        </div>
        <canvas ref="cpuCanvas" height="80" class="w-full rounded-lg"></canvas>
      </div>
      <div class="card">
        <div class="flex justify-between items-center mb-3">
          <h3 class="font-semibold">Memory Usage</h3>
          <span class="text-sm text-gray-500">{{ stats.system?.memory_percent || 0 }}%</span>
        </div>
        <canvas ref="memCanvas" height="80" class="w-full rounded-lg"></canvas>
      </div>
    </div>

    <!-- Bars -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
      <div class="card">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm text-gray-500 dark:text-gray-400">Memory</span>
          <span class="text-sm font-medium">{{ formatBytes(stats.system?.memory_used) }} / {{ formatBytes(stats.system?.memory_total) }}</span>
        </div>
        <div class="h-2 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-mc-accent to-mc-purple rounded-full transition-all" :style="{width: (stats.system?.memory_percent || 0) + '%'}"></div>
        </div>
      </div>
      <div class="card">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm text-gray-500 dark:text-gray-400">Disk</span>
          <span class="text-sm font-medium">{{ formatBytes(stats.system?.disk_used) }} / {{ formatBytes(stats.system?.disk_total) }}</span>
        </div>
        <div class="h-2 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-mc-accent to-mc-purple rounded-full transition-all" :style="{width: (stats.system?.disk_percent || 0) + '%'}"></div>
        </div>
      </div>
    </div>

    <!-- All Servers -->
    <div class="card">
      <h3 class="font-semibold mb-4">All Servers</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10">
              <th class="pb-2 pr-4">Name</th>
              <th class="pb-2 pr-4">Type</th>
              <th class="pb-2 pr-4">Version</th>
              <th class="pb-2 pr-4">Port</th>
              <th class="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="server in stats.servers" :key="server.id" class="border-b border-gray-100 dark:border-white/5">
              <td class="py-2.5 pr-4 font-medium">{{ server.name }}</td>
              <td class="py-2.5 pr-4">{{ server.type }}</td>
              <td class="py-2.5 pr-4">{{ server.version }}</td>
              <td class="py-2.5 pr-4">{{ server.port }}</td>
              <td class="py-2.5">
                <span :class="statusClass(server.status)" class="px-2 py-0.5 rounded text-xs font-medium">{{ server.status }}</span>
              </td>
            </tr>
            <tr v-if="!stats.servers?.length">
              <td colspan="5" class="py-4 text-center text-gray-500">No servers</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'

const stats = ref({})
const updateInfo = ref({})
const updating = ref(false)
const cpuCanvas = ref(null)
const memCanvas = ref(null)
let interval

function drawGraph(canvas, data, color) {
  if (!canvas || !data || data.length < 2) return
  const ctx = canvas.getContext('2d')
  const w = canvas.width = canvas.offsetWidth * 2
  const h = canvas.height = 160
  ctx.clearRect(0, 0, w, h)

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'
  ctx.lineWidth = 1
  for (let i = 0; i <= 4; i++) {
    const y = (h / 4) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }

  // Line
  const step = w / (data.length - 1)
  ctx.beginPath()
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.lineJoin = 'round'

  data.forEach((v, i) => {
    const x = i * step
    const y = h - (v / 100) * h
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()

  // Fill
  ctx.lineTo(w, h)
  ctx.lineTo(0, h)
  ctx.closePath()
  const grad = ctx.createLinearGradient(0, 0, 0, h)
  grad.addColorStop(0, color.replace(')', ',0.3)').replace('rgb', 'rgba'))
  grad.addColorStop(1, color.replace(')', ',0)').replace('rgb', 'rgba'))
  ctx.fillStyle = grad
  ctx.fill()
}

async function fetchStats() {
  try {
    const res = await axios.get('/api/admin/stats')
    stats.value = res.data
    await nextTick()
    if (res.data.history) {
      drawGraph(cpuCanvas.value, res.data.history.cpu, 'rgb(168,85,247)')
      drawGraph(memCanvas.value, res.data.history.memory, 'rgb(236,72,153)')
    }
  } catch (e) {}
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
    alert('Updated! Please restart the panel.')
    location.reload()
  } catch (e) {
    alert('Update failed: ' + (e.response?.data?.detail || 'Unknown error'))
  } finally {
    updating.value = false
  }
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++ }
  return bytes.toFixed(1) + ' ' + units[i]
}

function statusClass(status) {
  if (status === 'running') return 'bg-green-500/10 text-green-600 dark:text-green-400'
  if (status === 'exited' || status === 'stopped') return 'bg-red-500/10 text-red-600 dark:text-red-400'
  return 'bg-gray-100 dark:bg-white/5 text-gray-500'
}

onMounted(() => {
  fetchStats()
  checkUpdate()
  interval = setInterval(fetchStats, 15000)
})

onUnmounted(() => clearInterval(interval))
</script>

<style scoped>
.card {
  @apply bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl p-4;
}
canvas {
  image-rendering: auto;
}
</style>
