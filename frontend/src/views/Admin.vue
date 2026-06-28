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
          <div class="h-full transition-all duration-500" :class="isDqsTheme ? 'bg-gradient-to-r from-[#0f2748] via-[#174d88] to-[#38bdf8]' : 'bg-gradient-to-r from-red-500 to-orange-400'" :style="{width: (stats.system?.cpu_percent || 0) + '%'}"></div>
        </div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">CPU Usage</p>
          <svg class="w-6 h-6" :class="isDqsTheme ? 'text-sky-300' : 'text-red-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
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
             <div class="w-3 h-3 rounded-full" :class="isDqsTheme ? 'bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,0.7)]' : 'bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.7)]'"></div>
             <h3 class="font-bold text-lg">CPU History</h3>
          </div>
          <span class="text-sm font-medium px-3 py-1 rounded-full border" :class="isDqsTheme ? 'bg-sky-500/10 text-sky-300 border-sky-400/20' : 'bg-purple-500/10 text-purple-400 border-purple-500/20'">
            {{ stats.system?.cpu_percent || 0 }}% Load
          </span>
        </div>
        <div class="flex-1 w-full relative">
          <canvas ref="cpuCanvas" class="w-full h-[180px] rounded-lg"></canvas>
        </div>
        <div class="grid grid-cols-3 gap-3 mt-5">
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-3">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Current</p>
            <p class="text-lg font-bold mt-1">{{ formatPercent(cpuSummary.current) }}</p>
          </div>
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-3">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Average</p>
            <p class="text-lg font-bold mt-1">{{ formatPercent(cpuSummary.average) }}</p>
          </div>
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-3">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Peak</p>
            <p class="text-lg font-bold mt-1">{{ formatPercent(cpuSummary.peak) }}</p>
          </div>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-3">{{ historyTimeRangeLabel }}</p>
      </div>

      <!-- Memory Graph -->
      <div class="glass-panel p-6 hover-card flex flex-col">
        <div class="flex justify-between items-center mb-6">
          <div class="flex items-center gap-3">
             <div class="w-3 h-3 rounded-full" :class="isDqsTheme ? 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.7)]' : 'bg-pink-500 shadow-[0_0_10px_rgba(236,72,153,0.7)]'"></div>
             <h3 class="font-bold text-lg">Memory History</h3>
          </div>
          <span class="text-sm font-medium px-3 py-1 rounded-full border" :class="isDqsTheme ? 'bg-cyan-500/10 text-cyan-300 border-cyan-400/20' : 'bg-pink-500/10 text-pink-400 border-pink-500/20'">
            {{ stats.system?.memory_percent || 0 }}% Load
          </span>
        </div>
        <div class="flex-1 w-full relative">
          <canvas ref="memCanvas" class="w-full h-[180px] rounded-lg"></canvas>
        </div>
        <div class="grid grid-cols-3 gap-3 mt-5">
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-3">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Current</p>
            <p class="text-lg font-bold mt-1">{{ formatPercent(memorySummary.current) }}</p>
          </div>
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-3">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Average</p>
            <p class="text-lg font-bold mt-1">{{ formatPercent(memorySummary.average) }}</p>
          </div>
          <div class="rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-3">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Peak</p>
            <p class="text-lg font-bold mt-1">{{ formatPercent(memorySummary.peak) }}</p>
          </div>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-3">{{ historyTimeRangeLabel }}</p>
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
          <div class="h-full rounded-full transition-all duration-1000 ease-out" :class="isDqsTheme ? 'bg-gradient-to-r from-[#0b1c38] via-[#123d72] to-[#38bdf8]' : 'bg-gradient-to-r from-pink-500 to-rose-400'"
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

    <div class="glass-panel p-6 hover-card mb-8">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
        <div>
          <h3 class="font-bold text-lg flex items-center gap-2">
            <svg class="w-5 h-5 text-mc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 3h7l5 5v13a1 1 0 01-1 1H7a2 2 0 01-2-2V5a2 2 0 012-2z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 3v5h5"></path></svg>
            File Upload Limit
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Change the maximum allowed upload size for the panel file manager.</p>
        </div>
        <div class="flex flex-col sm:flex-row items-stretch sm:items-end gap-3 lg:min-w-[340px]">
          <label class="flex-1">
            <span class="block text-sm text-gray-500 dark:text-gray-400 mb-2">Limit in MB</span>
            <input v-model.number="panelSettings.upload_limit_mb" type="number" min="1" max="2048" class="input-field w-full" :class="isDqsTheme ? 'border-sky-900/60 bg-slate-950/70 text-sky-100 placeholder:text-sky-300/40 focus:border-sky-500 focus:ring-sky-500/20' : ''" />
          </label>
          <button @click="saveUploadLimit" :disabled="savingUploadLimit" class="px-5 py-3 rounded-xl font-bold text-white hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 disabled:scale-100" :class="isDqsTheme ? 'bg-gradient-to-r from-[#0f2748] via-[#174d88] to-[#2563eb] shadow-lg shadow-sky-950/30' : 'bg-gradient-to-r from-mc-accent to-mc-purple'">
            {{ savingUploadLimit ? 'Saving...' : 'Save Limit' }}
          </button>
        </div>
      </div>
      <div class="mt-4 flex flex-wrap items-center gap-3 text-sm">
        <span class="px-3 py-1 rounded-full bg-black/10 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-300">
          Current: {{ panelSettings.upload_limit_mb || 100 }} MB
        </span>
        <span class="text-gray-500 dark:text-gray-400">
          Bigger files than this will be rejected in the file manager upload modal.
        </span>
      </div>
    </div>

    <div class="glass-panel p-6 hover-card mb-8">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
        <div>
          <h3 class="font-bold text-lg flex items-center gap-2">
            <svg class="w-5 h-5 text-mc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h10M7 12h10m-10 5h6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z"></path></svg>
            Egg Controls
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Control whether Pterodactyl egg imports are available panel-wide and whether only admins can upload egg JSON files.</p>
        </div>
        <button @click="savePearlSettings" :disabled="savingPearlSettings" class="px-5 py-3 rounded-xl font-bold text-white hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 disabled:scale-100" :class="isDqsTheme ? 'bg-gradient-to-r from-[#0f2748] via-[#174d88] to-[#2563eb] shadow-lg shadow-sky-950/30' : 'bg-gradient-to-r from-mc-accent to-mc-purple'">
          {{ savingPearlSettings ? 'Saving...' : 'Save Egg Settings' }}
        </button>
      </div>

      <div class="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        <label class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-4 flex items-start gap-4 cursor-pointer">
          <input v-model="panelSettings.pearls_enabled" type="checkbox" class="mt-1 h-5 w-5 rounded border-gray-300 text-mc-accent focus:ring-mc-accent" />
          <div>
            <p class="font-semibold text-gray-900 dark:text-white">Enable Pterodactyl Eggs</p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Show the eggs tab in server creation and allow the saved egg library to be used.</p>
          </div>
        </label>

        <label class="rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-4 py-4 flex items-start gap-4 cursor-pointer">
          <input v-model="panelSettings.pearls_admin_only_upload" type="checkbox" class="mt-1 h-5 w-5 rounded border-gray-300 text-mc-accent focus:ring-mc-accent" :disabled="!panelSettings.pearls_enabled" />
          <div>
            <p class="font-semibold text-gray-900 dark:text-white">Only Admins can upload Eggs</p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Regular users will only see the saved egg collection and won’t be allowed to upload new JSON files.</p>
          </div>
        </label>
      </div>
      </div>
    </div>

    <!-- Integrations -->
    <div class="glass-panel overflow-hidden hover-card mb-8">
      <div class="p-6 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
        <h3 class="font-bold text-lg flex items-center gap-2">
          <svg class="w-5 h-5 text-mc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
          Google Drive Integration
        </h3>
        <span v-if="gdriveStatus.linked" class="px-2 py-1 bg-green-500/20 text-green-500 rounded text-xs font-bold uppercase tracking-wider">Linked</span>
        <span v-else class="px-2 py-1 bg-gray-500/20 text-gray-400 rounded text-xs font-bold uppercase tracking-wider">Unlinked</span>
      </div>
      
      <div class="p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Configure a Google Cloud OAuth App to allow EnderPanel to upload server backups directly to Google Drive.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Client ID</label>
            <input v-model="gdriveConfig.client_id" type="text" class="input-field w-full" placeholder="Enter Google Client ID" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Client Secret</label>
            <input v-model="gdriveConfig.client_secret" type="password" class="input-field w-full" placeholder="Enter Google Client Secret" />
          </div>
        </div>

        <div class="flex gap-4 items-center">
          <button @click="saveGDriveConfig" :disabled="savingGDrive" class="btn-primary py-2 px-4 rounded-xl">
            {{ savingGDrive ? 'Saving...' : 'Save Configuration' }}
          </button>
          
          <button v-if="gdriveStatus.configured && !gdriveStatus.linked" @click="linkGDrive" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-500 font-bold rounded-xl transition-all">
            Link Account
          </button>
          
          <button v-if="gdriveStatus.linked" @click="unlinkGDrive" class="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-500 font-bold rounded-xl transition-all">
            Unlink Account
          </button>
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
import { ref, computed, onMounted, onUnmounted, inject, nextTick, watchEffect } from 'vue'
import axios from 'axios'

const toast = inject('toast')

const stats = ref({})
const updateInfo = ref({})
const updating = ref(false)
const panelSettings = ref({
  upload_limit_mb: 100,
  min_upload_limit_mb: 1,
  max_upload_limit_mb: 2048,
  pearls_enabled: true,
  pearls_admin_only_upload: false,
})
const savingUploadLimit = ref(false)
const savingPearlSettings = ref(false)
const gdriveConfig = ref({ client_id: '', client_secret: '' })
const gdriveStatus = ref({ configured: false, linked: false })
const savingGDrive = ref(false)
const isDqsTheme = ref(false)

const dockerAvailable = computed(() => stats.value.docker?.available !== false)
const cpuCanvas = ref(null)
const memCanvas = ref(null)
let interval
const cpuSummary = computed(() => summarizeSeries(stats.value.history?.cpu || [], stats.value.system?.cpu_percent))
const memorySummary = computed(() => summarizeSeries(stats.value.history?.memory || [], stats.value.system?.memory_percent))
const historyTimeRangeLabel = computed(() => {
  const timestamps = stats.value.history?.timestamps || []
  if (!Array.isArray(timestamps) || timestamps.length < 2) return 'Waiting for more history points.'
  const start = new Date(timestamps[0] * 1000)
  const end = new Date(timestamps[timestamps.length - 1] * 1000)
  return `Range: ${start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} to ${end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
})
const cpuGraphColor = computed(() => (isDqsTheme.value ? '#38BDF8' : '#A855F7'))
const memoryGraphColor = computed(() => (isDqsTheme.value ? '#22D3EE' : '#EC4899'))

function syncAdminThemeState() {
  if (typeof document === 'undefined') return
  isDqsTheme.value =
    document.documentElement.classList.contains('theme-dqs') ||
    localStorage.getItem('theme') === 'dqs-hosting'
}

function summarizeSeries(series, currentOverride = null) {
  const values = Array.isArray(series) ? series.filter((value) => Number.isFinite(Number(value))).map(Number) : []
  if (!values.length) {
    const current = Number.isFinite(Number(currentOverride)) ? Number(currentOverride) : 0
    return { current, average: current, peak: current }
  }
  const total = values.reduce((sum, value) => sum + value, 0)
  const current = Number.isFinite(Number(currentOverride)) ? Number(currentOverride) : (values[values.length - 1] || 0)
  return {
    current,
    average: total / values.length,
    peak: Math.max(...values, current),
  }
}

function drawBezierGraph(canvas, data, timestamps, hexColor) {
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
  const padding = { top: 16, right: 12, bottom: 28, left: 38 }
  const plotW = Math.max(10, w - padding.left - padding.right)
  const plotH = Math.max(10, h - padding.top - padding.bottom)
  const maxValue = Math.max(100, ...data.map((value) => Number(value) || 0))
  const gridSteps = 4

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.14)'
  ctx.fillStyle = 'rgba(148, 163, 184, 0.85)'
  ctx.lineWidth = 1
  ctx.font = '11px system-ui, -apple-system, sans-serif'

  for (let i = 0; i <= gridSteps; i++) {
    const y = padding.top + (plotH / gridSteps) * i
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(w - padding.right, y)
    ctx.stroke()

    const labelValue = Math.round(maxValue - (maxValue / gridSteps) * i)
    ctx.fillText(`${labelValue}%`, 4, y + 4)
  }

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.10)'
  for (let i = 0; i <= 3; i++) {
    const x = padding.left + (plotW / 3) * i
    ctx.beginPath()
    ctx.moveTo(x, padding.top)
    ctx.lineTo(x, h - padding.bottom)
    ctx.stroke()
  }

  const step = plotW / (data.length - 1)
  const points = data.map((v, i) => ({
    x: padding.left + i * step,
    y: padding.top + plotH - ((Number(v) || 0) / maxValue) * plotH,
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
  ctx.lineTo(padding.left + plotW, padding.top + plotH)
  ctx.lineTo(padding.left, padding.top + plotH)
  ctx.closePath()

  const [_, r, g, b] = hexColor.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i) || [0, 168, 85, 247]
  const rgb = r && g && b ? `${parseInt(r, 16)}, ${parseInt(g, 16)}, ${parseInt(b, 16)}` : '168, 85, 247'
  
  const grad = ctx.createLinearGradient(0, 0, 0, h)
  grad.addColorStop(0, `rgba(${rgb}, 0.35)`)
  grad.addColorStop(1, `rgba(${rgb}, 0.0)`)
  
  ctx.fillStyle = grad
  ctx.fill()

  const lastPoint = points[points.length - 1]
  ctx.beginPath()
  ctx.arc(lastPoint.x, lastPoint.y, 4, 0, Math.PI * 2)
  ctx.fillStyle = '#ffffff'
  ctx.fill()
  ctx.beginPath()
  ctx.arc(lastPoint.x, lastPoint.y, 2.5, 0, Math.PI * 2)
  ctx.fillStyle = hexColor
  ctx.fill()

  const timeLabels = Array.isArray(timestamps) ? timestamps : []
  if (timeLabels.length >= 2) {
    const first = new Date(timeLabels[0] * 1000)
    const middle = new Date(timeLabels[Math.floor(timeLabels.length / 2)] * 1000)
    const last = new Date(timeLabels[timeLabels.length - 1] * 1000)
    const labels = [
      { x: padding.left, text: first.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), align: 'left' },
      { x: padding.left + plotW / 2, text: middle.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), align: 'center' },
      { x: padding.left + plotW, text: last.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), align: 'right' },
    ]
    ctx.fillStyle = 'rgba(148, 163, 184, 0.85)'
    labels.forEach((label) => {
      ctx.textAlign = label.align
      ctx.fillText(label.text, label.x, h - 8)
    })
    ctx.textAlign = 'left'
  }
}

async function fetchStats() {
  try {
    syncAdminThemeState()
    const res = await axios.get('/api/admin/stats')
    stats.value = res.data
    await nextTick()
    if (res.data.history) {
      drawBezierGraph(cpuCanvas.value, res.data.history.cpu, res.data.history.timestamps, cpuGraphColor.value)
      drawBezierGraph(memCanvas.value, res.data.history.memory, res.data.history.timestamps, memoryGraphColor.value)
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

async function fetchPanelSettings() {
  try {
    const res = await axios.get('/api/admin/panel-settings')
    panelSettings.value = {
      ...panelSettings.value,
      ...res.data,
    }
  } catch (e) {
    console.warn('Failed to fetch panel settings')
  }
}

async function saveUploadLimit() {
  const nextValue = Number(panelSettings.value.upload_limit_mb)
  const min = Number(panelSettings.value.min_upload_limit_mb || 1)
  const max = Number(panelSettings.value.max_upload_limit_mb || 2048)
  if (!Number.isFinite(nextValue) || nextValue < min || nextValue > max) {
    toast?.({ title: 'Invalid limit', message: `Choose a value between ${min}MB and ${max}MB.`, type: 'error' })
    return
  }

  savingUploadLimit.value = true
  try {
    const res = await axios.put('/api/admin/panel-settings/upload-limit', {
      upload_limit_mb: nextValue,
    })
    panelSettings.value.upload_limit_mb = res.data.upload_limit_mb
    toast?.({ title: 'Saved', message: `Upload limit set to ${res.data.upload_limit_mb}MB.`, type: 'success' })
  } catch (e) {
    toast?.({ title: 'Save failed', message: e.response?.data?.detail || 'Could not save upload limit.', type: 'error' })
  } finally {
    savingUploadLimit.value = false
  }
}

async function savePearlSettings() {
  savingPearlSettings.value = true
  try {
    const res = await axios.put('/api/admin/panel-settings/pearls', {
      pearls_enabled: !!panelSettings.value.pearls_enabled,
      pearls_admin_only_upload: !!panelSettings.value.pearls_admin_only_upload,
    })
    panelSettings.value.pearls_enabled = res.data.pearls_enabled
    panelSettings.value.pearls_admin_only_upload = res.data.pearls_admin_only_upload
    toast?.({ title: 'Saved', message: 'Egg feature settings updated.', type: 'success' })
  } catch (e) {
    toast?.({ title: 'Save failed', message: e.response?.data?.detail || 'Could not save egg settings.', type: 'error' })
  } finally {
    savingPearlSettings.value = false
  }
}

async function fetchGDriveConfig() {
  try {
    const res = await axios.get('/api/gdrive/config')
    gdriveConfig.value = res.data
    const statusRes = await axios.get('/api/gdrive/status')
    gdriveStatus.value = statusRes.data
  } catch (e) {
    console.warn('Failed to fetch GDrive config', e)
  }
}

async function saveGDriveConfig() {
  savingGDrive.value = true
  try {
    await axios.put('/api/gdrive/config', gdriveConfig.value)
    toast?.({ title: 'Saved', message: 'Google Drive configuration updated.', type: 'success' })
    fetchGDriveConfig()
  } catch (e) {
    toast?.({ title: 'Error', message: 'Failed to save Google Drive config', type: 'error' })
  } finally {
    savingGDrive.value = false
  }
}

async function linkGDrive() {
  try {
    const redirect_uri = window.location.origin + '/admin/gdrive-callback'
    const res = await axios.post('/api/gdrive/auth-url', { redirect_uri })
    window.location.href = res.data.url
  } catch (e) {
    toast?.({ title: 'Error', message: 'Failed to get auth URL', type: 'error' })
  }
}

async function unlinkGDrive() {
  if (!confirm('Are you sure you want to unlink Google Drive?')) return
  try {
    await axios.post('/api/gdrive/unlink')
    toast?.({ title: 'Unlinked', message: 'Google Drive has been unlinked.', type: 'success' })
    fetchGDriveConfig()
  } catch (e) {
    toast?.({ title: 'Error', message: 'Failed to unlink Google Drive', type: 'error' })
  }
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

function formatPercent(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '0%'
  return `${numeric.toFixed(1)}%`
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
  syncAdminThemeState()
  fetchStats()
  checkUpdate()
  fetchPanelSettings()
  fetchGDriveConfig()
  interval = setInterval(fetchStats, 15000)

  resizeHandler = () => {
    syncAdminThemeState()
    if (stats.value.history) {
      drawBezierGraph(cpuCanvas.value, stats.value.history.cpu, stats.value.history.timestamps, cpuGraphColor.value)
      drawBezierGraph(memCanvas.value, stats.value.history.memory, stats.value.history.timestamps, memoryGraphColor.value)
    }
  }
  window.addEventListener('resize', resizeHandler)
})

watchEffect(() => {
  if (stats.value.history && cpuCanvas.value && memCanvas.value) {
    drawBezierGraph(cpuCanvas.value, stats.value.history.cpu, stats.value.history.timestamps, cpuGraphColor.value)
    drawBezierGraph(memCanvas.value, stats.value.history.memory, stats.value.history.timestamps, memoryGraphColor.value)
  }
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
