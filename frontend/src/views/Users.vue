<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-2xl font-bold">User Management</h1>
      <span class="text-gray-500 dark:text-gray-400">{{ users.length }} users</span>
    </div>

    <div v-if="loading" class="text-center text-gray-500 dark:text-gray-400 py-12">Loading users...</div>

    <div v-else-if="users.length === 0" class="text-center py-16">
      <h2 class="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">No users found</h2>
    </div>

    <div v-else class="card overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-100 dark:bg-gray-800">
          <tr>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600 dark:text-gray-400">User</th>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600 dark:text-gray-400">Email</th>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600 dark:text-gray-400">Servers</th>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600 dark:text-gray-400">Role</th>
            <th class="text-right px-6 py-4 text-sm font-medium text-gray-600 dark:text-gray-400">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="border-t border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-mc-accent/20 flex items-center justify-center text-mc-accent font-bold">
                  {{ user.username.charAt(0).toUpperCase() }}
                </div>
                <span class="font-medium">{{ user.username }}</span>
              </div>
            </td>
            <td class="px-6 py-4 text-gray-500 dark:text-gray-400">{{ user.email }}</td>
            <td class="px-6 py-4">
              <span class="bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full text-sm">{{ user.server_count }}</span>
            </td>
            <td class="px-6 py-4">
              <span :class="user.is_admin ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'"
                class="px-3 py-1 rounded-full text-xs font-medium">
                {{ user.is_admin ? 'Admin' : 'User' }}
              </span>
            </td>
            <td class="px-6 py-4">
              <div class="flex gap-2 justify-end">
                <button @click="editUser(user)" class="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 px-3 py-1 rounded text-xs">Edit</button>
                <button v-if="!user.is_admin" @click="makeAdmin(user.id)" class="bg-yellow-100 dark:bg-yellow-600 hover:bg-yellow-200 dark:hover:bg-yellow-500 text-yellow-700 dark:text-white px-3 py-1 rounded text-xs">Make Admin</button>
                <button v-if="user.is_admin && user.id !== currentUserId" @click="removeAdmin(user.id)" class="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 px-3 py-1 rounded text-xs">Remove Admin</button>
                <button v-if="user.id !== currentUserId" @click="deleteUser(user.id, user.username)" class="bg-red-100 dark:bg-red-600 hover:bg-red-200 dark:hover:bg-red-500 text-red-700 dark:text-white px-3 py-1 rounded text-xs">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <transition name="modal">
      <div v-if="showEdit" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="showEdit = false">
        <div class="glass rounded-2xl p-8 w-full max-w-md scale-in">
          <h2 class="text-xl font-bold mb-6">Edit User: {{ editingUser.username }}</h2>
          <form @submit.prevent="saveUser" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Username</label>
              <input v-model="editForm.username" type="text" class="input-field" />
            </div>
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Email</label>
              <input v-model="editForm.email" type="email" class="input-field" />
            </div>
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">New Password (leave empty to keep current)</label>
              <input v-model="editForm.password" type="password" class="input-field" />
            </div>
            <div class="flex gap-3 pt-4">
              <button type="button" @click="showEdit = false" class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 py-3 rounded-xl transition">Cancel</button>
              <button type="submit" class="flex-1 btn-primary">Save</button>
            </div>
          </form>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const users = ref([])
const loading = ref(true)
const showEdit = ref(false)
const editingUser = ref(null)
const editForm = ref({ username: '', email: '', password: '' })
const currentUserId = ref(null)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await axios.get('/api/users/')
    users.value = res.data
  } catch (e) {
    console.error('Failed to fetch users:', e)
  } finally {
    loading.value = false
  }
}

function editUser(user) {
  editingUser.value = user
  editForm.value = { username: user.username, email: user.email, password: '' }
  showEdit.value = true
}

async function saveUser() {
  try {
    const data = {}
    if (editForm.value.username) data.username = editForm.value.username
    if (editForm.value.email) data.email = editForm.value.email
    if (editForm.value.password) data.password = editForm.value.password

    await axios.put(`/api/users/${editingUser.value.id}`, data)
    showEdit.value = false
    await fetchUsers()
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to update user')
  }
}

async function makeAdmin(userId) {
  if (confirm('Make this user an admin?')) {
    await axios.post(`/api/users/${userId}/make-admin`)
    await fetchUsers()
  }
}

async function removeAdmin(userId) {
  if (confirm('Remove admin privileges from this user?')) {
    await axios.post(`/api/users/${userId}/remove-admin`)
    await fetchUsers()
  }
}

async function deleteUser(userId, username) {
  if (confirm(`Delete user "${username}" and all their servers?`)) {
    await axios.delete(`/api/users/${userId}`)
    await fetchUsers()
  }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    currentUserId.value = user.id
  }
  await fetchUsers()
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
</style>
