<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-xl max-w-md w-full p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Backup Notes</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="mb-4">
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">For backup: <span class="font-medium">{{ filename }}</span></p>
        <textarea
          v-model="localNotes"
          rows="3"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
          placeholder="Add a note to remember what this backup contains..."
        ></textarea>
      </div>

      <div class="flex gap-3 justify-end">
        <button @click="$emit('close')" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all">
          Cancel
        </button>
        <button @click="saveNotes" :disabled="saving" class="px-4 py-2 text-sm bg-purple-500 text-white rounded-xl hover:bg-purple-600 disabled:opacity-50 transition-all flex items-center gap-2">
          <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, inject } from 'vue'
import axios from 'axios'

const props = defineProps({
  show: Boolean,
  serverId: Number,
  filename: String,
  initialNotes: String
})

const emit = defineEmits(['close', 'saved'])
const toast = inject('toast')

const localNotes = ref('')
const saving = ref(false)

watch(() => props.initialNotes, (newNotes) => {
  localNotes.value = newNotes || ''
})

const saveNotes = async () => {
  saving.value = true
  try {
    await axios.patch(`/api/servers/${props.serverId}/files/backups/${props.filename}/notes`, {
      notes: localNotes.value || null
    })
    emit('saved', localNotes.value)
    emit('close')
    toast({ title: 'Notes saved', type: 'success' })
  } catch (e) {
    toast({ title: 'Failed to save notes', message: e.response?.data?.detail || '', type: 'error' })
  }
  saving.value = false
}
</script>