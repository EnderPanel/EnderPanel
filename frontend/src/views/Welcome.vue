<template>
  <div class="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse-slow" style="animation-delay: 1.5s"></div>
    </div>

    <div class="w-full max-w-2xl relative z-10">
      <div class="glass rounded-2xl p-8 md:p-12 shadow-2xl">
        <transition name="slide" mode="out-in">
          <div v-if="step === 0" key="welcome" class="text-center">
            <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-500 via-pink-500 to-purple-700 rounded-3xl mb-6 animate-float relative overflow-hidden shadow-lg shadow-purple-500/30">
              <div class="absolute inset-3 bg-gradient-to-br from-pink-300 to-purple-400 rounded-2xl opacity-80"></div>
              <div class="absolute w-5 h-5 bg-white rounded-full top-4 left-4 opacity-90 shadow-lg shadow-white/50"></div>
            </div>
            <h1 class="text-3xl font-bold mb-3">Welcome to EnderPanel!</h1>
            <p class="text-gray-500 dark:text-gray-400 mb-8">Let's get you set up in just a few steps.</p>
            <button @click="step = 1" class="btn-primary px-8 py-3">
              Get Started
              <svg class="w-5 h-5 inline ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
              </svg>
            </button>
          </div>

          <div v-else-if="step === 1" key="profile" class="text-center">
            <div class="w-16 h-16 bg-gradient-to-br from-mc-accent to-mc-purple rounded-2xl mx-auto mb-6 flex items-center justify-center">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <h2 class="text-2xl font-bold mb-3">Set Your Avatar</h2>
            <p class="text-gray-500 dark:text-gray-400 mb-6">Upload a profile picture to personalize your account.</p>
            
            <div class="flex flex-col items-center gap-4 mb-8">
              <div class="relative group">
                <input type="file" ref="avatarInput" @change="handleAvatar" accept="image/*" class="hidden" />
                <button @click="$refs.avatarInput.click()" 
                  class="w-24 h-24 rounded-2xl overflow-hidden border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-mc-accent transition-all duration-200 flex items-center justify-center bg-gray-50 dark:bg-white/5">
                  <img v-if="avatarPreview" :src="avatarPreview" class="w-full h-full object-cover" />
                  <div v-else class="text-center">
                    <svg class="w-8 h-8 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                    </svg>
                  </div>
                </button>
              </div>
              <p class="text-xs text-gray-500">Click to upload (optional)</p>
            </div>

            <div class="flex gap-3">
              <button @click="step = 0" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">
                Back
              </button>
              <button @click="step = 2" class="flex-1 btn-primary">
                Continue
              </button>
            </div>
          </div>

          <div v-else-if="step === 2" key="features" class="text-center">
            <div class="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl mx-auto mb-6 flex items-center justify-center">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
              </svg>
            </div>
            <h2 class="text-2xl font-bold mb-6">What You Can Do</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 text-left">
              <div class="bg-gray-50 dark:bg-white/5 rounded-xl p-4">
                <div class="w-10 h-10 bg-purple-100 dark:bg-purple-500/20 rounded-lg flex items-center justify-center mb-3">
                  <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2"/>
                  </svg>
                </div>
                <h3 class="font-semibold mb-1">Create Servers</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">Paper, Fabric, Forge & more</p>
              </div>
              <div class="bg-gray-50 dark:bg-white/5 rounded-xl p-4">
                <div class="w-10 h-10 bg-emerald-100 dark:bg-emerald-500/20 rounded-lg flex items-center justify-center mb-3">
                  <svg class="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                </div>
                <h3 class="font-semibold mb-1">Install Plugins</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">One-click from Modrinth</p>
              </div>
              <div class="bg-gray-50 dark:bg-white/5 rounded-xl p-4">
                <div class="w-10 h-10 bg-blue-100 dark:bg-blue-500/20 rounded-lg flex items-center justify-center mb-3">
                  <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
                  </svg>
                </div>
                <h3 class="font-semibold mb-1">Auto Backups</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">Never lose your world</p>
              </div>
            </div>

            <div class="flex gap-3">
              <button @click="step = 1" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">
                Back
              </button>
              <button @click="finish" class="flex-1 btn-success py-3">
                Let's Go! 🚀
              </button>
            </div>
          </div>
        </transition>

        <div class="flex justify-center gap-2 mt-8">
          <div v-for="i in 3" :key="i" 
            :class="step === i - 1 ? 'bg-mc-accent w-8' : 'bg-gray-300 dark:bg-gray-600 w-2'"
            class="h-2 rounded-full transition-all duration-300"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const step = ref(0)
const avatarInput = ref(null)
const avatarPreview = ref(null)
const avatarFile = ref(null)

function handleAvatar(event) {
  const file = event.target.files[0]
  if (file) {
    avatarFile.value = file
    avatarPreview.value = URL.createObjectURL(file)
  }
}

async function finish() {
  if (avatarFile.value) {
    try {
      const formData = new FormData()
      formData.append('file', avatarFile.value)
      await axios.post('/api/user/avatar', formData)
      
      const res = await axios.get('/api/auth/me')
      localStorage.setItem('user', JSON.stringify(res.data))
    } catch (e) {
      console.error('Failed to upload avatar:', e)
    }
  }

  localStorage.setItem('welcome_shown', 'true')
  router.push('/dashboard')
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
