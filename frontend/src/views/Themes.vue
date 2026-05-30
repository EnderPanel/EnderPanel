<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold">Themes</h1>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        Choose how EnderPanel looks across the app.
      </p>
    </div>

    <div class="grid gap-6 md:grid-cols-3">
      <button
        @click="setTheme('light')"
        class="text-left rounded-2xl border p-6 transition-all duration-200"
        :class="themeStore.currentTheme === 'light'
          ? 'border-amber-300 bg-amber-50 shadow-lg shadow-amber-200/40 dark:border-amber-400/50 dark:bg-amber-500/10'
          : 'border-gray-200 bg-white hover:border-amber-200 dark:border-white/10 dark:bg-white/5 dark:hover:border-amber-400/30'"
      >
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <h2 class="text-xl font-semibold">Light</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Bright panels with softer contrast for daytime use.
            </p>
          </div>
          <span v-if="themeStore.currentTheme === 'light'" class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500 text-white">
            Active
          </span>
        </div>

        <div class="rounded-xl border border-gray-200 bg-gray-50 p-4">
          <div class="h-4 w-24 rounded bg-white shadow-sm"></div>
          <div class="mt-4 grid gap-3">
            <div class="h-10 rounded-lg bg-white shadow-sm"></div>
            <div class="h-10 rounded-lg bg-gray-100"></div>
            <div class="h-24 rounded-lg bg-white shadow-sm"></div>
          </div>
        </div>
      </button>

      <button
        @click="setTheme('dark')"
        class="text-left rounded-2xl border p-6 transition-all duration-200"
        :class="themeStore.currentTheme === 'dark'
          ? 'border-sky-400/50 bg-sky-500/10 shadow-lg shadow-sky-500/10'
          : 'border-gray-200 bg-white hover:border-sky-200 dark:border-white/10 dark:bg-white/5 dark:hover:border-sky-400/30'"
      >
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <h2 class="text-xl font-semibold">Dark</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              A lower-glare look with stronger contrast for night sessions.
            </p>
          </div>
          <span v-if="themeStore.currentTheme === 'dark'" class="px-3 py-1 rounded-full text-xs font-semibold bg-sky-500 text-white">
            Active
          </span>
        </div>

        <div class="rounded-xl border border-white/10 bg-gray-950 p-4">
          <div class="h-4 w-24 rounded bg-white/10"></div>
          <div class="mt-4 grid gap-3">
            <div class="h-10 rounded-lg bg-white/10"></div>
            <div class="h-10 rounded-lg bg-white/5"></div>
            <div class="h-24 rounded-lg bg-black/40 border border-white/5"></div>
          </div>
        </div>
      </button>

      <button
        @click="setTheme('dqs-hosting')"
        class="text-left rounded-2xl border p-6 transition-all duration-200"
        :class="themeStore.currentTheme === 'dqs-hosting'
          ? 'border-cyan-400/60 bg-cyan-500/10 shadow-lg shadow-cyan-500/10'
          : 'border-gray-200 bg-white hover:border-cyan-200 dark:border-white/10 dark:bg-white/5 dark:hover:border-cyan-400/30'"
      >
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <h2 class="text-xl font-semibold">dqs hosting theme</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Uses the older dqs hosting template look with near-black surfaces, simple blue actions, and softer green/red status styling.
            </p>
          </div>
          <span v-if="themeStore.currentTheme === 'dqs-hosting'" class="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500 text-white">
            Active
          </span>
        </div>

        <div class="rounded-xl border border-[#222] bg-[#0f0f0f] p-4">
          <div class="h-4 w-24 rounded bg-[#1a1a1a]"></div>
          <div class="mt-4 grid gap-3">
            <div class="h-10 rounded-lg bg-[#151515] border border-[#222]"></div>
            <div class="h-10 rounded-lg bg-[#151515] border border-[#222]"></div>
            <div class="h-24 rounded-lg bg-[#0a0a0a] border border-[#222]"></div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { useThemeStore } from '../stores/theme'

const themeStore = useThemeStore()

function setTheme(theme) {
  themeStore.setTheme(theme)
}
</script>
