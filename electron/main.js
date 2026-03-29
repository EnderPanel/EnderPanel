const { app, BrowserWindow, ipcMain, Menu, nativeTheme } = require('electron')
const path = require('path')
const fs = require('fs')

const configPath = path.join(app.getPath('userData'), 'enderpanel.json')
const isMac = process.platform === 'darwin'

function getConfig() {
  try { return JSON.parse(fs.readFileSync(configPath, 'utf8')) }
  catch { return null }
}

function saveConfig(config) {
  fs.writeFileSync(configPath, JSON.stringify(config))
}

let win

function loadSetup() {
  if (!win) return
  win.loadFile(path.join(__dirname, 'setup.html'))
  if (isMac) Menu.setApplicationMenu(Menu.buildFromTemplate([]))
}

function injectBar() {
  if (!win) return
  const dark = nativeTheme.shouldUseDarkColors
  const barHeight = isMac ? 38 : 28
  const barTop = isMac ? 0 : 0
  const padding = isMac ? 'padding-left:76px;' : ''

  win.webContents.executeJavaScript(`
    (function(){
      var old=document.getElementById('ep-bar');
      if(old){old.remove();document.body.style.paddingTop='0'}
      var s=document.createElement('style');
      s.textContent=\`
        #ep-bar{position:fixed;top:0;left:0;right:0;z-index:999999;height:${barHeight}px;display:flex;align-items:center;justify-content:space-between;${padding}padding-right:12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:12px;-webkit-app-region:drag;\${${dark}?'background:rgba(25,25,30,0.85);border-bottom:1px solid rgba(255,255,255,0.05);color:rgba(255,255,255,0.5);':'background:rgba(240,240,240,0.85);border-bottom:1px solid rgba(0,0,0,0.08);color:rgba(0,0,0,0.5);'}backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}
        #ep-bar .ep-logo{display:flex;align-items:center;gap:6px;opacity:0.6}
        #ep-bar .ep-logo-dot{width:6px;height:6px;border-radius:50%;background:linear-gradient(135deg,#a855f7,#ec4899)}
        #ep-bar .ep-btn{-webkit-app-region:no-drag;\${${dark}?'background:transparent;color:rgba(255,255,255,0.45);border:1px solid rgba(255,255,255,0.08);':'background:transparent;color:rgba(0,0,0,0.45);border:1px solid rgba(0,0,0,0.1);'}border-radius:4px;padding:2px 10px;font:inherit;font-size:11px;cursor:pointer;transition:all 0.15s;line-height:1.4}
        #ep-bar .ep-btn:hover{\${${dark}?'background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.7);':'background:rgba(0,0,0,0.06);color:rgba(0,0,0,0.7);'}}
      \`;
      document.head.appendChild(s);
      var b=document.createElement('div');b.id='ep-bar';
      var logo=document.createElement('div');logo.className='ep-logo';
      var dot=document.createElement('div');dot.className='ep-logo-dot';
      var name=document.createElement('span');name.textContent='EnderPanel';
      logo.appendChild(dot);logo.appendChild(name);
      var btn=document.createElement('button');btn.className='ep-btn';btn.textContent='Change Server';
      btn.onclick=function(){if(confirm('Change server address?'))window.__ep.reset()};
      b.appendChild(logo);b.appendChild(btn);document.body.appendChild(b);
      document.body.style.paddingTop='${barHeight}px';
    })();`).catch(function(){})
}

ipcMain.handle('save-config', (_, data) => {
  saveConfig(data)
  if (win) win.loadURL(data.serverUrl)
})

ipcMain.handle('reset-config', () => {
  try { fs.unlinkSync(configPath) } catch {}
  loadSetup()
})

function createWindow() {
  win = new BrowserWindow({
    width: 1200, height: 800,
    show: false,
    center: true,
    title: 'EnderPanel',
    icon: path.join(__dirname, 'icon.png'),
    titleBarStyle: isMac ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  win.webContents.session.webRequest.onHeadersReceived((d, cb) => {
    const h = { ...d.responseHeaders }
    delete h['content-security-policy']
    delete h['Content-Security-Policy']
    cb({ responseHeaders: h })
  })

  win.webContents.on('did-finish-load', () => setTimeout(injectBar, 500))
  win.webContents.on('did-navigate', () => setTimeout(injectBar, 500))
  win.webContents.on('did-navigate-in-page', () => setTimeout(injectBar, 500))

  const config = getConfig()
  if (config && config.serverUrl) {
    win.loadURL(config.serverUrl)
  } else {
    loadSetup()
  }

  win.once('ready-to-show', () => {
    win.show()
    win.focus()
  })

  if (isMac) {
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      { label: 'EnderPanel', submenu: [
        { label: 'Change Server', accelerator: 'CommandOrControl+Shift+L', click: () => {
          try { fs.unlinkSync(configPath) } catch {}
          loadSetup()
        }},
        { type: 'separator' },
        { role: 'quit' }
      ]},
      { role: 'editMenu' },
      { role: 'viewMenu' }
    ]))
  } else {
    Menu.setApplicationMenu(null)
  }
}

nativeTheme.on('updated', () => injectBar())
app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())
