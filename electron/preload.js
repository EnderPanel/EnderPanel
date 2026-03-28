const { contextBridge, ipcRenderer } = require('electron')
contextBridge.exposeInMainWorld('__ep', {
  save: (data) => ipcRenderer.invoke('save-config', data),
  reset: () => ipcRenderer.invoke('reset-config')
})
