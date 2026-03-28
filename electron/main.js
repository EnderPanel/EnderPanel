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

function loadSetup() {
  if (!win) return
  win.loadFile(path.join(__dirname, 'setup.html'))
  if (process.platform === 'darwin') Menu.setApplicationMenu(Menu.buildFromTemplate([]))
}

function injectBar() {
  if (!win) return
  const dark = nativeTheme.shouldUseDarkColors
  const css = dark
    ? 'background:rgba(10,10,20,0.75);border-bottom:1px solid rgba(255,255,255,0.06);color:rgba(255,255,255,0.4);'
    : 'background:rgba(245,245,245,0.75);border-bottom:1px solid rgba(0,0,0,0.08);color:rgba(0,0,0,0.4);'
  const btnStyle = dark
    ? 'background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:rgba(255,255,255,0.5);'
    : 'background:rgba(0,0,0,0.05);border:1px solid rgba(0,0,0,0.1);color:rgba(0,0,0,0.5);'

  win.webContents.executeJavaScript(`
    (function(){
      var e=document.getElementById('ep-bar');
      if(e){e.remove();document.body.style.paddingTop='0'}
      var s=document.createElement('style');
      s.textContent='#ep-bar{position:fixed;top:0;left:0;right:0;z-index:999999;height:26px;${css}backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);display:flex;align-items:center;justify-content:space-between;padding:0 10px;font:500 10px/1 Inter,-apple-system,sans-serif;-webkit-app-region:drag}#ep-bar span{user-select:none;opacity:0.7}#ep-bar button{-webkit-app-region:no-drag;${btnStyle}border-radius:4px;padding:1px 8px;font:inherit;font-size:10px;cursor:pointer;transition:opacity .15s}#ep-bar button:hover{opacity:0.8}';
      document.head.appendChild(s);
      var b=document.createElement('div');b.id='ep-bar';
      var t=document.createElement('span');t.textContent='EnderPanel';
      var c=document.createElement('button');c.textContent='Change Server';
      c.onclick=function(){if(confirm('Change server?'))window.__ep.reset()};
      b.appendChild(t);b.appendChild(c);document.body.appendChild(b);
      document.body.style.paddingTop='26px';
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
    show: true,
    center: true,
    title: 'EnderPanel',
    icon: path.join(__dirname, 'icon.png'),
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

  if (process.platform === 'darwin') {
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
