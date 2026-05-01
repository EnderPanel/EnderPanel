<template>
  <div class="max-w-6xl mx-auto px-3 sm:px-6 py-4 sm:py-8 dqs-page-shell dqs-server-page">
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8 animate-fade-up dqs-page-header">
      <button @click="$router.push('/dashboard')" 
        class="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition group">
        <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Back
      </button>
      <div class="flex items-center gap-4">
        <div class="relative group">
          <input type="file" ref="serverAvatarInput" @change="uploadServerAvatar" accept="image/*" class="hidden" />
          <button @click="$refs.serverAvatarInput.click()" 
            class="w-12 h-12 rounded-xl overflow-hidden flex items-center justify-center hover:ring-2 hover:ring-mc-accent/50 transition-all duration-200">
            <img v-if="server?.avatar" :src="server.avatar" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-gradient-to-br from-mc-accent to-mc-purple flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"/>
              </svg>
            </div>
          </button>
          <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <svg class="w-3 h-3 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </div>
        </div>
        <div>
          <p class="dqs-overline">Server Control</p>
          <h1 class="text-2xl font-bold">{{ server?.name }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <span :class="server?.status === 'running' ? 'status-dot-running' : 'status-dot-stopped'"></span>
            <span :class="server?.status === 'running' ? 'badge-running' : 'badge-stopped'">
              {{ server?.status }}
            </span>
            <span class="text-gray-500 text-xs">{{ server?.server_type }} {{ server?.version }}</span>
          </div>
        </div>
      </div>
      <div class="dqs-header-controls">
        <button @click="startServer" :disabled="server?.status === 'running'" class="btn-success text-sm py-2 flex items-center gap-2 disabled:opacity-50">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
          </svg>
          Start
        </button>
        <button @click="stopServer" :disabled="server?.status !== 'running'" class="btn-danger text-sm py-2 flex items-center gap-2 disabled:opacity-50">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
          </svg>
          Stop
        </button>
        <button @click="restartServer" :disabled="server?.status !== 'running'"
          class="dqs-restart-btn text-sm py-2 flex items-center gap-2 disabled:opacity-50">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          Restart
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-6 overflow-x-auto pb-2 animate-slide-up dqs-tab-strip">
      <button v-for="tab in tabs" :key="tab.id" @click="switchTab(tab.id)"
        :class="activeTab === tab.id 
          ? 'bg-gradient-to-r from-mc-accent to-blue-500 text-white shadow-lg shadow-mc-accent/20' 
          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-700'"
        class="px-5 py-2.5 rounded-xl font-medium transition-all duration-200 whitespace-nowrap border border-gray-200 dark:border-transparent">
        {{ tab.name }}
      </button>
    </div>

    <div class="glass rounded-2xl p-3 sm:p-6 dqs-server-shell">
      <div class="tab-content">
      <div v-show="activeTab === 'console'">
        <div class="flex gap-2 mb-4 server-console-controls">
          <button @click="startServer" :disabled="server?.status === 'running'" 
            class="btn-success text-sm py-2 flex items-center gap-2 disabled:opacity-50">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
            </svg>
            Start
          </button>
          <button @click="stopServer" :disabled="server?.status !== 'running'" 
            class="btn-danger text-sm py-2 flex items-center gap-2 disabled:opacity-50">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
            </svg>
            Stop
          </button>
          <button @click="restartServer" :disabled="server?.status !== 'running'" 
            class="bg-gradient-to-r from-yellow-600 to-yellow-700 hover:from-yellow-500 hover:to-yellow-600 
                   text-white font-semibold px-5 py-2 rounded-xl transition-all duration-300 
                   hover:shadow-lg hover:shadow-yellow-500/25 text-sm flex items-center gap-2 disabled:opacity-50">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Restart
          </button>
        </div>
        <div ref="consoleRef" class="bg-gray-900 dark:bg-black/80 rounded-xl p-4 h-96 overflow-y-auto font-mono text-sm text-green-400 mb-4 border border-gray-200 dark:border-white/5">
          <div v-for="(line, i) in consoleLines" :key="i" class="animate-fade-in">{{ line }}</div>
        </div>
        <div class="flex gap-2">
          <input v-model="command" @keyup.enter="sendCommand" type="text" placeholder="Enter command..." :disabled="server?.status !== 'running'"
            class="flex-1 input-field font-mono" />
          <button @click="sendCommand" :disabled="server?.status !== 'running'" class="btn-primary disabled:opacity-50">Send</button>
        </div>
      </div>

      <div v-show="activeTab === 'files'">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2 text-sm">
            <button @click="navigateTo('')" class="text-mc-accent hover:underline flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              root
            </button>
            <span v-for="(part, i) in currentPath.split('/').filter(Boolean)" :key="i" class="flex items-center gap-2">
              <span class="text-gray-600">/</span>
              <button @click="navigateTo(currentPath.split('/').slice(0, i + 1).join('/'))" class="text-mc-accent hover:underline">{{ part }}</button>
            </span>
          </div>
          <button @click="navigateTo(currentPath)" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
          </button>
        </div>
        <div class="mb-4 p-4 rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <p class="text-sm font-semibold">SFTP Access</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">Direct file access for this server on its own dedicated port. Admin only.</p>
            </div>
            <span :class="sftpEnabled ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-500 dark:text-gray-400'" class="text-sm font-medium">
              {{ sftpEnabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>

          <div v-if="authStore.user?.is_admin" class="grid gap-3 md:grid-cols-[1fr_auto] items-end">
            <div class="space-y-2">
              <label class="block text-sm text-gray-600 dark:text-gray-400">SFTP Password</label>
              <input v-model="sftpPassword" type="password" placeholder="Enter SFTP password"
                class="input-field w-full" />
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Set or change the password before enabling. Leave empty to keep the existing one.
              </p>
              <div v-if="sftpEnabled" class="text-xs text-gray-500 dark:text-gray-400">
                Connect to <span class="font-semibold">panel@{{ sftpHost }}:{{ sftpPort }}</span> — mounts this server's files only.
              </div>
            </div>
            <button @click="toggleSftp" class="btn-primary w-full md:w-auto">
              {{ sftpEnabled ? 'Disable SFTP' : 'Enable SFTP' }}
            </button>
          </div>
          <div v-else class="text-xs text-gray-500 dark:text-gray-400">SFTP access is visible only to admins.</div>
        </div>
        <div class="flex gap-2 mb-4">
          <button @click="showUpload = true" class="btn-primary text-sm py-2 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            Upload
          </button>
          <button @click="createFolder" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-xl text-sm transition flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            </svg>
            New Folder
          </button>
        </div>
        <div class="space-y-1">
          <div v-for="file in files" :key="file.name"
            @click="file.is_dir ? navigateTo(currentPath ? currentPath + '/' + file.name : file.name) : editFile(currentPath ? currentPath + '/' + file.name : file.name)"
            class="flex justify-between items-center px-4 py-3 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer group transition-all duration-200">
            <div class="flex items-center gap-3">
              <div :class="file.is_dir ? 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-600 dark:text-yellow-400' : 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400'" 
                class="w-8 h-8 rounded-lg flex items-center justify-center">
                <svg v-if="file.is_dir" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
              </div>
              <span>{{ file.name }}</span>
            </div>
            <div class="flex items-center gap-4">
              <span class="text-gray-500 dark:text-gray-500 text-sm">{{ formatSize(file.size) }}</span>
              <button @click.stop="deleteFile(currentPath ? currentPath + '/' + file.name : file.name)"
                class="text-red-500 opacity-0 group-hover:opacity-100 transition text-sm flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
                Delete
              </button>
            </div>
          </div>
        </div>

      </div>

      <div v-show="activeTab === 'players'">
        <div class="flex items-center gap-2 mb-4">
          <span class="text-gray-600 dark:text-gray-400">Online:</span>
          <span class="bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full text-sm font-medium">{{ players.length }}</span>
        </div>
        <div v-if="players.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-gray-100 dark:bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
          </div>
          <p class="text-gray-500 dark:text-gray-500">No players online</p>
        </div>
        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <div v-for="player in players" :key="player" 
            class="bg-gray-100 dark:bg-white/5 rounded-xl p-4 flex items-center gap-3 hover:bg-gray-200 dark:hover:bg-white/10 transition">
            <img :src="`https://mc-heads.net/avatar/${player}/32`" class="w-8 h-8 rounded" />
            <span class="font-medium">{{ player }}</span>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'plugins'">
        <div class="mb-6">
          <div class="flex items-center gap-2 mb-4">
            <span class="text-sm bg-gray-200 dark:bg-white/10 px-3 py-1.5 rounded-lg text-gray-700 dark:text-gray-300">{{ server?.server_type }} MC {{ server?.version || '?' }}</span>
            <input v-model="pluginSearch" @keyup.enter="searchPlugins" type="text" :placeholder="'Search ' + modLabel.toLowerCase() + '...'"
              class="flex-1 input-field" />
            <button @click="searchPlugins" class="btn-primary">Search</button>
          </div>
          <div v-if="pluginSearchLoading" class="flex justify-center py-8">
            <div class="w-8 h-8 border-4 border-mc-accent/20 border-t-mc-accent rounded-full animate-spin"></div>
          </div>
          <div v-else-if="pluginResults.length > 0" class="mb-6 p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="text-sm text-gray-700 dark:text-gray-300">
              <p class="font-medium">{{ pluginResults.length }} results found.</p>
              <p class="mt-1 text-gray-500 dark:text-gray-400">Search results are shown in a modal for a cleaner plugin/mod browser and installer experience.</p>
            </div>
            <button @click="showSearchModal = true" class="btn-primary text-sm">Open Results</button>
          </div>
          <div v-else-if="pluginSearch.trim() !== ''" class="mb-6 text-sm text-gray-500 dark:text-gray-400">
            No {{ modLabel.toLowerCase() }} found for "{{ pluginSearch }}".
          </div>
        </div>

        <h3 class="font-semibold mb-3">Installed {{ modLabel }}</h3>
        
        <div class="flex items-center justify-between mb-4">
          <div class="flex gap-2">
            <button @click="checkForUpdates" :disabled="checkingUpdates || !autoUpdateEnabled"
              class="bg-mc-accent hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 disabled:opacity-50">
              <svg v-if="checkingUpdates" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              {{ checkingUpdates ? 'Checking...' : 'Check for Updates' }}
            </button>
            <button v-if="availableUpdates.length > 0" @click="updateAll"
              class="bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
              </svg>
              Update All ({{ availableUpdates.length }})
            </button>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <span class="text-sm text-gray-500 dark:text-gray-400">Auto-update check</span>
            <div class="relative">
              <input type="checkbox" v-model="autoUpdateEnabled" class="sr-only peer" @change="saveAutoUpdatePref" />
              <div class="w-10 h-5 bg-gray-300 dark:bg-gray-600 rounded-full peer peer-checked:bg-emerald-500 transition"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
            </div>
          </label>
        </div>

        <div v-if="availableUpdates.length > 0" class="mb-6">
          <h4 class="text-sm font-medium text-yellow-600 dark:text-yellow-400 mb-3 flex items-center gap-2">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            Updates Available
          </h4>
          <div class="space-y-2">
            <div v-for="update in availableUpdates" :key="update.filename"
              class="flex justify-between items-center px-4 py-3 bg-yellow-50 dark:bg-yellow-500/10 rounded-xl border border-yellow-200 dark:border-yellow-500/20">
              <div>
                <p class="font-medium">{{ update.project_title || update.filename }}</p>
                <p class="text-sm text-gray-500">
                  {{ update.current_version }} → 
                  <span class="text-emerald-600 dark:text-emerald-400">{{ update.latest_version }}</span>
                  <span :class="update.version_type === 'release' ? 'text-emerald-600 dark:text-emerald-400' : 'text-yellow-600 dark:text-yellow-400'" 
                    class="ml-2 text-xs">({{ update.version_type }})</span>
                </p>
              </div>
              <button @click="updatePlugin(update.filename)"
                class="bg-emerald-500 hover:bg-emerald-400 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition">
                Update
              </button>
            </div>
          </div>
        </div>

        <div v-if="installedPlugins.length === 0" class="text-center py-8">
          <div class="w-12 h-12 bg-gray-100 dark:bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
            </svg>
          </div>
          <p class="text-gray-500 dark:text-gray-500">No {{ modLabel.toLowerCase() }} installed</p>
        </div>
        <div v-else class="space-y-2">
          <div v-for="plugin in installedPlugins" :key="plugin.name"
            class="flex justify-between items-center px-4 py-3 bg-gray-50 dark:bg-white/5 rounded-xl hover:bg-gray-100 dark:hover:bg-white/10 transition">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-emerald-100 dark:bg-emerald-500/20 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div>
                <span>{{ plugin.name }}</span>
                <span v-if="plugin.version" class="text-xs text-gray-500 dark:text-gray-400 ml-2">v{{ plugin.version }}</span>
                <span v-if="!plugin.project_id" class="text-xs text-yellow-500 dark:text-yellow-400 ml-2">(no update tracking)</span>
              </div>
            </div>
            <div class="flex gap-2">
              <button v-if="!plugin.project_id" @click="linkModrinthProjectPrompt(plugin)" 
                class="text-mc-accent hover:text-blue-400 text-sm flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                </svg>
                Link
              </button>
              <button @click="uninstallPlugin(plugin.name)" class="text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 text-sm flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
                Uninstall
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'resources'">
        <transition name="fade">
          <div v-if="server?.status === 'running'" class="mb-4 p-4 rounded-xl bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/30 text-yellow-700 dark:text-yellow-400 flex items-center gap-3">
            <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            Stop the server to change resource settings
          </div>
        </transition>
        <form @submit.prevent="saveResources" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold mb-4">Memory Allocation</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Minimum RAM (MB)</label>
                <input v-model.number="resources.ram_min" type="number" min="256" step="256" :disabled="server?.status === 'running'"
                  class="input-field disabled:opacity-50" />
              </div>
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Maximum RAM (MB)</label>
                <input v-model.number="resources.ram_max" type="number" min="256" step="256" :disabled="server?.status === 'running'"
                  class="input-field disabled:opacity-50" />
              </div>
            </div>
            <div class="mt-3 flex gap-2 flex-wrap">
              <button type="button" @click="setPreset(512, 1024)" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">512MB-1GB</button>
              <button type="button" @click="setPreset(1024, 2048)" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">1GB-2GB</button>
              <button type="button" @click="setPreset(2048, 4096)" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">2GB-4GB</button>
              <button type="button" @click="setPreset(4096, 8192)" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">4GB-8GB</button>
              <button type="button" @click="setPreset(8192, 16384)" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">8GB-16GB</button>
            </div>
          </div>
          <div>
            <h3 class="text-lg font-semibold mb-4">CPU Allocation</h3>
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">CPU Cores</label>
              <input v-model.number="resources.cpu_cores" type="number" min="1" max="16" :disabled="server?.status === 'running'"
                class="input-field disabled:opacity-50" />
            </div>
            <div class="mt-3 flex gap-2">
              <button type="button" @click="resources.cpu_cores = 1" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">1 Core</button>
              <button type="button" @click="resources.cpu_cores = 2" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">2 Cores</button>
              <button type="button" @click="resources.cpu_cores = 4" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">4 Cores</button>
              <button type="button" @click="resources.cpu_cores = 8" :disabled="server?.status === 'running'"
                class="text-xs bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">8 Cores</button>
            </div>
          </div>
          <div>
            <h3 class="text-lg font-semibold mb-4">Custom Launch Command</h3>
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Launch Command</label>
              <input v-model="resources.custom_launch_command" type="text" :disabled="server?.status === 'running'"
                placeholder="java -Xmx{ram_max}M -Xms{ram_min}M -jar {jar} nogui"
                class="input-field font-mono text-sm disabled:opacity-50" />
            </div>
            <p class="text-xs text-gray-500 mt-2">Leave empty for default. Use {jar}, {ram_min}, {ram_max} as placeholders.</p>
          </div>
          <button type="submit" :disabled="server?.status === 'running'" class="btn-primary disabled:opacity-50">
            Save Resources
          </button>
        </form>
      </div>

      <div v-show="activeTab === 'network'">
        <div class="space-y-6">
          <div class="rounded-2xl border border-emerald-200/70 dark:border-emerald-500/20 bg-gradient-to-br from-emerald-50/80 via-teal-50/60 to-white dark:from-emerald-500/10 dark:via-teal-500/5 dark:to-transparent p-6">
            <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-300 flex-shrink-0">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h8m-8 4h5m5-8H6a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2v-8a2 2 0 00-2-2h-1V7a5 5 0 00-10 0v1H6z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="text-lg font-semibold">Network Overview</h3>
                  <p class="text-sm text-emerald-900/80 dark:text-emerald-100/80 mt-1">
                    Live information for this server only, including players online and the last 3 hours of player and bandwidth history.
                  </p>
                </div>
              </div>
              <button
                @click="fetchNetworkStats"
                :disabled="networkLoading"
                class="bg-white/80 dark:bg-white/10 hover:bg-white dark:hover:bg-white/15 border border-emerald-200 dark:border-white/10 text-emerald-700 dark:text-emerald-200 px-4 py-2 rounded-xl text-sm font-medium transition disabled:opacity-50"
              >
                {{ networkLoading ? 'Refreshing...' : 'Refresh' }}
              </button>
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-5">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Players online</p>
              <p class="mt-3 text-3xl font-bold">{{ networkStats.current.players_online }}</p>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Current online player count</p>
            </div>
            <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-5">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Bandwidth total</p>
              <p class="mt-3 text-3xl font-bold">{{ formatRate(networkStats.current.bandwidth_total_bps) }}</p>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Inbound + outbound right now</p>
            </div>
            <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-5">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Inbound</p>
              <p class="mt-3 text-3xl font-bold">{{ formatRate(networkStats.current.bandwidth_rx_bps) }}</p>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Traffic received by this server</p>
            </div>
            <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-5">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Outbound</p>
              <p class="mt-3 text-3xl font-bold">{{ formatRate(networkStats.current.bandwidth_tx_bps) }}</p>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Traffic sent by this server</p>
            </div>
          </div>

          <div v-if="networkError" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
            {{ networkError }}
          </div>

          <div class="grid gap-6 xl:grid-cols-2">
            <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-6">
              <div class="flex items-center justify-between gap-4 mb-5">
                <div>
                  <h4 class="font-semibold text-lg">Players Over 3 Hours</h4>
                  <p class="text-sm text-gray-500 dark:text-gray-400">How many players were online over time.</p>
                </div>
                <span class="text-sm font-medium px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">
                  {{ networkStats.current.players_online }} online
                </span>
              </div>

              <div class="h-56 rounded-xl bg-white dark:bg-black/10 border border-gray-200 dark:border-white/10 p-3">
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" class="w-full h-full">
                  <defs>
                    <linearGradient id="playersGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="rgb(16 185 129)" stop-opacity="0.18"/>
                      <stop offset="100%" stop-color="rgb(16 185 129)" stop-opacity="0"/>
                    </linearGradient>
                  </defs>
                  <polygon
                    :points="`${playersChartPoints} 100,100 0,100`"
                    fill="url(#playersGrad)"
                  />
                  <polyline
                    :points="playersChartPoints"
                    fill="none"
                    stroke="rgb(16 185 129)"
                    stroke-width="0.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
              <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-3">
                <span>3h ago</span>
                <span>Now</span>
              </div>
            </div>

            <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-6">
              <div class="flex items-center justify-between gap-4 mb-5">
                <div>
                  <h4 class="font-semibold text-lg">Bandwidth Over 3 Hours</h4>
                  <p class="text-sm text-gray-500 dark:text-gray-400">Combined inbound and outbound traffic for this server.</p>
                </div>
                <span class="text-sm font-medium px-3 py-1 rounded-full bg-sky-100 dark:bg-sky-500/15 text-sky-700 dark:text-sky-300">
                  {{ formatRate(networkStats.current.bandwidth_total_bps) }}
                </span>
              </div>

              <div class="h-56 rounded-xl bg-white dark:bg-black/10 border border-gray-200 dark:border-white/10 p-3">
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" class="w-full h-full">
                  <defs>
                    <linearGradient id="bandwidthGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="rgb(14 165 233)" stop-opacity="0.18"/>
                      <stop offset="100%" stop-color="rgb(14 165 233)" stop-opacity="0"/>
                    </linearGradient>
                  </defs>
                  <polygon
                    :points="`${bandwidthChartPoints} 100,100 0,100`"
                    fill="url(#bandwidthGrad)"
                  />
                  <polyline
                    :points="bandwidthChartPoints"
                    fill="none"
                    stroke="rgb(14 165 233)"
                    stroke-width="0.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
              <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-3">
                <span>3h ago</span>
                <span>Now</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'playit'">
        <div class="space-y-6">
          <div class="rounded-2xl border border-blue-200/70 dark:border-blue-500/20 bg-gradient-to-br from-blue-50/80 via-sky-50/60 to-white dark:from-blue-500/10 dark:via-sky-500/5 dark:to-transparent p-6">
            <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-300 flex-shrink-0">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                </div>
                <div class="space-y-2">
                  <div class="flex flex-wrap items-center gap-2">
                    <h3 class="text-lg font-semibold">Playit Integration</h3>
                    <span class="px-2.5 py-1 rounded-full text-xs font-medium bg-white/70 dark:bg-white/10 text-blue-700 dark:text-blue-200 border border-blue-200/70 dark:border-blue-400/20">
                      Unofficial integration
                    </span>
                  </div>
                  <p class="text-sm text-blue-900/80 dark:text-blue-100/80">
                    EnderPanel is not owned by or associated with Playit beyond integrating with Playit's network.
                  </p>
                  <p class="text-sm text-blue-900/80 dark:text-blue-100/80">
                    This follows Playit's third-party rules (please dont sue us).
                  </p>
                </div>
              </div>

              <div class="grid gap-3 sm:grid-cols-3 lg:min-w-[360px]">
                <div class="rounded-xl bg-white/80 dark:bg-white/5 border border-blue-100 dark:border-white/10 px-4 py-3">
                  <p class="text-[11px] uppercase tracking-wide text-gray-500 dark:text-gray-400">Link status</p>
                  <p class="mt-1 font-semibold" :class="playitStatus.linked ? 'text-emerald-700 dark:text-emerald-300' : 'text-gray-800 dark:text-gray-100'">
                    {{ playitStatus.linked ? 'Linked' : 'Not linked' }}
                  </p>
                </div>
                <div class="rounded-xl bg-white/80 dark:bg-white/5 border border-blue-100 dark:border-white/10 px-4 py-3">
                  <p class="text-[11px] uppercase tracking-wide text-gray-500 dark:text-gray-400">Tunnel</p>
                  <p class="mt-1 font-semibold" :class="playitStatus.tunnel_created ? 'text-emerald-700 dark:text-emerald-300' : 'text-amber-700 dark:text-amber-300'">
                    {{ playitStatus.tunnel_created ? 'Created' : 'Pending' }}
                  </p>
                </div>
                <div class="rounded-xl bg-white/80 dark:bg-white/5 border border-blue-100 dark:border-white/10 px-4 py-3">
                  <p class="text-[11px] uppercase tracking-wide text-gray-500 dark:text-gray-400">Local port</p>
                  <p class="mt-1 font-semibold text-gray-900 dark:text-white font-mono">
                    {{ playitStatus.recommended_local_port }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div class="space-y-6">
              <div class="bg-gray-50 dark:bg-white/5 rounded-2xl border border-gray-200 dark:border-white/10 p-6">
                <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h4 class="font-semibold text-lg">Connect Playit</h4>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      Open your Playit agents page, grab the one-time setup code, then use the Connect modal so EnderPanel can handle the rest.
                    </p>
                  </div>
                  <div class="flex flex-col sm:flex-row gap-2">
                    <button @click="openPlayitConnectModal" :disabled="playitBusy"
                      class="btn-success text-sm text-center disabled:opacity-50">
                      {{ playitStatus.linked ? 'Reconnect' : 'Connect' }}
                    </button>
                  </div>
                </div>

                <div class="grid gap-4 mt-5 lg:grid-cols-[0.9fr_1.1fr]">
                  <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-black/10 p-4">
                    <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Quick steps</p>
                    <div class="mt-3 space-y-3 text-sm">
                      <div class="flex gap-3">
                        <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300 flex items-center justify-center text-xs font-semibold flex-shrink-0">1</span>
                        <p>Click <span class="font-medium">Connect</span> then click <span class="font-medium">Open Setup Page</span>.</p>
                      </div>
                      <div class="flex gap-3">
                        <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300 flex items-center justify-center text-xs font-semibold flex-shrink-0">2</span>
                        <p>On the Playit website select <span class="font-medium">Other</span>, copy the code and paste it into the box.</p>
                      </div>
                      <div class="flex gap-3">
                        <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300 flex items-center justify-center text-xs font-semibold flex-shrink-0">✓</span>
                        <p>You're done! Your server gets a free public address to share with friends. :)</p>
                      </div>
                    </div>
                  </div>

                  <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-black/10 p-4 space-y-4">
                    <div v-if="playitStatus.connection_error" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
                      Can't connect to EnderPanel Playit server.
                      <div class="mt-2 text-xs opacity-80">The hosted EnderPanel Playit service could not be reached.</div>
                    </div>

                    <div v-if="!playitStatus.connection_error && !playitStatus.partner_configured" class="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
                      The external Playit service is not configured yet. Set <code>PLAYIT_PARTNER_API_KEY</code> and <code>PLAYIT_VARIANT_ID</code> on your standalone Playit service, not in the EnderPanel backend.
                    </div>

                    <a
                      :href="playitStatus.dashboard_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="flex items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold px-5 py-4 text-base shadow-lg shadow-sky-500/20 transition-all duration-200"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                      </svg>
                      Open Playit Agents
                    </a>

                    <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>Uses EnderPanel hosted Playit integration</span>
                      <span class="font-mono text-[11px] text-gray-400 dark:text-gray-500">UI build {{ playitUiBuild }}</span>
                    </div>
                  </div>
                </div>

                <div v-if="playitStatus.linked" class="mt-5 rounded-xl border border-emerald-200 dark:border-emerald-500/20 bg-emerald-50 dark:bg-emerald-500/10 p-4">
                  <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 flex-1">
                      <div>
                        <p class="text-[11px] uppercase tracking-wide text-emerald-700/70 dark:text-emerald-300/70">Agent</p>
                        <p class="font-mono text-sm text-emerald-800 dark:text-emerald-200 break-all">{{ playitStatus.agent_id || 'pending' }}</p>
                      </div>
                      <div>
                        <p class="text-[11px] uppercase tracking-wide text-emerald-700/70 dark:text-emerald-300/70">Stored secret</p>
                        <p class="font-mono text-sm text-emerald-800 dark:text-emerald-200">{{ playitStatus.agent_secret_masked || 'hidden' }}</p>
                      </div>
                      <div>
                        <p class="text-[11px] uppercase tracking-wide text-emerald-700/70 dark:text-emerald-300/70">Tunnel state</p>
                        <p class="text-sm font-medium text-emerald-800 dark:text-emerald-200">
                          {{ playitStatus.tunnel_created ? 'Tunnel created' : (playitStatus.tunnel_create_detail || 'Server needs to be started to make a tunnel.') }}
                        </p>
                      </div>
                    </div>

                    <button @click="disconnectPlayit" :disabled="playitBusy"
                      class="bg-red-100 dark:bg-red-500/20 hover:bg-red-200 dark:hover:bg-red-500/30 text-red-700 dark:text-red-300 px-4 py-2 rounded-xl text-sm transition disabled:opacity-50">
                      Disconnect
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="space-y-6">
              <div class="bg-gray-50 dark:bg-white/5 rounded-2xl border border-gray-200 dark:border-white/10 p-6">
                <h4 class="font-semibold text-lg mb-4">Current Snapshot</h4>
                <div class="grid gap-3">
                  <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-black/10 px-4 py-3 flex items-center justify-between gap-3">
                    <span class="text-sm text-gray-500 dark:text-gray-400">Server status</span>
                    <span class="text-sm font-medium" :class="playitStatus.server_running ? 'text-emerald-600 dark:text-emerald-300' : 'text-gray-700 dark:text-gray-200'">
                      {{ playitStatus.server_running ? 'Running' : 'Stopped' }}
                    </span>
                  </div>
                  <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-black/10 px-4 py-3 flex items-center justify-between gap-3">
                    <span class="text-sm text-gray-500 dark:text-gray-400">Local agent</span>
                    <span class="text-sm font-medium" :class="playitStatus.agent_running ? 'text-emerald-600 dark:text-emerald-300' : 'text-gray-700 dark:text-gray-200'">
                      {{ playitStatus.agent_running ? 'Connected' : 'Not running' }}
                    </span>
                  </div>
                  <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-black/10 px-4 py-3 flex items-center justify-between gap-3">
                    <span class="text-sm text-gray-500 dark:text-gray-400">Saved tunnel ID</span>
                    <span class="text-sm font-mono text-gray-800 dark:text-gray-100 break-all text-right">
                      {{ playitStatus.saved_tunnel_id || 'None yet' }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="bg-gray-50 dark:bg-white/5 rounded-2xl border border-gray-200 dark:border-white/10 p-6">
                <h4 class="font-semibold text-lg mb-4">Public Address</h4>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  Once the tunnel is created, the public Playit hostname appears here and on the dashboard.
                </p>
                <div class="space-y-3">
                  <input v-model="playitDomainDraft" type="text" placeholder="example.playit.gg"
                    class="input-field font-mono" />
                  <button @click="savePlayitDomain" :disabled="playitBusy"
                    class="btn-primary w-full disabled:opacity-50">
                    Save Public Address
                  </button>
                </div>
                <div v-if="playitStatus.saved_domain" class="mt-4 rounded-xl border border-emerald-200 dark:border-emerald-500/20 bg-emerald-50 dark:bg-emerald-500/10 p-4">
                  <p class="text-xs uppercase tracking-wide text-emerald-700 dark:text-emerald-300 mb-1">Saved address</p>
                  <p class="font-mono text-sm break-all">{{ playitStatus.saved_domain }}</p>
                </div>
              </div>

              <div class="bg-gray-50 dark:bg-white/5 rounded-2xl border border-gray-200 dark:border-white/10 p-6">
                <h4 class="font-semibold text-lg mb-4">Rules of the Road</h4>
                <div class="space-y-3 text-sm text-gray-600 dark:text-gray-300">
                  <div class="rounded-xl bg-white dark:bg-black/10 border border-gray-200 dark:border-white/10 px-4 py-3">
                    Each EnderPanel user should link their own Playit account.
                  </div>
                  <div class="rounded-xl bg-white dark:bg-black/10 border border-gray-200 dark:border-white/10 px-4 py-3">
                    EnderPanel does not create Playit accounts for users.
                  </div>
                  <div class="rounded-xl bg-white dark:bg-black/10 border border-gray-200 dark:border-white/10 px-4 py-3">
                    The Playit website remains the place to manage premium, domains, and account settings.
                  </div>
                  <div class="rounded-xl bg-white dark:bg-black/10 border border-gray-200 dark:border-white/10 px-4 py-3">
                    If the server is stopped, the Playit sidecar stops too and restarts with the server.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'backups'">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h3 class="font-semibold">Server Backups</h3>
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="flex items-center gap-2 cursor-pointer">
                <span class="text-sm text-gray-500 dark:text-gray-400">Auto-backup</span>
                <div class="relative">
                  <input type="checkbox" v-model="autoBackupEnabled" class="sr-only peer" @change="saveAutoBackupPref" />
                  <div class="w-10 h-5 bg-gray-300 dark:bg-gray-600 rounded-full peer peer-checked:bg-emerald-500 transition"></div>
                  <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
                </div>
              </label>
              <select v-if="autoBackupEnabled" v-model="autoBackupInterval" @change="saveAutoBackupPref"
                class="bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1 text-sm focus:outline-none">
                <option value="3600000">1 hour</option>
                <option value="21600000">6 hours</option>
                <option value="43200000">12 hours</option>
                <option value="86400000">24 hours</option>
              </select>
            </div>
            <button @click="createBackup" :disabled="backupLoading" class="btn-primary text-sm py-2 flex items-center gap-2 disabled:opacity-50">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
              </svg>
              {{ backupLoading ? 'Creating...' : 'Create Backup' }}
            </button>
          </div>
        </div>
        
        <div v-if="autoBackupEnabled" class="mb-6 p-4 bg-emerald-50 dark:bg-emerald-500/10 rounded-xl border border-emerald-200 dark:border-emerald-500/20">
          <div class="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 text-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>Auto-backup every {{ formatInterval(autoBackupInterval) }}. Next backup: {{ nextBackupTime }}</span>
          </div>
        </div>

        <div v-if="backups.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-gray-100 dark:bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
            </svg>
          </div>
          <p class="text-gray-500 dark:text-gray-500">No backups yet</p>
        </div>
        <div v-else class="space-y-2">
          <div v-for="backup in backups" :key="backup.filename"
            class="flex justify-between items-center px-4 py-3 bg-gray-50 dark:bg-white/5 rounded-xl hover:bg-gray-100 dark:hover:bg-white/10 transition">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-blue-100 dark:bg-blue-500/20 rounded-xl flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                </svg>
              </div>
              <div>
                <p class="font-medium">{{ backup.filename }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-500">{{ formatSize(backup.size) }}</p>
              </div>
            </div>
            <div class="flex gap-2">
              <button @click="downloadBackup(backup.filename)" class="bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Download
              </button>
              <button @click="restoreBackup(backup.filename)" :disabled="server?.status === 'running'"
                class="bg-yellow-100 dark:bg-yellow-500/20 hover:bg-yellow-200 dark:hover:bg-yellow-500/30 text-yellow-700 dark:text-yellow-400 disabled:opacity-50 px-3 py-1.5 rounded-lg text-xs transition">Restore</button>
              <button @click="deleteBackup(backup.filename)" class="bg-red-100 dark:bg-red-500/20 hover:bg-red-200 dark:hover:bg-red-500/30 text-red-700 dark:text-red-400 px-3 py-1.5 rounded-lg text-xs transition">Delete</button>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'settings'">
        <form @submit.prevent="saveSettings" class="space-y-4">
          <div v-for="(value, key) in settings" :key="key">
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">{{ key }}</label>
            <input :value="value" @input="settings[key] = $event.target.value" type="text"
              class="input-field font-mono text-sm" />
          </div>
          <button type="submit" class="btn-primary">Save Settings</button>
        </form>
      </div>
      </div>
    </div>
  </div>

  <transition name="modal">
    <div v-if="showPlayitConnectModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="closePlayitConnectModal">
      <div class="glass rounded-2xl p-8 w-full max-w-lg scale-in dqs-modal-card">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="text-xl font-bold">Connect Playit</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Open Playit's setup page, copy the one-time code, and paste it here.
            </p>
          </div>
          <button @click="closePlayitConnectModal" :disabled="playitBusy" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition disabled:opacity-50">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <a :href="playitStatus.setup_url" target="_blank" rel="noopener noreferrer" class="btn-primary w-full text-center">
            Open Setup Page
          </a>

          <div>
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Setup code from Playit</label>
            <input
              v-model="playitSetupCode"
              type="text"
              placeholder="Paste your setup code"
              class="input-field font-mono uppercase"
              :disabled="playitBusy"
            />
          </div>

          <button
            @click="connectPlayit"
            :disabled="playitBusy || !playitSetupCode.trim()"
            class="btn-success w-full disabled:opacity-50 flex items-center justify-center gap-3"
          >
            <span
              v-if="playitBusy"
              class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"
            ></span>
            <span>{{ playitBusy ? 'Creating tunnel...' : 'Connect' }}</span>
          </button>

          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/20 px-4 py-3">
            <p class="text-sm text-gray-700 dark:text-gray-200">{{ playitConnectMessage }}</p>
          </div>

          <div v-if="playitStatus.saved_domain" class="rounded-xl border border-emerald-200 dark:border-emerald-500/20 bg-emerald-50 dark:bg-emerald-500/10 p-4">
            <p class="text-xs uppercase tracking-wide text-emerald-700 dark:text-emerald-300 mb-1">Tunnel ready</p>
            <p class="font-mono text-sm break-all">{{ playitStatus.saved_domain }}</p>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showLinkModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showLinkModal = false">
      <div class="glass rounded-2xl p-8 w-full max-w-md scale-in dqs-modal-card">
        <h2 class="text-xl font-bold mb-2">Link Modrinth Project</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Link "{{ linkingPlugin?.name }}" to a Modrinth project for update tracking.
        </p>
        <form @submit.prevent="linkModrinthProject">
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Modrinth Project ID</label>
            <input v-model="linkProjectId" type="text" placeholder="e.g., luckperms, essentialsx"
              class="input-field" />
            <p class="text-xs text-gray-500 dark:text-gray-500 mt-2">
              Find this in the Modrinth URL:<br/>
              <span class="text-mc-accent">modrinth.com/plugin/<strong>PROJECT_ID</strong></span>
            </p>
          </div>
          <div class="flex gap-3">
            <button type="button" @click="showLinkModal = false" 
              class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">
              Cancel
            </button>
            <button type="submit" :disabled="!linkProjectId.trim()"
              class="flex-1 btn-primary disabled:opacity-50">
              Link Project
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showVersionModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[1001] p-4 dqs-modal-overlay" @click.self="showVersionModal = false">
      <div class="glass rounded-2xl w-full max-w-lg flex flex-col max-h-[80vh] scale-in dqs-modal-card">
        <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-white/5">
          <div>
            <h3 class="font-semibold">{{ selectedPlugin?.title }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">Select version for MC {{ server?.version }}</p>
          </div>
          <button @click="showVersionModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="versionLoading" class="flex justify-center py-8">
            <div class="w-8 h-8 border-4 border-mc-accent/20 border-t-mc-accent rounded-full animate-spin"></div>
          </div>
          <div v-else-if="pluginVersions.length === 0" class="text-center text-gray-500 dark:text-gray-500 py-8">No compatible versions found</div>
          <div v-else class="space-y-2">
            <div v-for="v in pluginVersions" :key="v.id"
              class="flex justify-between items-center px-4 py-3 bg-gray-50 dark:bg-white/5 rounded-xl hover:bg-gray-100 dark:hover:bg-white/10 transition">
              <div>
                <p class="font-medium">{{ v.version_number }}</p>
                <div class="flex gap-2 mt-1">
                  <span :class="v.version_type === 'release' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-500/20' : v.version_type === 'beta' ? 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-500/20' : 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-500/20'"
                    class="text-xs px-2 py-0.5 rounded-full">{{ v.version_type }}</span>
                  <span class="text-xs text-gray-500 dark:text-gray-500">{{ formatDate(v.date_published) }}</span>
                </div>
              </div>
              <button @click="installSpecificVersion(v.id, v.version_number)"
                class="btn-success text-sm py-2">
                Install
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showSearchModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showSearchModal = false">
      <div class="glass rounded-2xl w-full max-w-4xl flex flex-col max-h-[80vh] scale-in dqs-modal-card">
        <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-white/5">
          <div>
            <h3 class="font-semibold">{{ modLabel }} Search Results</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">Browse and install from the results without leaving the page.</p>
          </div>
          <button @click="showSearchModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-if="pluginResults.length === 0" class="text-center text-gray-500 dark:text-gray-500 py-12">
            No results found.
          </div>
          <div v-else class="space-y-3">
            <div v-for="plugin in pluginResults" :key="plugin.project_id"
              class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 hover:bg-gray-100 dark:hover:bg-white/10 transition">
              <div class="flex justify-between items-start gap-4">
                <div class="flex gap-3 flex-1 min-w-0">
                  <img v-if="plugin.icon_url" :src="plugin.icon_url" class="w-12 h-12 rounded-xl flex-shrink-0" />
                  <div v-else class="w-12 h-12 rounded-xl bg-gradient-to-br from-mc-accent to-mc-purple flex items-center justify-center text-xl flex-shrink-0">&#x26cf;</div>
                  <div class="min-w-0">
                    <p class="font-medium truncate">{{ plugin.title }}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{{ plugin.description }}</p>
                    <div class="flex flex-wrap gap-3 mt-2 text-xs text-gray-500 dark:text-gray-500">
                      <span class="flex items-center gap-1">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        {{ formatNumber(plugin.downloads) }}
                      </span>
                      <span>{{ plugin.author }}</span>
                    </div>
                  </div>
                </div>
                <button @click="showVersions(plugin)" class="btn-success text-sm py-2 flex-shrink-0">Install</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>


  <!-- File editor modal — teleported to body to escape stacking contexts -->
  <Teleport to="body">
    <transition name="modal">
      <div v-if="showEditor" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 dqs-modal-overlay" @click.self="showEditor = false">
        <div class="glass rounded-2xl w-full max-w-4xl flex flex-col max-h-[80vh] scale-in dqs-modal-card">
          <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-white/5">
            <h3 class="font-semibold">{{ editingFile }}</h3>
            <button @click="showEditor = false" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <textarea v-model="fileContent" class="flex-1 bg-gray-50 dark:bg-black/50 p-4 font-mono text-sm text-gray-900 dark:text-white resize-none focus:outline-none min-h-[300px]"></textarea>
          <div class="p-4 border-t border-gray-200 dark:border-white/5 flex justify-end gap-2">
            <button @click="showEditor = false" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-4 py-2 rounded-xl transition">Cancel</button>
            <button @click="saveFile" class="btn-primary">Save</button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>

  <!-- File upload modal — teleported to body to escape stacking contexts -->
  <Teleport to="body">
    <transition name="modal">
      <div v-if="showUpload" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 dqs-modal-overlay" @click.self="showUpload = false">
        <div class="glass rounded-2xl p-5 sm:p-8 w-full max-w-md scale-in dqs-modal-card">
          <h3 class="text-xl font-bold mb-4">Upload</h3>
          <div class="flex gap-2 mb-4">
            <button @click="uploadMode = 'file'" :class="uploadMode === 'file' ? 'bg-mc-accent text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400'"
              class="flex-1 py-2.5 rounded-xl transition">File</button>
            <button @click="uploadMode = 'folder'" :class="uploadMode === 'folder' ? 'bg-mc-accent text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400'"
              class="flex-1 py-2.5 rounded-xl transition">Folder</button>
          </div>
          <input v-if="uploadMode === 'file'" type="file" @change="handleFileUpload" class="mb-4" />
          <input v-if="uploadMode === 'folder'" type="file" webkitdirectory @change="handleFolderUpload" class="mb-4" />
          <p v-if="uploadMode === 'folder' && uploadFiles.length > 0" class="text-sm text-gray-500 dark:text-gray-400 mb-4">{{ uploadFiles.length }} files selected</p>
          <div class="flex gap-2">
            <button @click="showUpload = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
            <button @click="uploadFile" class="flex-1 btn-primary">Upload</button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>

  <transition name="modal">
    <div v-if="showEulaModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showEulaModal = false">
      <div class="glass rounded-2xl w-full max-w-2xl p-6 scale-in dqs-modal-card">
        <div class="flex justify-between items-start gap-4 mb-4">
          <div>
            <h3 class="text-2xl font-bold">Minecraft EULA</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">This server requires acceptance of the Minecraft End User License Agreement before the first start.</p>
          </div>
          <button @click="showEulaModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="space-y-4 mb-6 text-sm text-gray-600 dark:text-gray-300">
          <p>To start this server, you must accept the Minecraft EULA. Your acceptance will create the required <code class="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">eula.txt</code> file with <code class="font-mono">eula=true</code>.</p>
          <p>Read the Mojang EULA here: <a href="https://account.mojang.com/documents/minecraft_eula" target="_blank" class="text-mc-accent hover:underline">https://account.mojang.com/documents/minecraft_eula</a></p>
        </div>
        <div class="flex flex-col sm:flex-row gap-3 justify-end">
          <button @click="showEulaModal = false" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 px-5 py-3 rounded-xl transition">Cancel</button>
          <button @click="acceptEula" class="btn-success px-5 py-3">Accept and Start</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, inject, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const route = useRoute()
const authStore = useAuthStore()
const serverId = route.params.id
const toast = inject('toast', (opts) => alert(opts.title + (opts.message ? ': ' + opts.message : '')))
const confirmFn = inject('confirm', (opts) => Promise.resolve(confirm(opts.title + '\n' + opts.message)))
const server = ref(null)
const serverAvatarInput = ref(null)
const activeTab = ref('console')
const consoleLines = ref([])
const command = ref('')
const consoleRef = ref(null)
const files = ref([])
const currentPath = ref('')
const showEditor = ref(false)
const showUpload = ref(false)
const showEulaModal = ref(false)
const showSearchModal = ref(false)
const uploadMode = ref('file')
const editingFile = ref('')
const fileContent = ref('')
const sftpEnabled = ref(false)
const sftpStatus = ref('stopped')
const sftpPassword = ref('')
const sftpHost = window.location.hostname || 'localhost'
const sftpPort = ref(2223)
const uploadFileRef = ref(null)
const uploadFiles = ref([])
const players = ref([])
const pluginSearch = ref('')
const pluginSearchLoading = ref(false)
const pluginResults = ref([])
const installedPlugins = ref([])
const availableUpdates = ref([])
const checkingUpdates = ref(false)
const autoUpdateEnabled = ref(localStorage.getItem('mcpanel_auto_update') !== 'false')
const showVersionModal = ref(false)
const showLinkModal = ref(false)
const linkingPlugin = ref(null)
const linkProjectId = ref('')
const selectedPlugin = ref(null)
const pluginVersions = ref([])
const versionLoading = ref(false)
const settings = ref({})
const resources = reactive({ ram_min: 512, ram_max: 1024, cpu_cores: 1, custom_launch_command: '' })
const backups = ref([])
const backupLoading = ref(false)
const autoBackupEnabled = ref(localStorage.getItem(`autoBackup_${serverId}`) === 'true')
const autoBackupInterval = ref(localStorage.getItem(`autoBackupInterval_${serverId}`) || '21600000')
const autoBackupTimer = ref(null)
const nextBackupTime = ref('')
const playitApiBase = import.meta.env.VITE_PLAYIT_PROXY_URL || 'https://vercel-playit-api.vercel.app/api/playit'
const playitUiBuild = '2026-04-16-playit-3'
const playitBusy = ref(false)
const showPlayitConnectModal = ref(false)
const playitConnectMessage = ref('Paste your one-time Playit setup code to connect this server.')
const playitSetupCode = ref('')
const playitDomainDraft = ref('')
const playitStatus = ref({
  partner_configured: false,
  setup_url: 'https://playit.gg/l/setup-third-party',
  dashboard_url: 'https://playit.gg/account/agents',
  linked: false,
  enabled: false,
  server_running: false,
  agent_running: false,
  agent_id: null,
  agent_secret_masked: null,
  recommended_local_port: 25565,
  saved_domain: '',
  saved_tunnel_id: null,
  tunnel_created: false,
  tunnel_create_detail: null,
  connection_error: false,
})
const networkLoading = ref(false)
const networkError = ref('')
const networkStats = ref({
  current: {
    players_online: 0,
    bandwidth_rx_bps: 0,
    bandwidth_tx_bps: 0,
    bandwidth_total_bps: 0,
  },
  history: {
    timestamps: [],
    players: [],
    bandwidth_total_bps: [],
  },
})

function buildChartPoints(values) {
  const series = Array.isArray(values) ? values : []
  if (!series.length) return '0,100 100,100'
  if (series.length === 1) {
    const y = 100 - Math.min(100, Math.max(0, Number(series[0]) || 0))
    return `0,${y} 100,${y}`
  }
  const numeric = series.map((value) => Number(value) || 0)
  const maxValue = Math.max(...numeric, 1)
  return numeric
    .map((value, index) => {
      const x = (index / (numeric.length - 1)) * 100
      const y = 100 - ((value / maxValue) * 100)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

const playersChartPoints = computed(() => buildChartPoints(networkStats.value.history.players))
const bandwidthChartPoints = computed(() => buildChartPoints(networkStats.value.history.bandwidth_total_bps))

function getPlayitLinkStorageKey() {
  const username = authStore.user?.username || 'guest'
  const createdAt = server.value?.created_at || 'unknown'
  return `enderpanel_playit_link_${playitApiBase}_${username}_${serverId}_${createdAt}`
}

function buildStoredPlayitLink(data) {
  return {
    linked: true,
    agent_id: data.agent_id || null,
    agent_secret_masked: data.agent_secret_masked || null,
    account_id: data.account_id || null,
    saved_domain: data.saved_domain || '',
    setup_url: data.setup_url || playitStatus.value.setup_url,
    dashboard_url: data.dashboard_url || playitStatus.value.dashboard_url,
    recommended_local_port: data.recommended_local_port || playitStatus.value.recommended_local_port,
    saved_tunnel_id: data.saved_tunnel_id || null,
    tunnel_created: Boolean(data.tunnel_created),
    tunnel_create_detail: data.tunnel_create_detail || null,
    partner_configured: data.partner_configured !== false,
  }
}

function saveStoredPlayitLink(data) {
  localStorage.setItem(getPlayitLinkStorageKey(), JSON.stringify(buildStoredPlayitLink(data)))
}

function loadStoredPlayitLink() {
  try {
    const raw = localStorage.getItem(getPlayitLinkStorageKey())
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function clearStoredPlayitLink() {
  localStorage.removeItem(getPlayitLinkStorageKey())
}

function getConsoleHistoryStorageKey() {
  const username = authStore.user?.username || 'guest'
  const createdAt = server.value?.created_at || 'unknown'
  return `enderpanel_console_history_${username}_${serverId}_${createdAt}`
}

function saveConsoleHistory() {
  try {
    const payload = {
      lines: consoleLines.value.slice(-400),
      lastLine: lastConsoleLine,
      updatedAt: Date.now(),
    }
    localStorage.setItem(getConsoleHistoryStorageKey(), JSON.stringify(payload))
  } catch {}
}

function loadConsoleHistory() {
  try {
    const raw = localStorage.getItem(getConsoleHistoryStorageKey())
    if (!raw) return false
    const parsed = JSON.parse(raw)
    const lines = Array.isArray(parsed?.lines) ? parsed.lines.filter((line) => typeof line === 'string' && line.trim() !== '') : []
    if (!lines.length) return false
    consoleLines.value = lines.slice(-400)
    lastConsoleLine = typeof parsed?.lastLine === 'string' ? parsed.lastLine : (consoleLines.value[consoleLines.value.length - 1] || '')
    return true
  } catch {
    return false
  }
}

function clearConsoleHistory() {
  consoleLines.value = []
  consoleLineBuffer = ''
  hasLoadedConsoleHistory = false
  lastConsoleLine = ''
  try {
    localStorage.removeItem(getConsoleHistoryStorageKey())
  } catch {}
}

let ws = null
let reconnectTimeout = null
let shouldKeepConsoleConnected = false
let reconnectAttempts = 0
let consoleLineBuffer = ''
let hasLoadedConsoleHistory = false
let lastConsoleLine = ''

watch(activeTab, (newTab) => {
  if (newTab === 'files') {
    navigateTo(currentPath.value)
  }
  if (newTab === 'console') {
    shouldKeepConsoleConnected = true
    if (server.value?.status === 'running' && (!ws || ws.readyState === WebSocket.CLOSED)) {
      connectWebSocket({ replay: !hasLoadedConsoleHistory || consoleLines.value.length === 0 })
    }
  } else {
    shouldKeepConsoleConnected = false
    disconnectWebSocket()
  }
})

const modLabel = computed(() => {
  const type = server.value?.server_type?.toLowerCase()
  if (type === 'paper' || type === 'spigot' || type === 'bukkit') return 'Plugins'
  return 'Mods'
})

const tabs = computed(() => {
  const type = server.value?.server_type?.toLowerCase()
  const list = [
    { id: 'console', name: 'Console' },
    { id: 'files', name: 'Files' },
    { id: 'players', name: 'Players' },
  ]
  if (type !== 'vanilla') {
    list.push({ id: 'plugins', name: modLabel.value })
  }
  list.push(
    { id: 'resources', name: 'Resources' },
    { id: 'network', name: 'Network' },
    { id: 'playit', name: 'Playit' },
    { id: 'backups', name: 'Backups' },
    { id: 'settings', name: 'Settings' },
  )
  return list
})

function switchTab(tabId) {
  activeTab.value = tabId
  if (tabId === 'files') {
    nextTick(() => navigateTo(currentPath.value))
  } else if (tabId === 'backups') {
    nextTick(() => fetchBackups())
  } else if (tabId === 'players') {
    nextTick(() => fetchPlayers())
  } else if (tabId === 'network') {
    nextTick(() => fetchNetworkStats())
  }
}

function appendConsoleChunk(chunk) {
  const normalized = String(chunk || '').replace(/\r/g, '')
  if (!normalized) return

  consoleLineBuffer += normalized
  const parts = consoleLineBuffer.split('\n')
  consoleLineBuffer = parts.pop() || ''

  for (const part of parts) {
    const line = part.trimEnd()
    if (!line) continue
    if (line === lastConsoleLine) continue
    lastConsoleLine = line
    consoleLines.value.push(line)
  }

  if (consoleLines.value.length > 400) {
    consoleLines.value = consoleLines.value.slice(-400)
  }

  saveConsoleHistory()

  nextTick(() => {
    if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
  })
}

function setPreset(min, max) {
  resources.ram_min = min
  resources.ram_max = max
}

async function fetchServer() {
  try {
    const res = await axios.get(`/api/servers/${serverId}`)
    server.value = res.data
    resources.ram_min = res.data.ram_min
    resources.ram_max = res.data.ram_max
    resources.cpu_cores = res.data.cpu_cores
    resources.custom_launch_command = res.data.custom_launch_command || ''
    playitStatus.value.server_running = res.data.status === 'running'
    playitStatus.value.enabled = !!res.data.playit_enabled
    playitStatus.value.recommended_local_port = res.data.port || playitStatus.value.recommended_local_port
  } catch (e) {
    console.error('Failed to fetch server:', e)
  }
}

function formatRate(bytesPerSecond) {
  const value = Number(bytesPerSecond) || 0
  if (value < 1024) return `${value.toFixed(0)} B/s`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB/s`
  if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB/s`
  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB/s`
}

async function fetchNetworkStats() {
  networkLoading.value = true
  networkError.value = ''
  try {
    const res = await axios.get(`/api/servers/${serverId}/network`)
    networkStats.value = {
      current: {
        players_online: res.data.current?.players_online || 0,
        bandwidth_rx_bps: res.data.current?.bandwidth_rx_bps || 0,
        bandwidth_tx_bps: res.data.current?.bandwidth_tx_bps || 0,
        bandwidth_total_bps: res.data.current?.bandwidth_total_bps || 0,
      },
      history: {
        timestamps: res.data.history?.timestamps || [],
        players: res.data.history?.players || [],
        bandwidth_total_bps: res.data.history?.bandwidth_total_bps || [],
      },
    }
  } catch (e) {
    console.error('Failed to fetch network stats:', e)
    networkError.value = e.response?.data?.detail || 'Failed to load server network data.'
  } finally {
    networkLoading.value = false
  }
}

function applyPlayitStatus(data) {
  playitStatus.value = {
    ...playitStatus.value,
    ...data,
  }
  playitDomainDraft.value = data.saved_domain || ''
}

function openPlayitConnectModal() {
  playitConnectMessage.value = playitStatus.value.linked
    ? 'Replace the current Playit link for this server.'
    : 'Paste your one-time Playit setup code to connect this server.'
  showPlayitConnectModal.value = true
}

function closePlayitConnectModal() {
  if (playitBusy.value) return
  showPlayitConnectModal.value = false
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function waitForPlayitTunnel(serverWasRunning) {
  let latest = null
  const attempts = serverWasRunning ? 15 : 20

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    playitConnectMessage.value = attempt === 0
      ? 'Waiting for Playit to finish creating the tunnel...'
      : `Still waiting for the tunnel... (${attempt + 1}/${attempts})`

    await delay(2000)

    try {
      const runtimeStatus = await axios.post(`/api/servers/${serverId}/playit/runtime/sync`)
      latest = runtimeStatus.data
      if (latest?.tunnel_created) {
        return latest
      }
    } catch (error) {
      return {
        ...latest,
        tunnel_create_detail: error.response?.data?.detail || error.message || 'Failed while waiting for tunnel creation.',
      }
    }
  }

  return latest
}

function detectPlayitPlatform() {
  const platform = String(navigator.userAgentData?.platform || navigator.platform || '').toLowerCase()
  if (platform.includes('win')) return 'windows'
  if (platform.includes('mac')) return 'macos'
  return 'linux'
}

function buildPlayitUrl(path) {
  return new URL(`${playitApiBase}${path}`, window.location.origin)
}

async function playitRequest(method, path, body = null) {
  const url = buildPlayitUrl(path)
  const headers = {
    'X-EnderPanel-Username': authStore.user?.username || '',
    'X-EnderPanel-Platform': detectPlayitPlatform(),
  }

  if (body) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  const raw = await res.text()
  let data = null

  try {
    data = raw ? JSON.parse(raw) : null
  } catch {
    data = null
  }

  if (!res.ok) {
    const error = new Error(data?.detail || raw || `Playit request failed with status ${res.status}`)
    error.response = { status: res.status, data: data || { detail: raw || `Playit request failed with status ${res.status}` } }
    throw error
  }

  return data
}

async function fetchPlayitStatus() {
  let hostedData = null
  let runtimeData = null
  let healthData = null
  try {
    hostedData = await playitRequest('GET', `/status?serverId=${encodeURIComponent(serverId)}`)
  } catch (e) {
    console.error('Failed to fetch hosted Playit status:', e)
  }

  if (!hostedData) {
    try {
      healthData = await playitRequest('GET', '/health')
    } catch (e) {
      console.error('Failed to fetch Playit health:', e)
    }
  }

  try {
    const runtimeRes = await axios.get(`/api/servers/${serverId}/playit/runtime`)
    runtimeData = runtimeRes.data
  } catch (e) {
    console.error('Failed to fetch local Playit runtime status:', e)
  }

  if (!hostedData && !healthData && !runtimeData) {
    playitStatus.value.connection_error = true
    return
  }

  const mergedData = {
    ...(hostedData || {}),
    ...(runtimeData || {}),
    connection_error: false,
  }

  if (!hostedData && healthData) {
    mergedData.partner_configured = healthData.partner_configured !== false
  } else if (!hostedData && !healthData) {
    mergedData.partner_configured = true
  }

  mergedData.server_running = playitStatus.value.server_running
  mergedData.enabled = runtimeData?.enabled ?? playitStatus.value.enabled
  mergedData.recommended_local_port = server.value?.port || hostedData?.recommended_local_port || playitStatus.value.recommended_local_port

  if (!runtimeData?.linked) {
    clearStoredPlayitLink()
  }

  applyPlayitStatus(mergedData)
}

async function syncPlayitStatus() {
  await fetchPlayitStatus()
}

async function connectPlayit() {
  playitBusy.value = true
  try {
    playitConnectMessage.value = 'Contacting Playit and claiming your agent...'
    const data = await playitRequest('POST', `/connect?serverId=${encodeURIComponent(serverId)}`, {
      setup_code: playitSetupCode.value.trim(),
      server_port: server.value?.port || playitStatus.value.recommended_local_port,
      server_name: server.value?.name || 'Minecraft Server',
    })
    if (!data.agent_secret_key) {
      throw new Error('Playit did not return an agent secret key.')
    }

    const runtimeRes = await axios.post(`/api/servers/${serverId}/playit/runtime/link`, {
      agent_id: data.agent_id || null,
      agent_secret_key: data.agent_secret_key,
      saved_tunnel_id: data.saved_tunnel_id || null,
      saved_domain: data.saved_domain || '',
    })
    let finalData = {
      ...data,
      ...runtimeRes.data,
    }

    if (!finalData.tunnel_created && finalData.tunnel_create_detail && !playitStatus.value.server_running) {
      try {
        playitConnectMessage.value = 'Starting the server so Playit can attach and create the tunnel...'
        await axios.post(`/api/servers/${serverId}/start`, {})
        await fetchServer()
        const runtimeStatus = await axios.post(`/api/servers/${serverId}/playit/runtime/sync`)
        finalData = {
          ...finalData,
          ...runtimeStatus.data,
        }
      } catch (startError) {
        const startDetail = startError.response?.data?.detail || startError.message || 'Failed to auto-start the server.'
        finalData = {
          ...finalData,
          tunnel_create_detail: startDetail,
        }
      }
    }

    if (!finalData.tunnel_created && finalData.linked) {
      const waited = await waitForPlayitTunnel(Boolean(finalData.server_running || playitStatus.value.server_running || server.value?.status === 'running'))
      if (waited) {
        finalData = {
          ...finalData,
          ...waited,
        }
      }
    }

    if (!finalData.linked) {
      throw new Error(finalData.tunnel_create_detail || 'EnderPanel could not finish linking Playit locally.')
    }

    saveStoredPlayitLink(finalData)
    applyPlayitStatus(finalData)
    await fetchServer()
    playitSetupCode.value = ''
    if (finalData.tunnel_created) {
      playitConnectMessage.value = `Tunnel ready: ${finalData.saved_domain || 'Playit address created.'}`
      showPlayitConnectModal.value = false
    } else {
      playitConnectMessage.value = finalData.tunnel_create_detail || 'Server needs to be started to make a tunnel.'
    }
    toast({
      type: finalData.tunnel_created ? 'success' : 'warning',
      title: finalData.tunnel_created ? 'Linked and Tunnel Created' : 'Linked',
      message: finalData.tunnel_created
        ? 'Playit account linked and tunnel created successfully.'
        : (finalData.tunnel_create_detail || 'Server needs to be started to make a tunnel.'),
    })
  } catch (e) {
    console.error('Playit link failed:', {
      message: e.message,
      status: e.response?.status,
      detail: e.response?.data?.detail,
      data: e.response?.data,
    })
    toast({
      type: 'error',
      title: 'Link Failed',
      message:
        e.response?.data?.detail ||
        e.response?.data?.error ||
        e.response?.data?.message ||
        (e.response?.status === 400 ? 'Playit rejected the setup code. Try a brand-new one-time code from the Playit setup page.' : null) ||
        e.message ||
        'Failed to link Playit.',
    })
  } finally {
    if (!playitStatus.value.tunnel_created) {
      playitConnectMessage.value = playitStatus.value.linked
        ? (playitStatus.value.tunnel_create_detail || 'Server needs to be started to make a tunnel.')
        : 'Paste your one-time Playit setup code to connect this server.'
    }
    playitBusy.value = false
  }
}

async function enablePlayit() {
  playitBusy.value = true
  try {
    const res = await axios.post(`${playitApiBase}/servers/${serverId}/playit/enable`)
    applyPlayitStatus(res.data)
    await fetchServer()
    toast({ type: 'success', title: 'Playit Enabled', message: playitStatus.value.server_running ? 'The Playit agent is running for this server.' : 'Playit will start when the server starts.' })
  } catch (e) {
    toast({ type: 'error', title: 'Enable Failed', message: e.response?.data?.detail || 'Failed to enable Playit.' })
  } finally {
    playitBusy.value = false
  }
}

async function disablePlayit() {
  playitBusy.value = true
  try {
    const res = await axios.post(`${playitApiBase}/servers/${serverId}/playit/disable`)
    applyPlayitStatus(res.data)
    await fetchServer()
    toast({ type: 'success', title: 'Playit Disabled', message: 'Playit has been disabled for this server.' })
  } catch (e) {
    toast({ type: 'error', title: 'Disable Failed', message: e.response?.data?.detail || 'Failed to disable Playit.' })
  } finally {
    playitBusy.value = false
  }
}

async function disconnectPlayit() {
  const ok = await confirmFn({
    title: 'Disconnect Playit',
    message: 'Disconnect your linked Playit account and disable it on your servers?',
    type: 'danger',
    confirmText: 'Disconnect',
  })
  if (!ok) return

  playitBusy.value = true
  try {
    await axios.post(`/api/servers/${serverId}/playit/runtime/disconnect`)
    clearStoredPlayitLink()
    applyPlayitStatus({
      linked: false,
      agent_id: null,
      agent_secret_masked: null,
      saved_domain: '',
      connection_error: false,
    })
    await fetchPlayitStatus()
    toast({ type: 'success', title: 'Disconnected', message: 'Local Playit link data has been cleared from EnderPanel.' })
  } catch (e) {
    toast({ type: 'error', title: 'Disconnect Failed', message: e.response?.data?.detail || 'Failed to disconnect Playit.' })
  } finally {
    playitBusy.value = false
  }
}

async function savePlayitDomain() {
  playitBusy.value = true
  try {
    const res = await axios.post(`${playitApiBase}/servers/${serverId}/playit/metadata`, {
      domain: playitDomainDraft.value.trim(),
    })
    applyPlayitStatus(res.data)
    toast({ type: 'success', title: 'Saved', message: 'Playit public address saved.' })
  } catch (e) {
    toast({ type: 'error', title: 'Save Failed', message: e.response?.data?.detail || 'Failed to save address.' })
  } finally {
    playitBusy.value = false
  }
}

async function uploadServerAvatar(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await axios.post(`/api/servers/${serverId}/avatar`, formData)
    server.value.avatar = res.data.url
    toast({ type: 'success', title: 'Uploaded', message: 'Avatar updated' })
  } catch (e) {
    toast({ type: 'error', title: 'Upload Failed', message: e.response?.data?.detail || 'Failed to upload avatar' })
  }
  event.target.value = ''
}

function connectWebSocket(options = {}) {
  const { replay = false } = options
  shouldKeepConsoleConnected = true
  if (ws) {
    ws.close()
    ws = null
  }
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const params = new URLSearchParams()
  if (server.value?.container_started_at) {
    params.set('startedAt', server.value.container_started_at)
  }
  if (replay) {
    params.set('replay', '1')
  }
  const query = params.toString() ? `?${params.toString()}` : ''
  const wsUrl = `${protocol}//${window.location.host}/api/servers/${serverId}/ws${query}`

  try {
    const openedAt = Date.now()
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      reconnectAttempts = 0
      hasLoadedConsoleHistory = true
    }

    ws.onmessage = (event) => {
      appendConsoleChunk(event.data)
    }

    ws.onclose = () => {
      const lifetimeMs = Date.now() - openedAt
      ws = null
      if (shouldKeepConsoleConnected && activeTab.value === 'console' && server.value?.status === 'running') {
        if (lifetimeMs < 1500) {
          reconnectAttempts += 1
        } else {
          reconnectAttempts = 0
        }

        if (reconnectAttempts >= 3) {
    consoleLines.value.push('[Console connection failed repeatedly. Reload the page or restart the backend.]')
          saveConsoleHistory()
          nextTick(() => {
            if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
          })
          return
        }

        const delay = 2000 * Math.max(1, reconnectAttempts)
        reconnectTimeout = setTimeout(() => connectWebSocket({ replay: true }), delay)
      }
    }

    ws.onerror = () => {
      ws = null
    }
  } catch (e) {
    consoleLines.value.push('[Failed to connect to console]')
    saveConsoleHistory()
  }
}

function disconnectWebSocket() {
  shouldKeepConsoleConnected = false
  reconnectAttempts = 0
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
}

async function startServer() {
  try {
    if (server.value && !server.value.eula_accepted) {
      showEulaModal.value = true
      return
    }

    clearConsoleHistory()
    await axios.post(`/api/servers/${serverId}/start`)
    await fetchServer()
    await syncPlayitStatus()
    await fetchPlayitStatus()
    setTimeout(connectWebSocket, 500)
    toast({ type: 'success', title: 'Started', message: 'Server starting...' })
  } catch (e) {
    const msg = e.response?.data?.detail || 'Failed to start server'
    if (msg === 'EULA acceptance required') {
      showEulaModal.value = true
      return
    }
    toast({ type: 'error', title: 'Start Failed', message: msg })
    await fetchServer()
  }
}

async function acceptEula() {
  try {
    clearConsoleHistory()
    await axios.post(`/api/servers/${serverId}/start`, { accept_eula: true })
    await fetchServer()
    await syncPlayitStatus()
    await fetchPlayitStatus()
    showEulaModal.value = false
    setTimeout(connectWebSocket, 500)
    toast({ type: 'success', title: 'EULA Accepted', message: 'Server starting...' })
  } catch (e) {
    const msg = e.response?.data?.detail || 'Failed to accept EULA'
    toast({ type: 'error', title: 'EULA Error', message: msg })
  }
}

async function stopServer() {
  try {
    disconnectWebSocket()
    await axios.post(`/api/servers/${serverId}/stop`, {}, { timeout: 15000 })
    await new Promise(r => setTimeout(r, 500))
    await fetchServer()
    await syncPlayitStatus()
    await fetchPlayitStatus()
    consoleLines.value.push('[Server stopped]')
    saveConsoleHistory()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || 'Failed to stop server'
    console.error('Stop error:', msg)
    await fetchServer()
  }
}

async function restartServer() {
  try {
    disconnectWebSocket()
    clearConsoleHistory()
    await axios.post(`/api/servers/${serverId}/restart`)
    await new Promise(r => setTimeout(r, 200))
    await fetchServer()
    await syncPlayitStatus()
    await fetchPlayitStatus()
    setTimeout(connectWebSocket, 500)
    toast({ type: 'success', title: 'Restarted', message: 'Server restarting...' })
  } catch (e) {
    const msg = e.response?.data?.detail || 'Failed to restart server'
    toast({ type: 'error', title: 'Restart Failed', message: msg })
    await fetchServer()
  }
}

function sendCommand() {
  if (!command.value.trim()) return
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(command.value)
    command.value = ''
  } else if (server.value?.status === 'running') {
    connectWebSocket()
    setTimeout(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(command.value)
        command.value = ''
      } else {
        toast({ type: 'info', title: 'Console', message: 'Connecting to console...' })
      }
    }, 500)
  } else {
    toast({ type: 'warning', title: 'Server Offline', message: 'Server is not running' })
  }
}

async function navigateTo(path) {
  currentPath.value = path
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/`, {
      params: { path, _: Date.now() }
    })
    files.value = res.data.sort((a, b) => {
      if (a.is_dir && !b.is_dir) return -1
      if (!a.is_dir && b.is_dir) return 1
      return a.name.localeCompare(b.name)
    })
  } catch (e) {
    files.value = []
    if (path) {
      currentPath.value = ''
    }
    toast({ type: 'error', title: 'Files Error', message: e.response?.data?.detail || 'Could not load files.' })
  }
}

async function editFile(path) {
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/read`, { params: { path } })
    editingFile.value = path
    fileContent.value = res.data.content
    showEditor.value = true
  } catch (e) {
    toast({ type: 'error', title: 'Read Failed', message: 'Failed to read file' })
  }
}

async function saveFile() {
  try {
    await axios.post(`/api/servers/${serverId}/files/write`, { path: editingFile.value, content: fileContent.value })
    showEditor.value = false
    toast({ type: 'success', title: 'Saved', message: 'File saved successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Save Failed', message: 'Failed to save file' })
  }
}

async function uploadFile() {
  if (uploadMode.value === 'file' && uploadFileRef.value) {
    try {
      const formData = new FormData()
      formData.append('file', uploadFileRef.value)
      await axios.post(`/api/servers/${serverId}/files/upload`, formData, { params: { path: currentPath.value } })
      showUpload.value = false
      uploadFileRef.value = null
      await navigateTo(currentPath.value)
      toast({ type: 'success', title: 'Uploaded', message: 'File uploaded successfully' })
    } catch (e) {
      toast({ type: 'error', title: 'Upload Failed', message: 'Failed to upload file' })
    }
  } else if (uploadMode.value === 'folder' && uploadFiles.value.length > 0) {
    try {
      const formData = new FormData()
      for (const file of uploadFiles.value) {
        formData.append('files', file, file.webkitRelativePath || file.name)
      }
      await axios.post(`/api/servers/${serverId}/files/upload-folder`, formData, { params: { path: currentPath.value } })
      showUpload.value = false
      uploadFiles.value = []
      await navigateTo(currentPath.value)
      toast({ type: 'success', title: 'Uploaded', message: 'Folder uploaded successfully' })
    } catch (e) {
      toast({ type: 'error', title: 'Upload Failed', message: 'Failed to upload folder' })
    }
  }
}

async function deleteFile(path) {
  const ok = await confirmFn({ title: 'Delete', message: 'Delete this file/folder?', type: 'danger', confirmText: 'Delete' })
  if (ok) {
    try {
      await axios.delete(`/api/servers/${serverId}/files/`, { params: { path } })
      await navigateTo(currentPath.value)
      toast({ type: 'success', title: 'Deleted', message: 'File deleted' })
    } catch (e) {
      toast({ type: 'error', title: 'Delete Failed', message: 'Failed to delete file' })
    }
  }
}

async function createFolder() {
  const name = prompt('Folder name:')
  if (name) {
    const path = currentPath.value ? `${currentPath.value}/${name}` : name
    try {
      await axios.post(`/api/servers/${serverId}/files/mkdir`, { path })
      await navigateTo(currentPath.value)
      toast({ type: 'success', title: 'Created', message: `Folder "${name}" created` })
    } catch (e) {
      toast({ type: 'error', title: 'Create Failed', message: 'Failed to create folder' })
    }
  }
}

async function searchPlugins() {
  pluginSearchLoading.value = true
  try {
    const res = await axios.get(`/api/servers/${serverId}/mods/search`, { params: { query: pluginSearch.value } })
    pluginResults.value = res.data.hits || []
    showSearchModal.value = pluginResults.value.length > 0
  } catch (e) {
    console.error('Failed to search mods:', e)
  } finally {
    pluginSearchLoading.value = false
  }
}

async function showVersions(plugin) {
  selectedPlugin.value = plugin
  showSearchModal.value = false
  showVersionModal.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
  versionLoading.value = true
  pluginVersions.value = []
  try {
    const res = await axios.get(`/api/servers/${serverId}/mods/${plugin.project_id}/versions`)
    pluginVersions.value = res.data.versions || []
  } catch (e) {
    console.error('Failed to fetch versions:', e)
  } finally {
    versionLoading.value = false
  }
}

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

async function installSpecificVersion(versionId, versionNumber) {
  try {
    toast({ type: 'info', title: 'Installing...', message: `Downloading version ${versionNumber}` })
    await axios.post(`/api/servers/${serverId}/mods/install/${selectedPlugin.value.project_id}?version_id=${versionId}`)
    toast({ type: 'success', title: 'Installed', message: `Version ${versionNumber} installed` })
    showVersionModal.value = false
    await fetchInstalledPlugins()
  } catch (e) {
    toast({ type: 'error', title: 'Install Failed', message: e.response?.data?.detail || 'Failed to install mod' })
  }
}

async function uninstallPlugin(filename) {
  try {
    await axios.delete(`/api/servers/${serverId}/mods/${filename}`)
    toast({ type: 'success', title: 'Uninstalled', message: `${filename} removed` })
    await fetchInstalledPlugins()
  } catch (e) {
    toast({ type: 'error', title: 'Uninstall Failed', message: 'Failed to uninstall mod' })
  }
}

async function fetchInstalledPlugins() {
  try {
    const res = await axios.get(`/api/servers/${serverId}/mods/installed`)
    installedPlugins.value = res.data
  } catch (e) {
    console.error('Failed to fetch mods:', e)
  }
}

async function checkForUpdates() {
  checkingUpdates.value = true
  try {
    const res = await axios.get(`/api/servers/${serverId}/mods/updates/check`)
    availableUpdates.value = res.data.updates || []
  } catch (e) {
    console.error('Failed to check updates:', e)
  } finally {
    checkingUpdates.value = false
  }
}

function saveAutoUpdatePref() {
  localStorage.setItem('mcpanel_auto_update', autoUpdateEnabled.value)
  if (!autoUpdateEnabled.value) {
    availableUpdates.value = []
  }
}

async function updatePlugin(filename) {
  try {
    const res = await axios.post(`/api/servers/${serverId}/mods/update/${filename}`)
    toast({ type: 'success', title: 'Updated', message: `${res.data.project_title}: ${res.data.old_version} → ${res.data.new_version}` })
    await fetchInstalledPlugins()
    await checkForUpdates()
  } catch (e) {
    toast({ type: 'error', title: 'Update Failed', message: e.response?.data?.detail || 'Failed to update' })
  }
}

async function updateAll() {
  const ok = await confirmFn({ title: 'Update All', message: `Update ${availableUpdates.value.length} plugins?`, type: 'info', confirmText: 'Update All' })
  if (!ok) return
  try {
    const res = await axios.post(`/api/servers/${serverId}/mods/updates/update-all`)
    const results = res.data.results
    const updated = results.filter(r => r.status === 'updated').length
    toast({ type: 'success', title: 'Updated', message: `${updated} of ${res.data.total} plugins updated` })
    await fetchInstalledPlugins()
    await checkForUpdates()
  } catch (e) {
    toast({ type: 'error', title: 'Update Failed', message: e.response?.data?.detail || 'Failed to update all' })
  }
}

function linkModrinthProjectPrompt(plugin) {
  linkingPlugin.value = plugin
  linkProjectId.value = ''
  showLinkModal.value = true
}

async function fetchSettings() {
  try {
    const res = await axios.get(`/api/servers/${serverId}/settings/`)
    settings.value = res.data
  } catch (e) {
    console.error('Failed to fetch settings:', e)
  }
}

async function saveSettings() {
  try {
    await axios.post(`/api/servers/${serverId}/settings/`, { settings: settings.value })
    toast({ type: 'success', title: 'Saved', message: 'Settings saved successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Save Failed', message: 'Failed to save settings' })
  }
}

async function fetchSftpStatus() {
  try {
    const res = await axios.get(`/api/servers/${serverId}/sftp`)
    sftpEnabled.value = res.data.enabled
    sftpStatus.value = res.data.status || (res.data.enabled ? 'running' : 'stopped')
    if (res.data.port) sftpPort.value = res.data.port
  } catch (e) {
    sftpStatus.value = 'unavailable'
  }
}

async function toggleSftp() {
  try {
    if (!sftpEnabled.value && !sftpPassword.value) {
      toast({ type: 'error', title: 'Password Required', message: 'Enter a password before enabling SFTP.' })
      return
    }

    const payload = {
      enabled: !sftpEnabled.value,
      password: sftpPassword.value || undefined,
    }

    const toggleRes = await axios.post(`/api/servers/${serverId}/sftp`, payload)
    if (toggleRes.data.port) sftpPort.value = toggleRes.data.port
    if (payload.enabled) {
      toast({ type: 'success', title: 'SFTP Enabled', message: 'SFTP enabled on port ${sftpPort.value}.' })
    } else {
      toast({ type: 'success', title: 'SFTP Disabled', message: 'Panel-wide SFTP access has been disabled.' })
    }
    sftpEnabled.value = payload.enabled
    sftpPassword.value = ''
    await fetchSftpStatus()
  } catch (e) {
    toast({ type: 'error', title: 'SFTP Failed', message: e.response?.data?.detail || 'Failed to update SFTP settings' })
  }
}

async function saveResources() {
  try {
    await axios.put(`/api/servers/${serverId}/resources`, resources)
    await fetchServer()
    toast({ type: 'success', title: 'Updated', message: 'Resources updated successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Update Failed', message: e.response?.data?.detail || 'Failed to update resources' })
  }
}

async function fetchBackups() {
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/backups`)
    backups.value = res.data
  } catch (e) {
    console.error('Failed to fetch backups:', e)
  }
}

async function createBackup() {
  backupLoading.value = true
  try {
    await axios.post(`/api/servers/${serverId}/files/backup`)
    await fetchBackups()
    toast({ type: 'success', title: 'Backup Created', message: 'Backup created successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Backup Failed', message: e.response?.data?.detail || 'Failed to create backup' })
  } finally {
    backupLoading.value = false
  }
}

async function restoreBackup(filename) {
  const ok = await confirmFn({ title: 'Restore Backup', message: `Restore "${filename}"? This will replace all current files!`, type: 'danger', confirmText: 'Restore' })
  if (ok) {
    try {
      await axios.post(`/api/servers/${serverId}/files/restore/${filename}`)
      await navigateTo('')
      toast({ type: 'success', title: 'Restored', message: 'Backup restored successfully' })
    } catch (e) {
      toast({ type: 'error', title: 'Restore Failed', message: e.response?.data?.detail || 'Failed to restore backup' })
    }
  }
}

async function deleteBackup(filename) {
  const ok = await confirmFn({ title: 'Delete Backup', message: `Delete "${filename}"?`, type: 'danger', confirmText: 'Delete' })
  if (ok) {
    try {
      await axios.delete(`/api/servers/${serverId}/files/backups/${filename}`)
      toast({ type: 'success', title: 'Deleted', message: 'Backup deleted' })
      await fetchBackups()
    } catch (e) {
      toast({ type: 'error', title: 'Delete Failed', message: e.response?.data?.detail || 'Failed to delete backup' })
    }
  }
}

function downloadBackup(filename) {
  window.open(`/api/servers/${serverId}/files/backups/${filename}/download`, '_blank', 'noopener')
}

function formatInterval(ms) {
  const hours = parseInt(ms) / 3600000
  if (hours === 1) return '1 hour'
  if (hours < 24) return `${hours} hours`
  return `${hours / 24} day${hours / 24 > 1 ? 's' : ''}`
}

function updateNextBackupTime() {
  if (!autoBackupEnabled.value) {
    nextBackupTime.value = ''
    return
  }
  const interval = parseInt(autoBackupInterval.value)
  const next = new Date(Date.now() + interval)
  nextBackupTime.value = next.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function saveAutoBackupPref() {
  localStorage.setItem(`autoBackup_${serverId}`, autoBackupEnabled.value)
  localStorage.setItem(`autoBackupInterval_${serverId}`, autoBackupInterval.value)
  setupAutoBackup()
}

function setupAutoBackup() {
  if (autoBackupTimer.value) {
    clearInterval(autoBackupTimer.value)
    autoBackupTimer.value = null
  }
  
  if (autoBackupEnabled.value) {
    const interval = parseInt(autoBackupInterval.value)
    updateNextBackupTime()
    
    autoBackupTimer.value = setInterval(async () => {
      try {
        await axios.post(`/api/servers/${serverId}/files/backup`)
        await fetchBackups()
        updateNextBackupTime()
      } catch (e) {
        console.error('Auto-backup failed:', e)
      }
    }, interval)
  }
}

function handleFileUpload(event) {
  uploadFileRef.value = event.target.files[0]
}

function handleFolderUpload(event) {
  uploadFiles.value = Array.from(event.target.files)
}

function formatSize(bytes) {
  if (bytes === 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

onMounted(async () => {
  await fetchServer()
  loadConsoleHistory()
  await navigateTo('')
  await fetchInstalledPlugins()
  await fetchSettings()
  await fetchSftpStatus()
  await fetchBackups()
  await fetchPlayitStatus()
  if (activeTab.value === 'network') {
    await fetchNetworkStats()
  }
  if (activeTab.value === 'console' && server.value?.status === 'running') {
    connectWebSocket()
  }
  statusInterval = setInterval(async () => {
    await fetchServer()
    await syncPlayitStatus()
    await fetchPlayitStatus()
    if (activeTab.value === 'network') {
      await fetchNetworkStats()
    }
  }, 5000)
  
  if (autoUpdateEnabled.value) {
    checkForUpdates()
    updateCheckInterval = setInterval(() => {
      if (autoUpdateEnabled.value) {
        checkForUpdates()
      }
    }, 6 * 60 * 60 * 1000)
  }
  
  setupAutoBackup()
})

let statusInterval = null
let updateCheckInterval = null

onUnmounted(() => {
  disconnectWebSocket()
  if (statusInterval) {
    clearInterval(statusInterval)
  }
  if (updateCheckInterval) {
    clearInterval(updateCheckInterval)
  }
  if (autoBackupTimer.value) {
    clearInterval(autoBackupTimer.value)
  }
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

.tab-content {
  /* animation removed - breaks fixed modals */
}

@keyframes tabSlideIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
