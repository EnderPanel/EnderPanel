<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8 animate-fade-up">
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
    </div>

    <div class="flex gap-2 mb-6 overflow-x-auto pb-2 animate-slide-up">
      <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
        :class="activeTab === tab.id 
          ? 'bg-gradient-to-r from-mc-accent to-blue-500 text-white shadow-lg shadow-mc-accent/20' 
          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-700'"
        class="px-5 py-2.5 rounded-xl font-medium transition-all duration-200 whitespace-nowrap border border-gray-200 dark:border-transparent">
        {{ tab.name }}
      </button>
    </div>

    <div class="glass rounded-2xl p-6">
      <div class="tab-content">
      <div v-show="activeTab === 'console'">
        <div class="flex gap-2 mb-4">
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

        <transition name="modal">
          <div v-if="showEditor" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="showEditor = false">
            <div class="glass rounded-2xl w-full max-w-4xl flex flex-col max-h-[80vh] scale-in">
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

        <transition name="modal">
          <div v-if="showUpload" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showUpload = false">
            <div class="glass rounded-2xl p-8 w-full max-w-md scale-in">
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
          <div v-else-if="pluginResults.length > 0" class="space-y-3 mb-6">
            <div v-for="plugin in pluginResults" :key="plugin.project_id"
              class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 hover:bg-gray-100 dark:hover:bg-white/10 transition">
              <div class="flex justify-between items-start gap-4">
                <div class="flex gap-3 flex-1 min-w-0">
                  <img v-if="plugin.icon_url" :src="plugin.icon_url" class="w-12 h-12 rounded-xl flex-shrink-0" />
                  <div v-else class="w-12 h-12 rounded-xl bg-gradient-to-br from-mc-accent to-mc-purple flex items-center justify-center text-xl flex-shrink-0">&#x26cf;</div>
                  <div class="min-w-0">
                    <p class="font-medium truncate">{{ plugin.title }}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{{ plugin.description }}</p>
                    <div class="flex gap-3 mt-2">
                      <span class="text-xs text-gray-500 dark:text-gray-500 flex items-center gap-1">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        {{ formatNumber(plugin.downloads) }}
                      </span>
                      <span class="text-xs text-gray-500">{{ plugin.author }}</span>
                    </div>
                  </div>
                </div>
                <button @click="showVersions(plugin)" class="btn-success text-sm py-2 flex-shrink-0">Install</button>
              </div>
            </div>
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
    <div v-if="showLinkModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4" @click.self="showLinkModal = false">
      <div class="glass rounded-2xl p-8 w-full max-w-md scale-in">
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
    <div v-if="showVersionModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4" @click.self="showVersionModal = false">
      <div class="glass rounded-2xl w-full max-w-lg flex flex-col max-h-[80vh] scale-in">
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
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, inject, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
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
const uploadMode = ref('file')
const editingFile = ref('')
const fileContent = ref('')
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
let ws = null
let reconnectTimeout = null

watch(activeTab, (newTab) => {
  if (newTab === 'files') {
    navigateTo(currentPath.value)
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
  }
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
  } catch (e) {
    console.error('Failed to fetch server:', e)
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

function connectWebSocket() {
  if (ws) {
    ws.close()
    ws = null
  }
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/servers/${serverId}/ws`

  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      consoleLines.value.push('[Console connected]')
      nextTick(() => {
        if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
      })
    }

    ws.onmessage = (event) => {
      consoleLines.value.push(event.data)
      nextTick(() => {
        if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
      })
    }

    ws.onclose = () => {
      consoleLines.value.push('[Console disconnected]')
      nextTick(() => {
        if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
      })
      ws = null
      if (server.value?.status === 'running') {
        reconnectTimeout = setTimeout(connectWebSocket, 2000)
      }
    }

    ws.onerror = () => {
      ws = null
    }
  } catch (e) {
    consoleLines.value.push('[Failed to connect to console]')
  }
}

function disconnectWebSocket() {
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
    consoleLines.value = []
    await axios.post(`/api/servers/${serverId}/start`)
    await fetchServer()
    setTimeout(connectWebSocket, 500)
    toast({ type: 'success', title: 'Started', message: 'Server starting...' })
  } catch (e) {
    const msg = e.response?.data?.detail || 'Failed to start server'
    toast({ type: 'error', title: 'Start Failed', message: msg })
    await fetchServer()
  }
}

async function stopServer() {
  try {
    disconnectWebSocket()
    await axios.post(`/api/servers/${serverId}/stop`, {}, { timeout: 15000 })
    await new Promise(r => setTimeout(r, 500))
    await fetchServer()
    consoleLines.value.push('[Server stopped]')
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || 'Failed to stop server'
    console.error('Stop error:', msg)
    await fetchServer()
  }
}

async function restartServer() {
  try {
    disconnectWebSocket()
    consoleLines.value = []
    await axios.post(`/api/servers/${serverId}/restart`)
    await new Promise(r => setTimeout(r, 200))
    await fetchServer()
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
    console.log('Files response:', res.data)
    files.value = res.data.sort((a, b) => {
      if (a.is_dir && !b.is_dir) return 1
      if (!a.is_dir && b.is_dir) return -1
      return a.name.localeCompare(b.name)
    })
    console.log('Files updated:', files.value)
  } catch (e) {
    console.error('Failed to fetch files:', e)
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
        formData.append('files', file)
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
  } catch (e) {
    console.error('Failed to search mods:', e)
  } finally {
    pluginSearchLoading.value = false
  }
}

async function showVersions(plugin) {
  selectedPlugin.value = plugin
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
  const token = localStorage.getItem('token')
  window.open(`/api/servers/${serverId}/files/backups/${filename}/download?token=${token}`, '_blank')
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
  await navigateTo('')
  await fetchInstalledPlugins()
  await fetchSettings()
  await fetchBackups()
  if (server.value?.status === 'running') {
    connectWebSocket()
  }
  statusInterval = setInterval(fetchServer, 5000)
  
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
