const { execSync } = require('child_process')
const ports = process.argv.slice(2)

for (const port of ports) {
  try {
    if (process.platform === 'win32') {
      const out = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf8' })
      for (const line of out.trim().split('\n')) {
        const pid = line.trim().split(/\s+/).pop()
        if (pid && pid !== '0') execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' })
      }
    } else {
      execSync(`lsof -ti:${port} | xargs kill -9 2>/dev/null`, { stdio: 'ignore' })
    }
  } catch {}
}
