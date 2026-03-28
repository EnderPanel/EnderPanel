const { app, BrowserWindow, ipcMain, Menu } = require('electron')
const path = require('path')
const fs = require('fs')

const configPath = path.join(app.getPath('userData'), 'enderpanel.json')

function getConfig() {
  try { return JSON.parse(fs.readFileSync(configPath, 'utf8')) }
  catch { return null }
}

function saveConfig(config) {
  fs.writeFileSync(configPath, JSON.stringify(config))
}

let win

ipcMain.handle('save-config', (_, data) => {
  saveConfig(data)
  win.loadURL(data.serverUrl)
  setPanelMenu()
})

ipcMain.handle('reset-config', () => {
  try { fs.unlinkSync(configPath) } catch {}
  win.loadFile(path.join(__dirname, 'setup.html'))
  hideMenu()
})

function hideMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([]))
}

function setPanelMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: 'EnderPanel',
      submenu: [
        { label: 'Reset Server Address', accelerator: 'CommandOrControl+Shift+L', click: () => {
          try { fs.unlinkSync(configPath) } catch {}
          win.loadFile(path.join(__dirname, 'setup.html'))
          hideMenu()
        }},
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    { role: 'editMenu' },
    { role: 'viewMenu' }
  ]))
}

function createWindow() {
  const config = getConfig()

  win = new BrowserWindow({
    width: 1200,
    height: 800,
    center: true,
    title: 'EnderPanel',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  win.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    const h = { ...details.responseHeaders }
    delete h['content-security-policy']
    delete h['Content-Security-Policy']
    callback({ responseHeaders: h })
  })

  if (config && config.serverUrl) {
    win.loadURL(config.serverUrl)
    setPanelMenu()
  } else {
    win.loadFile(path.join(__dirname, 'setup.html'))
    hideMenu()
  }
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())
