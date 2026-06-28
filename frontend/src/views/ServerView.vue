<template>
  <div class="max-w-6xl mx-auto px-3 sm:px-6 py-4 sm:py-8 dqs-page-shell dqs-server-page">
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8 animate-fade-up min-w-0 dqs-page-header">
      <button @click="$router.push('/dashboard')" 
        class="flex shrink-0 items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition group">
        <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Back
      </button>
      <div class="flex min-w-0 flex-1 items-center gap-4">
        <div class="relative shrink-0 group">
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
          <div class="absolute bottom-0 right-0 w-5 h-5 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <svg class="w-3 h-3 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </div>
        </div>
        <div class="min-w-0">
          <p class="dqs-overline">Server Control</p>
          <h1 class="text-2xl font-bold break-words">{{ server?.name }}</h1>
          <div class="flex flex-wrap items-center gap-2 mt-1">
            <span :class="server?.status === 'running' ? 'status-dot-running' : 'status-dot-stopped'"></span>
            <span :class="server?.status === 'running' ? 'badge-running' : 'badge-stopped'">
              {{ server?.status }}
            </span>
            <span class="text-gray-500 text-xs break-words">{{ server?.server_type }} {{ server?.version }}</span>
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

    <div class="flex flex-wrap gap-2 mb-6 pb-2 animate-slide-up dqs-tab-strip">
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
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4 server-console-controls dqs-console-toolbar">
          <div class="flex gap-2 server-console-primary-actions">
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
          <div class="flex flex-wrap items-center gap-2 text-xs sm:text-sm dqs-console-toolbar-actions">
            <span
              class="rounded-full border px-3 py-1 font-medium dqs-console-status-pill"
              :class="consoleStatusBadgeClass"
            >
              {{ consoleStatusLabel }}
            </span>
            <button @click="toggleConsoleAutoScroll" class="dqs-console-action-btn rounded-lg border border-gray-200 px-3 py-1.5 text-gray-600 transition hover:bg-gray-100 dark:border-white/10 dark:text-gray-300 dark:hover:bg-white/5">
              {{ consoleAutoScroll ? 'Auto-scroll on' : 'Auto-scroll off' }}
            </button>
            <button @click="copyConsoleOutput" class="dqs-console-action-btn rounded-lg border border-gray-200 px-3 py-1.5 text-gray-600 transition hover:bg-gray-100 dark:border-white/10 dark:text-gray-300 dark:hover:bg-white/5">
              Copy
            </button>
            <button @click="clearConsoleHistory" class="dqs-console-action-btn rounded-lg border border-gray-200 px-3 py-1.5 text-gray-600 transition hover:bg-gray-100 dark:border-white/10 dark:text-gray-300 dark:hover:bg-white/5">
              Clear
            </button>
          </div>
        </div>
        <div ref="consoleRef" class="server-terminal dqs-console-terminal bg-gray-950 rounded-xl h-96 mb-4 border border-gray-200 dark:border-white/5 overflow-hidden"></div>
        <div class="flex gap-2">
          <input
            v-model="command"
            @keyup.enter="sendCommand"
            @keydown.up.prevent="recallPreviousCommand"
            @keydown.down.prevent="recallNextCommand"
            type="text"
            placeholder="Enter command..."
            :disabled="server?.status !== 'running'"
            class="flex-1 input-field font-mono" />
          <button @click="sendCommand" :disabled="server?.status !== 'running'" class="btn-primary disabled:opacity-50">Send</button>
        </div>
      </div>

      <div v-show="activeTab === 'files'">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-4">
          <div class="flex items-center gap-2 text-sm min-w-0 flex-wrap">
            <button @click="navigateTo('')" class="text-mc-accent hover:underline flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              root
            </button>
            <span v-for="(part, i) in currentPathParts" :key="i" class="flex items-center gap-2 min-w-0">
              <span class="text-gray-600">/</span>
              <button @click="navigateTo(currentPathParts.slice(0, i + 1).join('/'))" class="text-mc-accent hover:underline truncate max-w-[14rem]">{{ part }}</button>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <div class="relative flex-1 min-w-[220px]">
              <input
                v-model="fileSearchQuery"
                @keyup.enter="runFileSearch"
                type="text"
                placeholder="Search files and folders..."
                class="input-field pr-24"
              />
              <button @click="runFileSearch" :disabled="searchingFiles || fileSearchQuery.trim().length < 2" class="absolute right-1.5 top-1.5 px-3 py-2 rounded-lg bg-mc-accent text-white text-sm disabled:opacity-50">
                {{ searchingFiles ? '...' : 'Search' }}
              </button>
            </div>
            <button @click="navigateTo(currentPath)" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </button>
          </div>
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
        <div class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-4 mb-4 space-y-4">
          <div class="flex flex-wrap gap-2">
            <button @click="openUploadModal" class="btn-primary text-sm py-2 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
              </svg>
              Upload
            </button>
            <button @click="openCreateFolderModal" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-xl text-sm transition flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              </svg>
              New Folder
            </button>
            <button @click="openArchiveModal" :disabled="!hasSelectedFiles" class="bg-emerald-100 dark:bg-emerald-500/15 hover:bg-emerald-200 dark:hover:bg-emerald-500/25 text-emerald-700 dark:text-emerald-300 px-4 py-2 rounded-xl text-sm transition flex items-center gap-2 disabled:opacity-50">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7h16M4 12h16m-7 5h7"/>
              </svg>
              Archive Selected
            </button>
            <button v-if="hasSelectedFiles" @click="clearSelectedFiles" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-xl text-sm transition">
              Clear Selection
            </button>
          </div>
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm">
            <p class="text-gray-500 dark:text-gray-400">
              {{ hasSelectedFiles ? `${selectedFiles.length} item${selectedFiles.length === 1 ? '' : 's'} selected` : 'Select files or folders to archive them together.' }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-500">
              Upload limit: {{ formatSize(fileLimits.upload_limit_bytes) }} per file
            </p>
          </div>
        </div>
        <div class="space-y-1">
          <div v-if="files.length === 0" class="rounded-2xl border border-dashed border-gray-200 dark:border-white/10 bg-gray-50/70 dark:bg-white/5 px-5 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
            This folder is empty.
          </div>
          <div v-for="file in files" :key="file.name"
            @click="openFileEntry(file)"
            class="flex justify-between items-center gap-4 px-4 py-3 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer group transition-all duration-200 overflow-hidden">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <input
                type="checkbox"
                :checked="isFileSelected(currentPath ? currentPath + '/' + file.name : file.name)"
                @click.stop
                @change="toggleFileSelection(currentPath ? currentPath + '/' + file.name : file.name)"
                class="rounded border-gray-300 dark:border-white/10"
              />
              <div :class="file.is_dir ? 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-600 dark:text-yellow-400' : 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400'"
                class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0">
                <svg v-if="file.is_dir" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
              </div>
              <div class="min-w-0">
                <p class="truncate">{{ file.name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-500">
                  {{ file.is_dir ? 'Folder' : formatSize(file.size) }} • {{ formatTimestamp(file.modified) }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button @click.stop="openRenameModalFor(file)" class="text-gray-500 dark:text-gray-400 hover:text-mc-accent text-sm px-2 py-1 rounded-lg hover:bg-white/70 dark:hover:bg-white/10 transition">
                Rename
              </button>
              <button v-if="!file.is_dir && canExtractFile(file.name)" @click.stop="extractFile(currentPath ? currentPath + '/' + file.name : file.name)" class="text-emerald-600 dark:text-emerald-300 hover:text-emerald-500 text-sm px-2 py-1 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition">
                Extract
              </button>
              <button @click.stop="deleteFile(currentPath ? currentPath + '/' + file.name : file.name)"
                class="text-red-500 opacity-0 group-hover:opacity-100 transition text-sm flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10">
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
          
          <!-- Dynamic Header -->
          <div class="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl p-8">
            <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none"></div>
            
            <div class="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div class="flex items-center gap-4">
                <div class="relative">
                  <div class="absolute -inset-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 opacity-50 blur"></div>
                  <div class="relative w-14 h-14 rounded-2xl bg-gray-900 border border-white/20 flex items-center justify-center text-white shadow-inner">
                    <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4H8l5-8v4h4l-4 8z"/>
                    </svg>
                  </div>
                </div>
                <div>
                  <h3 class="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Playit.gg Integration</h3>
                  <p class="text-gray-400 mt-1">Expose your local server to the internet without port forwarding.</p>
                </div>
              </div>
              
              <div class="flex items-center gap-3">
                <button @click="syncPlayitStatus" :disabled="playitBusy" 
                  class="group relative inline-flex items-center justify-center gap-2 rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-white/10 hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50">
                  <svg class="w-4 h-4 transition-transform group-hover:rotate-180" :class="{'animate-spin': playitBusy}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
                <button @click="enablePlayit" :disabled="playitBusy"
                  class="relative inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all hover:-translate-y-0.5 hover:shadow-indigo-500/40 disabled:opacity-50 border border-white/10">
                  {{ playitBusy ? 'Working...' : (playitStatus.enabled ? 'Restart Agent' : 'Enable Playit') }}
                </button>
              </div>
            </div>
          </div>

          <div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            
            <!-- Left Column: Status & Steps -->
            <div class="space-y-6">
              
              <!-- Setup Progress Stepper -->
              <div class="rounded-2xl border border-white/5 bg-white/5 backdrop-blur-md p-6 shadow-xl">
                <h4 class="text-sm uppercase tracking-widest text-gray-400 font-semibold mb-6 flex items-center justify-between">
                  <span>Setup Progress</span>
                  <span class="flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-2 w-2 rounded-full opacity-75" :class="playitBusy ? 'bg-indigo-400' : (playitStatus.tunnel_created ? 'bg-emerald-400' : 'bg-yellow-400')"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2" :class="playitBusy ? 'bg-indigo-500' : (playitStatus.tunnel_created ? 'bg-emerald-500' : 'bg-yellow-500')"></span>
                  </span>
                </h4>
                
                <div class="flex flex-col md:flex-row gap-4 mt-2">
                  
                  <!-- Step 1 -->
                  <div class="flex-1 p-5 rounded-2xl border bg-white/5 backdrop-blur-sm transition-all hover:bg-white/10 text-center relative overflow-hidden"
                    :class="playitStatus.enabled ? 'border-emerald-500/30' : 'border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]'">
                    <div class="mx-auto flex items-center justify-center w-10 h-10 rounded-full border-2 mb-4 transition-colors z-10 relative"
                      :class="playitStatus.enabled ? 'border-emerald-500 bg-gray-900 shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'border-indigo-500 bg-gray-900 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.4)]'">
                      <svg v-if="playitStatus.enabled" class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                      <span v-else class="font-bold">1</span>
                    </div>
                    <h5 class="font-semibold mb-2 transition-colors relative z-10" :class="playitStatus.enabled ? 'text-emerald-400' : 'text-indigo-300'">Enable Agent</h5>
                    <p class="text-sm text-gray-400 relative z-10">Click Enable Playit to start the sidecar agent container.</p>
                  </div>
                  
                  <!-- Step 2 -->
                  <div class="flex-1 p-5 rounded-2xl border bg-white/5 backdrop-blur-sm transition-all hover:bg-white/10 text-center relative overflow-hidden"
                    :class="playitStatus.linked ? 'border-emerald-500/30' : (playitStatus.enabled ? 'border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'border-white/5 opacity-70')">
                    <div class="mx-auto flex items-center justify-center w-10 h-10 rounded-full border-2 mb-4 transition-colors z-10 relative" 
                      :class="playitStatus.linked ? 'border-emerald-500 bg-gray-900 shadow-[0_0_15px_rgba(16,185,129,0.4)]' : (playitStatus.enabled ? 'border-indigo-500 bg-gray-900 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.4)]' : 'border-white/20 bg-gray-900 text-gray-500')">
                      <svg v-if="playitStatus.linked" class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                      <span v-else class="font-bold">2</span>
                    </div>
                    <h5 class="font-semibold mb-2 transition-colors relative z-10" :class="playitStatus.linked ? 'text-emerald-400' : (playitStatus.enabled ? 'text-indigo-300' : 'text-gray-500')">Claim Agent</h5>
                    <div v-if="!playitStatus.linked && playitStatus.claim_url" class="mt-2 p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 relative z-10 mx-auto max-w-[90%]">
                      <button @click="openPlayitClaimLink" type="button" class="w-full font-mono text-xs break-all text-indigo-300 hover:text-indigo-200 transition-colors underline decoration-indigo-500/50 underline-offset-2">
                        {{ playitStatus.claim_url }}
                      </button>
                    </div>
                    <p v-else class="text-sm text-gray-400 relative z-10">Open the claim link provided after enabling.</p>
                  </div>

                  <!-- Step 3 -->
                  <div class="flex-1 p-5 rounded-2xl border bg-white/5 backdrop-blur-sm transition-all hover:bg-white/10 text-center relative overflow-hidden"
                    :class="playitStatus.tunnel_created ? 'border-emerald-500/30' : (playitStatus.linked ? 'border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'border-white/5 opacity-70')">
                    <div class="mx-auto flex items-center justify-center w-10 h-10 rounded-full border-2 mb-4 transition-colors z-10 relative"
                      :class="playitStatus.tunnel_created ? 'border-emerald-500 bg-gray-900 shadow-[0_0_15px_rgba(16,185,129,0.4)]' : (playitStatus.linked ? 'border-indigo-500 bg-gray-900 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.4)] animate-pulse' : 'border-white/20 bg-gray-900 text-gray-500')">
                      <svg v-if="playitStatus.tunnel_created" class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                      <span v-else class="font-bold">3</span>
                    </div>
                    <h5 class="font-semibold mb-2 transition-colors relative z-10" :class="playitStatus.tunnel_created ? 'text-emerald-400' : (playitStatus.linked ? 'text-indigo-300' : 'text-gray-500')">Tunnel Ready</h5>
                    <p v-if="playitStatus.tunnel_create_detail" class="text-sm text-yellow-400 relative z-10 mb-2">{{ playitStatus.tunnel_create_detail }}</p>
                    <p v-else class="text-sm text-gray-400 relative z-10">Wait for Playit to assign a public address.</p>
                  </div>

                </div>
              </div>

            </div>

            <!-- Right Column: Address & Details -->
            <div class="space-y-6">
              
              <!-- Public Address Card -->
              <div class="rounded-2xl border bg-white/5 backdrop-blur-md p-6 shadow-xl transition-all duration-500 relative overflow-hidden"
                :class="playitStatus.saved_domain ? 'border-emerald-500/30 shadow-emerald-500/10' : 'border-white/5'">
                
                <div v-if="playitStatus.saved_domain" class="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-3xl -mr-10 -mt-10 rounded-full pointer-events-none"></div>

                <div class="flex items-center justify-between mb-4">
                  <h4 class="text-sm uppercase tracking-widest text-gray-400 font-semibold">Public Address</h4>
                  <span v-if="playitStatus.saved_domain" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Online
                  </span>
                </div>
                
                <div v-if="playitStatus.saved_domain" class="group relative">
                  <div class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500/30 to-teal-500/30 rounded-xl blur opacity-30 group-hover:opacity-50 transition duration-500"></div>
                  <div class="relative flex flex-col sm:flex-row items-center justify-between gap-4 rounded-xl bg-gray-900 border border-emerald-500/30 p-4">
                    <p class="font-mono text-lg break-all text-emerald-300 font-medium">{{ playitStatus.saved_domain }}</p>
                    <button @click="copyPlayitAddress" 
                      class="flex-shrink-0 flex items-center gap-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 px-4 py-2 text-sm font-medium text-emerald-400 transition-colors border border-emerald-500/20">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                      Copy
                    </button>
                  </div>
                </div>
                <div v-else class="rounded-xl border border-white/5 bg-gray-900/50 p-6 text-center">
                  <div class="mx-auto w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-3">
                    <svg class="w-6 h-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                  </div>
                  <p class="text-sm text-gray-400">
                    {{ playitStatus.linked 
                      ? (playitStatus.tunnel_create_detail || 'Waiting for Playit to assign an address...') 
                      : 'Complete setup to get your address.' }}
                  </p>
                </div>
              </div>

              <!-- Snapshot Details -->
              <div class="rounded-2xl border border-white/5 bg-white/5 backdrop-blur-md p-6 shadow-xl">
                <h4 class="text-sm uppercase tracking-widest text-gray-400 font-semibold mb-4">Diagnostics</h4>
                
                <div class="space-y-3">
                  <div class="flex items-center justify-between p-3 rounded-xl bg-gray-900/40 border border-white/5">
                    <span class="text-sm text-gray-400">Agent Process</span>
                    <span class="text-sm font-medium px-2 py-1 rounded-md" :class="playitStatus.agent_running ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'">
                      {{ playitStatus.agent_running ? 'Running' : 'Stopped' }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between p-3 rounded-xl bg-gray-900/40 border border-white/5">
                    <span class="text-sm text-gray-400">Secret Token</span>
                    <span class="text-sm font-mono text-gray-300">
                      {{ playitStatus.linked ? (playitStatus.agent_secret_masked || '••••••••') : 'None' }}
                    </span>
                  </div>
                </div>

                <div class="mt-6 flex flex-col sm:flex-row gap-3 pt-6 border-t border-white/10">
                  <a :href="playitStatus.dashboard_url" target="_blank" rel="noopener noreferrer" 
                    class="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-white/5 hover:bg-white/10 px-4 py-2.5 text-sm font-medium text-white transition-colors border border-white/10">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                    Web Dashboard
                  </a>
                  <button v-if="playitStatus.enabled" @click="disconnectPlayit" :disabled="playitBusy"
                    class="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 px-4 py-2.5 text-sm font-medium transition-colors border border-red-500/20 disabled:opacity-50">
                    Disconnect
                  </button>
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

      <div v-show="activeTab === 'tasks'">
        <div class="space-y-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 class="font-semibold text-lg">Saved Tasks</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Start, stop, restart, back up, or send console commands on a timer.
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button @click="fetchTasks" :disabled="tasksLoading" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-4 py-2 rounded-xl text-sm transition disabled:opacity-50">
                {{ tasksLoading ? 'Refreshing...' : 'Refresh' }}
              </button>
              <button @click="openTaskModalForCreate" class="btn-primary text-sm py-2 px-4">
                New Task
              </button>
            </div>
          </div>

          <div v-if="tasks.length === 0" class="text-center py-12 rounded-2xl border border-dashed border-gray-300 dark:border-white/10">
            <div class="w-16 h-16 bg-gray-100 dark:bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10m-11 9h12a2 2 0 002-2V7a2 2 0 00-2-2H6a2 2 0 00-2 2v11a2 2 0 002 2z"/>
              </svg>
            </div>
            <p class="text-gray-500 dark:text-gray-500">No scheduled tasks yet</p>
          </div>

          <div v-else class="space-y-3">
            <div v-for="task in tasks" :key="task.id" class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.03] p-5 overflow-hidden">
              <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2 mb-2">
                    <h4 class="font-semibold break-words min-w-0">{{ task.name }}</h4>
                    <span class="text-xs px-2.5 py-1 rounded-full border" :class="taskStatusBadgeClass(task)">
                      {{ taskStatusLabel(task) }}
                    </span>
                    <span class="text-xs px-2.5 py-1 rounded-full bg-gray-200 dark:bg-white/10 text-gray-700 dark:text-gray-300">
                      {{ taskActionLabel(task.action) }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 break-words">
                    {{ formatTaskSchedule(task) }}
                    <span v-if="task.action === 'command' && task.command"> • <span class="font-mono break-all">{{ task.command }}</span></span>
                  </p>
                  <div class="mt-3 grid gap-2 sm:grid-cols-2 text-sm text-gray-600 dark:text-gray-300">
                    <div>Next run: <span class="font-medium">{{ task.next_run_at ? formatDate(task.next_run_at) : 'Disabled' }}</span></div>
                    <div>Last run: <span class="font-medium">{{ task.last_run_at ? formatDate(task.last_run_at) : 'Never' }}</span></div>
                  </div>
                  <div v-if="task.last_error" class="mt-3 rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 px-3 py-2 text-sm text-red-700 dark:text-red-300 break-words">
                    {{ task.last_error }}
                  </div>
                </div>

                <div class="flex flex-wrap gap-2 lg:justify-end lg:max-w-[45%]">
                  <button @click="runTaskNow(task)" :disabled="runningTaskId === task.id" class="btn-success text-sm py-2 px-4 disabled:opacity-50">
                    {{ runningTaskId === task.id ? 'Running...' : 'Run Now' }}
                  </button>
                  <button @click="editTask(task)" class="bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 px-4 py-2 rounded-xl text-sm transition">
                    Edit
                  </button>
                  <button @click="toggleTaskEnabled(task)" class="px-4 py-2 rounded-xl text-sm transition"
                    :class="task.enabled ? 'bg-yellow-100 dark:bg-yellow-500/20 hover:bg-yellow-200 dark:hover:bg-yellow-500/30 text-yellow-700 dark:text-yellow-300' : 'bg-emerald-100 dark:bg-emerald-500/20 hover:bg-emerald-200 dark:hover:bg-emerald-500/30 text-emerald-700 dark:text-emerald-300'">
                    {{ task.enabled ? 'Disable' : 'Enable' }}
                  </button>
                  <button @click="deleteTask(task)" :disabled="deletingTaskId === task.id" class="bg-red-100 dark:bg-red-500/20 hover:bg-red-200 dark:hover:bg-red-500/30 text-red-700 dark:text-red-300 px-4 py-2 rounded-xl text-sm transition disabled:opacity-50">
                    {{ deletingTaskId === task.id ? 'Deleting...' : 'Delete' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'settings'">
        <form @submit.prevent="saveSettings" class="space-y-6">
          <div class="glass-panel p-5 sm:p-6">
            <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h3 class="text-xl font-bold">Server Settings</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Adjust the settings people actually use every day, without digging through raw property names.
                </p>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 font-mono">
                server.properties
              </div>
            </div>
          </div>

          <div v-for="section in settingsSections" :key="section.title" class="glass-panel p-5 sm:p-6">
            <div class="mb-5">
              <h4 class="text-lg font-semibold">{{ section.title }}</h4>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ section.description }}</p>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <template v-for="field in section.fields" :key="field.key">
                <label
                  v-if="field.type === 'boolean'"
                  class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.03] px-4 py-4 flex items-center justify-between gap-4"
                >
                  <div>
                    <div class="font-medium">{{ field.label }}</div>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ field.description }}</p>
                  </div>
                  <span class="relative inline-flex items-center flex-shrink-0">
                    <input
                      type="checkbox"
                      class="sr-only peer"
                      :checked="isBooleanSettingEnabled(field.key, field.defaultValue)"
                      @change="setBooleanSetting(field.key, $event.target.checked)"
                    />
                    <div class="w-10 h-5 bg-gray-300 dark:bg-gray-600 rounded-full peer peer-checked:bg-emerald-500 transition"></div>
                    <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
                  </span>
                </label>

                <div
                  v-else
                  class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.03] px-4 py-4"
                >
                  <div class="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <label class="block font-medium">{{ field.label }}</label>
                      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ field.description }}</p>
                    </div>
                    <span class="text-[11px] uppercase tracking-wide text-gray-400 dark:text-gray-500 font-mono">
                      {{ field.key }}
                    </span>
                  </div>

                  <select
                    v-if="field.type === 'select'"
                    :value="getSettingValue(field.key, field.defaultValue)"
                    @change="setSettingValue(field.key, $event.target.value)"
                    class="input-field text-sm"
                  >
                    <option v-for="option in field.options" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>

                  <input
                    v-else-if="field.type === 'number'"
                    :value="getSettingValue(field.key, field.defaultValue)"
                    @input="setSettingValue(field.key, $event.target.value)"
                    type="number"
                    :min="field.min"
                    :max="field.max"
                    class="input-field text-sm"
                  />

                  <input
                    v-else
                    :value="getSettingValue(field.key, field.defaultValue)"
                    @input="setSettingValue(field.key, $event.target.value)"
                    type="text"
                    :placeholder="field.placeholder || ''"
                    class="input-field text-sm"
                  />
                </div>
              </template>
            </div>
          </div>

          <div class="glass-panel p-5 sm:p-6">
            <div class="mb-5">
              <h4 class="text-lg font-semibold">Advanced Properties</h4>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Anything unusual or modpack-specific still lives here, so we don't box you into only the pretty controls.
              </p>
            </div>

            <div v-if="otherSettingsEntries.length === 0" class="rounded-2xl border border-dashed border-gray-300 dark:border-white/10 px-4 py-6 text-sm text-gray-500 dark:text-gray-400">
              No extra properties outside the guided settings right now.
            </div>

            <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div
                v-for="[key, value] in otherSettingsEntries"
                :key="key"
                class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.03] px-4 py-4"
              >
                <label class="block font-medium mb-2">{{ key }}</label>
                <input
                  :value="value"
                  @input="setSettingValue(key, $event.target.value)"
                  type="text"
                  class="input-field font-mono text-sm"
                />
              </div>
            </div>
          </div>

          <div class="flex justify-end">
            <button type="submit" class="btn-primary">
              Save Settings
            </button>
          </div>
        </form>
      </div>
      </div>
    </div>
  </div>

  <transition name="modal">
    <div v-if="showTaskModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="closeTaskModal">
      <div class="glass rounded-2xl p-6 sm:p-8 w-full max-w-xl scale-in dqs-modal-card">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="text-xl font-bold">{{ editingTaskId ? 'Edit Task' : 'New Task' }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Run server actions automatically in a set schedule.
            </p>
          </div>
          <button @click="closeTaskModal" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveTask" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Task Name</label>
            <input v-model="taskForm.name" type="text" placeholder="Nightly backup" class="input-field" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Schedule Type</label>
            <select v-model="taskForm.schedule_mode" class="input-field">
              <option value="interval">Repeat every X minutes</option>
              <option value="specific_time">Run at a specific time</option>
            </select>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Action</label>
              <select v-model="taskForm.action" class="input-field">
                <option v-for="option in taskActionOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
            <div v-if="taskForm.schedule_mode === 'interval'">
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Every</label>
              <select v-model.number="taskForm.interval_minutes" class="input-field">
                <option :value="5">5 minutes</option>
                <option :value="15">15 minutes</option>
                <option :value="30">30 minutes</option>
                <option :value="60">1 hour</option>
                <option :value="180">3 hours</option>
                <option :value="360">6 hours</option>
                <option :value="720">12 hours</option>
                <option :value="1440">24 hours</option>
              </select>
            </div>
            <div v-else>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Time</label>
              <input v-model="taskForm.run_time" type="time" class="input-field" />
            </div>
          </div>

          <div v-if="taskForm.schedule_mode === 'specific_time'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Days</label>
            <div class="grid grid-cols-4 sm:grid-cols-7 gap-2">
              <button
                v-for="day in taskDayOptions"
                :key="day.value"
                type="button"
                @click="toggleTaskRunDay(day.value)"
                :class="taskForm.run_days.includes(day.value)
                  ? 'bg-mc-accent text-white border-mc-accent'
                  : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-white/10 hover:bg-gray-200 dark:hover:bg-white/10'"
                class="rounded-xl border px-3 py-2 text-sm font-medium transition"
              >
                {{ day.label }}
              </button>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Specific times use the panel machine's local time.
            </p>
          </div>

          <div v-if="taskForm.action === 'command'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Console Command</label>
            <input v-model="taskForm.command" type="text" placeholder="say Server restart in 5 minutes" class="input-field font-mono" />
          </div>

          <label class="rounded-2xl border border-gray-200 dark:border-white/10 bg-white/80 dark:bg-black/10 px-4 py-4 flex items-center justify-between gap-4">
            <div>
              <div class="font-medium">Enabled</div>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Disabled tasks stay saved but stop running until you turn them back on.
              </p>
            </div>
            <span class="relative inline-flex items-center flex-shrink-0">
              <input type="checkbox" class="sr-only peer" v-model="taskForm.enabled" />
              <div class="w-10 h-5 bg-gray-300 dark:bg-gray-600 rounded-full peer peer-checked:bg-emerald-500 transition"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
            </span>
          </label>

          <div class="flex gap-3 pt-2">
            <button type="button" @click="closeTaskModal" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">
              Cancel
            </button>
            <button type="submit" :disabled="taskSaving" class="flex-1 btn-primary disabled:opacity-50">
              {{ taskSaving ? 'Saving...' : (editingTaskId ? 'Save Task' : 'Create Task') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showPlayitNeedsServerModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showPlayitNeedsServerModal = false">
      <div class="glass rounded-2xl p-6 sm:p-8 w-full max-w-md scale-in dqs-modal-card">
        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center text-amber-700 dark:text-amber-300 flex-shrink-0">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3m0 4h.01M10.29 3.86l-7.12 12.3A1 1 0 004.03 18h15.94a1 1 0 00.86-1.84l-7.12-12.3a1 1 0 00-1.72 0z" />
            </svg>
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold">Start the Server First</h2>
            <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Playit can only be claimed while this server is running. Start the server first, then come back here and click the Playit button again.
            </p>
          </div>
        </div>
        <div class="mt-6 flex justify-end">
          <button type="button" @click="showPlayitNeedsServerModal = false" class="btn-primary px-5 py-2.5">
            Okay
          </button>
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
      <div v-if="showEditor" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 dqs-modal-overlay" @click.self="requestCloseEditor">
        <div class="glass rounded-2xl w-full max-w-4xl flex flex-col max-h-[80vh] scale-in dqs-modal-card">
          <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-white/5">
            <div>
              <h3 class="font-semibold break-all">{{ editingFile }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Editable text files only • {{ formatSize(fileReadSize) }}</p>
            </div>
            <button @click="requestCloseEditor" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <textarea v-model="fileContent" class="flex-1 bg-gray-50 dark:bg-black/50 p-4 font-mono text-sm text-gray-900 dark:text-white resize-none focus:outline-none min-h-[300px]"></textarea>
          <div class="p-4 border-t border-gray-200 dark:border-white/5 flex items-center justify-between gap-3">
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ editorIsDirty ? 'Unsaved changes' : 'No unsaved changes' }}</span>
            <div class="flex justify-end gap-2">
              <button @click="requestCloseEditor" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-4 py-2 rounded-xl transition">Cancel</button>
              <button @click="saveFile" class="btn-primary">Save</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>

  <transition name="modal">
    <div v-if="showFileSearchModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showFileSearchModal = false">
      <div class="glass rounded-2xl w-full max-w-4xl flex flex-col max-h-[80vh] scale-in dqs-modal-card">
        <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-white/5">
          <div>
            <h3 class="font-semibold">File Search Results</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ fileSearchResults.length }} result{{ fileSearchResults.length === 1 ? '' : 's' }} for "{{ fileSearchQuery }}"
              <span v-if="fileSearchWasTruncated">(limited to {{ fileLimits.search_max_results }})</span>
            </p>
          </div>
          <button @click="showFileSearchModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-if="fileSearchResults.length === 0" class="text-center text-gray-500 dark:text-gray-500 py-12">
            No files matched this search.
          </div>
          <div v-else class="space-y-2">
            <div v-for="result in fileSearchResults" :key="result.path" class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-4 flex items-center justify-between gap-4">
              <div class="min-w-0">
                <p class="font-medium break-all">{{ result.name }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 break-all">{{ result.path }}</p>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <button @click="openSearchResult(result)" class="btn-primary text-sm py-2">Open</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showRenameModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showRenameModal = false">
      <div class="glass rounded-2xl p-6 w-full max-w-md scale-in dqs-modal-card">
        <h3 class="text-xl font-bold mb-2">Rename</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4 break-all">{{ renameForm.path }}</p>
        <input v-model="renameForm.newName" type="text" class="input-field mb-4" placeholder="New name" @keyup.enter="saveRename" />
        <div class="flex gap-2">
          <button @click="showRenameModal = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
          <button @click="saveRename" class="flex-1 btn-primary">Rename</button>
        </div>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showCreateFolderModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showCreateFolderModal = false">
      <div class="glass rounded-2xl p-6 w-full max-w-md scale-in dqs-modal-card">
        <h3 class="text-xl font-bold mb-2">New Folder</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Create a new folder inside {{ currentPath || 'root' }}.</p>
        <input v-model="createFolderForm.name" type="text" class="input-field mb-4" placeholder="Folder name" @keyup.enter="submitCreateFolder" />
        <div class="flex gap-2">
          <button @click="showCreateFolderModal = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
          <button @click="submitCreateFolder" class="flex-1 btn-primary">Create</button>
        </div>
      </div>
    </div>
  </transition>

  <transition name="modal">
    <div v-if="showArchiveModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="showArchiveModal = false">
      <div class="glass rounded-2xl p-6 w-full max-w-lg scale-in dqs-modal-card">
        <h3 class="text-xl font-bold mb-2">Archive Selected Files</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">{{ selectedFiles.length }} item{{ selectedFiles.length === 1 ? '' : 's' }} will be zipped into the current folder.</p>
        <input v-model="archiveForm.outputName" type="text" class="input-field mb-4" placeholder="archive-name.zip" @keyup.enter="createArchiveFromSelection" />
        <div class="max-h-40 overflow-y-auto rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/10 p-3 space-y-2 mb-4">
          <div v-for="item in selectedFiles" :key="item" class="text-sm break-all">{{ item }}</div>
        </div>
        <div class="flex gap-2">
          <button @click="showArchiveModal = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
          <button @click="createArchiveFromSelection" class="flex-1 btn-primary">Create Archive</button>
        </div>
      </div>
    </div>
  </transition>

  <!-- File upload modal — teleported to body to escape stacking contexts -->
  <Teleport to="body">
    <transition name="modal">
      <div v-if="showUpload" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 dqs-modal-overlay" @click.self="!uploadInProgress && closeUploadModal()">
        <div class="glass rounded-2xl p-5 sm:p-8 w-full max-w-2xl scale-in dqs-modal-card">
          <div class="flex items-center justify-between gap-3 mb-4">
            <div>
              <h3 class="text-xl font-bold">Upload</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">Queue files or folders and upload them with progress tracking.</p>
            </div>
            <button @click="closeUploadModal" :disabled="uploadInProgress" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition disabled:opacity-50">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="flex gap-2 mb-4">
            <button @click="uploadMode = 'file'" :class="uploadMode === 'file' ? 'bg-mc-accent text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400'"
              class="flex-1 py-2.5 rounded-xl transition">File</button>
            <button @click="uploadMode = 'folder'" :class="uploadMode === 'folder' ? 'bg-mc-accent text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400'"
              class="flex-1 py-2.5 rounded-xl transition">Folder</button>
          </div>
          <input v-if="uploadMode === 'file'" type="file" @change="handleFileUpload" class="mb-4" />
          <input v-if="uploadMode === 'folder'" type="file" webkitdirectory @change="handleFolderUpload" class="mb-4" />
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/10 p-4 mb-4 text-sm">
            <p>{{ uploadQueue.length }} item{{ uploadQueue.length === 1 ? '' : 's' }} queued • {{ formatSize(uploadTotalBytes) }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Each file must be under {{ formatSize(fileLimits.upload_limit_bytes) }}.</p>
          </div>
          <div v-if="uploadQueue.length > 0" class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/10 p-4 space-y-3 max-h-72 overflow-y-auto mb-4">
            <div v-for="item in uploadQueue" :key="item.id" class="space-y-1">
              <div class="flex items-center justify-between gap-3 text-sm">
                <span class="break-all">{{ item.relativePath }}</span>
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ item.status === 'queued' ? 'Waiting' : item.status === 'uploading' ? `${item.progress}%` : item.status === 'done' ? 'Done' : 'Failed' }}</span>
              </div>
              <div class="h-2 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
                <div :class="item.status === 'error' ? 'bg-red-500' : 'bg-mc-accent'" class="h-full transition-all duration-200" :style="{ width: `${item.progress}%` }"></div>
              </div>
              <p v-if="item.error" class="text-xs text-red-500 dark:text-red-300 break-all">{{ item.error }}</p>
            </div>
          </div>
          <div v-if="uploadInProgress" class="mb-4">
            <div class="flex items-center justify-between text-sm mb-2">
              <span>Overall progress</span>
              <span>{{ uploadOverallProgress }}%</span>
            </div>
            <div class="h-2 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
              <div class="h-full bg-emerald-500 transition-all duration-200" :style="{ width: `${uploadOverallProgress}%` }"></div>
            </div>
          </div>
          <div class="flex gap-2">
            <button @click="closeUploadModal" :disabled="uploadInProgress" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition disabled:opacity-50">Cancel</button>
            <button @click="uploadFile" :disabled="uploadInProgress || uploadQueue.length === 0" class="flex-1 btn-primary disabled:opacity-50">
              {{ uploadInProgress ? `Uploading ${uploadCompletedCount}/${uploadQueue.length}` : 'Upload' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>

  <transition name="modal">
    <div v-if="showEulaModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4 dqs-modal-overlay" @click.self="!acceptingEula && closeEulaModal()">
      <div class="glass rounded-2xl w-full max-w-2xl p-6 scale-in dqs-modal-card">
        <div class="flex justify-between items-start gap-4 mb-4">
          <div>
            <h3 class="text-2xl font-bold">Minecraft EULA</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">This server requires acceptance of the Minecraft End User License Agreement before the first start.</p>
          </div>
          <button @click="closeEulaModal" :disabled="acceptingEula" class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-xl transition disabled:opacity-50">
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
          <button @click="closeEulaModal" :disabled="acceptingEula" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 px-5 py-3 rounded-xl transition disabled:opacity-50">Cancel</button>
          <button @click="acceptEula" :disabled="acceptingEula" class="btn-success px-5 py-3 disabled:opacity-50">
            {{ acceptingEula ? 'Starting...' : 'Accept and Start' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, inject, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import { Terminal } from 'xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import 'xterm/css/xterm.css'

const route = useRoute()
const router = useRouter()
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
const consoleConnectionState = ref('idle')
const consoleAutoScroll = ref(true)
const files = ref([])
const currentPath = ref('')
const showEditor = ref(false)
const showUpload = ref(false)
const showFileSearchModal = ref(false)
const showRenameModal = ref(false)
const showCreateFolderModal = ref(false)
const showArchiveModal = ref(false)
const showEulaModal = ref(false)
const acceptingEula = ref(false)
const showSearchModal = ref(false)
const serverMissing = ref(false)
let missingServerRedirected = false

const ANSI_ESCAPE_REGEX = /\u001b\[[0-?]*[ -/]*[@-~]/g
const uploadMode = ref('file')
const editingFile = ref('')
const fileContent = ref('')
const originalFileContent = ref('')
const fileReadSize = ref(0)
const fileSearchQuery = ref('')
const searchingFiles = ref(false)
const fileSearchResults = ref([])
const fileSearchWasTruncated = ref(false)
const fileLimits = reactive({
  upload_limit_bytes: 100 * 1024 * 1024,
  text_edit_limit_bytes: 2 * 1024 * 1024,
  search_max_results: 200,
})
const renameForm = reactive({
  path: '',
  newName: '',
})
const createFolderForm = reactive({
  name: '',
})
const archiveForm = reactive({
  outputName: '',
})
const selectedFiles = ref([])
const sftpEnabled = ref(false)
const sftpStatus = ref('stopped')
const sftpPassword = ref('')
const sftpHost = window.location.hostname || 'localhost'
const sftpPort = ref(2223)
const uploadFileRef = ref(null)
const uploadFiles = ref([])
const uploadQueue = ref([])
const uploadInProgress = ref(false)
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
const settingsSections = [
  {
    title: 'Core Gameplay',
    description: 'The big server behavior choices people usually expect to change first.',
    fields: [
      {
        key: 'motd',
        label: 'MOTD',
        description: 'The message shown in the multiplayer server list.',
        type: 'text',
        defaultValue: 'A Minecraft Server',
        placeholder: 'A Minecraft Server',
      },
      {
        key: 'difficulty',
        label: 'Difficulty',
        description: 'How punishing the world should be.',
        type: 'select',
        defaultValue: 'easy',
        options: [
          { value: 'peaceful', label: 'Peaceful' },
          { value: 'easy', label: 'Easy' },
          { value: 'normal', label: 'Normal' },
          { value: 'hard', label: 'Hard' },
        ],
      },
      {
        key: 'gamemode',
        label: 'Default Game Mode',
        description: 'What players join into by default.',
        type: 'select',
        defaultValue: 'survival',
        options: [
          { value: 'survival', label: 'Survival' },
          { value: 'creative', label: 'Creative' },
          { value: 'adventure', label: 'Adventure' },
          { value: 'spectator', label: 'Spectator' },
        ],
      },
      {
        key: 'max-players',
        label: 'Max Players',
        description: 'How many players can join at once.',
        type: 'number',
        defaultValue: '20',
        min: 1,
        max: 500,
      },
      {
        key: 'pvp',
        label: 'PVP',
        description: 'Allow players to damage each other.',
        type: 'boolean',
        defaultValue: true,
      },
      {
        key: 'hardcore',
        label: 'Hardcore Mode',
        description: 'Enable hardcore survival rules.',
        type: 'boolean',
        defaultValue: false,
      },
    ],
  },
  {
    title: 'World Rules',
    description: 'A few practical world and mob settings without needing to know the raw property names.',
    fields: [
      {
        key: 'level-seed',
        label: 'World Seed',
        description: 'Leave blank to let Minecraft generate one.',
        type: 'text',
        defaultValue: '',
        placeholder: 'Optional seed',
      },
      {
        key: 'level-type',
        label: 'World Type',
        description: 'Choose the base terrain style for a new world.',
        type: 'select',
        defaultValue: 'minecraft:normal',
        options: [
          { value: 'minecraft:normal', label: 'Normal' },
          { value: 'minecraft:flat', label: 'Flat' },
          { value: 'minecraft:large_biomes', label: 'Large Biomes' },
          { value: 'minecraft:amplified', label: 'Amplified' },
        ],
      },
      {
        key: 'spawn-monsters',
        label: 'Hostile Mobs',
        description: 'Controls whether monsters can naturally spawn.',
        type: 'boolean',
        defaultValue: true,
      },
      {
        key: 'spawn-animals',
        label: 'Passive Animals',
        description: 'Controls whether passive mobs can naturally spawn.',
        type: 'boolean',
        defaultValue: true,
      },
      {
        key: 'generate-structures',
        label: 'Generate Structures',
        description: 'Villages, temples, strongholds, and other structures.',
        type: 'boolean',
        defaultValue: true,
      },
      {
        key: 'allow-nether',
        label: 'Allow Nether',
        description: 'Lets players travel to the Nether.',
        type: 'boolean',
        defaultValue: true,
      },
    ],
  },
  {
    title: 'Access & Performance',
    description: 'Connection, visibility, and simulation settings that matter for real players.',
    fields: [
      {
        key: 'online-mode',
        label: 'Online Mode',
        description: 'Verify players with Mojang before they join.',
        type: 'boolean',
        defaultValue: true,
      },
      {
        key: 'white-list',
        label: 'Whitelist',
        description: 'Only allow approved players to join.',
        type: 'boolean',
        defaultValue: false,
      },
      {
        key: 'allow-flight',
        label: 'Allow Flight',
        description: 'Useful for modded or admin-heavy servers.',
        type: 'boolean',
        defaultValue: false,
      },
      {
        key: 'enable-command-block',
        label: 'Command Blocks',
        description: 'Enable command block usage.',
        type: 'boolean',
        defaultValue: false,
      },
      {
        key: 'view-distance',
        label: 'View Distance',
        description: 'How far chunks are sent to players.',
        type: 'number',
        defaultValue: '10',
        min: 2,
        max: 32,
      },
      {
        key: 'simulation-distance',
        label: 'Simulation Distance',
        description: 'How far the world keeps ticking around players.',
        type: 'number',
        defaultValue: '10',
        min: 2,
        max: 32,
      },
    ],
  },
]
const knownSettingsKeys = new Set(settingsSections.flatMap((section) => section.fields.map((field) => field.key)))
const resources = reactive({ ram_min: 512, ram_max: 1024, cpu_cores: 1, custom_launch_command: '' })
const backups = ref([])
const backupLoading = ref(false)
const tasks = ref([])
const tasksLoading = ref(false)
const taskSaving = ref(false)
const editingTaskId = ref(null)
const runningTaskId = ref(null)
const deletingTaskId = ref(null)
const showTaskModal = ref(false)
const taskActionOptions = [
  { value: 'backup', label: 'Create Backup' },
  { value: 'restart', label: 'Restart Server' },
  { value: 'start', label: 'Start Server' },
  { value: 'stop', label: 'Stop Server' },
  { value: 'command', label: 'Send Command' },
]
const taskDayOptions = [
  { value: 0, label: 'Mon' },
  { value: 1, label: 'Tue' },
  { value: 2, label: 'Wed' },
  { value: 3, label: 'Thu' },
  { value: 4, label: 'Fri' },
  { value: 5, label: 'Sat' },
  { value: 6, label: 'Sun' },
]
const taskForm = reactive({
  name: '',
  action: 'backup',
  schedule_mode: 'interval',
  interval_minutes: 60,
  run_time: '03:00',
  run_days: [0, 1, 2, 3, 4, 5, 6],
  enabled: true,
  command: '',
})
const autoBackupEnabled = ref(localStorage.getItem(`autoBackup_${serverId}`) === 'true')
const autoBackupInterval = ref(localStorage.getItem(`autoBackupInterval_${serverId}`) || '21600000')
const autoBackupTimer = ref(null)
const nextBackupTime = ref('')
const playitBusy = ref(false)
const showPlayitNeedsServerModal = ref(false)
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
const commandHistory = ref([])
const commandHistoryIndex = ref(-1)

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
const consoleStatusLabel = computed(() => {
  if (consoleConnectionState.value === 'connected') return 'Live console connected'
  if (consoleConnectionState.value === 'connecting') return 'Connecting console'
  if (server.value?.status === 'running') return 'Console waiting to reconnect'
  return 'Server offline'
})
const consoleStatusBadgeClass = computed(() => {
  if (consoleConnectionState.value === 'connected') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
  if (consoleConnectionState.value === 'connecting') return 'border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300'
  if (server.value?.status === 'running') return 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300'
  return 'border-gray-300 bg-gray-100 text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300'
})
const otherSettingsEntries = computed(() =>
  Object.entries(settings.value || {})
    .filter(([key]) => !knownSettingsKeys.has(key))
    .sort(([a], [b]) => a.localeCompare(b))
)

function getSettingValue(key, fallback = '') {
  const value = settings.value?.[key]
  if (value === undefined || value === null || value === '') return String(fallback ?? '')
  return String(value)
}

function setSettingValue(key, value) {
  settings.value = {
    ...settings.value,
    [key]: String(value ?? ''),
  }
}

function isBooleanSettingEnabled(key, fallback = false) {
  const raw = String(settings.value?.[key] ?? String(Boolean(fallback))).toLowerCase()
  return raw === 'true' || raw === '1' || raw === 'yes'
}

function setBooleanSetting(key, enabled) {
  setSettingValue(key, enabled ? 'true' : 'false')
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
      startedAt: lastConsoleStartedAt,
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
    lastConsoleStartedAt = typeof parsed?.startedAt === 'string' ? parsed.startedAt : ''
    return true
  } catch {
    return false
  }
}

function clearConsoleHistory() {
  consoleLines.value = []
  consoleLineBuffer = ''
  lastConsoleStartedAt = ''
  renderConsoleHistory()
  try {
    localStorage.removeItem(getConsoleHistoryStorageKey())
  } catch {}
}

let consoleStream = null
let reconnectTimeout = null
let filesRefreshTimeout = null
let shouldKeepConsoleConnected = false
let consoleLineBuffer = ''
let lastConsoleStartedAt = ''
let filesRequestId = 0
let terminal = null
let terminalFitAddon = null
let terminalResizeObserver = null

function hasActiveConsoleStream() {
  return Boolean(consoleStream && (consoleStream.readyState === WebSocket.OPEN || consoleStream.readyState === WebSocket.CONNECTING))
}

function stopFilesRefreshLoop() {
  if (filesRefreshTimeout) {
    clearTimeout(filesRefreshTimeout)
    filesRefreshTimeout = null
  }
}

function startFilesRefreshLoop() {
  stopFilesRefreshLoop()
  const tick = async () => {
    if (activeTab.value !== 'files') {
      filesRefreshTimeout = null
      return
    }
    if (typeof document !== 'undefined' && document.hidden) {
      filesRefreshTimeout = setTimeout(() => {
        void tick()
      }, 4000)
      return
    }
    await navigateTo(currentPath.value, { silent: true })
    filesRefreshTimeout = setTimeout(() => {
      void tick()
    }, 2000)
  }
  filesRefreshTimeout = setTimeout(() => {
    void tick()
  }, 2000)
}

function fitConsoleTerminal() {
  if (!terminalFitAddon) return
  requestAnimationFrame(() => {
    try {
      terminalFitAddon.fit()
      if (consoleAutoScroll.value && terminal) {
        terminal.scrollToBottom()
      }
    } catch {}
  })
}

function renderConsoleHistory() {
  if (!terminal) return
  terminal.reset()
  if (consoleLines.value.length) {
    terminal.write(`${consoleLines.value.join('\r\n')}\r\n`)
  }
  if (consoleAutoScroll.value) {
    terminal.scrollToBottom()
  }
}

function initializeConsoleTerminal() {
  if (terminal || !consoleRef.value) return

  terminal = new Terminal({
    fontFamily: `'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`,
    fontSize: 13,
    lineHeight: 1.15,
    cursorBlink: true,
    cursorStyle: 'underline',
    allowTransparency: true,
    convertEol: true,
    disableStdin: true,
    theme: {
      background: '#050816',
      foreground: '#d1fae5',
      cursor: '#5eead4',
      selectionBackground: 'rgba(45, 212, 191, 0.25)',
      black: '#0b1120',
      red: '#f87171',
      green: '#4ade80',
      yellow: '#fbbf24',
      blue: '#60a5fa',
      magenta: '#c084fc',
      cyan: '#22d3ee',
      white: '#e5e7eb',
      brightBlack: '#475569',
      brightRed: '#fca5a5',
      brightGreen: '#86efac',
      brightYellow: '#fde68a',
      brightBlue: '#93c5fd',
      brightMagenta: '#d8b4fe',
      brightCyan: '#67e8f9',
      brightWhite: '#f8fafc',
    },
  })

  terminalFitAddon = new FitAddon()
  terminal.loadAddon(terminalFitAddon)
  terminal.loadAddon(new WebLinksAddon())
  terminal.open(consoleRef.value)
  terminal.onScroll(() => {
    if (!terminal) return
    consoleAutoScroll.value = terminal.buffer.active.viewportY >= terminal.buffer.active.baseY
  })
  renderConsoleHistory()
  fitConsoleTerminal()

  if (typeof ResizeObserver !== 'undefined') {
    terminalResizeObserver = new ResizeObserver(() => fitConsoleTerminal())
    terminalResizeObserver.observe(consoleRef.value)
  }
  window.addEventListener('resize', fitConsoleTerminal)
}

watch(activeTab, (newTab) => {
  if (newTab === 'files') {
    navigateTo(currentPath.value)
    startFilesRefreshLoop()
  }
  if (newTab === 'playit') {
    void fetchPlayitStatus()
  }
  if (newTab === 'console') {
    nextTick(() => initializeConsoleTerminal())
    shouldKeepConsoleConnected = true
    if (server.value?.status === 'running' && !hasActiveConsoleStream()) {
      connectConsoleStream({ replay: !consoleLines.value.length })
    } else {
      void fetchRecentConsoleLogs()
    }
  } else {
    shouldKeepConsoleConnected = false
    disconnectConsoleStream()
  }
  if (newTab === 'tasks') {
    void fetchTasks()
  }
  if (newTab !== 'files') {
    stopFilesRefreshLoop()
  }
})

const modLabel = computed(() => {
  const type = server.value?.server_type?.toLowerCase()
  if (type === 'paper' || type === 'spigot' || type === 'bukkit') return 'Plugins'
  return 'Mods'
})

const currentPathParts = computed(() => currentPath.value.split('/').filter(Boolean))
const hasSelectedFiles = computed(() => selectedFiles.value.length > 0)
const uploadTotalBytes = computed(() => uploadQueue.value.reduce((total, item) => total + (item.size || 0), 0))
const uploadCompletedCount = computed(() => uploadQueue.value.filter((item) => item.status === 'done').length)
const uploadFailedCount = computed(() => uploadQueue.value.filter((item) => item.status === 'error').length)
const uploadOverallProgress = computed(() => {
  if (!uploadQueue.value.length) return 0
  const completedBytes = uploadQueue.value.reduce((total, item) => {
    const ratio = item.status === 'done' ? 1 : Math.min(Math.max(item.progress || 0, 0), 100) / 100
    return total + Math.round((item.size || 0) * ratio)
  }, 0)
  return Math.min(Math.round((completedBytes / Math.max(uploadTotalBytes.value, 1)) * 100), 100)
})
const editorIsDirty = computed(() => showEditor.value && fileContent.value !== originalFileContent.value)

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
    { id: 'tasks', name: 'Tasks' },
    { id: 'settings', name: 'Settings' },
  )
  return list
})

function switchTab(tabId) {
  activeTab.value = tabId
  updatePlayitClaimPolling()
  if (tabId === 'files') {
    nextTick(() => navigateTo(currentPath.value))
  } else if (tabId === 'backups') {
    nextTick(() => fetchBackups())
  } else if (tabId === 'players') {
    nextTick(() => fetchPlayers())
  } else if (tabId === 'network') {
    nextTick(() => fetchNetworkStats())
  } else if (tabId === 'playit') {
    nextTick(() => fetchPlayitStatus())
  }
}

function shouldPollPlayitClaim() {
  return (
    activeTab.value === 'playit' &&
    !!playitStatus.value.enabled &&
    !!playitStatus.value.server_running &&
    !playitStatus.value.linked &&
    !!playitStatus.value.claim_url
  )
}

let playitClaimPollInterval = null
let playitClaimPollInFlight = false

function updatePlayitClaimPolling() {
  if (playitClaimPollInterval && !shouldPollPlayitClaim()) {
    clearInterval(playitClaimPollInterval)
    playitClaimPollInterval = null
  }

  if (!playitClaimPollInterval && shouldPollPlayitClaim()) {
    playitClaimPollInterval = setInterval(async () => {
      if (playitClaimPollInFlight || playitBusy.value) return
      playitClaimPollInFlight = true
      try {
        await syncPlayitStatus()
      } finally {
        playitClaimPollInFlight = false
      }
    }, 1500)
  }
}

function appendConsoleLine(line) {
  const normalized = String(line || '').trimEnd()
  if (!normalized) return
  consoleLines.value.push(normalized)
}

function finalizeConsoleLines() {
  if (consoleLines.value.length > 400) {
    consoleLines.value = consoleLines.value.slice(-400)
  }

  saveConsoleHistory()
  if (consoleAutoScroll.value && terminal) {
    terminal.scrollToBottom()
  }
}

function replaceConsoleLines(lines) {
  const incoming = Array.isArray(lines)
    ? lines
        .map((line) => String(line || '').trimEnd())
        .filter((line) => line)
    : []

  consoleLines.value = incoming.slice(-400)
  consoleLineBuffer = ''
  renderConsoleHistory()
  finalizeConsoleLines()
}

async function fetchRecentConsoleLogs() {
  try {
    const res = await axios.get(`/api/servers/${serverId}/console/recent`, {
      params: { tail: 200 },
    })
    const status = String(res.data?.status || '')
    const startedAt = String(res.data?.started_at || '')
    const lines = Array.isArray(res.data?.lines) ? res.data.lines : []

    if (status === 'missing' && lines.length === 0) {
      clearConsoleHistory()
      return
    }

    if (startedAt && startedAt !== lastConsoleStartedAt) {
      consoleLines.value = []
      consoleLineBuffer = ''
      lastConsoleStartedAt = startedAt
      saveConsoleHistory()
    } else if (startedAt && !lastConsoleStartedAt) {
      lastConsoleStartedAt = startedAt
    }

    replaceConsoleLines(lines)
  } catch (e) {
    console.error('Failed to fetch recent console logs:', e)
  }
}

function appendConsoleChunk(chunk) {
  const normalized = String(chunk || '').replace(/\r/g, '')
  if (!normalized) return

  if (terminal) {
    terminal.write(normalized.replace(/\n/g, '\r\n'))
    if (consoleAutoScroll.value) {
      terminal.scrollToBottom()
    }
  }

  consoleLineBuffer += normalized
  const parts = consoleLineBuffer.split('\n')
  consoleLineBuffer = parts.pop() || ''

  for (const part of parts) {
    appendConsoleLine(part)
  }

  finalizeConsoleLines()
}

function rememberConsoleCommand(value) {
  const next = String(value || '').trim()
  if (!next) return
  commandHistory.value = [next, ...commandHistory.value.filter((entry) => entry !== next)].slice(0, 50)
  commandHistoryIndex.value = -1
}

function recallPreviousCommand() {
  if (!commandHistory.value.length) return
  commandHistoryIndex.value = Math.min(commandHistoryIndex.value + 1, commandHistory.value.length - 1)
  command.value = commandHistory.value[commandHistoryIndex.value] || ''
}

function recallNextCommand() {
  if (!commandHistory.value.length) return
  commandHistoryIndex.value = Math.max(commandHistoryIndex.value - 1, -1)
  command.value = commandHistoryIndex.value >= 0 ? (commandHistory.value[commandHistoryIndex.value] || '') : ''
}

function toggleConsoleAutoScroll() {
  consoleAutoScroll.value = !consoleAutoScroll.value
  if (consoleAutoScroll.value && terminal) {
    terminal.scrollToBottom()
  }
}

async function copyConsoleOutput() {
  try {
    await navigator.clipboard.writeText(
      consoleLines.value
        .map((line) => String(line || '').replace(ANSI_ESCAPE_REGEX, ''))
        .join('\n')
    )
    toast({ type: 'success', title: 'Copied', message: 'Console output copied to clipboard' })
  } catch {
    toast({ type: 'error', title: 'Copy Failed', message: 'Could not copy console output' })
  }
}

async function copyPlayitAddress() {
  if (!playitStatus.value.saved_domain) return
  try {
    await navigator.clipboard.writeText(String(playitStatus.value.saved_domain))
    toast({ type: 'success', title: 'Copied', message: 'Playit address copied to clipboard' })
  } catch {
    toast({ type: 'error', title: 'Copy Failed', message: 'Could not copy the Playit address' })
  }
}

function setPreset(min, max) {
  resources.ram_min = min
  resources.ram_max = max
}

function isServerMissingError(error) {
  return Number(error?.response?.status) === 404
}

function handleServerMissing() {
  if (serverMissing.value) return
  serverMissing.value = true
  stopFilesRefreshLoop()
  disconnectConsoleStream()
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
  if (playitClaimPollInterval) {
    clearInterval(playitClaimPollInterval)
    playitClaimPollInterval = null
  }
  if (!missingServerRedirected) {
    missingServerRedirected = true
    toast({ type: 'warning', title: 'Server Removed', message: 'This server no longer exists.' })
    router.replace('/dashboard')
  }
}

async function fetchServer() {
  try {
    const res = await axios.get(`/api/servers/${serverId}`)
    serverMissing.value = false
    server.value = res.data
    resources.ram_min = res.data.ram_min
    resources.ram_max = res.data.ram_max
    resources.cpu_cores = res.data.cpu_cores
    resources.custom_launch_command = res.data.custom_launch_command || ''
    playitStatus.value.server_running = res.data.status === 'running'
    playitStatus.value.enabled = !!res.data.playit_enabled
    playitStatus.value.recommended_local_port = res.data.port || playitStatus.value.recommended_local_port
    return true
  } catch (e) {
    if (isServerMissingError(e)) {
      handleServerMissing()
      return false
    }
    console.error('Failed to fetch server:', e)
    return false
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
  updatePlayitClaimPolling()
}

async function fetchPlayitStatus() {
  try {
    const runtimeRes = await axios.get(`/api/servers/${serverId}/playit/runtime`)
    applyPlayitStatus({
      ...runtimeRes.data,
      connection_error: false,
      server_running: playitStatus.value.server_running,
      recommended_local_port: server.value?.port || runtimeRes.data?.recommended_local_port || playitStatus.value.recommended_local_port,
    })
    updatePlayitClaimPolling()
    return true
  } catch (e) {
    if (isServerMissingError(e)) {
      handleServerMissing()
      return false
    }
    console.error('Failed to fetch Playit runtime status:', e)
    playitStatus.value.connection_error = true
    updatePlayitClaimPolling()
    return false
  }
}

async function syncPlayitStatus() {
  try {
    const runtimeRes = await axios.post(`/api/servers/${serverId}/playit/runtime/sync`)
    applyPlayitStatus({
      ...runtimeRes.data,
      connection_error: false,
      server_running: playitStatus.value.server_running,
      recommended_local_port: server.value?.port || runtimeRes.data?.recommended_local_port || playitStatus.value.recommended_local_port,
    })
    updatePlayitClaimPolling()
    return true
  } catch (e) {
    if (isServerMissingError(e)) {
      handleServerMissing()
      return false
    }
    console.error('Failed to sync Playit runtime status:', e)
    toast({
      type: 'error',
      title: 'Refresh Failed',
      message: e.response?.data?.detail || 'Could not refresh Playit right now.',
    })
    updatePlayitClaimPolling()
    return false
  }
}

async function refreshServerActionState({ includeConsoleReplay = false } = {}) {
  const results = await Promise.allSettled([
    fetchServer(),
    fetchPlayitStatus(),
  ])

  const serverFailed = results[0]?.status === 'rejected'
  const playitFailed = results[1]?.status === 'rejected'

  if (serverFailed) {
    console.error('Failed to refresh server state after action:', results[0].reason)
  }
  if (playitFailed) {
    console.error('Failed to refresh Playit state after action:', results[1].reason)
  }

  if (activeTab.value === 'console') {
    if (server.value?.status === 'running') {
      if (!hasActiveConsoleStream()) {
        connectConsoleStream({ replay: includeConsoleReplay || !consoleLines.value.length })
      }
    } else {
      disconnectConsoleStream()
      await fetchRecentConsoleLogs()
    }
  }
}

async function enablePlayit() {
  if (!playitStatus.value.server_running) {
    showPlayitNeedsServerModal.value = true
    return
  }

  playitBusy.value = true
  try {
    const res = await axios.post(`/api/servers/${serverId}/playit/runtime/enable`)
    applyPlayitStatus(res.data)
    await fetchServer()
    toast({
      type: 'success',
      title: 'Playit Enabled',
      message: res.data?.claim_url
        ? 'Playit agent started. Open the claim link to finish linking it.'
        : (playitStatus.value.server_running ? 'The Playit agent is running for this server.' : 'Playit will start when the server starts.')
    })
  } catch (e) {
    toast({ type: 'error', title: 'Enable Failed', message: e.response?.data?.detail || 'Failed to enable Playit.' })
  } finally {
    playitBusy.value = false
  }
}

function openPlayitClaimLink() {
  if (!playitStatus.value.server_running) {
    showPlayitNeedsServerModal.value = true
    return
  }

  if (playitStatus.value.claim_url) {
    window.open(playitStatus.value.claim_url, '_blank', 'noopener,noreferrer')
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

async function monitorConsoleStartup(attempt = 0) {
  if (serverMissing.value || !shouldKeepConsoleConnected || activeTab.value !== 'console') {
    return
  }

  const serverStillExists = await fetchServer()
  if (serverStillExists === false || serverMissing.value) {
    return
  }

  if (server.value?.status === 'running') {
    connectConsoleStream({ replay: true })
    return
  }

  await fetchRecentConsoleLogs()

  if (attempt >= 19) {
    return
  }

  reconnectTimeout = setTimeout(() => {
    void monitorConsoleStartup(attempt + 1)
  }, 1500)
}

function getConsoleStreamUrl(options = {}) {
  const { replay = false } = options
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = (() => {
    const { hostname, port } = window.location
    if (port === '3000' || port === '5173') {
      return `${hostname}:8000`
    }
    return window.location.host
  })()
  const params = new URLSearchParams()
  if (server.value?.container_started_at) {
    params.set('startedAt', server.value.container_started_at)
  }
  if (replay) {
    params.set('replay', '1')
  }
  const query = params.toString() ? `?${params.toString()}` : ''
  return `${protocol}//${host}/api/servers/${serverId}/ws${query}`
}

function handleConsoleStreamMessage(payload) {
  if (!payload || typeof payload !== 'object') return

  if (payload.type === 'status') {
    const startedAt = String(payload.started_at || '')
    if (startedAt && startedAt !== lastConsoleStartedAt) {
      consoleLines.value = []
      consoleLineBuffer = ''
      lastConsoleStartedAt = startedAt
      renderConsoleHistory()
      saveConsoleHistory()
    } else if (startedAt && !lastConsoleStartedAt) {
      lastConsoleStartedAt = startedAt
    }

    if (payload.status && server.value) {
      server.value.status = payload.status
      server.value.container_started_at = startedAt
    }
    consoleConnectionState.value = payload.status === 'running' ? 'connected' : 'idle'
    return
  }

  if (payload.type === 'chunk') {
    if (payload.started_at && payload.started_at !== lastConsoleStartedAt) {
      consoleLines.value = []
      consoleLineBuffer = ''
      lastConsoleStartedAt = payload.started_at
      renderConsoleHistory()
    }
    appendConsoleChunk(payload.chunk || '')
    return
  }

  if (payload.type === 'error') {
    appendConsoleLine(`[${payload.detail || 'Console stream error'}]`)
    finalizeConsoleLines()
  }
}

function connectConsoleStream(options = {}) {
  if (serverMissing.value) return
  shouldKeepConsoleConnected = true
  if (consoleStream) {
    consoleStream.close()
    consoleStream = null
  }
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }

  try {
    const streamUrl = getConsoleStreamUrl(options)
    consoleConnectionState.value = 'connecting'
    const stream = new WebSocket(streamUrl)
    consoleStream = stream

    stream.onopen = () => {
      if (consoleStream !== stream) return
      consoleConnectionState.value = 'connected'
      if (server.value?.container_started_at) {
        lastConsoleStartedAt = server.value.container_started_at
        saveConsoleHistory()
      }
      fitConsoleTerminal()
    }

    stream.onmessage = (event) => {
      if (consoleStream !== stream) return
      try {
        handleConsoleStreamMessage(JSON.parse(event.data))
      } catch (error) {
        console.error('Failed to parse console stream event:', error)
      }
    }

    stream.onerror = () => {
      if (consoleStream !== stream) return
      consoleConnectionState.value = server.value?.status === 'running' ? 'idle' : 'idle'
    }

    stream.onclose = () => {
      if (consoleStream !== stream) {
        return
      }
      consoleConnectionState.value = server.value?.status === 'running' ? 'idle' : 'idle'
      const shouldReconnect = !serverMissing.value && shouldKeepConsoleConnected && activeTab.value === 'console' && server.value?.status === 'running'
      consoleStream = null
      if (shouldReconnect) {
        reconnectTimeout = setTimeout(async () => {
          const stillExists = await fetchServer()
          if (stillExists !== false && !serverMissing.value) {
            connectConsoleStream()
          }
        }, 1200)
      } else if (!shouldKeepConsoleConnected || activeTab.value !== 'console') {
        disconnectConsoleStream()
      } else {
        void fetchRecentConsoleLogs()
      }
    }
  } catch (e) {
    consoleConnectionState.value = 'idle'
    appendConsoleLine('[Failed to connect to console stream]')
    renderConsoleHistory()
    finalizeConsoleLines()
  }
}

function disconnectConsoleStream() {
  shouldKeepConsoleConnected = false
  consoleConnectionState.value = 'idle'
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  if (consoleStream) {
    consoleStream.close()
    consoleStream = null
  }
}

function closeEulaModal() {
  showEulaModal.value = false
}

async function startServer() {
  try {
    if (server.value && !server.value.eula_accepted) {
      showEulaModal.value = true
      return
    }

    clearConsoleHistory()
    await axios.post(`/api/servers/${serverId}/start`)
    await refreshServerActionState({ includeConsoleReplay: true })
    void monitorConsoleStartup()
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
  if (acceptingEula.value) {
    return
  }
  acceptingEula.value = true
  closeEulaModal()
  toast({ type: 'success', title: 'EULA Accepted', message: 'Server starting...' })
  try {
    clearConsoleHistory()
    await axios.post(`/api/servers/${serverId}/start`, { accept_eula: true })
    await refreshServerActionState({ includeConsoleReplay: true })
    void monitorConsoleStartup()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Failed to accept EULA'
    showEulaModal.value = true
    toast({ type: 'error', title: 'EULA Error', message: msg })
  } finally {
    acceptingEula.value = false
  }
}

async function stopServer() {
  try {
    disconnectConsoleStream()
    await axios.post(`/api/servers/${serverId}/stop`, {}, { timeout: 15000 })
    await new Promise(r => setTimeout(r, 500))
    await refreshServerActionState()
    appendConsoleLine('[Server stopped]')
    renderConsoleHistory()
    finalizeConsoleLines()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || 'Failed to stop server'
    console.error('Stop error:', msg)
    await fetchServer()
  }
}

async function restartServer() {
  try {
    disconnectConsoleStream()
    clearConsoleHistory()
    await axios.post(`/api/servers/${serverId}/restart`)
    await new Promise(r => setTimeout(r, 200))
    await refreshServerActionState({ includeConsoleReplay: true })
    setTimeout(() => {
      if (!hasActiveConsoleStream() && activeTab.value === 'console' && server.value?.status === 'running') {
        connectConsoleStream()
      }
    }, 500)
    toast({ type: 'success', title: 'Restarted', message: 'Server restarting...' })
  } catch (e) {
    const msg = e.response?.data?.detail || 'Failed to restart server'
    toast({ type: 'error', title: 'Restart Failed', message: msg })
    await fetchServer()
  }
}

async function sendCommand() {
  const nextCommand = command.value.trim()
  if (!nextCommand) return
  if (server.value?.status !== 'running') {
    toast({ type: 'warning', title: 'Server Offline', message: 'Server is not running' })
    return
  }

  try {
    if (consoleStream && consoleStream.readyState === WebSocket.OPEN) {
      consoleStream.send(JSON.stringify({ event: 'command', command: nextCommand }))
    } else {
      await axios.post(`/api/servers/${serverId}/console/command`, { command: nextCommand })
    }
    rememberConsoleCommand(nextCommand)
    command.value = ''
    commandHistoryIndex.value = -1
    if (!consoleStream || consoleStream.readyState === WebSocket.CLOSED) {
      connectConsoleStream()
    }
  } catch (e) {
    toast({ type: 'error', title: 'Command Failed', message: e.response?.data?.detail || 'Failed to send command' })
  }
}

async function navigateTo(path, options = {}) {
  const { silent = false } = options
  const requestedPath = path || ''
  currentPath.value = requestedPath
  const requestId = ++filesRequestId
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/`, {
      params: { path: requestedPath, _: Date.now() }
    })
    if (requestId !== filesRequestId || currentPath.value !== requestedPath) {
      return
    }
    files.value = res.data.sort((a, b) => {
      if (a.is_dir && !b.is_dir) return -1
      if (!a.is_dir && b.is_dir) return 1
      return a.name.localeCompare(b.name)
    })
  } catch (e) {
    if (requestId !== filesRequestId || currentPath.value !== requestedPath) {
      return
    }
    files.value = []
    if (requestedPath) {
      currentPath.value = ''
    }
    if (!silent) {
      toast({ type: 'error', title: 'Files Error', message: e.response?.data?.detail || 'Could not load files.' })
    }
  }
}

function formatTimestamp(value) {
  if (!value) return 'Unknown time'
  try {
    return new Date(value * 1000).toLocaleString()
  } catch {
    return 'Unknown time'
  }
}

function isFileSelected(path) {
  return selectedFiles.value.includes(path)
}

function toggleFileSelection(path) {
  if (isFileSelected(path)) {
    selectedFiles.value = selectedFiles.value.filter((item) => item !== path)
    return
  }
  selectedFiles.value = [...selectedFiles.value, path]
}

function clearSelectedFiles() {
  selectedFiles.value = []
}

function canExtractFile(name) {
  return String(name || '').toLowerCase().endsWith('.zip')
}

function isRiskyEditableFile(path) {
  return /\.(jar|zip|gz|tar|7z|png|jpe?g|gif|webp|ico|pdf|db|sqlite)$/i.test(path || '')
}

function createSuggestedArchiveName() {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  return `archive-${stamp}.zip`
}

async function fetchFileLimits() {
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/limits`)
    Object.assign(fileLimits, res.data || {})
  } catch (e) {
    console.error('Failed to fetch file limits:', e)
  }
}

function openUploadModal() {
  resetUploadSelection()
  showUpload.value = true
}

function closeUploadModal() {
  if (uploadInProgress.value) return
  showUpload.value = false
  resetUploadSelection()
}

function resetUploadSelection() {
  uploadFileRef.value = null
  uploadFiles.value = []
  uploadQueue.value = []
}

function createUploadQueueFromFiles(fileList) {
  uploadQueue.value = fileList.map((file, index) => ({
    id: `${Date.now()}-${index}-${file.name}`,
    file,
    relativePath: file.webkitRelativePath || file.name,
    size: file.size || 0,
    progress: 0,
    status: 'queued',
    error: '',
  }))
}

function handleFileUpload(event) {
  uploadFileRef.value = event.target.files?.[0] || null
  const nextFiles = uploadFileRef.value ? [uploadFileRef.value] : []
  createUploadQueueFromFiles(nextFiles)
}

function handleFolderUpload(event) {
  uploadFiles.value = Array.from(event.target.files || [])
  createUploadQueueFromFiles(uploadFiles.value)
}

async function openFileEntry(file) {
  const path = currentPath.value ? `${currentPath.value}/${file.name}` : file.name
  if (file.is_dir) {
    await navigateTo(path)
    return
  }
  await editFile(path)
}

async function editFile(path) {
  if (isRiskyEditableFile(path)) {
    const proceed = await confirmFn({
      title: 'Open Carefully',
      message: 'This file type may not be safe or useful to edit as plain text. Open it anyway?',
      type: 'warning',
      confirmText: 'Open',
    })
    if (!proceed) return
  }
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/read`, { params: { path } })
    editingFile.value = path
    fileContent.value = res.data.content
    originalFileContent.value = res.data.content
    fileReadSize.value = Number(res.data.size) || 0
    showEditor.value = true
  } catch (e) {
    toast({ type: 'error', title: 'Read Failed', message: e.response?.data?.detail || 'Failed to read file' })
  }
}

async function requestCloseEditor() {
  if (!editorIsDirty.value) {
    showEditor.value = false
    return
  }
  const ok = await confirmFn({
    title: 'Discard Changes',
    message: 'Close the editor and lose your unsaved changes?',
    type: 'warning',
    confirmText: 'Discard',
  })
  if (ok) {
    showEditor.value = false
  }
}

async function saveFile() {
  try {
    await axios.post(`/api/servers/${serverId}/files/write`, { path: editingFile.value, content: fileContent.value })
    originalFileContent.value = fileContent.value
    showEditor.value = false
    await navigateTo(currentPath.value, { silent: true })
    toast({ type: 'success', title: 'Saved', message: 'File saved successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Save Failed', message: 'Failed to save file' })
  }
}

async function uploadFile() {
  if (uploadQueue.value.length === 0) return

  uploadInProgress.value = true
  let uploadedCount = 0
  try {
    for (const item of uploadQueue.value) {
      item.status = 'uploading'
      item.error = ''
      item.progress = 0
      const formData = new FormData()
      formData.append('file', item.file)
      if (uploadMode.value === 'folder') {
        formData.append('relative_path', item.relativePath)
      }
      try {
        await axios.post(`/api/servers/${serverId}/files/upload`, formData, {
          params: { path: currentPath.value },
          onUploadProgress: (event) => {
            if (!event.total) return
            item.progress = Math.max(1, Math.min(100, Math.round((event.loaded / event.total) * 100)))
          },
        })
        item.progress = 100
        item.status = 'done'
        uploadedCount += 1
      } catch (e) {
        item.status = 'error'
        item.error = e.response?.data?.detail || 'Failed to upload this file'
      }
    }
    await navigateTo(currentPath.value)
    if (uploadedCount > 0) {
      toast({ type: 'success', title: 'Upload Complete', message: `${uploadedCount} file${uploadedCount === 1 ? '' : 's'} uploaded successfully` })
    }
    if (uploadFailedCount.value === 0) {
      closeUploadModal()
    }
  } finally {
    uploadInProgress.value = false
  }
}

async function deleteFile(path) {
  const ok = await confirmFn({ title: 'Delete', message: 'Delete this file/folder?', type: 'danger', confirmText: 'Delete' })
  if (ok) {
    try {
      await axios.delete(`/api/servers/${serverId}/files/`, { params: { path } })
      selectedFiles.value = selectedFiles.value.filter((item) => item !== path)
      await navigateTo(currentPath.value)
      toast({ type: 'success', title: 'Deleted', message: 'File deleted' })
    } catch (e) {
      toast({ type: 'error', title: 'Delete Failed', message: 'Failed to delete file' })
    }
  }
}

function openCreateFolderModal() {
  createFolderForm.name = ''
  showCreateFolderModal.value = true
}

async function submitCreateFolder() {
  const name = createFolderForm.name.trim()
  if (!name) return
  const path = currentPath.value ? `${currentPath.value}/${name}` : name
  try {
    await axios.post(`/api/servers/${serverId}/files/mkdir`, { path })
    showCreateFolderModal.value = false
    await navigateTo(currentPath.value)
    toast({ type: 'success', title: 'Created', message: `Folder "${name}" created` })
  } catch (e) {
    toast({ type: 'error', title: 'Create Failed', message: e.response?.data?.detail || 'Failed to create folder' })
  }
}

function openRenameModalFor(file) {
  renameForm.path = currentPath.value ? `${currentPath.value}/${file.name}` : file.name
  renameForm.newName = file.name
  showRenameModal.value = true
}

async function saveRename() {
  if (!renameForm.newName.trim()) return
  try {
    const res = await axios.post(`/api/servers/${serverId}/files/rename`, {
      path: renameForm.path,
      new_name: renameForm.newName.trim(),
    })
    const oldPath = renameForm.path
    const newPath = res.data?.path || oldPath
    selectedFiles.value = selectedFiles.value.map((item) => (item === oldPath ? newPath : item))
    if (editingFile.value === oldPath) {
      editingFile.value = newPath
    }
    showRenameModal.value = false
    await navigateTo(currentPath.value)
    toast({ type: 'success', title: 'Renamed', message: 'File renamed successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Rename Failed', message: e.response?.data?.detail || 'Failed to rename file' })
  }
}

function openArchiveModal() {
  if (!hasSelectedFiles.value) return
  archiveForm.outputName = createSuggestedArchiveName()
  showArchiveModal.value = true
}

async function createArchiveFromSelection() {
  if (!selectedFiles.value.length) return
  try {
    await axios.post(`/api/servers/${serverId}/files/archive`, {
      path: currentPath.value,
      items: selectedFiles.value,
      output_name: archiveForm.outputName.trim() || createSuggestedArchiveName(),
    })
    showArchiveModal.value = false
    clearSelectedFiles()
    await navigateTo(currentPath.value)
    toast({ type: 'success', title: 'Archive Created', message: 'ZIP archive created successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Archive Failed', message: e.response?.data?.detail || 'Failed to create archive' })
  }
}

async function extractFile(path) {
  const ok = await confirmFn({ title: 'Extract ZIP', message: 'Extract this ZIP archive into the current folder?', type: 'info', confirmText: 'Extract' })
  if (!ok) return
  try {
    await axios.post(`/api/servers/${serverId}/files/extract`, { path })
    await navigateTo(currentPath.value)
    toast({ type: 'success', title: 'Archive Extracted', message: 'ZIP archive extracted successfully' })
  } catch (e) {
    toast({ type: 'error', title: 'Extract Failed', message: e.response?.data?.detail || 'Failed to extract archive' })
  }
}

async function runFileSearch() {
  const query = fileSearchQuery.value.trim()
  if (query.length < 2) {
    toast({ type: 'warning', title: 'Search Too Short', message: 'Use at least 2 characters.' })
    return
  }
  searchingFiles.value = true
  try {
    const res = await axios.get(`/api/servers/${serverId}/files/search`, {
      params: { query, path: currentPath.value },
    })
    fileSearchResults.value = res.data.results || []
    fileSearchWasTruncated.value = !!res.data.truncated
    showFileSearchModal.value = true
  } catch (e) {
    toast({ type: 'error', title: 'Search Failed', message: e.response?.data?.detail || 'Failed to search files' })
  } finally {
    searchingFiles.value = false
  }
}

async function openSearchResult(result) {
  showFileSearchModal.value = false
  if (result.is_dir) {
    await navigateTo(result.path)
    return
  }
  const parent = result.parent || ''
  if (parent !== currentPath.value) {
    await navigateTo(parent, { silent: true })
  }
  await editFile(result.path)
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
      toast({ type: 'success', title: 'SFTP Enabled', message: `SFTP enabled on port ${sftpPort.value}.` })
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

function resetTaskForm() {
  editingTaskId.value = null
  taskForm.name = ''
  taskForm.action = 'backup'
  taskForm.schedule_mode = 'interval'
  taskForm.interval_minutes = 60
  taskForm.run_time = '03:00'
  taskForm.run_days = [0, 1, 2, 3, 4, 5, 6]
  taskForm.enabled = true
  taskForm.command = ''
}

function closeTaskModal() {
  showTaskModal.value = false
  resetTaskForm()
}

function openTaskModalForCreate() {
  resetTaskForm()
  showTaskModal.value = true
}

function editTask(task) {
  editingTaskId.value = task.id
  taskForm.name = task.name || ''
  taskForm.action = task.action || 'backup'
  taskForm.schedule_mode = task.schedule_mode || 'interval'
  taskForm.interval_minutes = Number(task.interval_minutes) || 60
  taskForm.run_time = task.run_time || '03:00'
  taskForm.run_days = Array.isArray(task.run_days) && task.run_days.length ? [...task.run_days] : [0, 1, 2, 3, 4, 5, 6]
  taskForm.enabled = task.enabled !== false
  taskForm.command = task.command || ''
  showTaskModal.value = true
}

function toggleTaskRunDay(dayValue) {
  if (taskForm.run_days.includes(dayValue)) {
    taskForm.run_days = taskForm.run_days.filter((day) => day !== dayValue)
    return
  }
  taskForm.run_days = [...taskForm.run_days, dayValue].sort((a, b) => a - b)
}

function taskPayloadFromForm() {
  return {
    name: taskForm.name.trim(),
    action: taskForm.action,
    schedule_mode: taskForm.schedule_mode,
    interval_minutes: Number(taskForm.interval_minutes) || 60,
    run_time: taskForm.schedule_mode === 'specific_time' ? taskForm.run_time : null,
    run_days: taskForm.schedule_mode === 'specific_time' ? [...taskForm.run_days].sort((a, b) => a - b) : [],
    enabled: !!taskForm.enabled,
    command: taskForm.action === 'command' ? taskForm.command.trim() : null,
  }
}

function taskPayloadFromTask(task, overrides = {}) {
  return {
    name: task.name,
    action: task.action,
    schedule_mode: task.schedule_mode || 'interval',
    interval_minutes: Number(task.interval_minutes) || 60,
    run_time: task.schedule_mode === 'specific_time' ? (task.run_time || '03:00') : null,
    run_days: task.schedule_mode === 'specific_time' ? (Array.isArray(task.run_days) ? [...task.run_days] : []) : [],
    enabled: task.enabled !== false,
    command: task.action === 'command' ? (task.command || '') : null,
    ...overrides,
  }
}

function taskActionLabel(action) {
  const option = taskActionOptions.find((entry) => entry.value === action)
  return option?.label || action
}

function formatTaskInterval(minutes) {
  const value = Number(minutes) || 0
  if (value < 60) return `${value} minute${value === 1 ? '' : 's'}`
  if (value % 1440 === 0) {
    const days = value / 1440
    return `${days} day${days === 1 ? '' : 's'}`
  }
  if (value % 60 === 0) {
    const hours = value / 60
    return `${hours} hour${hours === 1 ? '' : 's'}`
  }
  const hours = Math.floor(value / 60)
  const minutesPart = value % 60
  return `${hours}h ${minutesPart}m`
}

function formatTaskRunDays(days) {
  const values = Array.isArray(days) ? [...days].map((day) => Number(day)).filter((day) => day >= 0 && day <= 6).sort((a, b) => a - b) : []
  if (!values.length) return 'no days selected'
  if (values.length === 7) return 'every day'
  return values
    .map((value) => taskDayOptions.find((option) => option.value === value)?.label || String(value))
    .join(', ')
}

function formatTaskSchedule(task) {
  if ((task.schedule_mode || 'interval') === 'specific_time') {
    const time = task.run_time || '00:00'
    const days = formatTaskRunDays(task.run_days)
    if (days === 'every day') {
      return `Runs every day at ${time}`
    }
    return `Runs at ${time} on ${days}`
  }
  return `Runs every ${formatTaskInterval(task.interval_minutes)}`
}

function taskStatusLabel(task) {
  if (!task.enabled) return 'Disabled'
  if (task.last_status === 'running') return 'Running'
  if (task.last_status === 'success') return 'Healthy'
  if (task.last_status === 'failed') return 'Failed'
  return 'Waiting'
}

function taskStatusBadgeClass(task) {
  if (!task.enabled) return 'bg-gray-100 border-gray-200 text-gray-600 dark:bg-white/5 dark:border-white/10 dark:text-gray-300'
  if (task.last_status === 'running') return 'bg-blue-100 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:border-blue-500/20 dark:text-blue-300'
  if (task.last_status === 'success') return 'bg-emerald-100 border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-300'
  if (task.last_status === 'failed') return 'bg-red-100 border-red-200 text-red-700 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-300'
  return 'bg-yellow-100 border-yellow-200 text-yellow-700 dark:bg-yellow-500/10 dark:border-yellow-500/20 dark:text-yellow-300'
}

async function fetchTasks() {
  tasksLoading.value = true
  try {
    const res = await axios.get(`/api/servers/${serverId}/tasks`)
    tasks.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.error('Failed to fetch tasks:', e)
  } finally {
    tasksLoading.value = false
  }
}

async function saveTask() {
  const payload = taskPayloadFromForm()
  if (!payload.name) {
    toast({ type: 'error', title: 'Task Name Required', message: 'Give this task a name first.' })
    return
  }
  if (payload.action === 'command' && !payload.command) {
    toast({ type: 'error', title: 'Command Required', message: 'Command tasks need a console command to send.' })
    return
  }
  if (payload.schedule_mode === 'specific_time' && !payload.run_time) {
    toast({ type: 'error', title: 'Time Required', message: 'Pick a time for this scheduled task.' })
    return
  }
  if (payload.schedule_mode === 'specific_time' && payload.run_days.length === 0) {
    toast({ type: 'error', title: 'Days Required', message: 'Pick at least one day for this scheduled task.' })
    return
  }

  taskSaving.value = true
  try {
    if (editingTaskId.value) {
      await axios.put(`/api/servers/${serverId}/tasks/${editingTaskId.value}`, payload)
      toast({ type: 'success', title: 'Task Updated', message: 'Scheduled task updated successfully.' })
    } else {
      await axios.post(`/api/servers/${serverId}/tasks`, payload)
      toast({ type: 'success', title: 'Task Created', message: 'Scheduled task created successfully.' })
    }
    closeTaskModal()
    await fetchTasks()
  } catch (e) {
    toast({ type: 'error', title: 'Task Save Failed', message: e.response?.data?.detail || 'Failed to save scheduled task' })
  } finally {
    taskSaving.value = false
  }
}

async function toggleTaskEnabled(task) {
  try {
    await axios.put(`/api/servers/${serverId}/tasks/${task.id}`, taskPayloadFromTask(task, { enabled: !task.enabled }))
    await fetchTasks()
  } catch (e) {
    toast({ type: 'error', title: 'Task Update Failed', message: e.response?.data?.detail || 'Failed to update task state' })
  }
}

async function runTaskNow(task) {
  runningTaskId.value = task.id
  try {
    await axios.post(`/api/servers/${serverId}/tasks/${task.id}/run`)
    await fetchTasks()
    if (task.action === 'backup') {
      await fetchBackups()
    }
    toast({ type: 'success', title: 'Task Started', message: `"${task.name}" ran successfully.` })
  } catch (e) {
    toast({ type: 'error', title: 'Task Run Failed', message: e.response?.data?.detail || 'Failed to run task' })
  } finally {
    runningTaskId.value = null
  }
}

async function deleteTask(task) {
  const ok = await confirmFn({ title: 'Delete Task', message: `Delete "${task.name}"?`, type: 'danger', confirmText: 'Delete' })
  if (!ok) return

  deletingTaskId.value = task.id
  try {
    await axios.delete(`/api/servers/${serverId}/tasks/${task.id}`)
    if (editingTaskId.value === task.id) {
      closeTaskModal()
    }
    await fetchTasks()
    toast({ type: 'success', title: 'Task Deleted', message: 'Scheduled task deleted.' })
  } catch (e) {
    toast({ type: 'error', title: 'Task Delete Failed', message: e.response?.data?.detail || 'Failed to delete task' })
  } finally {
    deletingTaskId.value = null
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

function formatSize(bytes) {
  if (!Number.isFinite(Number(bytes)) || Number(bytes) < 0) return '-'
  if (bytes === 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

onMounted(async () => {
  await fetchServer()
  loadConsoleHistory()
  await fetchFileLimits()
  await navigateTo('')
  await fetchInstalledPlugins()
  await fetchSettings()
  await fetchSftpStatus()
  await fetchBackups()
  await fetchPlayitStatus()
  await nextTick()
  initializeConsoleTerminal()
  if (activeTab.value === 'network') {
    await fetchNetworkStats()
  }
  if (activeTab.value === 'tasks') {
    await fetchTasks()
  }
  if (activeTab.value === 'console') {
    if (server.value?.status === 'running') {
      connectConsoleStream({ replay: !consoleLines.value.length })
    } else {
      await fetchRecentConsoleLogs()
    }
  }
  if (activeTab.value === 'files') {
    startFilesRefreshLoop()
  }
  updatePlayitClaimPolling()
  statusInterval = setInterval(async () => {
    await fetchServer()
    await fetchPlayitStatus()
    if (activeTab.value === 'network') {
      await fetchNetworkStats()
    }
    if (activeTab.value === 'tasks') {
      await fetchTasks()
    }
    if (activeTab.value === 'console') {
      if (server.value?.status === 'running') {
        if (!hasActiveConsoleStream()) {
          connectConsoleStream({ replay: !consoleLines.value.length })
        }
      } else if (consoleConnectionState.value !== 'idle') {
        disconnectConsoleStream()
        await fetchRecentConsoleLogs()
      }
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

watch(() => taskForm.action, (action) => {
  if (action !== 'command') {
    taskForm.command = ''
  }
})

let statusInterval = null
let updateCheckInterval = null

onUnmounted(() => {
  stopFilesRefreshLoop()
  disconnectConsoleStream()
  if (terminalResizeObserver) {
    terminalResizeObserver.disconnect()
    terminalResizeObserver = null
  }
  window.removeEventListener('resize', fitConsoleTerminal)
  if (terminal) {
    terminal.dispose()
    terminal = null
    terminalFitAddon = null
  }
  if (statusInterval) {
    clearInterval(statusInterval)
  }
  if (playitClaimPollInterval) {
    clearInterval(playitClaimPollInterval)
    playitClaimPollInterval = null
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

.dqs-console-toolbar {
  padding: 0.85rem 0.95rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  background:
    radial-gradient(circle at top left, rgba(45, 212, 191, 0.12), transparent 38%),
    linear-gradient(135deg, rgba(10, 14, 24, 0.94), rgba(20, 28, 45, 0.88));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.dqs-console-toolbar-actions {
  justify-content: flex-end;
}

.dqs-console-status-pill {
  backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.dqs-console-action-btn {
  background: rgba(255, 255, 255, 0.05);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.dqs-console-action-btn:hover {
  border-color: rgba(45, 212, 191, 0.28);
  color: rgb(240 253 250);
  background: rgba(45, 212, 191, 0.12);
}

.server-terminal {
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.35), 0 20px 50px rgba(2, 6, 23, 0.35);
}

.dqs-console-terminal {
  background:
    radial-gradient(circle at top, rgba(45, 212, 191, 0.08), transparent 42%),
    linear-gradient(180deg, rgba(3, 7, 18, 0.98), rgba(2, 6, 23, 0.96));
  border-color: rgba(255, 255, 255, 0.08);
}

.server-terminal :deep(.xterm) {
  height: 100%;
  padding: 0.9rem 1rem;
}

.server-terminal :deep(.xterm-viewport) {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.45) transparent;
}

.server-terminal :deep(.xterm-screen canvas) {
  width: 100% !important;
}

@media (max-width: 640px) {
  .dqs-console-toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }
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
