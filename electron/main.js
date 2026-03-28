const { app, BrowserWindow, ipcMain, Menu, nativeTheme } = require('electron')
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
  showResetButton()
})

ipcMain.handle('reset-config', () => {
  try { fs.unlinkSync(configPath) } catch {}
  loadSetup()
})

function loadSetup() {
  if (!win) return
  win.loadFile(path.join(__dirname, 'setup.html'))
  if (process.platform === 'darwin') {
    Menu.setApplicationMenu(Menu.buildFromTemplate([]))
  }
}

function showResetButton() {
  if (!win) return
  const dark = nativeTheme.shouldUseDarkColors
  const bg = dark ? 'rgba(10,10,20,0.7)' : 'rgba(245,245,245,0.7)'
  const text = dark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)'
  const btnBg = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const btnBorder = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'
  const btnText = dark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)'
  const btnHoverBg = dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'
  const btnHoverText = dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.8)'
  const border = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.08)'

  win.webContents.executeJavaScript(`
    (function() {
      var bar = document.getElementById('ep-bar');
      if (bar) {
        bar.style.background = '${bg}';
        bar.style.borderBottom = '1px solid ${border}';
        var t = bar.querySelector('span');
        if (t) t.style.color = '${text}';
        var b = bar.querySelector('button');
        if (b) {
          b.style.background = '${btnBg}';
          b.style.border = '1px solid ${btnBorder}';
          b.style.color = '${btnText}';
          b.onmouseenter = function(){b.style.background='${btnHoverBg}';b.style.color='${btnHoverText}'};
          b.onmouseleave = function(){b.style.background='${btnBg}';b.style.color='${btnText}'};
        }
        return;
      }
      bar = document.createElement('div');
      bar.id = 'ep-bar';
      bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:999999;height:30px;background:${bg};backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid ${border};display:flex;align-items:center;justify-content:space-between;padding:0 12px;font-family:Inter,-apple-system,sans-serif;font-size:11px;-webkit-app-region:drag;transition:background 0.3s;';
      var title = document.createElement('span');
      title.textContent = 'EnderPanel';
      title.style.cssText = 'color:${text};user-select:none;font-weight:500;';
      var btn = document.createElement('button');
      btn.textContent = 'Change Server';
      btn.style.cssText = '-webkit-app-region:no-drag;background:${btnBg};color:${btnText};border:1px solid ${btnBorder};border-radius:5px;padding:2px 10px;font-size:11px;cursor:pointer;font-family:inherit;transition:all 0.15s;';
      btn.onmouseenter = function(){btn.style.background='${btnHoverBg}';btn.style.color='${btnHoverText}'};
      btn.onmouseleave = function(){btn.style.background='${btnBg}';btn.style.color='${btnText}'};
      btn.onclick = function(){if(confirm('Change server address?'))window.__ep.reset()};
      bar.appendChild(title);
      bar.appendChild(btn);
      document.body.appendChild(bar);
      document.body.style.paddingTop = '30px';
      document.body.style.transition = 'padding-top 0.2s';
    })();
  `).catch(function(){})
  
  win.webContents.once('did-navigate', () => {
    setTimeout(showResetButton, 1500)
  })
}

function setPanelMenu() {
  if (process.platform === 'darwin') {
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      {
        label: 'EnderPanel',
        submenu: [
          { label: 'Reset Server Address', accelerator: 'CommandOrControl+Shift+L', click: () => {
            try { fs.unlinkSync(configPath) } catch {}
            loadSetup()
          }},
          { type: 'separator' },
          { role: 'quit' }
        ]
      },
      { role: 'editMenu' },
      { role: 'viewMenu' }
    ]))
  } else {
    Menu.setApplicationMenu(null)
  }
}

nativeTheme.on('updated', () => {
  showResetButton()
})

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
    win.webContents.once('did-finish-load', () => {
      setTimeout(showResetButton, 1500)
    })
  } else {
    loadSetup()
  }
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())
