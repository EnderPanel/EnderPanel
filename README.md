# EnderPanel

EnderPanel is a self-hosted, open-source control panel for running Minecraft servers with Docker. It provides server lifecycle controls, a web console, file and backup management, scheduled tasks, mod management, user accounts, two-factor authentication, and optional Playit networking.

## Requirements

- Python 3.12 or newer
- Node.js 20 or newer
- Docker Engine or Docker Desktop

Java does not need to be installed on the host. EnderPanel builds Java 11, 17, 21, and 25 runtime images from the included Dockerfiles and automatically selects the appropriate image for the chosen Minecraft version.

The supplied installers can install or guide you through these prerequisites, but review scripts before running them with administrator privileges.

## Development setup

```text
git clone https://github.com/EnderPanel/EnderPanel.git
cd EnderPanel
python -m venv .venv
```

Activate the virtual environment, then install and build:

```text
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ../backend
python main.py
```

Open `http://localhost:8000`. The first registered account becomes the administrator, so create it before exposing the panel to a network.

For frontend development, run `npm run dev` inside `frontend`. The Vite server listens on port 3000.

## Configuration and backups

EnderPanel creates its SQLite database and encryption keys under `backend/` on first start. Back up these items together:

- `backend/enderpanel.db`
- `backend/.secret_key`
- `backend/.data_encryption_key`
- `backend/servers/`
- `backend/avatars/`
- `backend/data/`

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | JWT signing secret | Generated locally |
| `DATA_ENCRYPTION_KEY` | Encryption key for stored secrets | Generated locally |
| `SESSION_COOKIE_SECURE` | Restrict session cookies to HTTPS | `false` |
| `ENDERPANEL_UPLOAD_LIMIT_MB` | Initial file upload limit | `100` |
| `ENDERPANEL_START_FRONTEND_DEV` | Start Vite with the backend | Disabled on Windows |
| `ENDERPANEL_DISABLE_FRONTEND_DEV` | Prevent automatic Vite startup | `false` |

For deployments beyond localhost, use an HTTPS reverse proxy and set `SESSION_COOKIE_SECURE=true`. Never publish the Docker socket or backend data directory.

## Tests and checks

```text
python -m compileall -q backend
cd backend
python -m unittest discover -s tests -v
cd ../frontend
npm ci
npm run build
npm audit --omit=dev
```

These checks also run for pushes and pull requests through GitHub Actions.

## Updates and security

Create a backup before upgrading. In-app update archives require a matching `.sha256` sidecar; EnderPanel refuses archives that cannot be verified. Authentication uses an HttpOnly session cookie plus CSRF protection. Keep the generated key files private and never commit them.

Packaged builds and update metadata are maintained in the [EnderPanel Releases repository](https://github.com/EnderPanel/Releases).

See [license.md](license.md) for licensing information.

