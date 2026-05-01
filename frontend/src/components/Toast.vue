<template>
  <div class="fixed top-4 right-4 z-[9999] space-y-2 pointer-events-none">
    <transition-group name="toast">
      <div v-for="toast in toasts" :key="toast.id"
        class="pointer-events-auto glass rounded-xl p-4 shadow-xl max-w-sm animate-slide-in"
        :class="{
          'border-l-4 border-l-emerald-500': toast.type === 'success',
          'border-l-4 border-l-red-500': toast.type === 'error',
          'border-l-4 border-l-yellow-500': toast.type === 'warning',
          'border-l-4 border-l-blue-500': toast.type === 'info'
        }">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">
            <svg v-if="toast.type === 'success'" class="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <svg v-else-if="toast.type === 'error'" class="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            <svg v-else-if="toast.type === 'warning'" class="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <svg v-else class="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div class="flex-1">
            <p class="font-medium text-sm">{{ toast.title }}</p>
            <p v-if="toast.message" class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ toast.message }}</p>
          </div>
          <button @click="removeToast(toast.id)" class="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
    </transition-group>
  </div>

  <transition name="modal">
    <div v-if="confirmModal.show" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9998] p-4 dqs-modal-overlay" @click.self="cancelConfirm">
      <div class="glass rounded-2xl p-6 w-full max-w-md scale-in dqs-modal-card">
        <div class="flex items-center gap-3 mb-4">
          <div :class="{
            'bg-red-100 dark:bg-red-500/20': confirmModal.type === 'danger',
            'bg-yellow-100 dark:bg-yellow-500/20': confirmModal.type === 'warning',
            'bg-blue-100 dark:bg-blue-500/20': confirmModal.type === 'info'
          }" class="w-12 h-12 rounded-xl flex items-center justify-center">
            <svg v-if="confirmModal.type === 'danger'" class="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <svg v-else-if="confirmModal.type === 'warning'" class="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <svg v-else class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
          </div>
          <h3 class="text-lg font-semibold">{{ confirmModal.title }}</h3>
        </div>
        <p class="text-gray-600 dark:text-gray-400 mb-6">{{ confirmModal.message }}</p>
        <div class="flex gap-3">
          <button @click="cancelConfirm" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">
            {{ confirmModal.cancelText }}
          </button>
          <button @click="confirmAction" :class="{
            'btn-danger': confirmModal.type === 'danger',
            'btn-primary': confirmModal.type !== 'danger'
          }" class="flex-1">
            {{ confirmModal.confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, provide } from 'vue'

const toasts = ref([])
let toastId = 0

const confirmModal = reactive({
  show: false,
  title: '',
  message: '',
  type: 'info',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  resolve: null
})

function addToast(options) {
  const id = ++toastId
  toasts.value.push({
    id,
    title: options.title || 'Notification',
    message: options.message || '',
    type: options.type || 'info'
  })
  setTimeout(() => removeToast(id), options.duration || 4000)
}

function removeToast(id) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

function showConfirm(options) {
  return new Promise((resolve) => {
    confirmModal.show = true
    confirmModal.title = options.title || 'Confirm'
    confirmModal.message = options.message || 'Are you sure?'
    confirmModal.type = options.type || 'info'
    confirmModal.confirmText = options.confirmText || 'Confirm'
    confirmModal.cancelText = options.cancelText || 'Cancel'
    confirmModal.resolve = resolve
  })
}

function confirmAction() {
  confirmModal.show = false
  if (confirmModal.resolve) confirmModal.resolve(true)
}

function cancelConfirm() {
  confirmModal.show = false
  if (confirmModal.resolve) confirmModal.resolve(false)
}

provide('toast', addToast)
provide('confirm', showConfirm)

defineExpose({ addToast, showConfirm })
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
