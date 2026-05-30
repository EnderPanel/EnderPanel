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

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6 animate-stagger dashboard-server-grid">
      <div v-for="server in servers" :key="server.id"
        class="card-hover p-4 sm:p-6 cursor-pointer group dqs-server-card dashboard-server-card relative overflow-hidden"
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
      <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="!deleting && (showDeleteConfirm = false)">
        <div class="glass rounded-2xl p-5 sm:p-8 w-full max-w-md scale-in dqs-modal-card">
          <div class="flex items-center gap-3 mb-5">
            <div :class="deleting ? 'bg-mc-accent/10 text-mc-accent' : 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400'" class="w-12 h-12 rounded-xl flex items-center justify-center">
              <svg v-if="!deleting" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
              <svg v-else class="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div>
              <h2 :class="deleting ? 'text-mc-accent' : 'text-red-600 dark:text-red-400'" class="text-xl font-bold">
                {{ deleting ? 'Deleting Server' : 'Delete Server' }}
              </h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ deleting ? 'Please wait while Docker containers and server files are cleaned up.' : 'This action cannot be undone' }}
              </p>
            </div>
          </div>
          <p class="text-gray-600 dark:text-gray-300 mb-5">
            <template v-if="!deleting">
              Are you sure you want to delete <strong class="text-gray-900 dark:text-white">{{ deletingServer?.name }}</strong>?
            </template>
            <template v-else>
              <strong class="text-gray-900 dark:text-white">{{ deletingServer?.name }}</strong> is being deleted. This can take a little longer on Docker Desktop.
            </template>
          </p>
          <div :class="deleting ? 'bg-mc-accent/5 border-mc-accent/20' : 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20'" class="rounded-xl p-4 mb-6 border">
            <ul :class="deleting ? 'text-gray-600 dark:text-gray-300' : 'text-red-600 dark:text-red-400'" class="text-sm space-y-1">
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                {{ deleting ? 'Removing the server container and sidecars' : 'All server files will be permanently deleted' }}
              </li>
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                {{ deleting ? 'Deleting the server folder and log history' : 'World data and player progress will be lost' }}
              </li>
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                {{ deleting ? 'Refreshing the server list when cleanup finishes' : 'Plugins and configurations will be removed' }}
              </li>
            </ul>
          </div>
          <div class="flex gap-3">
            <button @click="showDeleteConfirm = false" :disabled="deleting" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition disabled:opacity-50">Cancel</button>
            <button @click="deleteServer" :disabled="deleting" class="flex-1 btn-danger disabled:opacity-50">
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showCreate" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="closeCreateModal">
        <div :class="createMode === 'pearl' ? 'max-w-4xl' : 'max-w-lg'" class="glass rounded-2xl p-4 sm:p-8 w-full max-h-[90vh] overflow-y-auto scale-in dqs-modal-card">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold">Create New Server</h2>
            <button @click="closeCreateModal" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
            <button
              type="button"
              @click="createMode = 'quick'"
              :class="createMode === 'quick'
                ? 'bg-gradient-to-r from-mc-accent to-blue-500 text-white shadow-lg shadow-mc-accent/20'
                : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white'"
              class="rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 border border-gray-200 dark:border-white/5"
            >
              Quick Create
            </button>
            <button
              v-if="pearlFeature.enabled"
              type="button"
              @click="createMode = 'pearl'"
              :class="createMode === 'pearl'
                ? 'bg-gradient-to-r from-mc-accent to-blue-500 text-white shadow-lg shadow-mc-accent/20'
                : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white'"
              class="rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 border border-gray-200 dark:border-white/5"
            >
              Pterodactyl Eggs
            </button>
          </div>

          <template v-if="createMode === 'quick'">
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
                  {{ downloadStatus === 'downloading' ? createStatusLabel() : downloadStatus === 'success' ? 'Server files downloaded!' : 'Failed to download server files' }}
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
                <button type="button" @click="closeCreateModal" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
                <button type="submit" :disabled="creating" class="flex-1 btn-primary">
                  {{ creating ? 'Creating...' : 'Create' }}
                </button>
              </div>
            </form>
          </template>

          <template v-else>
            <div class="mb-6 rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-100/70 dark:bg-white/5 p-4">
              <p class="text-sm font-medium text-gray-800 dark:text-white">Import Pterodactyl egg JSON files to build servers from them.</p>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">Upload a pearl JSON file, review the parsed startup and Docker image, then set RAM, CPU, port, and any template variables before creating the server.</p>
            </div>

            <input ref="pearlFileInput" type="file" accept=".json,application/json" class="hidden" @change="handlePearlUpload" />

            <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Egg Import</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ pearlData ? `${pearlData.name} loaded` : pearlFeature.can_upload ? 'No egg loaded yet' : 'Pick from the saved egg collection below' }}
                </p>
              </div>
              <button
                v-if="pearlFeature.can_upload"
                type="button"
                @click="openPearlPicker"
                :disabled="pearlParsing"
                class="btn-primary px-4 py-2.5 disabled:opacity-60"
              >
                {{ pearlParsing ? 'Parsing...' : pearlData ? 'Replace Egg JSON' : 'Upload Egg JSON' }}
              </button>
            </div>

            <div v-if="pearlFeature.admin_only_upload && !pearlFeature.can_upload" class="mb-5 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-300">
              Only admins can upload egg JSON files right now. You can still build servers from the saved egg collection below.
            </div>

            <div v-if="pearlError" class="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-400">
              {{ pearlError }}
            </div>

            <form @submit.prevent="createPearlServer" class="space-y-6">
              <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-100/70 dark:bg-white/5 p-4">
                <div class="flex items-center justify-between gap-3 mb-4">
                  <div>
                    <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Saved Egg Collection</h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Choose from the Pterodactyl eggs already uploaded to the panel.</p>
                  </div>
                  <span class="text-xs text-gray-500 dark:text-gray-500">{{ pearlLibrary.length }} saved</span>
                </div>

                <div v-if="pearlLibraryLoading" class="text-sm text-gray-500 dark:text-gray-400">Loading eggs...</div>
                <div v-else-if="pearlLibrary.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
                  No saved eggs yet.
                </div>
                <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  <button
                    v-for="item in pearlLibrary"
                    :key="item.id"
                    type="button"
                    @click="loadPearlFromLibrary(item.id)"
                    class="text-left rounded-xl border border-gray-200 dark:border-white/10 bg-white/80 dark:bg-black/20 px-4 py-4 hover:border-mc-accent/40 hover:bg-white dark:hover:bg-white/5 transition-all"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div>
                        <p class="font-semibold text-gray-900 dark:text-white">{{ item.name }}</p>
                        <p v-if="item.description" class="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{{ item.description }}</p>
                      </div>
                      <span class="rounded-full bg-mc-accent/10 px-2.5 py-1 text-[11px] font-medium text-mc-accent">{{ item.server_type }}</span>
                    </div>
                    <div class="mt-3 flex flex-wrap gap-2 text-[11px] text-gray-500 dark:text-gray-400">
                      <span class="rounded-full border border-gray-200 dark:border-white/10 px-2 py-1">{{ item.suggested_version || '1.21.11' }}</span>
                      <span v-if="item.docker_image" class="rounded-full border border-gray-200 dark:border-white/10 px-2 py-1 font-mono">{{ item.docker_image }}</span>
                    </div>
                  </button>
                </div>
              </div>

              <div v-if="!pearlData" class="rounded-2xl border border-dashed border-gray-300 dark:border-white/10 px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                {{ pearlFeature.can_upload ? 'Upload an egg JSON file or pick one from the saved collection to start building a server from it.' : 'Pick a saved egg from the collection above to start building a server from it.' }}
              </div>

              <template v-else>
                <div class="grid grid-cols-1 xl:grid-cols-[1.1fr,0.9fr] gap-6">
                  <div class="space-y-5">
                    <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-100/70 dark:bg-white/5 p-4">
                      <div class="flex items-start justify-between gap-4">
                        <div>
                          <p class="text-xs uppercase tracking-[0.2em] text-gray-500 dark:text-gray-500">Imported Egg</p>
                          <h3 class="mt-1 text-lg font-semibold text-gray-900 dark:text-white">{{ pearlData.name }}</h3>
                          <p v-if="pearlData.description" class="mt-2 text-sm text-gray-600 dark:text-gray-300">{{ pearlData.description }}</p>
                        </div>
                        <span class="rounded-full bg-mc-accent/10 px-3 py-1 text-xs font-medium text-mc-accent">
                          {{ pearlForm.server_type }}
                        </span>
                      </div>
                    </div>

                    <div>
                      <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Server Name</label>
                      <input v-model="pearlForm.name" type="text" required placeholder="Imported Server"
                        class="input-field" />
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Runtime Image</label>
                        <select v-if="pearlForm.docker_images.length > 0" v-model="pearlForm.runtime_image" class="input-field">
                          <option v-for="image in pearlForm.docker_images" :key="image.image" :value="image.image">
                            {{ image.label }}
                          </option>
                        </select>
                        <input v-else v-model="pearlForm.runtime_image" type="text" required placeholder="Docker image"
                          class="input-field" />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Minecraft Version</label>
                        <input v-model="pearlForm.version" type="text" required class="input-field" />
                      </div>
                    </div>

                    <div>
                      <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Startup Command</label>
                      <textarea v-model="pearlForm.startup" rows="5" class="input-field font-mono text-xs resize-y"></textarea>
                    </div>

                    <div v-if="editablePearlVariablesList().length > 0">
                      <div class="flex items-center justify-between mb-3">
                        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Template Variables</h4>
                        <span class="text-xs text-gray-500 dark:text-gray-500">{{ editablePearlVariablesList().length }} field{{ editablePearlVariablesList().length !== 1 ? 's' : '' }}</span>
                      </div>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div v-for="variable in editablePearlVariablesList()" :key="variable.key">
                          <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">{{ variable.name }}</label>
                          <input
                            v-model="pearlForm.variables[variable.key]"
                            :type="isNumericPearlVariable(variable) ? 'number' : 'text'"
                            class="input-field"
                            :placeholder="variable.default_value || variable.key"
                          />
                          <p v-if="variable.description" class="mt-1 text-xs text-gray-500 dark:text-gray-500">{{ variable.description }}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="space-y-5">
                    <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-100/70 dark:bg-white/5 p-4">
                      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">Resources</h4>
                      <div class="grid grid-cols-2 gap-4 mb-3">
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Port</label>
                          <input v-model.number="pearlForm.port" type="number" required class="input-field text-sm" />
                        </div>
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Max Players</label>
                          <input v-model.number="pearlForm.max_players" type="number" required class="input-field text-sm" />
                        </div>
                      </div>
                      <div class="grid grid-cols-2 gap-4 mb-3">
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Min RAM (MB)</label>
                          <input v-model.number="pearlForm.ram_min" type="number" min="256" step="256" required class="input-field text-sm" />
                        </div>
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Max RAM (MB)</label>
                          <input v-model.number="pearlForm.ram_max" type="number" min="256" step="256" required class="input-field text-sm" />
                        </div>
                      </div>
                      <div class="grid grid-cols-2 gap-4 mb-3">
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">CPU Cores</label>
                          <input v-model.number="pearlForm.cpu_cores" type="number" min="1" max="16" required class="input-field text-sm" />
                        </div>
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Swap (MB)</label>
                          <input v-model.number="pearlForm.swap_mb" type="number" min="0" step="256" required class="input-field text-sm" />
                        </div>
                      </div>
                      <div class="flex gap-2 flex-wrap">
                        <button type="button" @click="setPearlPreset(1024, 2048, 2)" class="text-xs bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 px-3 py-1.5 rounded-lg transition">1GB-2GB</button>
                        <button type="button" @click="setPearlPreset(2048, 4096, 4)" class="text-xs bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 px-3 py-1.5 rounded-lg transition">2GB-4GB</button>
                        <button type="button" @click="setPearlPreset(4096, 8192, 4)" class="text-xs bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 px-3 py-1.5 rounded-lg transition">4GB-8GB</button>
                      </div>
                    </div>

                    <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-100/70 dark:bg-white/5 p-4">
                      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">Template Runtime</h4>
                      <div class="space-y-4">
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">Base Server Type</label>
                          <select v-model="pearlForm.server_type" class="input-field text-sm">
                            <option v-for="type in serverTypes" :key="type.id" :value="type.id">{{ type.name }}</option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-500 mb-1">MOTD</label>
                          <input v-model="pearlForm.motd" type="text" class="input-field text-sm" />
                        </div>
                        <p class="text-xs text-gray-500 dark:text-gray-500">
                          {{ pearlForm.install_script ? 'This pearl includes an install script and will run it in a helper container when the server is created.' : 'This pearl does not include an install script, so only the startup command and runtime image will be applied.' }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="flex gap-3 pt-2">
                  <button type="button" @click="closeCreateModal" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
                  <button type="submit" :disabled="creating || pearlParsing" class="flex-1 btn-primary">
                    {{ creating ? 'Importing...' : 'Create from Egg' }}
                  </button>
                </div>
              </template>
            </form>
          </template>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showEulaModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 dqs-modal-overlay" @click.self="!acceptingEula && closeEulaModal()">
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
            <button @click="acceptEula" :disabled="acceptingEula" class="btn-success flex-1 py-3 disabled:opacity-50">
              {{ acceptingEula ? 'Starting...' : 'Accept & Start' }}
            </button>
            <button @click="closeEulaModal" :disabled="acceptingEula" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition disabled:opacity-50">Cancel</button>
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
const deleting = ref(false)
const showEulaModal = ref(false)
const eulaServer = ref(null)
const acceptingEula = ref(false)
const createMode = ref('quick')
const pearlFileInput = ref(null)
const pearlParsing = ref(false)
const pearlError = ref('')
const pearlData = ref(null)
const pearlFeature = ref({
  enabled: true,
  admin_only_upload: false,
  can_upload: true,
})
const pearlLibrary = ref([])
const pearlLibraryLoading = ref(false)
const newServer = ref({ name: '', server_type: 'paper', port: 25565, max_players: 20, version: '', ram_min: 512, ram_max: 1024, cpu_cores: 1, swap_mb: 512 })
const pearlForm = ref(createEmptyPearlForm())

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

function createEmptyQuickServer() {
  return { name: '', server_type: 'paper', port: 25565, max_players: 20, version: '', ram_min: 512, ram_max: 1024, cpu_cores: 1, swap_mb: 512 }
}

function createEmptyPearlForm() {
  return {
    name: '',
    pearl_name: '',
    library_id: null,
    description: '',
    server_type: 'paper',
    port: 25565,
    max_players: 20,
    version: '1.21.11',
    motd: 'A Minecraft Server',
    ram_min: 1024,
    ram_max: 2048,
    cpu_cores: 2,
    swap_mb: 1024,
    runtime_image: '',
    install_container: '',
    install_script: '',
    startup: '',
    variables: {},
    docker_images: [],
  }
}

function resetQuickCreateForm() {
  newServer.value = createEmptyQuickServer()
  const paperVersions = versionCache.paper || versions.value
  if (paperVersions.length > 0) {
    newServer.value.version = paperVersions[0]
  }
}

function resetPearlForm() {
  pearlParsing.value = false
  pearlError.value = ''
  pearlData.value = null
  pearlForm.value = createEmptyPearlForm()
  if (pearlFileInput.value) {
    pearlFileInput.value.value = ''
  }
}

function closeCreateModal() {
  showCreate.value = false
  creating.value = false
  downloadStatus.value = ''
  createMode.value = 'quick'
  resetQuickCreateForm()
  resetPearlForm()
  versionWarning.value = ''
}

function editablePearlVariablesList() {
  return (pearlData.value?.variables || []).filter((variable) => variable.user_editable || variable.user_viewable)
}

function isNumericPearlVariable(variable) {
  return /integer|numeric|digits|number/i.test(variable.rules || '') || /PORT|MEMORY|PLAYERS|CPU|SWAP/i.test(variable.key || '')
}

function openPearlPicker() {
  pearlFileInput.value?.click()
}

async function fetchPearlFeature() {
  try {
    const res = await axios.get('/api/servers/pearls/config')
    pearlFeature.value = res.data
    if (!res.data.enabled && createMode.value === 'pearl') {
      createMode.value = 'quick'
    }
  } catch (e) {
    pearlFeature.value = {
      enabled: false,
      admin_only_upload: false,
      can_upload: false,
    }
  }
}

async function fetchPearlLibrary() {
  if (!pearlFeature.value.enabled) {
    pearlLibrary.value = []
    return
  }
  pearlLibraryLoading.value = true
  try {
    const res = await axios.get('/api/servers/pearls/library')
    pearlLibrary.value = res.data.pearls || []
  } catch (e) {
    pearlLibrary.value = []
  } finally {
    pearlLibraryLoading.value = false
  }
}

function createStatusLabel() {
  if (newServer.value.server_type === 'forge' || newServer.value.server_type === 'neoforge') {
    return `Downloading ${newServer.value.server_type} installer...`
  }
  return `Downloading ${newServer.value.server_type} server.jar...`
}

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

function setPearlPreset(min, max, cores) {
  pearlForm.value.ram_min = min
  pearlForm.value.ram_max = max
  pearlForm.value.cpu_cores = cores
  pearlForm.value.swap_mb = Math.max(512, Math.floor(max / 2))
}

function hydratePearlForm(data) {
  const variables = {}
  for (const variable of data.variables || []) {
    variables[variable.key] = variable.default_value || ''
  }
  pearlData.value = data
  pearlForm.value = {
    name: data.name || 'Imported Server',
    pearl_name: data.name || 'Imported Egg',
    library_id: data.id || null,
    description: data.description || '',
    server_type: data.inferred_server_type || 'paper',
    port: 25565,
    max_players: 20,
    version: data.suggested_version || '1.21.11',
    motd: 'A Minecraft Server',
    ram_min: 1024,
    ram_max: 2048,
    cpu_cores: 2,
    swap_mb: 1024,
    runtime_image: data.docker_images?.[0]?.image || '',
    install_container: data.install_container || '',
    install_script: data.install_script || '',
    startup: data.startup || '',
    variables,
    docker_images: data.docker_images || [],
  }
}

async function loadPearlFromLibrary(pearlId) {
  pearlError.value = ''
  pearlParsing.value = true
  try {
    const res = await axios.get(`/api/servers/pearls/library/${pearlId}`)
    hydratePearlForm(res.data)
  } catch (e) {
    pearlError.value = e.response?.data?.detail || 'Failed to load that saved egg.'
  } finally {
    pearlParsing.value = false
  }
}

async function handlePearlUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  pearlParsing.value = true
  pearlError.value = ''
  pearlData.value = null

  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await axios.post('/api/servers/pearls/library', formData)
    hydratePearlForm(res.data)
    await fetchPearlLibrary()
    toast({ title: 'Egg Saved', message: `${res.data.name} was added to the egg collection.`, type: 'success' })
  } catch (e) {
    pearlError.value = e.response?.data?.detail || 'Failed to parse the egg JSON file.'
    resetPearlForm()
    pearlError.value = e.response?.data?.detail || 'Failed to parse the egg JSON file.'
  } finally {
    pearlParsing.value = false
  }
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
      closeCreateModal()
    }, 1500)
    await fetchServers()
  } catch (e) {
    downloadStatus.value = 'error'
    creating.value = false
    toast({
      title: 'Failed to create server',
      message: e.response?.data?.detail || e.message || 'Please try again.',
      type: 'error'
    })
  }
}

async function createPearlServer() {
  if (!pearlData.value) {
    pearlError.value = 'Upload an egg JSON file first.'
    return
  }

  creating.value = true
  pearlError.value = ''
  try {
    const payload = {
      library_id: pearlForm.value.library_id || null,
      name: pearlForm.value.name,
      pearl_name: pearlForm.value.pearl_name || pearlData.value.name,
      server_type: pearlForm.value.server_type,
      port: pearlForm.value.port,
      max_players: pearlForm.value.max_players,
      version: pearlForm.value.version,
      motd: pearlForm.value.motd,
      ram_min: pearlForm.value.ram_min,
      ram_max: pearlForm.value.ram_max,
      cpu_cores: pearlForm.value.cpu_cores,
      swap_mb: pearlForm.value.swap_mb,
      runtime_image: pearlForm.value.runtime_image,
      install_container: pearlForm.value.install_container || null,
      install_script: pearlForm.value.install_script || null,
      startup: pearlForm.value.startup,
      variables: pearlForm.value.variables,
    }
    const res = await axios.post('/api/servers/pearls', payload)
    if (res.data.port_changed) {
      toast({ title: `Port ${res.data.original_port} was in use`, message: `Server created on port ${res.data.port}.`, type: 'warning' })
    }
    if (res.data.install_error) {
      toast({ title: 'Egg Imported with Installer Warning', message: res.data.install_error, type: 'warning' })
    } else {
      toast({ title: 'Egg Imported', message: `${res.data.pearl_name || pearlForm.value.pearl_name} is ready.`, type: 'success' })
    }
    await fetchServers()
    closeCreateModal()
  } catch (e) {
    pearlError.value = e.response?.data?.detail || 'Failed to create server from egg.'
  } finally {
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

function closeEulaModal() {
  showEulaModal.value = false
  eulaServer.value = null
}

async function acceptEula() {
  if (!eulaServer.value || acceptingEula.value) return
  const targetServer = eulaServer.value
  acceptingEula.value = true
  closeEulaModal()
  toast({ title: 'EULA Accepted', message: 'Starting server now...', type: 'success' })
  try {
    await axios.post(`/api/servers/${targetServer.id}/start`, { accept_eula: true })
    await fetchServers()
  } catch (e) {
    eulaServer.value = targetServer
    showEulaModal.value = true
    toast({ title: 'EULA Error', message: e.response?.data?.detail || 'Failed to accept EULA', type: 'error' })
  } finally {
    acceptingEula.value = false
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
  if (!deletingServer.value || deleting.value) return
  deleting.value = true
  try {
    await axios.delete(`/api/servers/${deletingServer.value.id}`)
  } catch (e) {
    toast({ title: 'Failed to delete server', message: e.response?.data?.detail || '', type: 'error' })
  } finally {
    await fetchServers()
    deleting.value = false
    showDeleteConfirm.value = false
    deletingServer.value = null
  }
}

onMounted(() => {
  fetchServers()
  fetchVersions('paper')
  fetchPearlFeature().then(fetchPearlLibrary)
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
