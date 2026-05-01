<template>
  <div class="max-w-[1500px] mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8 dqs-page-shell dqs-dashboard-page">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8 animate-fade-up dqs-page-header">
      <div>
        <p class="dqs-overline">Hosting Overview</p>
        <h1 class="text-3xl font-bold dqs-page-title">Your Servers</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">{{ servers.length }} server{{ servers.length !== 1 ? 's' : '' }}</p>
      </div>
      <button @click="showCreate = true" class="btn-success flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
        </svg>
        New Server
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="flex flex-col items-center gap-4">
        <div class="w-12 h-12 border-4 border-mc-accent/20 border-t-mc-accent rounded-full animate-spin"></div>
        <p class="text-gray-500 dark:text-gray-400">Loading servers...</p>
      </div>
    </div>

    <div v-else-if="servers.length === 0" class="text-center py-20 animate-fade-up">
      <div class="inline-flex items-center justify-center w-24 h-24 bg-mc-accent/10 rounded-3xl mb-6 animate-float">
        <span class="text-5xl">&#x26cf;</span>
      </div>
      <h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-200 mb-2">No servers yet</h2>
      <p class="text-gray-500 dark:text-gray-500 mb-6">Create your first Minecraft server to get started</p>
      <button @click="showCreate = true" class="btn-success">Create Server</button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6 animate-stagger">
      <div v-for="server in servers" :key="server.id"
        class="card-hover p-4 sm:p-6 cursor-pointer group dqs-server-card"
        @click="$router.push(`/server/${server.id}`)">
        <div class="flex justify-between items-start mb-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl overflow-hidden flex items-center justify-center
                        group-hover:shadow-lg group-hover:shadow-mc-accent/20 transition-all duration-300 group-hover:scale-110">
              <img v-if="server.avatar" :src="server.avatar" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-gradient-to-br from-mc-accent to-mc-purple flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"/>
                </svg>
              </div>
            </div>
            <div>
              <h3 class="font-semibold text-lg">{{ server.name }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-500 capitalize">{{ server.server_type }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span :class="server.status === 'running' ? 'status-dot-running' : 'status-dot-stopped'"></span>
            <span :class="server.status === 'running' ? 'badge-running' : 'badge-stopped'">
              {{ server.status }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 text-sm mb-5">
          <div class="bg-gray-100 dark:bg-white/5 rounded-xl p-3 col-span-2 dqs-server-meta">
            <p class="text-gray-500 dark:text-gray-500 text-xs mb-1 dqs-metric-label">Address</p>
            <p class="font-medium font-mono break-all dqs-metric-value">{{ getServerAddress(server) }}</p>
          </div>
          <div class="bg-gray-100 dark:bg-white/5 rounded-xl p-3 dqs-server-meta">
            <p class="text-gray-500 dark:text-gray-500 text-xs mb-1 dqs-metric-label">Version</p>
            <p class="font-medium">{{ server.version }}</p>
          </div>
          <div class="bg-gray-100 dark:bg-white/5 rounded-xl p-3 dqs-server-meta">
            <p class="text-gray-500 dark:text-gray-500 text-xs mb-1 dqs-metric-label">Port</p>
            <p class="font-medium">{{ server.port }}</p>
          </div>
          <div class="bg-gray-100 dark:bg-white/5 rounded-xl p-3 dqs-server-meta">
            <p class="text-gray-500 dark:text-gray-500 text-xs mb-1 dqs-metric-label">RAM</p>
            <p class="font-medium">{{ server.ram_max }}MB</p>
          </div>
          <div class="bg-gray-100 dark:bg-white/5 rounded-xl p-3 dqs-server-meta">
            <p class="text-gray-500 dark:text-gray-500 text-xs mb-1 dqs-metric-label">CPU</p>
            <p class="font-medium">{{ server.cpu_cores }} core{{ server.cpu_cores > 1 ? 's' : '' }}</p>
          </div>
        </div>

        <div class="flex gap-2">
          <button @click.stop="startServer(server)" v-if="server.status !== 'running'"
            class="flex-1 bg-emerald-100 dark:bg-emerald-500/20 hover:bg-emerald-200 dark:hover:bg-emerald-500/30 
                   text-emerald-700 dark:text-emerald-400 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center justify-center gap-1">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
            </svg>
            Start
          </button>
          <button @click.stop="stopServer(server.id)" v-if="server.status === 'running'"
            class="flex-1 bg-red-100 dark:bg-red-500/20 hover:bg-red-200 dark:hover:bg-red-500/30 
                   text-red-700 dark:text-red-400 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center justify-center gap-1">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
            </svg>
            Stop
          </button>
          <button @click.stop="restartServer(server.id)" v-if="server.status === 'running'"
            class="flex-1 bg-yellow-100 dark:bg-yellow-500/20 hover:bg-yellow-200 dark:hover:bg-yellow-500/30 
                   text-yellow-700 dark:text-yellow-400 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center justify-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Restart
          </button>
          <button @click.stop="confirmDelete(server)"
            class="p-2 bg-red-100 dark:bg-red-500/10 hover:bg-red-200 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-xl transition-all duration-200">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <transition name="modal">
      <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="glass rounded-2xl p-5 sm:p-8 w-full max-w-md scale-in dqs-modal-card">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-12 h-12 bg-red-100 dark:bg-red-500/20 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
            </div>
            <div>
              <h2 class="text-xl font-bold text-red-600 dark:text-red-400">Delete Server</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">This action cannot be undone</p>
            </div>
          </div>
          <p class="text-gray-600 dark:text-gray-300 mb-5">Are you sure you want to delete <strong class="text-gray-900 dark:text-white">{{ deletingServer?.name }}</strong>?</p>
          <div class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl p-4 mb-6">
            <ul class="text-red-600 dark:text-red-400 text-sm space-y-1">
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                All server files will be permanently deleted
              </li>
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                World data and player progress will be lost
              </li>
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                Plugins and configurations will be removed
              </li>
            </ul>
          </div>
          <div class="flex gap-3">
            <button @click="showDeleteConfirm = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
            <button @click="deleteServer" class="flex-1 btn-danger">Delete</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showCreate" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="showCreate = false">
        <div class="glass rounded-2xl p-4 sm:p-8 w-full max-w-lg max-h-[90vh] overflow-y-auto scale-in dqs-modal-card">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold">Create New Server</h2>
            <button @click="showCreate = false" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <transition name="fade">
            <div v-if="downloadStatus" class="mb-5 p-4 rounded-xl flex items-center gap-3" 
              :class="{
                'bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/30 text-yellow-700 dark:text-yellow-400': downloadStatus === 'downloading',
                'bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400': downloadStatus === 'success',
                'bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-red-700 dark:text-red-400': downloadStatus === 'error'
              }">
              <svg v-if="downloadStatus === 'downloading'" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else-if="downloadStatus === 'success'" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              <span class="text-sm font-medium">
                {{ downloadStatus === 'downloading' ? `Downloading ${newServer.server_type} server.jar...` : downloadStatus === 'success' ? 'Server.jar downloaded!' : 'Failed to download server.jar' }}
              </span>
            </div>
          </transition>
          <p v-if="versionWarning" class="mb-4 text-xs text-yellow-700 dark:text-yellow-400">
            {{ versionWarning }}
          </p>

          <form @submit.prevent="createServer" class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Server Name</label>
              <input v-model="newServer.name" type="text" required placeholder="My Server"
                class="input-field" />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Server Type</label>
              <div class="flex gap-2">
                <button v-for="type in serverTypes" :key="type.id" type="button" 
                  @click="selectServerType(type.id)"
                  :class="newServer.server_type === type.id 
                    ? 'bg-gradient-to-r from-mc-accent to-blue-500 text-white shadow-lg shadow-mc-accent/20' 
                    : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white'"
                  class="flex-1 py-2.5 px-3 rounded-xl text-sm font-medium transition-all duration-200 border border-gray-200 dark:border-white/5 whitespace-nowrap">
                  {{ type.name }}
                </button>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Port</label>
                <input v-model.number="newServer.port" type="number" required
                  class="input-field" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Max Players</label>
                <input v-model.number="newServer.max_players" type="number" required
                  class="input-field" />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Version</label>
              <select v-model="newServer.version" class="input-field" :disabled="versionsLoading">
                <option v-if="versionsLoading" value="">Loading versions...</option>
                <option v-else-if="versions.length === 0" value="">No versions available</option>
                <option v-for="v in versions" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>

            <div class="border-t border-gray-200 dark:border-white/5 pt-5">
              <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Resources</h3>
              <div class="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Min RAM (MB)</label>
                  <input v-model.number="newServer.ram_min" type="number" min="256" step="256" required
                    class="input-field text-sm" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Max RAM (MB)</label>
                  <input v-model.number="newServer.ram_max" type="number" min="256" step="256" required
                    class="input-field text-sm" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">CPU Cores</label>
                  <input v-model.number="newServer.cpu_cores" type="number" min="1" max="16" required
                    class="input-field text-sm" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Swap (MB)</label>
                  <input v-model.number="newServer.swap_mb" type="number" min="0" step="256" required
                    class="input-field text-sm" />
                </div>
              </div>
              <div class="flex gap-2 flex-wrap">
                <button type="button" @click="setPreset(512, 1024, 1)" 
                  class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-3 py-1.5 rounded-lg transition">512MB-1GB</button>
                <button type="button" @click="setPreset(1024, 2048, 2)" 
                  class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-3 py-1.5 rounded-lg transition">1GB-2GB</button>
                <button type="button" @click="setPreset(2048, 4096, 4)" 
                  class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-3 py-1.5 rounded-lg transition">2GB-4GB</button>
                <button type="button" @click="setPreset(4096, 8192, 4)" 
                  class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-3 py-1.5 rounded-lg transition">4GB-8GB</button>
              </div>
            </div>

            <div class="flex gap-3 pt-4">
              <button type="button" @click="showCreate = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
              <button type="submit" :disabled="creating" class="flex-1 btn-primary">
                {{ creating ? 'Creating...' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showEulaModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="showEulaModal = false">
        <div class="glass rounded-2xl p-5 sm:p-8 w-full max-w-md scale-in dqs-modal-card">
          <div class="flex items-start gap-4 mb-5">
            <div class="w-12 h-12 bg-mc-accent/10 rounded-2xl flex items-center justify-center text-mc-accent">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M4.93 4.93a10 10 0 0114.14 0 10 10 0 010 14.14 10 10 0 01-14.14 0 10 10 0 010-14.14z"/>
              </svg>
            </div>
            <div class="flex-1">
              <h2 class="text-xl font-bold">Accept Minecraft EULA</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">You must accept the Minecraft End User License Agreement before this server can start for the first time.</p>
            </div>
          </div>

          <div class="space-y-4 mb-6 text-sm text-gray-600 dark:text-gray-300">
            <p>This action creates an <code class="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">eula.txt</code> file with <code class="font-mono">eula=true</code>.</p>
            <p>Read the official Mojang EULA here: <a href="https://account.mojang.com/documents/minecraft_eula" target="_blank" class="text-mc-accent hover:underline">https://account.mojang.com/documents/minecraft_eula</a></p>
            <p class="text-xs text-gray-500 dark:text-gray-500">This is required by Mojang before running a Minecraft server.</p>
          </div>

          <div class="flex gap-3 flex-col sm:flex-row-reverse">
            <button @click="acceptEula" class="btn-success flex-1 py-3">Accept & Start</button>
            <button @click="showEulaModal = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import axios from 'axios'

const toast = inject('toast', (opts) => alert(opts.title + (opts.message ? ': ' + opts.message : '')))
const confirmFn = inject('confirm', (opts) => Promise.resolve(confirm(opts.title + '\n' + opts.message)))

const servers = ref([])
const loading = ref(true)
const showCreate = ref(false)
const creating = ref(false)
const downloadStatus = ref('')
const showDeleteConfirm = ref(false)
const deletingServer = ref(null)
const showEulaModal = ref(false)
const eulaServer = ref(null)
const newServer = ref({ name: '', server_type: 'paper', port: 25565, max_players: 20, version: '', ram_min: 512, ram_max: 1024, cpu_cores: 1, swap_mb: 512 })

const serverTypes = [
  { id: 'paper', name: 'Paper' },
  { id: 'vanilla', name: 'Vanilla' },
  { id: 'fabric', name: 'Fabric' },
  { id: 'forge', name: 'Forge' },
  { id: 'neoforge', name: 'NeoForge' },
]

const versions = ref([])
const versionsLoading = ref(false)
const versionWarning = ref('')
const versionCache = {}
const currentHost = window.location.hostname || 'localhost'

function getServerAddress(server) {
  return server.playit_domain || `${currentHost}:${server.port}`
}

async function fetchVersions(serverType) {
  if (versionCache[serverType]) {
    versions.value = versionCache[serverType]
    if (versions.value.length > 0) {
      newServer.value.version = versions.value[0]
    }
    return
  }
  versionsLoading.value = true
  versions.value = []
  newServer.value.version = ''
  versionWarning.value = ''
  try {
    const res = await axios.get(`/api/servers/versions/${serverType}`)
    versionCache[serverType] = res.data.versions
    versions.value = res.data.versions
    if (res.data.fallback_used) {
      versionWarning.value = 'Using built-in fallback versions because the upstream version service could not be reached.'
    }
    if (versions.value.length > 0) {
      newServer.value.version = versions.value[0]
    }
  } catch (e) {
    console.error(`Failed to fetch versions for ${serverType}:`, e)
    versions.value = []
    versionWarning.value = 'Could not load versions from the backend.'
  } finally {
    versionsLoading.value = false
  }
}

function selectServerType(type) {
  newServer.value.server_type = type
  fetchVersions(type)
}

function setPreset(min, max, cores) {
  newServer.value.ram_min = min
  newServer.value.ram_max = max
  newServer.value.cpu_cores = cores
  newServer.value.swap_mb = Math.max(512, Math.floor(max / 2))
}

async function fetchServers() {
  loading.value = true
  try {
    const res = await axios.get('/api/servers/')
    servers.value = res.data
  } catch (e) {
    console.error('Failed to load servers:', e)
    toast({ title: 'Failed to load servers', message: e.response?.data?.detail || 'Please try again.', type: 'error' })
  } finally {
    loading.value = false
  }
}

async function createServer() {
  creating.value = true
  downloadStatus.value = 'downloading'
  try {
    const res = await axios.post('/api/servers/', newServer.value)
    if (res.data.port_changed) {
      toast({ title: `Port ${res.data.original_port} was in use`, message: `Server created on port ${res.data.port}.`, type: 'warning' })
    }
    if (res.data.jar_downloaded) {
      downloadStatus.value = 'success'
    } else {
      downloadStatus.value = 'error'
      toast({ title: 'Download Failed', message: res.data.download_error || 'Failed to download server.jar', type: 'error' })
    }
    setTimeout(() => {
      showCreate.value = false
      downloadStatus.value = ''
      creating.value = false
      newServer.value = { name: '', server_type: 'paper', port: 25565, max_players: 20, version: '', ram_min: 512, ram_max: 1024, cpu_cores: 1, swap_mb: 512 }
    }, 1500)
    await fetchServers()
  } catch (e) {
    downloadStatus.value = 'error'
    creating.value = false
  }
}

async function startServer(server) {
  try {
    if (server && !server.eula_accepted) {
      eulaServer.value = server
      showEulaModal.value = true
      return
    }

    await axios.post(`/api/servers/${server.id}/start`)
  } catch (e) {
    const msg = e.response?.data?.detail || ''
    if (msg === 'EULA acceptance required') {
      eulaServer.value = server
      showEulaModal.value = true
    } else {
      toast({ title: 'Failed to start server', message: msg, type: 'error' })
    }
  }
  await fetchServers()
}

async function acceptEula() {
  if (!eulaServer.value) return
  try {
    await axios.post(`/api/servers/${eulaServer.value.id}/accept-eula`, { accept: true })
    showEulaModal.value = false
    toast({ title: 'EULA Accepted', message: 'Starting server now...', type: 'success' })
    await startServer(eulaServer.value)
  } catch (e) {
    toast({ title: 'EULA Error', message: e.response?.data?.detail || 'Failed to accept EULA', type: 'error' })
  }
}

async function stopServer(id) {
  try {
    await axios.post(`/api/servers/${id}/stop`, {}, { timeout: 15000 })
  } catch (e) {
    console.error('Stop error:', e.response?.data?.detail || e.message)
  }
  await fetchServers()
}

async function restartServer(id) {
  try {
    await axios.post(`/api/servers/${id}/restart`)
  } catch (e) {
    toast({ title: 'Failed to restart server', message: e.response?.data?.detail || '', type: 'error' })
  }
  await fetchServers()
}

function confirmDelete(server) {
  deletingServer.value = server
  showDeleteConfirm.value = true
}

async function deleteServer() {
  if (!deletingServer.value) return
  try {
    await axios.delete(`/api/servers/${deletingServer.value.id}`)
  } catch (e) {
    toast({ title: 'Failed to delete server', message: e.response?.data?.detail || '', type: 'error' })
  }
  showDeleteConfirm.value = false
  deletingServer.value = null
  await fetchServers()
}

onMounted(() => {
  fetchServers()
  fetchVersions('paper')
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .glass,
.modal-leave-to .glass {
  transform: scale(0.95);
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
