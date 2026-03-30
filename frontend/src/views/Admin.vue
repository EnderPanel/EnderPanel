<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold mb-6">Admin Dashboard</h1>

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

    <!-- System Resources -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
      <div class="card">
        <h3 class="font-semibold mb-3">Memory</h3>
        <div class="h-3 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-mc-accent to-mc-purple rounded-full transition-all" :style="{width: (stats.system?.memory_percent || 0) + '%'}"></div>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">{{ formatBytes(stats.system?.memory_used) }} / {{ formatBytes(stats.system?.memory_total) }} ({{ stats.system?.memory_percent || 0 }}%)</p>
      </div>
      <div class="card">
        <h3 class="font-semibold mb-3">Disk</h3>
        <div class="h-3 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-mc-accent to-mc-purple rounded-full transition-all" :style="{width: (stats.system?.disk_percent || 0) + '%'}"></div>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">{{ formatBytes(stats.system?.disk_used) }} / {{ formatBytes(stats.system?.disk_total) }} ({{ stats.system?.disk_percent || 0 }}%)</p>
      </div>
    </div>

    <!-- All Servers -->
    <div class="card mb-8">
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
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const stats = ref({})
let interval

async function fetchStats() {
  try {
    const res = await axios.get('/api/admin/stats')
    stats.value = res.data
  } catch (e) {}
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
  interval = setInterval(fetchStats, 10000)
})

onUnmounted(() => clearInterval(interval))
</script>

<style scoped>
.card {
  @apply bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl p-4;
}
</style>
